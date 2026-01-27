"""SessionStore protocol for session persistence backends.

This module defines the abstract protocol that all session storage
implementations must follow. The default implementation is SQLiteSessionStore.
"""

from typing import Protocol, runtime_checkable

from quilto.session.models import SessionData, SessionInfo


@runtime_checkable
class SessionStore(Protocol):
    """Protocol for session persistence backends.

    Implementations must provide save, load, list_all, and delete operations.
    The default implementation is SQLiteSessionStore.

    The @runtime_checkable decorator enables isinstance() checks against
    this protocol, which is required for validation in SessionManager.

    Example:
        store = SQLiteSessionStore("./sessions.db")
        store.save(session_data)
        loaded = store.load(session_id)
    """

    def save(self, session_data: SessionData) -> None:
        """Save or update a session.

        Uses upsert semantics - creates if not exists, updates if exists.

        Args:
            session_data: The complete session data to persist.
        """
        ...

    def load(self, session_id: str) -> SessionData | None:
        """Load a session by ID.

        Args:
            session_id: The unique session identifier.

        Returns:
            SessionData if found, None if session doesn't exist.
        """
        ...

    def list_all(self) -> list[SessionInfo]:
        """List all sessions with summary info.

        Returns session metadata without loading full conversations
        for efficiency when displaying session lists.

        Returns:
            List of SessionInfo (does not load full conversations).
        """
        ...

    def delete(self, session_id: str) -> bool:
        """Delete a session by ID.

        Args:
            session_id: The unique session identifier.

        Returns:
            True if session was deleted, False if not found.
        """
        ...
