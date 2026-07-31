# Video model capability matrix

Status: **public contracts reviewed 2026-07-31; bounded live calls run
2026-08-01**. The selected public source was supplied for testing by the entrant;
its rights status was not independently verified.

| Dashboard display name | Exact callable API model ID | Input modalities | Video | Audio in video | Files/source reuse | Public YouTube URL | Bounded offsets | Structured output | Relevant input limit | Latency | Tokens | Observed rate behavior | Safety behavior | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Gemini 3.5 Flash-Lite | `gemini-3.5-flash-lite` | Text, image, video, audio, PDF documented | Live pass | Live pass | Public URL reused across windows | Live pass | 0-40 s and 40-80 s live pass; 9-window run complete | Pydantic schema live pass | 1,048,576 input / 65,536 output documented | 5.34 s first; 2.97 s second | 3,943/1,163 first; 4,062/526 second (input/output) | One internal RPM pause in the 9-window run; retry resumed safely | Sensitive source yielded observations, then Gloo `NO_ECHO` | Approved primary for this source |
| Gemini 3.1 Flash-Lite | `gemini-3.1-flash-lite` | Multimodal documented | Listed live | Listed live | Not exercised | Model listed in the live account | Not exercised | Documented | Account listing confirmed | Not measured | Not measured | Not measured | Not exercised | Available fallback; unapproved |
| Gemini 3.5 Flash | `gemini-3.5-flash` | Multimodal documented | Listed live | Listed live | Not exercised | Model listed in the live account | Not exercised | Documented | Account listing confirmed | Not measured | Not measured | Not measured | Not exercised | Available escalation; unapproved |
| NVIDIA Nemotron 3 Nano Omni | `nvidia/nemotron-3-nano-omni-30b-a3b-reasoning` | Not tested | Not tested | Not tested | N/A | Not assumed | Not assumed | Not tested | Not tested | Not measured | Not measured | Not measured | Not tested | Optional and disabled |

## Required evidence discipline

Record only sanitized metadata: provider, exact model, source fingerprint,
requested offsets, modality status, response/schema result, latency, token usage
where supplied, and classified failure. Never commit raw media, API keys,
unredacted transcripts, chain-of-thought, or full model responses.
