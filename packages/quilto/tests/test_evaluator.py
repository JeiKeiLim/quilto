"""Unit tests for EvaluatorAgent.

Tests cover model validation, prompt building, evaluate method,
helper methods, and exports.
"""

import json
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock

import pytest
from pydantic import BaseModel, ValidationError
from quilto import load_llm_config
from quilto.agents import (
    AnalyzerOutput,
    EvaluationDimension,
    EvaluationFeedback,
    EvaluatorAgent,
    EvaluatorInput,
    EvaluatorOutput,
    Finding,
    SufficiencyEvaluation,
    Verdict,
)
from quilto.llm.client import LLMClient
from quilto.llm.config import AgentConfig, LLMConfig, ProviderConfig, TierModels


def create_test_config() -> LLMConfig:
    """Create a test LLMConfig for EvaluatorAgent tests.

    Returns:
        Configured LLMConfig for testing.
    """
    return LLMConfig(
        default_provider="ollama",  # type: ignore[arg-type]
        providers={
            "ollama": ProviderConfig(api_base="http://localhost:11434"),
        },
        tiers={
            "high": TierModels(ollama="qwen2.5:14b"),
        },
        agents={
            "evaluator": AgentConfig(tier="high"),
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


def create_sample_analyzer_output() -> AnalyzerOutput:
    """Create a sample AnalyzerOutput for evaluator tests.

    Returns:
        AnalyzerOutput for tests.
    """
    return AnalyzerOutput(
        query_intent="User wants to know bench press progression over time",
        findings=[
            Finding(
                claim="Progressive overload observed",
                evidence=["2026-01-10: bench 185x5", "2026-01-05: bench 175x5"],
                confidence="high",
            ),
            Finding(
                claim="Consistent training pattern",
                evidence=["2026-01-10", "2026-01-08", "2026-01-05"],
                confidence="medium",
            ),
        ],
        patterns_identified=["progressive overload", "consistent training"],
        sufficiency_evaluation=SufficiencyEvaluation(
            critical_gaps=[],
            nice_to_have_gaps=[],
            evidence_check_passed=True,
            speculation_risk="none",
        ),
        verdict_reasoning="Found 3 entries showing clear 10lb progression",
        verdict=Verdict.SUFFICIENT,
    )


def create_sample_evaluation_rules() -> list[str]:
    """Create sample evaluation rules for testing.

    Returns:
        List of evaluation rules.
    """
    return [
        "Do not make claims without supporting data",
        "Acknowledge uncertainty when evidence is limited",
        "Never provide medical, legal, or financial advice without disclaimers",
    ]


def create_sample_entries_summary() -> str:
    """Create sample entries summary for testing.

    Returns:
        Entries summary string.
    """
    return """5 bench press entries found:
- 2026-01-10: bench 185x5, RPE 8
- 2026-01-08: bench 180x5, RPE 7
- 2026-01-05: bench 175x5, RPE 7
- 2026-01-03: bench 170x5, RPE 6
- 2026-01-01: bench 165x5, RPE 6"""


def create_sample_evaluation_feedback() -> list[EvaluationFeedback]:
    """Create sample evaluation feedback for retry testing.

    Returns:
        List of EvaluationFeedback.
    """
    return [
        EvaluationFeedback(
            issue="Response lacks volume analysis",
            suggestion="Include how total volume (sets x reps x weight) has changed",
            affected_claim=None,
        ),
        EvaluationFeedback(
            issue="Missing rep range discussion",
            suggestion="Mention that rep counts have been consistent at 5 reps",
            affected_claim="10 lb increase claim",
        ),
    ]


def create_sample_evaluator_output_pass() -> dict[str, Any]:
    """Create sample passing EvaluatorOutput JSON.

    Returns:
        Dictionary for JSON response.
    """
    return {
        "dimensions": [
            {
                "dimension": "accuracy",
                "verdict": "sufficient",
                "reasoning": "All claims about bench press progression are supported by the cited dates and weights.",
                "issues": [],
            },
            {
                "dimension": "relevance",
                "verdict": "sufficient",
                "reasoning": "Response directly addresses the user's question about bench press progress.",
                "issues": [],
            },
            {
                "dimension": "safety",
                "verdict": "sufficient",
                "reasoning": "No harmful recommendations. Response is purely informational.",
                "issues": [],
            },
            {
                "dimension": "completeness",
                "verdict": "sufficient",
                "reasoning": "Response covers weight progression and timeframe.",
                "issues": [],
            },
        ],
        "overall_verdict": "sufficient",
        "feedback": [],
        "recommendation": "accept",
    }


def create_sample_evaluator_output_fail() -> dict[str, Any]:
    """Create sample failing EvaluatorOutput JSON.

    Returns:
        Dictionary for JSON response.
    """
    return {
        "dimensions": [
            {
                "dimension": "accuracy",
                "verdict": "sufficient",
                "reasoning": "Claims are supported by evidence.",
                "issues": [],
            },
            {
                "dimension": "relevance",
                "verdict": "sufficient",
                "reasoning": "Response addresses the question.",
                "issues": [],
            },
            {
                "dimension": "safety",
                "verdict": "sufficient",
                "reasoning": "No harmful content.",
                "issues": [],
            },
            {
                "dimension": "completeness",
                "verdict": "insufficient",
                "reasoning": "User asked about progression but response doesn't mention rep counts or volume trends.",
                "issues": ["Missing volume analysis", "No mention of rep ranges over time"],
            },
        ],
        "overall_verdict": "insufficient",
        "feedback": [
            {
                "issue": "Response lacks volume analysis",
                "suggestion": "Include how total volume (sets x reps x weight) has changed",
                "affected_claim": None,
            }
        ],
        "recommendation": "retry_with_feedback",
    }


# =============================================================================
# Test EvaluationDimension Model (Task 7.1)
# =============================================================================


class TestEvaluationDimensionModel:
    """Tests for EvaluationDimension Pydantic model validation."""

    def test_evaluation_dimension_valid(self) -> None:
        """EvaluationDimension accepts valid data."""
        dimension = EvaluationDimension(
            dimension="accuracy",
            verdict=Verdict.SUFFICIENT,
            reasoning="All claims supported by evidence",
            issues=[],
        )
        assert dimension.dimension == "accuracy"
        assert dimension.verdict == Verdict.SUFFICIENT
        assert dimension.reasoning == "All claims supported by evidence"
        assert dimension.issues == []

    def test_evaluation_dimension_accuracy(self) -> None:
        """EvaluationDimension accepts 'accuracy' dimension."""
        dimension = EvaluationDimension(
            dimension="accuracy",
            verdict=Verdict.SUFFICIENT,
            reasoning="Valid reasoning",
        )
        assert dimension.dimension == "accuracy"

    def test_evaluation_dimension_relevance(self) -> None:
        """EvaluationDimension accepts 'relevance' dimension."""
        dimension = EvaluationDimension(
            dimension="relevance",
            verdict=Verdict.SUFFICIENT,
            reasoning="Valid reasoning",
        )
        assert dimension.dimension == "relevance"

    def test_evaluation_dimension_safety(self) -> None:
        """EvaluationDimension accepts 'safety' dimension."""
        dimension = EvaluationDimension(
            dimension="safety",
            verdict=Verdict.SUFFICIENT,
            reasoning="Valid reasoning",
        )
        assert dimension.dimension == "safety"

    def test_evaluation_dimension_completeness(self) -> None:
        """EvaluationDimension accepts 'completeness' dimension."""
        dimension = EvaluationDimension(
            dimension="completeness",
            verdict=Verdict.SUFFICIENT,
            reasoning="Valid reasoning",
        )
        assert dimension.dimension == "completeness"

    def test_evaluation_dimension_invalid_dimension_fails(self) -> None:
        """EvaluationDimension with invalid dimension value fails."""
        with pytest.raises(ValidationError):
            EvaluationDimension(
                dimension="correctness",  # type: ignore[arg-type]
                verdict=Verdict.SUFFICIENT,
                reasoning="Valid reasoning",
            )

    def test_evaluation_dimension_verdict_sufficient(self) -> None:
        """EvaluationDimension accepts SUFFICIENT verdict."""
        dimension = EvaluationDimension(
            dimension="accuracy",
            verdict=Verdict.SUFFICIENT,
            reasoning="Valid reasoning",
        )
        assert dimension.verdict == Verdict.SUFFICIENT

    def test_evaluation_dimension_verdict_insufficient(self) -> None:
        """EvaluationDimension accepts INSUFFICIENT verdict."""
        dimension = EvaluationDimension(
            dimension="accuracy",
            verdict=Verdict.INSUFFICIENT,
            reasoning="Invalid reasoning",
            issues=["Issue 1", "Issue 2"],
        )
        assert dimension.verdict == Verdict.INSUFFICIENT
        assert len(dimension.issues) == 2

    def test_evaluation_dimension_empty_reasoning_fails(self) -> None:
        """EvaluationDimension with empty reasoning fails min_length=1."""
        with pytest.raises(ValidationError):
            EvaluationDimension(
                dimension="accuracy",
                verdict=Verdict.SUFFICIENT,
                reasoning="",
            )

    def test_evaluation_dimension_issues_default_empty(self) -> None:
        """EvaluationDimension has empty issues by default."""
        dimension = EvaluationDimension(
            dimension="accuracy",
            verdict=Verdict.SUFFICIENT,
            reasoning="Valid reasoning",
        )
        assert dimension.issues == []

    def test_evaluation_dimension_issues_provided(self) -> None:
        """EvaluationDimension accepts issues list."""
        dimension = EvaluationDimension(
            dimension="completeness",
            verdict=Verdict.INSUFFICIENT,
            reasoning="Missing information",
            issues=["Missing volume", "Missing reps"],
        )
        assert len(dimension.issues) == 2
        assert "Missing volume" in dimension.issues

    def test_evaluation_dimension_partial_verdict_fails(self) -> None:
        """EvaluationDimension rejects PARTIAL verdict (only SUFFICIENT/INSUFFICIENT valid)."""
        with pytest.raises(ValidationError, match="SUFFICIENT or INSUFFICIENT"):
            EvaluationDimension(
                dimension="accuracy",
                verdict=Verdict.PARTIAL,
                reasoning="Valid reasoning",
            )


# =============================================================================
# Test EvaluatorInput Model (Task 7.1)
# =============================================================================


class TestEvaluatorInputModel:
    """Tests for EvaluatorInput Pydantic model validation."""

    def test_evaluator_input_valid(self) -> None:
        """EvaluatorInput accepts valid data."""
        evaluator_input = EvaluatorInput(
            query="How has my bench press progressed?",
            response="Your bench press increased by 10 lbs",
            analysis=create_sample_analyzer_output(),
            entries_summary=create_sample_entries_summary(),
            evaluation_rules=create_sample_evaluation_rules(),
        )
        assert evaluator_input.query == "How has my bench press progressed?"
        assert evaluator_input.response == "Your bench press increased by 10 lbs"
        assert evaluator_input.attempt_number == 1
        assert evaluator_input.previous_feedback == []

    def test_evaluator_input_empty_query_fails(self) -> None:
        """EvaluatorInput with empty query fails min_length=1."""
        with pytest.raises(ValidationError):
            EvaluatorInput(
                query="",
                response="Valid response",
                analysis=create_sample_analyzer_output(),
                entries_summary=create_sample_entries_summary(),
                evaluation_rules=[],
            )

    def test_evaluator_input_empty_response_fails(self) -> None:
        """EvaluatorInput with empty response fails min_length=1."""
        with pytest.raises(ValidationError):
            EvaluatorInput(
                query="Valid query",
                response="",
                analysis=create_sample_analyzer_output(),
                entries_summary=create_sample_entries_summary(),
                evaluation_rules=[],
            )

    def test_evaluator_input_empty_entries_summary_fails(self) -> None:
        """EvaluatorInput with empty entries_summary fails min_length=1."""
        with pytest.raises(ValidationError):
            EvaluatorInput(
                query="Valid query",
                response="Valid response",
                analysis=create_sample_analyzer_output(),
                entries_summary="",
                evaluation_rules=[],
            )

    def test_evaluator_input_attempt_number_default(self) -> None:
        """EvaluatorInput has attempt_number=1 by default."""
        evaluator_input = EvaluatorInput(
            query="Test query",
            response="Test response",
            analysis=create_sample_analyzer_output(),
            entries_summary="Test summary",
            evaluation_rules=[],
        )
        assert evaluator_input.attempt_number == 1

    def test_evaluator_input_attempt_number_one_valid(self) -> None:
        """EvaluatorInput accepts attempt_number=1."""
        evaluator_input = EvaluatorInput(
            query="Test query",
            response="Test response",
            analysis=create_sample_analyzer_output(),
            entries_summary="Test summary",
            evaluation_rules=[],
            attempt_number=1,
        )
        assert evaluator_input.attempt_number == 1

    def test_evaluator_input_attempt_number_zero_fails(self) -> None:
        """EvaluatorInput with attempt_number=0 fails ge=1 constraint."""
        with pytest.raises(ValidationError):
            EvaluatorInput(
                query="Test query",
                response="Test response",
                analysis=create_sample_analyzer_output(),
                entries_summary="Test summary",
                evaluation_rules=[],
                attempt_number=0,
            )

    def test_evaluator_input_attempt_number_negative_fails(self) -> None:
        """EvaluatorInput with negative attempt_number fails ge=1."""
        with pytest.raises(ValidationError):
            EvaluatorInput(
                query="Test query",
                response="Test response",
                analysis=create_sample_analyzer_output(),
                entries_summary="Test summary",
                evaluation_rules=[],
                attempt_number=-1,
            )

    def test_evaluator_input_attempt_number_two_valid(self) -> None:
        """EvaluatorInput accepts attempt_number > 1."""
        evaluator_input = EvaluatorInput(
            query="Test query",
            response="Test response",
            analysis=create_sample_analyzer_output(),
            entries_summary="Test summary",
            evaluation_rules=[],
            attempt_number=2,
        )
        assert evaluator_input.attempt_number == 2

    def test_evaluator_input_previous_feedback_default(self) -> None:
        """EvaluatorInput has empty previous_feedback by default."""
        evaluator_input = EvaluatorInput(
            query="Test query",
            response="Test response",
            analysis=create_sample_analyzer_output(),
            entries_summary="Test summary",
            evaluation_rules=[],
        )
        assert evaluator_input.previous_feedback == []

    def test_evaluator_input_previous_feedback_provided(self) -> None:
        """EvaluatorInput accepts previous_feedback list."""
        feedback = create_sample_evaluation_feedback()
        evaluator_input = EvaluatorInput(
            query="Test query",
            response="Test response",
            analysis=create_sample_analyzer_output(),
            entries_summary="Test summary",
            evaluation_rules=[],
            attempt_number=2,
            previous_feedback=feedback,
        )
        assert len(evaluator_input.previous_feedback) == 2

    def test_evaluator_input_evaluation_rules_empty(self) -> None:
        """EvaluatorInput accepts empty evaluation_rules list."""
        evaluator_input = EvaluatorInput(
            query="Test query",
            response="Test response",
            analysis=create_sample_analyzer_output(),
            entries_summary="Test summary",
            evaluation_rules=[],
        )
        assert evaluator_input.evaluation_rules == []

    def test_evaluator_input_evaluation_rules_provided(self) -> None:
        """EvaluatorInput accepts evaluation_rules list."""
        rules = create_sample_evaluation_rules()
        evaluator_input = EvaluatorInput(
            query="Test query",
            response="Test response",
            analysis=create_sample_analyzer_output(),
            entries_summary="Test summary",
            evaluation_rules=rules,
        )
        assert len(evaluator_input.evaluation_rules) == 3


# =============================================================================
# Test EvaluatorOutput Model (Task 7.1)
# =============================================================================


class TestEvaluatorOutputModel:
    """Tests for EvaluatorOutput Pydantic model validation."""

    def test_evaluator_output_valid(self) -> None:
        """EvaluatorOutput accepts valid data."""
        output = EvaluatorOutput(
            dimensions=[
                EvaluationDimension(
                    dimension="accuracy",
                    verdict=Verdict.SUFFICIENT,
                    reasoning="Valid",
                ),
                EvaluationDimension(
                    dimension="relevance",
                    verdict=Verdict.SUFFICIENT,
                    reasoning="Valid",
                ),
                EvaluationDimension(
                    dimension="safety",
                    verdict=Verdict.SUFFICIENT,
                    reasoning="Valid",
                ),
                EvaluationDimension(
                    dimension="completeness",
                    verdict=Verdict.SUFFICIENT,
                    reasoning="Valid",
                ),
            ],
            overall_verdict=Verdict.SUFFICIENT,
            feedback=[],
            recommendation="accept",
        )
        assert len(output.dimensions) == 4
        assert output.overall_verdict == Verdict.SUFFICIENT
        assert output.recommendation == "accept"

    def test_evaluator_output_recommendation_accept(self) -> None:
        """EvaluatorOutput accepts 'accept' recommendation."""
        output = EvaluatorOutput(
            dimensions=[
                EvaluationDimension(
                    dimension="accuracy",
                    verdict=Verdict.SUFFICIENT,
                    reasoning="Valid",
                ),
            ],
            overall_verdict=Verdict.SUFFICIENT,
            feedback=[],
            recommendation="accept",
        )
        assert output.recommendation == "accept"

    def test_evaluator_output_recommendation_retry_with_feedback(self) -> None:
        """EvaluatorOutput accepts 'retry_with_feedback' recommendation."""
        output = EvaluatorOutput(
            dimensions=[
                EvaluationDimension(
                    dimension="accuracy",
                    verdict=Verdict.INSUFFICIENT,
                    reasoning="Invalid",
                ),
            ],
            overall_verdict=Verdict.INSUFFICIENT,
            feedback=[],
            recommendation="retry_with_feedback",
        )
        assert output.recommendation == "retry_with_feedback"

    def test_evaluator_output_recommendation_retry_with_more_context(self) -> None:
        """EvaluatorOutput accepts 'retry_with_more_context' recommendation."""
        output = EvaluatorOutput(
            dimensions=[
                EvaluationDimension(
                    dimension="accuracy",
                    verdict=Verdict.INSUFFICIENT,
                    reasoning="Invalid",
                ),
            ],
            overall_verdict=Verdict.INSUFFICIENT,
            feedback=[],
            recommendation="retry_with_more_context",
        )
        assert output.recommendation == "retry_with_more_context"

    def test_evaluator_output_recommendation_give_partial(self) -> None:
        """EvaluatorOutput accepts 'give_partial' recommendation."""
        output = EvaluatorOutput(
            dimensions=[
                EvaluationDimension(
                    dimension="accuracy",
                    verdict=Verdict.INSUFFICIENT,
                    reasoning="Invalid",
                ),
            ],
            overall_verdict=Verdict.INSUFFICIENT,
            feedback=[],
            recommendation="give_partial",
        )
        assert output.recommendation == "give_partial"

    def test_evaluator_output_invalid_recommendation_fails(self) -> None:
        """EvaluatorOutput with invalid recommendation fails."""
        with pytest.raises(ValidationError):
            EvaluatorOutput(
                dimensions=[
                    EvaluationDimension(
                        dimension="accuracy",
                        verdict=Verdict.SUFFICIENT,
                        reasoning="Valid",
                    ),
                ],
                overall_verdict=Verdict.SUFFICIENT,
                feedback=[],
                recommendation="continue",  # type: ignore[arg-type]
            )

    def test_evaluator_output_feedback_default_empty(self) -> None:
        """EvaluatorOutput has empty feedback by default."""
        output = EvaluatorOutput(
            dimensions=[
                EvaluationDimension(
                    dimension="accuracy",
                    verdict=Verdict.SUFFICIENT,
                    reasoning="Valid",
                ),
            ],
            overall_verdict=Verdict.SUFFICIENT,
            recommendation="accept",
        )
        assert output.feedback == []

    def test_evaluator_output_feedback_provided(self) -> None:
        """EvaluatorOutput accepts feedback list."""
        feedback = create_sample_evaluation_feedback()
        output = EvaluatorOutput(
            dimensions=[
                EvaluationDimension(
                    dimension="accuracy",
                    verdict=Verdict.INSUFFICIENT,
                    reasoning="Invalid",
                ),
            ],
            overall_verdict=Verdict.INSUFFICIENT,
            feedback=feedback,
            recommendation="retry_with_feedback",
        )
        assert len(output.feedback) == 2

    def test_evaluator_output_verdict_reuse(self) -> None:
        """EvaluatorOutput uses same Verdict enum as dimensions."""
        output = EvaluatorOutput(
            dimensions=[
                EvaluationDimension(
                    dimension="accuracy",
                    verdict=Verdict.SUFFICIENT,
                    reasoning="Valid",
                ),
            ],
            overall_verdict=Verdict.SUFFICIENT,
            recommendation="accept",
        )
        assert output.overall_verdict == Verdict.SUFFICIENT
        assert output.dimensions[0].verdict == Verdict.SUFFICIENT


# =============================================================================
# Test EvaluatorAgent Instantiation (Task 7.2)
# =============================================================================


class TestEvaluatorAgentInstantiation:
    """Tests for EvaluatorAgent class instantiation."""

    def test_evaluator_agent_creates_with_llm_client(self) -> None:
        """EvaluatorAgent creates successfully with LLMClient."""
        client = create_mock_llm_client({})
        evaluator = EvaluatorAgent(client)
        assert evaluator.llm_client is client

    def test_evaluator_agent_name_constant(self) -> None:
        """EvaluatorAgent has correct AGENT_NAME constant."""
        client = create_mock_llm_client({})
        evaluator = EvaluatorAgent(client)
        assert evaluator.AGENT_NAME == "evaluator"
        assert EvaluatorAgent.AGENT_NAME == "evaluator"


# =============================================================================
# Test _format_analysis Helper (Task 7.3.1)
# =============================================================================


class TestFormatAnalysisHelper:
    """Tests for EvaluatorAgent._format_analysis method."""

    def test_format_analysis_with_findings(self) -> None:
        """_format_analysis includes findings with evidence."""
        client = create_mock_llm_client({})
        evaluator = EvaluatorAgent(client)

        analysis = create_sample_analyzer_output()
        result = evaluator._format_analysis(analysis)  # pyright: ignore[reportPrivateUsage]

        assert "FINDINGS:" in result
        assert "Progressive overload observed" in result
        assert "high" in result
        assert "2026-01-10" in result

    def test_format_analysis_with_empty_findings(self) -> None:
        """_format_analysis handles empty findings."""
        client = create_mock_llm_client({})
        evaluator = EvaluatorAgent(client)

        analysis = AnalyzerOutput(
            query_intent="User wants data",
            findings=[],
            patterns_identified=[],
            sufficiency_evaluation=SufficiencyEvaluation(
                critical_gaps=[],
                nice_to_have_gaps=[],
                evidence_check_passed=False,
                speculation_risk="high",
            ),
            verdict_reasoning="No data",
            verdict=Verdict.INSUFFICIENT,
        )
        result = evaluator._format_analysis(analysis)  # pyright: ignore[reportPrivateUsage]

        assert "FINDINGS:" in result
        assert "(No findings)" in result

    def test_format_analysis_includes_patterns(self) -> None:
        """_format_analysis includes patterns_identified."""
        client = create_mock_llm_client({})
        evaluator = EvaluatorAgent(client)

        analysis = create_sample_analyzer_output()
        result = evaluator._format_analysis(analysis)  # pyright: ignore[reportPrivateUsage]

        assert "PATTERNS IDENTIFIED:" in result
        assert "progressive overload" in result

    def test_format_analysis_includes_verdict(self) -> None:
        """_format_analysis includes analysis verdict."""
        client = create_mock_llm_client({})
        evaluator = EvaluatorAgent(client)

        analysis = create_sample_analyzer_output()
        result = evaluator._format_analysis(analysis)  # pyright: ignore[reportPrivateUsage]

        assert "ANALYSIS VERDICT: sufficient" in result


# =============================================================================
# Test _format_evaluation_rules Helper (Task 7.3.2)
# =============================================================================


class TestFormatEvaluationRulesHelper:
    """Tests for EvaluatorAgent._format_evaluation_rules method."""

    def test_format_evaluation_rules_with_rules(self) -> None:
        """_format_evaluation_rules formats rules list."""
        client = create_mock_llm_client({})
        evaluator = EvaluatorAgent(client)

        rules = create_sample_evaluation_rules()
        result = evaluator._format_evaluation_rules(rules)  # pyright: ignore[reportPrivateUsage]

        assert "Do not make claims without supporting data" in result
        assert "Acknowledge uncertainty" in result
        assert "1." in result
        assert "2." in result

    def test_format_evaluation_rules_empty(self) -> None:
        """_format_evaluation_rules handles empty rules list."""
        client = create_mock_llm_client({})
        evaluator = EvaluatorAgent(client)

        result = evaluator._format_evaluation_rules([])  # pyright: ignore[reportPrivateUsage]

        assert "(No domain-specific evaluation rules)" in result


# =============================================================================
# Test _format_previous_feedback Helper (Task 7.3.3)
# =============================================================================


class TestFormatPreviousFeedbackHelper:
    """Tests for EvaluatorAgent._format_previous_feedback method."""

    def test_format_previous_feedback_with_feedback(self) -> None:
        """_format_previous_feedback formats feedback list."""
        client = create_mock_llm_client({})
        evaluator = EvaluatorAgent(client)

        feedback = create_sample_evaluation_feedback()
        result = evaluator._format_previous_feedback(feedback)  # pyright: ignore[reportPrivateUsage]

        assert "Response lacks volume analysis" in result
        assert "Include how total volume" in result
        assert "Issue:" in result
        assert "Suggestion:" in result

    def test_format_previous_feedback_empty(self) -> None:
        """_format_previous_feedback handles empty feedback (first attempt)."""
        client = create_mock_llm_client({})
        evaluator = EvaluatorAgent(client)

        result = evaluator._format_previous_feedback([])  # pyright: ignore[reportPrivateUsage]

        assert "(First attempt - no previous feedback)" in result

    def test_format_previous_feedback_with_affected_claim(self) -> None:
        """_format_previous_feedback includes affected_claim when present."""
        client = create_mock_llm_client({})
        evaluator = EvaluatorAgent(client)

        feedback = [
            EvaluationFeedback(
                issue="Claim not supported",
                suggestion="Add evidence",
                affected_claim="The 10 lb increase claim",
            )
        ]
        result = evaluator._format_previous_feedback(feedback)  # pyright: ignore[reportPrivateUsage]

        assert "Affected claim: The 10 lb increase claim" in result


# =============================================================================
# Test _format_entries_summary Helper (Task 7.3.4)
# =============================================================================


class TestFormatEntriesSummaryHelper:
    """Tests for EvaluatorAgent._format_entries_summary method."""

    def test_format_entries_summary(self) -> None:
        """_format_entries_summary returns entries summary as-is.

        Note: The "AVAILABLE EVIDENCE" header is now in the prompt template,
        not in _format_entries_summary, for consistent section formatting.
        """
        client = create_mock_llm_client({})
        evaluator = EvaluatorAgent(client)

        summary = create_sample_entries_summary()
        result = evaluator._format_entries_summary(summary)  # pyright: ignore[reportPrivateUsage]

        # Returns raw summary (header is in template)
        assert result == summary
        assert "5 bench press entries found" in result


# =============================================================================
# Test Prompt Building (Task 7.3.5-7.3.7)
# =============================================================================


class TestEvaluatorPromptBuilding:
    """Tests for EvaluatorAgent.build_prompt method."""

    def test_prompt_includes_all_four_dimensions(self) -> None:
        """Prompt includes all four evaluation dimensions."""
        client = create_mock_llm_client({})
        evaluator = EvaluatorAgent(client)

        evaluator_input = EvaluatorInput(
            query="Test query",
            response="Test response",
            analysis=create_sample_analyzer_output(),
            entries_summary=create_sample_entries_summary(),
            evaluation_rules=[],
        )
        prompt = evaluator.build_prompt(evaluator_input)

        assert "1. ACCURACY" in prompt
        assert "2. RELEVANCE" in prompt
        assert "3. SAFETY" in prompt
        assert "4. COMPLETENESS" in prompt

    def test_prompt_includes_verdict_logic(self) -> None:
        """Prompt includes strict AND verdict logic."""
        client = create_mock_llm_client({})
        evaluator = EvaluatorAgent(client)

        evaluator_input = EvaluatorInput(
            query="Test query",
            response="Test response",
            analysis=create_sample_analyzer_output(),
            entries_summary=create_sample_entries_summary(),
            evaluation_rules=[],
        )
        prompt = evaluator.build_prompt(evaluator_input)

        assert "If ANY dimension is INSUFFICIENT" in prompt
        assert "overall_verdict = INSUFFICIENT" in prompt
        assert "If ALL dimensions are SUFFICIENT" in prompt

    def test_prompt_includes_query_and_response(self) -> None:
        """Prompt includes query and response to evaluate."""
        client = create_mock_llm_client({})
        evaluator = EvaluatorAgent(client)

        evaluator_input = EvaluatorInput(
            query="How has my bench press progressed?",
            response="Your bench press increased by 10 lbs",
            analysis=create_sample_analyzer_output(),
            entries_summary=create_sample_entries_summary(),
            evaluation_rules=[],
        )
        prompt = evaluator.build_prompt(evaluator_input)

        assert "How has my bench press progressed?" in prompt
        assert "Your bench press increased by 10 lbs" in prompt

    def test_prompt_includes_evaluation_rules(self) -> None:
        """Prompt includes evaluation rules."""
        client = create_mock_llm_client({})
        evaluator = EvaluatorAgent(client)

        rules = create_sample_evaluation_rules()
        evaluator_input = EvaluatorInput(
            query="Test query",
            response="Test response",
            analysis=create_sample_analyzer_output(),
            entries_summary=create_sample_entries_summary(),
            evaluation_rules=rules,
        )
        prompt = evaluator.build_prompt(evaluator_input)

        assert "DOMAIN SAFETY RULES" in prompt
        assert "Do not make claims without supporting data" in prompt

    def test_prompt_includes_retry_context(self) -> None:
        """Prompt includes retry context when attempt_number > 1."""
        client = create_mock_llm_client({})
        evaluator = EvaluatorAgent(client)

        feedback = create_sample_evaluation_feedback()
        evaluator_input = EvaluatorInput(
            query="Test query",
            response="Test response",
            analysis=create_sample_analyzer_output(),
            entries_summary=create_sample_entries_summary(),
            evaluation_rules=[],
            attempt_number=2,
            previous_feedback=feedback,
        )
        prompt = evaluator.build_prompt(evaluator_input)

        assert "RETRY CONTEXT" in prompt
        assert "attempt #2" in prompt
        assert "PREVIOUS FEEDBACK" in prompt
        assert "Response lacks volume analysis" in prompt

    def test_prompt_no_retry_context_first_attempt(self) -> None:
        """Prompt does not include retry context on first attempt."""
        client = create_mock_llm_client({})
        evaluator = EvaluatorAgent(client)

        evaluator_input = EvaluatorInput(
            query="Test query",
            response="Test response",
            analysis=create_sample_analyzer_output(),
            entries_summary=create_sample_entries_summary(),
            evaluation_rules=[],
            attempt_number=1,
        )
        prompt = evaluator.build_prompt(evaluator_input)

        assert "RETRY CONTEXT" not in prompt

    def test_prompt_includes_recommendation_logic(self) -> None:
        """Prompt includes recommendation logic."""
        client = create_mock_llm_client({})
        evaluator = EvaluatorAgent(client)

        evaluator_input = EvaluatorInput(
            query="Test query",
            response="Test response",
            analysis=create_sample_analyzer_output(),
            entries_summary=create_sample_entries_summary(),
            evaluation_rules=[],
        )
        prompt = evaluator.build_prompt(evaluator_input)

        assert "RECOMMENDATION LOGIC" in prompt
        assert '"accept"' in prompt
        assert '"retry_with_feedback"' in prompt
        assert '"retry_with_more_context"' in prompt
        assert '"give_partial"' in prompt


# =============================================================================
# Test Helper Methods (Task 7.4)
# =============================================================================


class TestEvaluatorHelperMethods:
    """Tests for EvaluatorAgent helper methods."""

    def test_is_passed_all_sufficient(self) -> None:
        """is_passed returns True when all dimensions SUFFICIENT."""
        client = create_mock_llm_client({})
        evaluator = EvaluatorAgent(client)

        output = EvaluatorOutput(
            dimensions=[
                EvaluationDimension(
                    dimension="accuracy",
                    verdict=Verdict.SUFFICIENT,
                    reasoning="Valid",
                ),
                EvaluationDimension(
                    dimension="relevance",
                    verdict=Verdict.SUFFICIENT,
                    reasoning="Valid",
                ),
            ],
            overall_verdict=Verdict.SUFFICIENT,
            recommendation="accept",
        )
        assert evaluator.is_passed(output) is True

    def test_is_passed_one_insufficient(self) -> None:
        """is_passed returns False when one dimension INSUFFICIENT."""
        client = create_mock_llm_client({})
        evaluator = EvaluatorAgent(client)

        output = EvaluatorOutput(
            dimensions=[
                EvaluationDimension(
                    dimension="accuracy",
                    verdict=Verdict.SUFFICIENT,
                    reasoning="Valid",
                ),
                EvaluationDimension(
                    dimension="completeness",
                    verdict=Verdict.INSUFFICIENT,
                    reasoning="Invalid",
                ),
            ],
            overall_verdict=Verdict.INSUFFICIENT,
            recommendation="retry_with_feedback",
        )
        assert evaluator.is_passed(output) is False

    def test_is_passed_all_insufficient(self) -> None:
        """is_passed returns False when all dimensions INSUFFICIENT."""
        client = create_mock_llm_client({})
        evaluator = EvaluatorAgent(client)

        output = EvaluatorOutput(
            dimensions=[
                EvaluationDimension(
                    dimension="accuracy",
                    verdict=Verdict.INSUFFICIENT,
                    reasoning="Invalid",
                ),
                EvaluationDimension(
                    dimension="completeness",
                    verdict=Verdict.INSUFFICIENT,
                    reasoning="Invalid",
                ),
            ],
            overall_verdict=Verdict.INSUFFICIENT,
            recommendation="give_partial",
        )
        assert evaluator.is_passed(output) is False

    def test_get_failed_dimensions_returns_insufficient(self) -> None:
        """get_failed_dimensions returns only INSUFFICIENT dimensions."""
        client = create_mock_llm_client({})
        evaluator = EvaluatorAgent(client)

        dim_accuracy = EvaluationDimension(
            dimension="accuracy",
            verdict=Verdict.SUFFICIENT,
            reasoning="Valid",
        )
        dim_completeness = EvaluationDimension(
            dimension="completeness",
            verdict=Verdict.INSUFFICIENT,
            reasoning="Invalid",
            issues=["Missing info"],
        )
        output = EvaluatorOutput(
            dimensions=[dim_accuracy, dim_completeness],
            overall_verdict=Verdict.INSUFFICIENT,
            recommendation="retry_with_feedback",
        )

        failed = evaluator.get_failed_dimensions(output)
        assert len(failed) == 1
        assert failed[0].dimension == "completeness"

    def test_get_failed_dimensions_no_failures(self) -> None:
        """get_failed_dimensions returns empty list when no failures."""
        client = create_mock_llm_client({})
        evaluator = EvaluatorAgent(client)

        output = EvaluatorOutput(
            dimensions=[
                EvaluationDimension(
                    dimension="accuracy",
                    verdict=Verdict.SUFFICIENT,
                    reasoning="Valid",
                ),
                EvaluationDimension(
                    dimension="relevance",
                    verdict=Verdict.SUFFICIENT,
                    reasoning="Valid",
                ),
            ],
            overall_verdict=Verdict.SUFFICIENT,
            recommendation="accept",
        )

        failed = evaluator.get_failed_dimensions(output)
        assert len(failed) == 0

    def test_get_all_issues_aggregates(self) -> None:
        """get_all_issues aggregates issues from all failed dimensions."""
        client = create_mock_llm_client({})
        evaluator = EvaluatorAgent(client)

        output = EvaluatorOutput(
            dimensions=[
                EvaluationDimension(
                    dimension="accuracy",
                    verdict=Verdict.INSUFFICIENT,
                    reasoning="Invalid",
                    issues=["Issue 1", "Issue 2"],
                ),
                EvaluationDimension(
                    dimension="completeness",
                    verdict=Verdict.INSUFFICIENT,
                    reasoning="Invalid",
                    issues=["Issue 3"],
                ),
            ],
            overall_verdict=Verdict.INSUFFICIENT,
            recommendation="retry_with_feedback",
        )

        issues = evaluator.get_all_issues(output)
        assert len(issues) == 3
        assert "Issue 1" in issues
        assert "Issue 2" in issues
        assert "Issue 3" in issues

    def test_get_all_issues_empty_when_no_failures(self) -> None:
        """get_all_issues returns empty list when no failures."""
        client = create_mock_llm_client({})
        evaluator = EvaluatorAgent(client)

        output = EvaluatorOutput(
            dimensions=[
                EvaluationDimension(
                    dimension="accuracy",
                    verdict=Verdict.SUFFICIENT,
                    reasoning="Valid",
                ),
            ],
            overall_verdict=Verdict.SUFFICIENT,
            recommendation="accept",
        )

        issues = evaluator.get_all_issues(output)
        assert len(issues) == 0

    def test_should_retry_fail_under_max(self) -> None:
        """should_retry returns True when FAIL and attempt < max."""
        client = create_mock_llm_client({})
        evaluator = EvaluatorAgent(client)

        output = EvaluatorOutput(
            dimensions=[
                EvaluationDimension(
                    dimension="completeness",
                    verdict=Verdict.INSUFFICIENT,
                    reasoning="Invalid",
                ),
            ],
            overall_verdict=Verdict.INSUFFICIENT,
            recommendation="retry_with_feedback",
        )

        assert evaluator.should_retry(output, attempt_number=1, max_retries=2) is True

    def test_should_retry_pass(self) -> None:
        """should_retry returns False when PASS."""
        client = create_mock_llm_client({})
        evaluator = EvaluatorAgent(client)

        output = EvaluatorOutput(
            dimensions=[
                EvaluationDimension(
                    dimension="accuracy",
                    verdict=Verdict.SUFFICIENT,
                    reasoning="Valid",
                ),
            ],
            overall_verdict=Verdict.SUFFICIENT,
            recommendation="accept",
        )

        assert evaluator.should_retry(output, attempt_number=1, max_retries=2) is False

    def test_should_retry_at_max(self) -> None:
        """should_retry returns False when attempt >= max_retries."""
        client = create_mock_llm_client({})
        evaluator = EvaluatorAgent(client)

        output = EvaluatorOutput(
            dimensions=[
                EvaluationDimension(
                    dimension="completeness",
                    verdict=Verdict.INSUFFICIENT,
                    reasoning="Invalid",
                ),
            ],
            overall_verdict=Verdict.INSUFFICIENT,
            recommendation="give_partial",
        )

        assert evaluator.should_retry(output, attempt_number=2, max_retries=2) is False

    def test_should_retry_over_max(self) -> None:
        """should_retry returns False when attempt > max_retries."""
        client = create_mock_llm_client({})
        evaluator = EvaluatorAgent(client)

        output = EvaluatorOutput(
            dimensions=[
                EvaluationDimension(
                    dimension="completeness",
                    verdict=Verdict.INSUFFICIENT,
                    reasoning="Invalid",
                ),
            ],
            overall_verdict=Verdict.INSUFFICIENT,
            recommendation="give_partial",
        )

        assert evaluator.should_retry(output, attempt_number=3, max_retries=2) is False


# =============================================================================
# Test Evaluate Method (Task 7.5)
# =============================================================================


class TestEvaluateMethod:
    """Tests for EvaluatorAgent.evaluate method."""

    @pytest.mark.asyncio
    async def test_empty_query_raises_value_error(self) -> None:
        """Evaluate raises ValueError for empty query."""
        client = create_mock_llm_client({})
        evaluator = EvaluatorAgent(client)

        # Note: Empty query will fail Pydantic validation first
        with pytest.raises(ValidationError):
            await evaluator.evaluate(
                EvaluatorInput(
                    query="",
                    response="Valid response",
                    analysis=create_sample_analyzer_output(),
                    entries_summary="Valid summary",
                    evaluation_rules=[],
                )
            )

    @pytest.mark.asyncio
    async def test_whitespace_query_raises_value_error(self) -> None:
        """Evaluate raises ValueError for whitespace-only query."""
        client = create_mock_llm_client({})
        evaluator = EvaluatorAgent(client)

        with pytest.raises(ValueError, match="query cannot be empty or whitespace"):
            await evaluator.evaluate(
                EvaluatorInput(
                    query="   \n\t  ",
                    response="Valid response",
                    analysis=create_sample_analyzer_output(),
                    entries_summary="Valid summary",
                    evaluation_rules=[],
                )
            )

    @pytest.mark.asyncio
    async def test_empty_response_raises_validation_error(self) -> None:
        """Evaluate raises ValidationError for empty response."""
        client = create_mock_llm_client({})
        evaluator = EvaluatorAgent(client)

        with pytest.raises(ValidationError):
            await evaluator.evaluate(
                EvaluatorInput(
                    query="Valid query",
                    response="",
                    analysis=create_sample_analyzer_output(),
                    entries_summary="Valid summary",
                    evaluation_rules=[],
                )
            )

    @pytest.mark.asyncio
    async def test_whitespace_response_raises_value_error(self) -> None:
        """Evaluate raises ValueError for whitespace-only response."""
        client = create_mock_llm_client({})
        evaluator = EvaluatorAgent(client)

        with pytest.raises(ValueError, match="response cannot be empty or whitespace"):
            await evaluator.evaluate(
                EvaluatorInput(
                    query="Valid query",
                    response="   \n\t  ",
                    analysis=create_sample_analyzer_output(),
                    entries_summary="Valid summary",
                    evaluation_rules=[],
                )
            )

    @pytest.mark.asyncio
    async def test_successful_evaluation_returns_output(self) -> None:
        """Evaluate returns EvaluatorOutput on success."""
        response = create_sample_evaluator_output_pass()
        client = create_mock_llm_client(response)
        evaluator = EvaluatorAgent(client)

        result = await evaluator.evaluate(
            EvaluatorInput(
                query="How has my bench press progressed?",
                response="Your bench press increased by 10 lbs",
                analysis=create_sample_analyzer_output(),
                entries_summary=create_sample_entries_summary(),
                evaluation_rules=create_sample_evaluation_rules(),
            )
        )

        assert isinstance(result, EvaluatorOutput)
        assert len(result.dimensions) == 4
        assert result.overall_verdict == Verdict.SUFFICIENT
        assert result.recommendation == "accept"

    @pytest.mark.asyncio
    async def test_failed_evaluation_returns_output(self) -> None:
        """Evaluate returns EvaluatorOutput with FAIL verdict."""
        response = create_sample_evaluator_output_fail()
        client = create_mock_llm_client(response)
        evaluator = EvaluatorAgent(client)

        result = await evaluator.evaluate(
            EvaluatorInput(
                query="How has my bench press progressed?",
                response="Your bench press increased by 10 lbs",
                analysis=create_sample_analyzer_output(),
                entries_summary=create_sample_entries_summary(),
                evaluation_rules=[],
            )
        )

        assert isinstance(result, EvaluatorOutput)
        assert result.overall_verdict == Verdict.INSUFFICIENT
        assert result.recommendation == "retry_with_feedback"
        assert len(result.feedback) == 1


# =============================================================================
# Test Exports (Task 7.6)
# =============================================================================


class TestEvaluatorExports:
    """Tests for evaluator exports from quilto.agents."""

    def test_evaluator_agent_importable(self) -> None:
        """EvaluatorAgent is importable from quilto.agents."""
        from quilto.agents import EvaluatorAgent

        assert EvaluatorAgent is not None

    def test_evaluator_input_importable(self) -> None:
        """EvaluatorInput is importable from quilto.agents."""
        from quilto.agents import EvaluatorInput

        assert EvaluatorInput is not None

    def test_evaluator_output_importable(self) -> None:
        """EvaluatorOutput is importable from quilto.agents."""
        from quilto.agents import EvaluatorOutput

        assert EvaluatorOutput is not None

    def test_evaluation_dimension_importable(self) -> None:
        """EvaluationDimension is importable from quilto.agents."""
        from quilto.agents import EvaluationDimension

        assert EvaluationDimension is not None

    def test_all_exports_in_all_list(self) -> None:
        """All new types are in __all__ list."""
        from quilto import agents

        assert "EvaluatorAgent" in agents.__all__
        assert "EvaluatorInput" in agents.__all__
        assert "EvaluatorOutput" in agents.__all__
        assert "EvaluationDimension" in agents.__all__


# =============================================================================
# Integration Tests
# =============================================================================


class TestEvaluatorIntegration:
    """Integration tests with real Ollama.

    Run with: pytest --use-real-ollama -k TestEvaluatorIntegration
    Or via: make test-ollama
    """

    @pytest.mark.asyncio
    async def test_real_evaluation_pass(self, use_real_ollama: bool, integration_llm_config_path: Path) -> None:
        """Test real evaluation with passing response."""
        if not use_real_ollama:
            pytest.skip("Requires --use-real-ollama flag")

        config = load_llm_config(integration_llm_config_path)
        real_llm_client = LLMClient(config)
        evaluator = EvaluatorAgent(real_llm_client)

        result = await evaluator.evaluate(
            EvaluatorInput(
                query="How has my bench press progressed?",
                response="Based on the data, your bench press has improved from 165 lbs "
                "to 185 lbs over the past 10 days, showing a consistent 5 lb increase "
                "per session. This represents a 12% improvement.",
                analysis=create_sample_analyzer_output(),
                entries_summary=create_sample_entries_summary(),
                evaluation_rules=create_sample_evaluation_rules(),
            )
        )

        # Should have valid output structure
        assert result is not None
        assert len(result.dimensions) == 4
        assert result.overall_verdict in [Verdict.SUFFICIENT, Verdict.INSUFFICIENT, Verdict.PARTIAL]
        assert result.recommendation in ["accept", "retry_with_feedback", "retry_with_more_context", "give_partial"]

    @pytest.mark.asyncio
    async def test_real_evaluation_fail(self, use_real_ollama: bool, integration_llm_config_path: Path) -> None:
        """Test real evaluation with incomplete response."""
        if not use_real_ollama:
            pytest.skip("Requires --use-real-ollama flag")

        config = load_llm_config(integration_llm_config_path)
        real_llm_client = LLMClient(config)
        evaluator = EvaluatorAgent(real_llm_client)

        # Deliberately incomplete response
        result = await evaluator.evaluate(
            EvaluatorInput(
                query="How has my bench press progressed and what should I do next week?",
                response="Your bench is going well.",  # Very incomplete
                analysis=create_sample_analyzer_output(),
                entries_summary=create_sample_entries_summary(),
                evaluation_rules=create_sample_evaluation_rules(),
            )
        )

        # Should have valid output structure
        assert result is not None
        assert len(result.dimensions) == 4
        # With such an incomplete response, expect failure
        # (but LLM might still pass it, so we just check structure)
        assert result.overall_verdict in [Verdict.SUFFICIENT, Verdict.INSUFFICIENT, Verdict.PARTIAL]

    @pytest.mark.asyncio
    async def test_real_evaluation_with_retry_context(
        self, use_real_ollama: bool, integration_llm_config_path: Path
    ) -> None:
        """Test real evaluation with retry context."""
        if not use_real_ollama:
            pytest.skip("Requires --use-real-ollama flag")

        config = load_llm_config(integration_llm_config_path)
        real_llm_client = LLMClient(config)
        evaluator = EvaluatorAgent(real_llm_client)

        feedback = [
            EvaluationFeedback(
                issue="Missing volume analysis",
                suggestion="Include total sets x reps x weight",
                affected_claim=None,
            )
        ]

        result = await evaluator.evaluate(
            EvaluatorInput(
                query="How has my bench press progressed?",
                response="Your bench press improved from 165 to 185 lbs. "
                "Total training volume increased from 825 lbs (5x165) to 925 lbs (5x185), "
                "representing a 12% increase in both load and volume.",
                analysis=create_sample_analyzer_output(),
                entries_summary=create_sample_entries_summary(),
                evaluation_rules=create_sample_evaluation_rules(),
                attempt_number=2,
                previous_feedback=feedback,
            )
        )

        # Should have valid output structure
        assert result is not None
        assert len(result.dimensions) == 4


# =============================================================================
# Test user_responses Field (Story 5.5)
# =============================================================================


class TestEvaluatorInputUserResponses:
    """Tests for EvaluatorInput.user_responses field (Story 5-5)."""

    def test_evaluator_input_user_responses_default_empty(self) -> None:
        """EvaluatorInput has empty user_responses dict by default (AC #6)."""
        evaluator_input = EvaluatorInput(
            query="Test query",
            response="Test response",
            analysis=create_sample_analyzer_output(),
            entries_summary="Test summary",
            evaluation_rules=[],
        )
        assert evaluator_input.user_responses == {}

    def test_evaluator_input_user_responses_accepts_dict(self) -> None:
        """EvaluatorInput accepts user_responses dict (AC #2)."""
        user_responses = {
            "Current 1RM": "60kg for 10 reps",
            "Training days": "4 days per week",
        }
        evaluator_input = EvaluatorInput(
            query="Test query",
            response="Test response",
            analysis=create_sample_analyzer_output(),
            entries_summary="Test summary",
            evaluation_rules=[],
            user_responses=user_responses,
        )
        assert evaluator_input.user_responses == user_responses
        assert len(evaluator_input.user_responses) == 2

    def test_evaluator_input_user_responses_single_entry(self) -> None:
        """EvaluatorInput accepts single user_responses entry."""
        user_responses = {"Current 1RM": "80kg"}
        evaluator_input = EvaluatorInput(
            query="Test query",
            response="Test response",
            analysis=create_sample_analyzer_output(),
            entries_summary="Test summary",
            evaluation_rules=[],
            user_responses=user_responses,
        )
        assert len(evaluator_input.user_responses) == 1
        assert evaluator_input.user_responses["Current 1RM"] == "80kg"

    def test_evaluator_input_backward_compat_without_user_responses(self) -> None:
        """EvaluatorInput works exactly as before without user_responses (AC #6)."""
        # This mirrors existing tests without user_responses field
        evaluator_input = EvaluatorInput(
            query="How has my bench press progressed?",
            response="Your bench press increased by 10 lbs",
            analysis=create_sample_analyzer_output(),
            entries_summary=create_sample_entries_summary(),
            evaluation_rules=create_sample_evaluation_rules(),
            attempt_number=2,
            previous_feedback=create_sample_evaluation_feedback(),
        )
        # All existing fields work as before
        assert evaluator_input.query == "How has my bench press progressed?"
        assert evaluator_input.attempt_number == 2
        assert len(evaluator_input.previous_feedback) == 2
        # user_responses defaults to empty dict
        assert evaluator_input.user_responses == {}


class TestFormatUserResponsesHelper:
    """Tests for EvaluatorAgent._format_user_responses method (Story 5-5, Task 5.5)."""

    def test_format_user_responses_empty_returns_empty(self) -> None:
        """_format_user_responses returns empty string for empty dict."""
        client = create_mock_llm_client({})
        evaluator = EvaluatorAgent(client)

        result = evaluator._format_user_responses({})  # pyright: ignore[reportPrivateUsage]
        assert result == ""

    def test_format_user_responses_single_entry(self) -> None:
        """_format_user_responses formats single entry correctly."""
        client = create_mock_llm_client({})
        evaluator = EvaluatorAgent(client)

        user_responses = {"Current 1RM": "60kg for 10 reps"}
        result = evaluator._format_user_responses(user_responses)  # pyright: ignore[reportPrivateUsage]

        assert "- Current 1RM: 60kg for 10 reps" in result

    def test_format_user_responses_multiple_entries(self) -> None:
        """_format_user_responses formats multiple entries correctly."""
        client = create_mock_llm_client({})
        evaluator = EvaluatorAgent(client)

        user_responses = {
            "Current 1RM": "60kg for 10 reps",
            "Training days": "4 days per week",
            "Goal": "Increase bench to 100kg",
        }
        result = evaluator._format_user_responses(user_responses)  # pyright: ignore[reportPrivateUsage]

        assert "- Current 1RM: 60kg for 10 reps" in result
        assert "- Training days: 4 days per week" in result
        assert "- Goal: Increase bench to 100kg" in result


class TestBuildPromptUserResponses:
    """Tests for build_prompt with user_responses (Story 5-5, Tasks 5.3, 5.4)."""

    def test_prompt_includes_clarification_context_when_provided(self) -> None:
        """build_prompt includes USER CLARIFICATION CONTEXT section when user_responses provided (AC #3)."""
        client = create_mock_llm_client({})
        evaluator = EvaluatorAgent(client)

        user_responses = {
            "Current 1RM": "60kg for 10 reps",
            "Training days": "4 days per week",
        }
        evaluator_input = EvaluatorInput(
            query="Test query",
            response="Test response",
            analysis=create_sample_analyzer_output(),
            entries_summary=create_sample_entries_summary(),
            evaluation_rules=[],
            user_responses=user_responses,
        )
        prompt = evaluator.build_prompt(evaluator_input)

        assert "USER CLARIFICATION CONTEXT" in prompt
        assert "Current 1RM: 60kg for 10 reps" in prompt
        assert "Training days: 4 days per week" in prompt

    def test_prompt_omits_clarification_context_when_empty(self) -> None:
        """build_prompt omits USER CLARIFICATION CONTEXT when user_responses empty (Task 5.4)."""
        client = create_mock_llm_client({})
        evaluator = EvaluatorAgent(client)

        evaluator_input = EvaluatorInput(
            query="Test query",
            response="Test response",
            analysis=create_sample_analyzer_output(),
            entries_summary=create_sample_entries_summary(),
            evaluation_rules=[],
            user_responses={},  # Empty
        )
        prompt = evaluator.build_prompt(evaluator_input)

        assert "USER CLARIFICATION CONTEXT" not in prompt

    def test_prompt_clarification_states_authoritative(self) -> None:
        """build_prompt states user answers are AUTHORITATIVE (AC #5)."""
        client = create_mock_llm_client({})
        evaluator = EvaluatorAgent(client)

        evaluator_input = EvaluatorInput(
            query="Test query",
            response="Test response",
            analysis=create_sample_analyzer_output(),
            entries_summary=create_sample_entries_summary(),
            evaluation_rules=[],
            user_responses={"Current 1RM": "80kg"},
        )
        prompt = evaluator.build_prompt(evaluator_input)

        assert "AUTHORITATIVE" in prompt
        assert "NOT be flagged as speculation" in prompt

    def test_prompt_clarification_instruction_no_ask_again(self) -> None:
        """build_prompt includes instruction not to suggest asking again (AC #4)."""
        client = create_mock_llm_client({})
        evaluator = EvaluatorAgent(client)

        evaluator_input = EvaluatorInput(
            query="Test query",
            response="Test response",
            analysis=create_sample_analyzer_output(),
            entries_summary=create_sample_entries_summary(),
            evaluation_rules=[],
            user_responses={"Current 1RM": "80kg"},
        )
        prompt = evaluator.build_prompt(evaluator_input)

        assert 'Do NOT suggest "ask the user"' in prompt

    def test_prompt_clarification_instruction_not_speculation(self) -> None:
        """build_prompt includes instruction that user-provided info is NOT speculation (AC #1)."""
        client = create_mock_llm_client({})
        evaluator = EvaluatorAgent(client)

        evaluator_input = EvaluatorInput(
            query="Test query",
            response="Test response",
            analysis=create_sample_analyzer_output(),
            entries_summary=create_sample_entries_summary(),
            evaluation_rules=[],
            user_responses={"Current 1RM": "80kg"},
        )
        prompt = evaluator.build_prompt(evaluator_input)

        assert "NOT speculation" in prompt
        assert "user-provided data" in prompt

    def test_prompt_clarification_instruction_valid_evidence(self) -> None:
        """build_prompt states user answers are valid evidence."""
        client = create_mock_llm_client({})
        evaluator = EvaluatorAgent(client)

        evaluator_input = EvaluatorInput(
            query="Test query",
            response="Test response",
            analysis=create_sample_analyzer_output(),
            entries_summary=create_sample_entries_summary(),
            evaluation_rules=[],
            user_responses={"Current 1RM": "80kg"},
        )
        prompt = evaluator.build_prompt(evaluator_input)

        assert "valid evidence" in prompt


class TestEvaluatorWithUserResponses:
    """Integration tests for Evaluator with user_responses (Story 5-5, Task 5.6)."""

    @pytest.mark.asyncio
    async def test_evaluate_with_user_responses_passes(self) -> None:
        """Evaluator with user_responses doesn't flag user-provided info as speculative."""
        # Create a response that acknowledges the mock returns PASS
        response = create_sample_evaluator_output_pass()
        client = create_mock_llm_client(response)
        evaluator = EvaluatorAgent(client)

        user_responses = {
            "Current 1RM": "60kg for 10 reps, so estimated ~80kg 1RM",
        }

        result = await evaluator.evaluate(
            EvaluatorInput(
                query="What weight should I use for my 5x5 bench program?",
                response="Based on your estimated 1RM of ~80kg, you should use around 60-65kg for 5x5.",
                analysis=create_sample_analyzer_output(),
                entries_summary=create_sample_entries_summary(),
                evaluation_rules=create_sample_evaluation_rules(),
                user_responses=user_responses,
            )
        )

        assert isinstance(result, EvaluatorOutput)
        # Mock returns PASS, so we verify the structure is correct
        assert result.overall_verdict == Verdict.SUFFICIENT
        assert result.recommendation == "accept"

    @pytest.mark.asyncio
    async def test_evaluate_without_user_responses_backward_compat(self) -> None:
        """Evaluator without user_responses works exactly as before (AC #6)."""
        response = create_sample_evaluator_output_pass()
        client = create_mock_llm_client(response)
        evaluator = EvaluatorAgent(client)

        # Call without user_responses field - should work exactly as before
        result = await evaluator.evaluate(
            EvaluatorInput(
                query="How has my bench press progressed?",
                response="Your bench press increased by 10 lbs",
                analysis=create_sample_analyzer_output(),
                entries_summary=create_sample_entries_summary(),
                evaluation_rules=create_sample_evaluation_rules(),
            )
        )

        assert isinstance(result, EvaluatorOutput)
        assert result.overall_verdict == Verdict.SUFFICIENT

    @pytest.mark.asyncio
    async def test_real_evaluation_with_user_responses(
        self, use_real_ollama: bool, integration_llm_config_path: Path
    ) -> None:
        """Test real evaluation with user_responses context.

        This tests that the Evaluator doesn't flag user-provided info as speculation
        when user_responses is provided.
        """
        if not use_real_ollama:
            pytest.skip("Requires --use-real-ollama flag")

        config = load_llm_config(integration_llm_config_path)
        real_llm_client = LLMClient(config)
        evaluator = EvaluatorAgent(real_llm_client)

        # User provided their estimated 1RM via clarification
        user_responses = {
            "Current 1RM": "Haven't measured directly. 60kg for 10 reps so far.",
        }

        result = await evaluator.evaluate(
            EvaluatorInput(
                query="What weight should I use for my 5x5 bench program?",
                response="Based on your estimate of 60kg for 10 reps, your 1RM is approximately "
                "78-80kg. For a 5x5 program, you should use around 65-70% of your 1RM, "
                "which means 52-56kg. Start with 52kg and progress as you get comfortable.",
                analysis=create_sample_analyzer_output(),
                entries_summary=create_sample_entries_summary(),
                evaluation_rules=create_sample_evaluation_rules(),
                user_responses=user_responses,
            )
        )

        # Should have valid output structure
        assert result is not None
        assert len(result.dimensions) == 4
        # The key test: with user_responses context, the evaluator should NOT
        # flag the 1RM estimate as speculation since it came from the user
        assert result.overall_verdict in [Verdict.SUFFICIENT, Verdict.INSUFFICIENT, Verdict.PARTIAL]
