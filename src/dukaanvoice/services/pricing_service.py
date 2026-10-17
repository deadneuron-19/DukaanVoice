from __future__ import annotations

from decimal import Decimal

from dukaanvoice.core.exceptions import OrderValidationError


class PricingService:
    """Deterministic pricing and total calculation service."""

    def calculate_line_total(self, unit_price: Decimal, quantity: int) -> Decimal:
        if unit_price < 0:
            raise OrderValidationError("Unit price cannot be negative.")
        if quantity <= 0:
            raise OrderValidationError("Quantity must be a positive integer.")
        return (unit_price * Decimal(quantity)).quantize(Decimal("0.01"))

    def calculate_total(self, line_totals: list[Decimal], discount: Decimal = Decimal("0")) -> Decimal:
        subtotal = sum(line_totals, Decimal("0")).quantize(Decimal("0.01"))
        if discount < 0:
            raise OrderValidationError("Discount cannot be negative.")
        total = (subtotal - discount).quantize(Decimal("0.01"))
        return total if total >= 0 else Decimal("0.00")

    def validate_discount(self, discount: Decimal, subtotal: Decimal) -> Decimal:
        if discount < 0:
            raise OrderValidationError("Discount cannot be negative.")
        if discount > subtotal:
            raise OrderValidationError("Discount cannot exceed subtotal.")
        return discount.quantize(Decimal("0.01"))
