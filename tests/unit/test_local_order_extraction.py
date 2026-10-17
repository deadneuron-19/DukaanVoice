from __future__ import annotations

from decimal import Decimal

from dukaanvoice.chains.local_order_extraction import LocalOrderExtraction
from dukaanvoice.domain.entities import ProductEntity


def test_local_extraction_matches_catalogue_aliases_and_multiple_quantities() -> None:
    catalogue = [
        ProductEntity(
            product_id="milk",
            canonical_name="Toned Milk",
            brand="Amul",
            category="Milk",
            pack_size=1,
            unit="litre",
            price=Decimal("62"),
            available_stock=10,
            alternative_product_ids=[],
            aliases=["milk", "doodh"],
        ),
        ProductEntity(
            product_id="rice",
            canonical_name="Basmati Rice",
            brand="Shree",
            category="Rice",
            pack_size=5,
            unit="kg",
            price=Decimal("245"),
            available_stock=10,
            alternative_product_ids=[],
            aliases=["rice", "chawal"],
        ),
    ]

    result = LocalOrderExtraction().run(
        "two packets of Amul milk and one kilo rice",
        catalogue,
    )

    assert [item.spoken_product_name for item in result.extracted_items] == [
        "Toned Milk",
        "Basmati Rice",
    ]
    assert [item.spoken_quantity for item in result.extracted_items] == [
        Decimal(2),
        Decimal(1),
    ]
    assert [item.spoken_unit for item in result.extracted_items] == ["pack", "kg"]
    assert result.extracted_items[0].brand_preference == "Amul"


def test_local_extraction_supports_hinglish_numbers_and_unknown_products() -> None:
    catalogue = [
        ProductEntity(
            product_id="sugar",
            canonical_name="Sugar",
            brand="Madhur",
            category="Sugar",
            pack_size=1,
            unit="kg",
            price=Decimal("52"),
            available_stock=10,
            alternative_product_ids=[],
            aliases=["sugar", "cheeni"],
        )
    ]

    result = LocalOrderExtraction().run("do cheeni", catalogue)
    unknown = LocalOrderExtraction().run("two dragon fruit", catalogue)

    assert result.extracted_items[0].spoken_quantity == Decimal(2)
    assert result.extracted_items[0].spoken_product_name == "Sugar"
    assert unknown.extracted_items == []
