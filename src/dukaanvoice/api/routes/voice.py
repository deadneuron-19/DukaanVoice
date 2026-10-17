from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

router = APIRouter(prefix="/voice", tags=["voice"])


@router.post("/transcribe", status_code=status.HTTP_501_NOT_IMPLEMENTED)
def transcribe_voice() -> None:
    """The real Gnani transport is blocked pending its verified API contract."""
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail=(
            "Voice transcription is not available until the official Gnani Prisma API "
            "request and authentication contract is verified."
        ),
    )


@router.post("/synthesize", status_code=status.HTTP_501_NOT_IMPLEMENTED)
def synthesize_voice() -> None:
    """Do not return mock audio as if it were real speech inference."""
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail=(
            "Speech synthesis is not available until the official Gnani Timbre API "
            "request and authentication contract is verified."
        ),
    )
