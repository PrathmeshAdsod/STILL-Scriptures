# ADR: Contiguous watched frontier

`contiguous_frontier_seconds` is the furthest time reached from zero through actual watched ranges. It is not the maximum playhead position.

Forward seeks are recorded as discontinuous ranges and do not unlock intervening content. Story Complete additionally requires a natural-ended signal and coverage through `duration - 2s`. The API performs the final gate; browser state alone is not trusted.
