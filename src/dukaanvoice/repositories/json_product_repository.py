from __future__ import annotations

import json
import os
from decimal import Decimal
from pathlib import Path
from uuid import uuid4

from dukaanvoice.core.config import settings
from dukaanvoice.core.exceptions import RepositoryError
from dukaanvoice.domain.entities import ProductEntity
from dukaanvoice.repositories.interfaces import ProductRepository


class JSONProductRepository(ProductRepository):
    """JSON-backed product catalogue repository for the MVP."""

    def __init__(self, path: str | Path | None = None) -> None:
        base_path = Path(path) if path is not None else settings.data_dir / "products.json"
        self.path = Path(base_path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def list_products(self) -> list[ProductEntity]:
        products = self._load_source()
        return [self._from_dict(item) for item in products if item.get("status") != "inactive"]

    def get_by_id(self, product_id: str) -> ProductEntity | None:
        for product in self.list_products():
            if product.product_id == product_id:
                return product
        return None

    def upsert(self, product: ProductEntity) -> None:
        records = self._load_source()
        updated = False
        for index, item in enumerate(records):
            if item.get("id") == product.product_id:
                records[index] = self._to_dict(product)
                updated = True
                break
        if not updated:
            records.append(self._to_dict(product))
        self._write_atomically(records)

    def update_stock(self, stock_by_product_id: dict[str, int]) -> None:
        records = self._load_source()
        found: set[str] = set()
        for item in records:
            product_id = item.get("id")
            if product_id in stock_by_product_id:
                stock = stock_by_product_id[product_id]
                if stock < 0:
                    raise ValueError("Product stock cannot be negative.")
                item["stock"] = stock
                found.add(product_id)
        missing = set(stock_by_product_id) - found
        if missing:
            raise RepositoryError(f"Cannot update stock for missing product IDs: {sorted(missing)}")
        self._write_atomically(records)

    def _write_atomically(self, records: list[dict]) -> None:
        temporary_path = self.path.with_name(f".{self.path.name}.{uuid4().hex}.tmp")
        try:
            temporary_path.write_text(json.dumps(records, indent=2), encoding="utf-8")
            os.replace(temporary_path, self.path)
        except OSError as exc:
            temporary_path.unlink(missing_ok=True)
            raise RepositoryError(f"Could not persist catalogue file: {self.path}") from exc

    def _load_source(self) -> list[dict]:
        if not self.path.exists():
            return []
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:  # pragma: no cover - rescue path
            raise RepositoryError(f"Catalogue file is invalid JSON: {self.path}") from exc
        if not isinstance(data, list):
            raise RepositoryError(f"Catalogue file must contain a list of products: {self.path}")
        return data

    @staticmethod
    def _from_dict(item: dict) -> ProductEntity:
        return ProductEntity(
            product_id=item["id"],
            canonical_name=item["name"],
            brand=item["brand"],
            category=item["category"],
            pack_size=int(item["pack_size"]),
            unit=str(item["unit"]),
            price=Decimal(str(item["price"])),
            available_stock=int(item["stock"]),
            alternative_product_ids=list(item.get("alternatives", [])),
            is_active=item.get("status", "active") != "inactive",
            aliases=list(item.get("aliases", [])),
        )

    @staticmethod
    def _to_dict(product: ProductEntity) -> dict:
        return {
            "id": product.product_id,
            "name": product.canonical_name,
            "brand": product.brand,
            "category": product.category,
            "pack_size": product.pack_size,
            "unit": product.unit,
            "price": str(product.price),
            "stock": product.available_stock,
            "status": "active" if product.is_active else "inactive",
            "aliases": product.aliases or [],
            "alternatives": product.alternative_product_ids,
        }
