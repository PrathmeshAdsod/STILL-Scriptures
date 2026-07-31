# Submission readiness checklist

## Deadline discipline

The signed-in Kaggle competition page showed **August 1, 2026 at 10:29 AM
IST**. Target final submission by **9:30 AM IST** and reserve the final hour for
signed-out link checks and Kaggle submission only.

## Inputs and platform

- [x] Local `.env` contains Gemini, Gloo, and YouVersion credentials and is
  ignored by Git.
- [x] YouVersion Bible 3034 is confirmed through a live passage call.
- [ ] A short rights-cleared demo source is confirmed. The current public 5:58
  source was supplied by the entrant, but rights were not independently checked
  and its real outcome is `NO_ECHO`.
- [x] Firebase Hosting is usable on the Spark project.
- [ ] Firestore, Tasks, Run, and Storage are not deployed; the public site is a
  clearly labeled static showcase.
- [x] Solo participation was confirmed by the entrant.

## Proof gates

- [x] Gemini model listing and two bounded audiovisual calls pass on the real
  source.
- [x] One paid Gloo Completions V2 call returns a valid required-tool Sacred
  Timing decision.
- [x] YouVersion returns an exact licensed passage plus version and copyright
  metadata.
- [x] The local worker completes 9/9 windows and demonstrates resumable retry.
- [ ] A real source produces an accepted, verified, persisted Scripture Echo.
- [ ] Public UI passes the full add -> prepare -> watch -> frontier -> Story
  Complete -> exact Scripture flow. Spark Hosting is static only.

## Public package

- [x] Firebase showcase opens publicly at <https://still-scriptures.web.app>.
- [x] Public GitHub repository is pushed and opens signed out.
- [x] Local Kaggle notebook executes top-to-bottom and contains no credentials.
- [ ] Notebook is attached publicly to the Kaggle writeup.
- [ ] Public YouTube demo is 3:00 or shorter and plays signed out.
- [x] `still-cover.png` is ready at Kaggle's 2:1 aspect ratio (1120 x 560).
- [ ] Replace the demo placeholder in `kaggle-writeup.md`; final text remains
  under 500 words.
- [x] Claims distinguish live provider checks, local E2E, static deployment,
  and still-open gates.

## Final Kaggle pass

- [ ] Correct Kaggle account and solo team are selected.
- [ ] Writeup title, subtitle, cover, media, notebook, video, and public project
  link are attached.
- [ ] Preview every link in a signed-out browser.
- [ ] Submit once, record confirmation, and do not submit from another account.
