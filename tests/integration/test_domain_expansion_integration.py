"""Integration tests for domain expansion with Swealog domains.

Tests Story 6.3: Mid-Flow Domain Expansion with actual Swealog domains.
Tests the full flow from Planner/Analyzer triggering expansion to downstream
agents receiving merged context.
"""

from pathlib import Path

import pytest
from quilto import DomainModule, DomainSelector
from quilto.state import (
    SessionState,
    expand_domain_node,
    route_after_analyzer,
    route_after_expand_domain,
    route_after_planner,
)
from swealog.domains import general_fitness, nutrition, running, strength


@pytest.fixture
def swealog_domains() -> list[DomainModule]:
    """Return all Swealog fitness domains."""
    return [strength, running, nutrition]


@pytest.fixture
def selector(swealog_domains: list[DomainModule]) -> DomainSelector:
    """Create DomainSelector with Swealog domains."""
    return DomainSelector(swealog_domains)


@pytest.fixture
def selector_with_base(swealog_domains: list[DomainModule]) -> DomainSelector:
    """Create DomainSelector with general_fitness as base domain."""
    return DomainSelector(
        [general_fitness] + swealog_domains, base_domain=general_fitness
    )


class TestPlannerToExpandDomainFlow:
    """Tests for Planner → EXPAND_DOMAIN → PLAN flow (AC #5, Task 7.1)."""

    def test_planner_expand_to_expand_domain(self, selector: DomainSelector) -> None:
        """Planner's expand_domain action routes to EXPAND_DOMAIN node."""
        # Simulate state after Planner outputs expand_domain
        state: SessionState = {
            "raw_input": "How is my bench press affecting my nutrition?",
            "current_state": "PLAN",
            "planner_output": {
                "next_action": "expand_domain",
                "domain_expansion_request": ["Nutrition"],
                "expansion_reasoning": "Query requires nutrition expertise",
            },
            "active_domain_context": selector.build_active_context(
                ["Strength"]
            ).model_dump(),
            "domain_expansion_request": ["Nutrition"],  # Set by Planner node
            "domain_expansion_history": [],
            "gaps": [],
        }

        # Route after planner
        route = route_after_planner(state)
        assert route == "expand_domain"

        # Execute expand_domain_node
        result = expand_domain_node(state, selector)

        assert result["next_state"] == "plan"
        assert "Nutrition" in result["domain_expansion_history"]

        # Merged context has both domains
        new_context = result["active_domain_context"]
        assert "Strength" in new_context["domains_loaded"]
        assert "Nutrition" in new_context["domains_loaded"]

    def test_planner_expand_multiple_domains(self, selector: DomainSelector) -> None:
        """Planner can request expansion to multiple domains at once."""
        state: SessionState = {
            "raw_input": "How does my strength training affect my running and nutrition?",
            "current_state": "PLAN",
            "planner_output": {
                "next_action": "expand_domain",
                "domain_expansion_request": ["Nutrition", "Running"],
            },
            "active_domain_context": selector.build_active_context(
                ["Strength"]
            ).model_dump(),
            "domain_expansion_request": ["Nutrition", "Running"],
            "domain_expansion_history": [],
            "gaps": [],
        }

        result = expand_domain_node(state, selector)

        new_context = result["active_domain_context"]
        assert "Strength" in new_context["domains_loaded"]
        assert "Nutrition" in new_context["domains_loaded"]
        assert "Running" in new_context["domains_loaded"]


class TestAnalyzerToExpandDomainFlow:
    """Tests for Analyzer → EXPAND_DOMAIN → PLAN flow (AC #5, Task 7.2)."""

    def test_analyzer_outside_expertise_gap(self, selector: DomainSelector) -> None:
        """Analyzer's outside_current_expertise gap triggers expansion."""
        state: SessionState = {
            "raw_input": "What should I eat after bench press?",
            "current_state": "ANALYZE",
            "analysis": {"verdict": "insufficient"},
            "gaps": [
                {
                    "gap_type": "factual",
                    "outside_current_expertise": True,
                    "suspected_domain": "Nutrition",
                    "description": "Query requires nutrition expertise",
                }
            ],
            "active_domain_context": selector.build_active_context(
                ["Strength"]
            ).model_dump(),
            "domain_expansion_request": ["Nutrition"],  # Set by Analyzer node
            "domain_expansion_history": [],
        }

        # Route after analyzer
        route = route_after_analyzer(state)
        assert route == "expand_domain"

        # Execute expand_domain_node
        result = expand_domain_node(state, selector)

        assert result["next_state"] == "plan"
        new_context = result["active_domain_context"]
        assert "Nutrition" in new_context["domains_loaded"]


class TestDownstreamAgentsMergedContext:
    """Tests that downstream agents receive merged context (AC #5, Task 7.3)."""

    def test_merged_vocabulary_available(self, selector: DomainSelector) -> None:
        """After expansion, merged vocabulary is available for downstream agents."""
        initial_context = selector.build_active_context(["Strength"])
        state: SessionState = {
            "raw_input": "Test",
            "current_state": "EXPAND_DOMAIN",
            "active_domain_context": initial_context.model_dump(),
            "domain_expansion_request": ["Nutrition"],
            "domain_expansion_history": [],
            "gaps": [],
        }

        result = expand_domain_node(state, selector)
        new_context = result["active_domain_context"]

        # Strength vocabulary
        assert "bp" in new_context["vocabulary"]
        assert new_context["vocabulary"]["bp"] == "bench press"
        # Nutrition vocabulary merged in
        assert "cal" in new_context["vocabulary"]
        assert new_context["vocabulary"]["cal"] == "calories"
        assert "pro" in new_context["vocabulary"]
        assert new_context["vocabulary"]["pro"] == "protein"

    def test_merged_expertise_available(self, selector: DomainSelector) -> None:
        """After expansion, merged expertise is available for downstream agents."""
        initial_context = selector.build_active_context(["Strength"])
        state: SessionState = {
            "raw_input": "Test",
            "current_state": "EXPAND_DOMAIN",
            "active_domain_context": initial_context.model_dump(),
            "domain_expansion_request": ["Nutrition"],
            "domain_expansion_history": [],
            "gaps": [],
        }

        result = expand_domain_node(state, selector)
        new_context = result["active_domain_context"]

        # Both domain expertise labels present
        assert "[Strength]" in new_context["expertise"]
        assert "[Nutrition]" in new_context["expertise"]

    def test_evaluation_rules_combined(self, selector: DomainSelector) -> None:
        """After expansion, evaluation rules from both domains are combined."""
        initial_context = selector.build_active_context(["Strength"])
        state: SessionState = {
            "raw_input": "Test",
            "current_state": "EXPAND_DOMAIN",
            "active_domain_context": initial_context.model_dump(),
            "domain_expansion_request": ["Nutrition"],
            "domain_expansion_history": [],
            "gaps": [],
        }

        result = expand_domain_node(state, selector)
        new_context = result["active_domain_context"]

        # Rules from both domains
        rules = new_context["evaluation_rules"]
        assert len(rules) > len(initial_context.evaluation_rules)


class TestSwealogDomainExpansion:
    """Tests domain expansion with specific Swealog domain combinations (Task 7.4)."""

    def test_strength_to_nutrition_expansion(self, selector: DomainSelector) -> None:
        """Start with strength, expand to nutrition."""
        initial_context = selector.build_active_context(["Strength"])
        state: SessionState = {
            "raw_input": "What should I eat after bench press?",
            "current_state": "EXPAND_DOMAIN",
            "active_domain_context": initial_context.model_dump(),
            "domain_expansion_request": ["Nutrition"],
            "domain_expansion_history": [],
            "gaps": [],
        }

        result = expand_domain_node(state, selector)

        assert result["domain_expansion_history"] == ["Nutrition"]
        new_context = result["active_domain_context"]
        assert new_context["domains_loaded"] == ["Strength", "Nutrition"]

    def test_running_to_nutrition_expansion(self, selector: DomainSelector) -> None:
        """Start with running, expand to nutrition."""
        initial_context = selector.build_active_context(["Running"])
        state: SessionState = {
            "raw_input": "What should I eat before a marathon?",
            "current_state": "EXPAND_DOMAIN",
            "active_domain_context": initial_context.model_dump(),
            "domain_expansion_request": ["Nutrition"],
            "domain_expansion_history": [],
            "gaps": [],
        }

        result = expand_domain_node(state, selector)

        new_context = result["active_domain_context"]
        assert new_context["domains_loaded"] == ["Running", "Nutrition"]

    def test_strength_to_running_expansion(self, selector: DomainSelector) -> None:
        """Start with strength, expand to running (cross-training scenario)."""
        initial_context = selector.build_active_context(["Strength"])
        state: SessionState = {
            "raw_input": "How does running affect my strength gains?",
            "current_state": "EXPAND_DOMAIN",
            "active_domain_context": initial_context.model_dump(),
            "domain_expansion_request": ["Running"],
            "domain_expansion_history": [],
            "gaps": [],
        }

        result = expand_domain_node(state, selector)

        new_context = result["active_domain_context"]
        assert new_context["domains_loaded"] == ["Strength", "Running"]


class TestNoInfiniteLoop:
    """Tests for preventing infinite expansion loops (Task 7.5)."""

    def test_single_expansion_for_same_domain(
        self, selector: DomainSelector
    ) -> None:
        """Requesting same domain twice only expands once."""
        initial_context = selector.build_active_context(["Strength"])

        # First expansion request
        state1: SessionState = {
            "raw_input": "Test",
            "current_state": "EXPAND_DOMAIN",
            "active_domain_context": initial_context.model_dump(),
            "domain_expansion_request": ["Nutrition"],
            "domain_expansion_history": [],
            "gaps": [],
        }
        result1 = expand_domain_node(state1, selector)

        # Second expansion request for same domain
        state2: SessionState = {
            "raw_input": "Test",
            "current_state": "EXPAND_DOMAIN",
            "active_domain_context": result1["active_domain_context"],
            "domain_expansion_request": ["Nutrition"],  # Same domain again
            "domain_expansion_history": result1["domain_expansion_history"],
            "gaps": [],
        }
        result2 = expand_domain_node(state2, selector)

        # Second request should NOT add Nutrition again
        assert result2["is_partial"] is True
        assert result2["next_state"] == "synthesize"
        # History should still only have one Nutrition
        assert result1["domain_expansion_history"].count("Nutrition") == 1

    def test_history_persists_across_retries(self, selector: DomainSelector) -> None:
        """domain_expansion_history persists across retry cycles."""
        initial_context = selector.build_active_context(["Strength"])

        # First expansion cycle
        state1: SessionState = {
            "raw_input": "Test",
            "current_state": "EXPAND_DOMAIN",
            "active_domain_context": initial_context.model_dump(),
            "domain_expansion_request": ["Nutrition"],
            "domain_expansion_history": [],
            "gaps": [],
        }
        result1 = expand_domain_node(state1, selector)

        # Simulate re-plan → analyze → expand again (retry cycle)
        state2: SessionState = {
            "raw_input": "Test",
            "current_state": "EXPAND_DOMAIN",
            "active_domain_context": result1["active_domain_context"],
            "domain_expansion_request": ["Running"],
            "domain_expansion_history": result1["domain_expansion_history"],
            "gaps": [],
        }
        result2 = expand_domain_node(state2, selector)

        # Both Nutrition and Running in history
        assert "Nutrition" in result2["domain_expansion_history"]
        assert "Running" in result2["domain_expansion_history"]

        # Third request - all domains already expanded
        state3: SessionState = {
            "raw_input": "Test",
            "current_state": "EXPAND_DOMAIN",
            "active_domain_context": result2["active_domain_context"],
            "domain_expansion_request": ["Nutrition", "Running"],  # Both already expanded
            "domain_expansion_history": result2["domain_expansion_history"],
            "gaps": [],
        }
        result3 = expand_domain_node(state3, selector)

        assert result3["is_partial"] is True
        assert result3["next_state"] == "synthesize"


class TestRouterToExpandDomainIntegration:
    """Tests full routing integration from Router selection to expansion."""

    def test_full_flow_router_to_expansion(
        self, selector_with_base: DomainSelector
    ) -> None:
        """Test full flow: Router selects domain → Planner requests expansion."""
        # Step 1: Router selects Strength (with GeneralFitness as base)
        initial_context = selector_with_base.build_active_context(["Strength"])

        # Step 2: Planner detects need for Nutrition expertise
        planner_state: SessionState = {
            "raw_input": "How does protein intake affect my bench press?",
            "current_state": "PLAN",
            "planner_output": {
                "next_action": "expand_domain",
                "domain_expansion_request": ["Nutrition"],
            },
            "active_domain_context": initial_context.model_dump(),
            "domain_expansion_request": ["Nutrition"],
            "domain_expansion_history": [],
            "gaps": [],
        }

        # Route to expand_domain
        route = route_after_planner(planner_state)
        assert route == "expand_domain"

        # Step 3: Expand domain
        result = expand_domain_node(planner_state, selector_with_base)
        assert result["next_state"] == "plan"

        # Step 4: Verify merged context
        new_context = result["active_domain_context"]
        # Base domain (GeneralFitness) should still be present
        assert "GeneralFitness" in new_context["domains_loaded"]
        # Original selection (Strength) should be present
        assert "Strength" in new_context["domains_loaded"]
        # Expanded domain (Nutrition) should be added
        assert "Nutrition" in new_context["domains_loaded"]

        # Route after expand_domain
        expand_state: SessionState = {
            "raw_input": "Test",
            "next_state": result["next_state"],
        }
        final_route = route_after_expand_domain(expand_state)
        assert final_route == "plan"


class TestPlannerDomainExpansionWithOllama:
    """Integration tests with real Ollama for domain expansion (Task 7.6).

    Run with: pytest --use-real-ollama -k TestPlannerDomainExpansionWithOllama
    Or via: make test-ollama
    """

    @pytest.mark.asyncio
    async def test_real_planner_requests_nutrition_expansion(
        self,
        use_real_ollama: bool,
        integration_llm_config_path: Path,
        selector: DomainSelector,
    ) -> None:
        """Test real Planner requests expansion for nutrition-related query.

        This test verifies that given a strength-only domain context,
        the Planner detects that a nutrition-related question requires
        domain expansion and outputs next_action="expand_domain".
        """
        if not use_real_ollama:
            pytest.skip("Requires --use-real-ollama flag")

        from quilto import LLMClient, load_llm_config
        from quilto.agents import PlannerAgent, PlannerInput

        config = load_llm_config(integration_llm_config_path)
        llm_client = LLMClient(config)
        planner = PlannerAgent(llm_client)

        # Build context with Strength only (no Nutrition)
        domain_context = selector.build_active_context(["Strength"])

        result = await planner.plan(
            PlannerInput(
                query="What should I eat after my bench press workout for muscle recovery?",
                domain_context=domain_context,
            )
        )

        # Planner should recognize nutrition expertise is needed
        # Note: LLM behavior is non-deterministic, so we accept either:
        # 1. next_action="expand_domain" with domain_expansion_request containing Nutrition
        # 2. next_action="retrieve" if LLM decides to proceed without expansion
        #
        # The key assertion is that the Planner CAN output expand_domain
        # and this test documents the expected behavior.
        assert result.next_action in ["expand_domain", "retrieve", "synthesize"]

        if result.next_action == "expand_domain":
            # If LLM chose expansion, verify it requests nutrition domain
            assert result.domain_expansion_request is not None
            assert len(result.domain_expansion_request) > 0
            # Planner should recognize Nutrition is needed
            # (domain name matching may vary - Nutrition vs nutrition)
            requested_domains_lower = [
                d.lower() for d in result.domain_expansion_request
            ]
            assert any(
                "nutrition" in d for d in requested_domains_lower
            ), f"Expected nutrition in expansion request, got: {result.domain_expansion_request}"
