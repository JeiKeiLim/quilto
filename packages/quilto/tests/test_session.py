"""Unit tests for Quilto session management.

Tests cover:
- Model validation (ConversationTurn, SessionData, SessionConfig, SessionInfo)
- SQLiteSessionStore CRUD operations
- Session turn management and pruning
- SessionManager lifecycle operations
"""

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError
from quilto import (
    ConversationTurn,
    Session,
    SessionConfig,
    SessionData,
    SessionInfo,
    SessionManager,
    SessionStore,
    SQLiteSessionStore,
)

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def store() -> SQLiteSessionStore:
    """In-memory SQLite store for testing."""
    return SQLiteSessionStore(":memory:")


@pytest.fixture
def config() -> SessionConfig:
    """Default session config for testing."""
    return SessionConfig()


@pytest.fixture
def manager(store: SQLiteSessionStore) -> SessionManager:
    """Session manager with in-memory store."""
    return SessionManager(store=store)


@pytest.fixture
def sample_turn() -> ConversationTurn:
    """Sample conversation turn for testing."""
    return ConversationTurn(
        role="user",
        content="Hello, how are you?",
        timestamp=datetime.now(UTC),
        metadata=None,
    )


@pytest.fixture
def sample_session_data() -> SessionData:
    """Sample session data for testing."""
    now = datetime.now(UTC)
    return SessionData(
        session_id="test-session-123",
        created_at=now,
        updated_at=now,
        conversation=[],
    )


# =============================================================================
# ConversationTurn Model Tests
# =============================================================================


class TestConversationTurn:
    """Tests for ConversationTurn model validation."""

    def test_valid_user_turn(self) -> None:
        """Valid user turn should be created successfully."""
        turn = ConversationTurn(
            role="user",
            content="Hello",
            timestamp=datetime.now(UTC),
        )
        assert turn.role == "user"
        assert turn.content == "Hello"
        assert turn.metadata is None

    def test_valid_agent_turn(self) -> None:
        """Valid agent turn should be created successfully."""
        turn = ConversationTurn(
            role="agent",
            content="Hi there!",
            timestamp=datetime.now(UTC),
        )
        assert turn.role == "agent"

    def test_empty_content_rejected(self) -> None:
        """Empty content string should be rejected."""
        with pytest.raises(ValidationError) as exc_info:
            ConversationTurn(
                role="user",
                content="",
                timestamp=datetime.now(UTC),
            )
        assert "String should have at least 1 character" in str(exc_info.value)

    def test_invalid_role_rejected(self) -> None:
        """Invalid role should be rejected."""
        with pytest.raises(ValidationError):
            ConversationTurn(
                role="system",  # type: ignore[arg-type]
                content="Hello",
                timestamp=datetime.now(UTC),
            )

    def test_metadata_storage(self) -> None:
        """Metadata dict should be stored correctly."""
        metadata = {"clarification_questions": [{"question": "What time?", "options": ["Morning", "Evening"]}]}
        turn = ConversationTurn(
            role="agent",
            content="I have a question.",
            timestamp=datetime.now(UTC),
            metadata=metadata,
        )
        assert turn.metadata == metadata
        assert turn.metadata is not None
        assert turn.metadata["clarification_questions"][0]["question"] == "What time?"


# =============================================================================
# SessionData Model Tests
# =============================================================================


class TestSessionData:
    """Tests for SessionData model validation."""

    def test_valid_session_data(self) -> None:
        """Valid session data should be created successfully."""
        now = datetime.now(UTC)
        data = SessionData(
            session_id="abc-123",
            created_at=now,
            updated_at=now,
        )
        assert data.session_id == "abc-123"
        assert data.conversation == []

    def test_empty_session_id_rejected(self) -> None:
        """Empty session_id should be rejected."""
        now = datetime.now(UTC)
        with pytest.raises(ValidationError) as exc_info:
            SessionData(
                session_id="",
                created_at=now,
                updated_at=now,
            )
        assert "String should have at least 1 character" in str(exc_info.value)

    def test_default_list_isolation(self) -> None:
        """Two SessionData instances should not share conversation lists."""
        now = datetime.now(UTC)
        data1 = SessionData(session_id="a", created_at=now, updated_at=now)
        data2 = SessionData(session_id="b", created_at=now, updated_at=now)

        # Add turn to first instance
        data1.conversation.append(
            ConversationTurn(
                role="user",
                content="Hello",
                timestamp=now,
            )
        )

        # Second instance should be unaffected
        assert len(data1.conversation) == 1
        assert len(data2.conversation) == 0


# =============================================================================
# SessionConfig Model Tests
# =============================================================================


class TestSessionConfig:
    """Tests for SessionConfig model validation."""

    def test_default_max_turns(self) -> None:
        """Default max_conversation_turns should be 20."""
        config = SessionConfig()
        assert config.max_conversation_turns == 20

    def test_custom_max_turns(self) -> None:
        """Custom max_conversation_turns should be accepted."""
        config = SessionConfig(max_conversation_turns=50)
        assert config.max_conversation_turns == 50

    def test_minimum_max_turns_boundary(self) -> None:
        """max_conversation_turns=2 should be accepted (minimum valid)."""
        config = SessionConfig(max_conversation_turns=2)
        assert config.max_conversation_turns == 2

    def test_max_turns_below_minimum_rejected(self) -> None:
        """max_conversation_turns < 2 should be rejected."""
        with pytest.raises(ValidationError) as exc_info:
            SessionConfig(max_conversation_turns=1)
        assert "greater than or equal to 2" in str(exc_info.value)


# =============================================================================
# SessionInfo Model Tests
# =============================================================================


class TestSessionInfo:
    """Tests for SessionInfo model validation."""

    def test_valid_session_info(self) -> None:
        """Valid session info should be created successfully."""
        now = datetime.now(UTC)
        info = SessionInfo(
            session_id="abc-123",
            created_at=now,
            updated_at=now,
            turn_count=5,
        )
        assert info.session_id == "abc-123"
        assert info.turn_count == 5

    def test_empty_session_id_rejected(self) -> None:
        """Empty session_id should be rejected."""
        now = datetime.now(UTC)
        with pytest.raises(ValidationError) as exc_info:
            SessionInfo(
                session_id="",
                created_at=now,
                updated_at=now,
            )
        assert "String should have at least 1 character" in str(exc_info.value)

    def test_default_turn_count(self) -> None:
        """Default turn_count should be 0."""
        now = datetime.now(UTC)
        info = SessionInfo(
            session_id="abc",
            created_at=now,
            updated_at=now,
        )
        assert info.turn_count == 0


# =============================================================================
# SQLiteSessionStore Tests
# =============================================================================


class TestSQLiteSessionStore:
    """Tests for SQLiteSessionStore CRUD operations."""

    def test_save_and_load_roundtrip(self, store: SQLiteSessionStore) -> None:
        """Save and load should preserve session data."""
        now = datetime.now(UTC)
        original = SessionData(
            session_id="test-123",
            created_at=now,
            updated_at=now,
            conversation=[
                ConversationTurn(
                    role="user",
                    content="Hello",
                    timestamp=now,
                )
            ],
        )

        store.save(original)
        loaded = store.load("test-123")

        assert loaded is not None
        assert loaded.session_id == original.session_id
        assert len(loaded.conversation) == 1
        assert loaded.conversation[0].content == "Hello"

    def test_load_nonexistent_returns_none(self, store: SQLiteSessionStore) -> None:
        """Loading non-existent session should return None."""
        result = store.load("does-not-exist")
        assert result is None

    def test_save_upsert(self, store: SQLiteSessionStore) -> None:
        """Save should update existing session (upsert)."""
        now = datetime.now(UTC)
        data = SessionData(
            session_id="test-123",
            created_at=now,
            updated_at=now,
        )

        store.save(data)

        # Update with new content
        data.conversation.append(ConversationTurn(role="user", content="Hello", timestamp=now))
        store.save(data)

        loaded = store.load("test-123")
        assert loaded is not None
        assert len(loaded.conversation) == 1

    def test_list_all_returns_correct_info(self, store: SQLiteSessionStore) -> None:
        """list_all should return SessionInfo for all sessions."""
        now = datetime.now(UTC)

        # Create two sessions with different turn counts
        store.save(
            SessionData(
                session_id="session-1",
                created_at=now,
                updated_at=now,
                conversation=[
                    ConversationTurn(role="user", content="Hi", timestamp=now),
                ],
            )
        )
        store.save(
            SessionData(
                session_id="session-2",
                created_at=now,
                updated_at=now,
                conversation=[
                    ConversationTurn(role="user", content="A", timestamp=now),
                    ConversationTurn(role="agent", content="B", timestamp=now),
                ],
            )
        )

        sessions = store.list_all()

        assert len(sessions) == 2
        # Find each session by ID
        session_map = {s.session_id: s for s in sessions}
        assert session_map["session-1"].turn_count == 1
        assert session_map["session-2"].turn_count == 2

    def test_delete_existing_returns_true(self, store: SQLiteSessionStore) -> None:
        """Deleting existing session should return True."""
        now = datetime.now(UTC)
        store.save(
            SessionData(
                session_id="to-delete",
                created_at=now,
                updated_at=now,
            )
        )

        result = store.delete("to-delete")

        assert result is True
        assert store.load("to-delete") is None

    def test_delete_nonexistent_returns_false(self, store: SQLiteSessionStore) -> None:
        """Deleting non-existent session should return False."""
        result = store.delete("does-not-exist")
        assert result is False

    def test_isinstance_session_store(self, store: SQLiteSessionStore) -> None:
        """SQLiteSessionStore should be recognized as SessionStore."""
        assert isinstance(store, SessionStore)

    def test_metadata_roundtrip(self, store: SQLiteSessionStore) -> None:
        """Metadata should survive save/load roundtrip."""
        now = datetime.now(UTC)
        metadata = {
            "clarification_questions": [{"question": "Morning or evening?", "options": ["AM", "PM"]}],
            "confidence": 0.95,
        }

        store.save(
            SessionData(
                session_id="meta-test",
                created_at=now,
                updated_at=now,
                conversation=[
                    ConversationTurn(
                        role="agent",
                        content="When?",
                        timestamp=now,
                        metadata=metadata,
                    )
                ],
            )
        )

        loaded = store.load("meta-test")
        assert loaded is not None
        assert loaded.conversation[0].metadata == metadata


# =============================================================================
# Session Class Tests
# =============================================================================


class TestSession:
    """Tests for Session class turn management."""

    def test_add_turn_creates_turn(
        self,
        store: SQLiteSessionStore,
        config: SessionConfig,
        sample_session_data: SessionData,
    ) -> None:
        """add_turn should create and persist turn."""
        store.save(sample_session_data)
        session = Session(sample_session_data, store, config)

        session.add_turn("user", "Hello!")

        assert len(session.get_history()) == 1
        assert session.get_history()[0].content == "Hello!"
        assert session.get_history()[0].role == "user"

        # Verify persisted
        loaded = store.load(session.session_id)
        assert loaded is not None
        assert len(loaded.conversation) == 1

    def test_add_turn_rejects_empty_content(
        self,
        store: SQLiteSessionStore,
        config: SessionConfig,
        sample_session_data: SessionData,
    ) -> None:
        """add_turn should reject empty content string."""
        store.save(sample_session_data)
        session = Session(sample_session_data, store, config)

        with pytest.raises(ValidationError) as exc_info:
            session.add_turn("user", "")
        assert "String should have at least 1 character" in str(exc_info.value)

    def test_session_id_property(
        self,
        store: SQLiteSessionStore,
        config: SessionConfig,
        sample_session_data: SessionData,
    ) -> None:
        """session_id property should return correct ID."""
        session = Session(sample_session_data, store, config)
        assert session.session_id == "test-session-123"

    def test_turn_pruning_keeps_first_and_recent(
        self,
        store: SQLiteSessionStore,
    ) -> None:
        """Turn pruning should keep first turn + last (max-1) turns."""
        config = SessionConfig(max_conversation_turns=5)
        now = datetime.now(UTC)
        data = SessionData(
            session_id="prune-test",
            created_at=now,
            updated_at=now,
        )
        store.save(data)
        session = Session(data, store, config)

        # Add 7 turns (exceeds max of 5)
        for i in range(7):
            session.add_turn("user", f"Turn {i}")

        history = session.get_history()

        # Should have 5 turns: first + last 4
        assert len(history) == 5
        assert history[0].content == "Turn 0"  # First turn preserved
        assert history[1].content == "Turn 3"  # Recent starts here
        assert history[2].content == "Turn 4"
        assert history[3].content == "Turn 5"
        assert history[4].content == "Turn 6"

    def test_updated_at_changes_on_add_turn(
        self,
        store: SQLiteSessionStore,
        config: SessionConfig,
    ) -> None:
        """updated_at should be updated when turn is added."""
        now = datetime.now(UTC)
        data = SessionData(
            session_id="update-test",
            created_at=now,
            updated_at=now,
        )
        store.save(data)
        session = Session(data, store, config)
        original_updated = data.updated_at

        # Add turn
        session.add_turn("user", "Hello")

        # Reload and check updated_at changed
        loaded = store.load("update-test")
        assert loaded is not None
        assert loaded.updated_at >= original_updated

    def test_add_turn_with_metadata(
        self,
        store: SQLiteSessionStore,
        config: SessionConfig,
        sample_session_data: SessionData,
    ) -> None:
        """add_turn should store metadata correctly."""
        store.save(sample_session_data)
        session = Session(sample_session_data, store, config)

        metadata = {"confidence": 0.9, "model": "gpt-4"}
        session.add_turn("agent", "Response", metadata=metadata)

        assert session.get_history()[0].metadata == metadata

    def test_get_history_returns_copy(
        self,
        store: SQLiteSessionStore,
        config: SessionConfig,
        sample_session_data: SessionData,
    ) -> None:
        """get_history should return a copy to prevent external mutation."""
        store.save(sample_session_data)
        session = Session(sample_session_data, store, config)
        session.add_turn("user", "Hello")

        # Get history and mutate the returned list
        history = session.get_history()
        original_len = len(history)
        history.clear()

        # Internal state should be unaffected
        assert len(session.get_history()) == original_len

    def test_complex_nested_metadata_survives_workflow(
        self,
        store: SQLiteSessionStore,
    ) -> None:
        """Complex nested metadata should survive add_turn → prune → reload."""
        config = SessionConfig(max_conversation_turns=3)
        now = datetime.now(UTC)
        data = SessionData(
            session_id="metadata-workflow-test",
            created_at=now,
            updated_at=now,
        )
        store.save(data)
        session = Session(data, store, config)

        # Complex nested metadata
        complex_metadata = {
            "clarification_questions": [
                {
                    "question": "When did you exercise?",
                    "options": ["Morning", "Afternoon", "Evening"],
                    "selected": None,
                },
                {
                    "question": "How intense was it?",
                    "options": [1, 2, 3, 4, 5],
                    "selected": 3,
                },
            ],
            "parsed_data": {
                "activity": "running",
                "duration_minutes": 30,
                "nested": {"deeply": {"nested": "value"}},
            },
            "flags": [True, False, True],
        }

        # Add turns to trigger pruning - metadata on last turn survives
        session.add_turn("user", "Turn 0")
        session.add_turn("agent", "Turn 1")
        session.add_turn("user", "Turn 2")
        session.add_turn("agent", "Turn 3", metadata=complex_metadata)  # Pruning + metadata

        # Reload from store
        reloaded = store.load("metadata-workflow-test")
        assert reloaded is not None

        # Find the turn with metadata (should be preserved after pruning)
        metadata_turn = next((t for t in reloaded.conversation if t.metadata is not None), None)
        assert metadata_turn is not None
        assert metadata_turn.metadata == complex_metadata


# =============================================================================
# SessionManager Tests
# =============================================================================


class TestSessionManager:
    """Tests for SessionManager lifecycle operations."""

    def test_create_session_generates_uuid(self, manager: SessionManager) -> None:
        """create_session should generate unique UUID."""
        session1 = manager.create_session()
        session2 = manager.create_session()

        assert session1.session_id != session2.session_id
        # UUID format check (basic)
        assert len(session1.session_id) == 36
        assert session1.session_id.count("-") == 4

    def test_create_session_persists(self, manager: SessionManager, store: SQLiteSessionStore) -> None:
        """create_session should persist session to store."""
        session = manager.create_session()

        loaded = store.load(session.session_id)
        assert loaded is not None
        assert loaded.session_id == session.session_id

    def test_get_session_loads_existing(self, manager: SessionManager) -> None:
        """get_session should load existing session."""
        session = manager.create_session()
        session.add_turn("user", "Hello")

        loaded = manager.get_session(session.session_id)

        assert loaded is not None
        assert loaded.session_id == session.session_id
        assert len(loaded.get_history()) == 1

    def test_get_session_returns_none_for_missing(self, manager: SessionManager) -> None:
        """get_session should return None for non-existent ID."""
        result = manager.get_session("does-not-exist")
        assert result is None

    def test_list_sessions_returns_all(self, manager: SessionManager) -> None:
        """list_sessions should return all sessions."""
        manager.create_session()
        manager.create_session()
        manager.create_session()

        sessions = manager.list_sessions()

        assert len(sessions) == 3

    def test_delete_session_removes_session(self, manager: SessionManager) -> None:
        """delete_session should remove session from store."""
        session = manager.create_session()
        session_id = session.session_id

        result = manager.delete_session(session_id)

        assert result is True
        assert manager.get_session(session_id) is None

    def test_delete_session_nonexistent_returns_false(self, manager: SessionManager) -> None:
        """delete_session should return False for non-existent ID."""
        result = manager.delete_session("does-not-exist")
        assert result is False

    def test_custom_config(self, store: SQLiteSessionStore) -> None:
        """SessionManager should use custom config."""
        config = SessionConfig(max_conversation_turns=3)
        manager = SessionManager(store=store, config=config)

        session = manager.create_session()

        # Add 5 turns - should prune to 3
        for i in range(5):
            session.add_turn("user", f"Turn {i}")

        assert len(session.get_history()) == 3


# =============================================================================
# Integration Tests
# =============================================================================


class TestIntegration:
    """Integration tests for session workflow."""

    def test_full_conversation_workflow(self, manager: SessionManager) -> None:
        """Test complete conversation workflow."""
        # Create session
        session = manager.create_session()
        session_id = session.session_id

        # Add conversation turns
        session.add_turn("user", "What's the weather?")
        session.add_turn("agent", "I don't have weather data.")
        session.add_turn("user", "Okay, thanks")
        session.add_turn("agent", "You're welcome!")

        # Retrieve in new session object
        reloaded = manager.get_session(session_id)
        assert reloaded is not None

        history = reloaded.get_history()
        assert len(history) == 4
        assert history[0].role == "user"
        assert history[1].role == "agent"

        # List shows session
        sessions = manager.list_sessions()
        assert any(s.session_id == session_id for s in sessions)
        session_info = next(s for s in sessions if s.session_id == session_id)
        assert session_info.turn_count == 4

        # Delete session
        assert manager.delete_session(session_id) is True
        assert manager.get_session(session_id) is None

    def test_import_verification(self) -> None:
        """Verify all session classes can be imported from quilto."""
        from quilto import (
            ConversationTurn,
            Session,
            SessionConfig,
            SessionData,
            SessionInfo,
            SessionManager,
            SessionStore,
            SQLiteSessionStore,
        )

        # Verify classes are accessible
        assert ConversationTurn is not None
        assert Session is not None
        assert SessionConfig is not None
        assert SessionData is not None
        assert SessionInfo is not None
        assert SessionManager is not None
        assert SessionStore is not None
        assert SQLiteSessionStore is not None
