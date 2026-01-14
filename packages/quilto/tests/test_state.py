"""Tests for quilto.state module.

Tests cover:
- SessionState TypedDict instantiation
- UserClarificationResponse validation
- enter_wait_user function with interrupt mock
- process_user_response function
- Routing functions for state transitions
- All exports importable from quilto.state
"""

from collections.abc import Generator
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from pydantic import ValidationError
from quilto.state import (
    SessionState,
    UserClarificationResponse,
    enter_wait_user,
    process_user_response,
    route_after_clarify,
    route_after_wait_user,
)

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def sample_state() -> SessionState:
    """Create a sample SessionState for testing."""
    return SessionState(
        raw_input="How am I feeling today?",
        input_type="QUERY",
        query="How am I feeling today?",
        query_type="simple",
        current_state="CLARIFY",
        waiting_for_user=False,
        complete=False,
        retry_count=0,
        max_retries=2,
        clarification_questions=[],
        user_responses={},
        gaps=[],
    )


@pytest.fixture
def sample_clarifier_output() -> dict[str, Any]:
    """Create a sample ClarifierOutput dict for testing."""
    return {
        "questions": [
            {
                "question": "What is your current energy level?",
                "gap_addressed": "energy_level",
                "options": ["High", "Medium", "Low"],
                "required": True,
            },
            {
                "question": "How did you sleep last night?",
                "gap_addressed": "sleep_quality",
                "options": None,
                "required": False,
            },
        ],
        "context_explanation": "To provide personalized advice, I need to understand your current state.",
        "fallback_action": "Provide general wellness recommendations based on available data.",
    }


@pytest.fixture
def mock_interrupt() -> Generator[MagicMock]:
    """Mock LangGraph interrupt for unit testing."""
    with patch("quilto.state.wait_user.interrupt") as mock:
        mock.return_value = {"responses": {"energy_level": "tired"}, "declined": False}
        yield mock


# =============================================================================
# Test SessionState TypedDict
# =============================================================================


class TestSessionState:
    """Tests for SessionState TypedDict."""

    def test_instantiate_with_all_fields(self) -> None:
        """Test SessionState can be instantiated with all fields."""
        state: SessionState = {
            "raw_input": "Test input",
            "input_type": "QUERY",
            "query": "Test query",
            "query_type": "simple",
            "retrieval_history": [],
            "retrieved_entries": [],
            "analysis": None,
            "gaps": [],
            "draft_response": None,
            "evaluation": None,
            "retry_count": 0,
            "max_retries": 2,
            "clarification_questions": [],
            "clarifier_output": None,
            "user_responses": {},
            "waiting_for_user": False,
            "current_state": "ROUTE",
            "next_state": None,
            "final_response": None,
            "complete": False,
        }

        assert state["raw_input"] == "Test input"
        assert state["input_type"] == "QUERY"
        assert state["waiting_for_user"] is False
        assert state["complete"] is False

    def test_instantiate_with_minimal_fields(self) -> None:
        """Test SessionState works with partial fields (total=False)."""
        state: SessionState = {
            "raw_input": "Test",
            "current_state": "ROUTE",
        }

        assert state["raw_input"] == "Test"
        assert state["current_state"] == "ROUTE"
        assert state.get("query") is None

    def test_clarification_fields_present(self) -> None:
        """Test clarification-related fields are defined."""
        state: SessionState = {
            "clarification_questions": [{"question": "Test?", "gap_addressed": "test"}],
            "clarifier_output": {"questions": [], "context_explanation": "x", "fallback_action": "y"},
            "user_responses": {"test": "answer"},
            "waiting_for_user": True,
        }

        assert len(state["clarification_questions"]) == 1
        assert state["user_responses"]["test"] == "answer"
        assert state["waiting_for_user"] is True

    def test_current_state_field(self) -> None:
        """Test current_state tracks state machine position."""
        state: SessionState = {
            "current_state": "WAIT_USER",
        }

        assert state["current_state"] == "WAIT_USER"


# =============================================================================
# Test UserClarificationResponse Model
# =============================================================================


class TestUserClarificationResponse:
    """Tests for UserClarificationResponse Pydantic model."""

    def test_valid_response_with_answers(self) -> None:
        """Test valid response with user answers."""
        response = UserClarificationResponse(
            responses={"energy_level": "tired", "sleep_quality": "poor"},
            declined=False,
        )

        assert response.responses == {"energy_level": "tired", "sleep_quality": "poor"}
        assert response.declined is False

    def test_declined_clears_responses(self) -> None:
        """Test that declined=True clears responses."""
        response = UserClarificationResponse(
            responses={"energy_level": "tired"},
            declined=True,
        )

        assert response.responses == {}
        assert response.declined is True

    def test_empty_responses_valid(self) -> None:
        """Test empty responses dict is valid."""
        response = UserClarificationResponse(
            responses={},
            declined=False,
        )

        assert response.responses == {}
        assert response.declined is False

    def test_declined_default_false(self) -> None:
        """Test declined defaults to False."""
        response = UserClarificationResponse(responses={"test": "answer"})

        assert response.declined is False

    def test_strict_mode_rejects_extra_fields(self) -> None:
        """Test strict mode rejects extra fields."""
        with pytest.raises(ValidationError):
            UserClarificationResponse(
                responses={},
                declined=False,
                extra_field="not allowed",  # pyright: ignore[reportCallIssue]
            )

    def test_declined_with_empty_responses_unchanged(self) -> None:
        """Test declined with already empty responses stays empty."""
        response = UserClarificationResponse(
            responses={},
            declined=True,
        )

        assert response.responses == {}
        assert response.declined is True


# =============================================================================
# Test enter_wait_user Function
# =============================================================================


class TestEnterWaitUser:
    """Tests for enter_wait_user function."""

    def test_stores_clarification_questions(
        self, mock_interrupt: MagicMock, sample_state: SessionState, sample_clarifier_output: dict[str, Any]
    ) -> None:
        """Test that enter_wait_user stores clarification questions correctly."""
        result = enter_wait_user(sample_state, sample_clarifier_output)

        # Check state was updated with clarification info
        assert result.get("clarifier_output") == sample_clarifier_output
        assert result.get("clarification_questions") == sample_clarifier_output["questions"]

    def test_calls_interrupt_with_correct_payload(
        self, mock_interrupt: MagicMock, sample_state: SessionState, sample_clarifier_output: dict[str, Any]
    ) -> None:
        """Test that enter_wait_user calls interrupt with correct payload."""
        enter_wait_user(sample_state, sample_clarifier_output)

        mock_interrupt.assert_called_once()
        call_kwargs: dict[str, Any] = mock_interrupt.call_args[1]
        payload: dict[str, Any] = call_kwargs["value"]

        assert "questions" in payload
        assert "context" in payload
        assert "fallback" in payload
        assert payload["questions"] == sample_clarifier_output["questions"]
        assert payload["context"] == sample_clarifier_output["context_explanation"]
        assert payload["fallback"] == sample_clarifier_output["fallback_action"]

    def test_sets_current_state_correctly(
        self, mock_interrupt: MagicMock, sample_state: SessionState, sample_clarifier_output: dict[str, Any]
    ) -> None:
        """Test that current_state is tracked through WAIT_USER flow."""
        # Mock returns user response, so state continues processing
        mock_interrupt.return_value = {"responses": {"test": "answer"}, "declined": False}

        result = enter_wait_user(sample_state, sample_clarifier_output)

        # After processing, waiting_for_user should be cleared
        assert result.get("waiting_for_user") is False
        # current_state should be updated to WAIT_USER_DONE after processing
        assert result.get("current_state") == "WAIT_USER_DONE"

    def test_processes_mock_response(
        self, mock_interrupt: MagicMock, sample_state: SessionState, sample_clarifier_output: dict[str, Any]
    ) -> None:
        """Test that mock response is processed correctly."""
        mock_interrupt.return_value = {"responses": {"energy_level": "high"}, "declined": False}

        result = enter_wait_user(sample_state, sample_clarifier_output)

        assert result.get("user_responses") == {"energy_level": "high"}
        assert result.get("next_state") == "analyze"

    def test_processes_declined_response(
        self, mock_interrupt: MagicMock, sample_state: SessionState, sample_clarifier_output: dict[str, Any]
    ) -> None:
        """Test that declined response routes to synthesize."""
        mock_interrupt.return_value = {"responses": {}, "declined": True}

        result = enter_wait_user(sample_state, sample_clarifier_output)

        assert result.get("user_responses") == {}
        assert result.get("next_state") == "synthesize"

    def test_handles_empty_clarifier_output(self, mock_interrupt: MagicMock, sample_state: SessionState) -> None:
        """Test handling of minimal clarifier output."""
        minimal_output: dict[str, Any] = {
            "questions": [],
            "context_explanation": "",
            "fallback_action": "",
        }
        mock_interrupt.return_value = {"responses": {}, "declined": True}

        result = enter_wait_user(sample_state, minimal_output)

        assert result.get("clarification_questions") == []


# =============================================================================
# Test process_user_response Function
# =============================================================================


class TestProcessUserResponse:
    """Tests for process_user_response function."""

    def test_with_provided_responses_routes_to_analyze(self, sample_state: SessionState) -> None:
        """Test that provided responses route to analyze."""
        sample_state["waiting_for_user"] = True
        sample_state["current_state"] = "WAIT_USER"

        user_input: dict[str, Any] = {"responses": {"energy_level": "tired", "mood": "happy"}, "declined": False}

        result = process_user_response(sample_state, user_input)

        assert result.get("user_responses") == {"energy_level": "tired", "mood": "happy"}
        assert result.get("next_state") == "analyze"
        assert result.get("waiting_for_user") is False

    def test_with_declined_routes_to_synthesize(self, sample_state: SessionState) -> None:
        """Test that declined routes to synthesize."""
        sample_state["waiting_for_user"] = True
        sample_state["current_state"] = "WAIT_USER"

        user_input: dict[str, Any] = {"responses": {}, "declined": True}

        result = process_user_response(sample_state, user_input)

        assert result.get("user_responses") == {}
        assert result.get("next_state") == "synthesize"
        assert result.get("waiting_for_user") is False

    def test_clears_waiting_for_user_flag(self, sample_state: SessionState) -> None:
        """Test that waiting_for_user is always cleared."""
        sample_state["waiting_for_user"] = True

        user_input: dict[str, Any] = {"responses": {"test": "answer"}, "declined": False}

        result = process_user_response(sample_state, user_input)

        assert result.get("waiting_for_user") is False

    def test_empty_responses_with_declined_false(self, sample_state: SessionState) -> None:
        """Test empty responses dict with declined=False still routes to analyze."""
        sample_state["waiting_for_user"] = True

        user_input: dict[str, Any] = {"responses": {}, "declined": False}

        result = process_user_response(sample_state, user_input)

        assert result.get("user_responses") == {}
        assert result.get("next_state") == "analyze"

    def test_preserves_other_state_fields(self, sample_state: SessionState) -> None:
        """Test that other state fields are preserved."""
        sample_state["raw_input"] = "Original input"
        sample_state["gaps"] = [{"description": "test gap"}]

        user_input: dict[str, Any] = {"responses": {"test": "answer"}, "declined": False}

        result = process_user_response(sample_state, user_input)

        assert result.get("raw_input") == "Original input"
        assert result.get("gaps") == [{"description": "test gap"}]

    def test_sets_current_state_to_wait_user_done(self, sample_state: SessionState) -> None:
        """Test that current_state is set to WAIT_USER_DONE after processing."""
        sample_state["current_state"] = "WAIT_USER"
        sample_state["waiting_for_user"] = True

        user_input: dict[str, Any] = {"responses": {"test": "answer"}, "declined": False}

        result = process_user_response(sample_state, user_input)

        assert result.get("current_state") == "WAIT_USER_DONE"

    def test_sets_current_state_to_wait_user_done_on_decline(self, sample_state: SessionState) -> None:
        """Test that current_state is set to WAIT_USER_DONE even when declined."""
        sample_state["current_state"] = "WAIT_USER"
        sample_state["waiting_for_user"] = True

        user_input: dict[str, Any] = {"responses": {}, "declined": True}

        result = process_user_response(sample_state, user_input)

        assert result.get("current_state") == "WAIT_USER_DONE"


# =============================================================================
# Test Routing Functions
# =============================================================================


class TestRouteAfterClarify:
    """Tests for route_after_clarify function."""

    def test_always_returns_wait_user(self, sample_state: SessionState) -> None:
        """Test that route_after_clarify always returns wait_user."""
        result = route_after_clarify(sample_state)

        assert result == "wait_user"

    def test_ignores_state_content(self) -> None:
        """Test that state content is ignored."""
        empty_state: SessionState = {}  # pyright: ignore[reportAssignmentType]

        result = route_after_clarify(empty_state)

        assert result == "wait_user"


class TestRouteAfterWaitUser:
    """Tests for route_after_wait_user function."""

    def test_returns_analyze_when_responses_provided(self, sample_state: SessionState) -> None:
        """Test returns analyze when next_state is analyze."""
        sample_state["next_state"] = "analyze"
        sample_state["user_responses"] = {"test": "answer"}

        result = route_after_wait_user(sample_state)

        assert result == "analyze"

    def test_returns_synthesize_when_declined(self, sample_state: SessionState) -> None:
        """Test returns synthesize when next_state is synthesize."""
        sample_state["next_state"] = "synthesize"
        sample_state["user_responses"] = {}

        result = route_after_wait_user(sample_state)

        assert result == "synthesize"

    def test_defaults_to_synthesize_when_next_state_none(self, sample_state: SessionState) -> None:
        """Test defaults to synthesize when next_state is None."""
        sample_state["next_state"] = None

        result = route_after_wait_user(sample_state)

        assert result == "synthesize"

    def test_defaults_to_synthesize_when_next_state_missing(self) -> None:
        """Test defaults to synthesize when next_state key is missing."""
        state: SessionState = {"current_state": "WAIT_USER"}  # pyright: ignore[reportAssignmentType]

        result = route_after_wait_user(state)

        assert result == "synthesize"


# =============================================================================
# Test Module Exports
# =============================================================================


class TestModuleExports:
    """Tests for module exports."""

    def test_all_exports_importable_from_quilto_state(self) -> None:
        """Test all exports are importable from quilto.state."""
        from quilto.state import (
            SessionState as SS,
        )
        from quilto.state import (
            UserClarificationResponse as UCR,
        )
        from quilto.state import (
            enter_wait_user as ewu,
        )
        from quilto.state import (
            process_user_response as pur,
        )
        from quilto.state import (
            route_after_clarify as rac,
        )
        from quilto.state import (
            route_after_wait_user as rawu,
        )

        assert SS is not None
        assert UCR is not None
        assert callable(ewu)
        assert callable(pur)
        assert callable(rac)
        assert callable(rawu)

    def test_all_exports_importable_from_quilto(self) -> None:
        """Test state exports are importable from main quilto package."""
        from quilto import (
            SessionState as SS,
        )
        from quilto import (
            UserClarificationResponse as UCR,
        )
        from quilto import (
            enter_wait_user as ewu,
        )
        from quilto import (
            process_user_response as pur,
        )
        from quilto import (
            route_after_clarify as rac,
        )
        from quilto import (
            route_after_wait_user as rawu,
        )

        assert SS is not None
        assert UCR is not None
        assert callable(ewu)
        assert callable(pur)
        assert callable(rac)
        assert callable(rawu)


# =============================================================================
# Test State Transitions (Integration-level)
# =============================================================================


class TestStateTransitions:
    """Tests verifying state transitions per AC #7."""

    def test_clarify_to_wait_user_to_analyze_transition(
        self, mock_interrupt: MagicMock, sample_state: SessionState, sample_clarifier_output: dict[str, Any]
    ) -> None:
        """Test CLARIFY -> WAIT_USER -> ANALYZE transition."""
        # Start in CLARIFY state
        sample_state["current_state"] = "CLARIFY"

        # Route after clarify -> should go to wait_user
        next_node = route_after_clarify(sample_state)
        assert next_node == "wait_user"

        # Mock user provides responses
        mock_interrupt.return_value = {"responses": {"energy_level": "high"}, "declined": False}

        # Enter wait_user state
        result = enter_wait_user(sample_state, sample_clarifier_output)

        # Verify current_state tracking
        assert result.get("current_state") == "WAIT_USER_DONE"

        # Route after wait_user -> should go to analyze (responses provided)
        next_node = route_after_wait_user(result)
        assert next_node == "analyze"

    def test_clarify_to_wait_user_to_synthesize_transition(
        self, mock_interrupt: MagicMock, sample_state: SessionState, sample_clarifier_output: dict[str, Any]
    ) -> None:
        """Test CLARIFY -> WAIT_USER -> SYNTHESIZE transition."""
        # Start in CLARIFY state
        sample_state["current_state"] = "CLARIFY"

        # Route after clarify -> should go to wait_user
        next_node = route_after_clarify(sample_state)
        assert next_node == "wait_user"

        # Mock user declines
        mock_interrupt.return_value = {"responses": {}, "declined": True}

        # Enter wait_user state
        result = enter_wait_user(sample_state, sample_clarifier_output)

        # Verify current_state tracking
        assert result.get("current_state") == "WAIT_USER_DONE"

        # Route after wait_user -> should go to synthesize (declined)
        next_node = route_after_wait_user(result)
        assert next_node == "synthesize"
