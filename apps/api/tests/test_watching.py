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
