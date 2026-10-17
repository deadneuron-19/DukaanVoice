from __future__ import annotations

from decimal import Decimal

import pytest

from dukaanvoice.core.exceptions import AmbiguousProductError
from dukaanvoice.domain.entities import ProductEntity
from dukaanvoice.services.product_matching import ProductMatcher


@pytest.fixture
def catalogue() -> list[ProductEntity]:
    return [
        ProductEntity(
            product_id="rice-basmati-5kg",
            canonical_name="Basmati Rice",
            brand="Shree",
            category="Rice",
            pack_size=5,
            unit="kg",
            price=Decimal("245.00"),
            available_stock=10,
            alternative_product_ids=["basmati chawal", "rice"],
            is_active=True,
        ),
        ProductEntity(
            product_id="milk-toned-1l",
            canonical_name="Toned Milk",
            brand="Amul",
            category="Milk",
            pack_size=1,
            unit="litre",
            price=Decimal("62.00"),
            available_stock=20,
            alternative_product_ids=["milk"],
            is_active=True,
        ),
        ProductEntity(
            product_id="rice-brown-5kg",
            canonical_name="Brown Rice",
            brand="Organic",
            category="Rice",
            pack_size=5,
            unit="kg",
            price=Decimal("260.00"),
            available_stock=6,
            alternative_product_ids=["brown chawal", "rice"],
            is_active=True,
        ),
    ]


def test_product_match_returns_best_product(catalogue):
    matcher = ProductMatcher()
    result = matcher.match("basmati rice", catalogue)
    assert result.product_id == "rice-basmati-5kg"


def test_product_match_raises_on_ambiguous_candidates(catalogue):
    matcher = ProductMatcher()
    with pytest.raises(AmbiguousProductError):
        matcher.match("rice", [catalogue[0], catalogue[2]])


def test_product_match_raises_on_missing_catalogue_item(catalogue):
    matcher = ProductMatcher()
    with pytest.raises(AmbiguousProductError):
        matcher.match("coffee beans", catalogue)
