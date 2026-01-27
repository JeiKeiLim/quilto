"""SQLite implementation of SessionStore.

This module provides persistent session storage using SQLite.
Sessions are stored with JSON-serialized conversation history.
"""

import json
import sqlite3
from datetime import datetime
from typing import Any

from quilto.session.models import ConversationTurn, SessionData, SessionInfo


class SQLiteSessionStore:
    """SQLite-backed session storage.

    Provides persistent storage for sessions using SQLite. Conversation
    history is stored as JSON in the conversation column.

    For in-memory databases (":memory:"), a single connection is maintained
    throughout the lifetime of the store to preserve data. For file-based
    databases, connections are opened and closed per operation.

    Attributes:
        db_path: Path to the SQLite database file. Use ":memory:" for
            in-memory testing.

    Example:
        # File-based storage
        store = SQLiteSessionStore("./sessions.db")

        # In-memory for testing
        store = SQLiteSessionStore(":memory:")
    """

    def __init__(self, db_path: str = "quilto_sessions.db") -> None:
        """Initialize SQLite session store.

        Creates the sessions table if it doesn't exist.

        Args:
            db_path: Path to SQLite database file. Defaults to
                "quilto_sessions.db" in current directory. Use ":memory:"
                for in-memory database (useful for testing).
        """
        self.db_path = db_path
        self._is_memory = db_path == ":memory:"
        # For in-memory databases, keep a persistent connection
        self._conn: sqlite3.Connection | None = None
        if self._is_memory:
            self._conn = sqlite3.connect(":memory:")
        self._init_schema()

    def _get_connection(self) -> sqlite3.Connection:
        """Get a database connection.

        For in-memory databases, returns the persistent connection.
        For file-based databases, creates a new connection.

        Returns:
            SQLite connection object.
        """
        if self._is_memory and self._conn is not None:
            return self._conn
        return sqlite3.connect(self.db_path)

    def _init_schema(self) -> None:
        """Create sessions table if it doesn't exist."""
        conn = self._get_connection()
        try:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    conversation TEXT NOT NULL
                )
            """)
            conn.commit()
        finally:
            if not self._is_memory:
                conn.close()

    def _serialize_conversation(self, conversation: list[ConversationTurn]) -> str:
        """Serialize conversation turns to JSON.

        Args:
            conversation: List of conversation turns.

        Returns:
            JSON string representation.
        """
        turns: list[dict[str, Any]] = []
        for turn in conversation:
            turn_dict: dict[str, Any] = {
                "role": turn.role,
                "content": turn.content,
                "timestamp": turn.timestamp.isoformat(),
            }
            if turn.metadata is not None:
                turn_dict["metadata"] = turn.metadata
            turns.append(turn_dict)
        return json.dumps(turns)

    def _deserialize_conversation(self, json_str: str) -> list[ConversationTurn]:
        """Deserialize conversation turns from JSON.

        Args:
            json_str: JSON string representation.

        Returns:
            List of ConversationTurn objects.
        """
        turns_data = json.loads(json_str)
        turns: list[ConversationTurn] = []
        for turn_dict in turns_data:
            turns.append(
                ConversationTurn(
                    role=turn_dict["role"],
                    content=turn_dict["content"],
                    timestamp=datetime.fromisoformat(turn_dict["timestamp"]),
                    metadata=turn_dict.get("metadata"),
                )
            )
        return turns

    def save(self, session_data: SessionData) -> None:
        """Save or update a session.

        Uses INSERT OR REPLACE for upsert semantics.

        Args:
            session_data: The complete session data to persist.
        """
        conn = self._get_connection()
        try:
            conn.execute(
                """
                INSERT OR REPLACE INTO sessions
                (session_id, created_at, updated_at, conversation)
                VALUES (?, ?, ?, ?)
                """,
                (
                    session_data.session_id,
                    session_data.created_at.isoformat(),
                    session_data.updated_at.isoformat(),
                    self._serialize_conversation(session_data.conversation),
                ),
            )
            conn.commit()
        finally:
            if not self._is_memory:
                conn.close()

    def load(self, session_id: str) -> SessionData | None:
        """Load a session by ID.

        Args:
            session_id: The unique session identifier.

        Returns:
            SessionData if found, None if session doesn't exist.
        """
        conn = self._get_connection()
        try:
            cursor = conn.execute(
                """
                SELECT session_id, created_at, updated_at, conversation
                FROM sessions
                WHERE session_id = ?
                """,
                (session_id,),
            )
            row = cursor.fetchone()
        finally:
            if not self._is_memory:
                conn.close()

        if row is None:
            return None

        return SessionData(
            session_id=row[0],
            created_at=datetime.fromisoformat(row[1]),
            updated_at=datetime.fromisoformat(row[2]),
            conversation=self._deserialize_conversation(row[3]),
        )

    def list_all(self) -> list[SessionInfo]:
        """List all sessions with summary info.

        Note: Currently parses conversation JSON to count turns. For large
        conversations, consider adding a turn_count column to the schema.

        Returns:
            List of SessionInfo ordered by updated_at descending.
        """
        conn = self._get_connection()
        try:
            cursor = conn.execute(
                """
                SELECT session_id, created_at, updated_at, conversation
                FROM sessions
                ORDER BY updated_at DESC
                """
            )
            rows = cursor.fetchall()
        finally:
            if not self._is_memory:
                conn.close()

        sessions: list[SessionInfo] = []
        for row in rows:
            # Parse conversation JSON to count turns
            conversation_data = json.loads(row[3])
            sessions.append(
                SessionInfo(
                    session_id=row[0],
                    created_at=datetime.fromisoformat(row[1]),
                    updated_at=datetime.fromisoformat(row[2]),
                    turn_count=len(conversation_data),
                )
            )
        return sessions

    def delete(self, session_id: str) -> bool:
        """Delete a session by ID.

        Args:
            session_id: The unique session identifier.

        Returns:
            True if session was deleted, False if not found.
        """
        conn = self._get_connection()
        try:
            cursor = conn.execute(
                "DELETE FROM sessions WHERE session_id = ?",
                (session_id,),
            )
            conn.commit()
            return cursor.rowcount > 0
        finally:
            if not self._is_memory:
                conn.close()
