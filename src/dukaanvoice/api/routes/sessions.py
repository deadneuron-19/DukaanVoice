from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from dukaanvoice.api.dependencies import get_session_repository
from dukaanvoice.repositories.json_session_repository import JSONSessionRepository
from dukaanvoice.schemas.conversation import ConversationState

router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.get("/{session_id}", response_model=ConversationState)
def get_session(
    session_id: str,
    repository: JSONSessionRepository = Depends(get_session_repository),
) -> ConversationState:
    state = repository.get_session(session_id)
    if state is None:
        raise HTTPException(status_code=404, detail="Session not found.")
    return ConversationState.model_validate(state)
