# Milestone 1B live verification

Status: **bounded verification and one full accepted Echo passed on
2026-08-01**.

## Required inputs

- Gemini API key and access to the selected project/model pool.
- Gloo credentials for the selected Completions V2 contract.
- YouVersion application key and at least one app-licensed Bible ID.
- Optional NVIDIA key only if its endpoint remains current.
- A rights-cleared audiovisual source with both audio-dependent and
  visual-dependent meaning.

## Run sequence

1. Run `python tools/milestone1_preflight.py`.
2. Run `python tools/live_capability_spike.py --source-uri <public-youtube-url>`
   for bounded Gemini and YouVersion verification. For an uploaded Firebase/GCS
   source, prove one Files API registration and reuse its returned URI.
3. Record only sanitized model IDs, latency, token usage, modality evidence,
   offsets, safety behavior, retries, and rate-limit behavior.
4. Run `python tools/live_sacred_timing_spike.py --source-uri
   <public-youtube-url>` for exactly one paid Gloo decision.
5. Run the local worker on the full source and confirm restart-safe progress.

## Sanitized observed evidence

- Gemini `gemini-3.5-flash-lite` returned valid structured, audiovisual output
  for 0-40 s and 40-80 s windows. The two calls took approximately 5.34 s and
  2.97 s and preserved the earlier narrative state as an immutable prefix.
- The local worker later completed all 9 windows. An internal RPM guard paused
  the first attempt at 8/9; retry resumed and completed as `READY_NO_ECHO`.
- One paid Gloo Completions V2 call returned the required Sacred Timing tool
  decision `NO_ECHO` with confidence 1.0. Usage was 2,474 prompt and 230
  completion tokens. The production worker now limits Gloo to the strongest
  single candidate per project.
- YouVersion returned HTTP 200 for Bible 3034 and passage `JHN.3.16`, including
  canonical content, version metadata, and copyright attribution.

## Accepted source run

- Dogs Inc's public release of “Pip” was inspected as a 245-second, public,
  non-live, age-unrestricted YouTube source.
- The free gate passed 0-40 s and 40-80 s with full audiovisual mode, audio and
  visual evidence, append-only narrative versions, and an eligible candidate.
- The durable worker completed seven chronological windows. The conservative
  router used `gemini-3.5-flash-lite` and `gemini-3.1-flash-lite` without
  reprocessing persisted windows.
- The source-bound acceptance runner capped Gloo at one candidate. Gloo accepted the
  candidate under the strengthened v2 proportionality policy, YouVersion Bible
  3034 returned exact 1 Corinthians 1:27 in BSB with copyright attribution, and
  Gloo accepted passage verification.
- One Echo was persisted and a sanitized source-bound document was published
  to Firestore. No provider credential or raw provider response was published.
- Before this final success, “Mr Indifferent” completed five real windows and
  one capped Gloo decision as `READY_NO_ECHO`; it was not published. “The
  Present” technically passed but editorial QA rejected its disproportionate
  light/dark connection, leading to the stricter v2 policy and replacement by
  the final Pip record.

Observed paid scope in this account work: four one-candidate decisions and two
passage-verification calls total. No unbounded Gloo batch was run.

No raw provider response, transcript, source media, account identifier, or
credential is stored in this evidence. No tool in this repository creates a
fake pass result.
