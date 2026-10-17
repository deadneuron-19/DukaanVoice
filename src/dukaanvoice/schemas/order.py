from __future__ import annotations

from decimal import Decimal
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class OrderItem(BaseModel):
    product_id: str = Field(..., min_length=3)
    quantity: int = Field(..., gt=0)
    unit_price: Decimal = Field(..., gt=0)
    line_total: Decimal = Field(..., gt=0)

    @field_validator("product_id")
    @classmethod
    def validate_product_id(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Product ID must not be blank.")
        return value.strip()


class OrderSchema(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    order_id: str = Field(..., min_length=3)
    session_id: str = Field(..., min_length=3)
    items: list[OrderItem] = Field(default_factory=list)
    subtotal: Decimal = Field(..., ge=0)
    discount: Decimal = Field(default=Decimal("0"), ge=0)
    total: Decimal = Field(..., ge=0)
    status: str = Field(default="draft")
    created_at: datetime | None = None
    updated_at: datetime | None = None
    confirmed_at: datetime | None = None
    idempotency_key: str | None = None
    confirmation_idempotency_key: str | None = None


class TextOrderRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    session_id: str = Field(..., min_length=3, max_length=128)
    transcript: str = Field(..., min_length=1, max_length=5000)
    language: str | None = Field(default=None, max_length=32)

    @field_validator("session_id", "transcript")
    @classmethod
    def strip_required_text(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Value cannot be blank.")
        return normalized


class ClarificationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    session_id: str = Field(..., min_length=3, max_length=128)
    selected_product_id: str | None = Field(default=None, min_length=3, max_length=128)
    quantity: int | None = Field(default=None, gt=0)
    clarification_text: str | None = Field(default=None, min_length=1, max_length=1000)

    @field_validator("clarification_text")
    @classmethod
    def strip_clarification_text(cls, value: str | None) -> str | None:
        return value.strip() if value else value

    @field_validator("selected_product_id")
    @classmethod
    def strip_product_id(cls, value: str | None) -> str | None:
        return value.strip() if value else value


class QuantityCorrectionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    quantity: int = Field(..., gt=0)


class OrderWorkflowResponse(BaseModel):
    status: str
    transcript: str | None = None
    order: OrderSchema | None = None
    clarification_question: str | None = None
    candidates: list[ProductRequestOption] = Field(default_factory=list)
    error: str | None = None


class ProductRequestOption(BaseModel):
    product_id: str
    name: str
    brand: str
    pack_size: int
    unit: str
    price: Decimal
    available_stock: int
