#!/usr/bin/env python3
"""Milestone 1 preflight; it never calls mocks or fabricates capability proof."""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apps" / "api"))

from app.config import Settings  # noqa: E402


REQUIRED_ENVIRONMENT = (
    "GEMINI_API_KEY",
    "GLOO_CLIENT_ID",
    "GLOO_CLIENT_SECRET",
    "YVP_APP_KEY",
)


def main() -> int:
    settings = Settings()
    video_path = Path(sys.argv[1]).expanduser() if len(sys.argv) == 2 else None
    credentials = {
        "GEMINI_API_KEY": settings.gemini_api_key,
        "GLOO_CLIENT_ID": settings.gloo_client_id,
        "GLOO_CLIENT_SECRET": settings.gloo_client_secret,
        "YVP_APP_KEY": settings.yvp_app_key,
    }
    report = {
        "credentials_present": {
            name: bool(credentials[name]) for name in REQUIRED_ENVIRONMENT
        },
        "optional_nvidia_enabled": settings.enable_nvidia_provider,
        "optional_nvidia_key_present": bool(settings.nvidia_api_key),
        "tooling_present": {
            tool: shutil.which(tool) is not None
            for tool in ("ffmpeg", "docker", "gcloud", "firebase")
        },
        "rights_cleared_test_video": bool(video_path and video_path.is_file()),
        "capability_proof": "NOT_RUN",
        "reason": (
            "This preflight reports readiness only. A capability proof requires "
            "real provider calls and must be recorded in the capability matrix."
        ),
    }
    print(json.dumps(report, indent=2, sort_keys=True))

    missing = [name for name, present in report["credentials_present"].items() if not present]
    if missing or not report["rights_cleared_test_video"]:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
