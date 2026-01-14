"""Unit tests for ClarifierAgent.

Tests cover model validation, prompt building, clarify execution,
helper methods, gap filtering, and exports.
"""

import json
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock

import pytest
from pydantic import BaseModel, ValidationError
from quilto import load_llm_config
from quilto.agents import (
    ClarificationQuestion,
    ClarifierAgent,
    ClarifierInput,
    ClarifierOutput,
    Gap,
    GapType,
    RetrievalAttempt,
)
from quilto.llm.client import LLMClient
from quilto.llm.config import AgentConfig, LLMConfig, ProviderConfig, TierModels


def create_test_config() -> LLMConfig:
    """Create a test LLMConfig for ClarifierAgent tests.

    Returns:
        Configured LLMConfig for testing.
    """
    return LLMConfig(
        default_provider="ollama",  # type: ignore[arg-type]
        providers={
            "ollama": ProviderConfig(api_base="http://localhost:11434"),
        },
        tiers={
            "medium": TierModels(ollama="qwen2.5:7b"),
        },
        agents={
            "clarifier": AgentConfig(tier="medium"),
        },
    )


def create_mock_llm_client(response_json: dict[str, Any]) -> LLMClient:
    """Create a mock LLMClient that returns the given JSON response.

    Args:
        response_json: The JSON response to return from complete_structured.

    Returns:
        Mocked LLMClient instance.
    """
    config = create_test_config()
    client = LLMClient(config)

    async def mock_complete_structured(
        agent: str,
        messages: list[dict[str, Any]],
        response_model: type[BaseModel],
        **kwargs: Any,
    ) -> BaseModel:
        return response_model.model_validate_json(json.dumps(response_json))

    client.complete_structured = AsyncMock(side_effect=mock_complete_structured)  # type: ignore[method-assign]
    return client


def create_subjective_gap() -> Gap:
    """Create a subjective gap for testing.

    Returns:
        Gap with gap_type SUBJECTIVE.
    """
    return Gap(
        description="Current energy level unknown",
        gap_type=GapType.SUBJECTIVE,
        severity="critical",
    )


def create_clarification_gap() -> Gap:
    """Create a clarification gap for testing.

    Returns:
        Gap with gap_type CLARIFICATION.
    """
    return Gap(
        description="Query is ambiguous - which workout?",
        gap_type=GapType.CLARIFICATION,
        severity="critical",
    )


def create_temporal_gap() -> Gap:
    """Create a temporal gap for testing.

    Returns:
        Gap with gap_type TEMPORAL (retrievable).
    """
    return Gap(
        description="Need data from last week",
        gap_type=GapType.TEMPORAL,
        severity="critical",
    )


def create_topical_gap() -> Gap:
    """Create a topical gap for testing.

    Returns:
        Gap with gap_type TOPICAL (retrievable).
    """
    return Gap(
        description="Need bench press specific data",
        gap_type=GapType.TOPICAL,
        severity="nice_to_have",
    )


def create_sample_retrieval_attempt() -> RetrievalAttempt:
    """Create sample retrieval attempt for testing.

    Returns:
        RetrievalAttempt for tests.
    """
    return RetrievalAttempt(
        attempt_number=1,
        strategy="date_range",
        params={"start_date": "2026-01-01", "end_date": "2026-01-10"},
        entries_found=5,
        summary="Retrieved 5 entries from 2026-01-01 to 2026-01-10",
        expanded_terms=[],
    )


# =============================================================================
# Test ClarificationQuestion Model (Task 1.1)
# =============================================================================


class TestClarificationQuestionModel:
    """Tests for ClarificationQuestion Pydantic model validation."""

    def test_clarification_question_valid(self) -> None:
        """ClarificationQuestion accepts valid data."""
        question = ClarificationQuestion(
            question="What time did this happen?",
            gap_addressed="Time of activity is ambiguous",
            options=["Morning", "Afternoon", "Evening"],
            required=True,
        )
        assert question.question == "What time did this happen?"
        assert question.gap_addressed == "Time of activity is ambiguous"
        assert question.options == ["Morning", "Afternoon", "Evening"]
        assert question.required is True

    def test_clarification_question_empty_question_fails(self) -> None:
        """ClarificationQuestion with empty question fails min_length=1."""
        with pytest.raises(ValidationError):
            ClarificationQuestion(
                question="",
                gap_addressed="Some gap",
                options=None,
                required=True,
            )

    def test_clarification_question_empty_gap_addressed_fails(self) -> None:
        """ClarificationQuestion with empty gap_addressed fails min_length=1."""
        with pytest.raises(ValidationError):
            ClarificationQuestion(
                question="What time?",
                gap_addressed="",
                options=None,
                required=True,
            )

    def test_clarification_question_options_none_valid(self) -> None:
        """ClarificationQuestion with options=None is valid."""
        question = ClarificationQuestion(
            question="When did this happen?",
            gap_addressed="Time is unclear",
            options=None,
            required=True,
        )
        assert question.options is None

    def test_clarification_question_options_empty_list_valid(self) -> None:
        """ClarificationQuestion with options=[] is valid."""
        question = ClarificationQuestion(
            question="When did this happen?",
            gap_addressed="Time is unclear",
            options=[],
            required=True,
        )
        assert question.options == []

    def test_clarification_question_required_default_true(self) -> None:
        """ClarificationQuestion required defaults to True."""
        question = ClarificationQuestion(
            question="What time?",
            gap_addressed="Time gap",
        )
        assert question.required is True

    def test_clarification_question_required_false(self) -> None:
        """ClarificationQuestion accepts required=False."""
        question = ClarificationQuestion(
            question="Optional question?",
            gap_addressed="Optional gap",
            required=False,
        )
        assert question.required is False


# =============================================================================
# Test ClarifierInput Model (Task 1.2)
# =============================================================================


class TestClarifierInputModel:
    """Tests for ClarifierInput Pydantic model validation."""

    def test_clarifier_input_valid(self) -> None:
        """ClarifierInput accepts valid data."""
        clarifier_input = ClarifierInput(
            original_query="How should I adjust my workout?",
            gaps=[create_subjective_gap()],
            vocabulary={"rpe": "rate of perceived exertion"},
            retrieval_history=[create_sample_retrieval_attempt()],
            previous_clarifications=["When did you last exercise?"],
        )
        assert clarifier_input.original_query == "How should I adjust my workout?"
        assert len(clarifier_input.gaps) == 1
        assert "rpe" in clarifier_input.vocabulary
        assert len(clarifier_input.retrieval_history) == 1
        assert len(clarifier_input.previous_clarifications) == 1

    def test_clarifier_input_empty_original_query_fails(self) -> None:
        """ClarifierInput with empty original_query fails min_length=1."""
        with pytest.raises(ValidationError):
            ClarifierInput(
                original_query="",
                gaps=[],
                vocabulary={},
            )

    def test_clarifier_input_empty_gaps_list_valid(self) -> None:
        """ClarifierInput with empty gaps list is valid."""
        clarifier_input = ClarifierInput(
            original_query="How should I adjust?",
            gaps=[],
            vocabulary={},
        )
        assert clarifier_input.gaps == []

    def test_clarifier_input_empty_vocabulary_valid(self) -> None:
        """ClarifierInput with empty vocabulary is valid."""
        clarifier_input = ClarifierInput(
            original_query="How should I adjust?",
            gaps=[],
            vocabulary={},
        )
        assert clarifier_input.vocabulary == {}

    def test_clarifier_input_empty_retrieval_history_default(self) -> None:
        """ClarifierInput retrieval_history defaults to empty list."""
        clarifier_input = ClarifierInput(
            original_query="How should I adjust?",
            gaps=[],
            vocabulary={},
        )
        assert clarifier_input.retrieval_history == []

    def test_clarifier_input_empty_previous_clarifications_default(self) -> None:
        """ClarifierInput previous_clarifications defaults to empty list."""
        clarifier_input = ClarifierInput(
            original_query="How should I adjust?",
            gaps=[],
            vocabulary={},
        )
        assert clarifier_input.previous_clarifications == []


# =============================================================================
# Test ClarifierOutput Model (Task 1.3)
# =============================================================================


class TestClarifierOutputModel:
    """Tests for ClarifierOutput Pydantic model validation."""

    def test_clarifier_output_valid(self) -> None:
        """ClarifierOutput accepts valid data."""
        question = ClarificationQuestion(
            question="How are you feeling?",
            gap_addressed="Current energy level unknown",
            options=["Tired", "Normal", "Energized"],
            required=True,
        )
        output = ClarifierOutput(
            questions=[question],
            context_explanation="To provide personalized advice, I need to know your current state",
            fallback_action="Provide general recommendations based on your history",
        )
        assert len(output.questions) == 1
        assert "personalized" in output.context_explanation
        assert "general" in output.fallback_action

    def test_clarifier_output_empty_questions_valid(self) -> None:
        """ClarifierOutput with empty questions list is valid."""
        output = ClarifierOutput(
            questions=[],
            context_explanation="No clarification needed",
            fallback_action="Proceed with available data",
        )
        assert output.questions == []

    def test_clarifier_output_empty_context_explanation_fails(self) -> None:
        """ClarifierOutput with empty context_explanation fails min_length=1."""
        with pytest.raises(ValidationError):
            ClarifierOutput(
                questions=[],
                context_explanation="",
                fallback_action="Proceed with available data",
            )

    def test_clarifier_output_empty_fallback_action_fails(self) -> None:
        """ClarifierOutput with empty fallback_action fails min_length=1."""
        with pytest.raises(ValidationError):
            ClarifierOutput(
                questions=[],
                context_explanation="No clarification needed",
                fallback_action="",
            )


# =============================================================================
# Test ClarifierAgent Instantiation (Task 2)
# =============================================================================


class TestClarifierAgentInstantiation:
    """Tests for ClarifierAgent class instantiation."""

    def test_clarifier_agent_creates_with_llm_client(self) -> None:
        """ClarifierAgent creates successfully with LLMClient."""
        client = create_mock_llm_client({})
        clarifier = ClarifierAgent(client)
        assert clarifier.llm_client is client

    def test_clarifier_agent_name_constant(self) -> None:
        """ClarifierAgent has correct AGENT_NAME constant."""
        client = create_mock_llm_client({})
        clarifier = ClarifierAgent(client)
        assert clarifier.AGENT_NAME == "clarifier"
        assert ClarifierAgent.AGENT_NAME == "clarifier"


# =============================================================================
# Test filter_non_retrievable_gaps Helper (Task 5.1)
# =============================================================================


class TestFilterNonRetrievableGaps:
    """Tests for filter_non_retrievable_gaps helper method."""

    def test_filter_keeps_subjective_gaps(self) -> None:
        """filter_non_retrievable_gaps keeps SUBJECTIVE gaps."""
        client = create_mock_llm_client({})
        clarifier = ClarifierAgent(client)

        subjective_gap = create_subjective_gap()
        gaps = [subjective_gap]

        result = clarifier.filter_non_retrievable_gaps(gaps)

        assert len(result) == 1
        assert result[0].gap_type == GapType.SUBJECTIVE

    def test_filter_keeps_clarification_gaps(self) -> None:
        """filter_non_retrievable_gaps keeps CLARIFICATION gaps."""
        client = create_mock_llm_client({})
        clarifier = ClarifierAgent(client)

        clarification_gap = create_clarification_gap()
        gaps = [clarification_gap]

        result = clarifier.filter_non_retrievable_gaps(gaps)

        assert len(result) == 1
        assert result[0].gap_type == GapType.CLARIFICATION

    def test_filter_removes_temporal_gaps(self) -> None:
        """filter_non_retrievable_gaps removes TEMPORAL gaps."""
        client = create_mock_llm_client({})
        clarifier = ClarifierAgent(client)

        temporal_gap = create_temporal_gap()
        gaps = [temporal_gap]

        result = clarifier.filter_non_retrievable_gaps(gaps)

        assert len(result) == 0

    def test_filter_removes_topical_gaps(self) -> None:
        """filter_non_retrievable_gaps removes TOPICAL gaps."""
        client = create_mock_llm_client({})
        clarifier = ClarifierAgent(client)

        topical_gap = create_topical_gap()
        gaps = [topical_gap]

        result = clarifier.filter_non_retrievable_gaps(gaps)

        assert len(result) == 0

    def test_filter_removes_contextual_gaps(self) -> None:
        """filter_non_retrievable_gaps removes CONTEXTUAL gaps."""
        client = create_mock_llm_client({})
        clarifier = ClarifierAgent(client)

        contextual_gap = Gap(
            description="Need related context",
            gap_type=GapType.CONTEXTUAL,
            severity="nice_to_have",
        )
        gaps = [contextual_gap]

        result = clarifier.filter_non_retrievable_gaps(gaps)

        assert len(result) == 0

    def test_filter_mixed_gaps(self) -> None:
        """filter_non_retrievable_gaps correctly filters mixed gap types."""
        client = create_mock_llm_client({})
        clarifier = ClarifierAgent(client)

        gaps = [
            create_subjective_gap(),
            create_temporal_gap(),
            create_clarification_gap(),
            create_topical_gap(),
        ]

        result = clarifier.filter_non_retrievable_gaps(gaps)

        assert len(result) == 2
        gap_types = {g.gap_type for g in result}
        assert gap_types == {GapType.SUBJECTIVE, GapType.CLARIFICATION}

    def test_filter_empty_list(self) -> None:
        """filter_non_retrievable_gaps handles empty list."""
        client = create_mock_llm_client({})
        clarifier = ClarifierAgent(client)

        result = clarifier.filter_non_retrievable_gaps([])

        assert result == []


# =============================================================================
# Test Prompt Building (Task 3)
# =============================================================================


class TestClarifierPromptBuilding:
    """Tests for ClarifierAgent.build_prompt method."""

    def test_prompt_includes_original_query(self) -> None:
        """Prompt includes the original query."""
        client = create_mock_llm_client({})
        clarifier = ClarifierAgent(client)

        clarifier_input = ClarifierInput(
            original_query="How should I adjust my workout today?",
            gaps=[create_subjective_gap()],
            vocabulary={},
        )
        prompt = clarifier.build_prompt(clarifier_input)

        assert "How should I adjust my workout today?" in prompt

    def test_prompt_includes_vocabulary(self) -> None:
        """Prompt includes vocabulary when provided."""
        client = create_mock_llm_client({})
        clarifier = ClarifierAgent(client)

        clarifier_input = ClarifierInput(
            original_query="How should I adjust?",
            gaps=[create_subjective_gap()],
            vocabulary={"rpe": "rate of perceived exertion", "pr": "personal record"},
        )
        prompt = clarifier.build_prompt(clarifier_input)

        assert "rpe" in prompt.lower()
        assert "rate of perceived exertion" in prompt.lower()

    def test_prompt_includes_gaps(self) -> None:
        """Prompt includes formatted gaps."""
        client = create_mock_llm_client({})
        clarifier = ClarifierAgent(client)

        clarifier_input = ClarifierInput(
            original_query="How should I adjust?",
            gaps=[create_subjective_gap()],
            vocabulary={},
        )
        prompt = clarifier.build_prompt(clarifier_input)

        assert "Current energy level unknown" in prompt
        assert "subjective" in prompt.lower()

    def test_prompt_includes_retrieval_history(self) -> None:
        """Prompt includes retrieval history when provided."""
        client = create_mock_llm_client({})
        clarifier = ClarifierAgent(client)

        clarifier_input = ClarifierInput(
            original_query="How should I adjust?",
            gaps=[create_subjective_gap()],
            vocabulary={},
            retrieval_history=[create_sample_retrieval_attempt()],
        )
        prompt = clarifier.build_prompt(clarifier_input)

        assert "date_range" in prompt.lower()
        assert "5 entries" in prompt.lower()

    def test_prompt_includes_previous_clarifications(self) -> None:
        """Prompt includes previous clarifications when provided."""
        client = create_mock_llm_client({})
        clarifier = ClarifierAgent(client)

        clarifier_input = ClarifierInput(
            original_query="How should I adjust?",
            gaps=[create_subjective_gap()],
            vocabulary={},
            previous_clarifications=[
                "When did you last exercise?",
                "What is your current goal?",
            ],
        )
        prompt = clarifier.build_prompt(clarifier_input)

        assert "When did you last exercise?" in prompt
        assert "What is your current goal?" in prompt

    def test_prompt_includes_do_not_reask_instruction(self) -> None:
        """Prompt includes instruction to not re-ask questions."""
        client = create_mock_llm_client({})
        clarifier = ClarifierAgent(client)

        clarifier_input = ClarifierInput(
            original_query="How should I adjust?",
            gaps=[create_subjective_gap()],
            vocabulary={},
        )
        prompt = clarifier.build_prompt(clarifier_input)

        assert "re-ask" in prompt.lower() or "re ask" in prompt.lower()

    def test_prompt_includes_max_3_questions_rule(self) -> None:
        """Prompt includes rule about maximum 3 questions."""
        client = create_mock_llm_client({})
        clarifier = ClarifierAgent(client)

        clarifier_input = ClarifierInput(
            original_query="How should I adjust?",
            gaps=[create_subjective_gap()],
            vocabulary={},
        )
        prompt = clarifier.build_prompt(clarifier_input)

        assert "3 questions" in prompt.lower() or "maximum 3" in prompt.lower()

    def test_prompt_includes_gap_type_guidance(self) -> None:
        """Prompt includes guidance about which gap types to ask about."""
        client = create_mock_llm_client({})
        clarifier = ClarifierAgent(client)

        clarifier_input = ClarifierInput(
            original_query="How should I adjust?",
            gaps=[create_subjective_gap()],
            vocabulary={},
        )
        prompt = clarifier.build_prompt(clarifier_input)

        # Should mention SUBJECTIVE and CLARIFICATION as types to ask about
        assert "subjective" in prompt.lower()
        assert "clarification" in prompt.lower()
        # Should mention not to ask about retrievable types
        assert "temporal" in prompt.lower()

    def test_prompt_includes_fallback_action_instruction(self) -> None:
        """Prompt includes instruction about fallback_action."""
        client = create_mock_llm_client({})
        clarifier = ClarifierAgent(client)

        clarifier_input = ClarifierInput(
            original_query="How should I adjust?",
            gaps=[create_subjective_gap()],
            vocabulary={},
        )
        prompt = clarifier.build_prompt(clarifier_input)

        assert "fallback" in prompt.lower()

    def test_prompt_handles_empty_vocabulary(self) -> None:
        """Prompt handles empty vocabulary gracefully."""
        client = create_mock_llm_client({})
        clarifier = ClarifierAgent(client)

        clarifier_input = ClarifierInput(
            original_query="How should I adjust?",
            gaps=[create_subjective_gap()],
            vocabulary={},
        )
        prompt = clarifier.build_prompt(clarifier_input)

        assert "(No domain vocabulary provided)" in prompt

    def test_prompt_handles_empty_retrieval_history(self) -> None:
        """Prompt handles empty retrieval history gracefully."""
        client = create_mock_llm_client({})
        clarifier = ClarifierAgent(client)

        clarifier_input = ClarifierInput(
            original_query="How should I adjust?",
            gaps=[create_subjective_gap()],
            vocabulary={},
            retrieval_history=[],
        )
        prompt = clarifier.build_prompt(clarifier_input)

        assert "(No retrieval attempts recorded)" in prompt

    def test_prompt_handles_empty_previous_clarifications(self) -> None:
        """Prompt handles empty previous clarifications gracefully."""
        client = create_mock_llm_client({})
        clarifier = ClarifierAgent(client)

        clarifier_input = ClarifierInput(
            original_query="How should I adjust?",
            gaps=[create_subjective_gap()],
            vocabulary={},
            previous_clarifications=[],
        )
        prompt = clarifier.build_prompt(clarifier_input)

        assert "first attempt" in prompt.lower() or "(No previous" in prompt


# =============================================================================
# Test has_questions Helper (Task 5.6)
# =============================================================================


class TestHasQuestionsHelper:
    """Tests for has_questions helper method."""

    def test_has_questions_true_when_non_empty(self) -> None:
        """has_questions returns True when questions list is non-empty."""
        client = create_mock_llm_client({})
        clarifier = ClarifierAgent(client)

        output = ClarifierOutput(
            questions=[
                ClarificationQuestion(
                    question="How are you feeling?",
                    gap_addressed="Current state unknown",
                )
            ],
            context_explanation="Need to know your state",
            fallback_action="Provide general advice",
        )

        assert clarifier.has_questions(output) is True

    def test_has_questions_false_when_empty(self) -> None:
        """has_questions returns False when questions list is empty."""
        client = create_mock_llm_client({})
        clarifier = ClarifierAgent(client)

        output = ClarifierOutput(
            questions=[],
            context_explanation="No clarification needed",
            fallback_action="Proceed with available data",
        )

        assert clarifier.has_questions(output) is False


# =============================================================================
# Test Clarify Method (Task 4)
# =============================================================================


class TestClarifyMethod:
    """Tests for ClarifierAgent.clarify method."""

    @pytest.mark.asyncio
    async def test_successful_clarification_with_subjective_gap(self) -> None:
        """Test successful clarification with subjective gap."""
        response: dict[str, Any] = {
            "questions": [
                {
                    "question": "How are you feeling right now?",
                    "gap_addressed": "Current energy level unknown",
                    "options": ["Tired", "Normal", "Energized"],
                    "required": True,
                }
            ],
            "context_explanation": "To provide personalized workout advice, I need to know your current energy level",
            "fallback_action": "Provide general workout recommendations based on your history",
        }
        client = create_mock_llm_client(response)
        clarifier = ClarifierAgent(client)

        result = await clarifier.clarify(
            ClarifierInput(
                original_query="How should I adjust my workout today?",
                gaps=[create_subjective_gap()],
                vocabulary={"rpe": "rate of perceived exertion"},
            )
        )

        assert len(result.questions) == 1
        assert "feeling" in result.questions[0].question.lower()
        assert result.context_explanation is not None
        assert result.fallback_action is not None

    @pytest.mark.asyncio
    async def test_clarification_with_clarification_gap(self) -> None:
        """Test clarification with ambiguous query gap."""
        response: dict[str, Any] = {
            "questions": [
                {
                    "question": "Which workout are you asking about?",
                    "gap_addressed": "Query is ambiguous - which workout?",
                    "options": ["Yesterday's workout", "Today's workout", "Weekly routine"],
                    "required": True,
                }
            ],
            "context_explanation": "Your question could refer to different workouts",
            "fallback_action": "Answer about your most recent workout",
        }
        client = create_mock_llm_client(response)
        clarifier = ClarifierAgent(client)

        result = await clarifier.clarify(
            ClarifierInput(
                original_query="How was my workout?",
                gaps=[create_clarification_gap()],
                vocabulary={},
            )
        )

        assert len(result.questions) == 1
        assert "which" in result.questions[0].question.lower()

    @pytest.mark.asyncio
    async def test_no_llm_call_when_only_retrievable_gaps(self) -> None:
        """Test that no LLM call is made when only retrievable gaps exist."""
        response: dict[str, Any] = {}  # Should not be called
        client = create_mock_llm_client(response)
        clarifier = ClarifierAgent(client)

        result = await clarifier.clarify(
            ClarifierInput(
                original_query="Show me last week's workouts",
                gaps=[create_temporal_gap(), create_topical_gap()],
                vocabulary={},
            )
        )

        # Should return empty output without calling LLM
        assert result.questions == []
        assert result.context_explanation == "No clarification needed"
        assert result.fallback_action == "Proceed with available data"
        # Verify no LLM call was made
        client.complete_structured.assert_not_called()  # type: ignore[union-attr]

    @pytest.mark.asyncio
    async def test_no_llm_call_when_empty_gaps(self) -> None:
        """Test that no LLM call is made when gaps list is empty."""
        response: dict[str, Any] = {}  # Should not be called
        client = create_mock_llm_client(response)
        clarifier = ClarifierAgent(client)

        result = await clarifier.clarify(
            ClarifierInput(
                original_query="Show me my workouts",
                gaps=[],
                vocabulary={},
            )
        )

        # Should return empty output without calling LLM
        assert result.questions == []
        assert result.context_explanation == "No clarification needed"
        client.complete_structured.assert_not_called()  # type: ignore[union-attr]

    @pytest.mark.asyncio
    async def test_max_3_questions_post_processing(self) -> None:
        """Test that output is limited to max 3 questions via post-processing."""
        response: dict[str, Any] = {
            "questions": [
                {"question": "Q1?", "gap_addressed": "Gap 1", "options": None, "required": True},
                {"question": "Q2?", "gap_addressed": "Gap 2", "options": None, "required": True},
                {"question": "Q3?", "gap_addressed": "Gap 3", "options": None, "required": True},
                {"question": "Q4?", "gap_addressed": "Gap 4", "options": None, "required": True},
                {"question": "Q5?", "gap_addressed": "Gap 5", "options": None, "required": True},
            ],
            "context_explanation": "Multiple questions needed",
            "fallback_action": "Proceed with partial info",
        }
        client = create_mock_llm_client(response)
        clarifier = ClarifierAgent(client)

        result = await clarifier.clarify(
            ClarifierInput(
                original_query="Complex query?",
                gaps=[create_subjective_gap(), create_clarification_gap()],
                vocabulary={},
            )
        )

        # Should be limited to MAX_QUESTIONS
        assert len(result.questions) == ClarifierAgent.MAX_QUESTIONS
        # First 3 questions should be preserved
        assert result.questions[0].question == "Q1?"
        assert result.questions[1].question == "Q2?"
        assert result.questions[2].question == "Q3?"

    @pytest.mark.asyncio
    async def test_empty_query_raises_value_error(self) -> None:
        """Test that empty query raises ValueError."""
        client = create_mock_llm_client({})
        clarifier = ClarifierAgent(client)

        # Pydantic catches empty string first
        with pytest.raises(ValidationError):
            await clarifier.clarify(
                ClarifierInput(
                    original_query="",
                    gaps=[create_subjective_gap()],
                    vocabulary={},
                )
            )

    @pytest.mark.asyncio
    async def test_whitespace_only_query_raises_value_error(self) -> None:
        """Test that whitespace-only query raises ValueError."""
        client = create_mock_llm_client({})
        clarifier = ClarifierAgent(client)

        with pytest.raises(ValueError, match="empty or whitespace"):
            await clarifier.clarify(
                ClarifierInput(
                    original_query="   \n\t  ",
                    gaps=[create_subjective_gap()],
                    vocabulary={},
                )
            )

    @pytest.mark.asyncio
    async def test_previous_clarifications_not_reask_instruction_in_prompt(self) -> None:
        """Test that previous clarifications are included in prompt to avoid re-asking."""
        response: dict[str, Any] = {
            "questions": [
                {
                    "question": "How are you feeling?",
                    "gap_addressed": "Current state",
                    "options": None,
                    "required": True,
                }
            ],
            "context_explanation": "Need current state",
            "fallback_action": "Provide general advice",
        }
        client = create_mock_llm_client(response)
        clarifier = ClarifierAgent(client)

        await clarifier.clarify(
            ClarifierInput(
                original_query="How should I adjust?",
                gaps=[create_subjective_gap()],
                vocabulary={},
                previous_clarifications=["When did you last exercise?"],
            )
        )

        # Verify the prompt includes the previous clarification
        call_args = client.complete_structured.call_args  # type: ignore[union-attr]
        messages = call_args[1]["messages"]  # pyright: ignore[reportUnknownVariableType]
        system_prompt = messages[0]["content"]  # pyright: ignore[reportUnknownVariableType]
        assert "When did you last exercise?" in system_prompt


# =============================================================================
# Test Exports (Task 6)
# =============================================================================


class TestClarifierExports:
    """Tests for clarifier exports from quilto.agents."""

    def test_clarifier_agent_importable(self) -> None:
        """ClarifierAgent is importable from quilto.agents."""
        from quilto.agents import ClarifierAgent

        assert ClarifierAgent is not None

    def test_clarification_question_importable(self) -> None:
        """ClarificationQuestion is importable from quilto.agents."""
        from quilto.agents import ClarificationQuestion

        assert ClarificationQuestion is not None

    def test_clarifier_input_importable(self) -> None:
        """ClarifierInput is importable from quilto.agents."""
        from quilto.agents import ClarifierInput

        assert ClarifierInput is not None

    def test_clarifier_output_importable(self) -> None:
        """ClarifierOutput is importable from quilto.agents."""
        from quilto.agents import ClarifierOutput

        assert ClarifierOutput is not None

    def test_all_exports_in_all_list(self) -> None:
        """All clarifier types are in __all__ list."""
        from quilto import agents

        assert "ClarifierAgent" in agents.__all__
        assert "ClarificationQuestion" in agents.__all__
        assert "ClarifierInput" in agents.__all__
        assert "ClarifierOutput" in agents.__all__


# =============================================================================
# Integration Tests
# =============================================================================


class TestClarifierIntegration:
    """Integration tests with real Ollama.

    Run with: pytest --use-real-ollama -k TestClarifierIntegration
    Or via: make test-ollama
    """

    @pytest.mark.asyncio
    async def test_real_clarification_with_subjective_gap(
        self, use_real_ollama: bool, integration_llm_config_path: Path
    ) -> None:
        """Test real clarification with subjective gap."""
        if not use_real_ollama:
            pytest.skip("Requires --use-real-ollama flag")

        config = load_llm_config(integration_llm_config_path)
        real_llm_client = LLMClient(config)
        clarifier = ClarifierAgent(real_llm_client)

        result = await clarifier.clarify(
            ClarifierInput(
                original_query="How should I adjust my workout intensity today?",
                gaps=[
                    Gap(
                        description="Current energy level and how user is feeling today",
                        gap_type=GapType.SUBJECTIVE,
                        severity="critical",
                    )
                ],
                vocabulary={"rpe": "rate of perceived exertion", "pr": "personal record"},
            )
        )

        # Should have valid output structure
        assert result.context_explanation is not None
        assert len(result.context_explanation) > 0
        assert result.fallback_action is not None
        assert len(result.fallback_action) > 0
        # Should have generated at least one question (or empty if no gaps)
        # With a subjective gap, should ask a question
        assert len(result.questions) >= 1
        assert len(result.questions) <= 3

    @pytest.mark.asyncio
    async def test_real_clarification_with_ambiguous_query(
        self, use_real_ollama: bool, integration_llm_config_path: Path
    ) -> None:
        """Test real clarification with ambiguous query gap."""
        if not use_real_ollama:
            pytest.skip("Requires --use-real-ollama flag")

        config = load_llm_config(integration_llm_config_path)
        real_llm_client = LLMClient(config)
        clarifier = ClarifierAgent(real_llm_client)

        result = await clarifier.clarify(
            ClarifierInput(
                original_query="How was it?",
                gaps=[
                    Gap(
                        description="Query is too vague - what is 'it' referring to?",
                        gap_type=GapType.CLARIFICATION,
                        severity="critical",
                    )
                ],
                vocabulary={},
            )
        )

        # Should have valid output structure
        assert result.context_explanation is not None
        assert result.fallback_action is not None
        # Should have generated question(s) to clarify
        assert len(result.questions) >= 1
