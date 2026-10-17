from __future__ import annotations

import json
import os
from pathlib import Path
from uuid import uuid4

from dukaanvoice.core.config import settings
from dukaanvoice.core.exceptions import RepositoryError
from dukaanvoice.repositories.interfaces import SessionRepository


class JSONSessionRepository(SessionRepository):
    """JSON-backed conversation session persistence for the MVP."""

    def __init__(self, path: str | Path | None = None) -> None:
        base_path = Path(path) if path is not None else settings.data_dir / "sessions.json"
        self.path = Path(base_path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def get_session(self, session_id: str) -> dict | None:
        records = self._load_source()
        for record in records:
            if record.get("session_id") == session_id:
                return record
        return None

    def save_session(self, session_id: str, state: dict) -> None:
        records = self._load_source()
        state["session_id"] = session_id
        existing_index = next((index for index, item in enumerate(records) if item.get("session_id") == session_id), None)
        if existing_index is None:
            records.append(state)
        else:
            records[existing_index] = state
        temporary_path = self.path.with_name(f".{self.path.name}.{uuid4().hex}.tmp")
        try:
            temporary_path.write_text(json.dumps(records, indent=2), encoding="utf-8")
            os.replace(temporary_path, self.path)
        except OSError as exc:
            temporary_path.unlink(missing_ok=True)
            raise RepositoryError(f"Could not persist session storage file: {self.path}") from exc

    def _load_source(self) -> list[dict]:
        if not self.path.exists():
            return []
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise RepositoryError(f"Session storage file is invalid JSON: {self.path}") from exc
        if not isinstance(data, list):
            raise RepositoryError(f"Session storage file must contain a list of session records: {self.path}")
        return data
