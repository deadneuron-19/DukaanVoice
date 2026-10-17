from __future__ import annotations

import logging
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from dukaanvoice.api.error_handlers import register_error_handlers
from dukaanvoice.api.routes.health import router as health_router
from dukaanvoice.api.routes.orders import router as orders_router
from dukaanvoice.api.routes.products import router as products_router
from dukaanvoice.api.routes.sessions import router as sessions_router
from dukaanvoice.api.routes.voice import router as voice_router
from dukaanvoice.core.config import settings
from dukaanvoice.core.logging import configure_logging
from dukaanvoice.repositories.json_order_repository import JSONOrderRepository
from dukaanvoice.repositories.json_product_repository import JSONProductRepository
from dukaanvoice.repositories.json_session_repository import JSONSessionRepository
from dukaanvoice.services.order_workflow_service import OrderWorkflowService

configure_logging(settings.log_level)
logger = logging.getLogger(__name__)


def create_app(
    *,
    product_repository: JSONProductRepository | None = None,
    order_repository: JSONOrderRepository | None = None,
    session_repository: JSONSessionRepository | None = None,
    order_workflow_service: OrderWorkflowService | None = None,
) -> FastAPI:
    """Build the application and allow repositories to be replaced in tests."""
    application = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        description="Voice-first ordering assistant for local kirana shops.",
    )
    application.state.product_repository = product_repository or JSONProductRepository()
    application.state.order_repository = order_repository or JSONOrderRepository()
    application.state.session_repository = session_repository or JSONSessionRepository()
    application.state.order_workflow_service = order_workflow_service or OrderWorkflowService(
        application.state.product_repository,
        application.state.order_repository,
        application.state.session_repository,
    )

    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origin_list,
        allow_credentials=False,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
        allow_headers=["Authorization", "Content-Type", "Idempotency-Key", "X-Correlation-ID"],
        expose_headers=["X-Correlation-ID"],
    )

    @application.middleware("http")
    async def correlation_id_middleware(request: Request, call_next):
        supplied_id = request.headers.get("X-Correlation-ID", "").strip()
        correlation_id = supplied_id[:128] if supplied_id else str(uuid4())
        request.state.correlation_id = correlation_id
        try:
            response = await call_next(request)
        except Exception:
            logger.exception("Unhandled request failure correlation_id=%s", correlation_id)
            response = JSONResponse(
                status_code=500,
                content={"detail": "Internal server error."},
            )
        response.headers["X-Correlation-ID"] = correlation_id
        return response

    register_error_handlers(application)
    application.include_router(health_router)
    application.include_router(products_router)
    application.include_router(orders_router)
    application.include_router(sessions_router)
    application.include_router(voice_router)

    @application.get("/")
    def root() -> dict[str, str]:
        return {"message": "DukaanVoice backend is running."}

    return application


app = create_app()
