from __future__ import annotations

from fastapi.testclient import TestClient


def test_list_products_returns_catalogue_values(api_client: TestClient) -> None:
    response = api_client.get("/products")

    assert response.status_code == 200
    assert response.json() == [
        {
            "product_id": "milk-toned-1l",
            "canonical_name": "Toned Milk",
            "brand": "Amul",
            "category": "Milk",
            "pack_size": 1,
            "unit": "litre",
            "price": "62.00",
            "available_stock": 9,
            "alternative_product_ids": ["milk", "doodh"],
            "is_active": True,
        }
    ]


def test_get_product_returns_404_for_unknown_id(api_client: TestClient) -> None:
    response = api_client.get("/products/missing-product")

    assert response.status_code == 404
    assert response.json()["detail"] == "Product not found."
