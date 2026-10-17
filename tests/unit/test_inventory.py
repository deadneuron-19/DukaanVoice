from __future__ import annotations

import pytest

from dukaanvoice.core.exceptions import InventoryError
from dukaanvoice.services.inventory_service import InventoryService


def test_reserve_stock_reduces_inventory() -> None:
    service = InventoryService()
    remaining = service.reserve_stock(12, 4)
    assert remaining == 8


def test_validate_stock_rejects_invalid_requests() -> None:
    service = InventoryService()
    with pytest.raises(InventoryError):
        service.validate_stock(5, 6)

    with pytest.raises(InventoryError):
        service.validate_stock(5, -1)


def test_release_stock_increases_inventory() -> None:
    service = InventoryService()
    assert service.release_stock(7, 3) == 10
