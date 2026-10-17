from __future__ import annotations

from fastapi.testclient import TestClient

from dukaanvoice.main import create_app


def test_health_reports_application_status() -> None:
    response = TestClient(create_app()).get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.headers["X-Correlation-ID"]


def test_correlation_id_is_preserved(api_client: TestClient) -> None:
    response = api_client.get("/health", headers={"X-Correlation-ID": "test-request-123"})

    assert response.headers["X-Correlation-ID"] == "test-request-123"
