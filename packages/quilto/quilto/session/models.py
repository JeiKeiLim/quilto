"""Session models for Quilto conversation tracking.

This module defines the Pydantic models used for session management:
- ConversationTurn: A single turn in a conversation
- SessionData: Complete session data for persistence
- SessionConfig: Configuration for session behavior
- SessionInfo: Summary info for session listing
"""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class ConversationTurn(BaseModel):
    """A single turn in a conversation.

    Attributes:
        role: Who produced this turn ("user" or "agent").
        content: The text content of the turn.
        timestamp: When this turn was created.
        metadata: Optional additional data (e.g., clarification_questions, parsed_data).
    """

    model_config = ConfigDict(strict=True)

    role: Literal["user", "agent"]
    content: str = Field(min_length=1)
    timestamp: datetime
    metadata: dict[str, Any] | None = None


class SessionData(BaseModel):
    """Complete session data for persistence.

    Attributes:
        session_id: Unique identifier for the session.
        created_at: When the session was created.
        updated_at: When the session was last modified.
        conversation: List of conversation turns in order.
    """

    model_config = ConfigDict(strict=True)

    session_id: str = Field(min_length=1)
    created_at: datetime
    updated_at: datetime
    conversation: list[ConversationTurn] = Field(
        default_factory=lambda: []
    )  # Empty list, type inferred from annotation


class SessionConfig(BaseModel):
    """Configuration for session behavior.

    Attributes:
        max_conversation_turns: Maximum turns to keep in storage (default 20).
            When exceeded, keeps first turn + last (N-1) turns.
        context_turns: Maximum turns to include in conversation context (default 6).
            When building context for agents, uses first turn + last (N-1) turns.
            Separate from storage pruning to allow fine-grained control.
    """

    model_config = ConfigDict(strict=True)

    max_conversation_turns: int = Field(default=20, ge=2)
    context_turns: int = Field(default=6, ge=2)


class SessionInfo(BaseModel):
    """Summary info for session listing (without full conversation).

    Attributes:
        session_id: Unique identifier for the session.
        created_at: When the session was created.
        updated_at: When the session was last modified.
        turn_count: Number of turns in the conversation.
    """

    model_config = ConfigDict(strict=True)

    session_id: str = Field(min_length=1)
    created_at: datetime
    updated_at: datetime
    turn_count: int = Field(default=0, ge=0)
