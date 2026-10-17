from __future__ import annotations

import logging
import mimetypes
from pathlib import Path
from typing import Any, Protocol
from uuid import uuid4

from dukaanvoice.core.config import settings
from dukaanvoice.core.exceptions import (
    ConfigurationError,
    ProviderAuthError,
    ProviderOutputError,
    ProviderUnavailableError,
)
from dukaanvoice.schemas.speech import SpeechResult, TranscriptionResult

logger = logging.getLogger(__name__)

_CONTENT_TYPES = {
    ".wav": "audio/wav",
    ".mp3": "audio/mpeg",
    ".m4a": "audio/mp4",
}


class GnaniTransport(Protocol):
    """Internal adapter shape; concrete wire details require official Gnani documentation."""

    def transcribe_audio(self, **kwargs: Any) -> Any: ...

    def synthesize_speech(self, **kwargs: Any) -> Any: ...


class GnaniClient:
    """Speech-provider boundary with normalized results and strict audio checks.

    Gnani's public material reviewed for this phase does not document the
    Prisma/Timbre request contract. Therefore this client intentionally has
    no guessed HTTP endpoint or authentication scheme.
    """

    def __init__(
        self,
        api_key: str | None = None,
        *,
        transport: GnaniTransport | None = None,
    ) -> None:
        self.api_key = api_key if api_key is not None else settings.gnani_api_key
        self._transport = transport
        self.mock_mode = settings.development_mock_mode and not bool(self.api_key)

        if self.api_key and self._transport is None:
            raise ProviderUnavailableError(
                "Gnani Prisma/Timbre wire integration is not enabled: official request documentation "
                "was unavailable, so no endpoint or authentication scheme has been assumed."
            )
        if not self.api_key and not self.mock_mode:
            raise ProviderAuthError(
                "GNANI_API_KEY is missing. Configure credentials or explicitly enable development mock mode."
            )

    def transcribe_audio(
        self,
        audio_path: str | Path,
        language: str | None = None,
    ) -> TranscriptionResult:
        if self._transport is None:
            raise ProviderUnavailableError(
                "Gnani transcription is unavailable in this mode; mock mode does not claim a real transcript."
            )

        path = Path(audio_path)
        content_type = self._validate_audio(path)
        audio_data = path.read_bytes()
        response = self._transport.transcribe_audio(
            audio_data=audio_data,
            content_type=content_type,
            model=settings.gnani_stt_model,
            language=language,
            api_key=self.api_key,
        )
        try:
            transcript = TranscriptionResult.model_validate(
                {
                    "transcript": response["transcript"],
                    "language": response.get("language") or language,
                    "confidence": response.get("confidence"),
                    "provider": "gnani",
                }
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise ProviderOutputError("Gnani returned an invalid transcription response.") from exc
        logger.info("Gnani transcription completed audio_bytes=%d", len(audio_data))
        return transcript

    def synthesize_speech(
        self,
        text: str,
        output_path: str | Path | None = None,
    ) -> SpeechResult:
        if not text.strip():
            raise ValueError("Speech text must not be blank.")
        if self._transport is None:
            raise ProviderUnavailableError(
                "Gnani synthesis is unavailable in this mode; mock mode does not create fake speech audio."
            )

        response = self._transport.synthesize_speech(
            text=text,
            model=settings.gnani_tts_model,
            api_key=self.api_key,
        )
        if not isinstance(response, dict) or not isinstance(response.get("audio_content"), bytes):
            raise ProviderOutputError("Gnani returned an invalid synthesis response.")

        audio_content = response["audio_content"]
        if not audio_content:
            raise ProviderOutputError("Gnani returned empty synthesized audio.")

        output_dir = (settings.data_dir / "generated_audio").resolve()
        output_dir.mkdir(parents=True, exist_ok=True)
        destination = Path(output_path).resolve() if output_path else output_dir / f"{uuid4().hex}.mp3"
        if not destination.is_relative_to(output_dir):
            raise ConfigurationError("Generated audio must be stored inside the configured generated_audio directory.")
        destination.write_bytes(audio_content)
        content_type = response.get("content_type", "audio/mpeg")
        result = SpeechResult(output_path=destination, content_type=content_type, provider="gnani")
        logger.info("Gnani synthesis completed output_bytes=%d", len(audio_content))
        return result

    def health_check(self) -> dict[str, Any]:
        if self.mock_mode:
            return {
                "status": "unavailable",
                "provider": "gnani",
                "mode": "development_mock",
                "inference": False,
            }
        if self._transport is None:
            return {
                "status": "unavailable",
                "provider": "gnani",
                "reason": "official request contract unavailable",
                "inference": False,
            }
        return {"status": "adapter_configured", "provider": "gnani", "inference": False}

    @staticmethod
    def _validate_audio(path: Path) -> str:
        if not path.is_file():
            raise ValueError(f"Audio file does not exist: {path}")
        extension = path.suffix.lower()
        if extension not in {f".{value}" for value in settings.supported_audio_extensions}:
            raise ValueError(f"Unsupported audio extension: {extension or '(none)'}")
        content_type = _CONTENT_TYPES.get(extension) or mimetypes.guess_type(path.name)[0]
        if content_type is None or not content_type.startswith("audio/"):
            raise ValueError("Could not determine a supported audio content type.")
        size = path.stat().st_size
        max_bytes = settings.max_upload_size_mb * 1024 * 1024
        if size == 0:
            raise ValueError("Audio file must not be empty.")
        if size > max_bytes:
            raise ValueError(f"Audio file exceeds the configured {settings.max_upload_size_mb} MB limit.")
        return content_type
