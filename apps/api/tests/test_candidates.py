from uuid import uuid4

import pytest

from app.repositories import InMemoryDataStore
from app.schemas import AnalysisOutcome, Evidence, ReflectionCandidate, ReflectionCandidateStatus, WindowObservation, WindowProvenance


@pytest.mark.asyncio
async def test_reflection_candidate_is_a_durable_idempotent_checkpoint() -> None:
    project_id = uuid4()
    provenance = WindowProvenance(
        project_id=project_id,
        start_offset_seconds=0,
        end_offset_seconds=40,
        provider="gemini",
        model_id="candidate-model",
        prompt_version="test",
        pipeline_version="test",
        input_narrative_state_version=0,
        output_narrative_state_version=1,
    )
    candidate = ReflectionCandidate(
        project_id=project_id,
        window_id=provenance.window_id,
        observation_index=0,
        knowledge_cutoff_seconds=40,
        observation=WindowObservation(
            event_start_seconds=1,
            event_end_seconds=2,
            interpretation="A speaker masks disappointment with a joke.",
            evidence=Evidence(observed_spoken_content="I am fine", observed_visual_action="They look away"),
            confidence=0.8,
            outcome=AnalysisOutcome.ACCEPT,
            candidate_tensions=["performed confidence and private disappointment"],
        ),
        video_provenance=provenance,
    )
    store = InMemoryDataStore()

    await store.put_candidate(candidate)
    await store.put_candidate(candidate.model_copy(update={"status": ReflectionCandidateStatus.ECHO_PERSISTED}))

    candidates = await store.candidates(project_id)
    assert len(candidates) == 1
    assert candidates[0].status == ReflectionCandidateStatus.ECHO_PERSISTED
