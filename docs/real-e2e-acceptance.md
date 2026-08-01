# Real end-to-end acceptance evidence

No mock, fixture, hardcoded Echo, transcript-only substitute, title analysis,
or cached result from another source may satisfy the production gate.
`READY_NO_ECHO` is a valid completion when the evidence does not support a
proportionate reflection.

## Gate 1 - provider pipeline

Status: **passed on real video sources** (2026-08-01).

- Gemini completed bounded chronological full-audiovisual windows with
  immutable prior narrative state.
- Gloo returned both a valid structured abstention for unsuitable material and
  an accepted candidate for a suitable source.
- YouVersion returned exact canonical passage text, version, and copyright
  attribution for the accepted path.
- Gloo accepted the final canonical-passage verification.
- One suitable source produced a verified persisted Echo; the sensitive test
  source correctly produced `NO_ECHO`.

The accepted source is Dogs Inc's public release, "Pip." STILL uses the
original YouTube embed and does not rehost the media. Copyright remains with
the source owner; this technical evidence is not a legal ownership claim.

## Gate 2 - deployed arbitrary-source product

Status: **passed** (2026-08-01).

The entrant-selected <https://youtu.be/3ZR3unZ3FW0> source has an authoritative
duration of 5:58. It was submitted through the public Hosting origin with an
authenticated, email-verified Access account. The deployed Cloud Tasks worker
completed 9/9 full audiovisual windows in about 84 seconds and reached terminal
status `READY_NO_ECHO`.

This result demonstrates:

1. real frontend-compatible authenticated submission;
2. authoritative video validation and six-minute enforcement;
3. durable Cloud Tasks dispatch to the Cloud Run worker;
4. real bounded audiovisual processing for every window;
5. honest abstention rather than a forced Scripture connection; and
6. persisted project state retrievable only by its owner.

## Gate 3 - saved library and account lifecycle

Status: **passed in production** (2026-08-01).

- The completed 5:58 project appears in **My videos** after a fresh page load
  and opens the original YouTube player without another analysis.
- Submitting the exact same YouTube URL resolves to the stored project, and the
  private account allowance remains unchanged.
- Repeated server resume calls return the same viewing session, so the reached
  timestamp and continuous watched ranges can continue across devices.
- The library is owner-scoped, and project deletion is ownership-checked.
- A disposable verified production account returned HTTP 204 from account
  deletion, disappeared from Firebase Authentication, and its old token was
  rejected with HTTP 401. The disposable account was removed completely.

## Gate 4 - timed Scripture experience

Status: **passed in production** (2026-08-01).

- Dogs Inc's 4:05 “Pip” was submitted through the authenticated hosted app,
  not copied from the earlier source-bound evidence project.
- The worker completed 7/7 audiovisual windows and persisted four candidates
  across 2:00, 2:40, and 3:20.
- The three-distinct-moment Gloo cap yielded two accepted and passage-verified
  Echoes: Hebrews 12:1 at 2:00 and Hebrews 13:16 at 3:20, both exact BSB text
  with YouVersion attribution.
- The hosted API returned zero Echoes at a 0:00 frontier, one at 2:01, and both
  at 3:21. The browser automatically rendered the same progression.
- Opening either timed card showed scene evidence, the canonical passage,
  version, attribution, and a viewer-facing explanation.
- Story Complete returned both reflections only after contiguous full coverage
  and a natural-ended signal.
- The reported HTTP 500 was reproduced as Firestore's rejection of nested
  arrays. Viewing ranges now use map records; the failing PATCH returns 200 in
  production and the demo session was reset to 0:00 after QA.
- Direct Watch/Reflection reloads now wait for Firebase session restoration,
  preventing the earlier bearer-token race.
- A real “The Present” session exposed the difference between a selected
  YouTube timestamp and continuous coverage: the player reached 4:17 while the
  old unlock frontier remained 0:14. Production evidence already contained one
  verified Ezekiel 36:26 Echo at 2:40. The gates are now separated so the
  furthest real playhead unlocks timed Echoes, while Story Complete still
  requires continuous coverage and a natural ending.
- YouTube playhead polling continues while paused, so scrubbing a paused embed
  updates STILL rather than waiting for playback to restart.

## Production browser and infrastructure checks

- Public landing and Plans pages render correctly signed out.
- Protected routes show an account-required state.
- Email/password sign-in and account allowance retrieval work.
- Saved-video listing, same-link reuse, and server-side session resume work.
- Full application-data and Firebase Authentication account deletion works.
- Timed reflection summaries appear automatically and expand on demand into
  exact Scripture, context, attribution, and connection.
- The private Access Pass activates and temporarily reports ten daily analyses;
  reduce it to two before judge handoff.
- Desktop and mobile layouts pass visual inspection.
- The browser console reports zero errors during the checked flows.
- Browser Firestore access is denied; authenticated API access is required.
- The health endpoint returns `ok`; an unauthenticated account request returns
  HTTP 401.
- Cloud Tasks is running with maximum concurrency one and two attempts.
- Cloud Run serves 100% of traffic from the ready revision, scales to zero, and
  has maximum instances one.

The acceptance runs consume private Access allowances. Do not rerun a paid
analysis merely to refresh this document.

The Pip demonstration run used one additional allowance after the temporary
testing limit was raised to ten. Do not rerun it; duplicate-link reuse opens the
stored analysis without provider spend.
