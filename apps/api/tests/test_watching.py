from uuid import uuid4

from app.repositories import FirestoreDataStore
from app.schemas import ViewingSession
from app.watching import contiguous_frontier, normalise_ranges, qualifies_for_story_complete


def test_forward_seek_does_not_advance_contiguous_frontier() -> None:
    watched = normalise_ranges([(0, 31), (598, 600)], 600)
    assert contiguous_frontier(watched) == 31
    assert not qualifies_for_story_complete(ranges=watched, duration_seconds=600, ended_naturally=True)


def test_contiguous_natural_watch_unlocks_only_at_ending() -> None:
    watched = normalise_ranges([(0, 145), (145.1, 300)], 300)
    assert contiguous_frontier(watched) == 300
    assert qualifies_for_story_complete(ranges=watched, duration_seconds=300, ended_naturally=True)
    assert not qualifies_for_story_complete(ranges=watched, duration_seconds=300, ended_naturally=False)


def test_firestore_session_ranges_use_map_representation() -> None:
    session = ViewingSession(
        project_id=uuid4(),
        owner_id="viewer",
        watched_ranges=[(0, 12.5), (24, 30)],
        contiguous_frontier_seconds=12.5,
    )

    document = FirestoreDataStore._session_doc(session)

    assert document["watched_ranges"] == [
        {"start_seconds": 0.0, "end_seconds": 12.5},
        {"start_seconds": 24.0, "end_seconds": 30.0},
    ]
    restored = FirestoreDataStore._session_from_doc(document)
    assert restored.watched_ranges == [(0, 12.5), (24, 30)]
    assert restored.contiguous_frontier_seconds == 12.5
