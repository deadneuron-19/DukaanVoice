from __future__ import annotations

from abc import ABC, abstractmethod

from dukaanvoice.domain.entities import ProductEntity


class ProductRepository(ABC):
    @abstractmethod
    def list_products(self) -> list[ProductEntity]:
        """Return all active products from the catalogue."""

    @abstractmethod
    def get_by_id(self, product_id: str) -> ProductEntity | None:
        """Fetch a product by canonical ID."""

    @abstractmethod
    def upsert(self, product: ProductEntity) -> None:
        """Insert or replace a product entry."""


class OrderRepository(ABC):
    @abstractmethod
    def list_orders(self) -> list[dict]:
        """Return all persisted order records."""

    @abstractmethod
    def get_by_id(self, order_id: str) -> dict | None:
        """Return a stored order record."""

    @abstractmethod
    def save(self, order: dict) -> None:
        """Persist a new or updated order."""


class SessionRepository(ABC):
    @abstractmethod
    def get_session(self, session_id: str) -> dict | None:
        """Return a session state by ID."""

    @abstractmethod
    def save_session(self, session_id: str, state: dict) -> None:
        """Write the current session state."""
