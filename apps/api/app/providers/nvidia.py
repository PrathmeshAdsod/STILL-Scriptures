from __future__ import annotations

from typing import Any

from ..config import Settings
from ..schemas import ModalityStatus, SourceRecord
from .base import FailureClass, PreparedSource, ProviderCapabilities, ProviderFailure, VideoAnalysisRequest, VideoAnalysisResult


class NvidiaVideoProvider:
    """Optional route. It is disabled by default and never a release requirement."""

    name = "nvidia"

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    async def verify_capabilities(self) -> list[ProviderCapabilities]:
        status = self.settings.integration_status(bool(self.settings.nvidia_api_key and self.settings.enable_nvidia_provider)).value
        return [ProviderCapabilities(self.name, self.settings.nvidia_model, True, False, False, False, False, True, status)]

    async def prepare_source(self, source: SourceRecord) -> PreparedSource:
        if not self.settings.enable_nvidia_provider:
            raise ProviderFailure(FailureClass.CONFIGURATION, "NVIDIA video fallback is disabled pending capability validation.")
        raise ProviderFailure(FailureClass.INPUT_INCOMPATIBLE, "NVIDIA media preparation has not passed capability validation.")

    async def analyze_window(self, *, model_id: str, request: VideoAnalysisRequest) -> VideoAnalysisResult:
        raise ProviderFailure(FailureClass.CONFIGURATION, "NVIDIA video analysis is disabled until a real capability spike validates audiovisual support.")

    def classify_failure(self, error: Exception) -> ProviderFailure:
        return ProviderFailure(FailureClass.PERMANENT, str(error))

    def return_provider_metadata(self) -> dict[str, Any]:
        return {"provider": self.name, "enabled": self.settings.enable_nvidia_provider, "optional": True}

    def return_modality_status(self) -> ModalityStatus:
        return ModalityStatus.UNKNOWN
