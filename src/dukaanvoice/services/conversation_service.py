from __future__ import annotations

from dukaanvoice.schemas.conversation import ConversationState


class ConversationService:
    """Coordinates workflow state transitions for ordering sessions."""

    def create_session(self, session_id: str) -> ConversationState:
        return ConversationState(session_id=session_id, current_state="RECEIVED")

    def update_state(self, state: ConversationState, next_state: str) -> ConversationState:
        state.current_state = next_state
        return state
