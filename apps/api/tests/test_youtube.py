import httpx
import pytest
from fastapi import HTTPException

from app.config import Settings
from app.youtube import YoutubeMetadataClient, iso_duration_seconds, youtube_video_id


def test_youtube_id_and_iso_duration_are_strict() -> None:
    assert youtube_video_id("https://youtu.be/3ZR3unZ3FW0") == "3ZR3unZ3FW0"
    assert youtube_video_id("https://www.youtube.com/watch?v=3ZR3unZ3FW0") == "3ZR3unZ3FW0"
    assert iso_duration_seconds("PT5M58S") == 358
    with pytest.raises(HTTPException):
        youtube_video_id("https://www.youtube.com/watch?v=too-short")


@pytest.mark.asyncio
async def test_development_fallback_still_enforces_duration_limit() -> None:
    client = YoutubeMetadataClient(Settings(max_video_duration_seconds=360))
    with pytest.raises(HTTPException) as error:
        await client.inspect("https://youtu.be/3ZR3unZ3FW0", 361)
    assert error.value.status_code == 422


@pytest.mark.asyncio
async def test_authoritative_metadata_replaces_browser_duration(monkeypatch) -> None:
    class FakeClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *_args):
            return None

        async def get(self, *_args, **_kwargs):
            return httpx.Response(
                200,
                request=httpx.Request("GET", "https://www.googleapis.com/youtube/v3/videos"),
                json={
                    "items": [{
                        "snippet": {"title": "Verified title"},
                        "contentDetails": {"duration": "PT5M58S"},
                        "status": {"privacyStatus": "public", "embeddable": True},
                    }]
                },
            )

    monkeypatch.setattr(httpx, "AsyncClient", lambda **_kwargs: FakeClient())
    client = YoutubeMetadataClient(Settings(youtube_api_key="restricted-test-key"))
    metadata = await client.inspect("https://youtu.be/3ZR3unZ3FW0", 1)
    assert metadata.duration_seconds == 358
    assert metadata.title == "Verified title"
