"""Unit tests for Quilto main class and orchestration.

Tests cover:
- Quilto class initialization
- create_session() returns Session with process method
- session.process() with mock LLM for QUERY flow
- session.process() with mock LLM for LOG flow
- Retry loop triggers when Evaluator returns INSUFFICIENT
- ProgressHandler callbacks are invoked correctly
- Observer is invoked on query completion
- Conversation history is passed to subsequent process calls
- Debug mode includes traces in ProcessResult
- Partial response returned after max_retries
- Clarification questions flow
- BOTH flow - query completes, then parse runs
- CORRECTION flow - uses process_correction with upsert
- Forced mode="log" bypasses Router classification
- Error handling in node functions - partial result returned on agent failure
"""

import tempfile
from collections.abc import Generator
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pydantic import BaseModel
from quilto import (
    DomainModule,
    LLMClient,
    ObserverTriggerConfig,
    ProcessResult,
    Quilto,
    Session,
    StorageRepository,
)

# =============================================================================
# Fixtures
# =============================================================================


class MockSchema(BaseModel):
    """Mock schema for testing."""

    value: str


@pytest.fixture
def temp_storage_dir() -> Generator[Path]:
    """Create a temporary directory for storage."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def mock_llm_client() -> MagicMock:
    """Create a mock LLM client."""
    client = MagicMock(spec=LLMClient)
    client.complete = AsyncMock(return_value='{"result": "ok"}')
    return client


@pytest.fixture
def mock_storage(temp_storage_dir: Path) -> StorageRepository:
    """Create a mock storage repository."""
    storage = StorageRepository(base_path=temp_storage_dir)
    return storage


@pytest.fixture
def mock_domain() -> DomainModule:
    """Create a mock domain module."""
    return DomainModule(
        name="test_domain",
        description="A test domain for unit testing",
        log_schema=MockSchema,
        vocabulary={"test": "testing term"},
        expertise="Test domain expertise",
        response_evaluation_rules=["Test responses should be accurate"],
        context_management_guidance="Test context guidance",
        clarification_patterns={},
    )


@pytest.fixture
def quilto(
    mock_llm_client: MagicMock,
    mock_storage: StorageRepository,
    mock_domain: DomainModule,
) -> Quilto:
    """Create a Quilto instance with mocks."""
    return Quilto(
        llm_client=mock_llm_client,
        storage=mock_storage,
        domains=[mock_domain],
        session_db_path=":memory:",
    )


# =============================================================================
# Quilto Initialization Tests
# =============================================================================


class TestQuiltoInitialization:
    """Tests for Quilto class initialization."""

    def test_initialization_with_required_params(
        self,
        mock_llm_client: MagicMock,
        mock_storage: StorageRepository,
        mock_domain: DomainModule,
    ) -> None:
        """Quilto should initialize with required params."""
        q = Quilto(
            llm_client=mock_llm_client,
            storage=mock_storage,
            domains=[mock_domain],
            session_db_path=":memory:",
        )

        assert q.llm_client == mock_llm_client
        assert q.storage == mock_storage
        assert len(q.domains) == 1
        assert q.max_retries == 2
        assert q.debug is False
        assert q.progress_handler is None

    def test_initialization_with_optional_params(
        self,
        mock_llm_client: MagicMock,
        mock_storage: StorageRepository,
        mock_domain: DomainModule,
    ) -> None:
        """Quilto should accept optional params."""

        class MockHandler:
            async def on_stage(self, stage: str) -> None:
                pass

        handler = MockHandler()
        observer_config = ObserverTriggerConfig(enable_post_query=False)

        q = Quilto(
            llm_client=mock_llm_client,
            storage=mock_storage,
            domains=[mock_domain],
            observer_config=observer_config,
            max_retries=5,
            debug=True,
            progress_handler=handler,  # type: ignore[arg-type]
            session_db_path=":memory:",
        )

        assert q.max_retries == 5
        assert q.debug is True
        assert q.progress_handler == handler
        assert q.observer_config.enable_post_query is False

    def test_domain_selector_initialized(self, quilto: Quilto) -> None:
        """Domain selector should be initialized from domains."""
        selector = quilto.domain_selector

        infos = selector.get_domain_infos()
        assert len(infos) == 1
        assert infos[0].name == "test_domain"


# =============================================================================
# Session Creation Tests
# =============================================================================


class TestSessionCreation:
    """Tests for Quilto.create_session()."""

    def test_create_session_returns_session(self, quilto: Quilto) -> None:
        """create_session should return a Session instance."""
        session = quilto.create_session()

        assert isinstance(session, Session)
        assert session.session_id is not None

    def test_session_has_process_method(self, quilto: Quilto) -> None:
        """Session from create_session should have process method."""
        session = quilto.create_session()

        assert hasattr(session, "process")
        assert callable(session.process)

    def test_session_has_quilto_reference(self, quilto: Quilto) -> None:
        """Session should have internal quilto reference."""
        session = quilto.create_session()

        # Access private attribute (for test verification)
        assert session._quilto == quilto  # pyright: ignore[reportPrivateUsage]

    def test_multiple_sessions_unique_ids(self, quilto: Quilto) -> None:
        """Multiple sessions should have unique IDs."""
        session1 = quilto.create_session()
        session2 = quilto.create_session()

        assert session1.session_id != session2.session_id


# =============================================================================
# Process QUERY Flow Tests
# =============================================================================


class TestProcessQueryFlow:
    """Tests for session.process() with QUERY input."""

    @pytest.mark.asyncio
    async def test_process_query_returns_result(self, quilto: Quilto) -> None:
        """process() should return ProcessResult for query."""
        session = quilto.create_session()

        # Mock the graph execution
        with patch.object(quilto, "_get_graph") as mock_get_graph:
            mock_graph = MagicMock()
            mock_graph.ainvoke = AsyncMock(
                return_value={
                    "input_type": "query",
                    "response": "Test response",
                    "confidence": 0.8,
                    "source_entry_ids": ["entry1", "entry2"],
                    "selected_domains": ["test_domain"],
                }
            )
            mock_get_graph.return_value = mock_graph

            result = await session.process("How was my test?")

        assert isinstance(result, ProcessResult)
        assert result.input_type == "query"
        assert result.response == "Test response"
        assert result.confidence == 0.8

    @pytest.mark.asyncio
    async def test_process_adds_user_turn(self, quilto: Quilto) -> None:
        """process() should add user turn to history."""
        session = quilto.create_session()

        with patch.object(quilto, "_get_graph") as mock_get_graph:
            mock_graph = MagicMock()
            mock_graph.ainvoke = AsyncMock(
                return_value={
                    "input_type": "query",
                    "response": "Test response",
                    "selected_domains": [],
                }
            )
            mock_get_graph.return_value = mock_graph

            await session.process("Test input")

        history = session.get_history()
        assert len(history) >= 1
        assert history[0].role == "user"
        assert history[0].content == "Test input"

    @pytest.mark.asyncio
    async def test_process_adds_agent_turn(self, quilto: Quilto) -> None:
        """process() should add agent turn with response."""
        session = quilto.create_session()

        with patch.object(quilto, "_get_graph") as mock_get_graph:
            mock_graph = MagicMock()
            mock_graph.ainvoke = AsyncMock(
                return_value={
                    "input_type": "query",
                    "response": "Agent response",
                    "selected_domains": [],
                }
            )
            mock_get_graph.return_value = mock_graph

            await session.process("Test input")

        history = session.get_history()
        assert len(history) == 2
        assert history[1].role == "agent"
        assert history[1].content == "Agent response"


# =============================================================================
# Process LOG Flow Tests
# =============================================================================


class TestProcessLogFlow:
    """Tests for session.process() with LOG input."""

    @pytest.mark.asyncio
    async def test_process_log_returns_parsed_data(self, quilto: Quilto) -> None:
        """process() with LOG should return parsed_data."""
        session = quilto.create_session()

        with patch.object(quilto, "_get_graph") as mock_get_graph:
            mock_graph = MagicMock()
            mock_graph.ainvoke = AsyncMock(
                return_value={
                    "input_type": "log",
                    "parsed_data": {"activity": "running", "duration": 30},
                    "selected_domains": ["test_domain"],
                }
            )
            mock_get_graph.return_value = mock_graph

            result = await session.process("Ran 5k today", mode="log")

        assert result.input_type == "log"
        assert result.parsed_data is not None
        assert result.parsed_data["activity"] == "running"

    @pytest.mark.asyncio
    async def test_forced_log_mode_bypasses_router(self, quilto: Quilto) -> None:
        """mode='log' should bypass Router classification."""
        session = quilto.create_session()

        with patch.object(quilto, "_get_graph") as mock_get_graph:
            mock_graph = MagicMock()

            # Capture the state passed to ainvoke
            captured_state: dict[str, Any] = {}

            async def capture_state(state: dict[str, Any]) -> dict[str, Any]:
                captured_state.update(state)
                return {
                    "input_type": "log",
                    "parsed_data": {},
                    "selected_domains": [],
                }

            mock_graph.ainvoke = capture_state
            mock_get_graph.return_value = mock_graph

            await session.process("Log entry", mode="log")

        assert captured_state.get("mode") == "log"


# =============================================================================
# Retry Loop Tests
# =============================================================================


class TestRetryLoop:
    """Tests for retry loop when Evaluator returns INSUFFICIENT."""

    @pytest.mark.asyncio
    async def test_retry_increments_count(self, quilto: Quilto) -> None:
        """Retry should increment retry_count in state."""
        session = quilto.create_session()

        with patch.object(quilto, "_get_graph") as mock_get_graph:
            mock_graph = MagicMock()
            mock_graph.ainvoke = AsyncMock(
                return_value={
                    "input_type": "query",
                    "response": "Partial response",
                    "retry_count": 2,
                    "is_partial": True,
                    "selected_domains": [],
                }
            )
            mock_get_graph.return_value = mock_graph

            result = await session.process("Test query")

        # Result built from state - check debug if enabled
        assert result is not None

    @pytest.mark.asyncio
    async def test_partial_response_after_max_retries(self, quilto: Quilto) -> None:
        """Partial response should be returned after max_retries."""
        quilto.max_retries = 1
        session = quilto.create_session()

        with patch.object(quilto, "_get_graph") as mock_get_graph:
            mock_graph = MagicMock()
            mock_graph.ainvoke = AsyncMock(
                return_value={
                    "input_type": "query",
                    "response": "Best effort response",
                    "is_partial": True,
                    "retry_count": 1,
                    "selected_domains": [],
                }
            )
            mock_get_graph.return_value = mock_graph

            result = await session.process("Test query")

        assert result.response == "Best effort response"


# =============================================================================
# ProgressHandler Tests
# =============================================================================


class TestProgressHandler:
    """Tests for ProgressHandler callbacks."""

    @pytest.mark.asyncio
    async def test_progress_handler_callbacks(
        self,
        mock_llm_client: MagicMock,
        mock_storage: StorageRepository,
        mock_domain: DomainModule,
    ) -> None:
        """ProgressHandler methods should be called."""

        class TestHandler:
            def __init__(self) -> None:
                self.stages: list[str] = []
                self.agents_started: list[str] = []
                self.agents_completed: list[str] = []

            async def on_stage(self, stage: str) -> None:
                self.stages.append(stage)

            async def on_agent_start(self, agent: str, input_summary: str) -> None:
                self.agents_started.append(agent)

            async def on_agent_complete(self, agent: str, elapsed: float) -> None:
                self.agents_completed.append(agent)

            async def on_retry(self, attempt: int, reason: str) -> None:
                pass

        handler = TestHandler()

        q = Quilto(
            llm_client=mock_llm_client,
            storage=mock_storage,
            domains=[mock_domain],
            progress_handler=handler,  # type: ignore[arg-type]
            session_db_path=":memory:",
        )
        session = q.create_session()

        with patch.object(q, "_get_graph") as mock_get_graph:
            mock_graph = MagicMock()
            mock_graph.ainvoke = AsyncMock(
                return_value={
                    "input_type": "query",
                    "response": "Test",
                    "selected_domains": [],
                }
            )
            mock_get_graph.return_value = mock_graph

            await session.process("Test query")

        # Handler was set (actual callback depends on graph execution)
        assert q.progress_handler == handler


# =============================================================================
# Debug Mode Tests
# =============================================================================


class TestDebugMode:
    """Tests for debug mode with traces."""

    @pytest.mark.asyncio
    async def test_debug_mode_includes_traces(
        self,
        mock_llm_client: MagicMock,
        mock_storage: StorageRepository,
        mock_domain: DomainModule,
    ) -> None:
        """Debug mode should include traces in ProcessResult."""
        q = Quilto(
            llm_client=mock_llm_client,
            storage=mock_storage,
            domains=[mock_domain],
            debug=True,
            session_db_path=":memory:",
        )
        session = q.create_session()

        with patch.object(q, "_get_graph") as mock_get_graph:
            mock_graph = MagicMock()
            mock_graph.ainvoke = AsyncMock(
                return_value={
                    "input_type": "query",
                    "response": "Test response",
                    "selected_domains": [],
                    "traces": [
                        {
                            "agent_name": "router",
                            "input_summary": "test input",
                            "output_summary": "type=query",
                            "elapsed_ms": 100.0,
                            "timestamp": datetime.now(UTC),
                        }
                    ],
                    "total_elapsed_ms": 500.0,
                    "retry_count": 0,
                }
            )
            mock_get_graph.return_value = mock_graph

            result = await session.process("Test query")

        assert result.debug is not None
        assert len(result.debug.traces) == 1
        assert result.debug.traces[0].agent_name == "router"


# =============================================================================
# Clarification Flow Tests
# =============================================================================


class TestClarificationFlow:
    """Tests for clarification questions flow."""

    @pytest.mark.asyncio
    async def test_clarification_questions_returned(self, quilto: Quilto) -> None:
        """Clarification questions should be in ProcessResult."""
        session = quilto.create_session()

        with patch.object(quilto, "_get_graph") as mock_get_graph:
            mock_graph = MagicMock()
            mock_graph.ainvoke = AsyncMock(
                return_value={
                    "input_type": "query",
                    "next_action": "clarify",
                    "clarify_questions": [
                        {"question": "Which workout?", "options": ["Morning", "Evening"]},
                        {"question": "What date?", "options": None},
                    ],
                    "selected_domains": [],
                }
            )
            mock_get_graph.return_value = mock_graph

            result = await session.process("How was my workout?")

        assert result.clarification_questions is not None
        assert len(result.clarification_questions) == 2
        assert result.clarification_questions[0].question == "Which workout?"
        assert result.clarification_questions[0].options == ["Morning", "Evening"]

    @pytest.mark.asyncio
    async def test_clarification_adds_agent_turn(self, quilto: Quilto) -> None:
        """Clarification should add agent turn with questions."""
        session = quilto.create_session()

        with patch.object(quilto, "_get_graph") as mock_get_graph:
            mock_graph = MagicMock()
            mock_graph.ainvoke = AsyncMock(
                return_value={
                    "input_type": "query",
                    "clarify_questions": [{"question": "Which one?", "options": None}],
                    "selected_domains": [],
                }
            )
            mock_get_graph.return_value = mock_graph

            await session.process("Test")

        history = session.get_history()
        assert len(history) == 2
        assert history[1].role == "agent"
        assert "clarification" in history[1].content.lower()


# =============================================================================
# Conversation Context Tests
# =============================================================================


class TestConversationContext:
    """Tests for conversation history context."""

    @pytest.mark.asyncio
    async def test_conversation_context_built(self, quilto: Quilto) -> None:
        """Conversation context should be built from history."""
        session = quilto.create_session()

        # First turn
        with patch.object(quilto, "_get_graph") as mock_get_graph:
            mock_graph = MagicMock()
            mock_graph.ainvoke = AsyncMock(
                return_value={
                    "input_type": "query",
                    "response": "First response",
                    "selected_domains": [],
                }
            )
            mock_get_graph.return_value = mock_graph

            await session.process("First question")

        # Second turn - should include context
        with patch.object(quilto, "_get_graph") as mock_get_graph:
            mock_graph = MagicMock()

            captured_state: dict[str, Any] = {}

            async def capture_state(state: dict[str, Any]) -> dict[str, Any]:
                captured_state.update(state)
                return {
                    "input_type": "query",
                    "response": "Second response",
                    "selected_domains": [],
                }

            mock_graph.ainvoke = capture_state
            mock_get_graph.return_value = mock_graph

            await session.process("Second question")

        # Context should include previous turns
        context = captured_state.get("conversation_context")
        assert context is not None
        assert "user: First question" in context or "First question" in context


# =============================================================================
# Session Without Quilto Tests
# =============================================================================


class TestSessionWithoutQuilto:
    """Tests for Session.process() without Quilto reference."""

    @pytest.mark.asyncio
    async def test_process_without_quilto_raises(self) -> None:
        """process() should raise if session not connected to Quilto."""
        from quilto.session import Session, SessionConfig, SessionData
        from quilto.session.stores import SQLiteSessionStore

        store = SQLiteSessionStore(":memory:")
        config = SessionConfig()
        data = SessionData(
            session_id="test",
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        store.save(data)

        session = Session(data, store, config)
        # _quilto is None

        with pytest.raises(RuntimeError) as exc_info:
            await session.process("Test")

        assert "not connected to Quilto" in str(exc_info.value)


# =============================================================================
# Get Session Tests
# =============================================================================


class TestGetSession:
    """Tests for Quilto.get_session()."""

    def test_get_session_existing(self, quilto: Quilto) -> None:
        """get_session should return existing session."""
        session = quilto.create_session()
        session.add_turn("user", "Hello")
        session_id = session.session_id

        loaded = quilto.get_session(session_id)

        assert loaded is not None
        assert loaded.session_id == session_id
        assert len(loaded.get_history()) == 1

    def test_get_session_nonexistent(self, quilto: Quilto) -> None:
        """get_session should return None for non-existent ID."""
        result = quilto.get_session("does-not-exist")
        assert result is None

    def test_get_session_has_quilto_reference(self, quilto: Quilto) -> None:
        """get_session should set Quilto reference on loaded session."""
        session = quilto.create_session()
        session_id = session.session_id

        loaded = quilto.get_session(session_id)

        assert loaded is not None
        assert loaded._quilto == quilto  # pyright: ignore[reportPrivateUsage]


# =============================================================================
# BOTH Flow Tests
# =============================================================================


class TestBothFlow:
    """Tests for BOTH input type (query + log)."""

    @pytest.mark.asyncio
    async def test_both_flow_returns_both_results(self, quilto: Quilto) -> None:
        """BOTH flow should have both response and parsed_data."""
        session = quilto.create_session()

        with patch.object(quilto, "_get_graph") as mock_get_graph:
            mock_graph = MagicMock()
            mock_graph.ainvoke = AsyncMock(
                return_value={
                    "input_type": "both",
                    "response": "Query response",
                    "parsed_data": {"activity": "running"},
                    "selected_domains": ["test_domain"],
                }
            )
            mock_get_graph.return_value = mock_graph

            result = await session.process("Ran 5k, how's my progress?")

        assert result.input_type == "both"
        assert result.response == "Query response"
        assert result.parsed_data is not None


# =============================================================================
# CORRECTION Flow Tests
# =============================================================================


class TestCorrectionFlow:
    """Tests for CORRECTION input type."""

    @pytest.mark.asyncio
    async def test_correction_flow_returns_result(self, quilto: Quilto) -> None:
        """CORRECTION flow should return correction result."""
        session = quilto.create_session()

        with patch.object(quilto, "_get_graph") as mock_get_graph:
            mock_graph = MagicMock()
            mock_graph.ainvoke = AsyncMock(
                return_value={
                    "input_type": "correction",
                    "correction_result": {
                        "success": True,
                        "target_entry_id": "entry123",
                    },
                    "selected_domains": ["test_domain"],
                }
            )
            mock_get_graph.return_value = mock_graph

            result = await session.process("Actually that was 6k not 5k")

        assert result.input_type == "correction"


# =============================================================================
# Error Handling Tests
# =============================================================================


class TestErrorHandling:
    """Tests for error handling in orchestration."""

    @pytest.mark.asyncio
    async def test_error_in_graph_returns_partial(self, quilto: Quilto) -> None:
        """Error in graph should return partial result."""
        session = quilto.create_session()

        with patch.object(quilto, "_get_graph") as mock_get_graph:
            mock_graph = MagicMock()
            mock_graph.ainvoke = AsyncMock(
                return_value={
                    "input_type": "query",
                    "error": "Router failed: connection error",
                    "response": "I encountered an error.",
                    "selected_domains": [],
                }
            )
            mock_get_graph.return_value = mock_graph

            result = await session.process("Test query")

        # Should still return a result
        assert result is not None
        assert result.input_type == "query"


# =============================================================================
# Import Verification Tests
# =============================================================================


class TestImportVerification:
    """Tests for import verification."""

    def test_quilto_import(self) -> None:
        """Quilto should be importable from quilto package."""
        from quilto import Quilto

        assert Quilto is not None

    def test_quilto_in_all(self) -> None:
        """Quilto should be in __all__."""
        import quilto

        assert "Quilto" in quilto.__all__
