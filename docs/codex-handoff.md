# STILL Codex handoff

## Read this first

STILL is a spoiler-safe video reflection application. Missing credentials,
failed providers, or fixture output cannot create a production Echo or make a
new project `READY`.

As of 2026-08-01, one real seven-window project produced an accepted, verified
Echo and a source-bound judge experience is live on Firebase Spark. Anonymous
Auth, Firestore rules, Hosting, code retrieval, real YouTube playback, natural
Story Complete, exact Scripture rendering, and a fresh final-record 0:00 lock
have passed. See `docs/real-e2e-acceptance.md`.

## Product contract

- A viewer watches first; reflections are hidden by the contiguous watched
  frontier and Story Complete gate.
- A worker analyses chronological bounded audiovisual windows with exact
  offsets and immutable prior narrative state.
- Gemini observes, Gloo decides Sacred Timing, and YouVersion is the only source
  rendered as canonical Scripture.
- Title-only, transcript-only, static, random, template, fixture, or
  cached-other-source output may never become a production Echo.
- `NO_ECHO` is a valid, complete outcome. Never weaken it to make a demo look
  more dramatic.
- NVIDIA is optional, disabled, and not a release dependency.

## Current verified status

| Area | Status |
| --- | --- |
| Web UI and playback firewall | Implemented; tests, lint, typecheck, production build, and local browser form inspection pass |
| FastAPI API and worker | 25 tests pass; the entrant's 5:58 URL completed 9/9 full audiovisual windows in the actual worker and ended `READY_NO_ECHO`; accepted seven-window runs also completed |
| Gemini | Accepted source completed seven audiovisual windows using `gemini-3.5-flash-lite` and conservative fallback `gemini-3.1-flash-lite` |
| Gloo | Abstention and acceptance passed; prepared runs cap candidates at one; final passage verification passed |
| YouVersion | Bible 3034 returned exact 1 Corinthians 1:27, BSB, and copyright metadata |
| Firebase | Anonymous Auth, Firestore prepared record/rules, and Hosting deployed at <https://still-scriptures.web.app> |
| Tasks / Cloud Run | Secured arbitrary-YouTube release and deployment automation implemented; deployment blocked only by unlinked Blaze billing |
| NVIDIA | Disabled and untested |
| GitHub | Public `master` currently contains the prepared-demo release; the arbitrary-source hardening changes still need the next commit and push |

The judge source is Dogs Inc's 4:05 public release of “Pip.” STILL embeds the
original; copyright remains with its owners. The public code is
`STILL-JUDGE-2026` and is a demo locator, not a password.

## Secrets and cost controls

- `.env` contains live local credentials and is ignored by Git. Never print,
  commit, screenshot, or copy those values into commands, docs, or provider
  payload evidence.
- The Windows ACL on `.env` is restricted to the current user.
- Gloo is pay-as-you-go. Every production project hard-caps candidates at one;
  the protected release also limits each guest to two analyses and the whole
  app to twenty per day. Current weekly spend remains $0.01 / $5.00 after the
  latest bounded acceptance.
- Production rejects `USE_PROVIDER_FIXTURES=true`.
- The public prepared demo contains no provider credentials and disables open
  submission instead of simulating a backend.

## Evidence already recorded

- `docs/live-verification.md`: sanitized call timings, tokens, and outcomes.
- `docs/video-model-capability-matrix.md`: live Gemini capability matrix.
- `docs/real-e2e-acceptance.md`: exact partial/open acceptance verdict.
- `docs/submission/`: writeup, demo script, readiness checklist, and cover.

## Immediate resume order

1. Ask the owner to link Blaze billing in the Firebase console; never handle or
   request payment details in chat.
2. Run `scripts/deploy-production.ps1`, then complete the public arbitrary-URL
   browser acceptance in `docs/deployment.md`.
3. Commit and push the verified release to
   <https://github.com/PrathmeshAdsod/STILL-Scriptures> on `master`.
4. Record and upload a public YouTube demo no longer than three minutes.
5. Publish/attach the executed Kaggle notebook and create the Kaggle writeup.
6. Preview all links signed out, then ask the entrant before the irreversible
   final Kaggle Submit action.

## Verification commands

```powershell
npm run typecheck
npm run lint
npm run test:web
npm run build
.\.venv\Scripts\python.exe -m pytest apps/api/tests -q
```

Live probes, when explicitly needed, are documented in
`docs/live-verification.md`. They consume real provider quota and must never be
run merely to make documentation appear greener.

## Definition of done

STILL is competition-complete only when every offline check passes, GitHub,
notebook, and demo are public, Kaggle assets are attached, and the entrant has
approved the final submission. Until a real accepted Echo and public interactive
backend exist, describe the current result as:

> Real bounded pipelines produced both an accepted canonical Echo and honest
> NO_ECHO results; a source-bound Firebase judge demo is public; arbitrary
> public-YouTube cloud processing is implemented but awaits Blaze deployment
> and public browser acceptance.
