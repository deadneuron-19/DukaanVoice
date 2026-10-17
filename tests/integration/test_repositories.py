from __future__ import annotations

from decimal import Decimal

from dukaanvoice.domain.entities import ProductEntity
from dukaanvoice.repositories.json_order_repository import JSONOrderRepository
from dukaanvoice.repositories.json_product_repository import JSONProductRepository
from dukaanvoice.repositories.json_session_repository import JSONSessionRepository


def test_product_repository_round_trips_product_records(tmp_path) -> None:
    repo = JSONProductRepository(tmp_path / "products.json")
    product = ProductEntity(
        product_id="milk-toned-1l",
        canonical_name="Toned Milk",
        brand="Amul",
        category="Milk",
        pack_size=1,
        unit="litre",
        price=Decimal("62.00"),
        available_stock=9,
        alternative_product_ids=["milk"],
        is_active=True,
    )

    repo.upsert(product)
    assert repo.get_by_id("milk-toned-1l").canonical_name == "Toned Milk"
    assert len(repo.list_products()) == 1


def test_json_order_and_session_repositories_persist_data(tmp_path) -> None:
    order_repo = JSONOrderRepository(tmp_path / "orders.json")
    session_repo = JSONSessionRepository(tmp_path / "sessions.json")

    order = {"order_id": "ORD-1", "session_id": "session-1", "items": [], "subtotal": "0.00", "total": "0.00", "status": "draft"}
    order_repo.save(order)
    session = {"session_id": "session-1", "current_state": "RECEIVED"}
    session_repo.save_session("session-1", session)

    assert order_repo.get_by_id("ORD-1")["status"] == "draft"
    assert session_repo.get_session("session-1")["current_state"] == "RECEIVED"
