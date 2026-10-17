from __future__ import annotations

from fastapi import APIRouter

from dukaanvoice.core.config import settings

router = APIRouter(prefix="/health", tags=["health"])


@router.get("")
def health() -> dict[str, str]:
    return {"status": "ok", "app": settings.app_name, "environment": settings.app_env}
