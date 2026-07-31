# Video model capability matrix

Status: **public contracts reviewed 2026-07-31; bounded live calls run
2026-08-01**. The final judge source is Dogs Inc's own public YouTube release of
“Pip”; copyright remains with its owners and STILL does not rehost it.

| Dashboard display name | Exact callable API model ID | Input modalities | Video | Audio in video | Files/source reuse | Public YouTube URL | Bounded offsets | Structured output | Relevant input limit | Latency | Tokens | Observed rate behavior | Safety behavior | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Gemini 3.5 Flash-Lite | `gemini-3.5-flash-lite` | Text, image, video, audio, PDF documented | Live pass | Live pass | Public URL reused across windows | Live pass | Multiple 0-40 s / 40-80 s gates; 9-, 5-, and 7-window runs | Pydantic schema live pass | 1,048,576 input / 65,536 output documented | Source-dependent; sanitized timings recorded in live evidence | Usage metadata captured | Conservative RPM ledger and durable resume passed | Sensitive source yielded `NO_ECHO`; final Pip source yielded a later bounded candidate | Approved primary |
| Gemini 3.1 Flash-Lite | `gemini-3.1-flash-lite` | Multimodal documented | Live pass | Live pass | Public URL reused | Live pass | Exercised as conservative fallback in accepted seven-window runs | Pydantic schema live pass | Account listing confirmed | Sanitized in Firestore provenance | Usage metadata captured | Selected when the primary's local RPM budget was unavailable | Full audiovisual fallback contributed to an accepted run | Approved fallback |
| Gemini 3.5 Flash | `gemini-3.5-flash` | Multimodal documented | Listed live | Listed live | Not exercised | Model listed in the live account | Not exercised | Documented | Account listing confirmed | Not measured | Not measured | Not measured | Not exercised | Available escalation; unapproved |
| NVIDIA Nemotron 3 Nano Omni | `nvidia/nemotron-3-nano-omni-30b-a3b-reasoning` | Not tested | Not tested | Not tested | N/A | Not assumed | Not assumed | Not tested | Not tested | Not measured | Not measured | Not measured | Not tested | Optional and disabled |

## Required evidence discipline

Record only sanitized metadata: provider, exact model, source fingerprint,
requested offsets, modality status, response/schema result, latency, token usage
where supplied, and classified failure. Never commit raw media, API keys,
unredacted transcripts, chain-of-thought, or full model responses.
