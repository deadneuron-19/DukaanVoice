from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class ConversationMessage(BaseModel):
    role: str = Field(..., min_length=1)
    content: str = Field(..., min_length=1)
    created_at: datetime | None = None


class ConversationState(BaseModel):
    session_id: str = Field(..., min_length=3)
    current_state: str = Field(default="RECEIVED")
    draft_order_id: str | None = None
    pending_clarification: str | None = None
    conversation_history: list[ConversationMessage] = Field(default_factory=list)
    last_updated_at: datetime | None = None
    expires_at: datetime | None = None
