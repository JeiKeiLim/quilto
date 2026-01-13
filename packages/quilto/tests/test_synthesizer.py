"""Unit tests for SynthesizerAgent.

Tests cover model validation, prompt building, synthesize method,
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
    Finding,
    Gap,
    GapType,
    QueryType,
    SufficiencyEvaluation,
    SynthesizerAgent,
    SynthesizerInput,
    SynthesizerOutput,
    Verdict,
)
from quilto.llm.client import LLMClient
from quilto.llm.config import AgentConfig, LLMConfig, ProviderConfig, TierModels


def create_test_config() -> LLMConfig:
    """Create a test LLMConfig for SynthesizerAgent tests.

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
            "synthesizer": AgentConfig(tier="high"),
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


def create_sample_analyzer_output_sufficient() -> AnalyzerOutput:
    """Create a sample AnalyzerOutput with SUFFICIENT verdict.

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


def create_sample_analyzer_output_partial() -> AnalyzerOutput:
    """Create a sample AnalyzerOutput with PARTIAL verdict.

    Returns:
        AnalyzerOutput for tests.
    """
    return AnalyzerOutput(
        query_intent="User wants progress analysis",
        findings=[
            Finding(
                claim="Some improvement observed",
                evidence=["entry1"],
                confidence="medium",
            )
        ],
        patterns_identified=["slight improvement"],
        sufficiency_evaluation=SufficiencyEvaluation(
            critical_gaps=[],
            nice_to_have_gaps=[
                Gap(
                    description="Historical baseline would help",
                    gap_type=GapType.TEMPORAL,
                    severity="nice_to_have",
                )
            ],
            evidence_check_passed=True,
            speculation_risk="low",
        ),
        verdict_reasoning="Can answer with noted limitations",
        verdict=Verdict.PARTIAL,
    )


def create_sample_analyzer_output_insufficient() -> AnalyzerOutput:
    """Create a sample AnalyzerOutput with INSUFFICIENT verdict.

    Returns:
        AnalyzerOutput for tests.
    """
    return AnalyzerOutput(
        query_intent="User wants workout data",
        findings=[],
        patterns_identified=[],
        sufficiency_evaluation=SufficiencyEvaluation(
            critical_gaps=[
                Gap(
                    description="No data for time period",
                    gap_type=GapType.TEMPORAL,
                    severity="critical",
                    searched=True,
                    found=False,
                )
            ],
            nice_to_have_gaps=[],
            evidence_check_passed=False,
            speculation_risk="high",
        ),
        verdict_reasoning="No data available",
        verdict=Verdict.INSUFFICIENT,
    )


def create_sample_vocabulary() -> dict[str, str]:
    """Create sample vocabulary for testing.

    Returns:
        Vocabulary dict for tests.
    """
    return {
        "bench": "bench press",
        "pr": "personal record",
        "1rm": "one rep max",
        "squat": "barbell squat",
    }


def create_sample_gaps() -> list[Gap]:
    """Create sample gaps for partial answer testing.

    Returns:
        List of Gap objects.
    """
    return [
        Gap(
            description="Historical comparison data from previous month",
            gap_type=GapType.TEMPORAL,
            severity="nice_to_have",
        ),
        Gap(
            description="Recovery information",
            gap_type=GapType.CONTEXTUAL,
            severity="nice_to_have",
            outside_current_expertise=True,
            suspected_domain="sleep",
        ),
    ]


# =============================================================================
# Test SynthesizerInput Model (Task 1.1)
# =============================================================================


class TestSynthesizerInputModel:
    """Tests for SynthesizerInput Pydantic model validation."""

    def test_synthesizer_input_valid(self) -> None:
        """SynthesizerInput accepts valid data."""
        synthesizer_input = SynthesizerInput(
            query="How has my bench press progressed?",
            query_type=QueryType.INSIGHT,
            analysis=create_sample_analyzer_output_sufficient(),
            vocabulary=create_sample_vocabulary(),
        )
        assert synthesizer_input.query == "How has my bench press progressed?"
        assert synthesizer_input.query_type == QueryType.INSIGHT
        assert synthesizer_input.is_partial is False
        assert synthesizer_input.response_style == "concise"

    def test_synthesizer_input_empty_query_fails(self) -> None:
        """SynthesizerInput with empty query fails min_length=1."""
        with pytest.raises(ValidationError):
            SynthesizerInput(
                query="",
                query_type=QueryType.INSIGHT,
                analysis=create_sample_analyzer_output_sufficient(),
                vocabulary={},
            )

    def test_synthesizer_input_response_style_concise(self) -> None:
        """SynthesizerInput accepts 'concise' response_style."""
        synthesizer_input = SynthesizerInput(
            query="Test",
            query_type=QueryType.SIMPLE,
            analysis=create_sample_analyzer_output_sufficient(),
            vocabulary={},
            response_style="concise",
        )
        assert synthesizer_input.response_style == "concise"

    def test_synthesizer_input_response_style_detailed(self) -> None:
        """SynthesizerInput accepts 'detailed' response_style."""
        synthesizer_input = SynthesizerInput(
            query="Test",
            query_type=QueryType.SIMPLE,
            analysis=create_sample_analyzer_output_sufficient(),
            vocabulary={},
            response_style="detailed",
        )
        assert synthesizer_input.response_style == "detailed"

    def test_synthesizer_input_invalid_response_style_fails(self) -> None:
        """SynthesizerInput with invalid response_style fails."""
        with pytest.raises(ValidationError):
            SynthesizerInput(
                query="Test",
                query_type=QueryType.SIMPLE,
                analysis=create_sample_analyzer_output_sufficient(),
                vocabulary={},
                response_style="verbose",  # type: ignore[arg-type]
            )

    def test_synthesizer_input_is_partial_default(self) -> None:
        """SynthesizerInput has is_partial=False by default."""
        synthesizer_input = SynthesizerInput(
            query="Test",
            query_type=QueryType.SIMPLE,
            analysis=create_sample_analyzer_output_sufficient(),
            vocabulary={},
        )
        assert synthesizer_input.is_partial is False

    def test_synthesizer_input_is_partial_true(self) -> None:
        """SynthesizerInput accepts is_partial=True."""
        synthesizer_input = SynthesizerInput(
            query="Test",
            query_type=QueryType.SIMPLE,
            analysis=create_sample_analyzer_output_insufficient(),
            vocabulary={},
            is_partial=True,
        )
        assert synthesizer_input.is_partial is True

    def test_synthesizer_input_unanswered_gaps_default(self) -> None:
        """SynthesizerInput has empty unanswered_gaps by default."""
        synthesizer_input = SynthesizerInput(
            query="Test",
            query_type=QueryType.SIMPLE,
            analysis=create_sample_analyzer_output_sufficient(),
            vocabulary={},
        )
        assert synthesizer_input.unanswered_gaps == []

    def test_synthesizer_input_unanswered_gaps_provided(self) -> None:
        """SynthesizerInput accepts unanswered_gaps list."""
        gaps = create_sample_gaps()
        synthesizer_input = SynthesizerInput(
            query="Test",
            query_type=QueryType.SIMPLE,
            analysis=create_sample_analyzer_output_insufficient(),
            vocabulary={},
            is_partial=True,
            unanswered_gaps=gaps,
        )
        assert len(synthesizer_input.unanswered_gaps) == 2

    def test_synthesizer_input_all_query_types(self) -> None:
        """SynthesizerInput accepts all QueryType values."""
        for query_type in QueryType:
            synthesizer_input = SynthesizerInput(
                query="Test query",
                query_type=query_type,
                analysis=create_sample_analyzer_output_sufficient(),
                vocabulary={},
            )
            assert synthesizer_input.query_type == query_type

    def test_synthesizer_input_empty_vocabulary(self) -> None:
        """SynthesizerInput accepts empty vocabulary."""
        synthesizer_input = SynthesizerInput(
            query="Test",
            query_type=QueryType.SIMPLE,
            analysis=create_sample_analyzer_output_sufficient(),
            vocabulary={},
        )
        assert synthesizer_input.vocabulary == {}


# =============================================================================
# Test SynthesizerOutput Model (Task 1.2)
# =============================================================================


class TestSynthesizerOutputModel:
    """Tests for SynthesizerOutput Pydantic model validation."""

    def test_synthesizer_output_valid(self) -> None:
        """SynthesizerOutput accepts valid data."""
        output = SynthesizerOutput(
            response="Your bench press has improved by 10 lbs over the past week.",
            key_points=["10 lb increase", "Consistent progression"],
            evidence_cited=["2026-01-03: bench 175x5", "2026-01-10: bench 185x5"],
            confidence="high",
        )
        assert "improved by 10 lbs" in output.response
        assert len(output.key_points) == 2
        assert len(output.evidence_cited) == 2
        assert output.confidence == "high"

    def test_synthesizer_output_empty_response_fails(self) -> None:
        """SynthesizerOutput with empty response fails min_length=1."""
        with pytest.raises(ValidationError):
            SynthesizerOutput(
                response="",
                key_points=[],
                evidence_cited=[],
                confidence="high",
            )

    def test_synthesizer_output_confidence_high(self) -> None:
        """SynthesizerOutput accepts 'high' confidence."""
        output = SynthesizerOutput(
            response="Test response",
            key_points=[],
            evidence_cited=[],
            confidence="high",
        )
        assert output.confidence == "high"

    def test_synthesizer_output_confidence_medium(self) -> None:
        """SynthesizerOutput accepts 'medium' confidence."""
        output = SynthesizerOutput(
            response="Test response",
            key_points=[],
            evidence_cited=[],
            confidence="medium",
        )
        assert output.confidence == "medium"

    def test_synthesizer_output_confidence_low(self) -> None:
        """SynthesizerOutput accepts 'low' confidence."""
        output = SynthesizerOutput(
            response="Test response",
            key_points=[],
            evidence_cited=[],
            confidence="low",
        )
        assert output.confidence == "low"

    def test_synthesizer_output_invalid_confidence_fails(self) -> None:
        """SynthesizerOutput with invalid confidence value fails."""
        with pytest.raises(ValidationError):
            SynthesizerOutput(
                response="Test response",
                key_points=[],
                evidence_cited=[],
                confidence="very_high",  # type: ignore[arg-type]
            )

    def test_synthesizer_output_gaps_disclosed_default(self) -> None:
        """SynthesizerOutput has empty gaps_disclosed by default."""
        output = SynthesizerOutput(
            response="Test response",
            key_points=[],
            evidence_cited=[],
            confidence="high",
        )
        assert output.gaps_disclosed == []

    def test_synthesizer_output_gaps_disclosed_provided(self) -> None:
        """SynthesizerOutput accepts gaps_disclosed list."""
        output = SynthesizerOutput(
            response="Here's what I can tell you...",
            key_points=["Partial answer"],
            evidence_cited=[],
            gaps_disclosed=["Historical data from last month", "Sleep recovery information"],
            confidence="low",
        )
        assert len(output.gaps_disclosed) == 2

    def test_synthesizer_output_empty_key_points_allowed(self) -> None:
        """SynthesizerOutput accepts empty key_points list."""
        output = SynthesizerOutput(
            response="Simple answer",
            key_points=[],
            evidence_cited=[],
            confidence="high",
        )
        assert output.key_points == []

    def test_synthesizer_output_empty_evidence_cited_allowed(self) -> None:
        """SynthesizerOutput accepts empty evidence_cited list."""
        output = SynthesizerOutput(
            response="No specific entries to cite",
            key_points=["General observation"],
            evidence_cited=[],
            confidence="low",
        )
        assert output.evidence_cited == []


# =============================================================================
# Test SynthesizerAgent Instantiation (Task 2)
# =============================================================================


class TestSynthesizerAgentInstantiation:
    """Tests for SynthesizerAgent class instantiation."""

    def test_synthesizer_agent_creates_with_llm_client(self) -> None:
        """SynthesizerAgent creates successfully with LLMClient."""
        client = create_mock_llm_client({})
        synthesizer = SynthesizerAgent(client)
        assert synthesizer.llm_client is client

    def test_synthesizer_agent_name_constant(self) -> None:
        """SynthesizerAgent has correct AGENT_NAME constant."""
        client = create_mock_llm_client({})
        synthesizer = SynthesizerAgent(client)
        assert synthesizer.AGENT_NAME == "synthesizer"
        assert SynthesizerAgent.AGENT_NAME == "synthesizer"


# =============================================================================
# Test _format_analysis Helper (Task 3.1, 6.3.1)
# =============================================================================


class TestFormatAnalysisHelper:
    """Tests for SynthesizerAgent._format_analysis method."""

    def test_format_analysis_with_findings(self) -> None:
        """_format_analysis includes findings with evidence."""
        client = create_mock_llm_client({})
        synthesizer = SynthesizerAgent(client)

        analysis = create_sample_analyzer_output_sufficient()
        result = synthesizer._format_analysis(analysis)  # pyright: ignore[reportPrivateUsage]

        assert "FINDINGS:" in result
        assert "Progressive overload observed" in result
        assert "high" in result
        assert "2026-01-10" in result

    def test_format_analysis_with_empty_findings(self) -> None:
        """_format_analysis handles empty findings."""
        client = create_mock_llm_client({})
        synthesizer = SynthesizerAgent(client)

        analysis = create_sample_analyzer_output_insufficient()
        result = synthesizer._format_analysis(analysis)  # pyright: ignore[reportPrivateUsage]

        assert "FINDINGS:" in result
        assert "(No findings)" in result

    def test_format_analysis_includes_patterns(self) -> None:
        """_format_analysis includes patterns_identified."""
        client = create_mock_llm_client({})
        synthesizer = SynthesizerAgent(client)

        analysis = create_sample_analyzer_output_sufficient()
        result = synthesizer._format_analysis(analysis)  # pyright: ignore[reportPrivateUsage]

        assert "PATTERNS IDENTIFIED:" in result
        assert "progressive overload" in result

    def test_format_analysis_with_empty_patterns(self) -> None:
        """_format_analysis handles empty patterns."""
        client = create_mock_llm_client({})
        synthesizer = SynthesizerAgent(client)

        analysis = create_sample_analyzer_output_insufficient()
        result = synthesizer._format_analysis(analysis)  # pyright: ignore[reportPrivateUsage]

        assert "PATTERNS IDENTIFIED:" in result
        assert "(No patterns identified)" in result

    def test_format_analysis_includes_verdict(self) -> None:
        """_format_analysis includes verdict and reasoning."""
        client = create_mock_llm_client({})
        synthesizer = SynthesizerAgent(client)

        analysis = create_sample_analyzer_output_sufficient()
        result = synthesizer._format_analysis(analysis)  # pyright: ignore[reportPrivateUsage]

        assert "ANALYSIS VERDICT: sufficient" in result
        assert "VERDICT REASONING:" in result


# =============================================================================
# Test _format_vocabulary Helper (Task 3.2, 6.3.2)
# =============================================================================


class TestFormatVocabularyHelper:
    """Tests for SynthesizerAgent._format_vocabulary method."""

    def test_format_vocabulary_with_terms(self) -> None:
        """_format_vocabulary formats vocabulary terms."""
        client = create_mock_llm_client({})
        synthesizer = SynthesizerAgent(client)

        vocabulary = create_sample_vocabulary()
        result = synthesizer._format_vocabulary(vocabulary)  # pyright: ignore[reportPrivateUsage]

        assert "bench: bench press" in result
        assert "pr: personal record" in result
        assert "1rm: one rep max" in result

    def test_format_vocabulary_empty(self) -> None:
        """_format_vocabulary handles empty vocabulary."""
        client = create_mock_llm_client({})
        synthesizer = SynthesizerAgent(client)

        result = synthesizer._format_vocabulary({})  # pyright: ignore[reportPrivateUsage]

        assert "(No domain vocabulary provided)" in result


# =============================================================================
# Test _format_gaps Helper (Task 3.3, 6.3.3)
# =============================================================================


class TestFormatGapsHelper:
    """Tests for SynthesizerAgent._format_gaps method."""

    def test_format_gaps_with_gaps(self) -> None:
        """_format_gaps formats gap list."""
        client = create_mock_llm_client({})
        synthesizer = SynthesizerAgent(client)

        gaps = create_sample_gaps()
        result = synthesizer._format_gaps(gaps)  # pyright: ignore[reportPrivateUsage]

        assert "Historical comparison data" in result
        assert "temporal" in result
        assert "Recovery information" in result
        assert "sleep" in result

    def test_format_gaps_empty(self) -> None:
        """_format_gaps handles empty gaps list."""
        client = create_mock_llm_client({})
        synthesizer = SynthesizerAgent(client)

        result = synthesizer._format_gaps([])  # pyright: ignore[reportPrivateUsage]

        assert "(No gaps)" in result

    def test_format_gaps_with_suspected_domain(self) -> None:
        """_format_gaps includes suspected_domain when present."""
        client = create_mock_llm_client({})
        synthesizer = SynthesizerAgent(client)

        gaps = [
            Gap(
                description="Need sleep data",
                gap_type=GapType.CONTEXTUAL,
                severity="critical",
                outside_current_expertise=True,
                suspected_domain="sleep",
            )
        ]
        result = synthesizer._format_gaps(gaps)  # pyright: ignore[reportPrivateUsage]

        assert "[may need: sleep]" in result


# =============================================================================
# Test _get_confidence_from_verdict Helper
# =============================================================================


class TestConfidenceFromVerdictHelper:
    """Tests for SynthesizerAgent._get_confidence_from_verdict method."""

    def test_sufficient_maps_to_high(self) -> None:
        """SUFFICIENT verdict maps to 'high' confidence."""
        client = create_mock_llm_client({})
        synthesizer = SynthesizerAgent(client)

        result = synthesizer._get_confidence_from_verdict(Verdict.SUFFICIENT)  # pyright: ignore[reportPrivateUsage]
        assert result == "high"

    def test_partial_maps_to_medium(self) -> None:
        """PARTIAL verdict maps to 'medium' confidence."""
        client = create_mock_llm_client({})
        synthesizer = SynthesizerAgent(client)

        result = synthesizer._get_confidence_from_verdict(Verdict.PARTIAL)  # pyright: ignore[reportPrivateUsage]
        assert result == "medium"

    def test_insufficient_maps_to_low(self) -> None:
        """INSUFFICIENT verdict maps to 'low' confidence."""
        client = create_mock_llm_client({})
        synthesizer = SynthesizerAgent(client)

        result = synthesizer._get_confidence_from_verdict(Verdict.INSUFFICIENT)  # pyright: ignore[reportPrivateUsage]
        assert result == "low"


# =============================================================================
# Test Prompt Building (Task 3, 6.3.4-6.3.6)
# =============================================================================


class TestSynthesizerPromptBuilding:
    """Tests for SynthesizerAgent.build_prompt method."""

    def test_prompt_includes_query(self) -> None:
        """Prompt includes the query."""
        client = create_mock_llm_client({})
        synthesizer = SynthesizerAgent(client)

        synthesizer_input = SynthesizerInput(
            query="How has my bench press progressed?",
            query_type=QueryType.INSIGHT,
            analysis=create_sample_analyzer_output_sufficient(),
            vocabulary={},
        )
        prompt = synthesizer.build_prompt(synthesizer_input)

        assert "How has my bench press progressed?" in prompt

    def test_prompt_includes_query_type(self) -> None:
        """Prompt includes query_type."""
        client = create_mock_llm_client({})
        synthesizer = SynthesizerAgent(client)

        synthesizer_input = SynthesizerInput(
            query="Test query",
            query_type=QueryType.INSIGHT,
            analysis=create_sample_analyzer_output_sufficient(),
            vocabulary={},
        )
        prompt = synthesizer.build_prompt(synthesizer_input)

        assert "insight" in prompt.lower()

    def test_prompt_includes_vocabulary(self) -> None:
        """Prompt includes vocabulary terms."""
        client = create_mock_llm_client({})
        synthesizer = SynthesizerAgent(client)

        synthesizer_input = SynthesizerInput(
            query="Test",
            query_type=QueryType.SIMPLE,
            analysis=create_sample_analyzer_output_sufficient(),
            vocabulary=create_sample_vocabulary(),
        )
        prompt = synthesizer.build_prompt(synthesizer_input)

        assert "bench: bench press" in prompt
        assert "pr: personal record" in prompt

    def test_prompt_includes_analysis_findings(self) -> None:
        """Prompt includes analysis findings."""
        client = create_mock_llm_client({})
        synthesizer = SynthesizerAgent(client)

        synthesizer_input = SynthesizerInput(
            query="Test",
            query_type=QueryType.SIMPLE,
            analysis=create_sample_analyzer_output_sufficient(),
            vocabulary={},
        )
        prompt = synthesizer.build_prompt(synthesizer_input)

        assert "Progressive overload observed" in prompt
        assert "2026-01-10" in prompt

    def test_prompt_concise_style_guidance(self) -> None:
        """Prompt includes concise style guidance."""
        client = create_mock_llm_client({})
        synthesizer = SynthesizerAgent(client)

        synthesizer_input = SynthesizerInput(
            query="Test",
            query_type=QueryType.SIMPLE,
            analysis=create_sample_analyzer_output_sufficient(),
            vocabulary={},
            response_style="concise",
        )
        prompt = synthesizer.build_prompt(synthesizer_input)

        assert "CONCISE STYLE" in prompt
        assert "50-100 words" in prompt
        assert "2-4 sentences" in prompt

    def test_prompt_detailed_style_guidance(self) -> None:
        """Prompt includes detailed style guidance."""
        client = create_mock_llm_client({})
        synthesizer = SynthesizerAgent(client)

        synthesizer_input = SynthesizerInput(
            query="Test",
            query_type=QueryType.SIMPLE,
            analysis=create_sample_analyzer_output_sufficient(),
            vocabulary={},
            response_style="detailed",
        )
        prompt = synthesizer.build_prompt(synthesizer_input)

        assert "DETAILED STYLE" in prompt
        assert "200-400 words" in prompt
        assert "Full context" in prompt

    def test_prompt_partial_answer_handling(self) -> None:
        """Prompt includes partial answer instructions when is_partial=True."""
        client = create_mock_llm_client({})
        synthesizer = SynthesizerAgent(client)

        gaps = create_sample_gaps()
        synthesizer_input = SynthesizerInput(
            query="Test",
            query_type=QueryType.SIMPLE,
            analysis=create_sample_analyzer_output_insufficient(),
            vocabulary={},
            is_partial=True,
            unanswered_gaps=gaps,
        )
        prompt = synthesizer.build_prompt(synthesizer_input)

        assert "PARTIAL ANSWER REQUIRED" in prompt
        assert "Here's what I can tell you" in prompt
        assert "To provide a more complete answer" in prompt
        assert "Historical comparison data" in prompt

    def test_prompt_not_partial_when_false(self) -> None:
        """Prompt does not include partial instructions when is_partial=False."""
        client = create_mock_llm_client({})
        synthesizer = SynthesizerAgent(client)

        synthesizer_input = SynthesizerInput(
            query="Test",
            query_type=QueryType.SIMPLE,
            analysis=create_sample_analyzer_output_sufficient(),
            vocabulary={},
            is_partial=False,
        )
        prompt = synthesizer.build_prompt(synthesizer_input)

        assert "PARTIAL ANSWER REQUIRED" not in prompt

    def test_prompt_includes_confidence_mapping(self) -> None:
        """Prompt includes confidence level mapping."""
        client = create_mock_llm_client({})
        synthesizer = SynthesizerAgent(client)

        synthesizer_input = SynthesizerInput(
            query="Test",
            query_type=QueryType.SIMPLE,
            analysis=create_sample_analyzer_output_sufficient(),
            vocabulary={},
        )
        prompt = synthesizer.build_prompt(synthesizer_input)

        assert "CONFIDENCE MAPPING" in prompt
        assert 'confidence: "high"' in prompt

    def test_prompt_response_guidelines(self) -> None:
        """Prompt includes response guidelines."""
        client = create_mock_llm_client({})
        synthesizer = SynthesizerAgent(client)

        synthesizer_input = SynthesizerInput(
            query="Test",
            query_type=QueryType.SIMPLE,
            analysis=create_sample_analyzer_output_sufficient(),
            vocabulary={},
        )
        prompt = synthesizer.build_prompt(synthesizer_input)

        assert "Address what the user asked directly" in prompt
        assert "Support claims with evidence" in prompt
        assert "domain-appropriate terminology" in prompt


# =============================================================================
# Test Synthesize Method (Task 4, 6.4)
# =============================================================================


class TestSynthesizeMethod:
    """Tests for SynthesizerAgent.synthesize method."""

    @pytest.mark.asyncio
    async def test_successful_synthesis_high_confidence(self) -> None:
        """Test successful synthesis with high confidence."""
        response: dict[str, Any] = {
            "response": (
                "Your bench press has improved by 10 lbs over the past week, progressing from 175 lbs to 185 lbs."
            ),
            "key_points": [
                "10 lb increase in bench press",
                "Progression over 7 days",
                "Consistent rep range maintained",
            ],
            "evidence_cited": [
                "2026-01-03: bench 175x5",
                "2026-01-10: bench 185x5",
            ],
            "gaps_disclosed": [],
            "confidence": "high",
        }
        client = create_mock_llm_client(response)
        synthesizer = SynthesizerAgent(client)

        result = await synthesizer.synthesize(
            SynthesizerInput(
                query="How has my bench press progressed?",
                query_type=QueryType.INSIGHT,
                analysis=create_sample_analyzer_output_sufficient(),
                vocabulary=create_sample_vocabulary(),
            )
        )

        assert "improved by 10 lbs" in result.response
        assert len(result.key_points) == 3
        assert len(result.evidence_cited) == 2
        assert result.confidence == "high"

    @pytest.mark.asyncio
    async def test_synthesis_with_partial_answer(self) -> None:
        """Test synthesis with partial answer (is_partial=True)."""
        response: dict[str, Any] = {
            "response": (
                "Here's what I can tell you: Some improvement observed. "
                "To provide a more complete answer, I would need historical data."
            ),
            "key_points": ["Limited improvement data available"],
            "evidence_cited": ["entry1"],
            "gaps_disclosed": ["Historical comparison data from previous month"],
            "confidence": "low",
        }
        client = create_mock_llm_client(response)
        synthesizer = SynthesizerAgent(client)

        result = await synthesizer.synthesize(
            SynthesizerInput(
                query="How is my progress?",
                query_type=QueryType.INSIGHT,
                analysis=create_sample_analyzer_output_insufficient(),
                vocabulary={},
                is_partial=True,
                unanswered_gaps=create_sample_gaps(),
            )
        )

        assert "Here's what I can tell you" in result.response
        assert len(result.gaps_disclosed) == 1
        assert result.confidence == "low"

    @pytest.mark.asyncio
    async def test_synthesis_medium_confidence(self) -> None:
        """Test synthesis with medium confidence (PARTIAL verdict)."""
        response: dict[str, Any] = {
            "response": "Based on available data, you appear to be making progress.",
            "key_points": ["Some improvement observed"],
            "evidence_cited": ["entry1"],
            "gaps_disclosed": [],
            "confidence": "medium",
        }
        client = create_mock_llm_client(response)
        synthesizer = SynthesizerAgent(client)

        result = await synthesizer.synthesize(
            SynthesizerInput(
                query="How is my progress?",
                query_type=QueryType.INSIGHT,
                analysis=create_sample_analyzer_output_partial(),
                vocabulary={},
            )
        )

        assert result.confidence == "medium"

    @pytest.mark.asyncio
    async def test_empty_query_raises_validation_error(self) -> None:
        """Test that empty query raises ValidationError from Pydantic."""
        client = create_mock_llm_client({})
        synthesizer = SynthesizerAgent(client)

        with pytest.raises(ValidationError):
            await synthesizer.synthesize(
                SynthesizerInput(
                    query="",
                    query_type=QueryType.SIMPLE,
                    analysis=create_sample_analyzer_output_sufficient(),
                    vocabulary={},
                )
            )

    @pytest.mark.asyncio
    async def test_whitespace_only_query_raises_value_error(self) -> None:
        """Test that whitespace-only query raises ValueError."""
        client = create_mock_llm_client({})
        synthesizer = SynthesizerAgent(client)

        with pytest.raises(ValueError, match="empty or whitespace"):
            await synthesizer.synthesize(
                SynthesizerInput(
                    query="   \n\t  ",
                    query_type=QueryType.SIMPLE,
                    analysis=create_sample_analyzer_output_sufficient(),
                    vocabulary={},
                )
            )

    @pytest.mark.asyncio
    async def test_detailed_response_style(self) -> None:
        """Test synthesis with detailed response style."""
        response: dict[str, Any] = {
            "response": (
                "Your bench press has shown consistent improvement over the past week. "
                "Starting at 175 lbs on January 3rd, you've progressed to 185 lbs by "
                "January 10th, representing a 5.7% increase in working weight. "
                "This demonstrates effective progressive overload."
            ),
            "key_points": [
                "10 lb increase (175 → 185 lbs)",
                "5.7% improvement in 7 days",
                "Consistent 5-rep sets maintained",
                "Progressive overload principle demonstrated",
            ],
            "evidence_cited": [
                "2026-01-03: bench 175x5",
                "2026-01-05: bench 177x5",
                "2026-01-08: bench 180x5",
                "2026-01-10: bench 185x5",
            ],
            "gaps_disclosed": [],
            "confidence": "high",
        }
        client = create_mock_llm_client(response)
        synthesizer = SynthesizerAgent(client)

        result = await synthesizer.synthesize(
            SynthesizerInput(
                query="How has my bench press progressed?",
                query_type=QueryType.INSIGHT,
                analysis=create_sample_analyzer_output_sufficient(),
                vocabulary=create_sample_vocabulary(),
                response_style="detailed",
            )
        )

        assert len(result.response) > 100  # Detailed should be longer
        assert len(result.key_points) >= 3
        assert len(result.evidence_cited) >= 2


# =============================================================================
# Test Exports (Task 5, 6.5)
# =============================================================================


class TestSynthesizerExports:
    """Tests for synthesizer exports from quilto.agents."""

    def test_synthesizer_agent_importable(self) -> None:
        """SynthesizerAgent is importable from quilto.agents."""
        from quilto.agents import SynthesizerAgent

        assert SynthesizerAgent is not None

    def test_synthesizer_input_importable(self) -> None:
        """SynthesizerInput is importable from quilto.agents."""
        from quilto.agents import SynthesizerInput

        assert SynthesizerInput is not None

    def test_synthesizer_output_importable(self) -> None:
        """SynthesizerOutput is importable from quilto.agents."""
        from quilto.agents import SynthesizerOutput

        assert SynthesizerOutput is not None

    def test_all_exports_in_all_list(self) -> None:
        """All new types are in __all__ list."""
        from quilto import agents

        assert "SynthesizerAgent" in agents.__all__
        assert "SynthesizerInput" in agents.__all__
        assert "SynthesizerOutput" in agents.__all__


# =============================================================================
# Integration Tests
# =============================================================================


class TestSynthesizerIntegration:
    """Integration tests with real Ollama.

    Run with: pytest --use-real-ollama -k TestSynthesizerIntegration
    Or via: make test-ollama
    """

    @pytest.mark.asyncio
    async def test_real_synthesis_sufficient_verdict(
        self, use_real_ollama: bool, integration_llm_config_path: Path
    ) -> None:
        """Test real synthesis with sufficient analysis data."""
        if not use_real_ollama:
            pytest.skip("Requires --use-real-ollama flag")

        config = load_llm_config(integration_llm_config_path)
        real_llm_client = LLMClient(config)
        synthesizer = SynthesizerAgent(real_llm_client)

        result = await synthesizer.synthesize(
            SynthesizerInput(
                query="How has my bench press progressed?",
                query_type=QueryType.INSIGHT,
                analysis=create_sample_analyzer_output_sufficient(),
                vocabulary=create_sample_vocabulary(),
            )
        )

        # Should have valid output structure
        assert result.response is not None
        assert len(result.response) > 0
        assert result.confidence in ["high", "medium", "low"]
        assert isinstance(result.key_points, list)
        assert isinstance(result.evidence_cited, list)

    @pytest.mark.asyncio
    async def test_real_synthesis_partial_answer(
        self, use_real_ollama: bool, integration_llm_config_path: Path
    ) -> None:
        """Test real synthesis with partial answer."""
        if not use_real_ollama:
            pytest.skip("Requires --use-real-ollama flag")

        config = load_llm_config(integration_llm_config_path)
        real_llm_client = LLMClient(config)
        synthesizer = SynthesizerAgent(real_llm_client)

        result = await synthesizer.synthesize(
            SynthesizerInput(
                query="How is my overall fitness progress?",
                query_type=QueryType.INSIGHT,
                analysis=create_sample_analyzer_output_insufficient(),
                vocabulary=create_sample_vocabulary(),
                is_partial=True,
                unanswered_gaps=create_sample_gaps(),
            )
        )

        # Should have valid output with appropriate confidence
        assert result.response is not None
        assert len(result.response) > 0
        # With partial answer, should have low or medium confidence
        assert result.confidence in ["low", "medium"]

    @pytest.mark.asyncio
    async def test_real_synthesis_detailed_style(
        self, use_real_ollama: bool, integration_llm_config_path: Path
    ) -> None:
        """Test real synthesis with detailed response style."""
        if not use_real_ollama:
            pytest.skip("Requires --use-real-ollama flag")

        config = load_llm_config(integration_llm_config_path)
        real_llm_client = LLMClient(config)
        synthesizer = SynthesizerAgent(real_llm_client)

        result = await synthesizer.synthesize(
            SynthesizerInput(
                query="How has my bench press progressed?",
                query_type=QueryType.INSIGHT,
                analysis=create_sample_analyzer_output_sufficient(),
                vocabulary=create_sample_vocabulary(),
                response_style="detailed",
            )
        )

        # Detailed style should produce longer response
        assert result.response is not None
        assert len(result.response) > 50  # Should be more than a short answer
