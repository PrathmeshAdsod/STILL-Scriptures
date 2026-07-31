from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import quote

import httpx

from ..config import Settings
from .base import FailureClass, ProviderFailure


@dataclass(frozen=True)
class CanonicalPassage:
    reference: str
    passage_id: str
    bible_id: int
    bible_version: str
    text: str
    copyright_attribution: str


class YouVersionClient:
    """Canonical Scripture client based on the documented YouVersion v1 passages API."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    @property
    def status(self) -> str:
        return self.settings.integration_status(bool(self.settings.yvp_app_key)).value

    def ensure_configuration(self) -> None:
        if not self.settings.yvp_app_key:
            raise ProviderFailure(FailureClass.CONFIGURATION, "YouVersion App Key is missing.")
        if not self.settings.yvp_allowed_bible_ids:
            raise ProviderFailure(FailureClass.CONFIGURATION, "YVP_ALLOWED_BIBLE_IDS must contain an app-licensed Bible ID before production analysis can start.")

    async def retrieve_passage(self, *, passage_id: str, bible_id: int) -> CanonicalPassage:
        self.ensure_configuration()
        if bible_id not in self.settings.yvp_allowed_bible_ids:
            raise ProviderFailure(FailureClass.CONFIGURATION, "The requested Bible ID is not in YVP_ALLOWED_BIBLE_IDS for this licensed application.")
        passage_url = f"{self.settings.yvp_base_url.rstrip('/')}/v1/bibles/{bible_id}/passages/{quote(passage_id, safe='.')}"
        bible_url = f"{self.settings.yvp_base_url.rstrip('/')}/v1/bibles/{bible_id}"
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                passage_response, bible_response = await __import__("asyncio").gather(
                    client.get(passage_url, headers={"X-YVP-App-Key": self.settings.yvp_app_key}, params={"format": "text", "include_headings": "false", "include_notes": "false"}),
                    client.get(bible_url, headers={"X-YVP-App-Key": self.settings.yvp_app_key}),
                )
            self._raise_for_status(passage_response, "passage lookup")
            self._raise_for_status(bible_response, "Bible metadata lookup")
            passage = passage_response.json()
            bible = bible_response.json()
            text = passage.get("content")
            copyright = bible.get("copyright")
            bible_version = bible.get("localized_abbreviation") or bible.get("abbreviation") or bible.get("localized_title") or bible.get("title")
            if not text or not copyright or not bible_version:
                raise ProviderFailure(FailureClass.INVALID_RESPONSE, "YouVersion response lacked canonical content, Bible version, or copyright attribution.")
            return CanonicalPassage(
                reference=str(passage.get("reference", "")),
                passage_id=str(passage.get("id", passage_id)),
                bible_id=bible_id,
                bible_version=str(bible_version),
                text=str(text),
                copyright_attribution=str(copyright),
            )
        except httpx.TimeoutException as error:
            raise ProviderFailure(FailureClass.RETRYABLE_TEMPORARY, "YouVersion timed out.") from error

    @staticmethod
    def _raise_for_status(response: httpx.Response, operation: str) -> None:
        if response.status_code == 429:
            raise ProviderFailure(FailureClass.RETRYABLE_RATE_LIMIT, f"YouVersion rate-limited the {operation}.")
        if response.status_code >= 500:
            raise ProviderFailure(FailureClass.RETRYABLE_TEMPORARY, f"YouVersion is temporarily unavailable during {operation}.")
        if response.status_code >= 400:
            raise ProviderFailure(FailureClass.PERMANENT, f"YouVersion {operation} failed: {response.status_code}.")
