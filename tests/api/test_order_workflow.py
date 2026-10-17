from __future__ import annotations

from decimal import Decimal
from fastapi.testclient import TestClient

from dukaanvoice.domain.entities import ProductEntity
from dukaanvoice.main import create_app


def test_text_order_requires_confirmation_and_uses_catalogue_price(api_client: TestClient) -> None:
    response = api_client.post(
        "/orders/text",
        headers={"Idempotency-Key": "order-create-001"},
        json={
            "session_id": "session-new-1",
            "transcript": "two milk packs",
            "language": "en",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "awaiting_confirmation"
    assert payload["order"]["items"][0]["unit_price"] == "62.00"
    assert payload["order"]["total"] == "124.00"
    assert payload["order"]["status"] == "awaiting_confirmation"


def test_default_mock_configuration_creates_catalogue_matched_order(api_client: TestClient) -> None:
    source_app = api_client.app
    app = create_app(
        product_repository=source_app.state.product_repository,
        order_repository=source_app.state.order_repository,
        session_repository=source_app.state.session_repository,
    )

    with TestClient(app) as client:
        response = client.post(
            "/orders/text",
            headers={"Idempotency-Key": "local-extraction-001"},
            json={
                "session_id": "session-local-extraction",
                "transcript": "two packets of milk",
            },
        )
        unknown_response = client.post(
            "/orders/text",
            headers={"Idempotency-Key": "local-extraction-002"},
            json={
                "session_id": "session-local-unknown",
                "transcript": "two dragon fruit",
            },
        )

    assert response.status_code == 200
    assert response.json()["status"] == "awaiting_confirmation"
    assert response.json()["order"]["items"][0]["product_id"] == "milk-toned-1l"
    assert response.json()["order"]["items"][0]["quantity"] == 2
    assert unknown_response.status_code == 200
    assert unknown_response.json()["status"] == "needs_clarification"


def test_ambiguous_or_missing_quantity_requests_clarification(api_client: TestClient) -> None:
    response = api_client.post(
        "/orders/text",
        headers={"Idempotency-Key": "order-create-002"},
        json={"session_id": "session-new-2", "transcript": "milk"},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "needs_clarification"
    assert response.json()["clarification_question"]
    assert response.json()["order"] is None


def test_confirm_decrements_inventory_once_and_is_idempotent(api_client: TestClient) -> None:
    created = api_client.post(
        "/orders/text",
        headers={"Idempotency-Key": "order-create-003"},
        json={"session_id": "session-new-3", "transcript": "two milk"},
    ).json()
    order_id = created["order"]["order_id"]

    first = api_client.post(
        f"/orders/{order_id}/confirm",
        headers={"Idempotency-Key": "confirm-key-0001"},
    )
    second = api_client.post(
        f"/orders/{order_id}/confirm",
        headers={"Idempotency-Key": "confirm-key-0001"},
    )

    assert first.status_code == 200
    assert first.json()["status"] == "confirmed"
    assert second.status_code == 200
    assert api_client.get("/products/milk-toned-1l").json()["available_stock"] == 7


def test_stock_is_checked_again_during_confirmation(api_client: TestClient) -> None:
    created = api_client.post(
        "/orders/text",
        headers={"Idempotency-Key": "order-create-004"},
        json={"session_id": "session-new-4", "transcript": "two milk"},
    ).json()
    order_id = created["order"]["order_id"]
    api_client.app.state.product_repository.update_stock({"milk-toned-1l": 1})

    response = api_client.post(
        f"/orders/{order_id}/confirm",
        headers={"Idempotency-Key": "confirm-key-0002"},
    )

    assert response.status_code == 409
    assert api_client.get("/products/milk-toned-1l").json()["available_stock"] == 1


def test_draft_order_can_be_corrected_and_cancelled(api_client: TestClient) -> None:
    created = api_client.post(
        "/orders/text",
        headers={"Idempotency-Key": "order-create-005"},
        json={"session_id": "session-new-5", "transcript": "two milk"},
    ).json()
    order_id = created["order"]["order_id"]

    corrected = api_client.patch(
        f"/orders/{order_id}/items/milk-toned-1l",
        json={"quantity": 1},
    )
    cancelled = api_client.post(f"/orders/{order_id}/cancel")

    assert corrected.status_code == 200
    assert corrected.json()["total"] == "62.00"
    assert cancelled.status_code == 200
    assert cancelled.json()["status"] == "cancelled"
    assert api_client.get("/products/milk-toned-1l").json()["available_stock"] == 9


def test_clarification_selects_product_and_continues_order(api_client: TestClient) -> None:
    created = api_client.post(
        "/orders/text",
        headers={"Idempotency-Key": "order-create-006"},
        json={"session_id": "session-new-6", "transcript": "milk"},
    ).json()
    assert created["status"] == "needs_clarification"

    clarified = api_client.post(
        "/orders/clarify",
        json={
            "session_id": "session-new-6",
            "selected_product_id": "milk-toned-1l",
            "quantity": 2,
        },
    )

    assert clarified.status_code == 200
    assert clarified.json()["status"] == "awaiting_confirmation"
    assert clarified.json()["order"]["total"] == "124.00"


def test_clarification_cannot_select_unrelated_catalogue_product(api_client: TestClient) -> None:
    api_client.app.state.product_repository.upsert(
        ProductEntity(
            product_id="sugar-1kg",
            canonical_name="Sugar",
            brand="Madhur",
            category="Sugar",
            pack_size=1,
            unit="kg",
            price=Decimal("52.00"),
            available_stock=20,
            alternative_product_ids=["cheeni"],
            is_active=True,
        )
    )
    api_client.post(
        "/orders/text",
        headers={"Idempotency-Key": "order-create-007"},
        json={"session_id": "session-new-7", "transcript": "milk"},
    )

    response = api_client.post(
        "/orders/clarify",
        json={
            "session_id": "session-new-7",
            "selected_product_id": "sugar-1kg",
            "quantity": 1,
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Selected product does not match the requested brand or pack size."


def test_retried_text_request_returns_same_order(api_client: TestClient) -> None:
    request_data = {"session_id": "session-new-8", "transcript": "two milk"}
    headers = {"Idempotency-Key": "order-create-008"}

    first = api_client.post("/orders/text", headers=headers, json=request_data)
    retry = api_client.post("/orders/text", headers=headers, json=request_data)

    assert first.status_code == retry.status_code == 200
    assert first.json()["order"]["order_id"] == retry.json()["order"]["order_id"]
    assert len([item for item in api_client.get("/orders").json() if item["idempotency_key"] == headers["Idempotency-Key"]]) == 1


def test_confirmation_rejects_price_change_without_stock_mutation(api_client: TestClient) -> None:
    created = api_client.post(
        "/orders/text",
        headers={"Idempotency-Key": "order-create-009"},
        json={"session_id": "session-new-9", "transcript": "two milk"},
    ).json()
    order_id = created["order"]["order_id"]
    product = api_client.app.state.product_repository.get_by_id("milk-toned-1l")
    product.price = Decimal("65.00")
    api_client.app.state.product_repository.upsert(product)

    response = api_client.post(
        f"/orders/{order_id}/confirm",
        headers={"Idempotency-Key": "confirm-key-0003"},
    )

    assert response.status_code == 409
    assert "Price changed" in response.json()["detail"]
    assert api_client.get("/products/milk-toned-1l").json()["available_stock"] == 9
