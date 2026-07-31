"""Run and publish one exact provider-backed judge demo.

The script never publishes fixtures or a NO_ECHO result as an accepted Echo.
It uses a single Gloo candidate cap and writes a sanitized read-only document
only after Gemini, Gloo, YouVersion, and Gloo passage verification all pass.
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import shutil
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from uuid import NAMESPACE_URL, uuid5

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apps" / "api"))

from google.oauth2.credentials import Credentials  # noqa: E402

from app.config import Settings  # noqa: E402
from app.providers import GeminiVideoProvider, GlooSacredTimingProvider, YouVersionClient  # noqa: E402
from app.repositories import FirestoreDataStore  # noqa: E402
from app.routing import ModelUsageBudgetLedger, VideoModelRouter, load_model_policies  # noqa: E402
from app.schemas import AnalysisJob, Project, ProjectStatus, SourceKind, SourceRecord  # noqa: E402
from app.worker import CausalAnalysisWorker  # noqa: E402


def active_user_credentials() -> Credentials:
    gcloud = shutil.which("gcloud") or shutil.which("gcloud.cmd")
    if not gcloud:
        raise RuntimeError("The Google Cloud CLI is unavailable.")
    token = subprocess.run(
        [gcloud, "auth", "print-access-token"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    if not token:
        raise RuntimeError("No active Google Cloud credential is available.")
    return Credentials(token=token)


def echo_payload(echo) -> dict:
    return {
        "id": str(echo.id),
        "project_id": str(echo.project_id),
        "knowledge_cutoff_seconds": echo.knowledge_cutoff_seconds,
        "first_view_interpretation": echo.first_view_interpretation,
        "after_story_interpretation": echo.after_story_interpretation,
        "tension": echo.tension,
        "scene_context": echo.scene_context,
        "scripture_reference": echo.scripture_reference,
        "bible_version": echo.bible_version,
        "exact_scripture_text": echo.exact_scripture_text,
        "copyright_attribution": echo.copyright_attribution,
        "connection_explanation": echo.connection_explanation,
        "confidence": echo.confidence,
    }


async def run(args: argparse.Namespace) -> int:
    settings = Settings(
        firebase_project_id=args.firebase_project,
        gloo_max_candidates_per_project=1,
    )
    gloo = GlooSacredTimingProvider(settings)
    youversion = YouVersionClient(settings)
    gloo.ensure_configuration()
    youversion.ensure_configuration()
    if not settings.gemini_api_key:
        raise RuntimeError("Gemini is not configured.")

    store = FirestoreDataStore(args.firebase_project, credentials=active_user_credentials())
    project_id = uuid5(NAMESPACE_URL, f"still:prepared-demo:{CausalAnalysisWorker.pipeline_version}:{args.source_uri}")
    job_id = uuid5(NAMESPACE_URL, f"still:prepared-demo-job:{CausalAnalysisWorker.pipeline_version}:{args.source_uri}")
    project = await store.get_project(project_id)
    if project is None:
        project = Project(
            id=project_id,
            owner_id="prepared-demo-worker",
            title=args.title,
            status=ProjectStatus.SOURCE_PENDING,
            source=SourceRecord(
                kind=SourceKind.YOUTUBE,
                public_url=args.source_uri,
                source_hash=hashlib.sha256(args.source_uri.encode("utf-8")).hexdigest(),
                title=args.title,
                duration_seconds=args.duration,
                prepared_demo=True,
            ),
        )
        await store.put_project(project)
    elif not project.source or project.source.public_url != args.source_uri or project.source.duration_seconds != args.duration:
        raise RuntimeError("The durable prepared-demo project does not match this exact source and duration.")

    echoes = await store.echoes(project_id)
    if project.status != ProjectStatus.READY or not echoes:
        if project.status == ProjectStatus.READY_NO_ECHO:
            print(json.dumps({"status": "READY_NO_ECHO", "published": False, "paid_gloo_candidate_cap": 1}))
            return 3
        job = await store.get_job(job_id) or AnalysisJob(
            id=job_id,
            project_id=project_id,
            owner_id=project.owner_id,
            idempotency_key="prepared-demo-v1",
        )
        job.status = "QUEUED"
        project.current_job_id = job.id
        project.status = ProjectStatus.QUEUED
        project.failure_code = None
        project.failure_message = None
        await store.put_job(job)
        await store.put_project(project)

        policies = load_model_policies(settings)
        router = VideoModelRouter(
            {"gemini": GeminiVideoProvider(settings)},
            ModelUsageBudgetLedger(policies),
            policies,
            settings,
        )
        worker = CausalAnalysisWorker(store=store, router=router, gloo=gloo, youversion=youversion)
        await worker.run(job.id)
        project = await store.get_project(project_id)
        echoes = await store.echoes(project_id)

    windows = await store.windows(project_id)
    candidates = await store.candidates(project_id)
    if not project or project.status != ProjectStatus.READY or not echoes:
        print(json.dumps({
            "status": project.status.value if project else "PROJECT_MISSING",
            "published": False,
            "completed_windows": len(windows),
            "candidate_statuses": sorted({item.status.value for item in candidates}),
            "failure_code": project.failure_code if project else None,
            "paid_gloo_candidate_cap": 1,
        }))
        return 2

    generated_at = datetime.now(UTC).isoformat()
    prepared_payload = {
        "schema_version": 1,
        "judge_label": "Prepared judge demo — real provider output",
        "project": {
            "id": str(project.id),
            "title": project.title,
            "status": project.status.value,
            "source": {
                "kind": "youtube",
                "public_url": project.source.public_url,
                "source_hash": project.source.source_hash,
                "title": project.source.title,
                "duration_seconds": project.source.duration_seconds,
                "prepared_demo": True,
            },
            "progress": {
                "completed_windows": project.progress.completed_windows,
                "total_windows": project.progress.total_windows,
                "stage": project.progress.stage,
            },
        },
        "echoes": [echo_payload(echo) for echo in echoes],
        "provenance": {
            "generated_at": generated_at,
            "source_url": project.source.public_url,
            "source_rights_note": args.rights_note,
            "source_locator_sha256": project.source.source_hash,
            "analysis_windows": len(windows),
            "pipeline": ["Gemini bounded audiovisual analysis", "Gloo Sacred Timing", "YouVersion canonical passage", "Gloo passage verification"],
            "pipeline_version": CausalAnalysisWorker.pipeline_version,
            "prompt_version": CausalAnalysisWorker.prompt_version,
            "models": sorted({item.model_id for item in windows}),
            "gloo_endpoint_mode": settings.gloo_endpoint_mode,
            "echo_ids": [str(echo.id) for echo in echoes],
            "outcome": "ACCEPTED_ECHO",
        },
    }
    document_id = hashlib.sha256(args.code.strip().upper().encode("utf-8")).hexdigest()
    await store.client.collection("prepared_demos").document(document_id).set(prepared_payload)
    print(json.dumps({
        "status": "PUBLISHED_ACCEPTED_ECHO",
        "published": True,
        "project_id": str(project.id),
        "completed_windows": len(windows),
        "echo_count": len(echoes),
        "models": sorted({item.model_id for item in windows}),
        "paid_gloo_candidate_cap": 1,
    }))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Run one exact prepared judge demo with a one-candidate Gloo cap")
    parser.add_argument("--source-uri", required=True)
    parser.add_argument("--title", required=True)
    parser.add_argument("--duration", type=float, required=True)
    parser.add_argument("--code", required=True)
    parser.add_argument("--firebase-project", default="still-scriptures")
    parser.add_argument("--rights-note", required=True)
    args = parser.parse_args()
    return asyncio.run(run(args))


if __name__ == "__main__":
    raise SystemExit(main())
