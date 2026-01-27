"""Session class for managing conversation turns.

This module provides the Session class which wraps SessionData and
handles turn management including automatic pruning and persistence.
"""

from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any, Literal

from quilto.session.models import ConversationTurn, SessionConfig, SessionData

if TYPE_CHECKING:
    from quilto.session.stores.base import SessionStore


class Session:
    """Manages a single conversation session.

    Wraps SessionData and provides methods for adding turns,
    automatic pruning when max turns is exceeded, and auto-saving
    to the backing store.

    Attributes:
        data: The underlying SessionData.
        store: The SessionStore for persistence.
        config: Session configuration (max turns, etc.).

    Example:
        session = Session(data, store, config)
        session.add_turn("user", "Hello!")
        session.add_turn("agent", "Hi there!")
        history = session.get_history()
    """

    def __init__(
        self,
        data: SessionData,
        store: "SessionStore",
        config: SessionConfig,
    ) -> None:
        """Initialize session with data, store, and config.

        Args:
            data: The session data to manage.
            store: The backing store for persistence.
            config: Session configuration.
        """
        self._data = data
        self._store = store
        self._config = config

    @property
    def session_id(self) -> str:
        """Return the session ID."""
        return self._data.session_id

    def add_turn(
        self,
        role: Literal["user", "agent"],
        content: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Add a conversation turn.

        Creates a new ConversationTurn, enforces the max turns limit
        via pruning, updates the session timestamp, and auto-saves.

        Pruning strategy: When conversation exceeds max_conversation_turns,
        keeps [first_turn] + last (max_turns - 1) turns. This preserves
        the initial context while removing older middle turns.

        Args:
            role: Who produced this turn ("user" or "agent").
            content: The text content of the turn.
            metadata: Optional additional data (e.g., clarification questions).

        Raises:
            ValueError: If content is empty (enforced by ConversationTurn model).
        """
        turn = ConversationTurn(
            role=role,
            content=content,
            timestamp=datetime.now(UTC),
            metadata=metadata,
        )
        self._data.conversation.append(turn)

        # Prune if over limit: keep first turn + last (max - 1) turns
        max_turns = self._config.max_conversation_turns
        if len(self._data.conversation) > max_turns:
            first_turn = self._data.conversation[0]
            recent_turns = self._data.conversation[-(max_turns - 1) :]
            self._data.conversation = [first_turn] + recent_turns

        # Update timestamp and save
        self._data.updated_at = datetime.now(UTC)
        self._store.save(self._data)

    def get_history(self) -> list[ConversationTurn]:
        """Return the conversation history.

        Returns a copy of the conversation list to prevent external mutation
        that would bypass turn management (pruning, timestamps, auto-save).

        Returns:
            List of ConversationTurn objects in chronological order.
        """
        return list(self._data.conversation)
