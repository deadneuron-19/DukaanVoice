from __future__ import annotations

from decimal import Decimal

from dukaanvoice.core.exceptions import OrderValidationError
from dukaanvoice.schemas.order import OrderItem
from dukaanvoice.services.order_service import OrderService


def test_create_order_and_confirm() -> None:
    service = OrderService()
    items = [
        OrderItem(product_id="milk-toned-1l", quantity=2, unit_price=Decimal("62.00"), line_total=Decimal("124.00")),
        OrderItem(product_id="sugar-1kg", quantity=1, unit_price=Decimal("52.00"), line_total=Decimal("52.00")),
    ]

    order = service.create_order("session-123", items, idempotency_key="dup-1")
    assert order.status == "draft"
    assert order.subtotal == Decimal("176.00")

    confirmed = service.confirm_order(order, idempotency_key="dup-1")
    assert confirmed.status == "confirmed"


def test_updating_and_cancelling_order() -> None:
    service = OrderService()
    item = OrderItem(product_id="tea-250g", quantity=1, unit_price=Decimal("120.00"), line_total=Decimal("120.00"))
    order = service.create_order("session-456", [item])

    updated = service.update_item_quantity(order, "tea-250g", 2)
    assert updated.items[0].quantity == 2
    assert updated.subtotal == Decimal("240.00")

    removed = service.remove_item(updated, "tea-250g")
    assert removed.items == []

    cancelled = service.cancel_order(removed)
    assert cancelled.status == "cancelled"


def test_idempotent_order_creation_prevents_duplicates() -> None:
    service = OrderService()
    item = OrderItem(product_id="rice-basmati-5kg", quantity=1, unit_price=Decimal("245.00"), line_total=Decimal("245.00"))

    first = service.create_order("session-789", [item], idempotency_key="same")
    second = service.create_order("session-789", [item], idempotency_key="same")
    assert first.order_id == second.order_id


def test_order_validation_rejects_empty_orders() -> None:
    service = OrderService()
    try:
        service.create_order("session-000", [])
        assert False, "Expected a validation error for empty order"
    except OrderValidationError:
        pass
