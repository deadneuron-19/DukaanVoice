from __future__ import annotations

from types import SimpleNamespace

import pytest
from pydantic import BaseModel

from dukaanvoice.core.exceptions import (
    ProviderOutputError,
    ProviderTimeoutError,
    ProviderUnavailableError,
)
from dukaanvoice.chains.order_extraction import OrderExtractionChain
from dukaanvoice.integrations.llm_client import LLMClient
from dukaanvoice.schemas.llm_outputs import OrderExtractionResult


class FakeModel:
    def __init__(self, result: object) -> None:
        self.result = result
        self.calls = 0

    def with_structured_output(self, schema: type[BaseModel]) -> FakeModel:
        return self

    def invoke(self, prompt: str, **kwargs: object) -> object:
        self.calls += 1
        if isinstance(self.result, Exception):
            raise self.result
        return self.result


def test_structured_result_is_pydantic_validated() -> None:
    model = FakeModel(
        {
            "original_transcript": "do doodh",
            "extracted_items": [{"spoken_product_name": "milk", "spoken_quantity": 2}],
            "clarification_questions": [],
        }
    )
    client = LLMClient(provider="openai", model=model)

    result = client.generate_structured(OrderExtractionResult, "extract this")

    assert isinstance(result, OrderExtractionResult)
    assert result.extracted_items[0].spoken_quantity == 2


def test_malformed_structured_result_is_rejected() -> None:
    client = LLMClient(provider="openai", model=FakeModel({"unexpected": "field"}))

    with pytest.raises(ProviderOutputError):
        client.generate_structured(OrderExtractionResult, "extract this")


def test_text_response_normalizes_message_content() -> None:
    model = FakeModel(SimpleNamespace(content=[{"type": "text", "text": "  Hello customer. "}]))
    client = LLMClient(provider="openai", model=model)

    assert client.generate_text("write a response") == "Hello customer."


def test_transient_timeout_is_retried_then_reported(monkeypatch: pytest.MonkeyPatch) -> None:
    model = FakeModel(TimeoutError("network timeout"))
    client = LLMClient(provider="openai", model=model)
    monkeypatch.setattr("dukaanvoice.integrations.llm_client.settings.max_retries", 1)
    monkeypatch.setattr("dukaanvoice.integrations.llm_client.time.sleep", lambda _: None)

    with pytest.raises(ProviderTimeoutError):
        client.generate_text("try provider")

    assert model.calls == 2


def test_mock_mode_does_not_claim_real_inference() -> None:
    client = LLMClient(provider="mock")

    assert client.health_check()["inference"] is False
    with pytest.raises(ProviderUnavailableError):
        client.generate_text("do not send a real provider request")


def test_extraction_chain_keeps_caller_transcript_and_discards_model_confidence() -> None:
    model = FakeModel(
        {
            "original_transcript": "model supplied transcript",
            "extracted_items": [{"spoken_product_name": "milk", "spoken_quantity": 2}],
            "clarification_questions": [],
            "extraction_confidence": 0.99,
        }
    )
    chain = OrderExtractionChain(LLMClient(provider="openai", model=model))

    result = chain.run("do litre doodh", "Amul Toned Milk; Amul 1L")

    assert result.original_transcript == "do litre doodh"
    assert result.extraction_confidence is None
