from __future__ import annotations

from dukaanvoice.core.exceptions import InventoryError


class InventoryService:
    """Inventory validation and stock tracking for the MVP."""

    def validate_stock(self, available_stock: int, requested_quantity: int) -> None:
        if available_stock < 0:
            raise InventoryError("Available stock cannot be negative.")
        if requested_quantity < 0:
            raise InventoryError("Requested quantity cannot be negative.")
        if requested_quantity > available_stock:
            raise InventoryError("Insufficient stock for requested quantity.")

    def reserve_stock(self, available_stock: int, requested_quantity: int) -> int:
        self.validate_stock(available_stock, requested_quantity)
        return available_stock - requested_quantity

    def release_stock(self, available_stock: int, released_quantity: int) -> int:
        if released_quantity < 0:
            raise InventoryError("Released quantity cannot be negative.")
        return available_stock + released_quantity
