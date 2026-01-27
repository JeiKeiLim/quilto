"""SessionManager for creating and managing sessions.

This module provides the SessionManager class which is the main entry
point for session operations including creation, retrieval, listing,
and deletion.
"""

import uuid
from datetime import UTC, datetime

from quilto.session.models import SessionConfig, SessionData, SessionInfo
from quilto.session.session import Session
from quilto.session.stores.base import SessionStore


class SessionManager:
    """Manages session lifecycle operations.

    Provides methods for creating, retrieving, listing, and deleting
    sessions. Acts as the main entry point for session operations.

    Attributes:
        store: The backing SessionStore for persistence.
        config: Session configuration (shared across all sessions).

    Example:
        store = SQLiteSessionStore("./sessions.db")
        manager = SessionManager(store)

        # Create new session
        session = manager.create_session()

        # Retrieve existing session
        session = manager.get_session("abc-123")

        # List all sessions
        sessions = manager.list_sessions()

        # Delete session
        deleted = manager.delete_session("abc-123")
    """

    def __init__(
        self,
        store: SessionStore,
        config: SessionConfig | None = None,
    ) -> None:
        """Initialize session manager.

        Args:
            store: The backing store for session persistence.
            config: Session configuration. Defaults to SessionConfig()
                with max_conversation_turns=20.
        """
        self._store = store
        self._config = config if config is not None else SessionConfig()

    def create_session(self) -> Session:
        """Create a new session.

        Generates a unique UUID for the session, creates SessionData,
        persists it to the store, and returns a Session wrapper.

        Returns:
            A new Session ready for conversation turns.
        """
        now = datetime.now(UTC)
        session_data = SessionData(
            session_id=str(uuid.uuid4()),
            created_at=now,
            updated_at=now,
            conversation=[],
        )
        self._store.save(session_data)
        return Session(session_data, self._store, self._config)

    def get_session(self, session_id: str) -> Session | None:
        """Retrieve an existing session by ID.

        Args:
            session_id: The unique session identifier.

        Returns:
            Session if found, None if session doesn't exist.
        """
        session_data = self._store.load(session_id)
        if session_data is None:
            return None
        return Session(session_data, self._store, self._config)

    def list_sessions(self) -> list[SessionInfo]:
        """List all sessions with summary info.

        Returns:
            List of SessionInfo (does not load full conversations).
        """
        return self._store.list_all()

    def delete_session(self, session_id: str) -> bool:
        """Delete a session by ID.

        Args:
            session_id: The unique session identifier.

        Returns:
            True if session was deleted, False if not found.
        """
        return self._store.delete(session_id)
