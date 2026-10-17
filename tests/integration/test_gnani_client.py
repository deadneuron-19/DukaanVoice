from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from dukaanvoice.core.config import settings
from dukaanvoice.core.exceptions import ProviderOutputError, ProviderUnavailableError
from dukaanvoice.integrations.gnani_client import GnaniClient


class FakeGnaniTransport:
    def transcribe_audio(self, **kwargs: Any) -> dict[str, Any]:
        assert kwargs["content_type"] == "audio/wav"
        return {"transcript": "do litre doodh", "language": "hi", "confidence": 0.91}

    def synthesize_speech(self, **kwargs: Any) -> dict[str, Any]:
        return {"audio_content": b"test-audio", "content_type": "audio/mpeg"}


def test_transcription_is_normalized_and_audio_is_validated(tmp_path: Path) -> None:
    audio_path = tmp_path / "order.wav"
    audio_path.write_bytes(b"audio")
    client = GnaniClient(api_key="test-key", transport=FakeGnaniTransport())

    result = client.transcribe_audio(audio_path)

    assert result.transcript == "do litre doodh"
    assert result.language == "hi"
    assert result.provider == "gnani"


def test_speech_output_is_written_only_under_configured_audio_dir(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings, "data_dir", tmp_path)
    client = GnaniClient(api_key="test-key", transport=FakeGnaniTransport())

    result = client.synthesize_speech("Namaste")

    assert result.output_path == tmp_path / "generated_audio" / result.output_path.name
    assert result.output_path.read_bytes() == b"test-audio"


def test_invalid_audio_extension_is_rejected(tmp_path: Path) -> None:
    audio_path = tmp_path / "order.txt"
    audio_path.write_text("not audio", encoding="utf-8")
    client = GnaniClient(api_key="test-key", transport=FakeGnaniTransport())

    with pytest.raises(ValueError, match="Unsupported audio extension"):
        client.transcribe_audio(audio_path)


def test_invalid_provider_response_is_rejected(tmp_path: Path) -> None:
    class InvalidTransport(FakeGnaniTransport):
        def transcribe_audio(self, **kwargs: Any) -> dict[str, Any]:
            return {"language": "hi"}

    audio_path = tmp_path / "order.wav"
    audio_path.write_bytes(b"audio")
    client = GnaniClient(api_key="test-key", transport=InvalidTransport())

    with pytest.raises(ProviderOutputError):
        client.transcribe_audio(audio_path)


def test_explicit_mock_mode_does_not_claim_transcription(tmp_path: Path) -> None:
    audio_path = tmp_path / "order.wav"
    audio_path.write_bytes(b"audio")
    client = GnaniClient(api_key="")

    assert client.health_check()["inference"] is False
    with pytest.raises(ProviderUnavailableError):
        client.transcribe_audio(audio_path)
