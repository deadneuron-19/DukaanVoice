from __future__ import annotations

import json
import os
from pathlib import Path
from uuid import uuid4

from dukaanvoice.core.config import settings
from dukaanvoice.core.exceptions import RepositoryError
from dukaanvoice.repositories.interfaces import OrderRepository


class JSONOrderRepository(OrderRepository):
    """JSON-backed order repository for prototype persistence."""

    def __init__(self, path: str | Path | None = None) -> None:
        base_path = Path(path) if path is not None else settings.data_dir / "orders.json"
        self.path = Path(base_path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def get_by_id(self, order_id: str) -> dict | None:
        return next((record for record in self.list_orders() if record.get("order_id") == order_id), None)

    def list_orders(self) -> list[dict]:
        return self._load_source()

    def save(self, order: dict) -> None:
        records = self._load_source()
        existing_index = next((index for index, item in enumerate(records) if item.get("order_id") == order.get("order_id")), None)
        if existing_index is None:
            records.append(order)
        else:
            records[existing_index] = order
        temporary_path = self.path.with_name(f".{self.path.name}.{uuid4().hex}.tmp")
        try:
            temporary_path.write_text(json.dumps(records, indent=2), encoding="utf-8")
            os.replace(temporary_path, self.path)
        except OSError as exc:
            temporary_path.unlink(missing_ok=True)
            raise RepositoryError(f"Could not persist order storage file: {self.path}") from exc

    def _load_source(self) -> list[dict]:
        if not self.path.exists():
            return []
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise RepositoryError(f"Order storage file is invalid JSON: {self.path}") from exc
        if not isinstance(data, list):
            raise RepositoryError(f"Order storage file must contain a list of order records: {self.path}")
        return data
