from __future__ import annotations

from dukaanvoice.integrations.gnani_client import GnaniClient


class VoiceService:
    """Wraps speech transcription and synthesis behind the integration boundary."""

    def __init__(self, gnani_client: GnaniClient | None = None) -> None:
        self.gnani_client = gnani_client or GnaniClient()

    def transcribe(self, audio_path: str, language: str | None = None) -> dict[str, str]:
        result = self.gnani_client.transcribe_audio(audio_path, language=language)
        return {"transcript": result.get("transcript", ""), "language": str(result.get("language") or language or "en")}

    def synthesize(self, text: str, output_path: str | None = None) -> dict[str, str]:
        result = self.gnani_client.synthesize_speech(text, output_path=output_path)
        return {"output_path": str(result.get("output_path", ""))}
