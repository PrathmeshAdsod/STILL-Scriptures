from __future__ import annotations

import asyncio
from dataclasses import dataclass
import json
import os
import subprocess
import tempfile
from uuid import UUID

from .providers.base import FailureClass, ProviderFailure
from .schemas import SourceKind, SourceRecord


SUPPORTED_UPLOAD_MIME_TYPES = {
    "video/mp4",
    "video/mpeg",
    "video/quicktime",
    "video/avi",
    "video/x-flv",
    "video/mpg",
    "video/webm",
    "video/wmv",
    "video/3gpp",
}


@dataclass(frozen=True)
class SemanticWindow:
    index: int
    start_seconds: float
    end_seconds: float


def validate_source(source: SourceRecord) -> None:
    if source.kind == SourceKind.UPLOAD:
        if source.content_type not in SUPPORTED_UPLOAD_MIME_TYPES:
            raise ValueError("This video format is not supported for analysis.")
        if source.has_audio is False or source.has_video is False:
            raise ValueError("STILL requires a source with both audio and visual tracks.")
        if not source.duration_seconds:
            raise ValueError("Source duration is required before causal analysis can begin.")
    if source.kind == SourceKind.YOUTUBE and not source.public_url:
        raise ValueError("A public YouTube URL is required.")


def validate_upload_storage_path(*, storage_path: str, project_id: UUID, expected_bucket: str | None) -> None:
    """Keep the API from attaching an arbitrary GCS object to an owned project."""
    if expected_bucket:
        is_owned_path = storage_path.startswith(f"gs://{expected_bucket}/projects/{project_id}/sources/")
    else:
        bucket_name, separator, object_path = storage_path.removeprefix("gs://").partition("/")
        is_owned_path = bool(bucket_name and separator and object_path.startswith(f"projects/{project_id}/sources/"))
    if not is_owned_path:
        raise ProviderFailure(
            FailureClass.INPUT_INCOMPATIBLE,
            "The upload must be stored under this project's owned Firebase Storage path.",
        )


async def inspect_uploaded_media(source: SourceRecord) -> SourceRecord:
    """FFprobe only media structure. It creates no narrative conclusion and never reads semantic content."""
    if source.kind != SourceKind.UPLOAD or not source.storage_path:
        return source
    if not source.storage_path.startswith("gs://"):
        raise ProviderFailure(FailureClass.INPUT_INCOMPATIBLE, "Uploaded source must be in Cloud Storage before structural validation.")
    bucket_name, _, object_name = source.storage_path.removeprefix("gs://").partition("/")
    if not bucket_name or not object_name:
        raise ProviderFailure(FailureClass.INPUT_INCOMPATIBLE, "Uploaded source Storage URI is incomplete.")
    suffix = os.path.splitext(source.original_filename or "source.mp4")[1] or ".mp4"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as temporary:
        temporary_name = temporary.name
    try:
        def download_and_probe() -> dict:
            from google.cloud import storage
            storage.Client().bucket(bucket_name).blob(object_name).download_to_filename(temporary_name)
            probe = subprocess.run(
                ["ffprobe", "-v", "error", "-show_entries", "format=duration:stream=codec_type", "-of", "json", temporary_name],
                check=True,
                capture_output=True,
                text=True,
            )
            return json.loads(probe.stdout)
        details = await asyncio.to_thread(download_and_probe)
    except FileNotFoundError as error:
        raise ProviderFailure(FailureClass.CONFIGURATION, "FFprobe is unavailable. The worker image must include FFmpeg.") from error
    except subprocess.CalledProcessError as error:
        raise ProviderFailure(FailureClass.INPUT_INCOMPATIBLE, "FFprobe could not validate the uploaded media structure.") from error
    finally:
        if os.path.exists(temporary_name):
            os.remove(temporary_name)
    streams = details.get("streams", [])
    has_audio = any(item.get("codec_type") == "audio" for item in streams)
    has_video = any(item.get("codec_type") == "video" for item in streams)
    duration = float(details.get("format", {}).get("duration", 0) or 0)
    return source.model_copy(update={"duration_seconds": duration, "has_audio": has_audio, "has_video": has_video})


def plan_semantic_windows(duration_seconds: float, *, base_seconds: float = 40, max_seconds: float = 60) -> list[SemanticWindow]:
    """Deterministic segmentation sees duration only, never semantic future content."""
    if duration_seconds <= 0:
        raise ProviderFailure(FailureClass.INPUT_INCOMPATIBLE, "A positive source duration is required to create bounded causal windows.")
    window_size = min(max_seconds, max(20, base_seconds))
    windows: list[SemanticWindow] = []
    cursor = 0.0
    index = 0
    while cursor < duration_seconds:
        end = min(duration_seconds, cursor + window_size)
        windows.append(SemanticWindow(index=index, start_seconds=round(cursor, 3), end_seconds=round(end, 3)))
        cursor = end
        index += 1
    return windows


async def delete_uploaded_source(source: SourceRecord) -> None:
    """Delete the owned Storage object before deleting its project records."""
    if source.kind != SourceKind.UPLOAD or not source.storage_path:
        return
    if not source.storage_path.startswith("gs://"):
        raise ValueError("The upload cannot be safely deleted because its Storage URI is invalid.")
    without_scheme = source.storage_path.removeprefix("gs://")
    bucket_name, _, object_name = without_scheme.partition("/")
    if not bucket_name or not object_name:
        raise ValueError("The upload cannot be safely deleted because its Storage URI is incomplete.")
    def delete() -> None:
        from google.cloud import storage
        storage.Client().bucket(bucket_name).blob(object_name).delete()
    await asyncio.to_thread(delete)
