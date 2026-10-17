from __future__ import annotations

from decimal import Decimal

import pytest

from dukaanvoice.core.exceptions import OrderValidationError
from dukaanvoice.services.pricing_service import PricingService


def test_calculate_line_total_uses_decimal_math():
    service = PricingService()
    total = service.calculate_line_total(Decimal("62.50"), 3)
    assert total == Decimal("187.50")


def test_calculate_total_applies_discount_and_clamps_negative_values():
    service = PricingService()
    total = service.calculate_total([Decimal("120.00"), Decimal("80.00")], Decimal("25.00"))
    assert total == Decimal("175.00")

    assert service.calculate_total([Decimal("10.00")], Decimal("20.00")) == Decimal("0.00")


def test_validate_discount_rejects_invalid_values():
    service = PricingService()
    with pytest.raises(OrderValidationError):
        service.validate_discount(Decimal("-1.00"), Decimal("50.00"))

    with pytest.raises(OrderValidationError):
        service.validate_discount(Decimal("90.00"), Decimal("50.00"))
