# Real end-to-end acceptance evidence

No mock, fixture, hardcoded Echo, transcript-only substitute, or
title/description analysis may satisfy the real pipeline gate. A public
prepared-demo record is allowed only after that real gate succeeds, only for
the exact source, and only with sanitized provenance. It cannot answer a new
submission.

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

Evidence status: **technical pipeline passed; source-rights caveat recorded**
(2026-08-01).

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

Those observations remain valid evidence of abstention and resume behavior.
Afterward, Dogs Inc's public release, “Pip,”
completed seven real bounded audiovisual windows. Gloo accepted one capped
candidate, YouVersion returned exact 1 Corinthians 1:27 in BSB with copyright
attribution, Gloo accepted passage verification, and one Echo was persisted.

Dogs Inc produced and published the guide-dog story on its own channel. STILL
uses only the original YouTube embed and does not rehost it.
Copyright remains with the owners; this evidence is not a legal ownership claim.

## Gate 2 - final deployment: deployed E2E acceptance

Repeat the flow through the public deployed application. Verify:

1. real frontend submission/upload;
2. durable background processing and READY state;
3. real playback, watched-range and spoiler-lock behavior;
4. Story Complete gating;
5. intentional reflection displaying exact YouVersion Scripture.

Evidence status: **prepared-demo interaction passed; open submission backend is
out of scope on Spark**.

Firebase Hosting is live at <https://still-scriptures.web.app> on Spark. A fresh
anonymous Firebase session successfully retrieved the exact hashed prepared
record. Deployed rules denied collection listing and every browser write.

Browser evidence passed:

- the source-bound YouTube player loaded from the producing nonprofit's channel;
- at frontier 0:00, the reflection drawer contained zero Echoes;
- contiguous real playback advanced the frontier;
- a full natural playback produced Story Complete and exact canonical rendering;
- the final Pip record remains hidden until its 3:20 frontier;
- the client contains no Gemini, Gloo, or YouVersion credential.

The 0:00/0:40 before-and-after frontier behavior was browser-verified on the
same schema before the final record replacement; the final Pip record was then
verified fresh at 0:00 with zero Echoes. This validates the public prepared-demo journey, not open `add → process` for an
arbitrary new source. Cloud Run, Cloud Tasks, and Firebase Storage remain
undeployed because the project is intentionally kept on Spark.
