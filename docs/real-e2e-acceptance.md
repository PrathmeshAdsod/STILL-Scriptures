# Real end-to-end acceptance evidence

No mock, fixture, Prepared Demo cache, hardcoded Echo, manual database write,
transcript-only substitute, or title/description analysis may be used for either
gate. Record sanitized provenance only.

## Gate 1 - Milestone 5: real pipeline acceptance

Use a previously unseen, rights-cleared supported video through the real
staging/backend pipeline. Verify:

1. real source validation;
2. real bounded Gemini audiovisual requests;
3. evidence that audio and visual context influenced output;
4. chronological causal narrative states;
5. real Gloo Sacred Timing decision;
6. real YouVersion retrieval and real Gloo passage verification;
7. final persisted Echo with full provider and Scripture provenance.

Evidence status: **partial, honestly non-accepting** (2026-08-01).

- Real public source validation passed for a 5:58 entrant-selected YouTube URL.
- Gemini completed two inspected audiovisual windows and a resumable 9-window
  local pipeline run with immutable chronological state.
- One paid Gloo required-tool call returned `NO_ECHO` with confidence 1.0. This
  is a valid safe result for the sensitive source, not a persisted Scripture
  Echo.
- YouVersion Bible 3034 independently returned an exact canonical passage,
  version metadata, and copyright attribution.
- The first 9-window attempt reached the local RPM budget at 8/9; a retry
  resumed and completed without reprocessing accepted work.

Because Gloo intentionally selected `NO_ECHO`, no YouVersion passage was attached
to that project and the final persisted-Echo requirement remains open. The
source rights status was supplied by the entrant and not independently verified.

## Gate 2 - final deployment: deployed E2E acceptance

Repeat the flow through the public deployed application. Verify:

1. real frontend submission/upload;
2. durable background processing and READY state;
3. real playback, watched-range and spoiler-lock behavior;
4. Story Complete gating;
5. intentional reflection displaying exact YouVersion Scripture.

Evidence status: **not run; public site is a static showcase**.

Firebase Hosting is live at <https://still-scriptures.web.app> on the Spark
plan. It exposes no credentials and clearly disables provider-backed controls.
Firestore, Cloud Tasks, and Cloud Run were not deployed because that backend
path requires billing; therefore the static site does not satisfy this gate.
