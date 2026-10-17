from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class BaseSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Money(BaseSchema):
    value: Decimal = Field(..., description="Monetary amount stored as Decimal.")

    @field_validator("value")
    @classmethod
    def non_negative_money(cls, value: Decimal) -> Decimal:
        if value < 0:
            raise ValueError("Money cannot be negative.")
        return value
