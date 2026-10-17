from __future__ import annotations

from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from dukaanvoice.core.exceptions import ConfigurationError


class Settings(BaseSettings):
    """Validated application settings loaded from environment and .env files."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    app_name: str = Field(default="DukaanVoice", alias="APP_NAME")
    app_env: str = Field(default="development", alias="APP_ENV")
    api_host: str = Field(default="0.0.0.0", alias="API_HOST")
    api_port: int = Field(default=8000, alias="API_PORT")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    data_dir: Path = Field(default=Path("./data"), alias="DATA_DIR")
    llm_provider: str = Field(default="mock", alias="LLM_PROVIDER")
    llm_model: str = Field(default="gpt-4o-mini", alias="LLM_MODEL")
    llm_api_key: str | None = Field(default=None, alias="LLM_API_KEY")
    llm_base_url: str | None = Field(default=None, alias="LLM_BASE_URL")
    gnani_api_key: str | None = Field(default=None, alias="GNANI_API_KEY")
    gnani_stt_model: str = Field(default="prisma", alias="GNANI_STT_MODEL")
    gnani_tts_model: str = Field(default="timbre", alias="GNANI_TTS_MODEL")
    development_mock_mode: bool = Field(default=True, alias="DEVELOPMENT_MOCK_MODE")
    request_timeout_seconds: int = Field(default=30, alias="REQUEST_TIMEOUT_SECONDS")
    max_retries: int = Field(default=2, alias="MAX_RETRIES")
    max_upload_size_mb: int = Field(default=20, alias="MAX_UPLOAD_SIZE_MB")
    supported_audio_formats: str = Field(default="wav,m4a,mp3", alias="SUPPORTED_AUDIO_FORMATS")
    allowed_origins: str = Field(
        default="http://localhost:3000,http://127.0.0.1:3000",
        alias="ALLOWED_ORIGINS",
    )

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, value: str) -> str:
        allowed = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        normalized = value.upper()
        if normalized not in allowed:
            raise ConfigurationError(f"Invalid log level: {value}. Use one of {sorted(allowed)}.")
        return normalized

    @field_validator("data_dir")
    @classmethod
    def validate_data_dir(cls, value: Path) -> Path:
        if not value.exists():
            value.mkdir(parents=True, exist_ok=True)
        return value

    @property
    def supported_audio_extensions(self) -> list[str]:
        return [ext.strip().lower() for ext in self.supported_audio_formats.split(",") if ext.strip()]

    @property
    def allowed_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.allowed_origins.split(",") if origin.strip()]


settings = Settings()
