from __future__ import annotations

from fastapi.testclient import TestClient


def test_orders_are_read_from_injected_repository(api_client: TestClient) -> None:
    response = api_client.get("/orders")

    assert response.status_code == 200
    assert response.json()[0]["order_id"] == "ORD-API-1"
    assert response.json()[0]["items"][0]["line_total"] == "124.00"


def test_get_order_returns_404_for_unknown_id(api_client: TestClient) -> None:
    response = api_client.get("/orders/missing-order")

    assert response.status_code == 404
    assert response.json()["detail"] == "Order not found."


def test_corrupt_json_is_reported_as_safe_server_error(api_client: TestClient) -> None:
    api_client.app.state.order_repository.path.write_text("{invalid", encoding="utf-8")

    response = api_client.get("/orders")

    assert response.status_code == 500
    assert response.json()["detail"] == "A storage operation failed."
