from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException

from dukaanvoice.api.dependencies import get_order_repository, get_order_workflow_service
from dukaanvoice.repositories.json_order_repository import JSONOrderRepository
from dukaanvoice.schemas.order import (
    ClarificationRequest,
    OrderSchema,
    OrderWorkflowResponse,
    QuantityCorrectionRequest,
    TextOrderRequest,
)
from dukaanvoice.services.order_workflow_service import OrderWorkflowService

router = APIRouter(prefix="/orders", tags=["orders"])


@router.post("/text", response_model=OrderWorkflowResponse)
def create_text_order(
    body: TextOrderRequest,
    idempotency_key: Annotated[str, Header(alias="Idempotency-Key", min_length=8, max_length=128)],
    workflow: OrderWorkflowService = Depends(get_order_workflow_service),
) -> OrderWorkflowResponse:
    result = workflow.start_text_order(
        body.session_id,
        body.transcript,
        idempotency_key=idempotency_key,
        language=body.language,
    )
    return OrderWorkflowResponse.model_validate(result)


@router.post("/clarify", response_model=OrderWorkflowResponse)
def clarify_order(
    body: ClarificationRequest,
    workflow: OrderWorkflowService = Depends(get_order_workflow_service),
) -> OrderWorkflowResponse:
    result = workflow.clarify(
        body.session_id,
        selected_product_id=body.selected_product_id,
        quantity=body.quantity,
        clarification_text=body.clarification_text,
    )
    return OrderWorkflowResponse.model_validate(result)


@router.get("", response_model=list[OrderSchema])
def list_orders(
    repository: JSONOrderRepository = Depends(get_order_repository),
) -> list[OrderSchema]:
    return [OrderSchema.model_validate(order) for order in repository.list_orders()]


@router.get("/{order_id}", response_model=OrderSchema)
def get_order(
    order_id: str,
    repository: JSONOrderRepository = Depends(get_order_repository),
) -> OrderSchema:
    order = repository.get_by_id(order_id)
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found.")
    return OrderSchema.model_validate(order)


@router.post("/{order_id}/confirm", response_model=OrderSchema)
def confirm_order(
    order_id: str,
    idempotency_key: Annotated[str, Header(alias="Idempotency-Key", min_length=8, max_length=128)],
    workflow: OrderWorkflowService = Depends(get_order_workflow_service),
) -> OrderSchema:
    return OrderSchema.model_validate(workflow.confirm(order_id, idempotency_key))


@router.post("/{order_id}/cancel", response_model=OrderSchema)
def cancel_order(
    order_id: str,
    workflow: OrderWorkflowService = Depends(get_order_workflow_service),
) -> OrderSchema:
    return OrderSchema.model_validate(workflow.cancel(order_id))


@router.patch("/{order_id}/items/{product_id}", response_model=OrderSchema)
def update_order_item(
    order_id: str,
    product_id: str,
    body: QuantityCorrectionRequest,
    workflow: OrderWorkflowService = Depends(get_order_workflow_service),
) -> OrderSchema:
    return OrderSchema.model_validate(workflow.change_quantity(order_id, product_id, body.quantity))


@router.delete("/{order_id}/items/{product_id}", response_model=OrderSchema)
def remove_order_item(
    order_id: str,
    product_id: str,
    workflow: OrderWorkflowService = Depends(get_order_workflow_service),
) -> OrderSchema:
    return OrderSchema.model_validate(workflow.remove_item(order_id, product_id))
