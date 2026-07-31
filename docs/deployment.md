# Deployment

## Required services

- Firebase Authentication, Firestore, Storage, and Hosting.
- Artifact Registry, Cloud Run, Cloud Tasks, and a service account for task OIDC.
- Gemini, Gloo, and YouVersion credentials stored in Secret Manager or equivalent runtime secrets.

Enable the chosen Firebase Authentication provider. The web client uses anonymous sign-in only in development; production uses Firebase Google sign-in and must have that provider enabled and the deployed domain authorized.

## Cloud Run

1. Build `apps/api/Dockerfile` from the repository root.
2. Deploy the API private (`--no-allow-unauthenticated`).
3. Create a dedicated Cloud Tasks invoker service account, set it as `WORKER_INVOKER_SERVICE_ACCOUNT`, and grant it `roles/run.invoker` on the API service.
4. Give the API service account minimum Firestore, Storage, Task enqueue, and secret access roles.
5. Inject `APP_MODE=production`, `USE_PROVIDER_FIXTURES=false`, and `LOCAL_WORKER_ENABLED=false`.

`scripts/deploy-cloud-run.ps1` accepts the non-secret deployment values explicitly, including the Cloud Run runtime service account, Firebase Storage bucket, worker URL, and the Cloud Tasks OIDC invoker service account. It deliberately does not put provider keys in a command line or source file; attach those as Cloud Run Secret Manager environment variables.

## Gemini Cloud Storage source registration

For a Firebase Storage upload, STILL does not send a browser URL or re-upload the video for every causal window. The worker registers the `gs://` object once with Gemini Files API, persists the returned opaque Gemini file URI on the project, and reuses that URI with the requested start/end offsets.

Before a live run, grant the runtime service account read access to the source bucket and grant the Gemini service agent `Storage Object Viewer` on that bucket. The runtime must also have Application Default Credentials available. Validate this with the Milestone 1B source-reuse check; do not substitute a public URL or an unregistered `gs://` URI if registration fails.

## Cloud Tasks

Create a queue named by `CLOUD_TASKS_QUEUE`. Tasks target `POST /internal/jobs/{jobId}` with OIDC. Cloud Run IAM rejects public callers; the application additionally rejects missing task headers in production.

The runtime service account needs narrow roles for Firestore, the configured Firebase Storage bucket, Cloud Tasks enqueue, and secret access. The Cloud Tasks invoker service account needs only `roles/run.invoker` on this service.

## Hosting

Build the web app, set `VITE_API_BASE_URL` to the API gateway/domain and Firebase client variables, then deploy the `apps/web/dist` directory via Firebase Hosting.

## Pre-deploy checks

Run all local checks, compile/validate rules with Firebase tooling, build the Docker image, and only then run the real acceptance gates. Docker, Firebase CLI, gcloud, and FFmpeg were not present in the initial local environment, so their execution remains pending until those tools/access are supplied.
