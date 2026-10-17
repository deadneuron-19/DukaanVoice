from __future__ import annotations

import logging
import time
from typing import Any, TypeVar

from pydantic import BaseModel, ValidationError

from dukaanvoice.core.config import settings
from dukaanvoice.core.exceptions import (
    ConfigurationError,
    ProviderAuthError,
    ProviderError,
    ProviderOutputError,
    ProviderRateLimitError,
    ProviderTimeoutError,
    ProviderUnavailableError,
)

logger = logging.getLogger(__name__)
SchemaT = TypeVar("SchemaT", bound=BaseModel)


class LLMClient:
    """Single boundary for configured LangChain text-model inference."""

    def __init__(
        self,
        provider: str | None = None,
        *,
        model: Any | None = None,
        api_key: str | None = None,
        base_url: str | None = None,
    ) -> None:
        self.provider = (provider or settings.llm_provider).strip().lower()
        self._model = model
        self._mock_mode = self.provider == "mock"
        self._transient_errors: tuple[type[BaseException], ...] = (TimeoutError, ConnectionError)
        self._auth_error: type[BaseException] | None = None
        self._rate_limit_error: type[BaseException] | None = None

        if self._mock_mode:
            if not settings.development_mock_mode:
                raise ConfigurationError(
                    "LLM_PROVIDER=mock requires DEVELOPMENT_MOCK_MODE=true."
                )
            return

        if self.provider == "none":
            raise ConfigurationError(
                "No LLM provider is configured. Set LLM_PROVIDER=openai and LLM_API_KEY, "
                "or explicitly enable development mock mode."
            )

        if self._model is not None:
            return

        if self.provider != "openai":
            raise ConfigurationError(
                f"Unsupported LLM_PROVIDER '{self.provider}'. Supported providers: openai, mock."
            )

        configured_key = api_key or settings.llm_api_key
        if not configured_key:
            raise ProviderAuthError(
                "LLM_API_KEY is required for the OpenAI provider; use explicit mock mode for local development."
            )

        try:
            from openai import APIConnectionError, APITimeoutError, AuthenticationError, RateLimitError
            from langchain_openai import ChatOpenAI
        except ImportError as exc:
            raise ConfigurationError(
                "OpenAI LangChain integration is unavailable. Install project dependencies with "
                "'pip install -r requirements.txt'."
            ) from exc

        self._transient_errors = (
            TimeoutError,
            ConnectionError,
            APITimeoutError,
            APIConnectionError,
            RateLimitError,
        )
        self._auth_error = AuthenticationError
        self._rate_limit_error = RateLimitError
        self._model = ChatOpenAI(
            model=settings.llm_model,
            api_key=configured_key,
            base_url=base_url or settings.llm_base_url,
            timeout=settings.request_timeout_seconds,
            max_retries=0,
        )

    def generate_structured(
        self,
        schema: type[SchemaT],
        prompt: str,
        **kwargs: Any,
    ) -> SchemaT:
        """Invoke structured model output and validate it again at this boundary."""
        if not prompt.strip():
            raise ValueError("Prompt must not be blank.")
        if self._model is None:
            raise ProviderUnavailableError(
                "Structured LLM inference is unavailable in mock mode; inject a fake model in tests "
                "or configure a real provider."
            )

        try:
            structured_model = self._model.with_structured_output(schema)
            raw = self._invoke_with_retries(structured_model, prompt, **kwargs)
            if isinstance(raw, schema):
                return raw
            if isinstance(raw, BaseModel):
                raw = raw.model_dump()
            try:
                return schema.model_validate(raw)
            except (ValidationError, TypeError, ValueError) as exc:
                raise ProviderOutputError(
                    f"LLM provider returned output that does not match {schema.__name__}."
                ) from exc
        except (ProviderAuthError, ProviderError, ValueError):
            raise
        except Exception as exc:
            self._raise_provider_error(exc)

    def generate_text(self, prompt: str, **kwargs: Any) -> str:
        """Generate a non-structured response and normalize LangChain message content."""
        if not prompt.strip():
            raise ValueError("Prompt must not be blank.")
        if self._model is None:
            raise ProviderUnavailableError(
                "Text LLM inference is unavailable in mock mode; inject a fake model in tests "
                "or configure a real provider."
            )

        try:
            response = self._invoke_with_retries(self._model, prompt, **kwargs)
        except (ProviderAuthError, ProviderError, ValueError):
            raise
        except Exception as exc:
            self._raise_provider_error(exc)

        content = getattr(response, "content", response)
        if isinstance(content, str) and content.strip():
            return content.strip()
        if isinstance(content, list):
            text = "".join(
                part.get("text", "")
                for part in content
                if isinstance(part, dict) and isinstance(part.get("text"), str)
            ).strip()
            if text:
                return text
        raise ProviderOutputError("LLM provider returned an empty or unsupported text response.")

    def health_check(self) -> dict[str, Any]:
        """Report local configuration without making a paid inference request."""
        if self._mock_mode:
            return {
                "status": "unavailable",
                "provider": "mock",
                "mode": "development",
                "inference": False,
            }
        if self._model is None:
            return {"status": "unavailable", "provider": self.provider, "inference": False}
        return {"status": "configured", "provider": self.provider, "inference": False}

    def _invoke_with_retries(self, model: Any, prompt: str, **kwargs: Any) -> Any:
        attempts = max(0, settings.max_retries) + 1
        for attempt in range(attempts):
            started = time.monotonic()
            try:
                result = model.invoke(prompt, **kwargs)
                logger.info(
                    "LLM request completed provider=%s elapsed_ms=%.1f attempt=%d",
                    self.provider,
                    (time.monotonic() - started) * 1000,
                    attempt + 1,
                )
                return result
            except self._transient_errors as exc:
                if attempt + 1 >= attempts:
                    self._raise_provider_error(exc)
                logger.warning(
                    "Transient LLM provider failure provider=%s attempt=%d",
                    self.provider,
                    attempt + 1,
                )
                time.sleep(min(0.25 * (2**attempt), 2.0))
            except Exception as exc:
                self._raise_provider_error(exc)

        raise ProviderError("LLM provider failed after bounded retries.")

    def _raise_provider_error(self, exc: Exception) -> None:
        if self._auth_error is not None and isinstance(exc, self._auth_error):
            raise ProviderAuthError("LLM provider rejected authentication credentials.") from exc
        if self._rate_limit_error is not None and isinstance(exc, self._rate_limit_error):
            raise ProviderRateLimitError("LLM provider rate limit persisted after bounded retries.") from exc
        if isinstance(exc, (TimeoutError,)) or exc.__class__.__name__ in {"APITimeoutError", "Timeout"}:
            raise ProviderTimeoutError("LLM provider request timed out.") from exc
        if isinstance(exc, (ConnectionError,)) or exc.__class__.__name__ == "APIConnectionError":
            raise ProviderError("Could not connect to the LLM provider.") from exc
        if isinstance(exc, ProviderError):
            raise exc
        logger.error("LLM provider request failed provider=%s error_type=%s", self.provider, type(exc).__name__)
        raise ProviderError("LLM provider request failed.") from exc
