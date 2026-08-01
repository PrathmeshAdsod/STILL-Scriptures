from uuid import uuid4

from app.repositories import FirestoreDataStore
from app.schemas import ViewingSession
from app.watching import contiguous_frontier, furthest_reached, normalise_ranges, qualifies_for_story_complete


def test_forward_seek_does_not_advance_contiguous_frontier() -> None:
    watched = normalise_ranges([(0, 31), (598, 600)], 600)
    assert contiguous_frontier(watched) == 31
    assert furthest_reached(watched, current_position_seconds=600, duration_seconds=600) == 600
    assert not qualifies_for_story_complete(ranges=watched, duration_seconds=600, ended_naturally=True)


def test_reached_position_is_clamped_and_can_advance_while_paused() -> None:
    watched = normalise_ranges([(0, 14)], 259)

    assert furthest_reached(watched, current_position_seconds=211, duration_seconds=259) == 211
    assert furthest_reached(watched, current_position_seconds=999, duration_seconds=259) == 259


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
        furthest_reached_seconds=30,
    )

    document = FirestoreDataStore._session_doc(session)

    assert document["watched_ranges"] == [
        {"start_seconds": 0.0, "end_seconds": 12.5},
        {"start_seconds": 24.0, "end_seconds": 30.0},
    ]
    restored = FirestoreDataStore._session_from_doc(document)
    assert restored.watched_ranges == [(0, 12.5), (24, 30)]
    assert restored.contiguous_frontier_seconds == 12.5
    assert restored.furthest_reached_seconds == 30


def test_firestore_migrates_furthest_position_from_legacy_ranges() -> None:
    session = ViewingSession(project_id=uuid4(), owner_id="viewer", watched_ranges=[(0, 14), (210, 214)])
    document = FirestoreDataStore._session_doc(session)
    document.pop("furthest_reached_seconds")

    restored = FirestoreDataStore._session_from_doc(document)

    assert restored.contiguous_frontier_seconds == 0
    assert restored.furthest_reached_seconds == 214
