from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, Protocol

from ..schemas import ModalityStatus, NarrativeState, SourceRecord, WindowObservation


class FailureClass(StrEnum):
    RETRYABLE_RATE_LIMIT = "RETRYABLE_RATE_LIMIT"
    RETRYABLE_TEMPORARY = "RETRYABLE_TEMPORARY"
    INPUT_INCOMPATIBLE = "INPUT_INCOMPATIBLE"
    SAFETY_BLOCK = "SAFETY_BLOCK"
    AUTHENTICATION = "AUTHENTICATION"
    CONFIGURATION = "CONFIGURATION"
    INVALID_RESPONSE = "INVALID_RESPONSE"
    PERMANENT = "PERMANENT"


class ProviderFailure(RuntimeError):
    def __init__(self, failure_class: FailureClass, message: str, retry_after_seconds: float | None = None):
        super().__init__(message)
        self.failure_class = failure_class
        self.retry_after_seconds = retry_after_seconds


@dataclass(frozen=True)
class ProviderCapabilities:
    provider: str
    model_id: str
    accepts_upload: bool
    accepts_youtube_url: bool
    supports_audio_in_video: bool
    supports_visual_in_video: bool
    supports_clipping: bool
    supports_structured_output: bool
    status: str


@dataclass(frozen=True)
class PreparedSource:
    provider: str
    source_reference: str
    mime_type: str | None
    reuse_key: str


@dataclass(frozen=True)
class VideoAnalysisRequest:
    source: SourceRecord
    prepared_source: PreparedSource
    start_offset_seconds: float
    end_offset_seconds: float
    narrative_state: NarrativeState
    prompt_version: str
    purpose: str = "ordinary"


@dataclass(frozen=True)
class VideoAnalysisResult:
    observations: list[WindowObservation]
    narrative_state: NarrativeState
    modality_status: ModalityStatus
    confidence: float
    token_usage: dict[str, int] | None = None
    raw_provider_metadata: dict[str, Any] = field(default_factory=dict)


class VideoUnderstandingProvider(Protocol):
    name: str

    async def verify_capabilities(self) -> list[ProviderCapabilities]: ...
    async def prepare_source(self, source: SourceRecord) -> PreparedSource: ...
    async def analyze_window(self, *, model_id: str, request: VideoAnalysisRequest) -> VideoAnalysisResult: ...
    def classify_failure(self, error: Exception) -> ProviderFailure: ...
    def return_provider_metadata(self) -> dict[str, Any]: ...
    def return_modality_status(self) -> ModalityStatus: ...
