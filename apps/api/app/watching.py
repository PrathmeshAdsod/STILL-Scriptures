from __future__ import annotations


def normalise_ranges(ranges: list[tuple[float, float]], duration_seconds: float) -> list[tuple[float, float]]:
    bounded = [(max(0.0, min(start, duration_seconds)), max(0.0, min(end, duration_seconds))) for start, end in ranges if end > start]
    ordered = sorted(bounded)
    merged: list[tuple[float, float]] = []
    for start, end in ordered:
        if not merged or start > merged[-1][1] + 0.25:
            merged.append((start, end))
        else:
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))
    return [(round(start, 3), round(end, 3)) for start, end in merged]


def contiguous_frontier(ranges: list[tuple[float, float]], *, tolerance_seconds: float = 1.0) -> float:
    frontier = 0.0
    for start, end in normalise_ranges(ranges, max((end for _, end in ranges), default=0.0)):
        if start > frontier + tolerance_seconds:
            break
        frontier = max(frontier, end)
    return round(frontier, 3)


def qualifies_for_story_complete(*, ranges: list[tuple[float, float]], duration_seconds: float, ended_naturally: bool) -> bool:
    # A seek to the ending contributes no watched coverage. Natural ended signal alone is insufficient.
    return ended_naturally and contiguous_frontier(ranges) >= max(0, duration_seconds - 2.0)
