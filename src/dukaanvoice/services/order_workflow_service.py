from __future__ import annotations

import logging
import threading
from decimal import Decimal
from uuid import uuid4

from dukaanvoice.chains.local_order_extraction import LocalOrderExtraction
from dukaanvoice.chains.order_extraction import OrderExtractionChain
from dukaanvoice.chains.local_order_extraction import LocalOrderExtraction
from dukaanvoice.core.config import settings
from dukaanvoice.core.exceptions import (
    InventoryError,
    OrderValidationError,
    ProductNotFoundError,
    RepositoryError,
)
from dukaanvoice.domain.entities import ProductEntity
from dukaanvoice.repositories.json_order_repository import JSONOrderRepository
from dukaanvoice.repositories.json_product_repository import JSONProductRepository
from dukaanvoice.repositories.json_session_repository import JSONSessionRepository
from dukaanvoice.schemas.llm_outputs import ExtractedProductRequest, OrderExtractionResult
from dukaanvoice.schemas.order import OrderItem, OrderSchema
from dukaanvoice.services.inventory_service import InventoryService
from dukaanvoice.services.order_service import OrderService
from dukaanvoice.services.pricing_service import PricingService
from dukaanvoice.services.product_matching import ProductMatcher

logger = logging.getLogger(__name__)


class OrderWorkflowService:
    """Coordinates text extraction, deterministic catalogue resolution, and order state."""

    def __init__(
        self,
        products: JSONProductRepository,
        orders: JSONOrderRepository,
        sessions: JSONSessionRepository,
        *,
        extraction_chain: OrderExtractionChain | None = None,
        matcher: ProductMatcher | None = None,
        pricing: PricingService | None = None,
        inventory: InventoryService | None = None,
    ) -> None:
        self.products = products
        self.orders = orders
        self.sessions = sessions
        self._use_local_extraction = extraction_chain is None and settings.llm_provider.strip().lower() == "mock"
        self.extraction_chain = extraction_chain or OrderExtractionChain()
        self.local_extraction = LocalOrderExtraction()
        self.matcher = matcher or ProductMatcher()
        self.pricing = pricing or PricingService()
        self.inventory = inventory or InventoryService()
        self.order_service = OrderService()
        self._lock = threading.RLock()

    def start_text_order(
        self,
        session_id: str,
        transcript: str,
        *,
        idempotency_key: str,
        language: str | None = None,
    ) -> dict:
        with self._lock:
            existing = self._find_by_idempotency_key(idempotency_key)
            if existing:
                if existing["session_id"] != session_id:
                    raise OrderValidationError("Idempotency key was already used for another session.")
                return {"status": existing["status"], "transcript": transcript, "order": existing}

            catalogue = self.products.list_products()
            extraction = self._extract_order(transcript, catalogue)
            if not extraction.extracted_items:
                return {
                    "status": "needs_clarification",
                    "transcript": transcript,
                    "clarification_question": "I couldn't identify any products. What would you like to order?",
                }

            context = {
                "idempotency_key": idempotency_key,
                "transcript": transcript,
                "language": language,
                "requests": [item.model_dump(mode="json") for item in extraction.extracted_items],
                "resolved": [],
                "next_index": 0,
            }
            self.sessions.save_session(
                session_id,
                {
                    "session_id": session_id,
                    "current_state": "VALIDATING",
                    "draft_order_id": None,
                    "pending_clarification": None,
                    "conversation_history": [],
                    "workflow_context": context,
                },
            )
            return self._resolve_remaining(session_id, context, transcript)

    def clarify(
        self,
        session_id: str,
        *,
        selected_product_id: str | None = None,
        quantity: int | None = None,
        clarification_text: str | None = None,
    ) -> dict:
        with self._lock:
            session = self.sessions.get_session(session_id)
            if session is None or not isinstance(session.get("workflow_context"), dict):
                raise ProductNotFoundError("No pending order clarification exists for this session.")

            context = session["workflow_context"]
            index = context.get("next_index")
            requests = context.get("requests", [])
            if not isinstance(index, int) or index >= len(requests):
                raise OrderValidationError("This session has no pending product to clarify.")

            if clarification_text:
                extraction = self._extract_order(clarification_text, self.products.list_products())
                if len(extraction.extracted_items) != 1:
                    raise OrderValidationError(
                        "Please clarify one product at a time, or choose one of the listed catalogue options."
                    )
                requests[index] = extraction.extracted_items[0].model_dump(mode="json")
                context["transcript"] = f"{context['transcript']} {clarification_text}".strip()
            elif selected_product_id:
                product = self.products.get_by_id(selected_product_id)
                if product is None:
                    raise ProductNotFoundError("Selected product is not in the active catalogue.")
                extracted = ExtractedProductRequest.model_validate(requests[index])
                allowed_candidates = self._candidate_products(extracted, self.products.list_products())
                if product.product_id not in {candidate.product_id for candidate in allowed_candidates}:
                    raise ProductNotFoundError("Selected product does not match the requested brand or pack size.")
                picked = product
                requested_quantity = quantity if quantity is not None else self._quantity_in_packs(extracted, picked)
                if requested_quantity is None:
                    raise OrderValidationError("Please provide a whole-number quantity of catalogue packs.")
                self.inventory.validate_stock(picked.available_stock, requested_quantity)
                context["resolved"].append(self._make_item(picked, requested_quantity).model_dump(mode="json"))
                context["next_index"] = index + 1
            else:
                raise OrderValidationError("Choose a listed product or provide one short clarification.")

            session["workflow_context"] = context
            self.sessions.save_session(session_id, session)
            return self._resolve_remaining(session_id, context, context["transcript"])

    def confirm(self, order_id: str, idempotency_key: str) -> dict:
        with self._lock:
            stored = self.orders.get_by_id(order_id)
            if stored is None:
                raise ProductNotFoundError("Order not found.")
            order = OrderSchema.model_validate(stored)
            if order.status == "confirmed":
                return order.model_dump(mode="json")
            if order.status != "awaiting_confirmation":
                raise OrderValidationError("Only orders awaiting confirmation can be confirmed.")

            current_products = self.products.list_products()
            product_by_id = {product.product_id: product for product in current_products}
            quantities: dict[str, int] = {}
            previous_stock: dict[str, int] = {}
            next_stock: dict[str, int] = {}
            for item in order.items:
                product = product_by_id.get(item.product_id)
                if product is None:
                    raise ProductNotFoundError(f"Product {item.product_id} is no longer available.")
                if product.price != item.unit_price:
                    raise OrderValidationError(
                        f"Price changed for {product.canonical_name}; please review the updated order."
                    )
                quantities[item.product_id] = quantities.get(item.product_id, 0) + item.quantity
                previous_stock[item.product_id] = product.available_stock
            for product_id, quantity in quantities.items():
                self.inventory.validate_stock(previous_stock[product_id], quantity)
                next_stock[product_id] = previous_stock[product_id] - quantity

            confirmed = order.model_copy(deep=True)
            confirmed.status = "confirmed"
            confirmed.confirmed_at = self.order_service.confirm_order(confirmed).confirmed_at
            confirmed.updated_at = confirmed.confirmed_at
            confirmed.confirmation_idempotency_key = idempotency_key

            self.products.update_stock(next_stock)
            try:
                self.orders.save(confirmed.model_dump(mode="json"))
            except Exception as exc:
                try:
                    self.products.update_stock(previous_stock)
                except Exception as rollback_error:
                    logger.exception("Inventory rollback failed after order persistence failure.")
                    raise RepositoryError(
                        "Order persistence failed and inventory rollback also failed; inspect persisted data."
                    ) from rollback_error
                raise exc

            session = self.sessions.get_session(order.session_id)
            if session is not None:
                session["current_state"] = "CONFIRMED"
                session["draft_order_id"] = order_id
                session["pending_clarification"] = None
                self.sessions.save_session(order.session_id, session)
            return confirmed.model_dump(mode="json")

    def cancel(self, order_id: str) -> dict:
        with self._lock:
            stored = self.orders.get_by_id(order_id)
            if stored is None:
                raise ProductNotFoundError("Order not found.")
            order = OrderSchema.model_validate(stored)
            if order.status == "confirmed":
                raise OrderValidationError("Confirmed orders cannot be cancelled through this MVP endpoint.")
            if order.status == "cancelled":
                return order.model_dump(mode="json")
            cancelled = self.order_service.cancel_order(order)
            self.orders.save(cancelled.model_dump(mode="json"))
            session = self.sessions.get_session(order.session_id)
            if session is not None:
                session["current_state"] = "CANCELLED"
                session["pending_clarification"] = None
                session["workflow_context"] = None
                self.sessions.save_session(order.session_id, session)
            return cancelled.model_dump(mode="json")

    def change_quantity(self, order_id: str, product_id: str, quantity: int) -> dict:
        with self._lock:
            stored = self.orders.get_by_id(order_id)
            if stored is None:
                raise ProductNotFoundError("Order not found.")
            order = OrderSchema.model_validate(stored)
            self._ensure_editable(order)
            product = self.products.get_by_id(product_id)
            if product is None:
                raise ProductNotFoundError("Product is not in the active catalogue.")
            self.inventory.validate_stock(product.available_stock, quantity)
            matching = next((item for item in order.items if item.product_id == product_id), None)
            if matching is None:
                raise ProductNotFoundError("Product is not present in the order.")
            if product.price != matching.unit_price:
                raise OrderValidationError("Product price changed; start a new order to review current pricing.")
            updated = self.order_service.update_item_quantity(order, product_id, quantity)
            self.orders.save(updated.model_dump(mode="json"))
            return updated.model_dump(mode="json")

    def remove_item(self, order_id: str, product_id: str) -> dict:
        with self._lock:
            stored = self.orders.get_by_id(order_id)
            if stored is None:
                raise ProductNotFoundError("Order not found.")
            order = OrderSchema.model_validate(stored)
            self._ensure_editable(order)
            if not any(item.product_id == product_id for item in order.items):
                raise ProductNotFoundError("Product is not present in the order.")
            updated = self.order_service.remove_item(order, product_id)
            if not updated.items:
                updated.status = "cancelled"
            self.orders.save(updated.model_dump(mode="json"))
            return updated.model_dump(mode="json")

    def _resolve_remaining(self, session_id: str, context: dict, transcript: str) -> dict:
        catalogue = self.products.list_products()
        requests = context["requests"]
        while context["next_index"] < len(requests):
            index = context["next_index"]
            extracted = ExtractedProductRequest.model_validate(requests[index])
            candidates = self._candidate_products(extracted, catalogue)
            product = candidates[0] if len(candidates) == 1 else None
            if product is None:
                question = self._clarification_question(extracted, candidates)
                self._save_pending(session_id, context, question)
                return {
                    "status": "needs_clarification",
                    "transcript": transcript,
                    "clarification_question": question,
                    "candidates": [self._candidate_dict(item) for item in candidates],
                }

            quantity = self._quantity_in_packs(extracted, product)
            if quantity is None:
                question = (
                    f"What quantity of {product.canonical_name} ({product.pack_size} {product.unit} per pack) "
                    "would you like?"
                )
                self._save_pending(session_id, context, question)
                return {
                    "status": "needs_clarification",
                    "transcript": transcript,
                    "clarification_question": question,
                    "candidates": [self._candidate_dict(product)],
                }
            try:
                self.inventory.validate_stock(product.available_stock, quantity)
            except InventoryError:
                question = (
                    f"We have {product.available_stock} pack(s) of {product.canonical_name}. "
                    "Would you like to change the quantity?"
                )
                self._save_pending(session_id, context, question)
                return {
                    "status": "needs_clarification",
                    "transcript": transcript,
                    "clarification_question": question,
                    "candidates": [self._candidate_dict(product)],
                    "error": "requested quantity exceeds current stock",
                }
            context["resolved"].append(self._make_item(product, quantity).model_dump(mode="json"))
            context["next_index"] = index + 1

        items = [OrderItem.model_validate(item) for item in context["resolved"]]
        if not items:
            raise OrderValidationError("An order needs at least one item.")
        order = OrderSchema(
            order_id=f"ORD-{uuid4().hex}",
            session_id=session_id,
            items=items,
            subtotal=self.pricing.calculate_total([item.line_total for item in items]),
            total=self.pricing.calculate_total([item.line_total for item in items]),
            status="awaiting_confirmation",
            idempotency_key=context["idempotency_key"],
        )
        self.orders.save(order.model_dump(mode="json"))
        self.sessions.save_session(
            session_id,
            {
                "session_id": session_id,
                "current_state": "AWAITING_CONFIRMATION",
                "draft_order_id": order.order_id,
                "pending_clarification": None,
                "conversation_history": [],
                "workflow_context": None,
            },
        )
        return {"status": order.status, "transcript": transcript, "order": order.model_dump(mode="json")}

    def _save_pending(self, session_id: str, context: dict, question: str) -> None:
        self.sessions.save_session(
            session_id,
            {
                "session_id": session_id,
                "current_state": "NEEDS_CLARIFICATION",
                "draft_order_id": None,
                "pending_clarification": question,
                "conversation_history": [],
                "workflow_context": context,
            },
        )

    def _find_by_idempotency_key(self, idempotency_key: str) -> dict | None:
        return next(
            (order for order in self.orders.list_orders() if order.get("idempotency_key") == idempotency_key),
            None,
        )

    def _extract_order(
        self,
        transcript: str,
        catalogue: list[ProductEntity],
    ) -> OrderExtractionResult:
        if self._use_local_extraction:
            return self.local_extraction.run(transcript, catalogue)
        return self.extraction_chain.run(transcript, self._catalogue_context(catalogue))

    @staticmethod
    def _catalogue_context(products: list[ProductEntity]) -> str:
        return "\n".join(
            f"{item.canonical_name} | brand={item.brand} | pack={item.pack_size} {item.unit}"
            for item in products
            if item.is_active
        )

    @staticmethod
    def _matching_query(item: ExtractedProductRequest) -> str:
        return " ".join(
            value
            for value in (
                item.spoken_product_name,
                item.brand_preference,
                item.pack_size_preference,
            )
            if value
        )

    @staticmethod
    def _match_preferences(
        request: ExtractedProductRequest,
        products: list[ProductEntity],
    ) -> ProductEntity | None:
        filtered = products
        if request.brand_preference:
            filtered = [
                product for product in filtered
                if request.brand_preference.casefold() in product.brand.casefold()
            ]
        if request.pack_size_preference:
            preference = (
                request.pack_size_preference.casefold().replace(" ", "")
                .replace("litre", "l")
                .replace("liter", "l")
            )
            filtered = [
                product for product in filtered
                if preference in f"{product.pack_size}{product.unit}".casefold().replace(" ", "")
                .replace("litre", "l").replace("liter", "l")
            ]
        return filtered[0] if len(filtered) == 1 else None

    def _candidate_products(
        self,
        request: ExtractedProductRequest,
        catalogue: list[ProductEntity],
    ) -> list[ProductEntity]:
        candidates = self.matcher.candidates(request.spoken_product_name, catalogue)
        filtered = [
            product for product in candidates
            if self._match_preferences(request, [product]) is not None
        ]
        return filtered[:5]

    def _clarification_question(
        self,
        request: ExtractedProductRequest,
        candidates: list[ProductEntity],
    ) -> str:
        if candidates:
            options = ", ".join(
                f"{product.brand} {product.canonical_name} {product.pack_size}{product.unit}"
                for product in candidates
            )
            return f"Which {request.spoken_product_name} did you mean: {options}?"
        return f"I couldn't match {request.spoken_product_name} to the catalogue. What product did you mean?"

    @staticmethod
    def _quantity_in_packs(request: ExtractedProductRequest, product: ProductEntity) -> int | None:
        quantity = request.spoken_quantity
        if quantity is None:
            return None
        unit = (request.spoken_unit or "").strip().casefold()
        if not unit or unit in {"pack", "packs", "packet", "packets", "pcs", "piece", "pieces"}:
            if quantity != quantity.to_integral_value():
                return None
            return int(quantity)

        normalized_unit = unit.rstrip("s")
        product_unit = product.unit.casefold().rstrip("s")
        conversions: dict[tuple[str, str], Decimal] = {
            ("kg", "g"): Decimal("1000"),
            ("g", "kg"): Decimal("0.001"),
            ("litre", "ml"): Decimal("1000"),
            ("ml", "litre"): Decimal("0.001"),
            ("l", "ml"): Decimal("1000"),
            ("ml", "l"): Decimal("0.001"),
        }
        requested_amount = quantity
        if normalized_unit != product_unit:
            factor = conversions.get((normalized_unit, product_unit))
            if factor is None:
                return None
            requested_amount *= factor
        pack_count = requested_amount / Decimal(product.pack_size)
        if pack_count <= 0 or pack_count != pack_count.to_integral_value():
            return None
        return int(pack_count)

    def _make_item(self, product: ProductEntity, quantity: int) -> OrderItem:
        return OrderItem(
            product_id=product.product_id,
            quantity=quantity,
            unit_price=product.price,
            line_total=self.pricing.calculate_line_total(product.price, quantity),
        )

    @staticmethod
    def _candidate_dict(product: ProductEntity) -> dict:
        return {
            "product_id": product.product_id,
            "name": product.canonical_name,
            "brand": product.brand,
            "pack_size": product.pack_size,
            "unit": product.unit,
            "price": product.price,
            "available_stock": product.available_stock,
        }

    @staticmethod
    def _ensure_editable(order: OrderSchema) -> None:
        if order.status != "awaiting_confirmation":
            raise OrderValidationError("Only an order awaiting confirmation can be edited.")
