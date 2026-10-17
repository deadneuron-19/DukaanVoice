from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from dukaanvoice.domain.entities import ProductEntity
from dukaanvoice.schemas.llm_outputs import ExtractedProductRequest, OrderExtractionResult
from dukaanvoice.main import create_app
from dukaanvoice.repositories.json_order_repository import JSONOrderRepository
from dukaanvoice.repositories.json_product_repository import JSONProductRepository
from dukaanvoice.repositories.json_session_repository import JSONSessionRepository
from dukaanvoice.services.order_workflow_service import OrderWorkflowService


class FixedExtractionChain:
    def run(self, transcript: str, catalog_context: str | None = None) -> OrderExtractionResult:
        if "two" in transcript.casefold():
            item_name, quantity = "milk", 2
        else:
            item_name, quantity = "milk", None
        return OrderExtractionResult(
            original_transcript=transcript,
            extracted_items=[
                ExtractedProductRequest(
                    spoken_product_name=item_name,
                    spoken_quantity=quantity,
                )
            ],
        )


@pytest.fixture
def api_client(tmp_path: Path) -> TestClient:
    products = JSONProductRepository(tmp_path / "products.json")
    products.upsert(
        ProductEntity(
            product_id="milk-toned-1l",
            canonical_name="Toned Milk",
            brand="Amul",
            category="Milk",
            pack_size=1,
            unit="litre",
            price=Decimal("62.00"),
            available_stock=9,
            alternative_product_ids=["milk", "doodh"],
            is_active=True,
        )
    )
    orders_path = tmp_path / "orders.json"
    orders_path.write_text(
        json.dumps(
            [
                {
                    "order_id": "ORD-API-1",
                    "session_id": "session-api-1",
                    "items": [
                        {
                            "product_id": "milk-toned-1l",
                            "quantity": 2,
                            "unit_price": "62.00",
                            "line_total": "124.00",
                        }
                    ],
                    "subtotal": "124.00",
                    "discount": "0.00",
                    "total": "124.00",
                    "status": "draft",
                }
            ]
        ),
        encoding="utf-8",
    )
    sessions = JSONSessionRepository(tmp_path / "sessions.json")
    sessions.save_session(
        "session-api-1",
        {
            "session_id": "session-api-1",
            "current_state": "AWAITING_CONFIRMATION",
            "draft_order_id": "ORD-API-1",
            "conversation_history": [],
            "pending_clarification": None,
        },
    )
    orders = JSONOrderRepository(orders_path)
    workflow = OrderWorkflowService(
        products,
        orders,
        sessions,
        extraction_chain=FixedExtractionChain(),
    )
    return TestClient(
        create_app(
            product_repository=products,
            order_repository=orders,
            session_repository=sessions,
            order_workflow_service=workflow,
        )
    )
