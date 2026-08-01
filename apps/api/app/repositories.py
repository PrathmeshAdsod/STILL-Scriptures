from __future__ import annotations

from collections import defaultdict
from datetime import UTC, datetime, time, timedelta
from enum import StrEnum
from typing import Protocol
from uuid import UUID

from .schemas import AccountPlan, AccountStatus, AnalysisJob, Echo, NarrativeState, Project, ProjectStatus, ReflectionCandidate, SourceKind, ViewingSession, WindowProvenance
from .youtube import youtube_video_id


class AnalysisReservationResult(StrEnum):
    RESERVED = "RESERVED"
    USER_LIMIT_REACHED = "USER_LIMIT_REACHED"
    GLOBAL_LIMIT_REACHED = "GLOBAL_LIMIT_REACHED"


class DataStore(Protocol):
    async def put_project(self, project: Project) -> None: ...
    async def get_project(self, project_id: UUID) -> Project | None: ...
    async def list_projects(self, owner_id: str) -> list[Project]: ...
    async def find_youtube_project(self, owner_id: str, video_id: str) -> Project | None: ...
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
    async def latest_session(self, *, owner_id: str, project_id: UUID) -> ViewingSession | None: ...
    async def account_status(self, *, owner_id: str, free_limit: int, access_daily_limit: int, max_duration_seconds: int) -> AccountStatus: ...
    async def grant_access(self, *, owner_id: str) -> None: ...
    async def reserve_analysis(self, *, owner_id: str, project_id: UUID, free_limit: int, access_daily_limit: int, global_limit: int) -> AnalysisReservationResult: ...
    async def delete_project(self, project_id: UUID) -> None: ...
    async def delete_account(self, owner_id: str) -> None: ...


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
        self.analysis_usage: dict[str, dict[str, object]] = {}
        self.account_profiles: dict[str, AccountPlan] = {}
        self.free_usage: dict[str, set[UUID]] = defaultdict(set)
        self.analysis_reservations: dict[UUID, str] = {}

    async def put_project(self, project: Project) -> None:
        project.updated_at = datetime.now(UTC)
        self.projects[project.id] = project

    async def get_project(self, project_id: UUID) -> Project | None:
        return self.projects.get(project_id)

    async def list_projects(self, owner_id: str) -> list[Project]:
        return sorted((project for project in self.projects.values() if project.owner_id == owner_id), key=lambda item: item.updated_at, reverse=True)

    async def find_youtube_project(self, owner_id: str, video_id: str) -> Project | None:
        reusable = {
            ProjectStatus.SOURCE_PENDING,
            ProjectStatus.QUEUED,
            ProjectStatus.PREPARING,
            ProjectStatus.ANALYZING,
            ProjectStatus.GROUNDING,
            ProjectStatus.READY,
            ProjectStatus.READY_NO_ECHO,
            ProjectStatus.FAILED_RETRIABLE,
        }
        for project in await self.list_projects(owner_id):
            source = project.source
            if not source or source.kind != SourceKind.YOUTUBE or project.status not in reusable:
                continue
            stored_id = source.youtube_video_id
            if not stored_id and source.public_url:
                try:
                    stored_id = youtube_video_id(source.public_url)
                except Exception:
                    stored_id = None
            if stored_id == video_id:
                return project
        return None

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
        session.updated_at = datetime.now(UTC)
        self.sessions[session.id] = session

    async def get_session(self, session_id: UUID) -> ViewingSession | None:
        return self.sessions.get(session_id)

    async def latest_session(self, *, owner_id: str, project_id: UUID) -> ViewingSession | None:
        matches = [session for session in self.sessions.values() if session.owner_id == owner_id and session.project_id == project_id]
        return max(matches, key=lambda item: item.updated_at) if matches else None

    async def account_status(self, *, owner_id: str, free_limit: int, access_daily_limit: int, max_duration_seconds: int) -> AccountStatus:
        plan = self.account_profiles.get(owner_id, AccountPlan.FREE)
        if plan == AccountPlan.ACCESS:
            day = datetime.now(UTC).date().isoformat()
            usage = self.analysis_usage.get(day, {"users": {}})
            users = usage.get("users", {})
            assert isinstance(users, dict)
            used = len(users.get(owner_id, set()))
            resets_at = datetime.combine(datetime.now(UTC).date() + timedelta(days=1), time.min, tzinfo=UTC)
            return AccountStatus(plan=plan, max_video_duration_seconds=max_duration_seconds, analysis_limit=access_daily_limit, analyses_used=used, analyses_remaining=max(0, access_daily_limit - used), usage_period="day", usage_resets_at=resets_at)
        used = len(self.free_usage[owner_id])
        return AccountStatus(plan=plan, max_video_duration_seconds=max_duration_seconds, analysis_limit=free_limit, analyses_used=used, analyses_remaining=max(0, free_limit - used), usage_period="lifetime")

    async def grant_access(self, *, owner_id: str) -> None:
        self.account_profiles[owner_id] = AccountPlan.ACCESS

    async def reserve_analysis(self, *, owner_id: str, project_id: UUID, free_limit: int, access_daily_limit: int, global_limit: int) -> AnalysisReservationResult:
        if self.analysis_reservations.get(project_id) == owner_id:
            return AnalysisReservationResult.RESERVED
        day = datetime.now(UTC).date().isoformat()
        usage = self.analysis_usage.setdefault(day, {"total": 0, "users": {}})
        users = usage["users"]
        assert isinstance(users, dict)
        plan = self.account_profiles.get(owner_id, AccountPlan.FREE)
        user_projects = self.free_usage[owner_id] if plan == AccountPlan.FREE else users.setdefault(owner_id, set())
        assert isinstance(user_projects, set)
        limit = free_limit if plan == AccountPlan.FREE else access_daily_limit
        if len(user_projects) >= limit:
            return AnalysisReservationResult.USER_LIMIT_REACHED
        total = int(usage["total"])
        if total >= global_limit:
            return AnalysisReservationResult.GLOBAL_LIMIT_REACHED
        user_projects.add(project_id)
        self.analysis_reservations[project_id] = owner_id
        usage["total"] = total + 1
        return AnalysisReservationResult.RESERVED

    async def delete_project(self, project_id: UUID) -> None:
        self.projects.pop(project_id, None)
        self.states.pop(project_id, None)
        self.window_records.pop(project_id, None)
        self.candidate_records.pop(project_id, None)
        self.echo_records.pop(project_id, None)
        self.analysis_reservations.pop(project_id, None)
        for job_id, job in list(self.jobs.items()):
            if job.project_id == project_id:
                self.jobs.pop(job_id)
                self.jobs_by_key.pop((project_id, job.idempotency_key), None)
        for session_id, session in list(self.sessions.items()):
            if session.project_id == project_id:
                self.sessions.pop(session_id)

    async def delete_account(self, owner_id: str) -> None:
        for project in list(await self.list_projects(owner_id)):
            await self.delete_project(project.id)
        self.account_profiles.pop(owner_id, None)
        self.free_usage.pop(owner_id, None)
        for usage in self.analysis_usage.values():
            users = usage.get("users", {})
            if isinstance(users, dict):
                users.pop(owner_id, None)
        for session_id, session in list(self.sessions.items()):
            if session.owner_id == owner_id:
                self.sessions.pop(session_id)
        for project_id, reserved_owner in list(self.analysis_reservations.items()):
            if reserved_owner == owner_id:
                self.analysis_reservations.pop(project_id)


class FirestoreDataStore:
    """Firestore implementation using a project-scoped collection hierarchy."""

    def __init__(self, project_id: str, credentials=None) -> None:
        from google.cloud.firestore_v1.async_client import AsyncClient

        self.client = AsyncClient(project=project_id, credentials=credentials)
        self.projects = self.client.collection("projects")
        self.jobs = self.client.collection("analysisJobs")
        self.sessions = self.client.collection("viewingSessions")
        self.analysis_usage = self.client.collection("analysisUsage")
        self.account_profiles = self.client.collection("accountProfiles")
        self.account_usage = self.client.collection("accountUsage")
        self.analysis_reservations = self.client.collection("analysisReservations")

    @staticmethod
    def _doc(model: object) -> dict:
        return model.model_dump(mode="json")  # type: ignore[attr-defined]

    @staticmethod
    def _session_doc(session: ViewingSession) -> dict:
        """Encode watched ranges without Firestore's forbidden nested arrays."""
        document = session.model_dump(mode="json")
        document["watched_ranges"] = [
            {"start_seconds": start, "end_seconds": end}
            for start, end in session.watched_ranges
        ]
        return document

    @staticmethod
    def _session_from_doc(document: dict) -> ViewingSession:
        payload = dict(document)
        ranges: list[tuple[float, float]] = []
        for item in payload.get("watched_ranges", []):
            if isinstance(item, dict) and "start_seconds" in item and "end_seconds" in item:
                ranges.append((float(item["start_seconds"]), float(item["end_seconds"])))
            elif isinstance(item, (list, tuple)) and len(item) == 2:
                # Backward compatibility for test/emulator documents. Real
                # Firestore rejects this representation once a range exists.
                ranges.append((float(item[0]), float(item[1])))
        payload["watched_ranges"] = ranges
        # Existing production sessions predate the separate reached-position
        # field. Their honest sampled ranges already contain the furthest
        # playhead, so migrate them safely when read.
        if "furthest_reached_seconds" not in payload:
            payload["furthest_reached_seconds"] = max((end for _, end in ranges), default=payload.get("contiguous_frontier_seconds", 0.0))
        return ViewingSession.model_validate(payload)

    async def put_project(self, project: Project) -> None:
        project.updated_at = datetime.now(UTC)
        await self.projects.document(str(project.id)).set(self._doc(project))

    async def get_project(self, project_id: UUID) -> Project | None:
        snapshot = await self.projects.document(str(project_id)).get()
        return Project.model_validate(snapshot.to_dict()) if snapshot.exists else None

    async def list_projects(self, owner_id: str) -> list[Project]:
        records = [Project.model_validate(item.to_dict()) async for item in self.projects.where("owner_id", "==", owner_id).stream()]
        return sorted(records, key=lambda item: item.updated_at, reverse=True)

    async def find_youtube_project(self, owner_id: str, video_id: str) -> Project | None:
        reusable = {
            ProjectStatus.SOURCE_PENDING,
            ProjectStatus.QUEUED,
            ProjectStatus.PREPARING,
            ProjectStatus.ANALYZING,
            ProjectStatus.GROUNDING,
            ProjectStatus.READY,
            ProjectStatus.READY_NO_ECHO,
            ProjectStatus.FAILED_RETRIABLE,
        }
        for project in await self.list_projects(owner_id):
            source = project.source
            if not source or source.kind != SourceKind.YOUTUBE or project.status not in reusable:
                continue
            stored_id = source.youtube_video_id
            if not stored_id and source.public_url:
                try:
                    stored_id = youtube_video_id(source.public_url)
                except Exception:
                    stored_id = None
            if stored_id == video_id:
                return project
        return None

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
        session.updated_at = datetime.now(UTC)
        await self.sessions.document(str(session.id)).set(self._session_doc(session))

    async def get_session(self, session_id: UUID) -> ViewingSession | None:
        snapshot = await self.sessions.document(str(session_id)).get()
        return self._session_from_doc(snapshot.to_dict()) if snapshot.exists else None

    async def latest_session(self, *, owner_id: str, project_id: UUID) -> ViewingSession | None:
        records = [self._session_from_doc(item.to_dict()) async for item in self.sessions.where("project_id", "==", str(project_id)).stream()]
        matches = [session for session in records if session.owner_id == owner_id]
        return max(matches, key=lambda item: item.updated_at) if matches else None

    async def account_status(self, *, owner_id: str, free_limit: int, access_daily_limit: int, max_duration_seconds: int) -> AccountStatus:
        day = datetime.now(UTC).date().isoformat()
        profile_snapshot = await self.account_profiles.document(owner_id).get()
        plan = AccountPlan((profile_snapshot.to_dict() or {}).get("plan", AccountPlan.FREE.value))
        if plan == AccountPlan.ACCESS:
            daily_snapshot = await self.analysis_usage.document(day).collection("users").document(owner_id).get()
            used = len((daily_snapshot.to_dict() or {}).get("project_ids", []))
            resets_at = datetime.combine(datetime.now(UTC).date() + timedelta(days=1), time.min, tzinfo=UTC)
            return AccountStatus(plan=plan, max_video_duration_seconds=max_duration_seconds, analysis_limit=access_daily_limit, analyses_used=used, analyses_remaining=max(0, access_daily_limit - used), usage_period="day", usage_resets_at=resets_at)
        lifetime_snapshot = await self.account_usage.document(owner_id).get()
        used = len((lifetime_snapshot.to_dict() or {}).get("free_project_ids", []))
        return AccountStatus(plan=plan, max_video_duration_seconds=max_duration_seconds, analysis_limit=free_limit, analyses_used=used, analyses_remaining=max(0, free_limit - used), usage_period="lifetime")

    async def grant_access(self, *, owner_id: str) -> None:
        await self.account_profiles.document(owner_id).set({"plan": AccountPlan.ACCESS.value, "access_granted_at": datetime.now(UTC), "updated_at": datetime.now(UTC)}, merge=True)

    async def reserve_analysis(self, *, owner_id: str, project_id: UUID, free_limit: int, access_daily_limit: int, global_limit: int) -> AnalysisReservationResult:
        from google.cloud import firestore_v1

        day = datetime.now(UTC).date().isoformat()
        usage_ref = self.analysis_usage.document(day)
        user_ref = usage_ref.collection("users").document(owner_id)
        profile_ref = self.account_profiles.document(owner_id)
        lifetime_ref = self.account_usage.document(owner_id)
        reservation_ref = self.analysis_reservations.document(str(project_id))

        @firestore_v1.async_transactional
        async def reserve(transaction):
            usage_snapshot = await usage_ref.get(transaction=transaction)
            user_snapshot = await user_ref.get(transaction=transaction)
            profile_snapshot = await profile_ref.get(transaction=transaction)
            lifetime_snapshot = await lifetime_ref.get(transaction=transaction)
            reservation_snapshot = await reservation_ref.get(transaction=transaction)
            if reservation_snapshot.exists and (reservation_snapshot.to_dict() or {}).get("owner_id") == owner_id:
                return AnalysisReservationResult.RESERVED
            usage_payload = usage_snapshot.to_dict() or {}
            user_payload = user_snapshot.to_dict() or {}
            profile_payload = profile_snapshot.to_dict() or {}
            lifetime_payload = lifetime_snapshot.to_dict() or {}
            plan = AccountPlan(profile_payload.get("plan", AccountPlan.FREE.value))
            usage_field = "free_project_ids" if plan == AccountPlan.FREE else "project_ids"
            usage_payload_for_plan = lifetime_payload if plan == AccountPlan.FREE else user_payload
            projects = list(usage_payload_for_plan.get(usage_field, []))
            project_key = str(project_id)
            limit = free_limit if plan == AccountPlan.FREE else access_daily_limit
            if len(projects) >= limit:
                return AnalysisReservationResult.USER_LIMIT_REACHED
            total = int(usage_payload.get("total", 0))
            if total >= global_limit:
                return AnalysisReservationResult.GLOBAL_LIMIT_REACHED
            transaction.set(usage_ref, {"total": total + 1, "updated_at": datetime.now(UTC)}, merge=True)
            target_ref = lifetime_ref if plan == AccountPlan.FREE else user_ref
            transaction.set(target_ref, {usage_field: [*projects, project_key], "updated_at": datetime.now(UTC)}, merge=True)
            transaction.set(reservation_ref, {"owner_id": owner_id, "project_id": project_key, "plan": plan.value, "reserved_at": datetime.now(UTC), "usage_day": day})
            return AnalysisReservationResult.RESERVED

        return await reserve(self.client.transaction())

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
        await self.analysis_reservations.document(str(project_id)).delete()
        await project_doc.delete()

    async def delete_account(self, owner_id: str) -> None:
        for project in list(await self.list_projects(owner_id)):
            await self.delete_project(project.id)
        orphan_jobs = [item async for item in self.jobs.where("owner_id", "==", owner_id).stream()]
        for document in orphan_jobs:
            await document.reference.delete()
        orphan_sessions = [item async for item in self.sessions.where("owner_id", "==", owner_id).stream()]
        for document in orphan_sessions:
            await document.reference.delete()
        reservations = [item async for item in self.analysis_reservations.where("owner_id", "==", owner_id).stream()]
        for document in reservations:
            await document.reference.delete()
        usage_days = [item async for item in self.analysis_usage.stream()]
        for day in usage_days:
            await day.reference.collection("users").document(owner_id).delete()
        await self.account_profiles.document(owner_id).delete()
        await self.account_usage.document(owner_id).delete()
