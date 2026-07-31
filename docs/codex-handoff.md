# STILL Codex handoff

## Read this first

STILL is a real, hosted, spoiler-safe video reflection product. Missing
credentials, failed providers, or fixture output cannot create a production
Echo. `NO_ECHO` is a valid complete result and must never be weakened to make
a demo look more dramatic.

As of 2026-08-01, the public application is live at
<https://still-scriptures.web.app>. Firebase email/password authentication,
Firestore, Cloud Tasks, Cloud Run, Secret Manager, and Hosting are deployed.
The arbitrary-video cloud gate passed on the entrant's 5:58 source: 9/9 full
audiovisual windows completed in about 84 seconds with an honest
`READY_NO_ECHO` result.

## Product contract

- The viewer watches first; reflections remain behind the contiguous watched
  frontier and Story Complete gate.
- Gemini analyzes chronological bounded audiovisual windows with exact offsets
  and immutable prior narrative state.
- Gloo decides Sacred Timing and may accept, hold, reject, or remain silent.
- YouVersion is the only source rendered as canonical Scripture.
- Title-only, transcript-only, static, random, template, fixture, or
  other-source cached output may never become a production Echo.
- NVIDIA is optional, disabled, and not a release dependency.

## Verified status

| Area | Status |
| --- | --- |
| Product UI | Public landing, auth, Plans, account, add, processing, watch, completion, and reflection flows implemented |
| Authentication | Email/password sign-up, verification, sign-in, sign-out, and password reset deployed; anonymous auth disabled |
| API and worker | 27 tests pass; deployed Cloud Tasks worker completed 9/9 windows for the 5:58 acceptance source |
| Gemini | Live bounded full-audiovisual analysis verified |
| Gloo | Live abstention and accepted-candidate paths verified; production candidate cap is one |
| YouVersion | Exact canonical passage, version, and copyright metadata verified |
| Firebase and Google Cloud | Hosting, Auth, Firestore, Tasks, Run, and Secret Manager deployed |
| Browser QA | Desktop and mobile production checks pass with zero console errors |
| GitHub | Public `master` is the release branch |

## Accounts, access, and cost

- Free accounts receive one analysis total, with a maximum video length of six
  minutes.
- A privately issued Access Pass grants two analyses per UTC day, also limited
  to six minutes each.
- Payments are intentionally absent from this competition release.
- The private test account and Access Pass are handed to the owner outside the
  repository. Never copy them into code, docs, screenshots, commits, logs, or
  competition text.
- The production global cap is twenty analyses per UTC day.
- Cloud Tasks concurrency is one, Cloud Run maximum instances is one, and each
  project permits at most one paid Gloo candidate.
- Live provider probes spend quota. Do not rerun them merely to make evidence
  look newer.

## Secret handling

- `.env` and the generated private-access handoff are ignored by Git.
- Their Windows ACLs are restricted to the current user and SYSTEM.
- Runtime secrets are held in Secret Manager and are never bundled into the
  web client.
- Rotate the temporary competition credentials after the demo as planned.

## Resume order

1. Check `git status` and ensure the local release matches public `master`.
2. Open the public app signed out, then sign in with the private account without
   exposing its password on screen.
3. Confirm the account allowance before spending a live run.
4. Record and upload the public demo, then replace the video placeholder in the
   competition writeup.
5. Attach the executed Kaggle notebook and public links.
6. Preview every link signed out and let the entrant perform the final Kaggle
   submission.

## Verification commands

```powershell
npm run typecheck
npm run lint
npm run test:web
npm run build
.\.venv\Scripts\python.exe -m pytest apps/api/tests -q
```

Provider evidence is documented in `docs/live-verification.md`; deployed
acceptance is in `docs/real-e2e-acceptance.md`.
