# Production deployment

## Current state

The complete product is live at <https://still-scriptures.web.app> on Firebase
Hosting. `/api` is rewritten to the owned FastAPI service on Cloud Run. The
runtime uses Firestore, Cloud Tasks, Secret Manager, Firebase Authentication,
and the YouTube Data API.

The deployed app requires verified Firebase email/password authentication for
processing. It does not use anonymous authentication, publish private access
credentials, or simulate results. Authenticated users receive an owner-scoped
My Videos library; results and viewing sessions persist in Firestore, and an
already analyzed YouTube ID reopens without reserving another allowance.

## Releasing

Run from the repository root:

```powershell
.\scripts\deploy-production.ps1
```

The idempotent script:

1. verifies billing and enables the required Google Cloud APIs;
2. creates narrow runtime and task service accounts;
3. copies ignored local secrets into Secret Manager without printing values;
4. provisions a YouTube API key restricted to `youtube.googleapis.com`;
5. builds the FastAPI container with Cloud Build;
6. deploys Cloud Run with zero minimum instances, one maximum instance,
   concurrency 20, and an 1,800-second timeout;
7. configures a one-at-a-time Cloud Tasks queue with two attempts at most;
8. builds the web client for same-origin `/api` calls;
9. deploys Hosting, Firestore rules, and indexes; and
10. runs a production health probe.

Use `-ImageTag` to reuse an existing container image when only deployment
configuration or the web client changed.

## Runtime security

- Every user API route verifies a Firebase ID token, verified email, and
  project ownership.
- `/internal/jobs/{jobId}` accepts only Cloud Tasks requests with a verified
  Google OIDC token, expected audience, and expected service-account email.
- Browser Firestore reads, listing, and writes are denied.
- Provider and metadata credentials are mounted from Secret Manager and never
  compiled into Vite.
- Production refuses fixtures, a local worker, missing authoritative YouTube
  metadata, and more than one Gloo candidate.
- Firebase email-enumeration protection is enabled and the enforced password
  policy requires at least 12 characters.
- Account deletion removes owned application data and the Firebase
  Authentication user. The runtime service account has only the additional
  `firebaseauth.users.get` and `firebaseauth.users.delete` permissions needed
  for that lifecycle operation.

## Plans and hard limits

- Free: one analysis for the lifetime of a verified account.
- Access Pass: ten analyses per UTC day during final testing; the release
  owner will reduce this to two for judge access.
- Every video: authoritative duration of 6:00 or less.
- Entire service: twenty analysis reservations per UTC day.
- One Cloud Tasks dispatch at a time and one Cloud Run instance at most.
- At most three temporally distinct Gloo candidates per project; escalation
  budget is zero.

The API creates atomic Firestore reservations before queueing work. Repeated or
concurrent requests therefore cannot race past an account or global limit.
Cloud billing alerts remain useful notifications, but these application and
infrastructure limits are the actual cost controls.

## Acceptance evidence

On 2026-08-01, the entrant-selected 5:58 YouTube URL was submitted through the
hosted authenticated API. The Cloud Tasks worker completed 9/9 full
audiovisual windows in about 84 seconds and reached `READY_NO_ECHO`. That
conservative outcome proves arbitrary-source processing without inventing a
Scripture connection.

The final demonstration source, Dogs Inc's 4:05 “Pip,” then completed 7/7
windows through the same hosted account and worker. Four grounded candidates
across 2:00, 2:40, and 3:20 produced two verified BSB reflections: Hebrews 12:1
at 2:00 and Hebrews 13:16 at 3:20. Production QA proved zero reflections at
0:00, one after 2:00, both after 3:20, and both on Story Complete.

Production browser QA also passed landing, Plans, account creation/sign-in
flows, private Access Pass state, saved-library reopening, duplicate-link reuse,
protected routes, responsive layout, and a zero-error console check. A
disposable verified account proved end-to-end deletion and old-token rejection.
The deployed API health endpoint returns `ok`, an
unauthenticated account request returns HTTP 401, the task queue is running
with max concurrency 1, and the current Cloud Run service serves 100% of
traffic with max instances 1.

Before a recording or competition handoff, repeat the signed-out landing check,
sign in with the privately supplied account, confirm the remaining allowance,
and submit only a video you are prepared to spend live provider quota on.
