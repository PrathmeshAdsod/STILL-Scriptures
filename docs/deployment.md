# Deployment

## Current public state

Firebase Hosting serves <https://still-scriptures.web.app>. Anonymous Auth and
read-only Firestore access provide the source-bound prepared demo. Provider
credentials are absent from the browser.

The arbitrary public-YouTube backend is implemented but not yet deployed. The
project is still on Spark with no Cloud Billing account linked. Firebase's
official pricing documentation requires Blaze for Cloud Run and Cloud
Functions production services, even when use remains within a no-cost quota.

## Owner action required once

Open the Firebase project billing page and upgrade `still-scriptures` from
Spark to Blaze by linking a Cloud Billing account. Do not paste payment details
into a chat or terminal. After the console shows Blaze, run:

```powershell
.\scripts\deploy-production.ps1
```

The script checks billing before provisioning anything. It is idempotent and
performs the following guarded release:

1. enables Artifact Registry, Cloud Build, Cloud Run, Cloud Tasks, Secret
   Manager, Firestore, and the YouTube Data API;
2. creates narrow runtime and task identities;
3. copies provider values from the ignored `.env` into Secret Manager without
   printing them;
4. attaches a separate API key restricted to `youtube.googleapis.com`;
5. builds the FastAPI container with Cloud Build;
6. deploys Cloud Run with min instances `0`, max instances `1`, concurrency
   `20` so status polling remains responsive during the one active worker, and
   an 1,800-second request timeout;
7. creates a one-at-a-time Cloud Tasks queue with at most two attempts;
8. builds the web client with `VITE_PUBLIC_SHOWCASE=false` and same-origin
   `/api` calls;
9. deploys the Firebase Hosting rewrite and Firestore rules/indexes; and
10. performs a Cloud Run health check.

## Runtime security

Cloud Run permits network access because the browser must reach the owned API,
but that does not make application data anonymous:

- every `/api` route verifies a Firebase ID token and project ownership;
- `/internal/jobs/{jobId}` requires both a Cloud Tasks header and a verified
  Google OIDC token whose audience and service-account email match the runtime
  configuration;
- browser Firestore writes remain denied;
- Gemini, Gloo, YouVersion, and YouTube metadata keys are mounted from Secret
  Manager, never compiled into Vite; and
- production refuses fixtures, a local worker, more than one Gloo candidate,
  or missing authoritative YouTube metadata credentials.

## Cost and abuse controls

The competition release accepts only public or unlisted, embeddable YouTube
videos with an authoritative duration of 6:00 or less. It enforces:

- two real analyses per anonymous Firebase user per UTC day;
- twenty real analyses globally per UTC day;
- an atomic Firestore reservation before a job is queued;
- at most one paid Gloo candidate per project;
- zero escalation-model allowance in the deployment configuration;
- Cloud Run scale-to-zero with at most one instance; and
- one Cloud Tasks dispatch at a time.

The YouTube `videos.list` metadata check costs one YouTube API quota unit and
does not call Gemini or Gloo. Google Cloud budget alerts are still recommended,
but alerts do not cap charges. The application limits above are the hard usage
controls.

## Acceptance after deployment

Do not call the release complete after a successful build alone. Through the
public Hosting URL, verify:

1. a fresh anonymous guest can paste the entrant-selected 5:58 URL;
2. the server reports the authoritative duration and queues exactly one job;
3. Firestore progress reaches 9/9 windows and a terminal `READY` or
   `READY_NO_ECHO` state;
4. YouTube playback loads and seeking does not advance the contiguous frontier;
5. Story Complete requires natural ending plus contiguous coverage;
6. any rendered Scripture contains exact YouVersion text, version, and
   attribution; and
7. the prepared sample remains available from the fallback link.

The already completed local application-worker acceptance for that URL ended
`READY_NO_ECHO` with 9/9 `FULL_AUDIOVISUAL` windows in about 82 seconds. The
public deployment must still repeat the complete browser path.
