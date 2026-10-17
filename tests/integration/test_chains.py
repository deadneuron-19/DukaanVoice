from __future__ import annotations

from dukaanvoice.chains.clarification import ClarificationChain
from dukaanvoice.chains.response_generation import ResponseGenerationChain


class FakeTextClient:
    def __init__(self, response: str) -> None:
        self.response = response
        self.prompt = ""

    def generate_text(self, prompt: str) -> str:
        self.prompt = prompt
        return self.response


def test_clarification_chain_supplies_only_application_known_candidates() -> None:
    client = FakeTextClient("Did you mean Amul milk or Mother Dairy milk?")

    question = ClarificationChain(client).run("milk", ["Amul milk", "Mother Dairy milk"])

    assert question == client.response
    assert "Amul milk" in client.prompt
    assert "Do not add products" in client.prompt


def test_response_generation_grounds_prompt_in_application_result() -> None:
    client = FakeTextClient("Your draft order total is Rs. 120.")

    message = ResponseGenerationChain(client).run("Draft order total: Rs. 120")

    assert message == client.response
    assert "Draft order total: Rs. 120" in client.prompt
    assert "Do not add, remove, or change any factual details" in client.prompt
