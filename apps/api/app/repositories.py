from __future__ import annotations

from collections import defaultdict
from datetime import UTC, datetime
from typing import Protocol
from uuid import UUID

from .schemas import AnalysisJob, Echo, NarrativeState, Project, ReflectionCandidate, ViewingSession, WindowProvenance


class DataStore(Protocol):
    async def put_project(self, project: Project) -> None: ...
    async def get_project(self, project_id: UUID) -> Project | None: ...
    async def put_job(self, job: AnalysisJob) -> None: ...
    async def get_job(self, job_id: UUID) -> AnalysisJob | None: ...
    async def find_job_by_key(self, project_id: UUID, key: str) -> AnalysisJob | None: ...
    async def put_state(self, project_id: UUID, state: NarrativeState) -> None: ...
    async def latest_state(self, project_id: UUID) -> NarrativeState | None: ...
    async def put_window(self, window: WindowProvenance) -> None: ...
    async def windows(self, project_id: UUID) -> list[WindowProvenance]: ...
    async def put_candidate(self, candidate: ReflectionCandidate) -> None: ...
    async def candidates(self, project_id: UUID) -> list[ReflectionCandidate]: ...
    async def put_echo(self, echo: Echo) -> None: ...
    async def echoes(self, project_id: UUID) -> list[Echo]: ...
    async def put_session(self, session: ViewingSession) -> None: ...
    async def get_session(self, session_id: UUID) -> ViewingSession | None: ...
    async def delete_project(self, project_id: UUID) -> None: ...


class InMemoryDataStore:
    """Development/test store. It is never selected by production settings."""

    def __init__(self) -> None:
        self.projects: dict[UUID, Project] = {}
        self.jobs: dict[UUID, AnalysisJob] = {}
        self.jobs_by_key: dict[tuple[UUID, str], UUID] = {}
        self.states: dict[UUID, list[NarrativeState]] = defaultdict(list)
        self.window_records: dict[UUID, list[WindowProvenance]] = defaultdict(list)
        self.candidate_records: dict[UUID, list[ReflectionCandidate]] = defaultdict(list)
        self.echo_records: dict[UUID, list[Echo]] = defaultdict(list)
        self.sessions: dict[UUID, ViewingSession] = {}

    async def put_project(self, project: Project) -> None:
        project.updated_at = datetime.now(UTC)
        self.projects[project.id] = project

    async def get_project(self, project_id: UUID) -> Project | None:
        return self.projects.get(project_id)

    async def put_job(self, job: AnalysisJob) -> None:
        job.updated_at = datetime.now(UTC)
        self.jobs[job.id] = job
        self.jobs_by_key[(job.project_id, job.idempotency_key)] = job.id

    async def get_job(self, job_id: UUID) -> AnalysisJob | None:
        return self.jobs.get(job_id)

    async def find_job_by_key(self, project_id: UUID, key: str) -> AnalysisJob | None:
        job_id = self.jobs_by_key.get((project_id, key))
        return self.jobs.get(job_id) if job_id else None

    async def put_state(self, project_id: UUID, state: NarrativeState) -> None:
        states = self.states[project_id]
        if states and state.version <= states[-1].version:
            raise ValueError("Narrative states are immutable and strictly versioned.")
        states.append(state)

    async def latest_state(self, project_id: UUID) -> NarrativeState | None:
        states = self.states.get(project_id, [])
        return states[-1] if states else None

    async def put_window(self, window: WindowProvenance) -> None:
        records = self.window_records[window.project_id]
        if any(record.window_id == window.window_id for record in records):
            return
        records.append(window)

    async def windows(self, project_id: UUID) -> list[WindowProvenance]:
        return sorted(self.window_records.get(project_id, []), key=lambda item: item.start_offset_seconds)

    async def put_candidate(self, candidate: ReflectionCandidate) -> None:
        records = self.candidate_records[candidate.project_id]
        for index, existing in enumerate(records):
            if existing.id == candidate.id or (existing.window_id == candidate.window_id and existing.observation_index == candidate.observation_index):
                records[index] = candidate
                return
        records.append(candidate)

    async def candidates(self, project_id: UUID) -> list[ReflectionCandidate]:
        return sorted(self.candidate_records.get(project_id, []), key=lambda item: (item.knowledge_cutoff_seconds, item.observation_index))

    async def put_echo(self, echo: Echo) -> None:
        records = self.echo_records[echo.project_id]
        if any(record.id == echo.id for record in records):
            return
        records.append(echo)

    async def echoes(self, project_id: UUID) -> list[Echo]:
        return sorted(self.echo_records.get(project_id, []), key=lambda item: item.knowledge_cutoff_seconds)

    async def put_session(self, session: ViewingSession) -> None:
        self.sessions[session.id] = session

    async def get_session(self, session_id: UUID) -> ViewingSession | None:
        return self.sessions.get(session_id)

    async def delete_project(self, project_id: UUID) -> None:
        self.projects.pop(project_id, None)
        self.states.pop(project_id, None)
        self.window_records.pop(project_id, None)
        self.candidate_records.pop(project_id, None)
        self.echo_records.pop(project_id, None)
        for job_id, job in list(self.jobs.items()):
            if job.project_id == project_id:
                self.jobs.pop(job_id)
                self.jobs_by_key.pop((project_id, job.idempotency_key), None)
        for session_id, session in list(self.sessions.items()):
            if session.project_id == project_id:
                self.sessions.pop(session_id)


class FirestoreDataStore:
    """Firestore implementation using a project-scoped collection hierarchy."""

    def __init__(self, project_id: str, credentials=None) -> None:
        from google.cloud.firestore_v1.async_client import AsyncClient

        self.client = AsyncClient(project=project_id, credentials=credentials)
        self.projects = self.client.collection("projects")
        self.jobs = self.client.collection("analysisJobs")
        self.sessions = self.client.collection("viewingSessions")

    @staticmethod
    def _doc(model: object) -> dict:
        return model.model_dump(mode="json")  # type: ignore[attr-defined]

    async def put_project(self, project: Project) -> None:
        project.updated_at = datetime.now(UTC)
        await self.projects.document(str(project.id)).set(self._doc(project))

    async def get_project(self, project_id: UUID) -> Project | None:
        snapshot = await self.projects.document(str(project_id)).get()
        return Project.model_validate(snapshot.to_dict()) if snapshot.exists else None

    async def put_job(self, job: AnalysisJob) -> None:
        job.updated_at = datetime.now(UTC)
        await self.jobs.document(str(job.id)).set(self._doc(job))

    async def get_job(self, job_id: UUID) -> AnalysisJob | None:
        snapshot = await self.jobs.document(str(job_id)).get()
        return AnalysisJob.model_validate(snapshot.to_dict()) if snapshot.exists else None

    async def find_job_by_key(self, project_id: UUID, key: str) -> AnalysisJob | None:
        query = self.jobs.where("project_id", "==", str(project_id)).where("idempotency_key", "==", key).limit(1)
        found = [item async for item in query.stream()]
        return AnalysisJob.model_validate(found[0].to_dict()) if found else None

    async def put_state(self, project_id: UUID, state: NarrativeState) -> None:
        doc = self.projects.document(str(project_id)).collection("narrativeStates").document(f"v{state.version}")
        existing = await doc.get()
        if existing.exists:
            raise ValueError("Narrative state version already exists and is immutable.")
        await doc.create(self._doc(state))

    async def latest_state(self, project_id: UUID) -> NarrativeState | None:
        from google.cloud.firestore_v1 import Query

        query = self.projects.document(str(project_id)).collection("narrativeStates").order_by("version", direction=Query.DESCENDING).limit(1)
        found = [item async for item in query.stream()]
        return NarrativeState.model_validate(found[0].to_dict()) if found else None

    async def put_window(self, window: WindowProvenance) -> None:
        await self.projects.document(str(window.project_id)).collection("windows").document(str(window.window_id)).set(self._doc(window))

    async def windows(self, project_id: UUID) -> list[WindowProvenance]:
        query = self.projects.document(str(project_id)).collection("windows").order_by("start_offset_seconds")
        return [WindowProvenance.model_validate(item.to_dict()) async for item in query.stream()]

    async def put_candidate(self, candidate: ReflectionCandidate) -> None:
        await self.projects.document(str(candidate.project_id)).collection("reflectionCandidates").document(str(candidate.id)).set(self._doc(candidate))

    async def candidates(self, project_id: UUID) -> list[ReflectionCandidate]:
        records = [ReflectionCandidate.model_validate(item.to_dict()) async for item in self.projects.document(str(project_id)).collection("reflectionCandidates").stream()]
        return sorted(records, key=lambda item: (item.knowledge_cutoff_seconds, item.observation_index))

    async def put_echo(self, echo: Echo) -> None:
        await self.projects.document(str(echo.project_id)).collection("echoes").document(str(echo.id)).set(self._doc(echo))

    async def echoes(self, project_id: UUID) -> list[Echo]:
        query = self.projects.document(str(project_id)).collection("echoes").order_by("knowledge_cutoff_seconds")
        return [Echo.model_validate(item.to_dict()) async for item in query.stream()]

    async def put_session(self, session: ViewingSession) -> None:
        await self.sessions.document(str(session.id)).set(self._doc(session))

    async def get_session(self, session_id: UUID) -> ViewingSession | None:
        snapshot = await self.sessions.document(str(session_id)).get()
        return ViewingSession.model_validate(snapshot.to_dict()) if snapshot.exists else None

    async def delete_project(self, project_id: UUID) -> None:
        project_doc = self.projects.document(str(project_id))
        for collection in ("narrativeStates", "windows", "reflectionCandidates", "echoes"):
            documents = [item async for item in project_doc.collection(collection).stream()]
            for document in documents:
                await document.reference.delete()
        jobs = [item async for item in self.jobs.where("project_id", "==", str(project_id)).stream()]
        for document in jobs:
            await document.reference.delete()
        sessions = [item async for item in self.sessions.where("project_id", "==", str(project_id)).stream()]
        for document in sessions:
            await document.reference.delete()
        await project_doc.delete()
