from __future__ import annotations

from enum import StrEnum
from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class IntegrationStatus(StrEnum):
    IMPLEMENTED_UNVERIFIED = "IMPLEMENTED_UNVERIFIED"
    VERIFIED = "VERIFIED"
    BLOCKED_MISSING_CREDENTIALS = "BLOCKED_MISSING_CREDENTIALS"
    FAILED_CAPABILITY_TEST = "FAILED_CAPABILITY_TEST"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parents[3] / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_mode: Literal["development", "test", "production"] = "development"
    use_provider_fixtures: bool = False
    local_worker_enabled: bool = False
    api_prefix: str = "/api"
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:5173"])
    firebase_project_id: str | None = None
    firebase_storage_bucket: str | None = None
    google_cloud_project: str | None = None
    google_cloud_location: str = "us-central1"
    cloud_tasks_queue: str | None = None
    worker_base_url: str | None = None
    worker_invoker_service_account: str | None = None
    gemini_api_key: str | None = None
    gemini_primary_model: str = "gemini-3.5-flash-lite"
    gemini_fallback_model: str = "gemini-3.1-flash-lite"
    gemini_escalation_model: str = "gemini-3.5-flash"
    nvidia_api_key: str | None = None
    nvidia_base_url: str = "https://integrate.api.nvidia.com/v1"
    nvidia_model: str = "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning"
    enable_nvidia_provider: bool = False
    gloo_client_id: str | None = None
    gloo_client_secret: str | None = None
    gloo_base_url: str = "https://platform.ai.gloo.com"
    gloo_endpoint_mode: Literal["responses", "completions_v2", "unselected"] = "unselected"
    gloo_max_candidates_per_project: int = Field(default=2, ge=1, le=10)
    # Omit tradition by default to use Gloo's general Christian perspective.
    # Completions V2 does not allow `not_faith_specific` with auto-routing.
    gloo_tradition: Literal["evangelical", "catholic", "mainline"] | None = None
    yvp_app_key: str | None = None
    yvp_base_url: str = "https://api.youversion.com"
    yvp_allowed_bible_ids: list[int] = Field(default_factory=list)
    development_user_id: str = "local-user"
    prepared_demo_source_hash: str | None = None
    model_policy_path: str = "config/model-policy.json"
    project_video_analysis_token_budget: int = 300_000
    daily_escalation_budget: int = 2

    @model_validator(mode="after")
    def enforce_production_truthfulness(self) -> "Settings":
        if self.app_mode == "production" and self.use_provider_fixtures:
            raise ValueError("Production refuses to start when USE_PROVIDER_FIXTURES=true.")
        if self.app_mode == "production" and self.local_worker_enabled:
            raise ValueError("Production requires Cloud Tasks; LOCAL_WORKER_ENABLED must be false.")
        return self

    def integration_status(self, credential_present: bool) -> IntegrationStatus:
        return (
            IntegrationStatus.IMPLEMENTED_UNVERIFIED
            if credential_present
            else IntegrationStatus.BLOCKED_MISSING_CREDENTIALS
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()
