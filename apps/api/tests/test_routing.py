import pytest

from app.providers.base import FailureClass, ProviderFailure
from app.routing import ModelPolicy, ModelUsageBudgetLedger


def policy() -> ModelPolicy:
    return ModelPolicy("gemini-test", "gemini", "primary", rpm=1, tpm=100, rpd=2, max_retries=1, max_concurrent_calls=1)


def test_usage_ledger_is_conservative_not_provider_quota() -> None:
    ledger = ModelUsageBudgetLedger([policy()])
    assert ledger.is_available("gemini-test", project_id="project", is_escalation=False, escalation_budget=0)
    ledger.reserve("gemini-test", project_id="project", is_escalation=False)
    assert not ledger.is_available("gemini-test", project_id="project", is_escalation=False, escalation_budget=0)


def test_two_rate_limit_failures_open_circuit() -> None:
    ledger = ModelUsageBudgetLedger([policy()])
    failure = ProviderFailure(FailureClass.RETRYABLE_RATE_LIMIT, "429", 90)
    ledger.record_failure("gemini-test", failure)
    ledger.record_failure("gemini-test", failure)
    assert not ledger.is_available("gemini-test", project_id="project", is_escalation=False, escalation_budget=0)


def test_usage_ledger_honours_configured_concurrency() -> None:
    concurrency_policy = ModelPolicy("gemini-concurrent", "gemini", "primary", rpm=3, tpm=100, rpd=3, max_retries=1, max_concurrent_calls=1)
    ledger = ModelUsageBudgetLedger([concurrency_policy])
    ledger.reserve("gemini-concurrent", project_id="project", is_escalation=False)
    assert not ledger.is_available("gemini-concurrent", project_id="another", is_escalation=False, escalation_budget=0)
    ledger.release("gemini-concurrent")
    assert ledger.is_available("gemini-concurrent", project_id="another", is_escalation=False, escalation_budget=0)
