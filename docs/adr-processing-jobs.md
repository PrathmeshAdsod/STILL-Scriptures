# ADR: Durable causal jobs

The browser creates one idempotent analysis job. The API persists the job and project state before enqueueing a Cloud Task. A private Cloud Run worker processes one causal window at a time, writes each checkpoint, and can retry/resume without duplicate provenance or Echoes.

Development may opt into a local worker only with `LOCAL_WORKER_ENABLED=true`; it still calls actual providers and fails transparently if they are unavailable. Production cannot start with that switch enabled.
