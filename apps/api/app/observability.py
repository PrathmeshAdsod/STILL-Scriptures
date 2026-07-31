from __future__ import annotations

import json
import logging
from typing import Any


logger = logging.getLogger("still")


def log_event(event: str, **fields: Any) -> None:
    """Structured logs intentionally exclude secret values and raw media/transcripts."""
    safe_fields = {key: value for key, value in fields.items() if key not in {"authorization", "token", "secret", "raw_media", "raw_transcript"}}
    logger.info(json.dumps({"event": event, **safe_fields}, default=str))
