from __future__ import annotations

from fastapi import Request

from dukaanvoice.repositories.json_order_repository import JSONOrderRepository
from dukaanvoice.repositories.json_product_repository import JSONProductRepository
from dukaanvoice.repositories.json_session_repository import JSONSessionRepository
from dukaanvoice.services.order_workflow_service import OrderWorkflowService


def get_product_repository(request: Request) -> JSONProductRepository:
    return request.app.state.product_repository


def get_order_repository(request: Request) -> JSONOrderRepository:
    return request.app.state.order_repository


def get_session_repository(request: Request) -> JSONSessionRepository:
    return request.app.state.session_repository


def get_order_workflow_service(request: Request) -> OrderWorkflowService:
    return request.app.state.order_workflow_service
