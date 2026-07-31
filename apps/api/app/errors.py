from __future__ import annotations

from enum import StrEnum

from fastapi import HTTPException, status


class ErrorCode(StrEnum):
    AUTH_REQUIRED = "AUTH_REQUIRED"
    FORBIDDEN = "FORBIDDEN"
    NOT_FOUND = "NOT_FOUND"
    INVALID_SOURCE = "INVALID_SOURCE"
    INVALID_STATE = "INVALID_STATE"
    ANALYSIS_UNAVAILABLE = "ANALYSIS_UNAVAILABLE"
    PROVIDER_TEMPORARILY_UNAVAILABLE = "PROVIDER_TEMPORARILY_UNAVAILABLE"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    IDEMPOTENCY_CONFLICT = "IDEMPOTENCY_CONFLICT"


def api_error(code: ErrorCode, message: str, http_status: int) -> HTTPException:
    return HTTPException(status_code=http_status, detail={"code": code, "message": message})


def not_found(message: str = "The requested project does not exist.") -> HTTPException:
    return api_error(ErrorCode.NOT_FOUND, message, status.HTTP_404_NOT_FOUND)
