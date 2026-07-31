from __future__ import annotations

import json
import random
import time
from collections import defaultdict, deque
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

from .config import Settings
from .providers.base import FailureClass, ProviderFailure, VideoUnderstandingProvider


@dataclass(frozen=True)
class ModelPolicy:
    model_id: str
    provider: str
    role: Literal["primary", "fallback", "escalation", "optional"]
    rpm: int
    tpm: int
    rpd: int
    max_retries: int
    max_concurrent_calls: int
    requires_audio: bool = True
    requires_visual: bool = True


@dataclass(frozen=True)
class RouteDecision:
    provider: VideoUnderstandingProvider
    policy: ModelPolicy
    fallback_reason: str | None = None
    escalation_reason: str | None = None


class ModelUsageBudgetLedger:
    """Conservative STILL-owned usage signals; never an authoritative provider-quota ledger."""

    def __init__(self, policies: list[ModelPolicy]) -> None:
        self.policies = {policy.model_id: policy for policy in policies}
        self.requests: dict[str, deque[float]] = defaultdict(deque)
        self.token_events: dict[str, deque[tuple[float, int]]] = defaultdict(deque)
        self.daily_requests: dict[tuple[str, str], int] = defaultdict(int)
        self.project_estimated_tokens: dict[tuple[str, str], int] = defaultdict(int)
        self.escalation_by_project: dict[tuple[str, str], int] = defaultdict(int)
        self.in_flight: dict[str, int] = defaultdict(int)
        self.successful_requests: dict[tuple[str, str], int] = defaultdict(int)
        self.failed_requests: dict[tuple[str, str], int] = defaultdict(int)
        self.retry_requests: dict[tuple[str, str], int] = defaultdict(int)
        self.circuit_open_until: dict[str, float] = {}
        self.recent_rate_limits: dict[str, deque[float]] = defaultdict(deque)

    def _today(self) -> str:
        return datetime.now(UTC).date().isoformat()

    def is_available(self, model_id: str, *, project_id: str, is_escalation: bool, escalation_budget: int, estimated_tokens: int = 0, project_token_budget: int = 300_000) -> bool:
        policy = self.policies[model_id]
        now = time.monotonic()
        if self.circuit_open_until.get(model_id, 0) > now:
            return False
        recent = self.requests[model_id]
        while recent and recent[0] < now - 60:
            recent.popleft()
        recent_tokens = self.token_events[model_id]
        while recent_tokens and recent_tokens[0][0] < now - 60:
            recent_tokens.popleft()
        if self.in_flight[model_id] >= policy.max_concurrent_calls:
            return False
        if len(recent) >= policy.rpm or self.daily_requests[(model_id, self._today())] >= policy.rpd:
            return False
        if sum(tokens for _, tokens in recent_tokens) + estimated_tokens > policy.tpm:
            return False
        if self.project_estimated_tokens[(project_id, self._today())] + estimated_tokens > project_token_budget:
            return False
        if is_escalation and self.escalation_by_project[(project_id, self._today())] >= escalation_budget:
            return False
        return True

    def reserve(self, model_id: str, *, project_id: str, is_escalation: bool, estimated_tokens: int = 0, is_retry: bool = False) -> None:
        self.requests[model_id].append(time.monotonic())
        self.token_events[model_id].append((time.monotonic(), estimated_tokens))
        self.in_flight[model_id] += 1
        self.daily_requests[(model_id, self._today())] += 1
        self.project_estimated_tokens[(project_id, self._today())] += estimated_tokens
        if is_retry:
            self.retry_requests[(model_id, self._today())] += 1
        if is_escalation:
            self.escalation_by_project[(project_id, self._today())] += 1

    def release(self, model_id: str) -> None:
        self.in_flight[model_id] = max(0, self.in_flight[model_id] - 1)

    def record_success(self, model_id: str) -> None:
        self.successful_requests[(model_id, self._today())] += 1

    def record_failure(self, model_id: str, failure: ProviderFailure) -> None:
        self.failed_requests[(model_id, self._today())] += 1
        if failure.failure_class in {FailureClass.RETRYABLE_RATE_LIMIT, FailureClass.RETRYABLE_TEMPORARY}:
            now = time.monotonic()
            rates = self.recent_rate_limits[model_id]
            rates.append(now)
            while rates and rates[0] < now - 120:
                rates.popleft()
            if len(rates) >= 2:
                retry_after = failure.retry_after_seconds or 60
                self.circuit_open_until[model_id] = now + retry_after


def load_model_policies(settings: Settings) -> list[ModelPolicy]:
    root = Path(__file__).resolve().parents[3]
    configured = root / settings.model_policy_path
    fallback = root / "config" / "model-policy.example.json"
    policy_path = configured if configured.exists() else fallback
    payload = json.loads(policy_path.read_text(encoding="utf-8"))
    return [ModelPolicy(**item) for item in payload["models"]]


class VideoModelRouter:
    def __init__(self, providers: dict[str, VideoUnderstandingProvider], ledger: ModelUsageBudgetLedger, policies: list[ModelPolicy], settings: Settings) -> None:
        self.providers = providers
        self.ledger = ledger
        self.policies = policies
        self.settings = settings

    def decide(
        self,
        *,
        project_id: str,
        requires_audio: bool,
        requires_visual: bool,
        importance: Literal["ordinary", "high"],
        confidence: float | None,
        safety_sensitive: bool,
        escalation_budget: int = 2,
        estimated_tokens: int = 12_000,
        project_token_budget: int = 300_000,
        exclude_models: set[str] | None = None,
    ) -> RouteDecision:
        needs_escalation = importance == "high" or safety_sensitive or (confidence is not None and confidence < 0.65)
        ordered_roles = ["escalation", "primary", "fallback"] if needs_escalation else ["primary", "fallback"]
        for role in ordered_roles:
            for policy in self.policies:
                if policy.role != role or policy.provider not in self.providers:
                    continue
                if policy.model_id in (exclude_models or set()):
                    continue
                if (requires_audio and not policy.requires_audio) or (requires_visual and not policy.requires_visual):
                    continue
                escalation = policy.role == "escalation"
                if not self.ledger.is_available(policy.model_id, project_id=project_id, is_escalation=escalation, escalation_budget=escalation_budget, estimated_tokens=estimated_tokens, project_token_budget=project_token_budget):
                    continue
                return RouteDecision(
                    provider=self.providers[policy.provider],
                    policy=policy,
                    fallback_reason="primary unavailable" if role == "fallback" else None,
                    escalation_reason="high-value ambiguity" if escalation else None,
                )
        raise ProviderFailure(FailureClass.RETRYABLE_TEMPORARY, "No validated Gemini route is presently available; analysis will remain retriable.")

    async def execute_with_failover(self, *, decision_input: dict, invoke) -> tuple[RouteDecision, object]:
        attempted: set[str] = set()
        last_error: ProviderFailure | None = None
        for _ in range(3):
            try:
                decision = self.decide(**decision_input, exclude_models=attempted)
            except ProviderFailure as error:
                raise last_error or error
            attempted.add(decision.policy.model_id)
            escalation = decision.policy.role == "escalation"
            for retry in range(decision.policy.max_retries + 1):
                self.ledger.reserve(
                    decision.policy.model_id,
                    project_id=decision_input["project_id"],
                    is_escalation=escalation,
                    estimated_tokens=decision_input.get("estimated_tokens", 12_000),
                    is_retry=retry > 0,
                )
                try:
                    result = await invoke(decision, retry)
                    self.ledger.record_success(decision.policy.model_id)
                    return decision, result
                except ProviderFailure as error:
                    last_error = error
                    self.ledger.record_failure(decision.policy.model_id, error)
                    if error.failure_class not in {FailureClass.RETRYABLE_RATE_LIMIT, FailureClass.RETRYABLE_TEMPORARY} or retry >= decision.policy.max_retries:
                        break
                    delay = error.retry_after_seconds or min(16, (2**retry) + random.random())
                    await __import__("asyncio").sleep(delay)
                finally:
                    self.ledger.release(decision.policy.model_id)
        raise last_error or ProviderFailure(FailureClass.RETRYABLE_TEMPORARY, "Video routing failed without a provider result.")
