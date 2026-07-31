from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any, Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator


class SourceKind(StrEnum):
    UPLOAD = "upload"
    YOUTUBE = "youtube"
    PREPARED_DEMO = "prepared_demo"


class ProjectStatus(StrEnum):
    DRAFT = "DRAFT"
    SOURCE_PENDING = "SOURCE_PENDING"
    QUEUED = "QUEUED"
    PREPARING = "PREPARING"
    ANALYZING = "ANALYZING"
    GROUNDING = "GROUNDING"
    READY = "READY"
    READY_NO_ECHO = "READY_NO_ECHO"
    FAILED_RETRIABLE = "FAILED_RETRIABLE"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class AnalysisOutcome(StrEnum):
    NO_ECHO = "NO_ECHO"
    HOLD = "HOLD"
    ABSTAIN = "ABSTAIN"
    NEEDS_MORE_CONTEXT = "NEEDS_MORE_CONTEXT"
    SAFETY_SENSITIVE = "SAFETY_SENSITIVE"
    DEGRADED_MODALITY = "DEGRADED_MODALITY"
    PROVIDER_TEMPORARILY_UNAVAILABLE = "PROVIDER_TEMPORARILY_UNAVAILABLE"
    REJECT_ALL_SCRIPTURE = "REJECT_ALL_SCRIPTURE"
    ACCEPT = "ACCEPT"


class AccountPlan(StrEnum):
    FREE = "FREE"
    ACCESS = "ACCESS"


class AccountStatus(BaseModel):
    plan: AccountPlan
    max_video_duration_seconds: int
    analysis_limit: int
    analyses_used: int
    analyses_remaining: int
    usage_period: Literal["lifetime", "day"]
    usage_resets_at: datetime | None = None


class AccessCodeRequest(BaseModel):
    code: str = Field(min_length=8, max_length=200)


class ModalityStatus(StrEnum):
    FULL_AUDIOVISUAL = "FULL_AUDIOVISUAL"
    DEGRADED_AUDIO_MISSING = "DEGRADED_AUDIO_MISSING"
    DEGRADED_VISUAL_MISSING = "DEGRADED_VISUAL_MISSING"
    UNKNOWN = "UNKNOWN"


class SourceCreateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=180)


class ProjectCreateResponse(BaseModel):
    project_id: UUID
    status: ProjectStatus


class YoutubeSourceRequest(BaseModel):
    url: HttpUrl
    title: str | None = Field(default=None, max_length=180)
    duration_seconds: float | None = Field(default=None, gt=0, le=43_200)

    @field_validator("url")
    @classmethod
    def valid_youtube_host(cls, url: HttpUrl) -> HttpUrl:
        if url.host not in {"youtube.com", "www.youtube.com", "m.youtube.com", "youtu.be"}:
            raise ValueError("Only public YouTube URLs are supported.")
        return url


class UploadCompleteRequest(BaseModel):
    storage_path: str = Field(min_length=3, max_length=500)
    original_filename: str = Field(min_length=1, max_length=255)
    content_type: str = Field(pattern=r"^video/[a-zA-Z0-9.+-]+$")
    size_bytes: int = Field(gt=0, le=10_737_418_240)
    sha256: str = Field(pattern=r"^[a-fA-F0-9]{64}$")
    duration_seconds: float | None = Field(default=None, gt=0, le=43_200)
    has_audio: bool | None = None
    has_video: bool | None = None


class SourceRecord(BaseModel):
    kind: SourceKind
    storage_path: str | None = None
    public_url: str | None = None
    youtube_video_id: str | None = None
    source_hash: str | None = None
    title: str
    duration_seconds: float | None = None
    content_type: str | None = None
    original_filename: str | None = None
    has_audio: bool | None = None
    has_video: bool | None = None
    # Provider-owned references are opaque handles, never public source URLs.
    # They let a retried causal job reuse a registered source instead of
    # registering or uploading the full video for each window.
    provider_references: dict[str, str] = Field(default_factory=dict)
    provider_mime_types: dict[str, str] = Field(default_factory=dict)
    prepared_demo: bool = False


class Progress(BaseModel):
    completed_windows: int = 0
    total_windows: int | None = None
    stage: Literal["source_received", "preparing_media", "understanding_story", "grounding_reflection", "ready", "failed"] = "source_received"

    @property
    def honest_percent(self) -> int | None:
        if self.total_windows is None or self.total_windows <= 0:
            return None
        return int((self.completed_windows / self.total_windows) * 100)


class Project(BaseModel):
    model_config = ConfigDict(use_enum_values=False)
    id: UUID = Field(default_factory=uuid4)
    owner_id: str
    title: str
    status: ProjectStatus = ProjectStatus.DRAFT
    source: SourceRecord | None = None
    progress: Progress = Field(default_factory=Progress)
    current_job_id: UUID | None = None
    failure_code: str | None = None
    failure_message: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class StartAnalysisResponse(BaseModel):
    job_id: UUID
    status: ProjectStatus


class AnalysisJob(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    project_id: UUID
    owner_id: str
    status: Literal["QUEUED", "RUNNING", "COMPLETED", "FAILED", "CANCELLED"] = "QUEUED"
    idempotency_key: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class Evidence(BaseModel):
    observed_spoken_content: str | None = None
    observed_visual_action: str | None = None
    observed_voice_or_delivery: str | None = None
    observed_audience_response: str | None = None
    supporting_evidence: list[str] = Field(default_factory=list)
    contradicting_evidence: list[str] = Field(default_factory=list)


class WindowObservation(BaseModel):
    event_start_seconds: float = Field(ge=0)
    event_end_seconds: float = Field(ge=0)
    interpretation: str
    evidence: Evidence
    confidence: float = Field(ge=0, le=1)
    needs_more_context: bool = False
    outcome: AnalysisOutcome = AnalysisOutcome.HOLD
    candidate_tensions: list[str] = Field(default_factory=list)


class NarrativeState(BaseModel):
    version: int
    known_characters: list[str] = Field(default_factory=list)
    revealed_facts: list[str] = Field(default_factory=list)
    relationships: list[str] = Field(default_factory=list)
    unresolved_questions: list[str] = Field(default_factory=list)
    observed_events: list[str] = Field(default_factory=list)
    content_mode: str = "unknown"
    uncertainties: list[str] = Field(default_factory=list)


class WindowProvenance(BaseModel):
    window_id: UUID = Field(default_factory=uuid4)
    project_id: UUID
    start_offset_seconds: float
    end_offset_seconds: float
    provider: str
    model_id: str
    prompt_version: str
    pipeline_version: str
    input_narrative_state_version: int
    output_narrative_state_version: int
    retry_count: int = 0
    fallback_reason: str | None = None
    escalation_reason: str | None = None
    modality_status: ModalityStatus = ModalityStatus.UNKNOWN
    confidence: float | None = None
    latency_ms: int | None = None
    token_usage: dict[str, int] | None = None
    completion_timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))


class ReflectionCandidateStatus(StrEnum):
    PENDING = "PENDING"
    NO_ECHO = "NO_ECHO"
    REJECTED = "REJECTED"
    ECHO_PERSISTED = "ECHO_PERSISTED"


class ReflectionCandidate(BaseModel):
    """A durable, spoiler-bounded input to Sacred Timing, never a generated reflection."""

    id: UUID = Field(default_factory=uuid4)
    project_id: UUID
    window_id: UUID
    observation_index: int = Field(ge=0)
    knowledge_cutoff_seconds: float = Field(ge=0)
    observation: WindowObservation
    video_provenance: WindowProvenance
    status: ReflectionCandidateStatus = ReflectionCandidateStatus.PENDING
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class Echo(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    project_id: UUID
    candidate_id: UUID | None = None
    knowledge_cutoff_seconds: float
    first_view_interpretation: str
    after_story_interpretation: str | None = None
    tension: str
    scene_context: str
    outcome: AnalysisOutcome
    scripture_reference: str | None = None
    bible_id: int | None = None
    bible_version: str | None = None
    exact_scripture_text: str | None = None
    copyright_attribution: str | None = None
    connection_explanation: str | None = None
    confidence: float = Field(ge=0, le=1)
    provider_provenance: dict[str, Any] = Field(default_factory=dict)


class ViewingSessionCreateResponse(BaseModel):
    session_id: UUID


class ViewingSessionPatch(BaseModel):
    ranges: list[tuple[float, float]]
    duration_seconds: float = Field(gt=0)
    ended_naturally: bool = False


class ViewingSession(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    project_id: UUID
    owner_id: str
    watched_ranges: list[tuple[float, float]] = Field(default_factory=list)
    contiguous_frontier_seconds: float = 0
    story_complete: bool = False
    ended_naturally: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class ProjectLibraryItem(BaseModel):
    project: Project
    latest_session: ViewingSession | None = None


class PublicProjectResponse(BaseModel):
    project: Project
    echoes: list[Echo] = Field(default_factory=list)
