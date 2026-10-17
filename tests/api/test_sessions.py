from __future__ import annotations

from fastapi.testclient import TestClient


def test_get_session_returns_persisted_state(api_client: TestClient) -> None:
    response = api_client.get("/sessions/session-api-1")

    assert response.status_code == 200
    assert response.json()["current_state"] == "AWAITING_CONFIRMATION"
    assert response.json()["draft_order_id"] == "ORD-API-1"


def test_get_session_returns_404_for_unknown_id(api_client: TestClient) -> None:
    response = api_client.get("/sessions/missing-session")

    assert response.status_code == 404
    assert response.json()["detail"] == "Session not found."
