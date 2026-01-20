"""Unit tests for feedback recording infrastructure."""

import json
from datetime import datetime
from pathlib import Path

import pytest
from pydantic import ValidationError
from swealog.cli.feedback import (
    FeedbackRecord,
    FeedbackRecorder,
    IntermediateOutputs,
    SessionMetadata,
    generate_feedback_id,
    get_unique_feedback_path,
)


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

    def test_missing_field_raises_error(self) -> None:
        """Test that missing required fields raise validation error."""
        with pytest.raises(ValidationError) as exc_info:
            IntermediateOutputs(
                router={"input_type": "QUERY"},
                planner={"query": "test"},
                retriever={"entries": []},
                analyzer={"verdict": "SUFFICIENT"},
                # Missing synthesizer and evaluator
            )  # type: ignore[call-arg]
        assert "synthesizer" in str(exc_info.value) or "evaluator" in str(exc_info.value)


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
