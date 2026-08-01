# ADR: Timed unlock and continuous-completion frontiers

STILL persists two separate playback facts because they answer different product questions:

- `furthest_reached_seconds` is the greatest real video playhead timestamp reported by the player. Timed Echoes with `knowledge_cutoff_seconds` at or before this value may appear. A deliberate forward scrub advances this value, matching the YouTube timestamp the viewer chose to reach.
- `contiguous_frontier_seconds` is the furthest time covered continuously from zero through actual watched ranges. It does not advance across a seek gap.

Story Complete requires a natural-ended signal plus contiguous coverage through `duration - 2s`. Therefore seeking works for interactive timed-Echo testing without falsely claiming that the whole story was watched. The API performs both gates; browser state alone is not trusted.
