"""Unit tests for expand_domain_node function.

Tests cover:
- Valid domain expansion requests
- Filtering out already-expanded domains (history check)
- Logging warnings for invalid domains
- Routing to clarify/synthesize when no new domains
- Setting is_partial flag on expansion failure
- Handling active_domain_context=None (AC #7)
"""

import logging

import pytest
from pydantic import BaseModel
from quilto import DomainModule, DomainSelector
from quilto.state import SessionState, expand_domain_node


class MockSchema(BaseModel):
    """Simple schema for testing."""

    value: str | None = None


@pytest.fixture
def domain_strength() -> DomainModule:
    """Create strength domain for testing."""
    return DomainModule(
        name="strength",
        description="Strength training domain",
        log_schema=MockSchema,
        vocabulary={"rep": "repetition", "set": "a group of reps"},
        expertise="Strength training expertise for weightlifting",
        response_evaluation_rules=["Verify form advice"],
        context_management_guidance="Track progressive overload",
        clarification_patterns={"SUBJECTIVE": ["How intense was the workout?"]},
    )


@pytest.fixture
def domain_nutrition() -> DomainModule:
    """Create nutrition domain for testing."""
    return DomainModule(
        name="nutrition",
        description="Nutrition and diet domain",
        log_schema=MockSchema,
        vocabulary={"macro": "macronutrient", "calorie": "unit of energy"},
        expertise="Nutrition expertise for diet planning",
        response_evaluation_rules=["Verify nutritional accuracy"],
        context_management_guidance="Track daily intake",
        clarification_patterns={"SUBJECTIVE": ["How do you feel after eating?"]},
    )


@pytest.fixture
def domain_running() -> DomainModule:
    """Create running domain for testing."""
    return DomainModule(
        name="running",
        description="Running and cardio domain",
        log_schema=MockSchema,
        vocabulary={"pace": "speed per distance", "cadence": "steps per minute"},
        expertise="Running expertise for cardio training",
        response_evaluation_rules=["Verify pace advice"],
        context_management_guidance="Track mileage",
        clarification_patterns={"SUBJECTIVE": ["How was your run?"]},
    )


@pytest.fixture
def selector(
    domain_strength: DomainModule,
    domain_nutrition: DomainModule,
    domain_running: DomainModule,
) -> DomainSelector:
    """Create DomainSelector with all test domains."""
    return DomainSelector([domain_strength, domain_nutrition, domain_running])


@pytest.fixture
def state_with_strength_context(selector: DomainSelector) -> SessionState:
    """Create state with strength domain already active."""
    context = selector.build_active_context(["strength"])
    return SessionState(
        raw_input="How is my nutrition?",
        current_state="EXPAND_DOMAIN",
        active_domain_context=context.model_dump(),
        domain_expansion_request=["nutrition"],
        domain_expansion_history=[],
        gaps=[],
    )


class TestExpandDomainNodeValidExpansion:
    """Tests for valid domain expansion scenarios (AC #3)."""

    def test_expands_single_domain(
        self, selector: DomainSelector, state_with_strength_context: SessionState
    ) -> None:
        """expand_domain_node adds requested domain to context."""
        result = expand_domain_node(state_with_strength_context, selector)

        assert result["next_state"] == "plan"
        assert "nutrition" in result["domain_expansion_history"]
        assert result["domain_expansion_request"] is None

    def test_rebuilds_active_context(
        self, selector: DomainSelector, state_with_strength_context: SessionState
    ) -> None:
        """expand_domain_node rebuilds ActiveDomainContext with merged domains."""
        result = expand_domain_node(state_with_strength_context, selector)

        new_context = result["active_domain_context"]
        assert "strength" in new_context["domains_loaded"]
        assert "nutrition" in new_context["domains_loaded"]
        # Vocabulary from both domains merged
        assert "rep" in new_context["vocabulary"]
        assert "macro" in new_context["vocabulary"]

    def test_appends_to_history(
        self, selector: DomainSelector, state_with_strength_context: SessionState
    ) -> None:
        """expand_domain_node appends new domains to history."""
        state_with_strength_context["domain_expansion_history"] = ["running"]
        state_with_strength_context["domain_expansion_request"] = ["nutrition"]

        result = expand_domain_node(state_with_strength_context, selector)

        assert result["domain_expansion_history"] == ["running", "nutrition"]

    def test_logs_expansion_info(
        self,
        selector: DomainSelector,
        state_with_strength_context: SessionState,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """expand_domain_node logs expansion for debugging (AC #1)."""
        with caplog.at_level(logging.INFO):
            expand_domain_node(state_with_strength_context, selector)

        assert "Domain expansion: adding" in caplog.text
        assert "nutrition" in caplog.text


class TestExpandDomainNodeHistoryFilter:
    """Tests for filtering domains already in history (AC #4)."""

    def test_filters_out_domains_in_history(
        self, selector: DomainSelector, state_with_strength_context: SessionState
    ) -> None:
        """expand_domain_node skips domains already in history."""
        state_with_strength_context["domain_expansion_history"] = ["nutrition"]
        state_with_strength_context["domain_expansion_request"] = ["nutrition"]

        result = expand_domain_node(state_with_strength_context, selector)

        # No new domains, should route to synthesize (no gaps)
        assert result["next_state"] == "synthesize"
        assert result["is_partial"] is True

    def test_partial_history_filter(
        self, selector: DomainSelector, state_with_strength_context: SessionState
    ) -> None:
        """expand_domain_node expands only domains not in history."""
        state_with_strength_context["domain_expansion_history"] = ["nutrition"]
        state_with_strength_context["domain_expansion_request"] = [
            "nutrition",
            "running",
        ]

        result = expand_domain_node(state_with_strength_context, selector)

        assert result["next_state"] == "plan"
        # Only running should be added
        assert "running" in result["domain_expansion_history"]
        assert result["domain_expansion_history"].count("nutrition") == 1

    def test_accumulates_across_expansions(
        self, selector: DomainSelector, state_with_strength_context: SessionState
    ) -> None:
        """domain_expansion_history accumulates across multiple expansions (Subtask 6.11)."""
        # First expansion adds nutrition
        state_with_strength_context["domain_expansion_request"] = ["nutrition"]
        result1 = expand_domain_node(state_with_strength_context, selector)

        # Second expansion with same state (simulating retry)
        state_with_strength_context["domain_expansion_history"] = result1[
            "domain_expansion_history"
        ]
        state_with_strength_context["domain_expansion_request"] = ["running"]
        result2 = expand_domain_node(state_with_strength_context, selector)

        # History should have both
        assert result2["domain_expansion_history"] == ["nutrition", "running"]


class TestExpandDomainNodeInvalidDomains:
    """Tests for handling invalid domain names (AC #6)."""

    def test_logs_warning_for_invalid_domain(
        self,
        selector: DomainSelector,
        state_with_strength_context: SessionState,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """expand_domain_node logs warning for invalid domains (Subtask 6.3)."""
        state_with_strength_context["domain_expansion_request"] = ["unknown_domain"]

        with caplog.at_level(logging.WARNING):
            expand_domain_node(state_with_strength_context, selector)

        assert "unknown_domain" in caplog.text
        assert "not in available domains" in caplog.text

    def test_skips_invalid_expands_valid(
        self, selector: DomainSelector, state_with_strength_context: SessionState
    ) -> None:
        """expand_domain_node skips invalid, expands valid domains."""
        state_with_strength_context["domain_expansion_request"] = [
            "unknown_domain",
            "nutrition",
        ]

        result = expand_domain_node(state_with_strength_context, selector)

        assert result["next_state"] == "plan"
        assert "nutrition" in result["domain_expansion_history"]
        assert "unknown_domain" not in result["domain_expansion_history"]

    def test_all_invalid_domains(
        self, selector: DomainSelector, state_with_strength_context: SessionState
    ) -> None:
        """expand_domain_node handles all invalid domains gracefully."""
        state_with_strength_context["domain_expansion_request"] = [
            "unknown1",
            "unknown2",
        ]

        result = expand_domain_node(state_with_strength_context, selector)

        assert result["is_partial"] is True
        assert result["next_state"] == "synthesize"


class TestExpandDomainNodeNoNewDomains:
    """Tests for routing when no new domains can be added (AC #4)."""

    def test_routes_to_clarify_with_gaps(
        self, selector: DomainSelector, state_with_strength_context: SessionState
    ) -> None:
        """Routes to clarify when no new domains and has non-retrievable gaps (Subtask 6.4)."""
        state_with_strength_context["domain_expansion_history"] = ["nutrition"]
        state_with_strength_context["domain_expansion_request"] = ["nutrition"]
        state_with_strength_context["gaps"] = [
            {"gap_type": "subjective", "description": "How do you feel?"}
        ]

        result = expand_domain_node(state_with_strength_context, selector)

        assert result["next_state"] == "clarify"
        assert result["is_partial"] is True

    def test_routes_to_synthesize_without_gaps(
        self, selector: DomainSelector, state_with_strength_context: SessionState
    ) -> None:
        """Routes to synthesize when no new domains and no non-retrievable gaps (Subtask 6.5)."""
        state_with_strength_context["domain_expansion_history"] = ["nutrition"]
        state_with_strength_context["domain_expansion_request"] = ["nutrition"]
        state_with_strength_context["gaps"] = []

        result = expand_domain_node(state_with_strength_context, selector)

        assert result["next_state"] == "synthesize"
        assert result["is_partial"] is True

    def test_clarification_gap_routes_to_clarify(
        self, selector: DomainSelector, state_with_strength_context: SessionState
    ) -> None:
        """Gaps with gap_type='clarification' route to clarify."""
        state_with_strength_context["domain_expansion_history"] = ["nutrition"]
        state_with_strength_context["domain_expansion_request"] = ["nutrition"]
        state_with_strength_context["gaps"] = [
            {"gap_type": "clarification", "description": "Which exercise?"}
        ]

        result = expand_domain_node(state_with_strength_context, selector)

        assert result["next_state"] == "clarify"

    def test_factual_gap_routes_to_synthesize(
        self, selector: DomainSelector, state_with_strength_context: SessionState
    ) -> None:
        """Gaps with gap_type='factual' don't trigger clarify."""
        state_with_strength_context["domain_expansion_history"] = ["nutrition"]
        state_with_strength_context["domain_expansion_request"] = ["nutrition"]
        state_with_strength_context["gaps"] = [
            {"gap_type": "factual", "description": "Missing data"}
        ]

        result = expand_domain_node(state_with_strength_context, selector)

        assert result["next_state"] == "synthesize"


class TestExpandDomainNodeIsPartial:
    """Tests for is_partial flag setting (Subtask 6.6)."""

    def test_sets_is_partial_when_expansion_fails(
        self, selector: DomainSelector, state_with_strength_context: SessionState
    ) -> None:
        """Sets is_partial=True when expansion fails."""
        state_with_strength_context["domain_expansion_history"] = ["nutrition"]
        state_with_strength_context["domain_expansion_request"] = ["nutrition"]

        result = expand_domain_node(state_with_strength_context, selector)

        assert result["is_partial"] is True

    def test_does_not_set_is_partial_on_success(
        self, selector: DomainSelector, state_with_strength_context: SessionState
    ) -> None:
        """Does not set is_partial on successful expansion."""
        result = expand_domain_node(state_with_strength_context, selector)

        assert "is_partial" not in result


class TestExpandDomainNodeNoneContext:
    """Tests for handling active_domain_context=None (AC #7)."""

    def test_handles_none_context(
        self, selector: DomainSelector, domain_nutrition: DomainModule
    ) -> None:
        """expand_domain_node handles active_domain_context=None (Subtask 6.7)."""
        state: SessionState = SessionState(
            raw_input="Test",
            current_state="EXPAND_DOMAIN",
            active_domain_context=None,
            domain_expansion_request=["nutrition"],
            domain_expansion_history=[],
            gaps=[],
        )

        result = expand_domain_node(state, selector)

        assert result["next_state"] == "plan"
        assert "nutrition" in result["domain_expansion_history"]
        assert result["active_domain_context"]["domains_loaded"] == ["nutrition"]

    def test_handles_missing_domains_loaded(
        self, selector: DomainSelector
    ) -> None:
        """expand_domain_node handles active_domain_context without domains_loaded."""
        state: SessionState = SessionState(
            raw_input="Test",
            current_state="EXPAND_DOMAIN",
            active_domain_context={},  # Empty dict, no domains_loaded key
            domain_expansion_request=["nutrition"],
            domain_expansion_history=[],
            gaps=[],
        )

        result = expand_domain_node(state, selector)

        assert result["next_state"] == "plan"
        assert "nutrition" in result["active_domain_context"]["domains_loaded"]


class TestExpandDomainNodeEmptyRequest:
    """Tests for empty domain expansion request."""

    def test_empty_request_list(
        self, selector: DomainSelector, state_with_strength_context: SessionState
    ) -> None:
        """expand_domain_node handles empty request list."""
        state_with_strength_context["domain_expansion_request"] = []

        result = expand_domain_node(state_with_strength_context, selector)

        assert result["is_partial"] is True
        assert result["next_state"] == "synthesize"

    def test_none_request(
        self, selector: DomainSelector, state_with_strength_context: SessionState
    ) -> None:
        """expand_domain_node handles None request."""
        state_with_strength_context["domain_expansion_request"] = None

        result = expand_domain_node(state_with_strength_context, selector)

        assert result["is_partial"] is True
        assert result["next_state"] == "synthesize"


class TestExpandDomainNodeDeduplication:
    """Tests for domain deduplication in merged list."""

    def test_does_not_duplicate_current_domains(
        self, selector: DomainSelector, state_with_strength_context: SessionState
    ) -> None:
        """expand_domain_node deduplicates when requesting an already-loaded domain.

        The node filters by history (not current domains) when checking for "new" domains.
        Requesting a domain already in current context but not in history:
        - Adds it to history (since not blocked by history check)
        - Rebuilds context with merged list
        - Deduplicates merged list so domain appears only once

        This test verifies the deduplication behavior in the merged domain list.
        """
        state_with_strength_context["domain_expansion_request"] = ["strength"]

        result = expand_domain_node(state_with_strength_context, selector)

        context = result["active_domain_context"]
        assert context["domains_loaded"].count("strength") == 1
