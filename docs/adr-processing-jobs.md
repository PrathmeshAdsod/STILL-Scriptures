# ADR: Durable causal jobs

The browser creates one idempotent analysis job. The API persists the job and project state before enqueueing a Cloud Task. Cloud Run processes one causal window at a time, writes each checkpoint, and can retry/resume without duplicate provenance or Echoes. The browser-facing API requires Firebase authentication; the worker route separately verifies the Cloud Tasks OIDC audience and service-account identity.

Development may opt into a local worker only with `LOCAL_WORKER_ENABLED=true`; it still calls actual providers and fails transparently if they are unavailable. Production cannot start with that switch enabled.
