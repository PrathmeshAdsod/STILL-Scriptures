# Prepared Demo provenance

Status: **created and deployed 2026-08-01**.

## Exact source

- Title: “Pip — Small Steps, Steady Courage”
- Original embed: <https://www.youtube.com/watch?v=07d2dXHYb94>
- Duration: 245 seconds
- Publisher: Dogs Inc
- Rights note: Dogs Inc produced and publicly published this guide-dog story on
  its own channel. Copyright remains with its owners. STILL embeds the original
  YouTube player and does not rehost media.
- The stored SHA-256 is a source-locator hash, not a downloaded-content hash.

## Provider-backed evidence

- Pipeline: `still-causal-v2`
- Prompt: `bounded-audiovisual-observation-v2`
- Gemini: seven bounded chronological windows; models
  `gemini-3.5-flash-lite` and `gemini-3.1-flash-lite`; full audiovisual mode
  observed during the bounded gate.
- Gloo: Completions V2; one-candidate project cap; accepted one candidate and
  accepted the canonical-passage verification under the strengthened v2
  proportionality policy.
- YouVersion: Bible 3034; exact 1 Corinthians 1:27; BSB; copyright attribution
  present.
- Persisted Echo cutoff: 200 seconds.
- The v2 Sacred Timing policy explicitly rejects superficial wordplay,
  disproportionate moral labels, and connections that must disclaim their own
  mismatch. It was added after editorial QA rejected an earlier technically
  accepted but morally disproportionate demo result; that record was replaced.
- Firestore publication occurs only when project status is `READY`, at least
  one verified Echo exists, and the top-level outcome is `ACCEPTED_ECHO`.

## Public boundary

The access code `STILL-JUDGE-2026` is normalized and SHA-256 hashed before the
document lookup. It is a public demo locator, not a password. Firebase Anonymous
Auth is enabled. Rules allow an authenticated `get` of one prepared-demo
document, deny collection listing, and deny every browser write.

The prepared record contains no raw provider response, provider credential,
user identity, opaque provider source reference, or unpublished media. It may
be used only for this exact labelled source and cannot answer a new submission.
