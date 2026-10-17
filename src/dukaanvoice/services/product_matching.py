from __future__ import annotations

import re
from typing import Iterable

from dukaanvoice.core.exceptions import AmbiguousProductError
from dukaanvoice.domain.entities import ProductEntity


class ProductMatcher:
    """Deterministic match engine for catalogue lookup."""

    def __init__(self, threshold: float = 0.7, fuzzy_enabled: bool = False) -> None:
        self.threshold = threshold
        self.fuzzy_enabled = fuzzy_enabled

    def match(self, raw_name: str, catalogue: Iterable[ProductEntity]) -> ProductEntity:
        if not raw_name or not raw_name.strip():
            raise AmbiguousProductError("Product name cannot be blank.")

        normalized = self._normalize(raw_name)
        matches: list[tuple[ProductEntity, float]] = []
        for product in catalogue:
            score = self._score(normalized, product)
            if score > 0:
                matches.append((product, score))

        if not matches:
            raise AmbiguousProductError(f"No product matched '{raw_name}'.")

        sorted_matches = sorted(matches, key=lambda item: item[1], reverse=True)
        top_product, top_score = sorted_matches[0]
        second_score = sorted_matches[1][1] if len(sorted_matches) > 1 else 0.0

        if top_score < self.threshold:
            raise AmbiguousProductError(f"Product '{raw_name}' is too weakly matched to the catalogue.")
        if len(sorted_matches) > 1 and second_score >= top_score * 0.98:
            raise AmbiguousProductError(f"Multiple plausible matches for '{raw_name}'.")
        return top_product

    def candidates(
        self,
        raw_name: str,
        catalogue: Iterable[ProductEntity],
    ) -> list[ProductEntity]:
        normalized = self._normalize(raw_name)
        scored = [
            (product, self._score(normalized, product))
            for product in catalogue
            if product.is_active
        ]
        qualified = [(product, score) for product, score in scored if score >= self.threshold]
        qualified.sort(key=lambda pair: pair[1], reverse=True)
        return [product for product, _ in qualified]

    @staticmethod
    def _normalize(value: str) -> str:
        value = value.lower().strip()
        value = re.sub(r"[^a-z0-9]+", " ", value)
        return " ".join(value.split())

    def _score(self, raw_name: str, product: ProductEntity) -> float:
        product_tokens = set(self._normalize(product.canonical_name).split())
        alias_tokens = {
            token
            for alias in [*(product.aliases or []), *product.alternative_product_ids]
            for token in self._normalize(alias).split()
        }
        brand_tokens = set(self._normalize(product.brand).split())
        candidate_tokens = product_tokens | alias_tokens | brand_tokens

        raw_tokens = set(raw_name.split())
        overlap = len(raw_tokens & candidate_tokens)
        if not overlap:
            return 0.0

        base = overlap / max(len(raw_tokens), 1)
        canonical = self._normalize(product.canonical_name)
        if canonical == raw_name or canonical in raw_name or raw_name in canonical:
            base += 0.25
        if self._normalize(product.brand) in raw_name:
            base += 0.1

        if self.fuzzy_enabled:
            base += self._fuzzy_bonus(raw_name, canonical)

        return min(base, 1.0)

    @staticmethod
    def _fuzzy_bonus(raw_name: str, canonical_name: str) -> float:
        if not raw_name or not canonical_name:
            return 0.0
        if canonical_name.startswith(raw_name) or raw_name.startswith(canonical_name):
            return 0.1
        return 0.0
