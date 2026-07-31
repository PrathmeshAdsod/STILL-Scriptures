from __future__ import annotations

import asyncio
import json
import time
from dataclasses import dataclass, field
from typing import Any

import httpx

from ..config import Settings
from ..schemas import AnalysisOutcome, Echo, WindowObservation
from .base import FailureClass, ProviderFailure


@dataclass(frozen=True)
class SacredTimingDecision:
    outcome: AnalysisOutcome
    rationale: str
    selected_reference: str | None = None
    selected_passage_id: str | None = None
    bible_id: int | None = None
    confidence: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


class GlooSacredTimingProvider:
    """Gloo Completions V2 implementation with OAuth2 and forced function-call structure.

    The Gloo Responses candidate remains unselected until its official contract is
    independently verified during Milestone 1B; this code never guesses one.
    """

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._access_token: str | None = None
        self._token_expires_at: float = 0
        self._token_lock = asyncio.Lock()

    @property
    def status(self) -> str:
        return self.settings.integration_status(bool(self.settings.gloo_client_id and self.settings.gloo_client_secret)).value

    def _ensure_configured(self) -> None:
        if self.settings.gloo_endpoint_mode == "unselected":
            raise ProviderFailure(FailureClass.CONFIGURATION, "Gloo endpoint mode is unselected; Milestone 1B must choose it.")
        if self.settings.gloo_endpoint_mode == "responses":
            raise ProviderFailure(FailureClass.CONFIGURATION, "Gloo Responses API has no verified official request contract in this codebase yet; select it only after the capability spike implements and passes that contract.")
        if not self.settings.gloo_client_id or not self.settings.gloo_client_secret:
            raise ProviderFailure(FailureClass.CONFIGURATION, "Gloo client credentials are missing.")

    def ensure_configuration(self) -> None:
        """Fail before analysis rather than allowing a no-op path to look complete."""
        self._ensure_configured()

    async def decide(self, *, observation: WindowObservation, video_context: str) -> SacredTimingDecision:
        tool_schema = {
            "type": "function",
            "function": {
                "name": "record_sacred_timing_decision",
                "description": "Return the only machine-readable Sacred Timing decision for one audiovisual observation.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "outcome": {"type": "string", "enum": [item.value for item in AnalysisOutcome]},
                        "rationale": {"type": "string"},
                        "confidence": {"type": "number"},
                        "selected_reference": {"type": "string"},
                        "selected_passage_id": {"type": "string", "description": "USFM passage ID, e.g. JHN.3.16. Required only for ACCEPT."},
                        "bible_id": {"type": "integer", "description": "Must be one of the allowed YouVersion Bible IDs; required only for ACCEPT."},
                    },
                    "required": ["outcome", "rationale", "confidence"],
                },
            },
        }
        result, metadata = await self._call_tool(
            system=(
                "You make Sacred Timing decisions for STILL. You may accept a reflection only when the audiovisual "
                "observation provides sufficient, non-sensitive evidence and Scripture is not forced. Prefer NO_ECHO, "
                "HOLD, ABSTAIN, NEEDS_MORE_CONTEXT, SAFETY_SENSITIVE, or REJECT_ALL_SCRIPTURE. Never write Bible text. "
                "For ACCEPT, provide a human reference, a USFM passage ID, and only an ID from allowed_bible_ids."
            ),
            user_payload={
                "observation": observation.model_dump(mode="json"),
                "presentation_context": video_context,
                "allowed_bible_ids": self.settings.yvp_allowed_bible_ids,
            },
            tool=tool_schema,
        )
        try:
            decision = SacredTimingDecision(
                outcome=AnalysisOutcome(result["outcome"]),
                rationale=str(result["rationale"]),
                confidence=float(result["confidence"]),
                selected_reference=result.get("selected_reference"),
                selected_passage_id=result.get("selected_passage_id"),
                bible_id=int(result["bible_id"]) if result.get("bible_id") is not None else None,
                metadata=metadata,
            )
        except (KeyError, TypeError, ValueError) as error:
            raise ProviderFailure(FailureClass.INVALID_RESPONSE, "Gloo Sacred Timing tool arguments did not meet the schema.") from error
        if decision.outcome == AnalysisOutcome.ACCEPT:
            if not decision.selected_reference or not decision.selected_passage_id or decision.bible_id not in self.settings.yvp_allowed_bible_ids:
                raise ProviderFailure(FailureClass.INVALID_RESPONSE, "Gloo accepted a passage without an approved YouVersion Bible ID and USFM passage ID.")
        return decision

    async def verify_passage(self, *, echo: Echo, canonical_text: str, attribution: str) -> tuple[AnalysisOutcome, str, dict[str, Any]]:
        tool_schema = {
            "type": "function",
            "function": {
                "name": "record_passage_verification",
                "description": "Verify whether canonical Scripture is appropriately grounded in the observed tension without rewriting canonical text.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "outcome": {"type": "string", "enum": [AnalysisOutcome.ACCEPT.value, AnalysisOutcome.REJECT_ALL_SCRIPTURE.value, AnalysisOutcome.ABSTAIN.value]},
                        "rationale": {"type": "string"},
                    },
                    "required": ["outcome", "rationale"],
                },
            },
        }
        result, metadata = await self._call_tool(
            system="You verify a proposed STILL reflection. Respect the canonical text exactly; return ACCEPT only when the connection is grounded, non-forced, and does not overstate authorial intent.",
            user_payload={"tension": echo.tension, "scene_context": echo.scene_context, "reference": echo.scripture_reference, "canonical_text": canonical_text, "attribution": attribution},
            tool=tool_schema,
        )
        try:
            return AnalysisOutcome(result["outcome"]), str(result["rationale"]), metadata
        except (KeyError, ValueError, TypeError) as error:
            raise ProviderFailure(FailureClass.INVALID_RESPONSE, "Gloo passage-verification tool arguments did not meet the schema.") from error

    async def _get_access_token(self) -> str:
        self._ensure_configured()
        if self._access_token and time.monotonic() < self._token_expires_at - 60:
            return self._access_token
        async with self._token_lock:
            if self._access_token and time.monotonic() < self._token_expires_at - 60:
                return self._access_token
            try:
                async with httpx.AsyncClient(timeout=20) as client:
                    response = await client.post(
                        f"{self.settings.gloo_base_url.rstrip('/')}/oauth2/token",
                        data={"grant_type": "client_credentials", "scope": "api/access"},
                        auth=(self.settings.gloo_client_id, self.settings.gloo_client_secret),
                        headers={"Content-Type": "application/x-www-form-urlencoded"},
                    )
                if response.status_code >= 400:
                    raise ProviderFailure(FailureClass.AUTHENTICATION if response.status_code in {401, 403} else FailureClass.RETRYABLE_TEMPORARY, f"Gloo OAuth token exchange returned {response.status_code}.")
                payload = response.json()
                token = payload.get("access_token")
                expires_in = int(payload.get("expires_in", 0))
                if not token or expires_in <= 60:
                    raise ProviderFailure(FailureClass.INVALID_RESPONSE, "Gloo OAuth response omitted a usable bearer token.")
                self._access_token = str(token)
                self._token_expires_at = time.monotonic() + expires_in
                return self._access_token
            except httpx.TimeoutException as error:
                raise ProviderFailure(FailureClass.RETRYABLE_TEMPORARY, "Gloo OAuth token exchange timed out.") from error

    async def _call_tool(self, *, system: str, user_payload: dict[str, Any], tool: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
        self._ensure_configured()
        for attempt in range(2):
            token = await self._get_access_token()
            payload = self._build_request_payload(system=system, user_payload=user_payload, tool=tool)
            try:
                async with httpx.AsyncClient(timeout=45) as client:
                    response = await client.post(
                        f"{self.settings.gloo_base_url.rstrip('/')}/ai/v2/chat/completions",
                        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
                        json=payload,
                    )
                if response.status_code == 401 and attempt == 0:
                    self._access_token = None
                    self._token_expires_at = 0
                    continue
                if response.status_code == 429:
                    raise ProviderFailure(FailureClass.RETRYABLE_RATE_LIMIT, "Gloo rate-limited the request.", self._retry_after(response))
                if response.status_code >= 500:
                    raise ProviderFailure(FailureClass.RETRYABLE_TEMPORARY, f"Gloo returned {response.status_code}.")
                if response.status_code >= 400:
                    raise ProviderFailure(FailureClass.PERMANENT, f"Gloo returned {response.status_code}: {response.text[:400]}")
                response_body = response.json()
                function = response_body["choices"][0]["message"]["tool_calls"][0]["function"]
                arguments = json.loads(function["arguments"])
                metadata = {key: response_body.get(key) for key in ("id", "model", "provider", "model_family", "routing_mechanism", "routing_tier", "routing_confidence", "tradition", "usage")}
                return arguments, metadata
            except httpx.TimeoutException as error:
                raise ProviderFailure(FailureClass.RETRYABLE_TEMPORARY, "Gloo timed out.") from error
            except (KeyError, IndexError, TypeError, json.JSONDecodeError) as error:
                raise ProviderFailure(FailureClass.INVALID_RESPONSE, "Gloo did not return the required tool call.") from error
        raise ProviderFailure(FailureClass.AUTHENTICATION, "Gloo rejected a refreshed bearer token.")

    def _build_request_payload(self, *, system: str, user_payload: dict[str, Any], tool: dict[str, Any]) -> dict[str, Any]:
        """Build a documented Completions V2 request with one routing mechanism.

        Omitting `tradition` uses Gloo's general Christian perspective. The
        explicit supported traditions remain compatible with auto-routing.
        """
        payload: dict[str, Any] = {
            "auto_routing": True,
            "temperature": 0,
            "max_tokens": 800,
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": json.dumps(user_payload)}],
            "tools": [tool],
            "tool_choice": "required",
        }
        if self.settings.gloo_tradition is not None:
            payload["tradition"] = self.settings.gloo_tradition
        return payload

    @staticmethod
    def _retry_after(response: httpx.Response) -> float | None:
        value = response.headers.get("Retry-After")
        return float(value) if value and value.isdigit() else None
