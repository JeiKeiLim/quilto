"""Unit tests for quilto/models.py public API models."""

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError
from quilto.models import (
    AgentTrace,
    ClarificationQuestion,
    ProcessDebug,
    ProcessResult,
)


class TestClarificationQuestion:
    """Tests for ClarificationQuestion model."""

    def test_with_options(self) -> None:
        """ClarificationQuestion with options list is valid."""
        q = ClarificationQuestion(
            question="What muscle group?",
            options=["Chest", "Back", "Legs"],
        )
        assert q.question == "What muscle group?"
        assert q.options == ["Chest", "Back", "Legs"]

    def test_without_options(self) -> None:
        """ClarificationQuestion with None options is valid."""
        q = ClarificationQuestion(question="What is your goal?", options=None)
        assert q.question == "What is your goal?"
        assert q.options is None

    def test_options_default_none(self) -> None:
        """ClarificationQuestion defaults options to None."""
        q = ClarificationQuestion(question="How are you feeling?")
        assert q.options is None

    def test_empty_question_rejected(self) -> None:
        """ClarificationQuestion rejects empty question string."""
        with pytest.raises(ValidationError) as exc_info:
            ClarificationQuestion(question="")
        assert "String should have at least 1 character" in str(exc_info.value)


class TestAgentTrace:
    """Tests for AgentTrace model."""

    def test_valid_trace(self) -> None:
        """AgentTrace with valid fields is accepted."""
        now = datetime.now(UTC)
        trace = AgentTrace(
            agent_name="router",
            input_summary="User input: 'Did I run today?'",
            output_summary="Classified as QUERY",
            elapsed_ms=150.5,
            timestamp=now,
        )
        assert trace.agent_name == "router"
        assert trace.elapsed_ms == 150.5
        assert trace.timestamp == now

    def test_empty_agent_name_rejected(self) -> None:
        """AgentTrace rejects empty agent_name."""
        with pytest.raises(ValidationError) as exc_info:
            AgentTrace(
                agent_name="",
                input_summary="input",
                output_summary="output",
                elapsed_ms=100,
                timestamp=datetime.now(UTC),
            )
        assert "String should have at least 1 character" in str(exc_info.value)

    def test_negative_elapsed_ms_rejected(self) -> None:
        """AgentTrace rejects negative elapsed_ms."""
        with pytest.raises(ValidationError) as exc_info:
            AgentTrace(
                agent_name="planner",
                input_summary="input",
                output_summary="output",
                elapsed_ms=-1,
                timestamp=datetime.now(UTC),
            )
        assert "greater than or equal to 0" in str(exc_info.value)

    def test_zero_elapsed_ms_accepted(self) -> None:
        """AgentTrace accepts zero elapsed_ms."""
        trace = AgentTrace(
            agent_name="parser",
            input_summary="input",
            output_summary="output",
            elapsed_ms=0,
            timestamp=datetime.now(UTC),
        )
        assert trace.elapsed_ms == 0

    def test_empty_input_summary_rejected(self) -> None:
        """AgentTrace rejects empty input_summary."""
        with pytest.raises(ValidationError) as exc_info:
            AgentTrace(
                agent_name="router",
                input_summary="",
                output_summary="output",
                elapsed_ms=100,
                timestamp=datetime.now(UTC),
            )
        assert "String should have at least 1 character" in str(exc_info.value)

    def test_empty_output_summary_rejected(self) -> None:
        """AgentTrace rejects empty output_summary."""
        with pytest.raises(ValidationError) as exc_info:
            AgentTrace(
                agent_name="router",
                input_summary="input",
                output_summary="",
                elapsed_ms=100,
                timestamp=datetime.now(UTC),
            )
        assert "String should have at least 1 character" in str(exc_info.value)


class TestProcessDebug:
    """Tests for ProcessDebug model."""

    def test_default_instantiation(self) -> None:
        """ProcessDebug can be created with all defaults."""
        debug = ProcessDebug()
        assert debug.traces == []
        assert debug.total_elapsed_ms == 0
        assert debug.retry_count == 0

    def test_empty_traces_list(self) -> None:
        """ProcessDebug with empty traces list (default) is valid."""
        debug = ProcessDebug(total_elapsed_ms=500)
        assert debug.traces == []
        assert debug.total_elapsed_ms == 500
        assert debug.retry_count == 0

    def test_with_populated_traces(self) -> None:
        """ProcessDebug with populated traces list is valid."""
        now = datetime.now(UTC)
        trace1 = AgentTrace(
            agent_name="router",
            input_summary="input1",
            output_summary="output1",
            elapsed_ms=100,
            timestamp=now,
        )
        trace2 = AgentTrace(
            agent_name="planner",
            input_summary="input2",
            output_summary="output2",
            elapsed_ms=200,
            timestamp=now,
        )
        debug = ProcessDebug(
            traces=[trace1, trace2],
            total_elapsed_ms=300,
            retry_count=1,
        )
        assert len(debug.traces) == 2
        assert debug.traces[0].agent_name == "router"
        assert debug.traces[1].agent_name == "planner"
        assert debug.retry_count == 1

    def test_negative_total_elapsed_ms_rejected(self) -> None:
        """ProcessDebug rejects negative total_elapsed_ms."""
        with pytest.raises(ValidationError) as exc_info:
            ProcessDebug(total_elapsed_ms=-100)
        assert "greater than or equal to 0" in str(exc_info.value)

    def test_negative_retry_count_rejected(self) -> None:
        """ProcessDebug rejects negative retry_count."""
        with pytest.raises(ValidationError) as exc_info:
            ProcessDebug(total_elapsed_ms=100, retry_count=-1)
        assert "greater than or equal to 0" in str(exc_info.value)


class TestProcessResult:
    """Tests for ProcessResult model."""

    def test_valid_log_result(self) -> None:
        """ProcessResult for LOG input is valid."""
        result = ProcessResult(
            input_type="log",
            parsed_data={"type": "running", "distance_km": 5.0},
            selected_domains=["running"],
        )
        assert result.input_type == "log"
        assert result.parsed_data == {"type": "running", "distance_km": 5.0}
        assert result.response is None
        assert result.confidence is None

    def test_valid_query_result(self) -> None:
        """ProcessResult for QUERY input is valid."""
        result = ProcessResult(
            input_type="query",
            response="You ran 5km yesterday.",
            confidence=0.85,
            source_entry_ids=["entry-001", "entry-002"],
            selected_domains=["running"],
        )
        assert result.input_type == "query"
        assert result.response == "You ran 5km yesterday."
        assert result.confidence == 0.85
        assert result.source_entry_ids == ["entry-001", "entry-002"]

    def test_valid_both_result(self) -> None:
        """ProcessResult for BOTH input is valid."""
        result = ProcessResult(
            input_type="both",
            response="Logged and analyzed.",
            confidence=0.9,
            parsed_data={"workout": "completed"},
            selected_domains=["general_fitness"],
        )
        assert result.input_type == "both"
        assert result.response is not None
        assert result.parsed_data is not None

    def test_valid_correction_result(self) -> None:
        """ProcessResult for CORRECTION input is valid."""
        result = ProcessResult(
            input_type="correction",
            parsed_data={"corrected_distance": 6.0},
        )
        assert result.input_type == "correction"

    def test_confidence_below_zero_rejected(self) -> None:
        """ProcessResult rejects confidence below 0."""
        with pytest.raises(ValidationError) as exc_info:
            ProcessResult(input_type="query", confidence=-0.1)
        assert "greater than or equal to 0" in str(exc_info.value)

    def test_confidence_above_one_rejected(self) -> None:
        """ProcessResult rejects confidence above 1."""
        with pytest.raises(ValidationError) as exc_info:
            ProcessResult(input_type="query", confidence=1.1)
        assert "less than or equal to 1" in str(exc_info.value)

    def test_confidence_bounds_accepted(self) -> None:
        """ProcessResult accepts confidence at exact bounds (0.0 and 1.0)."""
        result_low = ProcessResult(input_type="query", confidence=0.0)
        result_high = ProcessResult(input_type="query", confidence=1.0)
        assert result_low.confidence == 0.0
        assert result_high.confidence == 1.0

    def test_with_clarification_questions(self) -> None:
        """ProcessResult with clarification_questions is valid."""
        questions = [
            ClarificationQuestion(question="What workout type?", options=["Run", "Gym"]),
            ClarificationQuestion(question="How long?"),
        ]
        result = ProcessResult(
            input_type="query",
            clarification_questions=questions,
        )
        assert result.clarification_questions is not None
        assert len(result.clarification_questions) == 2

    def test_with_debug_info(self) -> None:
        """ProcessResult with debug info is valid."""
        debug = ProcessDebug(total_elapsed_ms=1000, retry_count=0)
        result = ProcessResult(
            input_type="log",
            parsed_data={"note": "test"},
            debug=debug,
        )
        assert result.debug is not None
        assert result.debug.total_elapsed_ms == 1000

    def test_invalid_input_type_rejected(self) -> None:
        """ProcessResult rejects invalid input_type."""
        with pytest.raises(ValidationError) as exc_info:
            ProcessResult(input_type="invalid")  # type: ignore[arg-type]
        assert "Input should be 'log', 'query', 'both' or 'correction'" in str(exc_info.value)

    def test_default_empty_lists(self) -> None:
        """ProcessResult defaults lists to empty."""
        result = ProcessResult(input_type="log")
        assert result.source_entry_ids == []
        assert result.selected_domains == []

    def test_default_lists_are_isolated(self) -> None:
        """ProcessResult instances don't share default list references."""
        result1 = ProcessResult(input_type="log")
        result2 = ProcessResult(input_type="query")

        # Mutating one should not affect the other
        result1.source_entry_ids.append("entry-1")
        result1.selected_domains.append("running")

        assert result2.source_entry_ids == []
        assert result2.selected_domains == []
        assert result1.source_entry_ids == ["entry-1"]
        assert result1.selected_domains == ["running"]
