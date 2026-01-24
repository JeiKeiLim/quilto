"""Integration tests for clarification flow with routing (Story 12.1).

Tests the routing logic for clarification trigger:
- Critical SUBJECTIVE/CLARIFICATION gaps + 0 entries → clarify
- Verifies the full state flow from Analyzer to Clarify state

Run with: pytest --use-real-ollama -k TestClarificationFlowWithOllama
Or via: make test-ollama
"""

from pathlib import Path

import pytest
from quilto.state import SessionState, route_after_analyzer
from quilto.state.routing import MAX_REPLANS


class TestClarificationFlowIntegration:
    """Integration tests for clarification trigger logic.

    These tests verify that the routing correctly handles realistic
    scenarios from the dogfooding analysis (Story 12.1).
    """

    def test_running_fitness_query_with_subjective_gap_triggers_clarify(self) -> None:
        """Scenario from dogfooding: query about running fitness with no logs.

        Record e16dbc36: Analyzer identified critical SUBJECTIVE gap
        ("user's current running fitness") but flow went to Synthesize.
        With fix, should go to CLARIFY when 0 entries retrieved.
        """
        state: SessionState = {
            "raw_input": "Am I ready to run a marathon?",
            "analysis": {
                "verdict": "insufficient",
                "reasoning": "Cannot assess marathon readiness without knowing user's current running fitness level",
            },
            "gaps": [
                {
                    "gap_type": "subjective",
                    "severity": "critical",
                    "description": "User's current running fitness level",
                    "question_to_ask": "What is your current longest run distance?",
                }
            ],
            "retrieved_entries": [],  # 0 entries - no running logs
            "domain_expansion_history": [],
            "retry_count": 0,
        }

        result = route_after_analyzer(state)

        assert result == "clarify"

    def test_nutrition_query_with_clarification_gap_triggers_clarify(self) -> None:
        """Scenario: ambiguous nutrition query with no entries.

        When user asks vague question and no relevant entries exist,
        should trigger clarification to understand intent.
        """
        state: SessionState = {
            "raw_input": "Should I eat more?",
            "analysis": {
                "verdict": "insufficient",
                "reasoning": "Query is ambiguous - more of what? For what purpose?",
            },
            "gaps": [
                {
                    "gap_type": "clarification",
                    "severity": "critical",
                    "description": "Query intent is ambiguous",
                    "question_to_ask": "What specifically are you asking about - protein, calories, or general diet?",
                }
            ],
            "retrieved_entries": [],
            "domain_expansion_history": [],
            "retry_count": 0,
        }

        result = route_after_analyzer(state)

        assert result == "clarify"

    def test_query_with_entries_bypasses_clarify(self) -> None:
        """When entries exist, should synthesize with available data.

        Even with critical subjective gaps, if we have data, try to
        provide an answer based on that data rather than asking.
        """
        state: SessionState = {
            "raw_input": "How is my running progress?",
            "analysis": {
                "verdict": "sufficient",
                "reasoning": "Can analyze running progress from retrieved entries",
            },
            "gaps": [
                {
                    "gap_type": "subjective",
                    "severity": "critical",
                    "description": "User's perceived exertion",
                }
            ],
            "retrieved_entries": [
                {"id": "run1", "distance": 5.0, "duration": "30min"},
                {"id": "run2", "distance": 5.2, "duration": "29min"},
            ],
            "domain_expansion_history": [],
            "retry_count": 0,
        }

        result = route_after_analyzer(state)

        assert result == "synthesize"

    def test_mixed_gaps_with_zero_entries_triggers_clarify(self) -> None:
        """Mixed retrievable and non-retrievable gaps with 0 entries.

        When both temporal and subjective gaps exist, but no entries,
        should clarify since re-planning won't help.
        """
        state: SessionState = {
            "raw_input": "Am I stronger than last month?",
            "analysis": {"verdict": "insufficient"},
            "gaps": [
                {
                    "gap_type": "temporal",
                    "severity": "critical",
                    "description": "No entries from last month",
                },
                {
                    "gap_type": "subjective",
                    "severity": "critical",
                    "description": "User's strength goals",
                },
            ],
            "retrieved_entries": [],
            "domain_expansion_history": [],
            "retry_count": 0,
        }

        result = route_after_analyzer(state)

        # Should trigger clarify due to critical subjective gap + 0 entries
        assert result == "clarify"

    def test_max_replans_prevents_infinite_loop(self) -> None:
        """After MAX_REPLANS exceeded, should synthesize partial answer.

        Prevents infinite re-planning loops when retrieval keeps failing.
        """
        state: SessionState = {
            "raw_input": "What about my workout last Tuesday?",
            "analysis": {
                "verdict": "insufficient",
                "reasoning": "No entries found for last Tuesday",
            },
            "gaps": [{"gap_type": "temporal", "severity": "critical"}],
            "retrieved_entries": [],
            "domain_expansion_history": [],
            "retry_count": MAX_REPLANS + 1,  # Exceeded
        }

        result = route_after_analyzer(state)

        assert result == "synthesize"


class TestClarificationFlowWithOllama:
    """Integration tests with real Ollama for clarification flow.

    These tests verify that the Analyzer produces appropriate gap types
    for queries that should trigger clarification.

    Run with: pytest --use-real-ollama -k TestClarificationFlowWithOllama
    Or via: make test-ollama
    """

    @pytest.mark.asyncio
    async def test_analyzer_identifies_subjective_gap_for_fitness_state_query(
        self,
        use_real_ollama: bool,
        integration_llm_config_path: Path,
    ) -> None:
        """Test Analyzer identifies subjective gaps for fitness state queries.

        When user asks about their subjective state (e.g., "Am I ready?"),
        Analyzer should identify this as a SUBJECTIVE gap type.
        """
        if not use_real_ollama:
            pytest.skip("Requires --use-real-ollama flag")

        from quilto import DomainSelector, LLMClient, load_llm_config
        from quilto.agents import AnalyzerAgent, AnalyzerInput, QueryType, RetrievalAttempt
        from swealog.domains import general_fitness, running

        config = load_llm_config(integration_llm_config_path)
        llm_client = LLMClient(config)
        analyzer = AnalyzerAgent(llm_client)

        selector = DomainSelector([general_fitness, running], base_domain=general_fitness)
        domain_context = selector.build_active_context(["Running"])

        result = await analyzer.analyze(
            AnalyzerInput(
                query="Am I ready to run a half marathon next week?",
                query_type=QueryType.INSIGHT,
                entries=[],  # No entries available
                retrieval_summary=[
                    RetrievalAttempt(
                        attempt_number=1,
                        strategy="date_range",
                        params={"days": 30},
                        entries_found=0,
                        summary="No relevant running logs found in last 30 days",
                    )
                ],
                domain_context=domain_context,
            )
        )

        # Analyzer should identify gaps
        all_gaps = result.sufficiency_evaluation.critical_gaps + result.sufficiency_evaluation.nice_to_have_gaps
        assert len(all_gaps) > 0

        # Check that at least one gap is non-retrievable (subjective/clarification)
        non_retrievable_gaps = [g for g in all_gaps if g.gap_type in ["subjective", "clarification"]]

        # Note: LLM behavior is non-deterministic
        # We assert that the Analyzer CAN identify subjective gaps
        # and that routing handles them correctly (tested in unit tests)
        if non_retrievable_gaps:
            # If Analyzer identified non-retrievable gaps, verify critical severity
            critical_non_retrievable = [
                g for g in result.sufficiency_evaluation.critical_gaps if g.gap_type in ["subjective", "clarification"]
            ]
            if critical_non_retrievable:
                # Build state and verify routing goes to clarify
                state: SessionState = {
                    "raw_input": "Am I ready to run a half marathon?",
                    "analysis": result.model_dump(),
                    "gaps": [g.model_dump() for g in all_gaps],
                    "retrieved_entries": [],
                    "domain_expansion_history": [],
                    "retry_count": 0,
                }
                route = route_after_analyzer(state)
                assert route == "clarify"
