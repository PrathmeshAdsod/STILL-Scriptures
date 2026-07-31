"""Run only with approved credentials and a rights-cleared source. Never produces a fake pass."""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apps" / "api"))

from app.config import get_settings  # noqa: E402
from app.providers.gemini import GeminiVideoProvider  # noqa: E402
from app.providers.base import ProviderFailure, VideoAnalysisRequest  # noqa: E402
from app.schemas import NarrativeState, SourceKind, SourceRecord  # noqa: E402


async def main() -> int:
    parser = argparse.ArgumentParser(description="STILL Milestone 1B Gemini bounded audiovisual capability spike")
    parser.add_argument("--source-uri", required=True, help="Public YouTube URL, gs:// URI, or Gemini file URI")
    parser.add_argument("--mime-type", default="video/*")
    parser.add_argument("--duration", type=float, required=True)
    parser.add_argument("--models", nargs="*", help="Callable IDs to test; defaults to configured Gemini pool")
    args = parser.parse_args()
    settings = get_settings()
    if not settings.gemini_api_key:
        print(json.dumps({"status": "BLOCKED_MISSING_CREDENTIALS", "provider": "gemini", "message": "GEMINI_API_KEY is missing"}))
        return 2
    provider = GeminiVideoProvider(settings)
    try:
        from google import genai
        client = genai.Client(api_key=settings.gemini_api_key)
        listed_models = []
        for model in client.models.list():
            name = getattr(model, "name", None)
            if name:
                listed_models.append(str(name))
    except Exception as error:
        print(json.dumps({"status": "FAILED_CAPABILITY_TEST", "provider": "gemini", "message": f"models.list failed: {error}"}))
        return 1
    kind = SourceKind.YOUTUBE if "youtube.com" in args.source_uri or "youtu.be" in args.source_uri else SourceKind.UPLOAD
    source = SourceRecord(kind=kind, public_url=args.source_uri if kind == SourceKind.YOUTUBE else None, storage_path=args.source_uri if kind == SourceKind.UPLOAD else None, title="Milestone 1B rights-cleared source", duration_seconds=args.duration, content_type=args.mime_type)
    try:
        # GCS sources must prove Files API registration and reuse. Public
        # YouTube sources retain their original URI where supported.
        prepared = await provider.prepare_source(source)
    except ProviderFailure as error:
        print(json.dumps({"status": "FAILED_CAPABILITY_TEST", "provider": "gemini", "failure_class": error.failure_class.value, "message": str(error)[:500]}))
        return 1
    models = args.models or [settings.gemini_primary_model, settings.gemini_fallback_model, settings.gemini_escalation_model]
    evidence: list[dict] = []
    for model in models:
        try:
            first_end = min(40, args.duration)
            first = await provider.analyze_window(
                model_id=model,
                request=VideoAnalysisRequest(
                    source=source,
                    prepared_source=prepared,
                    start_offset_seconds=0,
                    end_offset_seconds=first_end,
                    narrative_state=NarrativeState(version=0),
                    prompt_version="bounded-audiovisual-observation-v1",
                    purpose="capability_spike",
                ),
            )
            intervals = [[0, first_end]]
            second = None
            if args.duration > first_end:
                second_end = min(args.duration, first_end + 40)
                second = await provider.analyze_window(
                    model_id=model,
                    request=VideoAnalysisRequest(
                        source=source,
                        prepared_source=prepared,
                        start_offset_seconds=first_end,
                        end_offset_seconds=second_end,
                        narrative_state=first.narrative_state,
                        prompt_version="bounded-audiovisual-observation-v1",
                        purpose="capability_spike",
                    ),
                )
                intervals.append([first_end, second_end])
            evidence.append({
                "model": model,
                "status": "PASS_REAL_CALL",
                "registered_source_reused": prepared.source_reference != args.source_uri if args.source_uri.startswith("gs://") else None,
                "bounded_intervals": intervals,
                "first_window": {
                    "modality_status": first.modality_status.value,
                    "audio_evidence_present": any(item.evidence.observed_voice_or_delivery or item.evidence.observed_spoken_content for item in first.observations),
                    "visual_evidence_present": any(item.evidence.observed_visual_action for item in first.observations),
                    "audience_evidence_present": any(item.evidence.observed_audience_response for item in first.observations),
                    "schema_validated_observations": len(first.observations),
                    "candidate_observations": sum(item.outcome.value == "ACCEPT" and bool(item.candidate_tensions) for item in first.observations),
                    "outcome_counts": {
                        outcome: sum(item.outcome.value == outcome for item in first.observations)
                        for outcome in sorted({item.outcome.value for item in first.observations})
                    },
                    "latency_ms": first.raw_provider_metadata.get("latency_ms"),
                    "token_usage": first.token_usage,
                },
                "second_window": None if second is None else {
                    "modality_status": second.modality_status.value,
                    "input_narrative_version": first.narrative_state.version,
                    "output_narrative_version": second.narrative_state.version,
                    "schema_validated_observations": len(second.observations),
                    "latency_ms": second.raw_provider_metadata.get("latency_ms"),
                    "token_usage": second.token_usage,
                },
            })
        except Exception as error:
            classified = error if isinstance(error, ProviderFailure) else provider.classify_failure(error)
            evidence.append({"model": model, "status": "FAILED_CAPABILITY_TEST", "failure_class": classified.failure_class.value, "message": str(classified)[:500]})
    print(json.dumps({"source_uri_redacted": args.source_uri.split("?")[0], "listed_model_ids": listed_models, "results": evidence}, indent=2))
    return 0 if any(item["status"] == "PASS_REAL_CALL" for item in evidence) else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
