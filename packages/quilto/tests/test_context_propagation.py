"""Unit tests for session context propagation to all agents.

Story 20.5: Fix Session Context Propagation to All Agents
Tests that all agent Input models accept conversation_context field.
"""

import pytest
from quilto.agents.models import (
    ActiveDomainContext,
    AnalyzerInput,
    AnalyzerOutput,
    EvaluatorInput,
    Finding,
    ObserverInput,
    QueryType,
    RetrievalAttempt,
    RouterInput,
    SufficiencyEvaluation,
    SynthesizerInput,
    Verdict,
)


class TestRouterInputSessionContext:
    """Tests for RouterInput session_context field (AC: #1)."""

    def test_router_input_accepts_session_context(self) -> None:
        """RouterInput accepts session_context field."""
        from quilto.agents.models import DomainInfo

        router_input = RouterInput(
            raw_input="What workout did you recommend?",
            available_domains=[DomainInfo(name="fitness", description="Fitness domain")],
            session_context="Previous: Recommended leg workout with squats and lunges.",
        )
        assert router_input.session_context == "Previous: Recommended leg workout with squats and lunges."

    def test_router_input_session_context_defaults_none(self) -> None:
        """RouterInput session_context defaults to None."""
        from quilto.agents.models import DomainInfo

        router_input = RouterInput(
            raw_input="bench pressed 185x5",
            available_domains=[DomainInfo(name="fitness", description="Fitness domain")],
        )
        assert router_input.session_context is None


class TestAnalyzerInputConversationContext:
    """Tests for AnalyzerInput conversation_context field (AC: #2)."""

    @pytest.fixture
    def domain_context(self) -> ActiveDomainContext:
        """Create minimal domain context for testing."""
        return ActiveDomainContext(
            domains_loaded=["fitness"],
            vocabulary={"pr": "personal record"},
            expertise="Fitness analysis",
        )

    @pytest.fixture
    def retrieval_summary(self) -> list[RetrievalAttempt]:
        """Create minimal retrieval summary for testing."""
        return [
            RetrievalAttempt(
                attempt_number=1,
                strategy="date_range",
                params={"days": 7},
                entries_found=5,
                summary="Found 5 entries",
            )
        ]

    def test_analyzer_input_accepts_conversation_context(
        self,
        domain_context: ActiveDomainContext,
        retrieval_summary: list[RetrievalAttempt],
    ) -> None:
        """AnalyzerInput accepts conversation_context field."""
        analyzer_input = AnalyzerInput(
            query="What workout did you recommend?",
            query_type=QueryType.SIMPLE,
            entries=[],
            retrieval_summary=retrieval_summary,
            domain_context=domain_context,
            conversation_context="Previous: Recommended leg workout with squats and lunges.",
        )
        assert analyzer_input.conversation_context == "Previous: Recommended leg workout with squats and lunges."

    def test_analyzer_input_conversation_context_defaults_none(
        self,
        domain_context: ActiveDomainContext,
        retrieval_summary: list[RetrievalAttempt],
    ) -> None:
        """AnalyzerInput conversation_context defaults to None."""
        analyzer_input = AnalyzerInput(
            query="How many sets did I do?",
            query_type=QueryType.SIMPLE,
            entries=[],
            retrieval_summary=retrieval_summary,
            domain_context=domain_context,
        )
        assert analyzer_input.conversation_context is None


class TestSynthesizerInputConversationContext:
    """Tests for SynthesizerInput conversation_context field (AC: #3)."""

    @pytest.fixture
    def analyzer_output(self) -> AnalyzerOutput:
        """Create minimal analyzer output for testing."""
        return AnalyzerOutput(
            query_intent="User wants to know about previous recommendation",
            findings=[],
            patterns_identified=[],
            sufficiency_evaluation=SufficiencyEvaluation(
                critical_gaps=[],
                nice_to_have_gaps=[],
                evidence_check_passed=True,
                speculation_risk="none",
            ),
            verdict_reasoning="Information available in conversation context",
            verdict=Verdict.SUFFICIENT,
        )

    def test_synthesizer_input_accepts_conversation_context(
        self,
        analyzer_output: AnalyzerOutput,
    ) -> None:
        """SynthesizerInput accepts conversation_context field."""
        synthesizer_input = SynthesizerInput(
            query="What workout did you recommend?",
            query_type=QueryType.SIMPLE,
            analysis=analyzer_output,  # type: ignore[arg-type]
            vocabulary={"pr": "personal record"},
            conversation_context="Previous: Recommended leg workout with squats and lunges.",
        )
        assert synthesizer_input.conversation_context == "Previous: Recommended leg workout with squats and lunges."

    def test_synthesizer_input_conversation_context_defaults_none(
        self,
        analyzer_output: AnalyzerOutput,
    ) -> None:
        """SynthesizerInput conversation_context defaults to None."""
        synthesizer_input = SynthesizerInput(
            query="How many sets did I do?",
            query_type=QueryType.SIMPLE,
            analysis=analyzer_output,  # type: ignore[arg-type]
            vocabulary={},
        )
        assert synthesizer_input.conversation_context is None


class TestEvaluatorInputConversationContext:
    """Tests for EvaluatorInput conversation_context field (AC: #4)."""

    @pytest.fixture
    def analyzer_output(self) -> AnalyzerOutput:
        """Create minimal analyzer output for testing."""
        return AnalyzerOutput(
            query_intent="User wants to know about previous recommendation",
            findings=[
                Finding(
                    claim="Leg workout was recommended",
                    evidence=["from context"],
                    confidence="high",
                )
            ],
            patterns_identified=[],
            sufficiency_evaluation=SufficiencyEvaluation(
                critical_gaps=[],
                nice_to_have_gaps=[],
                evidence_check_passed=True,
                speculation_risk="none",
            ),
            verdict_reasoning="Information available in conversation context",
            verdict=Verdict.SUFFICIENT,
        )

    def test_evaluator_input_accepts_conversation_context(
        self,
        analyzer_output: AnalyzerOutput,
    ) -> None:
        """EvaluatorInput accepts conversation_context field."""
        evaluator_input = EvaluatorInput(
            query="What workout did you recommend?",
            response="Earlier I recommended a leg workout with squats and lunges.",
            analysis=analyzer_output,  # type: ignore[arg-type]
            entries_summary="(No entries)",
            evaluation_rules=[],
            conversation_context="Previous: Recommended leg workout with squats and lunges.",
        )
        assert evaluator_input.conversation_context == "Previous: Recommended leg workout with squats and lunges."

    def test_evaluator_input_conversation_context_defaults_none(
        self,
        analyzer_output: AnalyzerOutput,
    ) -> None:
        """EvaluatorInput conversation_context defaults to None."""
        evaluator_input = EvaluatorInput(
            query="How many sets did I do?",
            response="You did 5 sets.",
            analysis=analyzer_output,  # type: ignore[arg-type]
            entries_summary="5 entries",
            evaluation_rules=[],
        )
        assert evaluator_input.conversation_context is None


class TestObserverInputConversationContext:
    """Tests for ObserverInput conversation_context field (AC: #5)."""

    def test_observer_input_accepts_conversation_context(self) -> None:
        """ObserverInput accepts conversation_context field."""
        observer_input = ObserverInput(
            trigger="post_query",
            current_global_context="",
            context_management_guidance="Track user preferences",
            query="What workout did you recommend?",
            analysis={},
            response="Earlier I recommended a leg workout.",
            conversation_context="Previous: Recommended leg workout with squats and lunges.",
        )
        assert observer_input.conversation_context == "Previous: Recommended leg workout with squats and lunges."

    def test_observer_input_conversation_context_defaults_none(self) -> None:
        """ObserverInput conversation_context defaults to None."""
        observer_input = ObserverInput(
            trigger="post_query",
            current_global_context="",
            context_management_guidance="Track user preferences",
            query="How many sets did I do?",
            analysis={},
            response="You did 5 sets.",
        )
        assert observer_input.conversation_context is None

    def test_observer_input_with_user_correction_trigger(self) -> None:
        """ObserverInput with user_correction trigger accepts conversation_context."""
        observer_input = ObserverInput(
            trigger="user_correction",
            current_global_context="",
            context_management_guidance="Track user preferences",
            correction="Actually I meant 60kg not 50kg",
            what_was_corrected="bench press weight",
            conversation_context="Previous: Logged bench press at 50kg.",
        )
        assert observer_input.conversation_context == "Previous: Logged bench press at 50kg."


class TestContextDependentQueryScenario:
    """Integration test for context-dependent query scenario (AC: #6).

    Scenario: Previous turn recommended a leg workout, user asks
    "What workout did you recommend earlier?" and system should
    answer from context when Planner skips retrieval.
    """

    def test_synthesizer_prompt_includes_context_answering_instructions(self) -> None:
        """Synthesizer prompt should include instructions for answering from context."""
        from unittest.mock import MagicMock

        from quilto.agents.models import AnalyzerOutput
        from quilto.agents.synthesizer import SynthesizerAgent

        # Create minimal analyzer output
        analyzer_output = AnalyzerOutput(
            query_intent="User wants to know about previous recommendation",
            findings=[],  # Empty because Planner skipped retrieval
            patterns_identified=[],
            sufficiency_evaluation=SufficiencyEvaluation(
                critical_gaps=[],
                nice_to_have_gaps=[],
                evidence_check_passed=True,
                speculation_risk="none",
            ),
            verdict_reasoning="Information available in conversation context",
            verdict=Verdict.SUFFICIENT,
        )

        # Create synthesizer input with conversation context
        synthesizer_input = SynthesizerInput(
            query="What workout did you recommend earlier?",
            query_type=QueryType.SIMPLE,
            analysis=analyzer_output,
            vocabulary={},
            conversation_context=(
                "User: I want to build leg strength.\n"
                "Agent: I recommend a leg workout with squats, lunges, and leg press. "
                "Start with 3 sets of 10 reps each."
            ),
        )

        # Build prompt and verify context instructions are included
        mock_client = MagicMock()
        synthesizer = SynthesizerAgent(mock_client)
        prompt = synthesizer.build_prompt(synthesizer_input)

        # Key AC #6 assertions:
        # 1. Context should be in the prompt
        assert "I recommend a leg workout" in prompt
        # 2. Instructions for answering from context should be present
        assert "CRITICAL: CONTEXT-BASED ANSWERING" in prompt
        assert "findings are empty" in prompt.lower() or "retrieval returned no entries" in prompt.lower()
        # 3. Should NOT say "I don't have a record"
        assert "I don't have a record" in prompt  # This is in the WRONG example

    def test_router_prompt_includes_follow_up_detection(self) -> None:
        """Router prompt should include follow-up detection instructions."""
        from unittest.mock import MagicMock

        from quilto.agents.models import DomainInfo
        from quilto.agents.router import RouterAgent

        router_input = RouterInput(
            raw_input="Upper body",  # Clarification answer, could be misclassified as LOG
            available_domains=[DomainInfo(name="fitness", description="Fitness domain")],
            session_context="Agent: What type of strength training would you like?",
        )

        # Build prompt and verify follow-up detection instructions
        mock_client = MagicMock()
        router = RouterAgent(mock_client)
        prompt = router.build_prompt(router_input)

        # Key assertions for Pattern #1 fix:
        assert "FOLLOW-UP" in prompt.upper() or "CLARIFICATION" in prompt.upper()
        assert "QUERY continuation" in prompt
        # Session context should be in prompt
        assert "What type of strength training" in prompt
