from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


@dataclass(slots=True)
class ProductEntity:
    product_id: str
    canonical_name: str
    brand: str
    category: str
    pack_size: int
    unit: str
    price: Decimal
    available_stock: int
    alternative_product_ids: list[str]
    is_active: bool = True
    aliases: list[str] | None = None


@dataclass(slots=True)
class OrderLine:
    product_id: str
    quantity: int
    unit_price: Decimal
    line_total: Decimal
