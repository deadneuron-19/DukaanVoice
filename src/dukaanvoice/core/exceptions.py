from __future__ import annotations

class DukaanVoiceError(Exception):
    """Base application exception."""


class ConfigurationError(DukaanVoiceError):
    """Raised when required app configuration is invalid."""


class RepositoryError(DukaanVoiceError):
    """Raised when persistence fails."""


class ProductNotFoundError(DukaanVoiceError):
    """Raised when a requested product cannot be found."""


class AmbiguousProductError(DukaanVoiceError):
    """Raised when product matching is ambiguous."""


class InventoryError(DukaanVoiceError):
    """Raised when inventory constraints are violated."""


class OrderValidationError(DukaanVoiceError):
    """Raised when an order cannot be validated."""


class ProviderError(DukaanVoiceError):
    """Raised when a provider call fails."""


class ProviderAuthError(ProviderError):
    """Raised for provider authentication failures."""


class ProviderTimeoutError(ProviderError):
    """Raised when a provider times out."""


class ProviderRateLimitError(ProviderError):
    """Raised when a provider rate limit is hit."""


class ProviderOutputError(ProviderError):
    """Raised when a provider response cannot be validated."""


class ProviderUnavailableError(ProviderError):
    """Raised when an integration is intentionally unavailable."""
