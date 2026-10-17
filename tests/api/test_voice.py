from __future__ import annotations

from fastapi.testclient import TestClient

from dukaanvoice.main import create_app


def test_voice_routes_do_not_claim_unavailable_provider_inference() -> None:
    client = TestClient(create_app())

    transcription = client.post("/voice/transcribe")
    synthesis = client.post("/voice/synthesize")

    assert transcription.status_code == 501
    assert "Gnani Prisma" in transcription.json()["detail"]
    assert synthesis.status_code == 501
    assert "Gnani Timbre" in synthesis.json()["detail"]
