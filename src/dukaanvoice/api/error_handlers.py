from __future__ import annotations

import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from dukaanvoice.core.exceptions import (
    AmbiguousProductError,
    ConfigurationError,
    DukaanVoiceError,
    InventoryError,
    OrderValidationError,
    ProviderAuthError,
    ProviderError,
    ProviderOutputError,
    ProviderRateLimitError,
    ProviderTimeoutError,
    ProviderUnavailableError,
    ProductNotFoundError,
    RepositoryError,
)

logger = logging.getLogger(__name__)


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(DukaanVoiceError)
    async def handle_domain_error(request: Request, exc: DukaanVoiceError) -> JSONResponse:
        status_code = 400
        if isinstance(exc, ProductNotFoundError):
            status_code = 404
            detail = str(exc)
        elif isinstance(exc, (InventoryError, OrderValidationError, AmbiguousProductError)):
            status_code = 409
            detail = str(exc)
        elif isinstance(exc, RepositoryError):
            status_code = 500
            logger.exception("Repository operation failed", exc_info=exc)
            detail = "A storage operation failed."
        elif isinstance(exc, ProviderUnavailableError):
            status_code = 501
            detail = str(exc)
        elif isinstance(exc, ProviderAuthError):
            status_code = 503
            detail = "Provider credentials are not valid or configured."
        elif isinstance(exc, ProviderRateLimitError):
            status_code = 429
            detail = str(exc)
        elif isinstance(exc, ProviderTimeoutError):
            status_code = 504
            detail = str(exc)
        elif isinstance(exc, ProviderOutputError):
            status_code = 502
            detail = str(exc)
        elif isinstance(exc, ProviderError):
            status_code = 502
            detail = str(exc)
        elif isinstance(exc, ConfigurationError):
            status_code = 503
            detail = str(exc)
        else:
            detail = str(exc)

        return JSONResponse(
            status_code=status_code,
            content={"detail": detail},
            headers={"X-Correlation-ID": request.state.correlation_id},
        )
