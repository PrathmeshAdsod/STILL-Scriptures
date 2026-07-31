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

## Production browser and infrastructure checks

- Public landing and Plans pages render correctly signed out.
- Protected routes show an account-required state.
- Email/password sign-in and account allowance retrieval work.
- The private Access Pass activates and reports two daily analyses.
- Desktop and mobile layouts pass visual inspection.
- The browser console reports zero errors during the checked flows.
- Browser Firestore access is denied; authenticated API access is required.
- The health endpoint returns `ok`; an unauthenticated account request returns
  HTTP 401.
- Cloud Tasks is running with maximum concurrency one and two attempts.
- Cloud Run serves 100% of traffic from the ready revision, scales to zero, and
  has maximum instances one.

The acceptance run used one of that day's two Access allowances. Do not rerun a
paid acceptance merely to refresh this document.
