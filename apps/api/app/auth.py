from __future__ import annotations

from fastapi import Header, Request

from .config import Settings
from .errors import ErrorCode, api_error


async def current_user(request: Request, authorization: str | None = Header(default=None)) -> str:
    settings: Settings = request.app.state.settings
    if settings.app_mode in {"development", "test"}:
        return request.headers.get("X-Development-User", settings.development_user_id)
    if not authorization or not authorization.startswith("Bearer "):
        raise api_error(ErrorCode.AUTH_REQUIRED, "A Firebase bearer token is required.", 401)
    try:
        import firebase_admin.auth

        token = firebase_admin.auth.verify_id_token(authorization.removeprefix("Bearer "))
        return str(token["uid"])
    except Exception as error:
        raise api_error(ErrorCode.AUTH_REQUIRED, "The Firebase token could not be verified.", 401) from error
