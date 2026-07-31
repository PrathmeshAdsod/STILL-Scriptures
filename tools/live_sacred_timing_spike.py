"""Run one real Gemini observation and exactly one Gloo Sacred Timing decision."""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apps" / "api"))

from app.config import Settings  # noqa: E402
from app.providers.base import PreparedSource, VideoAnalysisRequest  # noqa: E402
from app.providers.gemini import GeminiVideoProvider  # noqa: E402
from app.providers.gloo import GlooSacredTimingProvider  # noqa: E402
from app.schemas import AnalysisOutcome, NarrativeState, SourceKind, SourceRecord  # noqa: E402


async def main() -> int:
    parser = argparse.ArgumentParser(description="Bounded STILL Gemini -> Gloo capability spike")
    parser.add_argument("--source-uri", required=True)
    parser.add_argument("--end", type=float, default=40.0)
    args = parser.parse_args()

    settings = Settings()
    gemini = GeminiVideoProvider(settings)
    gloo = GlooSacredTimingProvider(settings)
    gloo.ensure_configuration()

    source = SourceRecord(
        kind=SourceKind.YOUTUBE,
        public_url=args.source_uri,
        title="Authorized public capability source",
        duration_seconds=args.end,
    )
    prepared = PreparedSource("gemini", args.source_uri, "video/*", f"youtube:{args.source_uri}")
    analysis = await gemini.analyze_window(
        model_id=settings.gemini_primary_model,
        request=VideoAnalysisRequest(
            source=source,
            prepared_source=prepared,
            start_offset_seconds=0,
            end_offset_seconds=args.end,
            narrative_state=NarrativeState(version=0),
            prompt_version="bounded-audiovisual-observation-v2",
            purpose="sacred_timing_capability_spike",
        ),
    )
    eligible = [
        item for item in analysis.observations
        if item.outcome == AnalysisOutcome.ACCEPT and item.candidate_tensions
    ]
    if not eligible:
        print(json.dumps({"status": "NO_GLOO_CALL", "reason": "Gemini returned no eligible ACCEPT candidate."}))
        return 1

    observation = max(eligible, key=lambda item: item.confidence)
    decision = await gloo.decide(
        observation=observation,
        video_context=f"Only presentation time 0-{args.end:.1f} seconds is known. No future scene is available.",
    )
    safe_metadata = {
        key: decision.metadata.get(key)
        for key in ("model", "provider", "model_family", "routing_mechanism", "routing_tier", "routing_confidence", "usage")
    }
    print(
        json.dumps(
            {
                "status": "PASS_REAL_CALL",
                "gemini_model": settings.gemini_primary_model,
                "gemini_modality_status": analysis.modality_status.value,
                "gemini_observation_count": len(analysis.observations),
                "gloo_outcome": decision.outcome.value,
                "gloo_confidence": decision.confidence,
                "selected_reference_present": bool(decision.selected_reference),
                "selected_passage_id_present": bool(decision.selected_passage_id),
                "selected_bible_id_allowed": decision.bible_id in settings.yvp_allowed_bible_ids if decision.bible_id is not None else None,
                "gloo_metadata": safe_metadata,
                "paid_gloo_completion_calls": 1,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
