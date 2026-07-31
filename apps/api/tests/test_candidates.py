from uuid import uuid4

import pytest

from app.repositories import InMemoryDataStore
from app.schemas import AnalysisOutcome, Evidence, ReflectionCandidate, ReflectionCandidateStatus, WindowObservation, WindowProvenance
from app.worker import select_diverse_candidates


def candidate_at(project_id, cutoff: float, confidence: float, observation_index: int) -> ReflectionCandidate:
    provenance = WindowProvenance(
        project_id=project_id,
        start_offset_seconds=max(0, cutoff - 40),
        end_offset_seconds=cutoff,
        provider="gemini",
        model_id="candidate-model",
        prompt_version="test",
        pipeline_version="test",
        input_narrative_state_version=0,
        output_narrative_state_version=1,
    )
    return ReflectionCandidate(
        project_id=project_id,
        window_id=provenance.window_id,
        observation_index=observation_index,
        knowledge_cutoff_seconds=cutoff,
        observation=WindowObservation(
            event_start_seconds=max(0, cutoff - 10),
            event_end_seconds=cutoff,
            interpretation=f"Moment at {cutoff}",
            evidence=Evidence(observed_visual_action="A grounded action"),
            confidence=confidence,
            outcome=AnalysisOutcome.ACCEPT,
            candidate_tensions=["a specific human tension"],
        ),
        video_provenance=provenance,
    )


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


def test_candidate_selection_prefers_distinct_timestamps() -> None:
    project_id = uuid4()
    candidates = [
        candidate_at(project_id, 120, 0.99, 0),
        candidate_at(project_id, 120, 0.98, 1),
        candidate_at(project_id, 160, 0.90, 0),
        candidate_at(project_id, 200, 0.80, 0),
    ]

    selected = select_diverse_candidates(candidates, 3)

    assert [candidate.knowledge_cutoff_seconds for candidate in selected] == [120, 160, 200]
