from __future__ import annotations

from uuid import NAMESPACE_URL, UUID, uuid5

from .media import SemanticWindow, inspect_uploaded_media, plan_semantic_windows, validate_source
from .observability import log_event
from .providers.base import FailureClass, ProviderFailure, VideoAnalysisRequest
from .providers.gloo import GlooSacredTimingProvider
from .providers.youversion import YouVersionClient
from .repositories import DataStore
from .routing import VideoModelRouter
from .schemas import AnalysisJob, AnalysisOutcome, Echo, ModalityStatus, NarrativeState, ProjectStatus, ReflectionCandidate, ReflectionCandidateStatus, WindowProvenance


def select_diverse_candidates(candidates: list[ReflectionCandidate], limit: int) -> list[ReflectionCandidate]:
    """Prefer strong candidates from different moments before duplicates."""
    ranked = sorted(candidates, key=lambda candidate: candidate.observation.confidence, reverse=True)
    selected: list[ReflectionCandidate] = []
    selected_ids: set[UUID] = set()
    seen_cutoffs: set[float] = set()
    for candidate in ranked:
        cutoff = round(candidate.knowledge_cutoff_seconds, 3)
        if cutoff in seen_cutoffs:
            continue
        selected.append(candidate)
        selected_ids.add(candidate.id)
        seen_cutoffs.add(cutoff)
        if len(selected) == limit:
            return selected
    for candidate in ranked:
        if candidate.id in selected_ids:
            continue
        selected.append(candidate)
        if len(selected) == limit:
            break
    return selected


class CausalAnalysisWorker:
    pipeline_version = "still-causal-v2"
    prompt_version = "bounded-audiovisual-observation-v2"

    def __init__(self, *, store: DataStore, router: VideoModelRouter, gloo: GlooSacredTimingProvider, youversion: YouVersionClient) -> None:
        self.store = store
        self.router = router
        self.gloo = gloo
        self.youversion = youversion

    async def run(self, job_id: UUID) -> None:
        job = await self.store.get_job(job_id)
        if not job or job.status == "CANCELLED":
            return
        project = await self.store.get_project(job.project_id)
        if not project or not project.source:
            await self._fail(job, project, "SOURCE_MISSING", "The source is unavailable for analysis.")
            return
        try:
            # A no-Echo outcome is still a real pipeline result. Do not permit
            # a missing downstream provider to turn into a deceptively READY
            # project merely because no passage happened to be selected.
            self.gloo.ensure_configuration()
            self.youversion.ensure_configuration()
            project.source = await inspect_uploaded_media(project.source)
            await self.store.put_project(project)
            validate_source(project.source)
            if project.source.duration_seconds is None:
                raise ProviderFailure(FailureClass.INPUT_INCOMPATIBLE, "Source duration has not been verified yet.")
            if project.source.duration_seconds > self.router.settings.max_video_duration_seconds:
                raise ProviderFailure(FailureClass.INPUT_INCOMPATIBLE, "The source exceeds this deployment's protected duration limit.")
            job.status = "RUNNING"
            project.status = ProjectStatus.PREPARING
            project.progress.stage = "preparing_media"
            await self.store.put_job(job)
            await self.store.put_project(project)
            primary_provider = self.router.providers.get("gemini")
            if primary_provider is None:
                raise ProviderFailure(FailureClass.CONFIGURATION, "No Gemini provider is registered.")
            prepared_source = await primary_provider.prepare_source(project.source)
            if project.source.kind.value == "upload" and project.source.provider_references.get(prepared_source.provider) != prepared_source.source_reference:
                project.source.provider_references[prepared_source.provider] = prepared_source.source_reference
                project.source.provider_mime_types[prepared_source.provider] = prepared_source.mime_type
                await self.store.put_project(project)
            windows = plan_semantic_windows(project.source.duration_seconds)
            project.progress.total_windows = len(windows)
            completed = await self.store.windows(project.id)
            completed_bounds = {(record.start_offset_seconds, record.end_offset_seconds) for record in completed}
            project.progress.completed_windows = len(completed_bounds)
            await self.store.put_project(project)
            state = await self.store.latest_state(project.id)
            if state is None:
                state = NarrativeState(version=0)
                await self.store.put_state(project.id, state)
            project.status = ProjectStatus.ANALYZING
            project.progress.stage = "understanding_story"
            await self.store.put_project(project)
            for window in windows:
                latest_job = await self.store.get_job(job.id)
                if latest_job and latest_job.status == "CANCELLED":
                    return
                if (window.start_seconds, window.end_seconds) in completed_bounds:
                    continue
                decision_input = {
                    "project_id": str(project.id),
                    "requires_audio": True,
                    "requires_visual": True,
                    "importance": "ordinary",
                    "confidence": None,
                    "safety_sensitive": False,
                    "estimated_tokens": int((window.end_seconds - window.start_seconds) * 300),
                    "project_token_budget": self.router.settings.project_video_analysis_token_budget,
                    "escalation_budget": self.router.settings.daily_escalation_budget,
                }

                async def invoke(route, retry_count: int):
                    request = VideoAnalysisRequest(
                        source=project.source,
                        prepared_source=prepared_source,
                        start_offset_seconds=window.start_seconds,
                        end_offset_seconds=window.end_seconds,
                        narrative_state=state,
                        prompt_version=self.prompt_version,
                    )
                    result = await route.provider.analyze_window(model_id=route.policy.model_id, request=request)
                    provenance = WindowProvenance(
                        project_id=project.id,
                        start_offset_seconds=window.start_seconds,
                        end_offset_seconds=window.end_seconds,
                        provider=route.provider.name,
                        model_id=route.policy.model_id,
                        prompt_version=self.prompt_version,
                        pipeline_version=self.pipeline_version,
                        input_narrative_state_version=state.version,
                        output_narrative_state_version=result.narrative_state.version,
                        retry_count=retry_count,
                        fallback_reason=route.fallback_reason,
                        escalation_reason=route.escalation_reason,
                        modality_status=result.modality_status,
                        confidence=result.confidence,
                        latency_ms=result.raw_provider_metadata.get("latency_ms"),
                        token_usage=result.token_usage,
                    )
                    return result, provenance

                route, completed_window = await self.router.execute_with_failover(decision_input=decision_input, invoke=invoke)
                result, provenance = completed_window
                if result.confidence < 0.65 or any(item.needs_more_context for item in result.observations):
                    escalation_input = {**decision_input, "importance": "high", "confidence": result.confidence}
                    route, completed_window = await self.router.execute_with_failover(decision_input=escalation_input, invoke=invoke)
                    result, provenance = completed_window
                if result.modality_status != ModalityStatus.FULL_AUDIOVISUAL:
                    # Do not make Scripture decisions from degraded sensitive evidence.
                    log_event("window_degraded_modality", project_id=project.id, window_id=provenance.window_id, modality=result.modality_status)
                await self.store.put_window(provenance)
                await self.store.put_state(project.id, result.narrative_state)
                state = result.narrative_state
                project.progress.completed_windows += 1
                await self.store.put_project(project)
                log_event("window_completed", project_id=project.id, window_id=provenance.window_id, provider=route.provider.name, model=route.policy.model_id)
                for observation_index, observation in enumerate(result.observations):
                    if observation.outcome in {AnalysisOutcome.HOLD, AnalysisOutcome.ABSTAIN, AnalysisOutcome.NO_ECHO, AnalysisOutcome.NEEDS_MORE_CONTEXT, AnalysisOutcome.SAFETY_SENSITIVE}:
                        continue
                    if result.modality_status != ModalityStatus.FULL_AUDIOVISUAL:
                        continue
                    # A Scripture candidate must originate in model-observed human
                    # tension. Never supply a generic/template tension as a substitute.
                    if not observation.candidate_tensions:
                        continue
                    candidate = ReflectionCandidate(
                        id=uuid5(NAMESPACE_URL, f"still:{project.id}:{provenance.window_id}:{observation_index}"),
                        project_id=project.id,
                        window_id=provenance.window_id,
                        observation_index=observation_index,
                        knowledge_cutoff_seconds=window.end_seconds,
                        observation=observation,
                        video_provenance=provenance,
                    )
                    await self.store.put_candidate(candidate)
            project.status = ProjectStatus.GROUNDING
            project.progress.stage = "grounding_reflection"
            await self.store.put_project(project)
            pending_candidates = [
                candidate
                for candidate in await self.store.candidates(project.id)
                if candidate.status == ReflectionCandidateStatus.PENDING
            ]
            selected_candidates = select_diverse_candidates(
                pending_candidates,
                self.gloo.settings.gloo_max_candidates_per_project,
            )
            selected_ids = {candidate.id for candidate in selected_candidates}
            for skipped_candidate in pending_candidates:
                if skipped_candidate.id in selected_ids:
                    continue
                skipped_candidate.status = ReflectionCandidateStatus.NO_ECHO
                await self.store.put_candidate(skipped_candidate)
            for candidate in selected_candidates:
                decision = await self.gloo.decide(
                    observation=candidate.observation,
                    video_context=f"Observed presentation interval ends at {candidate.knowledge_cutoff_seconds} seconds.",
                )
                if decision.outcome != AnalysisOutcome.ACCEPT or not decision.selected_reference:
                    candidate.status = ReflectionCandidateStatus.NO_ECHO
                    await self.store.put_candidate(candidate)
                    continue
                draft = Echo(
                    id=candidate.id,
                    project_id=project.id,
                    candidate_id=candidate.id,
                    knowledge_cutoff_seconds=candidate.knowledge_cutoff_seconds,
                    first_view_interpretation=candidate.observation.interpretation,
                    tension=candidate.observation.candidate_tensions[0],
                    scene_context=" ".join(filter(None, [candidate.observation.evidence.observed_spoken_content, candidate.observation.evidence.observed_visual_action]))[:600],
                    outcome=decision.outcome,
                    scripture_reference=decision.selected_reference,
                    confidence=min(candidate.observation.confidence, decision.confidence),
                    provider_provenance={"video": candidate.video_provenance.model_dump(mode="json"), "gloo": {"endpoint_mode": self.gloo.settings.gloo_endpoint_mode, "rationale": decision.rationale, **decision.metadata}},
                )
                passage = await self.youversion.retrieve_passage(passage_id=decision.selected_passage_id, bible_id=decision.bible_id)
                verification_outcome, verification_rationale, verification_metadata = await self.gloo.verify_passage(echo=draft, canonical_text=passage.text, attribution=passage.copyright_attribution)
                if verification_outcome != AnalysisOutcome.ACCEPT:
                    candidate.status = ReflectionCandidateStatus.REJECTED
                    await self.store.put_candidate(candidate)
                    continue
                final_echo = draft.model_copy(update={
                    "scripture_reference": passage.reference or draft.scripture_reference,
                    "bible_id": passage.bible_id,
                    "bible_version": passage.bible_version,
                    "exact_scripture_text": passage.text,
                    "copyright_attribution": passage.copyright_attribution,
                    "connection_explanation": verification_rationale,
                    "provider_provenance": {**draft.provider_provenance, "youversion": {"reference": passage.reference, "passage_id": passage.passage_id, "bible_id": passage.bible_id}, "gloo_passage_verification": verification_metadata},
                })
                await self.store.put_echo(final_echo)
                candidate.status = ReflectionCandidateStatus.ECHO_PERSISTED
                await self.store.put_candidate(candidate)
            created_echoes = len(await self.store.echoes(project.id))
            project.status = ProjectStatus.READY if created_echoes else ProjectStatus.READY_NO_ECHO
            project.progress.stage = "ready"
            project.failure_code = None
            project.failure_message = None
            job.status = "COMPLETED"
            await self.store.put_project(project)
            await self.store.put_job(job)
            log_event("analysis_completed", project_id=project.id, job_id=job.id, echoes=created_echoes)
        except ProviderFailure as error:
            await self._fail(job, project, error.failure_class.value, str(error))
        except Exception as error:
            await self._fail(job, project, "UNEXPECTED_WORKER_FAILURE", "Analysis stopped unexpectedly and can be retried.")
            log_event("analysis_unexpected_failure", job_id=job.id, error_type=type(error).__name__)

    async def _fail(self, job: AnalysisJob, project, code: str, message: str) -> None:
        job.status = "FAILED"
        await self.store.put_job(job)
        if project:
            non_retriable = {
                FailureClass.INPUT_INCOMPATIBLE.value,
                FailureClass.SAFETY_BLOCK.value,
                FailureClass.INVALID_RESPONSE.value,
                FailureClass.PERMANENT.value,
            }
            project.status = ProjectStatus.FAILED if code in non_retriable else ProjectStatus.FAILED_RETRIABLE
            project.failure_code = code
            project.failure_message = message[:500]
            project.progress.stage = "failed"
            await self.store.put_project(project)
        log_event("analysis_failed", job_id=job.id, project_id=job.project_id, failure_code=code)
