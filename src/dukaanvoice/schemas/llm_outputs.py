from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class ExtractedProductRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    spoken_product_name: str = Field(..., min_length=1)
    spoken_quantity: Decimal | None = Field(default=None, gt=0)
    spoken_unit: str | None = None
    brand_preference: str | None = None
    pack_size_preference: str | None = None
    notes: str | None = None
    ambiguity: bool = False


class OrderExtractionResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    original_transcript: str = Field(..., min_length=1)
    language_metadata: dict[str, str] | None = None
    extracted_items: list[ExtractedProductRequest] = Field(default_factory=list)
    clarification_questions: list[str] = Field(default_factory=list)
    extraction_confidence: float | None = Field(default=None, ge=0, le=1)
