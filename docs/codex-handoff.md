# STILL Codex handoff

## Read this first

STILL is a spoiler-safe video reflection application. Missing credentials,
failed providers, or fixture output cannot create a production Echo or make a
new project `READY`.

As of 2026-08-01, bounded calls to Gemini, Gloo, and YouVersion have passed, a
real local 9-window project completed as `READY_NO_ECHO`, and the credential-free
Firebase Hosting showcase is live. The two full acceptance gates remain open;
see `docs/real-e2e-acceptance.md`.

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
| Web UI and playback firewall | Implemented; tests, lint, typecheck, and production build pass |
| FastAPI API and worker | 16 tests pass; local real worker completed 9/9 windows |
| Gemini | `gemini-3.5-flash-lite` passed 0-40 s and 40-80 s audiovisual calls; account also lists fallback/escalation models |
| Gloo | One paid required-tool call passed as `NO_ECHO`; worker cap is two candidates per project |
| YouVersion | Bible 3034 returned an exact passage, version, and copyright metadata |
| Firebase Hosting | Static Spark showcase deployed at <https://still-scriptures.web.app> |
| Firestore / Tasks / Cloud Run | Not deployed because this architecture requires billing |
| NVIDIA | Disabled and untested |
| GitHub | Publication is the next release step; GitHub CLI is absent |

The selected 5:58 public source is sensitive 26/11 material. Gemini completed
the analysis and Gloo correctly returned `NO_ECHO`. The source was supplied by
the entrant, but its rights status was not independently verified. A short
rights-cleared positive source is still needed to demonstrate a persisted Echo.

## Secrets and cost controls

- `.env` contains live local credentials and is ignored by Git. Never print,
  commit, screenshot, or copy those values into commands, docs, or provider
  payload evidence.
- The Windows ACL on `.env` is restricted to the current user.
- Gloo is pay-as-you-go. `GLOO_MAX_CANDIDATES_PER_PROJECT=2`; one paid probe has
  already been run. Do not make another unbounded call.
- Production rejects `USE_PROVIDER_FIXTURES=true`.
- The public showcase contains no provider credentials and disables interactive
  submission instead of simulating a backend.

## Evidence already recorded

- `docs/live-verification.md`: sanitized call timings, tokens, and outcomes.
- `docs/video-model-capability-matrix.md`: live Gemini capability matrix.
- `docs/real-e2e-acceptance.md`: exact partial/open acceptance verdict.
- `docs/submission/`: writeup, demo script, readiness checklist, and cover.

## Immediate resume order

1. Run all offline checks and secret scan before publication.
2. Commit and push the intended repository to
   <https://github.com/PrathmeshAdsod/STILL-Scriptures> on `master`, as explicitly
   requested by the entrant.
3. Attach or create a short rights-cleared positive source, run one bounded
   project, and stop if Gloo returns `NO_ECHO`; never force an Echo.
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

> Bounded integrations live-verified; local sensitive-source run completed
> safely as No Echo; static public showcase deployed; full Echo and deployed E2E
> acceptance remain open.
