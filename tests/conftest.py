from __future__ import annotations

import os

import pytest


@pytest.fixture
def mock_env(monkeypatch):
    monkeypatch.setenv("APP_NAME", "DukaanVoice")
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("API_HOST", "127.0.0.1")
    monkeypatch.setenv("API_PORT", "8001")
    monkeypatch.setenv("LOG_LEVEL", "INFO")
    monkeypatch.setenv("DATA_DIR", "./data")
    monkeypatch.setenv("LLM_PROVIDER", "mock")
    monkeypatch.setenv("DEVELOPMENT_MOCK_MODE", "true")
    monkeypatch.setenv("GNANI_API_KEY", "")
