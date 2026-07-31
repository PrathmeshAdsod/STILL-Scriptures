import pytest
from pydantic import ValidationError

from app.config import Settings
from app.providers.base import FailureClass, ProviderFailure
from app.providers.gemini import GeminiVideoProvider
from app.schemas import NarrativeState, SourceKind, SourceRecord


def test_production_refuses_fixtures() -> None:
    with pytest.raises(ValidationError):
        Settings(app_mode="production", use_provider_fixtures=True, access_coupon_code="TEST-ACCESS-CODE")


def test_production_refuses_local_worker() -> None:
    with pytest.raises(ValidationError):
        Settings(app_mode="production", local_worker_enabled=True, access_coupon_code="TEST-ACCESS-CODE")


def test_production_requires_authoritative_youtube_validation() -> None:
    with pytest.raises(ValidationError):
        Settings(app_mode="production", youtube_api_key=None, gloo_max_candidates_per_project=1, access_coupon_code="TEST-ACCESS-CODE")


def test_production_refuses_more_than_one_gloo_candidate() -> None:
    with pytest.raises(ValidationError):
        Settings(app_mode="production", youtube_api_key="restricted-key", gloo_max_candidates_per_project=2, access_coupon_code="TEST-ACCESS-CODE")


def test_production_requires_private_access_code() -> None:
    with pytest.raises(ValidationError):
        Settings(app_mode="production", youtube_api_key="restricted-key", access_coupon_code=None)


def test_missing_gemini_credentials_fail_transparently() -> None:
    with pytest.raises(ProviderFailure) as error:
        GeminiVideoProvider(Settings(gemini_api_key=None))._client()
    assert error.value.failure_class == FailureClass.CONFIGURATION


@pytest.mark.asyncio
async def test_registered_gemini_source_is_reused_without_another_registration() -> None:
    provider = GeminiVideoProvider(Settings(gemini_api_key="test-key"))
    source = SourceRecord(
        kind=SourceKind.UPLOAD,
        storage_path="gs://still-test/projects/project/source.mp4",
        content_type="video/mp4",
        source_hash="a" * 64,
        title="Test source",
        provider_references={"gemini": "https://generativelanguage.googleapis.com/v1beta/files/reused"},
        provider_mime_types={"gemini": "video/mp4"},
    )

    prepared = await provider.prepare_source(source)

    assert prepared.source_reference.endswith("/reused")
    assert prepared.mime_type == "video/mp4"


def test_gemini_causal_state_cannot_rewrite_a_revealed_fact() -> None:
    with pytest.raises(ProviderFailure) as error:
        GeminiVideoProvider._assert_immutable_state(
            previous=NarrativeState(version=1, revealed_facts=["Mara lost the letter"]),
            next_state=NarrativeState(version=2, revealed_facts=["Mara found the letter"]),
        )
    assert error.value.failure_class == FailureClass.INVALID_RESPONSE
