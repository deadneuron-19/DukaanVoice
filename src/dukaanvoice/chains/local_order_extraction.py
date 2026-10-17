from __future__ import annotations

import re
from decimal import Decimal

from dukaanvoice.domain.entities import ProductEntity
from dukaanvoice.schemas.llm_outputs import ExtractedProductRequest, OrderExtractionResult

_NUMBER_WORDS = {
    "a": Decimal(1),
    "an": Decimal(1),
    "one": Decimal(1),
    "ek": Decimal(1),
    "एक": Decimal(1),
    "two": Decimal(2),
    "do": Decimal(2),
    "दो": Decimal(2),
    "three": Decimal(3),
    "teen": Decimal(3),
    "तीन": Decimal(3),
    "four": Decimal(4),
    "chaar": Decimal(4),
    "चार": Decimal(4),
    "five": Decimal(5),
    "paanch": Decimal(5),
    "पांच": Decimal(5),
    "छह": Decimal(6),
    "six": Decimal(6),
    "seven": Decimal(7),
    "eight": Decimal(8),
    "nine": Decimal(9),
    "ten": Decimal(10),
}
_NUMBER_PATTERN = r"\d+(?:\.\d+)?|" + "|".join(
    sorted((re.escape(word) for word in _NUMBER_WORDS), key=len, reverse=True)
)
_UNIT_PATTERN = (
    r"kilograms?|kilos?|kgs?|kg|grams?|gms?|g|millilit(?:er|re)s?|ml|lit(?:er|re)s?|l|"
    r"packets?|packs?|pieces?|pcs?"
)


class LocalOrderExtraction:
    """Extract only product names and quantities explicitly present in the catalogue and transcript."""

    def run(
        self,
        transcript: str,
        catalogue: list[ProductEntity],
    ) -> OrderExtractionResult:
        if not transcript.strip():
            raise ValueError("Transcript must not be blank.")

        occurrences: list[tuple[int, int, str, ProductEntity]] = []
        for product in catalogue:
            if not product.is_active:
                continue
            names = {product.canonical_name, *(product.aliases or []), *product.alternative_product_ids}
            for name in names:
                if not name.strip():
                    continue
                pattern = re.compile(rf"(?<!\w){re.escape(name.strip())}(?!\w)", re.IGNORECASE)
                occurrences.extend(
                    (match.start(), match.end(), match.group(), product)
                    for match in pattern.finditer(transcript)
                )

        selected: list[tuple[int, int, str, list[ProductEntity]]] = []
        for start, end, matched_name, product in sorted(
            occurrences,
            key=lambda occurrence: (occurrence[0], -(occurrence[1] - occurrence[0])),
        ):
            overlapping = next(
                (
                    index
                    for index, (selected_start, selected_end, _, _) in enumerate(selected)
                    if start < selected_end and end > selected_start
                ),
                None,
            )
            if overlapping is not None:
                selected_start, selected_end, selected_name, matches = selected[overlapping]
                if start == selected_start and end == selected_end:
                    if product.product_id not in {match.product_id for match in matches}:
                        matches.append(product)
                    if len(matched_name) > len(selected_name):
                        selected[overlapping] = (selected_start, selected_end, matched_name, matches)
                continue
            selected.append((start, end, matched_name, [product]))

        selected.sort(key=lambda occurrence: occurrence[0])
        extracted_items: list[ExtractedProductRequest] = []
        previous_end = 0
        for start, end, matched_name, matches in selected:
            prefix = transcript[previous_end:start]
            quantity, unit = self._quantity_before_product(prefix)
            distinct_matches = {product.product_id: product for product in matches}
            if len(distinct_matches) == 1:
                product = next(iter(distinct_matches.values()))
                product_name = product.canonical_name
                brand = product.brand if re.search(
                    rf"(?<!\w){re.escape(product.brand)}(?!\w)",
                    prefix,
                    re.IGNORECASE,
                ) else None
            else:
                product_name = matched_name
                brand = None
            extracted_items.append(
                ExtractedProductRequest(
                    spoken_product_name=product_name,
                    spoken_quantity=quantity,
                    spoken_unit=unit,
                    brand_preference=brand,
                    ambiguity=len(distinct_matches) > 1,
                )
            )
            previous_end = end

        return OrderExtractionResult(
            original_transcript=transcript,
            extracted_items=extracted_items,
        )

    @staticmethod
    def _quantity_before_product(prefix: str) -> tuple[Decimal | None, str | None]:
        matches = list(
            re.finditer(
                rf"(?<!\w)(?P<quantity>{_NUMBER_PATTERN})(?:\s*(?P<unit>{_UNIT_PATTERN}))?(?!\w)",
                prefix,
                re.IGNORECASE,
            )
        )
        if not matches:
            return None, None

        match = matches[-1]
        raw_quantity = match.group("quantity").casefold()
        quantity = _NUMBER_WORDS.get(raw_quantity, Decimal(raw_quantity) if raw_quantity[0].isdigit() else None)
        raw_unit = match.group("unit")
        unit_aliases = {
            "kilogram": "kg",
            "kilograms": "kg",
            "kilo": "kg",
            "kilos": "kg",
            "gram": "g",
            "grams": "g",
            "gm": "g",
            "gms": "g",
            "milliliter": "ml",
            "milliliters": "ml",
            "millilitre": "ml",
            "millilitres": "ml",
            "liter": "litre",
            "liters": "litre",
            "litre": "litre",
            "litres": "litre",
            "l": "litre",
            "packet": "pack",
            "packets": "pack",
            "packs": "pack",
            "pieces": "pcs",
            "piece": "pcs",
        }
        normalized_unit = unit_aliases.get(raw_unit.casefold(), raw_unit.casefold()) if raw_unit else None
        return quantity, normalized_unit
