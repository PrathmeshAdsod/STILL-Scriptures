# ADR: Spoiler Firewall

## Decision

Presentation order controls what STILL may know during a first watch. Every semantic request has an exact source start/end offset, and every output receives a `knowledge_cutoff_seconds` equal to the causal window end.

## Invariants

- A first-view call never includes source media after its end offset.
- Narrative states are append-only versions; later evidence cannot silently mutate an earlier snapshot.
- An Echo is returned during a first watch only where `knowledge_cutoff_seconds <= furthest_reached_seconds`; this follows a timestamp the viewer actually reached, including a deliberate scrub.
- Story Complete remains stricter: it requires contiguous watched coverage and a natural ending.
- Ambiguous, sensitive, degraded, blocked, and unavailable conditions resolve to a truthful non-Echo outcome.
- Full-story interpretation is stored separately from first-view interpretation.

## Consequence

STILL can handle flashbacks, dreams, and nonlinear presentation because it follows what the viewer has been shown, not fictional chronological time.
