from __future__ import annotations

from dukaanvoice.core.config import Settings


def test_settings_loads_default_values(mock_env):
    settings = Settings()
    assert settings.app_name == "DukaanVoice"
    assert settings.app_env == "test"
    assert settings.api_port == 8001
    assert settings.supported_audio_extensions
