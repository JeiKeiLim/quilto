"""Unit tests for feedback recording infrastructure."""

import json
from datetime import datetime
from pathlib import Path

import pytest
from pydantic import ValidationError
from swealog.cli.feedback import (
    FeedbackProgressHandler,
    FeedbackRecord,
    FeedbackRecorder,
    IntermediateOutputs,
    SessionMetadata,
    generate_feedback_id,
    get_unique_feedback_path,
)


class TestFeedbackProgressHandler:
    """Tests for FeedbackProgressHandler class."""

    @pytest.fixture
    def handler(self) -> FeedbackProgressHandler:
        """Create a handler for testing."""
        return FeedbackProgressHandler()

    @pytest.mark.asyncio
    async def test_on_agent_start_no_op(self, handler: FeedbackProgressHandler) -> None:
        """Test that on_agent_start is a no-op but doesn't error."""
        await handler.on_agent_start("router", "test input")
        # Should not raise, should not store anything
        assert handler.get_outputs() == {}

    @pytest.mark.asyncio
    async def test_on_agent_complete_captures_output(self, handler: FeedbackProgressHandler) -> None:
        """Test that on_agent_complete captures agent output."""
        output = {"input_type": "QUERY", "confidence": 0.95}
        await handler.on_agent_complete("router", 0.5, output)

        outputs = handler.get_outputs()
        assert "router" in outputs
        assert outputs["router"] == output

    @pytest.mark.asyncio
    async def test_on_retry_no_op(self, handler: FeedbackProgressHandler) -> None:
        """Test that on_retry is a no-op but doesn't error."""
        await handler.on_retry(1, "test reason")
        assert handler.get_outputs() == {}

    @pytest.mark.asyncio
    async def test_on_stage_no_op(self, handler: FeedbackProgressHandler) -> None:
        """Test that on_stage is a no-op but doesn't error."""
        await handler.on_stage("routing")
        assert handler.get_outputs() == {}

    @pytest.mark.asyncio
    async def test_captures_multiple_agents(self, handler: FeedbackProgressHandler) -> None:
        """Test capturing outputs from multiple agents."""
        await handler.on_agent_complete("router", 0.1, {"input_type": "QUERY"})
        await handler.on_agent_complete("planner", 0.2, {"query": "test"})
        await handler.on_agent_complete("retriever", 0.3, {"entries": []})

        outputs = handler.get_outputs()
        assert len(outputs) == 3
        assert "router" in outputs
        assert "planner" in outputs
        assert "retriever" in outputs

    @pytest.mark.asyncio
    async def test_get_outputs_returns_copy(self, handler: FeedbackProgressHandler) -> None:
        """Test that get_outputs returns a copy, not the internal dict."""
        await handler.on_agent_complete("router", 0.1, {"input_type": "QUERY"})

        outputs1 = handler.get_outputs()
        outputs1["new_key"] = {"data": "test"}

        outputs2 = handler.get_outputs()
        assert "new_key" not in outputs2

    @pytest.mark.asyncio
    async def test_get_intermediate_outputs_query_flow(self, handler: FeedbackProgressHandler) -> None:
        """Test get_intermediate_outputs for a QUERY flow."""
        await handler.on_agent_complete("router", 0.1, {"input_type": "QUERY"})
        await handler.on_agent_complete("planner", 0.2, {"query": "test"})
        await handler.on_agent_complete("retriever", 0.3, {"entries": []})
        await handler.on_agent_complete("analyzer", 0.2, {"verdict": "SUFFICIENT"})
        await handler.on_agent_complete("synthesizer", 0.5, {"response": "answer"})
        await handler.on_agent_complete("evaluator", 0.1, {"overall_verdict": "PASS"})

        outputs = handler.get_intermediate_outputs()
        assert outputs.router == {"input_type": "QUERY"}
        assert outputs.planner == {"query": "test"}
        assert outputs.retriever == {"entries": []}
        assert outputs.analyzer == {"verdict": "SUFFICIENT"}
        assert outputs.synthesizer == {"response": "answer"}
        assert outputs.evaluator == {"overall_verdict": "PASS"}
        # Non-called agents should be empty dicts
        assert outputs.parser == {}
        assert outputs.observer == {}
        assert outputs.correction == {}

    @pytest.mark.asyncio
    async def test_get_intermediate_outputs_log_flow(self, handler: FeedbackProgressHandler) -> None:
        """Test get_intermediate_outputs for a LOG flow."""
        await handler.on_agent_complete("router", 0.1, {"input_type": "LOG"})
        await handler.on_agent_complete("parser", 0.3, {"domain_data": {}})

        outputs = handler.get_intermediate_outputs()
        assert outputs.router == {"input_type": "LOG"}
        assert outputs.parser == {"domain_data": {}}
        # Query flow agents not called
        assert outputs.planner == {}
        assert outputs.retriever == {}
        assert outputs.analyzer == {}
        assert outputs.synthesizer == {}
        assert outputs.evaluator == {}

    @pytest.mark.asyncio
    async def test_get_intermediate_outputs_empty(self, handler: FeedbackProgressHandler) -> None:
        """Test get_intermediate_outputs with no captured data."""
        outputs = handler.get_intermediate_outputs()
        assert outputs.router == {}
        assert outputs.planner == {}
        assert outputs.retriever == {}
        assert outputs.analyzer == {}
        assert outputs.synthesizer == {}
        assert outputs.evaluator == {}
        assert outputs.parser == {}
        assert outputs.observer == {}
        assert outputs.correction == {}

    @pytest.mark.asyncio
    async def test_integration_with_feedback_recorder(self, handler: FeedbackProgressHandler, tmp_path: Path) -> None:
        """Test that handler outputs work with FeedbackRecorder.record()."""
        # Simulate a full QUERY flow
        await handler.on_agent_complete("router", 0.1, {"input_type": "QUERY"})
        await handler.on_agent_complete("planner", 0.2, {"query": "test"})
        await handler.on_agent_complete("retriever", 0.3, {"entries": []})
        await handler.on_agent_complete("analyzer", 0.2, {"verdict": "SUFFICIENT"})
        await handler.on_agent_complete("synthesizer", 0.5, {"response": "answer"})
        await handler.on_agent_complete("evaluator", 0.1, {"overall_verdict": "PASS"})

        # Create FeedbackRecord using handler
        intermediate_outputs = handler.get_intermediate_outputs()
        feedback_record = FeedbackRecord(
            id="2026-01-27_test1234",
            query="test query",
            intermediate_outputs=intermediate_outputs,
            final_response="test response",
            user_feedback="good",
            session=SessionMetadata(
                timestamp=datetime.now(),
                input_type="QUERY",
            ),
        )

        # Record should succeed
        recorder = FeedbackRecorder(feedback_dir=tmp_path)
        file_path = recorder.record(feedback_record)

        assert file_path.exists()

        # Verify content
        content = json.loads(file_path.read_text(encoding="utf-8"))
        assert content["intermediate_outputs"]["router"] == {"input_type": "QUERY"}
        assert content["intermediate_outputs"]["evaluator"] == {"overall_verdict": "PASS"}
        assert content["intermediate_outputs"]["parser"] == {}  # Not called

    @pytest.mark.asyncio
    async def test_observer_output_captured(self, handler: FeedbackProgressHandler) -> None:
        """Test that observer agent output is captured."""
        await handler.on_agent_complete("observer", 0.3, {"should_update": True, "updates": []})

        outputs = handler.get_intermediate_outputs()
        assert outputs.observer == {"should_update": True, "updates": []}

    @pytest.mark.asyncio
    async def test_debug_mode_prints_output(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Test that debug mode prints agent output to terminal (Story 18.2 AC:1, AC:2).

        Implementation outputs raw JSON format for full debug visibility.
        """
        debug_handler = FeedbackProgressHandler(debug=True)
        await debug_handler.on_agent_complete(
            "router", 0.5, {"input_type": "QUERY", "selected_domains": ["fitness"], "confidence": 0.95}
        )

        captured = capsys.readouterr()
        assert "Router" in captured.out
        # Raw JSON output format
        assert '"input_type": "QUERY"' in captured.out
        assert '"selected_domains"' in captured.out
        assert "fitness" in captured.out
        assert '"confidence": 0.95' in captured.out

    @pytest.mark.asyncio
    async def test_debug_mode_formats_planner_output(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Test planner output formatting in debug mode (Story 18.2 AC:3).

        Implementation outputs raw JSON format for full debug visibility.
        """
        debug_handler = FeedbackProgressHandler(debug=True)
        await debug_handler.on_agent_complete(
            "planner",
            0.5,
            {
                "query_type": "insight",
                "retrieval_instructions": [{"strategy": "date_range"}],
                "next_action": "retrieve",
            },
        )

        captured = capsys.readouterr()
        assert "Planner" in captured.out
        # Raw JSON output format
        assert '"strategy": "date_range"' in captured.out
        assert '"query_type": "insight"' in captured.out
        assert '"next_action": "retrieve"' in captured.out

    @pytest.mark.asyncio
    async def test_debug_mode_formats_planner_with_none_instructions(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Test planner handles None retrieval_instructions gracefully.

        Implementation outputs raw JSON format for full debug visibility.
        """
        debug_handler = FeedbackProgressHandler(debug=True)
        await debug_handler.on_agent_complete(
            "planner",
            0.5,
            {
                "query_type": "insight",
                "retrieval_instructions": None,  # Explicit None
                "next_action": "retrieve",
            },
        )

        captured = capsys.readouterr()
        assert "Planner" in captured.out
        # Raw JSON output: null for None
        assert '"retrieval_instructions": null' in captured.out

    @pytest.mark.asyncio
    async def test_debug_mode_formats_retriever_output(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Test retriever output formatting in debug mode (Story 18.2 AC:4).

        Implementation outputs raw JSON format for full debug visibility.
        """
        debug_handler = FeedbackProgressHandler(debug=True)
        await debug_handler.on_agent_complete("retriever", 0.1, {"entries": [{}, {}, {}]})

        captured = capsys.readouterr()
        assert "Retriever" in captured.out
        # Raw JSON output: entries array with 3 objects
        assert '"entries"' in captured.out
        assert captured.out.count("{}") == 3  # Three empty entry objects

    @pytest.mark.asyncio
    async def test_debug_mode_formats_analyzer_output(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Test analyzer output formatting in debug mode (Story 18.2 AC:5).

        Implementation outputs raw JSON format for full debug visibility.
        """
        debug_handler = FeedbackProgressHandler(debug=True)
        await debug_handler.on_agent_complete(
            "analyzer",
            0.5,
            {
                "verdict": "SUFFICIENT",
                "findings": [{"type": "progress"}],
                "patterns_identified": [{"name": "consistent"}],
            },
        )

        captured = capsys.readouterr()
        assert "Analyzer" in captured.out
        # Raw JSON output format
        assert '"verdict": "SUFFICIENT"' in captured.out
        assert '"findings"' in captured.out
        assert '"patterns_identified"' in captured.out

    @pytest.mark.asyncio
    async def test_debug_mode_formats_synthesizer_output(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Test synthesizer output formatting in debug mode (Story 18.2 AC:6).

        Implementation outputs raw JSON format for full debug visibility.
        """
        debug_handler = FeedbackProgressHandler(debug=True)
        await debug_handler.on_agent_complete(
            "synthesizer", 0.5, {"response": "Based on your 23 workout sessions, you've made good progress..."}
        )

        captured = capsys.readouterr()
        assert "Synthesizer" in captured.out
        # Raw JSON output format
        assert '"response":' in captured.out
        assert "Based on your 23 workout sessions" in captured.out

    @pytest.mark.asyncio
    async def test_debug_mode_off_no_print(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Test that debug=False (default) does not print output."""
        handler = FeedbackProgressHandler()  # debug=False by default
        await handler.on_agent_complete("router", 0.5, {"input_type": "QUERY"})

        captured = capsys.readouterr()
        assert "Router" not in captured.out

    @pytest.mark.asyncio
    async def test_debug_mode_formats_evaluator_output(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Test evaluator output formatting in debug mode.

        Implementation outputs raw JSON format for full debug visibility.
        """
        debug_handler = FeedbackProgressHandler(debug=True)
        await debug_handler.on_agent_complete("evaluator", 0.1, {"overall_verdict": "PASS"})

        captured = capsys.readouterr()
        assert "Evaluator" in captured.out
        # Raw JSON output format
        assert '"overall_verdict": "PASS"' in captured.out

    @pytest.mark.asyncio
    async def test_debug_mode_formats_parser_output(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Test parser output formatting in debug mode.

        Implementation outputs raw JSON format for full debug visibility.
        """
        debug_handler = FeedbackProgressHandler(debug=True)
        await debug_handler.on_agent_complete("parser", 0.3, {"domain_data": {"fitness": {}, "strength": {}}})

        captured = capsys.readouterr()
        assert "Parser" in captured.out
        # Raw JSON output format
        assert '"domain_data"' in captured.out
        assert '"fitness"' in captured.out
        assert '"strength"' in captured.out

    @pytest.mark.asyncio
    async def test_debug_mode_formats_observer_output(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Test observer output formatting in debug mode.

        Implementation outputs raw JSON format for full debug visibility.
        """
        debug_handler = FeedbackProgressHandler(debug=True)
        await debug_handler.on_agent_complete("observer", 0.2, {"should_update": True})

        captured = capsys.readouterr()
        assert "Observer" in captured.out
        # Raw JSON output: true (not True)
        assert '"should_update": true' in captured.out

    @pytest.mark.asyncio
    async def test_debug_mode_formats_unknown_agent(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Test unknown agent output formatting falls back to listing keys."""
        debug_handler = FeedbackProgressHandler(debug=True)
        await debug_handler.on_agent_complete("custom_agent", 0.2, {"key1": "val1", "key2": "val2"})

        captured = capsys.readouterr()
        assert "Custom_agent" in captured.out
        assert "key1" in captured.out
        assert "key2" in captured.out


class TestIntermediateOutputs:
    """Tests for IntermediateOutputs model."""

    def test_valid_outputs(self) -> None:
        """Test creating valid intermediate outputs."""
        outputs = IntermediateOutputs(
            router={"input_type": "QUERY", "confidence": 0.95},
            planner={"query": "test", "strategies": []},
            retriever={"entries": [], "sources": []},
            analyzer={"analysis": "test analysis", "verdict": "SUFFICIENT"},
            synthesizer={"response": "test response"},
            evaluator={"verdict": "PASS", "feedback": ""},
        )
        assert outputs.router["input_type"] == "QUERY"
        assert outputs.evaluator["verdict"] == "PASS"

    def test_fields_default_to_empty_dict(self) -> None:
        """Test that all fields default to empty dict."""
        outputs = IntermediateOutputs()
        assert outputs.router == {}
        assert outputs.planner == {}
        assert outputs.retriever == {}
        assert outputs.analyzer == {}
        assert outputs.synthesizer == {}
        assert outputs.evaluator == {}
        assert outputs.parser == {}
        assert outputs.observer == {}
        assert outputs.correction == {}


class TestSessionMetadata:
    """Tests for SessionMetadata model."""

    def test_valid_session_metadata(self) -> None:
        """Test creating valid session metadata."""
        metadata = SessionMetadata(
            timestamp=datetime.now(),
            input_type="QUERY",
            config_path="llm-config.yaml",
            storage_path="logs/",
            debug_enabled=True,
        )
        assert metadata.input_type == "QUERY"
        assert metadata.debug_enabled is True

    def test_minimal_session_metadata(self) -> None:
        """Test creating session metadata with only required fields."""
        metadata = SessionMetadata(
            timestamp=datetime.now(),
            input_type="BOTH",
        )
        assert metadata.config_path is None
        assert metadata.storage_path is None
        assert metadata.debug_enabled is True  # Default

    def test_invalid_input_type_raises_error(self) -> None:
        """Test that invalid input type raises validation error."""
        with pytest.raises(ValidationError) as exc_info:
            SessionMetadata(
                timestamp=datetime.now(),
                input_type="INVALID",  # type: ignore[arg-type]
            )
        assert "input_type" in str(exc_info.value)


class TestFeedbackRecord:
    """Tests for FeedbackRecord model."""

    @pytest.fixture
    def valid_intermediate_outputs(self) -> IntermediateOutputs:
        """Create valid intermediate outputs for testing."""
        return IntermediateOutputs(
            router={"input_type": "QUERY"},
            planner={"query": "test"},
            retriever={"entries": []},
            analyzer={"verdict": "SUFFICIENT"},
            synthesizer={"response": "test"},
            evaluator={"verdict": "PASS"},
            parser={},
            observer={},
            correction={},
        )

    @pytest.fixture
    def valid_session_metadata(self) -> SessionMetadata:
        """Create valid session metadata for testing."""
        return SessionMetadata(
            timestamp=datetime(2026, 1, 20, 15, 30, 45),
            input_type="QUERY",
        )

    def test_valid_feedback_record(
        self, valid_intermediate_outputs: IntermediateOutputs, valid_session_metadata: SessionMetadata
    ) -> None:
        """Test creating a valid feedback record."""
        record = FeedbackRecord(
            id="2026-01-20_a1b2c3d4",
            query="What was my running pace last week?",
            intermediate_outputs=valid_intermediate_outputs,
            final_response="Based on your logs, your average pace was 5:30/km.",
            user_feedback="Good answer!",
            session=valid_session_metadata,
        )
        assert record.id == "2026-01-20_a1b2c3d4"
        assert record.user_feedback == "Good answer!"
        assert record.feedback_sentiment is None

    def test_empty_feedback_allowed(
        self, valid_intermediate_outputs: IntermediateOutputs, valid_session_metadata: SessionMetadata
    ) -> None:
        """Test that empty user feedback is allowed (skip case)."""
        record = FeedbackRecord(
            id="2026-01-20_a1b2c3d4",
            query="What was my running pace?",
            intermediate_outputs=valid_intermediate_outputs,
            final_response="Your pace was 5:30/km.",
            user_feedback="",  # Empty is allowed
            session=valid_session_metadata,
        )
        assert record.user_feedback == ""

    def test_empty_query_rejected(
        self, valid_intermediate_outputs: IntermediateOutputs, valid_session_metadata: SessionMetadata
    ) -> None:
        """Test that empty query is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            FeedbackRecord(
                id="2026-01-20_a1b2c3d4",
                query="",  # Empty query not allowed
                intermediate_outputs=valid_intermediate_outputs,
                final_response="Some response",
                user_feedback="",
                session=valid_session_metadata,
            )
        assert "query" in str(exc_info.value)

    def test_empty_id_rejected(
        self, valid_intermediate_outputs: IntermediateOutputs, valid_session_metadata: SessionMetadata
    ) -> None:
        """Test that empty ID is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            FeedbackRecord(
                id="",  # Empty ID not allowed
                query="Some query",
                intermediate_outputs=valid_intermediate_outputs,
                final_response="Some response",
                user_feedback="",
                session=valid_session_metadata,
            )
        assert "id" in str(exc_info.value)

    def test_feedback_sentiment_optional(
        self, valid_intermediate_outputs: IntermediateOutputs, valid_session_metadata: SessionMetadata
    ) -> None:
        """Test that feedback_sentiment is optional."""
        record = FeedbackRecord(
            id="2026-01-20_a1b2c3d4",
            query="Test query",
            intermediate_outputs=valid_intermediate_outputs,
            final_response="Response",
            user_feedback="Great!",
            session=valid_session_metadata,
            feedback_sentiment="positive",
        )
        assert record.feedback_sentiment == "positive"


class TestGenerateFeedbackId:
    """Tests for generate_feedback_id function."""

    def test_generates_valid_format(self) -> None:
        """Test that ID follows YYYY-MM-DD_xxxxxxxx format."""
        feedback_id = generate_feedback_id("test query")
        parts = feedback_id.split("_")
        assert len(parts) == 2
        # Date part should be YYYY-MM-DD format
        date_part = parts[0]
        assert len(date_part) == 10
        assert date_part.count("-") == 2
        # Hash part should be 8 characters
        hash_part = parts[1]
        assert len(hash_part) == 8

    def test_same_query_same_hash(self) -> None:
        """Test that same query produces same hash."""
        id1 = generate_feedback_id("test query")
        id2 = generate_feedback_id("test query")
        # Same query on same day should have same hash part
        assert id1.split("_")[1] == id2.split("_")[1]

    def test_different_query_different_hash(self) -> None:
        """Test that different queries produce different hashes."""
        id1 = generate_feedback_id("test query one")
        id2 = generate_feedback_id("test query two")
        # Different queries should have different hash parts
        assert id1.split("_")[1] != id2.split("_")[1]

    def test_hash_is_hex(self) -> None:
        """Test that hash part is valid hexadecimal."""
        feedback_id = generate_feedback_id("any query")
        hash_part = feedback_id.split("_")[1]
        # Should be valid hex
        int(hash_part, 16)  # Raises ValueError if not valid hex


class TestGetUniqueFeedbackPath:
    """Tests for get_unique_feedback_path function."""

    def test_returns_base_path_when_no_conflict(self, tmp_path: Path) -> None:
        """Test that base path is returned when file doesn't exist."""
        path = get_unique_feedback_path(tmp_path, "2026-01-20_a1b2c3d4")
        assert path == tmp_path / "2026-01-20_a1b2c3d4.json"

    def test_appends_timestamp_on_conflict(self, tmp_path: Path) -> None:
        """Test that timestamp is appended when file exists."""
        # Create existing file
        existing = tmp_path / "2026-01-20_a1b2c3d4.json"
        existing.write_text("{}")

        path = get_unique_feedback_path(tmp_path, "2026-01-20_a1b2c3d4")
        # Should have timestamp appended
        assert path != existing
        assert path.name.startswith("2026-01-20_a1b2c3d4_")
        assert path.name.endswith(".json")
        # Timestamp should be 6 digits (HHMMSS)
        timestamp_part = path.stem.split("_")[-1]
        assert len(timestamp_part) == 6


class TestFeedbackRecorder:
    """Tests for FeedbackRecorder class."""

    @pytest.fixture
    def sample_feedback(self) -> FeedbackRecord:
        """Create a sample feedback record for testing."""
        return FeedbackRecord(
            id="2026-01-20_a1b2c3d4",
            query="What was my running pace?",
            intermediate_outputs=IntermediateOutputs(
                router={"input_type": "QUERY"},
                planner={"query": "test"},
                retriever={"entries": []},
                analyzer={"verdict": "SUFFICIENT"},
                synthesizer={"response": "test"},
                evaluator={"verdict": "PASS"},
                parser={},
                observer={},
                correction={},
            ),
            final_response="Your pace was 5:30/km.",
            user_feedback="Great answer!",
            session=SessionMetadata(
                timestamp=datetime(2026, 1, 20, 15, 30, 45),
                input_type="QUERY",
            ),
        )

    def test_get_feedback_dir(self, tmp_path: Path) -> None:
        """Test getting feedback directory."""
        recorder = FeedbackRecorder(feedback_dir=tmp_path)
        assert recorder.get_feedback_dir() == tmp_path

    def test_record_creates_file(self, tmp_path: Path, sample_feedback: FeedbackRecord) -> None:
        """Test that record() creates a JSON file."""
        recorder = FeedbackRecorder(feedback_dir=tmp_path)
        file_path = recorder.record(sample_feedback)

        assert file_path.exists()
        assert file_path.suffix == ".json"

    def test_record_file_content(self, tmp_path: Path, sample_feedback: FeedbackRecord) -> None:
        """Test that recorded file has correct content."""
        recorder = FeedbackRecorder(feedback_dir=tmp_path)
        file_path = recorder.record(sample_feedback)

        content = json.loads(file_path.read_text(encoding="utf-8"))
        assert content["id"] == "2026-01-20_a1b2c3d4"
        assert content["query"] == "What was my running pace?"
        assert content["user_feedback"] == "Great answer!"
        assert content["intermediate_outputs"]["router"]["input_type"] == "QUERY"

    def test_record_creates_directory_if_missing(self, tmp_path: Path, sample_feedback: FeedbackRecord) -> None:
        """Test that record() creates the directory if it doesn't exist."""
        feedback_dir = tmp_path / "nested" / "feedback"
        recorder = FeedbackRecorder(feedback_dir=feedback_dir)
        file_path = recorder.record(sample_feedback)

        assert file_path.exists()
        assert feedback_dir.exists()

    def test_record_handles_duplicate(self, tmp_path: Path, sample_feedback: FeedbackRecord) -> None:
        """Test that duplicate queries get unique file names."""
        recorder = FeedbackRecorder(feedback_dir=tmp_path)

        # Record first
        path1 = recorder.record(sample_feedback)

        # Record same feedback again (same id)
        path2 = recorder.record(sample_feedback)

        # Both should exist and be different files
        assert path1.exists()
        assert path2.exists()
        assert path1 != path2

    def test_record_unicode_content(self, tmp_path: Path) -> None:
        """Test that Unicode content is properly recorded."""
        feedback = FeedbackRecord(
            id="2026-01-20_korean",
            query="오늘 러닝 페이스가 어땠어?",
            intermediate_outputs=IntermediateOutputs(
                router={"input_type": "QUERY"},
                planner={"query": "러닝 페이스"},
                retriever={"entries": []},
                analyzer={"verdict": "SUFFICIENT"},
                synthesizer={"response": "평균 페이스는 5:30/km 입니다"},
                evaluator={"verdict": "PASS"},
                parser={},
                observer={},
                correction={},
            ),
            final_response="평균 페이스는 5:30/km 입니다",
            user_feedback="좋은 답변이에요!",
            session=SessionMetadata(
                timestamp=datetime(2026, 1, 20, 15, 30, 45),
                input_type="QUERY",
            ),
        )

        recorder = FeedbackRecorder(feedback_dir=tmp_path)
        file_path = recorder.record(feedback)

        content = json.loads(file_path.read_text(encoding="utf-8"))
        assert content["query"] == "오늘 러닝 페이스가 어땠어?"
        assert content["user_feedback"] == "좋은 답변이에요!"
