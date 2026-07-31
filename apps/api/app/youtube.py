from __future__ import annotations

import re
from dataclasses import dataclass
from urllib.parse import parse_qs, urlparse

import httpx

from .config import Settings
from .errors import ErrorCode, api_error


_DURATION = re.compile(
    r"^P(?:(?P<days>\d+)D)?(?:T(?:(?P<hours>\d+)H)?(?:(?P<minutes>\d+)M)?(?:(?P<seconds>\d+)S)?)?$"
)
_VIDEO_ID = re.compile(r"^[A-Za-z0-9_-]{11}$")


@dataclass(frozen=True)
class YoutubeMetadata:
    video_id: str
    title: str
    duration_seconds: int


def youtube_video_id(value: str) -> str:
    parsed = urlparse(value)
    host = (parsed.hostname or "").lower()
    if host == "youtu.be":
        candidate = parsed.path.strip("/").split("/", 1)[0]
    elif host in {"youtube.com", "www.youtube.com", "m.youtube.com"}:
        candidate = parse_qs(parsed.query).get("v", [""])[0]
    else:
        candidate = ""
    if not _VIDEO_ID.fullmatch(candidate):
        raise api_error(ErrorCode.INVALID_SOURCE, "Enter a public YouTube watch link with a valid video ID.", 422)
    return candidate


def iso_duration_seconds(value: str) -> int:
    match = _DURATION.fullmatch(value)
    if not match:
        raise ValueError("YouTube returned an unsupported duration.")
    parts = {key: int(number or 0) for key, number in match.groupdict().items()}
    return parts["days"] * 86_400 + parts["hours"] * 3_600 + parts["minutes"] * 60 + parts["seconds"]


class YoutubeMetadataClient:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    async def inspect(self, url: str, browser_duration: float | None = None) -> YoutubeMetadata:
        video_id = youtube_video_id(url)
        if not self.settings.youtube_api_key:
            if self.settings.app_mode == "production":
                raise api_error(ErrorCode.ANALYSIS_UNAVAILABLE, "Authoritative YouTube validation is not configured.", 503)
            if not browser_duration:
                raise api_error(ErrorCode.INVALID_SOURCE, "STILL must verify the public video's duration before analysis.", 422)
            if browser_duration > self.settings.max_video_duration_seconds:
                raise api_error(
                    ErrorCode.INVALID_SOURCE,
                    f"This competition demo accepts public YouTube videos up to {self.settings.max_video_duration_seconds // 60} minutes.",
                    422,
                )
            return YoutubeMetadata(video_id=video_id, title="Public YouTube story", duration_seconds=round(browser_duration))
        try:
            async with httpx.AsyncClient(timeout=12) as client:
                response = await client.get(
                    "https://www.googleapis.com/youtube/v3/videos",
                    params={
                        "part": "contentDetails,snippet,status",
                        "id": video_id,
                        "key": self.settings.youtube_api_key,
                        "fields": "items(id,snippet/title,contentDetails/duration,status/privacyStatus,status/embeddable)",
                    },
                )
            response.raise_for_status()
            items = response.json().get("items", [])
        except (httpx.HTTPError, TypeError, ValueError) as error:
            raise api_error(ErrorCode.ANALYSIS_UNAVAILABLE, "YouTube validation is temporarily unavailable. No analysis was started.", 503) from error
        if not items:
            raise api_error(ErrorCode.INVALID_SOURCE, "This YouTube video is unavailable or not public.", 422)
        item = items[0]
        status = item.get("status", {})
        if status.get("privacyStatus") == "private" or status.get("embeddable") is not True:
            raise api_error(ErrorCode.INVALID_SOURCE, "Choose a public or unlisted YouTube video that permits embedding.", 422)
        try:
            duration = iso_duration_seconds(item["contentDetails"]["duration"])
        except (KeyError, TypeError, ValueError) as error:
            raise api_error(ErrorCode.INVALID_SOURCE, "YouTube did not return a usable fixed video duration.", 422) from error
        if duration <= 0:
            raise api_error(ErrorCode.INVALID_SOURCE, "Live or durationless YouTube sources are not supported.", 422)
        if duration > self.settings.max_video_duration_seconds:
            raise api_error(
                ErrorCode.INVALID_SOURCE,
                f"This competition demo accepts public YouTube videos up to {self.settings.max_video_duration_seconds // 60} minutes.",
                422,
            )
        return YoutubeMetadata(
            video_id=video_id,
            title=str(item.get("snippet", {}).get("title") or "Public YouTube story")[:180],
            duration_seconds=duration,
        )
