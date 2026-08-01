from __future__ import annotations

from pathlib import Path

import nbformat as nbf
from nbclient import NotebookClient


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "docs" / "submission" / "still_spoiler_firewall.ipynb"


def markdown(text: str):
    return nbf.v4.new_markdown_cell(text.strip())


def code(text: str):
    return nbf.v4.new_code_cell(text.strip())


notebook = nbf.v4.new_notebook()
notebook["metadata"] = {
    "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
    "language_info": {"name": "python", "version": "3"},
}
notebook["cells"] = [
    markdown(
        """
# STILL: an executable spoiler-firewall companion

## Goal

This public-safe notebook demonstrates the deterministic product rules behind
STILL: chronological causal windows, timed reflection visibility bounded by
the furthest video timestamp reached, and a stricter contiguous-completion gate.

It does **not** call Gemini, Gloo, YouVersion, or any cloud service. It contains
no credential, private video, provider output, or simulated acceptance result.
The production application and live evidence belong in the public repository
and demo video.
"""
    ),
    markdown(
        """
## Setup

Only the Python standard library is used. Times are seconds on the video's
presentation timeline. A reflection's `knowledge_cutoff` is the latest moment
whose evidence it may contain.
"""
    ),
    code(
        """
from dataclasses import dataclass


@dataclass(frozen=True)
class Echo:
    label: str
    knowledge_cutoff: float


def causal_windows(duration: float, window: float = 20.0, overlap: float = 5.0):
    # Return chronological bounded windows without looking beyond duration.
    assert duration > 0 and window > overlap >= 0
    step = window - overlap
    start = 0.0
    result = []
    while start < duration:
        end = min(start + window, duration)
        result.append((round(start, 3), round(end, 3)))
        if end == duration:
            break
        start += step
    return result


def normalize_ranges(ranges, duration: float):
    clipped = sorted((max(0.0, start), min(duration, end)) for start, end in ranges if end > start)
    merged = []
    for start, end in clipped:
        if not merged or start > merged[-1][1] + 0.75:
            merged.append([start, end])
        else:
            merged[-1][1] = max(merged[-1][1], end)
    return [(round(start, 3), round(end, 3)) for start, end in merged]


def contiguous_frontier(ranges, tolerance: float = 1.5):
    frontier = 0.0
    for start, end in ranges:
        if start > frontier + tolerance:
            break
        frontier = max(frontier, end)
    return round(frontier, 3)


def furthest_reached(ranges, current_position: float, duration: float):
    return round(max([min(max(current_position, 0.0), duration), *[end for _, end in ranges]]), 3)


def visible_echoes(echoes, reached_position: float):
    return [echo for echo in echoes if echo.knowledge_cutoff <= reached_position]


def story_complete(ranges, duration: float, ended_naturally: bool):
    if not ended_naturally or duration <= 0:
        return False
    watched = sum(end - start for start, end in ranges)
    return contiguous_frontier(ranges) >= duration - 2.0 and watched / duration >= 0.95
"""
    ),
    markdown(
        """
## Steps

### 1. Split one story into causal windows

Each analysis request is bounded. Overlap preserves local continuity, while the
end of every window remains explicit.
"""
    ),
    code(
        """
duration_seconds = 90.0
windows = causal_windows(duration_seconds)
windows
"""
    ),
    markdown(
        """
### 2. Compute what the viewer genuinely knows

The example includes a seek from second 31 to second 70. The viewer deliberately
reached second 82, so timed Echoes through that point may appear. The gap still
prevents the stricter contiguous frontier from advancing.
"""
    ),
    code(
        """
sampled_ranges = normalize_ranges([(0, 18), (17.5, 31), (70, 82)], duration_seconds)
frontier = contiguous_frontier(sampled_ranges)
reached_position = furthest_reached(sampled_ranges, current_position=82, duration=duration_seconds)
echoes = [Echo("quiet joke", 12), Echo("trust changes", 28), Echo("final reveal", 76)]

print("normalized ranges:", sampled_ranges)
print("contiguous frontier:", frontier)
print("furthest reached:", reached_position)
print("visible reflections:", [echo.label for echo in visible_echoes(echoes, reached_position)])
"""
    ),
    markdown(
        """
### 3. Require a real ending for full-story reflection

Reaching the last frame by seeking is insufficient. The viewer needs a nearly
complete contiguous watch and a natural ending event.
"""
    ),
    code(
        """
print("seeked ending:", story_complete(sampled_ranges, duration_seconds, ended_naturally=True))

complete_ranges = normalize_ranges([(0, 30.2), (29.8, 61), (60.5, 90)], duration_seconds)
print("continuous natural ending:", story_complete(complete_ranges, duration_seconds, ended_naturally=True))
"""
    ),
    markdown(
        """
## Checks

These assertions are the notebook's deterministic acceptance boundary. Passing
them demonstrates the gating logic only; it is not evidence that an external AI
provider or deployment is live.
"""
    ),
    code(
        """
assert windows == [(0.0, 20.0), (15.0, 35.0), (30.0, 50.0), (45.0, 65.0), (60.0, 80.0), (75.0, 90.0)]
assert frontier == 31
assert reached_position == 82
assert [echo.label for echo in visible_echoes(echoes, reached_position)] == ["quiet joke", "trust changes", "final reveal"]
assert not story_complete(sampled_ranges, duration_seconds, ended_naturally=True)
assert not story_complete(complete_ranges, duration_seconds, ended_naturally=False)
assert story_complete(complete_ranges, duration_seconds, ended_naturally=True)

print("All deterministic spoiler-firewall checks passed.")
"""
    ),
    markdown(
        """
## Next Steps

The competition demo should pair these deterministic rules with one sanitized,
rights-cleared, provider-backed run: Gemini bounded audiovisual evidence, a Gloo
Sacred Timing decision, and an exact app-licensed YouVersion passage with
version and attribution. Silence (`NO_ECHO`) remains a valid complete outcome.
"""
    ),
]

OUTPUT.parent.mkdir(parents=True, exist_ok=True)
NotebookClient(
    notebook,
    timeout=60,
    kernel_name="python3",
    resources={"metadata": {"path": str(OUTPUT.parent)}},
).execute()
nbf.write(notebook, OUTPUT)
nbf.validate(notebook)
print(f"Wrote and executed {OUTPUT}")
