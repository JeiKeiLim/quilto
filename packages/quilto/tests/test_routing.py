"""Unit tests for routing functions.

Tests cover:
- route_after_planner: routes based on next_action
- route_after_analyzer: routes based on gaps and verdict
- route_after_expand_domain: routes based on next_state
"""

from quilto.state import (
    SessionState,
    route_after_analyzer,
    route_after_expand_domain,
    route_after_planner,
)


class TestRouteAfterPlanner:
    """Tests for route_after_planner function (AC #1)."""

    def test_returns_expand_domain_for_expand_action(self) -> None:
        """route_after_planner returns 'expand_domain' for expand action (Subtask 6.8)."""
        state: SessionState = {
            "raw_input": "Test",
            "planner_output": {
                "next_action": "expand_domain",
                "domain_expansion_request": ["nutrition"],
            },
        }

        result = route_after_planner(state)

        assert result == "expand_domain"

    def test_returns_retrieve_for_retrieve_action(self) -> None:
        """route_after_planner returns 'retrieve' for retrieve action."""
        state: SessionState = {
            "raw_input": "Test",
            "planner_output": {"next_action": "retrieve"},
        }

        result = route_after_planner(state)

        assert result == "retrieve"

    def test_returns_clarify_for_clarify_action(self) -> None:
        """route_after_planner returns 'clarify' for clarify action."""
        state: SessionState = {
            "raw_input": "Test",
            "planner_output": {"next_action": "clarify"},
        }

        result = route_after_planner(state)

        assert result == "clarify"

    def test_returns_synthesize_for_synthesize_action(self) -> None:
        """route_after_planner returns 'synthesize' for synthesize action."""
        state: SessionState = {
            "raw_input": "Test",
            "planner_output": {"next_action": "synthesize"},
        }

        result = route_after_planner(state)

        assert result == "synthesize"

    def test_defaults_to_retrieve_for_unknown_action(self) -> None:
        """route_after_planner defaults to 'retrieve' for unknown action."""
        state: SessionState = {
            "raw_input": "Test",
            "planner_output": {"next_action": "unknown_action"},
        }

        result = route_after_planner(state)

        assert result == "retrieve"

    def test_defaults_to_retrieve_when_no_planner_output(self) -> None:
        """route_after_planner defaults to 'retrieve' when planner_output is None."""
        state: SessionState = {
            "raw_input": "Test",
            "planner_output": None,
        }

        result = route_after_planner(state)

        assert result == "retrieve"

    def test_defaults_to_retrieve_when_planner_output_missing(self) -> None:
        """route_after_planner defaults to 'retrieve' when planner_output key missing."""
        state: SessionState = {"raw_input": "Test"}

        result = route_after_planner(state)

        assert result == "retrieve"

    def test_defaults_to_retrieve_when_next_action_missing(self) -> None:
        """route_after_planner defaults to 'retrieve' when next_action key missing."""
        state: SessionState = {
            "raw_input": "Test",
            "planner_output": {},  # No next_action key
        }

        result = route_after_planner(state)

        assert result == "retrieve"


class TestRouteAfterAnalyzer:
    """Tests for route_after_analyzer function (AC #2)."""

    def test_returns_expand_domain_for_outside_expertise_gap(self) -> None:
        """route_after_analyzer returns 'expand_domain' for outside_current_expertise gap (Subtask 6.9)."""
        state: SessionState = {
            "raw_input": "Test",
            "analysis": {"verdict": "insufficient"},
            "gaps": [
                {
                    "outside_current_expertise": True,
                    "suspected_domain": "nutrition",
                    "gap_type": "factual",
                }
            ],
            "domain_expansion_history": [],
        }

        result = route_after_analyzer(state)

        assert result == "expand_domain"

    def test_respects_domain_expansion_history(self) -> None:
        """route_after_analyzer respects domain_expansion_history (Subtask 6.10)."""
        state: SessionState = {
            "raw_input": "Test",
            "analysis": {"verdict": "insufficient"},
            "gaps": [
                {
                    "outside_current_expertise": True,
                    "suspected_domain": "nutrition",
                    "gap_type": "factual",
                }
            ],
            "domain_expansion_history": ["nutrition"],  # Already expanded
        }

        result = route_after_analyzer(state)

        # Should NOT return expand_domain since nutrition already in history
        assert result == "plan"

    def test_returns_synthesize_for_sufficient_verdict(self) -> None:
        """route_after_analyzer returns 'synthesize' for sufficient verdict."""
        state: SessionState = {
            "raw_input": "Test",
            "analysis": {"verdict": "sufficient"},
            "gaps": [],
            "domain_expansion_history": [],
        }

        result = route_after_analyzer(state)

        assert result == "synthesize"

    def test_returns_plan_for_insufficient_verdict(self) -> None:
        """route_after_analyzer returns 'plan' for insufficient verdict."""
        state: SessionState = {
            "raw_input": "Test",
            "analysis": {"verdict": "insufficient"},
            "gaps": [{"gap_type": "factual"}],  # No outside_current_expertise
            "domain_expansion_history": [],
        }

        result = route_after_analyzer(state)

        assert result == "plan"

    def test_returns_plan_for_partial_verdict(self) -> None:
        """route_after_analyzer returns 'plan' for partial verdict."""
        state: SessionState = {
            "raw_input": "Test",
            "analysis": {"verdict": "partial"},
            "gaps": [{"gap_type": "factual"}],
            "domain_expansion_history": [],
        }

        result = route_after_analyzer(state)

        assert result == "plan"

    def test_defaults_to_synthesize_when_no_analysis(self) -> None:
        """route_after_analyzer defaults to 'synthesize' when analysis is None."""
        state: SessionState = {
            "raw_input": "Test",
            "analysis": None,
            "gaps": [],
            "domain_expansion_history": [],
        }

        result = route_after_analyzer(state)

        assert result == "synthesize"

    def test_defaults_to_synthesize_when_analysis_missing(self) -> None:
        """route_after_analyzer defaults to 'synthesize' when analysis key missing."""
        state: SessionState = {"raw_input": "Test"}

        result = route_after_analyzer(state)

        assert result == "synthesize"

    def test_requires_suspected_domain_for_expansion(self) -> None:
        """route_after_analyzer requires suspected_domain for expansion."""
        state: SessionState = {
            "raw_input": "Test",
            "analysis": {"verdict": "insufficient"},
            "gaps": [
                {
                    "outside_current_expertise": True,
                    # No suspected_domain
                    "gap_type": "factual",
                }
            ],
            "domain_expansion_history": [],
        }

        result = route_after_analyzer(state)

        # Without suspected_domain, can't expand
        assert result == "plan"

    def test_handles_multiple_outside_expertise_gaps(self) -> None:
        """route_after_analyzer handles multiple outside_current_expertise gaps."""
        state: SessionState = {
            "raw_input": "Test",
            "analysis": {"verdict": "insufficient"},
            "gaps": [
                {
                    "outside_current_expertise": True,
                    "suspected_domain": "nutrition",
                },
                {
                    "outside_current_expertise": True,
                    "suspected_domain": "running",
                },
            ],
            "domain_expansion_history": ["nutrition"],  # nutrition already expanded
        }

        result = route_after_analyzer(state)

        # running is not in history, so should expand
        assert result == "expand_domain"

    def test_handles_none_gaps(self) -> None:
        """route_after_analyzer handles None gaps."""
        state: SessionState = {
            "raw_input": "Test",
            "analysis": {"verdict": "sufficient"},
            "gaps": None,  # pyright: ignore[reportAssignmentType]
            "domain_expansion_history": [],
        }

        result = route_after_analyzer(state)

        assert result == "synthesize"

    def test_handles_none_history(self) -> None:
        """route_after_analyzer handles None domain_expansion_history."""
        state: SessionState = {
            "raw_input": "Test",
            "analysis": {"verdict": "insufficient"},
            "gaps": [
                {
                    "outside_current_expertise": True,
                    "suspected_domain": "nutrition",
                }
            ],
            "domain_expansion_history": None,  # pyright: ignore[reportAssignmentType]
        }

        result = route_after_analyzer(state)

        assert result == "expand_domain"


class TestRouteAfterExpandDomain:
    """Tests for route_after_expand_domain function."""

    def test_returns_plan_for_plan_next_state(self) -> None:
        """route_after_expand_domain returns 'plan' when next_state is 'plan'."""
        state: SessionState = {
            "raw_input": "Test",
            "next_state": "plan",
        }

        result = route_after_expand_domain(state)

        assert result == "plan"

    def test_returns_clarify_for_clarify_next_state(self) -> None:
        """route_after_expand_domain returns 'clarify' when next_state is 'clarify'."""
        state: SessionState = {
            "raw_input": "Test",
            "next_state": "clarify",
        }

        result = route_after_expand_domain(state)

        assert result == "clarify"

    def test_returns_synthesize_for_synthesize_next_state(self) -> None:
        """route_after_expand_domain returns 'synthesize' when next_state is 'synthesize'."""
        state: SessionState = {
            "raw_input": "Test",
            "next_state": "synthesize",
        }

        result = route_after_expand_domain(state)

        assert result == "synthesize"

    def test_defaults_to_plan_for_unknown_next_state(self) -> None:
        """route_after_expand_domain defaults to 'plan' for unknown next_state."""
        state: SessionState = {
            "raw_input": "Test",
            "next_state": "unknown",
        }

        result = route_after_expand_domain(state)

        assert result == "plan"

    def test_defaults_to_plan_when_next_state_none(self) -> None:
        """route_after_expand_domain defaults to 'plan' when next_state is None."""
        state: SessionState = {
            "raw_input": "Test",
            "next_state": None,
        }

        result = route_after_expand_domain(state)

        assert result == "plan"

    def test_defaults_to_plan_when_next_state_missing(self) -> None:
        """route_after_expand_domain defaults to 'plan' when next_state key missing."""
        state: SessionState = {"raw_input": "Test"}

        result = route_after_expand_domain(state)

        assert result == "plan"


class TestRoutingIntegration:
    """Integration tests for routing flow."""

    def test_planner_expand_to_expand_domain_to_plan_flow(self) -> None:
        """Test Planner → EXPAND_DOMAIN → PLAN routing flow."""
        # Planner requests expansion
        planner_state: SessionState = {
            "raw_input": "Test",
            "planner_output": {
                "next_action": "expand_domain",
                "domain_expansion_request": ["nutrition"],
            },
        }
        assert route_after_planner(planner_state) == "expand_domain"

        # After expand_domain_node, next_state is set to "plan"
        expand_state: SessionState = {
            "raw_input": "Test",
            "next_state": "plan",
        }
        assert route_after_expand_domain(expand_state) == "plan"

    def test_analyzer_expand_to_expand_domain_to_plan_flow(self) -> None:
        """Test Analyzer → EXPAND_DOMAIN → PLAN routing flow."""
        # Analyzer detects outside_current_expertise gap
        analyzer_state: SessionState = {
            "raw_input": "Test",
            "analysis": {"verdict": "insufficient"},
            "gaps": [
                {
                    "outside_current_expertise": True,
                    "suspected_domain": "nutrition",
                }
            ],
            "domain_expansion_history": [],
        }
        assert route_after_analyzer(analyzer_state) == "expand_domain"

        # After expand_domain_node, next_state is set to "plan"
        expand_state: SessionState = {
            "raw_input": "Test",
            "next_state": "plan",
        }
        assert route_after_expand_domain(expand_state) == "plan"

    def test_analyzer_no_expansion_to_synthesize_flow(self) -> None:
        """Test Analyzer → SYNTHESIZE when all domains already expanded."""
        analyzer_state: SessionState = {
            "raw_input": "Test",
            "analysis": {"verdict": "insufficient"},
            "gaps": [
                {
                    "outside_current_expertise": True,
                    "suspected_domain": "nutrition",
                }
            ],
            "domain_expansion_history": ["nutrition"],  # Already expanded
        }
        # Since nutrition already in history, route to plan (re-plan with gaps)
        assert route_after_analyzer(analyzer_state) == "plan"
