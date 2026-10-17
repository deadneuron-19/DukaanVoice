from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, Field, field_validator


class AudioRequest(BaseModel):
    file_name: str = Field(..., min_length=1)
    content_type: str = Field(..., min_length=1)
    data: bytes = Field(...)
    language: str | None = None

    @field_validator("content_type")
    @classmethod
    def validate_content_type(cls, value: str) -> str:
        allowed = {"audio/wav", "audio/mpeg", "audio/mp4", "audio/x-m4a"}
        if value.lower() not in allowed:
            raise ValueError(f"Unsupported audio MIME type: {value}")
        return value


class TranscriptionResult(BaseModel):
    transcript: str = Field(..., min_length=1)
    language: str | None = None
    confidence: float | None = Field(default=None, ge=0, le=1)
    provider: str = "gnani"


class SpeechResult(BaseModel):
    output_path: Path
    content_type: str = "audio/mpeg"
    provider: str = "gnani"
