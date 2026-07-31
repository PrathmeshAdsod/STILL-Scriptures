from __future__ import annotations

import asyncio

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
        import firebase_admin
        import firebase_admin.auth

        try:
            firebase_admin.get_app()
        except ValueError:
            firebase_admin.initialize_app(options={"projectId": settings.firebase_project_id})
        token = await asyncio.to_thread(firebase_admin.auth.verify_id_token, authorization.removeprefix("Bearer "), check_revoked=True)
        provider = (token.get("firebase") or {}).get("sign_in_provider")
        if provider == "anonymous" or not token.get("email"):
            raise api_error(ErrorCode.AUTH_REQUIRED, "Sign in with an email account to continue.", 401)
        if token.get("email_verified") is not True:
            raise api_error(ErrorCode.FORBIDDEN, "Verify your email address before analyzing a video.", 403)
        return str(token["uid"])
    except Exception as error:
        if hasattr(error, "status_code"):
            raise
        raise api_error(ErrorCode.AUTH_REQUIRED, "The Firebase token could not be verified.", 401) from error


async def require_cloud_task(request: Request, authorization: str | None, task_name: str | None) -> None:
    settings: Settings = request.app.state.settings
    if settings.app_mode != "production":
        return
    if not task_name or not authorization or not authorization.startswith("Bearer "):
        raise api_error(ErrorCode.FORBIDDEN, "This endpoint only accepts authenticated Cloud Tasks requests.", 403)
    if not settings.worker_base_url or not settings.worker_invoker_service_account:
        raise api_error(ErrorCode.FORBIDDEN, "The Cloud Tasks identity is not configured.", 403)

    def verify() -> dict:
        from google.auth.transport.requests import Request as GoogleAuthRequest
        from google.oauth2 import id_token

        return id_token.verify_oauth2_token(
            authorization.removeprefix("Bearer "),
            GoogleAuthRequest(),
            audience=settings.worker_base_url.rstrip("/"),
        )

    try:
        claims = await asyncio.to_thread(verify)
    except Exception as error:
        raise api_error(ErrorCode.FORBIDDEN, "The Cloud Tasks identity could not be verified.", 403) from error
    if claims.get("email") != settings.worker_invoker_service_account or claims.get("email_verified") is not True:
        raise api_error(ErrorCode.FORBIDDEN, "The Cloud Tasks identity is not authorized.", 403)
