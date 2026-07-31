from __future__ import annotations

from contextlib import asynccontextmanager
from uuid import UUID

from fastapi import Depends, FastAPI, Header, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .auth import current_user
from .config import Settings, get_settings
from .errors import ErrorCode, api_error, not_found
from .repositories import FirestoreDataStore, InMemoryDataStore
from .routing import ModelUsageBudgetLedger, VideoModelRouter, load_model_policies
from .schemas import (
    AnalysisJob,
    Project,
    ProjectCreateResponse,
    ProjectStatus,
    PublicProjectResponse,
    SourceCreateRequest,
    SourceKind,
    SourceRecord,
    StartAnalysisResponse,
    UploadCompleteRequest,
    ViewingSession,
    ViewingSessionCreateResponse,
    ViewingSessionPatch,
    YoutubeSourceRequest,
)
from .tasks import CloudTasksEnqueuer, LocalTaskEnqueuer
from .media import delete_uploaded_source, validate_upload_storage_path
from .watching import contiguous_frontier, normalise_ranges, qualifies_for_story_complete
from .worker import CausalAnalysisWorker
from .providers import GeminiVideoProvider, GlooSacredTimingProvider, NvidiaVideoProvider, YouVersionClient


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    if settings.app_mode == "production" and not settings.firebase_project_id:
        raise RuntimeError("Production requires FIREBASE_PROJECT_ID and Firestore.")
    store = FirestoreDataStore(settings.firebase_project_id) if settings.firebase_project_id else InMemoryDataStore()
    providers = {"gemini": GeminiVideoProvider(settings)}
    if settings.enable_nvidia_provider:
        providers["nvidia"] = NvidiaVideoProvider(settings)
    policies = load_model_policies(settings)
    router = VideoModelRouter(providers, ModelUsageBudgetLedger(policies), policies, settings)
    worker = CausalAnalysisWorker(store=store, router=router, gloo=GlooSacredTimingProvider(settings), youversion=YouVersionClient(settings))
    app.state.settings = settings
    app.state.store = store
    app.state.worker = worker
    app.state.enqueuer = CloudTasksEnqueuer(settings) if settings.app_mode == "production" else LocalTaskEnqueuer(worker, settings.local_worker_enabled)
    yield


app = FastAPI(title="STILL API", version="0.1.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=get_settings().cors_origins, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])


@app.middleware("http")
async def request_id(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Request-Id"] = request.headers.get("X-Request-Id", __import__("uuid").uuid4().hex)
    return response


def store_for(request: Request):
    return request.app.state.store


async def owned_project(request: Request, project_id: UUID, user_id: str) -> Project:
    project = await store_for(request).get_project(project_id)
    if not project:
        raise not_found()
    if project.owner_id != user_id:
        raise api_error(ErrorCode.FORBIDDEN, "You do not have access to this project.", 403)
    return project


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}


@app.get("/ready")
async def ready(request: Request) -> dict:
    settings: Settings = request.app.state.settings
    return {"status": "ready", "app_mode": settings.app_mode, "fixtures_enabled": settings.use_provider_fixtures}


@app.post("/api/projects", response_model=ProjectCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_project(payload: SourceCreateRequest, request: Request, user_id: str = Depends(current_user)) -> ProjectCreateResponse:
    project = Project(owner_id=user_id, title=payload.title, status=ProjectStatus.SOURCE_PENDING)
    await store_for(request).put_project(project)
    return ProjectCreateResponse(project_id=project.id, status=project.status)


@app.post("/api/projects/{project_id}/source/youtube")
async def set_youtube_source(project_id: UUID, payload: YoutubeSourceRequest, request: Request, user_id: str = Depends(current_user)) -> Project:
    project = await owned_project(request, project_id, user_id)
    if project.status not in {ProjectStatus.DRAFT, ProjectStatus.SOURCE_PENDING, ProjectStatus.FAILED_RETRIABLE, ProjectStatus.FAILED}:
        raise api_error(ErrorCode.INVALID_STATE, "This project source can no longer be changed.", 409)
    project.source = SourceRecord(kind=SourceKind.YOUTUBE, public_url=str(payload.url), title=payload.title or project.title, duration_seconds=payload.duration_seconds)
    project.status = ProjectStatus.SOURCE_PENDING
    await store_for(request).put_project(project)
    return project


@app.post("/api/projects/{project_id}/source/upload-complete")
async def upload_complete(project_id: UUID, payload: UploadCompleteRequest, request: Request, user_id: str = Depends(current_user)) -> Project:
    project = await owned_project(request, project_id, user_id)
    if project.status not in {ProjectStatus.DRAFT, ProjectStatus.SOURCE_PENDING, ProjectStatus.FAILED_RETRIABLE, ProjectStatus.FAILED}:
        raise api_error(ErrorCode.INVALID_STATE, "This project source can no longer be changed.", 409)
    try:
        validate_upload_storage_path(
            storage_path=payload.storage_path,
            project_id=project.id,
            expected_bucket=request.app.state.settings.firebase_storage_bucket,
        )
    except Exception as error:
        raise api_error(ErrorCode.INVALID_SOURCE, str(error), 422) from error
    project.source = SourceRecord(
        kind=SourceKind.UPLOAD,
        storage_path=payload.storage_path,
        source_hash=payload.sha256,
        title=project.title,
        content_type=payload.content_type,
        original_filename=payload.original_filename,
        duration_seconds=payload.duration_seconds,
        has_audio=payload.has_audio,
        has_video=payload.has_video,
    )
    project.status = ProjectStatus.SOURCE_PENDING
    await store_for(request).put_project(project)
    return project


@app.post("/api/projects/{project_id}/analysis", response_model=StartAnalysisResponse)
async def start_analysis(project_id: UUID, request: Request, idempotency_key: str = Header(alias="Idempotency-Key"), user_id: str = Depends(current_user)) -> StartAnalysisResponse:
    project = await owned_project(request, project_id, user_id)
    if not project.source:
        raise api_error(ErrorCode.INVALID_SOURCE, "Add a source before requesting analysis.", 409)
    existing = await store_for(request).find_job_by_key(project_id, idempotency_key)
    if existing:
        return StartAnalysisResponse(job_id=existing.id, status=project.status)
    if project.status in {ProjectStatus.READY, ProjectStatus.READY_NO_ECHO}:
        raise api_error(ErrorCode.INVALID_STATE, "This project has already completed analysis.", 409)
    if project.status in {ProjectStatus.QUEUED, ProjectStatus.PREPARING, ProjectStatus.ANALYZING, ProjectStatus.GROUNDING}:
        raise api_error(ErrorCode.INVALID_STATE, "Analysis is already in progress for this project.", 409)
    job = AnalysisJob(project_id=project.id, owner_id=user_id, idempotency_key=idempotency_key)
    project.current_job_id = job.id
    project.status = ProjectStatus.QUEUED
    project.failure_code = None
    project.failure_message = None
    await store_for(request).put_job(job)
    await store_for(request).put_project(project)
    try:
        await request.app.state.enqueuer.enqueue_analysis(job.id)
    except RuntimeError as error:
        job.status = "FAILED"
        project.status = ProjectStatus.FAILED_RETRIABLE
        project.failure_code = "TASK_CONFIGURATION"
        project.failure_message = str(error)[:500]
        project.progress.stage = "failed"
        await store_for(request).put_job(job)
        await store_for(request).put_project(project)
        raise api_error(ErrorCode.ANALYSIS_UNAVAILABLE, "Analysis is temporarily unavailable because the worker is not configured.", 503) from error
    return StartAnalysisResponse(job_id=job.id, status=project.status)


@app.post("/internal/jobs/{job_id}", status_code=status.HTTP_202_ACCEPTED)
async def execute_task(job_id: UUID, request: Request, x_cloudtasks_taskname: str | None = Header(default=None)) -> dict:
    if request.app.state.settings.app_mode == "production" and not x_cloudtasks_taskname:
        raise api_error(ErrorCode.FORBIDDEN, "This endpoint only accepts Cloud Tasks requests.", 403)
    await request.app.state.worker.run(job_id)
    return {"accepted": True}


@app.post("/api/projects/{project_id}/analysis/cancel")
async def cancel_analysis(project_id: UUID, request: Request, user_id: str = Depends(current_user)) -> Project:
    project = await owned_project(request, project_id, user_id)
    if project.current_job_id:
        job = await store_for(request).get_job(project.current_job_id)
        if job and job.status in {"QUEUED", "RUNNING"}:
            job.status = "CANCELLED"
            await store_for(request).put_job(job)
    project.status = ProjectStatus.CANCELLED
    await store_for(request).put_project(project)
    return project


@app.get("/api/projects/{project_id}", response_model=PublicProjectResponse)
async def get_project(project_id: UUID, request: Request, user_id: str = Depends(current_user)) -> PublicProjectResponse:
    project = await owned_project(request, project_id, user_id)
    return PublicProjectResponse(project=project, echoes=[])


@app.get("/api/projects/{project_id}/status")
async def get_status(project_id: UUID, request: Request, user_id: str = Depends(current_user)) -> Project:
    return await owned_project(request, project_id, user_id)


@app.post("/api/projects/{project_id}/viewing-sessions", response_model=ViewingSessionCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_viewing_session(project_id: UUID, request: Request, user_id: str = Depends(current_user)) -> ViewingSessionCreateResponse:
    project = await owned_project(request, project_id, user_id)
    if project.status not in {ProjectStatus.READY, ProjectStatus.READY_NO_ECHO}:
        raise api_error(ErrorCode.INVALID_STATE, "A viewing session starts only after the story is ready.", 409)
    session = ViewingSession(project_id=project.id, owner_id=user_id)
    await store_for(request).put_session(session)
    return ViewingSessionCreateResponse(session_id=session.id)


@app.patch("/api/projects/{project_id}/viewing-sessions/{session_id}")
async def update_viewing_session(project_id: UUID, session_id: UUID, payload: ViewingSessionPatch, request: Request, user_id: str = Depends(current_user)) -> ViewingSession:
    await owned_project(request, project_id, user_id)
    session = await store_for(request).get_session(session_id)
    if not session or session.project_id != project_id or session.owner_id != user_id:
        raise not_found("The viewing session does not exist.")
    session.watched_ranges = normalise_ranges(session.watched_ranges + payload.ranges, payload.duration_seconds)
    session.contiguous_frontier_seconds = contiguous_frontier(session.watched_ranges)
    session.ended_naturally = session.ended_naturally or payload.ended_naturally
    session.story_complete = qualifies_for_story_complete(ranges=session.watched_ranges, duration_seconds=payload.duration_seconds, ended_naturally=session.ended_naturally)
    await store_for(request).put_session(session)
    return session


@app.get("/api/projects/{project_id}/echoes")
async def get_available_echoes(project_id: UUID, session_id: UUID, request: Request, user_id: str = Depends(current_user)) -> list:
    await owned_project(request, project_id, user_id)
    session = await store_for(request).get_session(session_id)
    if not session or session.owner_id != user_id:
        raise not_found("The viewing session does not exist.")
    echoes = await store_for(request).echoes(project_id)
    return [echo for echo in echoes if echo.knowledge_cutoff_seconds <= session.contiguous_frontier_seconds + 1]


@app.post("/api/projects/{project_id}/story-reflection")
async def story_reflection(project_id: UUID, session_id: UUID, request: Request, user_id: str = Depends(current_user)) -> list:
    await owned_project(request, project_id, user_id)
    session = await store_for(request).get_session(session_id)
    if not session or session.owner_id != user_id or not session.story_complete:
        raise api_error(ErrorCode.INVALID_STATE, "Story Complete requires contiguous watched coverage and a natural ending.", 409)
    return await store_for(request).echoes(project_id)


@app.delete("/api/projects/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(project_id: UUID, request: Request, user_id: str = Depends(current_user)) -> Response:
    project = await owned_project(request, project_id, user_id)
    if project.current_job_id:
        job = await store_for(request).get_job(project.current_job_id)
        if job and job.status in {"QUEUED", "RUNNING"}:
            job.status = "CANCELLED"
            await store_for(request).put_job(job)
    if project.source:
        await delete_uploaded_source(project.source)
    await store_for(request).delete_project(project_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
