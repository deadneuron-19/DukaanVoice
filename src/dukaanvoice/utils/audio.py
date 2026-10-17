from __future__ import annotations

from pathlib import Path


def ensure_audio_file(path: str | Path, max_size_bytes: int = 20 * 1024 * 1024) -> Path:
    candidate = Path(path)
    if not candidate.exists():
        raise FileNotFoundError(f"Audio file does not exist: {candidate}")
    if candidate.stat().st_size > max_size_bytes:
        raise ValueError(f"Audio file exceeds the maximum allowed size of {max_size_bytes} bytes.")
    return candidate
