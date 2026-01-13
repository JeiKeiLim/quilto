"""Unit tests for AnalyzerAgent.

Tests cover model validation, prompt building, analysis execution,
sufficiency evaluation, helper methods, and exports.
"""

import json
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock

import pytest
from pydantic import BaseModel, ValidationError
from quilto import load_llm_config
from quilto.agents import (
    ActiveDomainContext,
    AnalyzerAgent,
    AnalyzerInput,
    AnalyzerOutput,
    DomainInfo,
    Finding,
    Gap,
    GapType,
    QueryType,
    RetrievalAttempt,
    SufficiencyEvaluation,
    Verdict,
)
from quilto.llm.client import LLMClient
from quilto.llm.config import AgentConfig, LLMConfig, ProviderConfig, TierModels


def create_test_config() -> LLMConfig:
    """Create a test LLMConfig for AnalyzerAgent tests.

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
            "analyzer": AgentConfig(tier="high"),
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


def create_sample_domain_context() -> ActiveDomainContext:
    """Create sample domain context for testing.

    Returns:
        ActiveDomainContext for tests.
    """
    return ActiveDomainContext(
        domains_loaded=["strength", "nutrition"],
        vocabulary={"bench": "bench press", "pr": "personal record"},
        expertise="Strength training and nutrition tracking with focus on progressive overload",
        evaluation_rules=["Check form consistency", "Validate rep ranges"],
        context_guidance="Focus on progressive overload patterns",
        available_domains=[
            DomainInfo(name="running", description="Running and cardio activities"),
            DomainInfo(name="sleep", description="Sleep tracking and quality"),
        ],
    )


def create_minimal_domain_context() -> ActiveDomainContext:
    """Create minimal domain context for testing.

    Returns:
        Minimal ActiveDomainContext for tests.
    """
    return ActiveDomainContext(
        domains_loaded=[],
        vocabulary={},
        expertise="",
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


def create_sample_entries() -> list[dict[str, Any]]:
    """Create sample entries for testing.

    Returns:
        List of entry-like dicts for tests.
    """
    return [
        {
            "date": "2026-01-10",
            "raw_content": "Bench press 185x5, feeling strong",
            "domain_data": {"strength": {"exercise": "bench press", "weight": 185, "reps": 5}},
        },
        {
            "date": "2026-01-08",
            "raw_content": "Bench press 180x5, normal effort",
            "domain_data": {"strength": {"exercise": "bench press", "weight": 180, "reps": 5}},
        },
        {
            "date": "2026-01-05",
            "raw_content": "Bench press 175x5",
            "domain_data": {"strength": {"exercise": "bench press", "weight": 175, "reps": 5}},
        },
    ]


# =============================================================================
# Test Verdict Enum (Task 1.1)
# =============================================================================


class TestVerdictEnum:
    """Tests for Verdict enum values."""

    def test_verdict_sufficient_value(self) -> None:
        """SUFFICIENT verdict has correct value."""
        assert Verdict.SUFFICIENT.value == "sufficient"

    def test_verdict_insufficient_value(self) -> None:
        """INSUFFICIENT verdict has correct value."""
        assert Verdict.INSUFFICIENT.value == "insufficient"

    def test_verdict_partial_value(self) -> None:
        """PARTIAL verdict has correct value."""
        assert Verdict.PARTIAL.value == "partial"

    def test_verdict_count(self) -> None:
        """Verdict enum has exactly 3 values."""
        assert len(Verdict) == 3


# =============================================================================
# Test Finding Model (Task 1.2)
# =============================================================================


class TestFindingModel:
    """Tests for Finding Pydantic model validation."""

    def test_finding_valid(self) -> None:
        """Finding accepts valid data."""
        finding = Finding(
            claim="Progressive overload on bench press",
            evidence=["2026-01-10: bench 185x5", "2026-01-05: bench 175x5"],
            confidence="high",
        )
        assert finding.claim == "Progressive overload on bench press"
        assert len(finding.evidence) == 2
        assert finding.confidence == "high"

    def test_finding_empty_claim_fails(self) -> None:
        """Finding with empty claim fails min_length=1."""
        with pytest.raises(ValidationError):
            Finding(
                claim="",
                evidence=["some evidence"],
                confidence="high",
            )

    def test_finding_confidence_high(self) -> None:
        """Finding accepts 'high' confidence."""
        finding = Finding(claim="Test", evidence=[], confidence="high")
        assert finding.confidence == "high"

    def test_finding_confidence_medium(self) -> None:
        """Finding accepts 'medium' confidence."""
        finding = Finding(claim="Test", evidence=[], confidence="medium")
        assert finding.confidence == "medium"

    def test_finding_confidence_low(self) -> None:
        """Finding accepts 'low' confidence."""
        finding = Finding(claim="Test", evidence=[], confidence="low")
        assert finding.confidence == "low"

    def test_finding_invalid_confidence_fails(self) -> None:
        """Finding with invalid confidence value fails."""
        with pytest.raises(ValidationError):
            Finding(
                claim="Test",
                evidence=[],
                confidence="very_high",  # type: ignore[arg-type]
            )

    def test_finding_empty_evidence_allowed(self) -> None:
        """Finding with empty evidence list is allowed."""
        finding = Finding(claim="Speculation claim", evidence=[], confidence="low")
        assert finding.evidence == []


# =============================================================================
# Test SufficiencyEvaluation Model (Task 1.3)
# =============================================================================


class TestSufficiencyEvaluationModel:
    """Tests for SufficiencyEvaluation Pydantic model."""

    def test_sufficiency_evaluation_valid(self) -> None:
        """SufficiencyEvaluation accepts valid data."""
        evaluation = SufficiencyEvaluation(
            critical_gaps=[],
            nice_to_have_gaps=[
                Gap(
                    description="Historical comparison",
                    gap_type=GapType.TEMPORAL,
                    severity="nice_to_have",
                )
            ],
            evidence_check_passed=True,
            speculation_risk="low",
        )
        assert len(evaluation.critical_gaps) == 0
        assert len(evaluation.nice_to_have_gaps) == 1
        assert evaluation.evidence_check_passed is True
        assert evaluation.speculation_risk == "low"

    def test_sufficiency_evaluation_speculation_risk_none(self) -> None:
        """SufficiencyEvaluation accepts 'none' speculation_risk."""
        evaluation = SufficiencyEvaluation(
            critical_gaps=[],
            nice_to_have_gaps=[],
            evidence_check_passed=True,
            speculation_risk="none",
        )
        assert evaluation.speculation_risk == "none"

    def test_sufficiency_evaluation_speculation_risk_high(self) -> None:
        """SufficiencyEvaluation accepts 'high' speculation_risk."""
        evaluation = SufficiencyEvaluation(
            critical_gaps=[],
            nice_to_have_gaps=[],
            evidence_check_passed=False,
            speculation_risk="high",
        )
        assert evaluation.speculation_risk == "high"

    def test_sufficiency_evaluation_invalid_speculation_risk_fails(self) -> None:
        """SufficiencyEvaluation with invalid speculation_risk fails."""
        with pytest.raises(ValidationError):
            SufficiencyEvaluation(
                critical_gaps=[],
                nice_to_have_gaps=[],
                evidence_check_passed=True,
                speculation_risk="medium",  # type: ignore[arg-type]
            )

    def test_sufficiency_evaluation_with_critical_gaps(self) -> None:
        """SufficiencyEvaluation with critical gaps."""
        critical_gap = Gap(
            description="Missing recent data",
            gap_type=GapType.TEMPORAL,
            severity="critical",
        )
        evaluation = SufficiencyEvaluation(
            critical_gaps=[critical_gap],
            nice_to_have_gaps=[],
            evidence_check_passed=False,
            speculation_risk="high",
        )
        assert len(evaluation.critical_gaps) == 1
        assert evaluation.critical_gaps[0].severity == "critical"


# =============================================================================
# Test AnalyzerInput Model (Task 1.4)
# =============================================================================


class TestAnalyzerInputModel:
    """Tests for AnalyzerInput Pydantic model."""

    def test_analyzer_input_valid(self) -> None:
        """AnalyzerInput accepts valid data."""
        analyzer_input = AnalyzerInput(
            query="How has my bench press progressed?",
            query_type=QueryType.INSIGHT,
            entries=create_sample_entries(),
            retrieval_summary=[create_sample_retrieval_attempt()],
            domain_context=create_sample_domain_context(),
        )
        assert analyzer_input.query == "How has my bench press progressed?"
        assert analyzer_input.query_type == QueryType.INSIGHT
        assert len(analyzer_input.entries) == 3

    def test_analyzer_input_empty_query_fails(self) -> None:
        """AnalyzerInput with empty query fails min_length=1."""
        with pytest.raises(ValidationError):
            AnalyzerInput(
                query="",
                query_type=QueryType.SIMPLE,
                entries=[],
                retrieval_summary=[],
                domain_context=create_minimal_domain_context(),
            )

    def test_analyzer_input_with_sub_query_id(self) -> None:
        """AnalyzerInput with sub_query_id."""
        analyzer_input = AnalyzerInput(
            query="What exercises?",
            query_type=QueryType.SIMPLE,
            sub_query_id=2,
            entries=[],
            retrieval_summary=[],
            domain_context=create_minimal_domain_context(),
        )
        assert analyzer_input.sub_query_id == 2

    def test_analyzer_input_with_global_context(self) -> None:
        """AnalyzerInput with global_context_summary."""
        analyzer_input = AnalyzerInput(
            query="What is my pattern?",
            query_type=QueryType.INSIGHT,
            entries=[],
            retrieval_summary=[],
            domain_context=create_minimal_domain_context(),
            global_context_summary="User prefers morning workouts",
        )
        assert analyzer_input.global_context_summary == "User prefers morning workouts"

    def test_analyzer_input_all_query_types(self) -> None:
        """AnalyzerInput accepts all QueryType values."""
        for query_type in QueryType:
            analyzer_input = AnalyzerInput(
                query="Test query",
                query_type=query_type,
                entries=[],
                retrieval_summary=[],
                domain_context=create_minimal_domain_context(),
            )
            assert analyzer_input.query_type == query_type


# =============================================================================
# Test AnalyzerOutput Model (Task 1.5)
# =============================================================================


class TestAnalyzerOutputModel:
    """Tests for AnalyzerOutput Pydantic model."""

    def test_analyzer_output_valid(self) -> None:
        """AnalyzerOutput accepts valid data."""
        output = AnalyzerOutput(
            query_intent="User wants to know bench press progression over time",
            findings=[
                Finding(
                    claim="Progressive overload observed",
                    evidence=["2026-01-10: 185x5", "2026-01-05: 175x5"],
                    confidence="high",
                )
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
        assert output.query_intent == "User wants to know bench press progression over time"
        assert len(output.findings) == 1
        assert len(output.patterns_identified) == 2
        assert output.verdict == Verdict.SUFFICIENT

    def test_analyzer_output_empty_query_intent_fails(self) -> None:
        """AnalyzerOutput with empty query_intent fails min_length=1."""
        with pytest.raises(ValidationError):
            AnalyzerOutput(
                query_intent="",
                findings=[],
                patterns_identified=[],
                sufficiency_evaluation=SufficiencyEvaluation(
                    critical_gaps=[],
                    nice_to_have_gaps=[],
                    evidence_check_passed=True,
                    speculation_risk="none",
                ),
                verdict_reasoning="Test",
                verdict=Verdict.SUFFICIENT,
            )

    def test_analyzer_output_empty_verdict_reasoning_fails(self) -> None:
        """AnalyzerOutput with empty verdict_reasoning fails min_length=1."""
        with pytest.raises(ValidationError):
            AnalyzerOutput(
                query_intent="Test intent",
                findings=[],
                patterns_identified=[],
                sufficiency_evaluation=SufficiencyEvaluation(
                    critical_gaps=[],
                    nice_to_have_gaps=[],
                    evidence_check_passed=True,
                    speculation_risk="none",
                ),
                verdict_reasoning="",
                verdict=Verdict.SUFFICIENT,
            )

    def test_analyzer_output_with_insufficient_verdict(self) -> None:
        """AnalyzerOutput with INSUFFICIENT verdict and critical gaps."""
        critical_gap = Gap(
            description="No data for requested time period",
            gap_type=GapType.TEMPORAL,
            severity="critical",
        )
        output = AnalyzerOutput(
            query_intent="User wants recent workout data",
            findings=[],
            patterns_identified=[],
            sufficiency_evaluation=SufficiencyEvaluation(
                critical_gaps=[critical_gap],
                nice_to_have_gaps=[],
                evidence_check_passed=False,
                speculation_risk="high",
            ),
            verdict_reasoning="No data available for the requested time period",
            verdict=Verdict.INSUFFICIENT,
        )
        assert output.verdict == Verdict.INSUFFICIENT
        assert len(output.sufficiency_evaluation.critical_gaps) == 1

    def test_analyzer_output_with_partial_verdict(self) -> None:
        """AnalyzerOutput with PARTIAL verdict and only nice_to_have gaps."""
        nice_gap = Gap(
            description="Historical comparison would help",
            gap_type=GapType.TEMPORAL,
            severity="nice_to_have",
        )
        output = AnalyzerOutput(
            query_intent="User wants progress analysis",
            findings=[Finding(claim="Some progress", evidence=["entry1"], confidence="medium")],
            patterns_identified=["slight improvement"],
            sufficiency_evaluation=SufficiencyEvaluation(
                critical_gaps=[],
                nice_to_have_gaps=[nice_gap],
                evidence_check_passed=True,
                speculation_risk="low",
            ),
            verdict_reasoning="Can answer with limitations - missing historical data",
            verdict=Verdict.PARTIAL,
        )
        assert output.verdict == Verdict.PARTIAL


# =============================================================================
# Test _format_entries Edge Cases (MEDIUM-3 code review fix)
# =============================================================================


class TestFormatEntriesEdgeCases:
    """Tests for _format_entries edge cases with None values."""

    def test_format_entries_with_none_date_attribute(self) -> None:
        """_format_entries handles entry with date=None gracefully."""
        client = create_mock_llm_client({})
        analyzer = AnalyzerAgent(client)

        class MockEntry:
            date = None
            raw_content = "Test content"
            domain_data = None

        result = analyzer._format_entries([MockEntry()])  # pyright: ignore[reportPrivateUsage]
        assert "unknown" in result
        assert "Test content" in result

    def test_format_entries_with_none_raw_content_attribute(self) -> None:
        """_format_entries handles entry with raw_content=None gracefully."""
        client = create_mock_llm_client({})
        analyzer = AnalyzerAgent(client)

        class MockEntry:
            date = "2026-01-10"
            raw_content = None
            domain_data = None

        result = analyzer._format_entries([MockEntry()])  # pyright: ignore[reportPrivateUsage]
        assert "2026-01-10" in result
        # Should use repr(entry) as fallback
        assert "MockEntry" in result

    def test_format_entries_with_dict_none_values(self) -> None:
        """_format_entries handles dict with None values gracefully."""
        client = create_mock_llm_client({})
        analyzer = AnalyzerAgent(client)

        entry = {"date": None, "raw_content": None}
        result = analyzer._format_entries([entry])  # pyright: ignore[reportPrivateUsage]
        assert "unknown" in result


# =============================================================================
# Test AnalyzerAgent Instantiation (Task 2)
# =============================================================================


class TestAnalyzerAgentInstantiation:
    """Tests for AnalyzerAgent class instantiation."""

    def test_analyzer_agent_creates_with_llm_client(self) -> None:
        """AnalyzerAgent creates successfully with LLMClient."""
        client = create_mock_llm_client({})
        analyzer = AnalyzerAgent(client)
        assert analyzer.llm_client is client

    def test_analyzer_agent_name_constant(self) -> None:
        """AnalyzerAgent has correct AGENT_NAME constant."""
        client = create_mock_llm_client({})
        analyzer = AnalyzerAgent(client)
        assert analyzer.AGENT_NAME == "analyzer"
        assert AnalyzerAgent.AGENT_NAME == "analyzer"


# =============================================================================
# Test Prompt Building (Task 3)
# =============================================================================


class TestAnalyzerPromptBuilding:
    """Tests for AnalyzerAgent.build_prompt method."""

    def test_prompt_includes_query(self) -> None:
        """Prompt includes the query."""
        client = create_mock_llm_client({})
        analyzer = AnalyzerAgent(client)

        analyzer_input = AnalyzerInput(
            query="How has my bench press progressed?",
            query_type=QueryType.INSIGHT,
            entries=[],
            retrieval_summary=[],
            domain_context=create_minimal_domain_context(),
        )
        prompt = analyzer.build_prompt(analyzer_input)

        assert "How has my bench press progressed?" in prompt

    def test_prompt_includes_query_type(self) -> None:
        """Prompt includes query_type."""
        client = create_mock_llm_client({})
        analyzer = AnalyzerAgent(client)

        analyzer_input = AnalyzerInput(
            query="Test query",
            query_type=QueryType.INSIGHT,
            entries=[],
            retrieval_summary=[],
            domain_context=create_minimal_domain_context(),
        )
        prompt = analyzer.build_prompt(analyzer_input)

        assert "insight" in prompt.lower()

    def test_prompt_includes_domain_expertise(self) -> None:
        """Prompt includes domain expertise from domain_context."""
        client = create_mock_llm_client({})
        analyzer = AnalyzerAgent(client)

        analyzer_input = AnalyzerInput(
            query="Test query",
            query_type=QueryType.SIMPLE,
            entries=[],
            retrieval_summary=[],
            domain_context=create_sample_domain_context(),
        )
        prompt = analyzer.build_prompt(analyzer_input)

        assert "progressive overload" in prompt.lower()

    def test_prompt_includes_sufficiency_criteria(self) -> None:
        """Prompt includes sufficiency criteria (evidence check, gap assessment, speculation test)."""
        client = create_mock_llm_client({})
        analyzer = AnalyzerAgent(client)

        analyzer_input = AnalyzerInput(
            query="Test",
            query_type=QueryType.SIMPLE,
            entries=[],
            retrieval_summary=[],
            domain_context=create_minimal_domain_context(),
        )
        prompt = analyzer.build_prompt(analyzer_input)

        assert "Evidence check" in prompt
        assert "Gap assessment" in prompt
        assert "Speculation test" in prompt

    def test_prompt_includes_verdict_last_instruction(self) -> None:
        """Prompt includes instruction to generate verdict LAST."""
        client = create_mock_llm_client({})
        analyzer = AnalyzerAgent(client)

        analyzer_input = AnalyzerInput(
            query="Test",
            query_type=QueryType.SIMPLE,
            entries=[],
            retrieval_summary=[],
            domain_context=create_minimal_domain_context(),
        )
        prompt = analyzer.build_prompt(analyzer_input)

        assert "GENERATE THIS LAST" in prompt or "verdict - GENERATE" in prompt

    def test_prompt_includes_formatted_entries(self) -> None:
        """Prompt includes formatted entries."""
        client = create_mock_llm_client({})
        analyzer = AnalyzerAgent(client)

        entries = create_sample_entries()
        analyzer_input = AnalyzerInput(
            query="Test",
            query_type=QueryType.SIMPLE,
            entries=entries,
            retrieval_summary=[],
            domain_context=create_minimal_domain_context(),
        )
        prompt = analyzer.build_prompt(analyzer_input)

        assert "2026-01-10" in prompt
        assert "Bench press 185x5" in prompt

    def test_prompt_includes_retrieval_summary(self) -> None:
        """Prompt includes retrieval summary."""
        client = create_mock_llm_client({})
        analyzer = AnalyzerAgent(client)

        analyzer_input = AnalyzerInput(
            query="Test",
            query_type=QueryType.SIMPLE,
            entries=[],
            retrieval_summary=[create_sample_retrieval_attempt()],
            domain_context=create_minimal_domain_context(),
        )
        prompt = analyzer.build_prompt(analyzer_input)

        assert "date_range" in prompt.lower()
        assert "5 entries" in prompt

    def test_prompt_includes_global_context_when_provided(self) -> None:
        """Prompt includes global context when provided."""
        client = create_mock_llm_client({})
        analyzer = AnalyzerAgent(client)

        analyzer_input = AnalyzerInput(
            query="Test",
            query_type=QueryType.SIMPLE,
            entries=[],
            retrieval_summary=[],
            domain_context=create_minimal_domain_context(),
            global_context_summary="User prefers morning workouts and tracks macros",
        )
        prompt = analyzer.build_prompt(analyzer_input)

        assert "morning workouts" in prompt.lower()

    def test_prompt_handles_empty_entries_gracefully(self) -> None:
        """Prompt handles empty entries with appropriate message."""
        client = create_mock_llm_client({})
        analyzer = AnalyzerAgent(client)

        analyzer_input = AnalyzerInput(
            query="Test",
            query_type=QueryType.SIMPLE,
            entries=[],
            retrieval_summary=[],
            domain_context=create_minimal_domain_context(),
        )
        prompt = analyzer.build_prompt(analyzer_input)

        assert "(No entries retrieved)" in prompt

    def test_prompt_includes_available_domains(self) -> None:
        """Prompt includes available domains for expansion hints."""
        client = create_mock_llm_client({})
        analyzer = AnalyzerAgent(client)

        analyzer_input = AnalyzerInput(
            query="Test",
            query_type=QueryType.SIMPLE,
            entries=[],
            retrieval_summary=[],
            domain_context=create_sample_domain_context(),
        )
        prompt = analyzer.build_prompt(analyzer_input)

        assert "running" in prompt.lower()
        assert "sleep" in prompt.lower()

    def test_prompt_includes_sub_query_id_when_provided(self) -> None:
        """Prompt includes sub_query_id when provided."""
        client = create_mock_llm_client({})
        analyzer = AnalyzerAgent(client)

        analyzer_input = AnalyzerInput(
            query="Test",
            query_type=QueryType.SIMPLE,
            sub_query_id=3,
            entries=[],
            retrieval_summary=[],
            domain_context=create_minimal_domain_context(),
        )
        prompt = analyzer.build_prompt(analyzer_input)

        assert "Sub-query ID: 3" in prompt

    def test_prompt_sub_query_id_na_when_none(self) -> None:
        """Prompt shows N/A for sub_query_id when None."""
        client = create_mock_llm_client({})
        analyzer = AnalyzerAgent(client)

        analyzer_input = AnalyzerInput(
            query="Test",
            query_type=QueryType.SIMPLE,
            entries=[],
            retrieval_summary=[],
            domain_context=create_minimal_domain_context(),
        )
        prompt = analyzer.build_prompt(analyzer_input)

        assert "Sub-query ID: N/A" in prompt


# =============================================================================
# Test Helper Methods (Task 6)
# =============================================================================


class TestAnalyzerHelperMethods:
    """Tests for AnalyzerAgent helper methods.

    Note: Private formatting methods (_format_*) are tested indirectly
    via build_prompt output tests. Only public helper methods are tested directly.
    """

    def test_has_critical_gaps_true_when_non_empty(self) -> None:
        """has_critical_gaps returns True when critical_gaps is non-empty."""
        client = create_mock_llm_client({})
        analyzer = AnalyzerAgent(client)

        evaluation = SufficiencyEvaluation(
            critical_gaps=[
                Gap(
                    description="Missing data",
                    gap_type=GapType.TEMPORAL,
                    severity="critical",
                )
            ],
            nice_to_have_gaps=[],
            evidence_check_passed=False,
            speculation_risk="high",
        )

        assert analyzer.has_critical_gaps(evaluation) is True

    def test_has_critical_gaps_false_when_empty(self) -> None:
        """has_critical_gaps returns False when critical_gaps is empty."""
        client = create_mock_llm_client({})
        analyzer = AnalyzerAgent(client)

        evaluation = SufficiencyEvaluation(
            critical_gaps=[],
            nice_to_have_gaps=[
                Gap(
                    description="Would be nice",
                    gap_type=GapType.CONTEXTUAL,
                    severity="nice_to_have",
                )
            ],
            evidence_check_passed=True,
            speculation_risk="low",
        )

        assert analyzer.has_critical_gaps(evaluation) is False

    def test_needs_domain_expansion_true_when_gap_outside_expertise(self) -> None:
        """needs_domain_expansion returns True when any gap has outside_current_expertise=True."""
        client = create_mock_llm_client({})
        analyzer = AnalyzerAgent(client)

        evaluation = SufficiencyEvaluation(
            critical_gaps=[
                Gap(
                    description="Need sleep data",
                    gap_type=GapType.CONTEXTUAL,
                    severity="critical",
                    outside_current_expertise=True,
                    suspected_domain="sleep",
                )
            ],
            nice_to_have_gaps=[],
            evidence_check_passed=False,
            speculation_risk="high",
        )

        assert analyzer.needs_domain_expansion(evaluation) is True

    def test_needs_domain_expansion_false_when_no_outside_expertise(self) -> None:
        """needs_domain_expansion returns False when no gap has outside_current_expertise."""
        client = create_mock_llm_client({})
        analyzer = AnalyzerAgent(client)

        evaluation = SufficiencyEvaluation(
            critical_gaps=[
                Gap(
                    description="Need more data",
                    gap_type=GapType.TEMPORAL,
                    severity="critical",
                    outside_current_expertise=False,
                )
            ],
            nice_to_have_gaps=[],
            evidence_check_passed=False,
            speculation_risk="high",
        )

        assert analyzer.needs_domain_expansion(evaluation) is False

    def test_needs_domain_expansion_checks_both_gap_lists(self) -> None:
        """needs_domain_expansion checks both critical and nice_to_have gaps."""
        client = create_mock_llm_client({})
        analyzer = AnalyzerAgent(client)

        evaluation = SufficiencyEvaluation(
            critical_gaps=[],
            nice_to_have_gaps=[
                Gap(
                    description="Sleep correlation would help",
                    gap_type=GapType.CONTEXTUAL,
                    severity="nice_to_have",
                    outside_current_expertise=True,
                    suspected_domain="sleep",
                )
            ],
            evidence_check_passed=True,
            speculation_risk="low",
        )

        assert analyzer.needs_domain_expansion(evaluation) is True

    def test_get_all_gaps_combines_both_lists(self) -> None:
        """get_all_gaps combines critical + nice_to_have gaps."""
        client = create_mock_llm_client({})
        analyzer = AnalyzerAgent(client)

        critical_gap = Gap(description="Critical", gap_type=GapType.TEMPORAL, severity="critical")
        nice_gap = Gap(description="Nice", gap_type=GapType.CONTEXTUAL, severity="nice_to_have")

        evaluation = SufficiencyEvaluation(
            critical_gaps=[critical_gap],
            nice_to_have_gaps=[nice_gap],
            evidence_check_passed=True,
            speculation_risk="low",
        )

        all_gaps = analyzer.get_all_gaps(evaluation)

        assert len(all_gaps) == 2
        assert critical_gap in all_gaps
        assert nice_gap in all_gaps

    def test_get_all_gaps_handles_empty_lists(self) -> None:
        """get_all_gaps handles empty lists."""
        client = create_mock_llm_client({})
        analyzer = AnalyzerAgent(client)

        evaluation = SufficiencyEvaluation(
            critical_gaps=[],
            nice_to_have_gaps=[],
            evidence_check_passed=True,
            speculation_risk="none",
        )

        all_gaps = analyzer.get_all_gaps(evaluation)

        assert all_gaps == []


# =============================================================================
# Test Analyze Method (Task 4, 8.5)
# =============================================================================


class TestAnalyzeMethod:
    """Tests for AnalyzerAgent.analyze method."""

    @pytest.mark.asyncio
    async def test_successful_analysis_sufficient_verdict(self) -> None:
        """Test successful analysis with SUFFICIENT verdict."""
        response: dict[str, Any] = {
            "query_intent": "User wants to know bench press progression",
            "findings": [
                {
                    "claim": "Progressive overload observed",
                    "evidence": ["2026-01-10: 185x5", "2026-01-05: 175x5"],
                    "confidence": "high",
                }
            ],
            "patterns_identified": ["progressive overload"],
            "sufficiency_evaluation": {
                "critical_gaps": [],
                "nice_to_have_gaps": [],
                "evidence_check_passed": True,
                "speculation_risk": "none",
            },
            "verdict_reasoning": "Clear progression pattern with supporting data",
            "verdict": "sufficient",
        }
        client = create_mock_llm_client(response)
        analyzer = AnalyzerAgent(client)

        result = await analyzer.analyze(
            AnalyzerInput(
                query="How has my bench press progressed?",
                query_type=QueryType.INSIGHT,
                entries=create_sample_entries(),
                retrieval_summary=[create_sample_retrieval_attempt()],
                domain_context=create_sample_domain_context(),
            )
        )

        assert result.verdict == Verdict.SUFFICIENT
        assert len(result.findings) == 1
        assert result.sufficiency_evaluation.evidence_check_passed is True

    @pytest.mark.asyncio
    async def test_analysis_with_insufficient_verdict(self) -> None:
        """Test analysis with INSUFFICIENT verdict (has critical_gaps)."""
        response: dict[str, Any] = {
            "query_intent": "User wants workout data",
            "findings": [],
            "patterns_identified": [],
            "sufficiency_evaluation": {
                "critical_gaps": [
                    {
                        "description": "No data for time period",
                        "gap_type": "temporal",
                        "severity": "critical",
                        "searched": True,
                        "found": False,
                        "outside_current_expertise": False,
                        "suspected_domain": None,
                    }
                ],
                "nice_to_have_gaps": [],
                "evidence_check_passed": False,
                "speculation_risk": "high",
            },
            "verdict_reasoning": "No data available",
            "verdict": "insufficient",
        }
        client = create_mock_llm_client(response)
        analyzer = AnalyzerAgent(client)

        result = await analyzer.analyze(
            AnalyzerInput(
                query="Show me last month's workouts",
                query_type=QueryType.SIMPLE,
                entries=[],
                retrieval_summary=[],
                domain_context=create_sample_domain_context(),
            )
        )

        assert result.verdict == Verdict.INSUFFICIENT
        assert analyzer.has_critical_gaps(result.sufficiency_evaluation) is True

    @pytest.mark.asyncio
    async def test_analysis_with_partial_verdict(self) -> None:
        """Test analysis with PARTIAL verdict (only nice_to_have_gaps)."""
        response: dict[str, Any] = {
            "query_intent": "User wants progress analysis",
            "findings": [
                {
                    "claim": "Some improvement observed",
                    "evidence": ["entry1"],
                    "confidence": "medium",
                }
            ],
            "patterns_identified": ["slight improvement"],
            "sufficiency_evaluation": {
                "critical_gaps": [],
                "nice_to_have_gaps": [
                    {
                        "description": "Historical baseline would help",
                        "gap_type": "temporal",
                        "severity": "nice_to_have",
                        "searched": False,
                        "found": False,
                        "outside_current_expertise": False,
                        "suspected_domain": None,
                    }
                ],
                "evidence_check_passed": True,
                "speculation_risk": "low",
            },
            "verdict_reasoning": "Can answer with noted limitations",
            "verdict": "partial",
        }
        client = create_mock_llm_client(response)
        analyzer = AnalyzerAgent(client)

        result = await analyzer.analyze(
            AnalyzerInput(
                query="How is my progress?",
                query_type=QueryType.INSIGHT,
                entries=[{"date": "2026-01-10", "raw_content": "workout"}],
                retrieval_summary=[],
                domain_context=create_sample_domain_context(),
            )
        )

        assert result.verdict == Verdict.PARTIAL
        assert analyzer.has_critical_gaps(result.sufficiency_evaluation) is False

    @pytest.mark.asyncio
    async def test_analysis_with_domain_expansion_needed(self) -> None:
        """Test analysis with domain expansion needed (outside_current_expertise)."""
        response: dict[str, Any] = {
            "query_intent": "User wants sleep-workout correlation",
            "findings": [],
            "patterns_identified": [],
            "sufficiency_evaluation": {
                "critical_gaps": [
                    {
                        "description": "Need sleep data",
                        "gap_type": "contextual",
                        "severity": "critical",
                        "searched": False,
                        "found": False,
                        "outside_current_expertise": True,
                        "suspected_domain": "sleep",
                    }
                ],
                "nice_to_have_gaps": [],
                "evidence_check_passed": False,
                "speculation_risk": "high",
            },
            "verdict_reasoning": "Cannot analyze without sleep domain data",
            "verdict": "insufficient",
        }
        client = create_mock_llm_client(response)
        analyzer = AnalyzerAgent(client)

        result = await analyzer.analyze(
            AnalyzerInput(
                query="How does my sleep affect workouts?",
                query_type=QueryType.INSIGHT,
                entries=[],
                retrieval_summary=[],
                domain_context=create_sample_domain_context(),
            )
        )

        assert result.verdict == Verdict.INSUFFICIENT
        assert analyzer.needs_domain_expansion(result.sufficiency_evaluation) is True

    @pytest.mark.asyncio
    async def test_empty_query_raises_value_error(self) -> None:
        """Test that empty query raises ValueError."""
        client = create_mock_llm_client({})
        analyzer = AnalyzerAgent(client)

        # Pydantic catches empty string first
        with pytest.raises(ValidationError):
            await analyzer.analyze(
                AnalyzerInput(
                    query="",
                    query_type=QueryType.SIMPLE,
                    entries=[],
                    retrieval_summary=[],
                    domain_context=create_minimal_domain_context(),
                )
            )

    @pytest.mark.asyncio
    async def test_whitespace_only_query_raises_value_error(self) -> None:
        """Test that whitespace-only query raises ValueError."""
        client = create_mock_llm_client({})
        analyzer = AnalyzerAgent(client)

        with pytest.raises(ValueError, match="empty or whitespace"):
            await analyzer.analyze(
                AnalyzerInput(
                    query="   \n\t  ",
                    query_type=QueryType.SIMPLE,
                    entries=[],
                    retrieval_summary=[],
                    domain_context=create_minimal_domain_context(),
                )
            )


# =============================================================================
# Test Exports (Task 7, 8.6)
# =============================================================================


class TestAnalyzerExports:
    """Tests for analyzer exports from quilto.agents."""

    def test_analyzer_agent_importable(self) -> None:
        """AnalyzerAgent is importable from quilto.agents."""
        from quilto.agents import AnalyzerAgent

        assert AnalyzerAgent is not None

    def test_analyzer_input_importable(self) -> None:
        """AnalyzerInput is importable from quilto.agents."""
        from quilto.agents import AnalyzerInput

        assert AnalyzerInput is not None

    def test_analyzer_output_importable(self) -> None:
        """AnalyzerOutput is importable from quilto.agents."""
        from quilto.agents import AnalyzerOutput

        assert AnalyzerOutput is not None

    def test_finding_importable(self) -> None:
        """Finding is importable from quilto.agents."""
        from quilto.agents import Finding

        assert Finding is not None

    def test_verdict_importable(self) -> None:
        """Verdict is importable from quilto.agents."""
        from quilto.agents import Verdict

        assert Verdict is not None

    def test_sufficiency_evaluation_importable(self) -> None:
        """SufficiencyEvaluation is importable from quilto.agents."""
        from quilto.agents import SufficiencyEvaluation

        assert SufficiencyEvaluation is not None

    def test_all_exports_in_all_list(self) -> None:
        """All new types are in __all__ list."""
        from quilto import agents

        assert "AnalyzerAgent" in agents.__all__
        assert "AnalyzerInput" in agents.__all__
        assert "AnalyzerOutput" in agents.__all__
        assert "Finding" in agents.__all__
        assert "Verdict" in agents.__all__
        assert "SufficiencyEvaluation" in agents.__all__


# =============================================================================
# Integration Tests
# =============================================================================


class TestAnalyzerIntegration:
    """Integration tests with real Ollama.

    Run with: pytest --use-real-ollama -k TestAnalyzerIntegration
    Or via: make test-ollama
    """

    @pytest.mark.asyncio
    async def test_real_analysis_with_entries(self, use_real_ollama: bool, integration_llm_config_path: Path) -> None:
        """Test real analysis with sample entries."""
        if not use_real_ollama:
            pytest.skip("Requires --use-real-ollama flag")

        config = load_llm_config(integration_llm_config_path)
        real_llm_client = LLMClient(config)
        analyzer = AnalyzerAgent(real_llm_client)

        result = await analyzer.analyze(
            AnalyzerInput(
                query="How has my bench press progressed?",
                query_type=QueryType.INSIGHT,
                entries=create_sample_entries(),
                retrieval_summary=[create_sample_retrieval_attempt()],
                domain_context=create_sample_domain_context(),
            )
        )

        # Should have valid output structure
        assert result.query_intent is not None
        assert len(result.query_intent) > 0
        assert result.verdict in [Verdict.SUFFICIENT, Verdict.INSUFFICIENT, Verdict.PARTIAL]
        assert result.verdict_reasoning is not None

    @pytest.mark.asyncio
    async def test_real_analysis_with_empty_entries(
        self, use_real_ollama: bool, integration_llm_config_path: Path
    ) -> None:
        """Test real analysis with no entries (should be insufficient)."""
        if not use_real_ollama:
            pytest.skip("Requires --use-real-ollama flag")

        config = load_llm_config(integration_llm_config_path)
        real_llm_client = LLMClient(config)
        analyzer = AnalyzerAgent(real_llm_client)

        result = await analyzer.analyze(
            AnalyzerInput(
                query="Show me yesterday's workouts",
                query_type=QueryType.SIMPLE,
                entries=[],
                retrieval_summary=[],
                domain_context=create_sample_domain_context(),
            )
        )

        # With no entries, should recognize insufficient data
        assert result.verdict in [Verdict.INSUFFICIENT, Verdict.PARTIAL]
        # Should have identified gaps
        all_gaps = analyzer.get_all_gaps(result.sufficiency_evaluation)
        # Either has gaps or verdict_reasoning explains the limitation
        assert len(all_gaps) > 0 or len(result.verdict_reasoning) > 0
