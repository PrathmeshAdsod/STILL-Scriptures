# Submission readiness checklist

## Deadline discipline

The signed-in competition page showed **August 1, 2026 at 10:29 AM IST**.
Reserve the final hour for signed-out link checks and the Kaggle submission.

## Product and security

- [x] Public application is live at <https://still-scriptures.web.app>.
- [x] Firebase email/password sign-up, verification, sign-in, sign-out, and
  password reset are deployed.
- [x] Anonymous authentication is disabled; browser Firestore access is denied.
- [x] Private test credentials and Access Pass are absent from tracked files
  and the public UI.
- [x] Runtime provider keys are in Secret Manager, not the browser bundle.
- [x] Free and Access Pass allowances are enforced server-side with atomic
  reservations.
- [x] Owner-scoped My Videos, duplicate-link reuse, cross-device watch resume,
  project deletion, and complete account deletion are deployed.
- [x] Six-minute per-video and twenty-per-day global limits are enforced.
- [x] Cloud Tasks concurrency and Cloud Run maximum instances are both one.
- [x] The private Access Pass is temporarily 10 analyses/day for testing; the
  global cap remains 20/day and Gemini escalation remains disabled.
- [x] Solo participation was confirmed by the entrant.

## Proof gates

- [x] Gemini live audiovisual analysis is verified.
- [x] Gloo structured abstention and accepted-candidate paths are verified.
- [x] YouVersion exact passage, version, and attribution retrieval is verified.
- [x] A real accepted and verified Scripture Echo has been persisted for a
  suitable source.
- [x] The entrant's 5:58 test URL completed 9/9 full audiovisual windows through
  the hosted authenticated API in about 84 seconds.
- [x] That test ended `READY_NO_ECHO`, demonstrating honest abstention rather
  than a fabricated result.
- [x] The 4:05 Pip demo completed 7/7 windows and persisted two verified timed
  reflections at 2:00 and 3:20.
- [x] Production gates proved 0/1/2 visible reflections at 0:00/2:01/3:21,
  expandable exact Scripture, and two-reflection Story Complete.
- [x] The Firestore watch-progress 500 and direct-route auth race are fixed and
  production-tested.
- [x] Production browser QA passed desktop and mobile flows with zero console
  errors.
- [x] 35 API tests, 5 web tests, typecheck, lint, and production build pass.

## Public package

- [x] Public GitHub repository is pushed and opens signed out.
- [x] Public product link opens signed out; interaction requires a real account.
- [x] A private Access account is ready to share with judges outside the public
  submission materials.
- [x] Local Kaggle notebook executes top-to-bottom and contains no credentials.
- [ ] Notebook is attached publicly to the Kaggle writeup.
- [ ] Public YouTube demo is 3:00 or shorter and plays signed out.
- [x] `still-cover.png` is ready at 1120 x 560.
- [ ] Replace the demo placeholder in `kaggle-writeup.md`.

## Final Kaggle pass

- [ ] Reduce the private Access Pass from 10 analyses/day back to 2 and redeploy
  before the judge handoff.
- [ ] Correct Kaggle account and solo team are selected.
- [ ] Title, subtitle, cover, media, notebook, video, and public product link are
  attached.
- [ ] Preview every link in a signed-out browser.
- [ ] Share credentials only through the private judge channel, never in the
  public writeup, repository, recording, or screenshots.
- [ ] Submit once, record confirmation, and do not submit from another account.
