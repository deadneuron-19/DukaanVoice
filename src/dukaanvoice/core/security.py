from __future__ import annotations

from fastapi import HTTPException, Request


async def get_correlation_id(request: Request) -> str:
    """Return a request-specific correlation identifier when present."""
    return request.headers.get("x-correlation-id", "unknown")


def safe_message(exc: Exception) -> str:
    """Return a sanitized message for public-facing error responses."""
    return exc.__class__.__name__


def ensure_safe_request_size(size_bytes: int, maximum_bytes: int) -> None:
    if size_bytes > maximum_bytes:
        raise HTTPException(status_code=413, detail="Request exceeds supported size limit.")
