from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from dukaanvoice.core.exceptions import OrderValidationError
from dukaanvoice.schemas.order import OrderItem, OrderSchema


class OrderService:
    """Creates, validates, confirms, updates, and cancels draft orders."""

    def __init__(self) -> None:
        self._idempotency_keys: dict[str, OrderSchema] = {}

    def create_order(
        self,
        session_id: str,
        items: list[OrderItem],
        *,
        idempotency_key: str | None = None,
    ) -> OrderSchema:
        if not items:
            raise OrderValidationError("Order must contain at least one item.")

        if idempotency_key and idempotency_key in self._idempotency_keys:
            return self._idempotency_keys[idempotency_key]

        subtotal = sum((item.line_total for item in items), Decimal("0"))
        now = datetime.now(UTC)
        order = OrderSchema(
            order_id=f"ORD-{session_id[:6]}-{abs(hash(now)) % 100000}",
            session_id=session_id,
            items=items,
            subtotal=subtotal,
            total=subtotal,
            status="draft",
            created_at=now,
            updated_at=now,
            idempotency_key=idempotency_key,
        )

        if idempotency_key:
            self._idempotency_keys[idempotency_key] = order
        return order

    def confirm_order(self, order: OrderSchema, *, idempotency_key: str | None = None) -> OrderSchema:
        if order.status == "confirmed":
            return order
        if not order.items:
            raise OrderValidationError("Cannot confirm an empty order.")

        if idempotency_key and idempotency_key in self._idempotency_keys:
            existing = self._idempotency_keys[idempotency_key]
            if existing.status == "confirmed":
                return existing

        order.status = "confirmed"
        order.confirmed_at = datetime.now(UTC)
        order.updated_at = datetime.now(UTC)
        if idempotency_key:
            self._idempotency_keys[idempotency_key] = order
        return order

    def update_item_quantity(self, order: OrderSchema, product_id: str, quantity: int) -> OrderSchema:
        for item in order.items:
            if item.product_id == product_id:
                if quantity <= 0:
                    return self.remove_item(order, product_id)
                item.quantity = quantity
                item.line_total = item.unit_price * Decimal(quantity)
                order.updated_at = datetime.now(UTC)
                order.subtotal = sum((entry.line_total for entry in order.items), Decimal("0"))
                order.total = order.subtotal - order.discount
                return order
        raise OrderValidationError(f"Product {product_id} is not present in the order.")

    def remove_item(self, order: OrderSchema, product_id: str) -> OrderSchema:
        order.items = [item for item in order.items if item.product_id != product_id]
        if not order.items:
            order.status = "draft"
        order.updated_at = datetime.now(UTC)
        order.subtotal = sum((item.line_total for item in order.items), Decimal("0"))
        order.total = order.subtotal - order.discount
        return order

    def cancel_order(self, order: OrderSchema) -> OrderSchema:
        order.status = "cancelled"
        order.updated_at = datetime.now(UTC)
        return order
