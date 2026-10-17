from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel, Field, field_validator


class ProductSchema(BaseModel):
    product_id: str = Field(..., min_length=3)
    canonical_name: str = Field(..., min_length=2)
    brand: str = Field(..., min_length=1)
    category: str = Field(..., min_length=1)
    pack_size: int = Field(..., gt=0)
    unit: str = Field(..., min_length=1)
    price: Decimal = Field(..., gt=0)
    available_stock: int = Field(..., ge=0)
    alternative_product_ids: list[str] = Field(default_factory=list)
    is_active: bool = True

    @field_validator("product_id")
    @classmethod
    def validate_product_id(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Product ID is required.")
        return value.strip()
