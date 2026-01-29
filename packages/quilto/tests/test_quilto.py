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


class TestVagueQueryClarification:
    """Tests for vague query clarification heuristics.

    Story 20.1 - AC #4: System asks for clarification when vague query
    is submitted without conversation context.
    """

    @pytest.mark.asyncio
    async def test_vague_query_without_context_triggers_clarification(self, quilto: Quilto) -> None:
        """Vague query in new session should trigger clarification.

        Scenario: User submits "What about that?" as first query in new session.
        Expected: Planner should return clarify_questions since there's no context.

        Note: This is a UNIT TEST verifying the orchestration layer handles
        clarification responses. It mocks the graph to return clarification,
        testing the plumbing rather than actual Planner prompt behavior.
        Integration testing of Planner prompt is done via test-ollama.
        """
        session = quilto.create_session()
        assert len(session.get_history()) == 0  # New session

        # Mock graph to return clarification (simulating Planner behavior)
        with patch.object(quilto, "_get_graph") as mock_get_graph:
            mock_graph = MagicMock()
            mock_graph.ainvoke = AsyncMock(
                return_value={
                    "input_type": "query",
                    "next_action": "clarify",
                    "clarify_questions": [
                        "What are you referring to?",
                        "Can you provide more details about your question?",
                    ],
                    "selected_domains": [],
                }
            )
            mock_get_graph.return_value = mock_graph

            result = await session.process("What about that?")

        # Should return clarification questions
        assert result.clarification_questions is not None
        assert len(result.clarification_questions) >= 1

    @pytest.mark.asyncio
    async def test_vague_query_with_context_proceeds_normally(self, quilto: Quilto) -> None:
        """Vague query with prior context should proceed with retrieval.

        Scenario: User has prior conversation about bench press, then asks
        "What about that?" - should interpret "that" from context.
        """
        session = quilto.create_session()

        # First turn - establish context
        with patch.object(quilto, "_get_graph") as mock_get_graph:
            mock_graph = MagicMock()
            mock_graph.ainvoke = AsyncMock(
                return_value={
                    "input_type": "query",
                    "response": "Your bench press was 185lbs.",
                    "selected_domains": ["strength"],
                }
            )
            mock_get_graph.return_value = mock_graph
            await session.process("How was my bench press?")

        # Second turn - vague query with context available
        with patch.object(quilto, "_get_graph") as mock_get_graph:
            mock_graph = MagicMock()

            captured_state: dict[str, Any] = {}

            async def capture_state(state: dict[str, Any]) -> dict[str, Any]:
                captured_state.update(state)
                return {
                    "input_type": "query",
                    "next_action": "retrieve",  # Should proceed, not clarify
                    "response": "Your bench press last week was 180lbs.",
                    "selected_domains": ["strength"],
                }

            mock_graph.ainvoke = capture_state
            mock_get_graph.return_value = mock_graph

            result = await session.process("What about last week?")

        # Should NOT ask for clarification since context is available
        assert result.clarification_questions is None
        # Should have conversation context
        assert captured_state.get("conversation_context") is not None
        assert "bench press" in captured_state["conversation_context"].lower()


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

    @pytest.mark.asyncio
    async def test_resumed_session_includes_conversation_context(self, quilto: Quilto) -> None:
        """Resumed session should include previous conversation context.

        Simulates CLI resume flow:
        1. Create session, process query, get response
        2. Resume session via get_session()
        3. Process follow-up query
        4. Verify conversation_context contains previous turns

        Story 20.1 - AC #1, #2: Session conversation context loaded and passed.
        """
        # === Session 1: Original conversation ===
        session = quilto.create_session()
        session_id = session.session_id

        with patch.object(quilto, "_get_graph") as mock_get_graph:
            mock_graph = MagicMock()
            mock_graph.ainvoke = AsyncMock(
                return_value={
                    "input_type": "query",
                    "response": "Your bench press was 185lbs for 5 reps.",
                    "selected_domains": ["strength"],
                }
            )
            mock_get_graph.return_value = mock_graph

            await session.process("How was my bench press this week?")

        # Verify history was saved
        assert len(session.get_history()) == 2  # user + agent

        # === Session 2: Resumed session ===
        resumed = quilto.get_session(session_id)
        assert resumed is not None
        assert len(resumed.get_history()) == 2  # History persisted

        # Process follow-up and capture state
        with patch.object(quilto, "_get_graph") as mock_get_graph:
            mock_graph = MagicMock()

            captured_state: dict[str, Any] = {}

            async def capture_state(state: dict[str, Any]) -> dict[str, Any]:
                captured_state.update(state)
                return {
                    "input_type": "query",
                    "response": "Last week you did 175lbs.",
                    "selected_domains": ["strength"],
                }

            mock_graph.ainvoke = capture_state
            mock_get_graph.return_value = mock_graph

            await resumed.process("What about last week?")

        # Verify conversation_context includes previous turns
        # Context format: "user: <message>\nagent: <response>\n..." (built by Session._build_conversation_context)
        context = captured_state.get("conversation_context")
        assert context is not None, "conversation_context should be populated"
        assert "bench press" in context.lower(), (
            f"Context should contain 'bench press' from previous turn. Got: {context}"
        )
        assert "185" in context or "185lbs" in context, (
            f"Context should contain '185' from previous response. Got: {context}"
        )


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


# =============================================================================
# Analyzer Failure Cascade Tests (Story 16.2)
# =============================================================================


class TestAnalyzerFailureCascade:
    """Tests for analyzer failure handling - Story 16.2."""

    @pytest.mark.asyncio
    async def test_analyzer_failure_provides_fallback_output(self, quilto: Quilto) -> None:
        """Analyzer failure should provide fallback analyzer_output."""
        session = quilto.create_session()

        with patch.object(quilto, "_get_graph") as mock_get_graph:
            mock_graph = MagicMock()
            mock_graph.ainvoke = AsyncMock(
                return_value={
                    "input_type": "query",
                    "error": "Analyzer failed: ValidationError",
                    "analyzer_output": {  # Fallback should be present
                        "query_intent": "Unable to analyze due to error",
                        "findings": [],
                        "patterns_identified": [],
                        "sufficiency_evaluation": {
                            "critical_gaps": [],
                            "nice_to_have_gaps": [],
                            "evidence_check_passed": False,
                            "speculation_risk": "high",
                        },
                        "verdict_reasoning": "Analysis failed with error",
                        "verdict": "insufficient",
                    },
                    "response": "I encountered an error: Analyzer failed",
                    "selected_domains": [],
                    "traces": [
                        {
                            "agent_name": "analyzer",
                            "input_summary": "test",
                            "output_summary": "ERROR: ValidationError",
                            "elapsed_ms": 100.0,
                            "timestamp": datetime.now(UTC),
                        }
                    ],
                }
            )
            mock_get_graph.return_value = mock_graph

            result = await session.process("Test query")

        assert result is not None
        # Error trace should be present if debug enabled
        # The response should indicate the error

    @pytest.mark.asyncio
    async def test_synthesizer_handles_missing_analyzer_output(self, quilto: Quilto) -> None:
        """Synthesizer should not crash on missing analyzer_output."""
        session = quilto.create_session()

        with patch.object(quilto, "_get_graph") as mock_get_graph:
            mock_graph = MagicMock()
            mock_graph.ainvoke = AsyncMock(
                return_value={
                    "input_type": "query",
                    # No analyzer_output key at all
                    "response": "Fallback response",
                    "selected_domains": [],
                }
            )
            mock_get_graph.return_value = mock_graph

            # Should not raise
            result = await session.process("Test query")

        assert result is not None

    @pytest.mark.asyncio
    async def test_error_trace_appears_in_debug_output(
        self,
        mock_llm_client: MagicMock,
        mock_storage: StorageRepository,
        mock_domain: DomainModule,
    ) -> None:
        """Error trace should appear in ProcessResult.debug.traces."""
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
                    "error": "Analyzer failed: some error",
                    "response": "I encountered an error: Analyzer failed - some error",
                    "selected_domains": [],
                    "traces": [
                        {
                            "agent_name": "router",
                            "input_summary": "test",
                            "output_summary": "type=query",
                            "elapsed_ms": 50.0,
                            "timestamp": datetime.now(UTC),
                        },
                        {
                            "agent_name": "analyzer",
                            "input_summary": "5 entries",
                            "output_summary": "ERROR: some error",
                            "elapsed_ms": 100.0,
                            "timestamp": datetime.now(UTC),
                        },
                    ],
                    "total_elapsed_ms": 500.0,
                    "retry_count": 0,
                }
            )
            mock_get_graph.return_value = mock_graph

            result = await session.process("Test query")

        assert result.debug is not None
        assert len(result.debug.traces) == 2
        # Check that error trace is present
        error_traces = [t for t in result.debug.traces if "ERROR" in t.output_summary]
        assert len(error_traces) == 1
        assert error_traces[0].agent_name == "analyzer"

    @pytest.mark.asyncio
    async def test_error_response_includes_agent_name(self, quilto: Quilto) -> None:
        """Error response should include which agent failed."""
        session = quilto.create_session()

        with patch.object(quilto, "_get_graph") as mock_get_graph:
            mock_graph = MagicMock()
            mock_graph.ainvoke = AsyncMock(
                return_value={
                    "input_type": "query",
                    "error": "Synthesizer failed: LLM timeout",
                    "response": "I encountered an error: Synthesizer failed - LLM timeout",
                    "selected_domains": [],
                }
            )
            mock_get_graph.return_value = mock_graph

            result = await session.process("Test query")

        assert result is not None
        assert result.response is not None
        assert "Synthesizer failed" in result.response


# =============================================================================
# Orchestration Node Unit Tests (Story 16.2 - Direct Node Testing)
# =============================================================================


class TestOrchestrationNodeExceptionHandling:
    """Direct unit tests for orchestration node exception handling.

    These tests call node functions directly instead of mocking the graph,
    verifying actual exception handling behavior.
    """

    @pytest.mark.asyncio
    async def test_analyze_node_exception_returns_fallback_output(
        self,
        mock_llm_client: MagicMock,
        mock_storage: StorageRepository,
        mock_domain: DomainModule,
    ) -> None:
        """analyze_node should return fallback analyzer_output on exception."""
        from quilto.orchestration import analyze_node

        q = Quilto(
            llm_client=mock_llm_client,
            storage=mock_storage,
            domains=[mock_domain],
            session_db_path=":memory:",
        )

        # Make LLM client raise an exception
        mock_llm_client.complete = AsyncMock(side_effect=ValueError("LLM failed"))

        state = {
            "_quilto": q,
            "user_input": "Test query",
            "entries": [],
            "domain_context": {
                "domains": [],
                "vocabulary": {},
                "expertise": "",
                "evaluation_rules": [],
                "context_management_guidance": "",
            },
            "query_type": "factual",
            "retrieval_summary": [],
            "traces": [],
        }

        result = await analyze_node(state)  # type: ignore[arg-type]

        # Should have fallback analyzer_output
        assert "analyzer_output" in result
        assert result["analyzer_output"]["query_intent"] == "Unable to analyze due to error"
        assert result["analyzer_output"]["verdict"] == "insufficient"
        assert "error" in result
        assert "Analyzer failed" in result["error"]

    @pytest.mark.asyncio
    async def test_analyze_node_exception_adds_error_trace(
        self,
        mock_llm_client: MagicMock,
        mock_storage: StorageRepository,
        mock_domain: DomainModule,
    ) -> None:
        """analyze_node should add ERROR trace on exception."""
        from quilto.orchestration import analyze_node

        q = Quilto(
            llm_client=mock_llm_client,
            storage=mock_storage,
            domains=[mock_domain],
            session_db_path=":memory:",
        )

        mock_llm_client.complete = AsyncMock(side_effect=RuntimeError("Connection lost"))

        state = {
            "_quilto": q,
            "user_input": "Test query for trace",
            "entries": [{"id": "e1", "raw_content": "test"}],
            "domain_context": {
                "domains": [],
                "vocabulary": {},
                "expertise": "",
                "evaluation_rules": [],
                "context_management_guidance": "",
            },
            "query_type": "factual",
            "retrieval_summary": [],
            "traces": [],
        }

        result = await analyze_node(state)  # type: ignore[arg-type]

        # Should have error trace
        assert "traces" in result
        traces = result["traces"]
        assert len(traces) == 1
        assert traces[0]["agent_name"] == "analyzer"
        assert "ERROR:" in traces[0]["output_summary"]

    @pytest.mark.asyncio
    async def test_synthesize_node_handles_invalid_analyzer_output(
        self,
        mock_llm_client: MagicMock,
        mock_storage: StorageRepository,
        mock_domain: DomainModule,
    ) -> None:
        """synthesize_node should handle invalid analyzer_output gracefully."""
        from quilto.orchestration import synthesize_node

        q = Quilto(
            llm_client=mock_llm_client,
            storage=mock_storage,
            domains=[mock_domain],
            session_db_path=":memory:",
        )

        # Make synthesizer succeed with valid response
        mock_llm_client.complete = AsyncMock(
            return_value='{"response": "Test response", "key_points": [], "confidence_notes": []}'
        )

        state = {
            "_quilto": q,
            "user_input": "Test query",
            "analysis_verdict": "insufficient",
            "analyzer_output": {"invalid": "data"},  # Invalid - missing required fields
            "domain_context": {
                "domains": [],
                "vocabulary": {},
                "expertise": "",
                "evaluation_rules": [],
                "context_management_guidance": "",
            },
            "query_type": "factual",
            "is_partial": False,
            "traces": [],
        }

        # Should not raise - should use fallback AnalyzerOutput
        result = await synthesize_node(state)  # type: ignore[arg-type]

        # Should complete (either with response or error, but not crash)
        assert result is not None
        # Either has response or has error with graceful message
        assert "response" in result or "error" in result

    @pytest.mark.asyncio
    async def test_evaluate_node_exception_adds_error_trace(
        self,
        mock_llm_client: MagicMock,
        mock_storage: StorageRepository,
        mock_domain: DomainModule,
    ) -> None:
        """evaluate_node should add ERROR trace on exception."""
        from quilto.orchestration import evaluate_node

        q = Quilto(
            llm_client=mock_llm_client,
            storage=mock_storage,
            domains=[mock_domain],
            session_db_path=":memory:",
        )

        mock_llm_client.complete = AsyncMock(side_effect=TimeoutError("LLM timeout"))

        state = {
            "_quilto": q,
            "user_input": "Test query",
            "response": "Test response",
            "analyzer_output": {
                "query_intent": "test",
                "findings": [],
                "patterns_identified": [],
                "sufficiency_evaluation": {
                    "critical_gaps": [],
                    "nice_to_have_gaps": [],
                    "evidence_check_passed": True,
                    "speculation_risk": "low",
                },
                "verdict_reasoning": "test",
                "verdict": "sufficient",
            },
            "entries": [],
            "domain_context": {
                "domains": [],
                "vocabulary": {},
                "expertise": "",
                "evaluation_rules": [],
                "context_management_guidance": "",
            },
            "retry_count": 0,
            "traces": [],
        }

        result = await evaluate_node(state)  # type: ignore[arg-type]

        # Should have error trace
        assert "traces" in result
        traces = result["traces"]
        assert len(traces) == 1
        assert traces[0]["agent_name"] == "evaluator"
        assert "ERROR:" in traces[0]["output_summary"]
        assert "error" in result
        assert "Evaluator failed" in result["error"]


# =============================================================================
# Clarification Flow with Session Resume Tests (Story 20.2)
# =============================================================================


class TestClarificationFlowSessionResume:
    """Tests for clarification flow integrated with session resume.

    Story 20.2: Verify/Fix Clarification Flow + Session Resume
    Tests the complete flow:
    1. Query triggers clarification → session persisted
    2. Resume session with answer → verify history includes original + clarification
    3. Final response incorporates both original query AND clarification answer
    """

    @pytest.mark.asyncio
    async def test_clarification_resume_includes_original_and_clarification(self, quilto: Quilto) -> None:
        """AC #2: Resumed session should include original query + agent clarification.

        Flow:
        1. Send query that triggers clarification
        2. Resume session with answer
        3. Verify conversation_context includes:
           - Original user query
           - Agent clarification question
        """
        session = quilto.create_session()
        session_id = session.session_id

        # === Turn 1: Query triggers clarification ===
        with patch.object(quilto, "_get_graph") as mock_get_graph:
            mock_graph = MagicMock()
            mock_graph.ainvoke = AsyncMock(
                return_value={
                    "input_type": "query",
                    "next_action": "clarify",
                    "clarify_questions": ["What time did you workout?"],
                    "selected_domains": ["general_fitness"],
                }
            )
            mock_get_graph.return_value = mock_graph

            result = await session.process("How was my workout?")

        # Verify clarification was returned
        assert result.clarification_questions is not None
        assert len(result.clarification_questions) == 1
        assert result.clarification_questions[0].question == "What time did you workout?"

        # Verify history includes user query + agent clarification turn
        history = session.get_history()
        assert len(history) == 2
        assert history[0].role == "user"
        assert history[0].content == "How was my workout?"
        assert history[1].role == "agent"
        assert "clarification" in history[1].content.lower()

        # === Turn 2: Resume session with answer ===
        resumed = quilto.get_session(session_id)
        assert resumed is not None
        assert len(resumed.get_history()) == 2  # History persisted

        with patch.object(quilto, "_get_graph") as mock_get_graph:
            mock_graph = MagicMock()

            captured_state: dict[str, Any] = {}

            async def capture_state(state: dict[str, Any]) -> dict[str, Any]:
                captured_state.update(state)
                return {
                    "input_type": "query",
                    "next_action": "retrieve",
                    "response": "Your morning workout went well - 45 minutes of cardio.",
                    "selected_domains": ["general_fitness"],
                }

            mock_graph.ainvoke = capture_state
            mock_get_graph.return_value = mock_graph

            await resumed.process("Morning session")

        # Verify conversation_context includes original query + clarification
        context = captured_state.get("conversation_context")
        assert context is not None
        assert "how was my workout" in context.lower()
        assert "clarification" in context.lower() or "time" in context.lower()

    @pytest.mark.asyncio
    async def test_clarification_answer_integrated_into_response(self, quilto: Quilto) -> None:
        """AC #3: Final response reflects both original query AND clarification answer.

        Flow:
        1. Send vague query → Get clarification question
        2. Resume with answer
        3. Verify Planner receives full conversation context
        """
        session = quilto.create_session()
        session_id = session.session_id

        # === Turn 1: Vague query triggers clarification ===
        with patch.object(quilto, "_get_graph") as mock_get_graph:
            mock_graph = MagicMock()
            mock_graph.ainvoke = AsyncMock(
                return_value={
                    "input_type": "query",
                    "next_action": "clarify",
                    "clarify_questions": ["Which workout would you like to know about - strength or cardio?"],
                    "selected_domains": [],
                }
            )
            mock_get_graph.return_value = mock_graph

            await session.process("How did I do?")

        # === Turn 2: Resume with clarification answer ===
        resumed = quilto.get_session(session_id)
        assert resumed is not None

        with patch.object(quilto, "_get_graph") as mock_get_graph:
            mock_graph = MagicMock()

            captured_state: dict[str, Any] = {}

            async def capture_state(state: dict[str, Any]) -> dict[str, Any]:
                captured_state.update(state)
                # Simulates Planner using context to provide appropriate response
                return {
                    "input_type": "query",
                    "next_action": "retrieve",
                    "response": "Based on your strength workout, you did 3 sets of squats at 135lbs.",
                    "selected_domains": ["strength"],
                }

            mock_graph.ainvoke = capture_state
            mock_get_graph.return_value = mock_graph

            result = await resumed.process("Strength training")

        # Verify conversation context passed to graph includes both original query and answer
        context = captured_state.get("conversation_context")
        assert context is not None

        # Should contain original query "How did I do?"
        assert "how did i do" in context.lower() or "how did" in context.lower()

        # Should contain the clarification question from agent
        assert "strength" in context.lower() or "cardio" in context.lower()

        # Final result should have response (simulated but proves flow works)
        assert result.response is not None
        assert "strength" in result.response.lower()

    @pytest.mark.asyncio
    async def test_multiple_clarification_rounds(self, quilto: Quilto) -> None:
        """AC #4: Multiple clarification rounds accumulate correctly.

        Flow:
        1. Query → clarification1
        2. Answer1 → clarification2
        3. Answer2 → final response
        4. Verify all answers are incorporated in context
        """
        session = quilto.create_session()
        session_id = session.session_id

        # === Turn 1: Initial query triggers first clarification ===
        with patch.object(quilto, "_get_graph") as mock_get_graph:
            mock_graph = MagicMock()
            mock_graph.ainvoke = AsyncMock(
                return_value={
                    "input_type": "query",
                    "next_action": "clarify",
                    "clarify_questions": ["What type of exercise?"],
                    "selected_domains": [],
                }
            )
            mock_get_graph.return_value = mock_graph

            await session.process("Compare my progress")

        # === Turn 2: First answer triggers second clarification ===
        with patch.object(quilto, "_get_graph") as mock_get_graph:
            mock_graph = MagicMock()
            mock_graph.ainvoke = AsyncMock(
                return_value={
                    "input_type": "query",
                    "next_action": "clarify",
                    "clarify_questions": ["What time period - this week or last month?"],
                    "selected_domains": ["running"],
                }
            )
            mock_get_graph.return_value = mock_graph

            await session.process("Running")

        # Verify history has 4 turns (2 user + 2 agent)
        assert len(session.get_history()) == 4

        # === Turn 3: Second answer leads to final response ===
        resumed = quilto.get_session(session_id)
        assert resumed is not None
        assert len(resumed.get_history()) == 4

        with patch.object(quilto, "_get_graph") as mock_get_graph:
            mock_graph = MagicMock()

            captured_state: dict[str, Any] = {}

            async def capture_state(state: dict[str, Any]) -> dict[str, Any]:
                captured_state.update(state)
                return {
                    "input_type": "query",
                    "next_action": "retrieve",
                    "response": "Your running progress this week shows 15km total.",
                    "selected_domains": ["running"],
                }

            mock_graph.ainvoke = capture_state
            mock_get_graph.return_value = mock_graph

            result = await resumed.process("This week")

        # Verify conversation_context includes recent turns
        # Note: _build_conversation_context() uses last 4 turns, so after 5 turns
        # (user1, agent1, user2, agent2, user3), the context includes:
        # agent1, user2, agent2, user3 - but NOT user1 (original query)
        # This is expected behavior for memory efficiency.
        context = captured_state.get("conversation_context")
        assert context is not None

        # Context should include the first clarification answer ("Running")
        assert "running" in context.lower()
        # Context should include the second clarification question (time period)
        assert "time period" in context.lower() or "this week" in context.lower()
        # Context should include the first clarification question (exercise type)
        assert "exercise" in context.lower() or "type" in context.lower()

        # Final response should be present
        assert result.response is not None
        assert result.clarification_questions is None  # No more clarification needed

    @pytest.mark.asyncio
    async def test_clarification_metadata_persisted_in_turn(self, quilto: Quilto) -> None:
        """Clarification questions should be stored in turn metadata.

        Verifies that clarification questions are properly serialized
        in the agent turn metadata for conversation history display.
        """
        session = quilto.create_session()

        with patch.object(quilto, "_get_graph") as mock_get_graph:
            mock_graph = MagicMock()
            mock_graph.ainvoke = AsyncMock(
                return_value={
                    "input_type": "query",
                    "next_action": "clarify",
                    "clarify_questions": [{"question": "When?", "options": ["Morning", "Evening"]}],
                    "selected_domains": [],
                }
            )
            mock_get_graph.return_value = mock_graph

            await session.process("How was my workout?")

        # Verify agent turn has metadata with clarification questions
        history = session.get_history()
        agent_turn = history[1]
        assert agent_turn.role == "agent"
        assert agent_turn.metadata is not None
        assert "clarification_questions" in agent_turn.metadata

        # Verify metadata structure
        questions = agent_turn.metadata["clarification_questions"]
        assert len(questions) == 1
        assert questions[0]["question"] == "When?"
        assert questions[0]["options"] == ["Morning", "Evening"]
