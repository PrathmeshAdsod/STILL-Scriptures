# ADR: Select the Gloo Sacred Timing endpoint

Status: **Completions V2 selected; one live `NO_ECHO` spike passed; full decision suite pending**

## Candidates

1. Gloo Responses API: evaluate typed/schema output, OpenAI-compatible usage,
   Sacred Timing decisions, passage selection, abstention, and rejection.
2. Gloo Completions V2: evaluate routing, values alignment, guardrails,
   tradition configuration, model control, and structured JSON reliability.

## Decision rule

Use the smallest endpoint or endpoint combination that passes the same
versioned Sacred Timing probes reliably. Do not use both merely to increase
integration count.

## Evidence to record

- credential/authentication method verified without storing secrets;
- exact endpoint and model/routing configuration;
- valid-schema rate and invalid-output behavior;
- ACCEPT, REJECT, ABSTAIN, NO_ECHO, and REJECT_ALL_SCRIPTURE behavior;
- latency and retry behavior;
- chosen endpoint, rejected alternative, and rationale.

## Decision

Use **Completions V2** for the competition build. Its documented contract has
the controls STILL requires: OAuth2 client credentials, auto-routing, optional
Christian tradition alignment, and required tool selection for schema-shaped
Sacred Timing decisions. The general Christian perspective is represented by
omitting `tradition`; `not_faith_specific` is not sent because it cannot be
combined with auto-routing.

On 2026-08-01, one paid credentialed call returned a valid required-tool
`NO_ECHO` decision with confidence 1.0 for the entrant-selected sensitive
source. That verifies authentication, endpoint compatibility, auto-routing,
tool selection, and schema parsing for this path. ACCEPT, REJECT, ABSTAIN, and
REJECT_ALL_SCRIPTURE remain unverified and must not be claimed as passed.

## Implemented evidence-based candidate

The offline implementation now follows the documented Completions V2 path:
OAuth2 client-credentials bearer token, `POST /ai/v2/chat/completions`, exactly one
`auto_routing` mechanism, and required function tools for structured output.
The Responses API remains intentionally unimplemented because Completions V2
already supplies the values-alignment and routing controls used by this design.
It may be reconsidered only if a real capability spike exposes a concrete gap.
