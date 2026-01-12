"""Unit tests for PlannerAgent.

Tests cover query decomposition, dependency classification, retrieval strategy
generation, domain expansion detection, re-planning on feedback, and model validation.
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
    DependencyType,
    DomainInfo,
    EvaluationFeedback,
    Gap,
    GapType,
    PlannerAgent,
    PlannerInput,
    PlannerOutput,
    QueryType,
    RetrievalStrategy,
    SubQuery,
)
from quilto.llm.client import LLMClient
from quilto.llm.config import AgentConfig, LLMConfig, ProviderConfig, TierModels


def create_test_config() -> LLMConfig:
    """Create a test LLMConfig for PlannerAgent tests.

    Returns:
        Configured LLMConfig for testing.
    """
    return LLMConfig(
        default_provider="ollama",  # type: ignore[arg-type]
        providers={
            "ollama": ProviderConfig(api_base="http://localhost:11434"),
        },
        tiers={
            "low": TierModels(ollama="qwen2.5:7b"),
            "medium": TierModels(ollama="qwen2.5:14b"),
        },
        agents={
            "planner": AgentConfig(tier="low"),
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
        vocabulary={"bench": "bench press", "PR": "personal record"},
        expertise="Fitness tracking and nutrition logging",
        evaluation_rules=["Check units are consistent", "Validate date ranges"],
        context_guidance="Focus on progressive overload and balanced macros",
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


# =============================================================================
# Test Planner Enums (Task 1)
# =============================================================================


class TestPlannerEnums:
    """Tests for Planner-related enums (AC: #1, #2, #3)."""

    def test_query_type_values(self) -> None:
        """QueryType enum has correct values."""
        assert QueryType.SIMPLE.value == "simple"
        assert QueryType.INSIGHT.value == "insight"
        assert QueryType.RECOMMENDATION.value == "recommendation"
        assert QueryType.COMPARISON.value == "comparison"
        assert QueryType.CORRECTION.value == "correction"

    def test_query_type_count(self) -> None:
        """QueryType enum has exactly 5 values."""
        assert len(QueryType) == 5

    def test_dependency_type_values(self) -> None:
        """DependencyType enum has correct values."""
        assert DependencyType.INDEPENDENT.value == "independent"
        assert DependencyType.DEPENDENT.value == "dependent"
        assert DependencyType.COUPLED.value == "coupled"

    def test_dependency_type_count(self) -> None:
        """DependencyType enum has exactly 3 values."""
        assert len(DependencyType) == 3

    def test_gap_type_values(self) -> None:
        """GapType enum has correct values."""
        assert GapType.TEMPORAL.value == "temporal"
        assert GapType.TOPICAL.value == "topical"
        assert GapType.CONTEXTUAL.value == "contextual"
        assert GapType.SUBJECTIVE.value == "subjective"
        assert GapType.CLARIFICATION.value == "clarification"

    def test_gap_type_count(self) -> None:
        """GapType enum has exactly 5 values."""
        assert len(GapType) == 5

    def test_retrieval_strategy_values(self) -> None:
        """RetrievalStrategy enum has correct values."""
        assert RetrievalStrategy.DATE_RANGE.value == "date_range"
        assert RetrievalStrategy.KEYWORD.value == "keyword"
        assert RetrievalStrategy.TOPICAL.value == "topical"

    def test_retrieval_strategy_count(self) -> None:
        """RetrievalStrategy enum has exactly 3 values."""
        assert len(RetrievalStrategy) == 3


# =============================================================================
# Test Planner Models (Task 2)
# =============================================================================


class TestPlannerModels:
    """Tests for Planner Pydantic models (AC: #1, #2, #3)."""

    def test_gap_model_all_fields(self) -> None:
        """Gap model accepts all fields including outside_current_expertise."""
        gap = Gap(
            description="Missing sleep data",
            gap_type=GapType.TEMPORAL,
            severity="critical",
            searched=True,
            found=False,
            outside_current_expertise=True,
            suspected_domain="sleep",
        )
        assert gap.description == "Missing sleep data"
        assert gap.gap_type == GapType.TEMPORAL
        assert gap.severity == "critical"
        assert gap.searched is True
        assert gap.found is False
        assert gap.outside_current_expertise is True
        assert gap.suspected_domain == "sleep"

    def test_gap_model_defaults(self) -> None:
        """Gap model has correct defaults."""
        gap = Gap(
            description="Missing data",
            gap_type=GapType.CONTEXTUAL,
            severity="nice_to_have",
        )
        assert gap.searched is False
        assert gap.found is False
        assert gap.outside_current_expertise is False
        assert gap.suspected_domain is None

    def test_gap_severity_validation(self) -> None:
        """Gap severity must be 'critical' or 'nice_to_have'."""
        with pytest.raises(ValidationError):
            Gap(
                description="Test",
                gap_type=GapType.TEMPORAL,
                severity="invalid",  # type: ignore[arg-type]
            )

    def test_evaluation_feedback_model(self) -> None:
        """EvaluationFeedback model accepts all fields."""
        feedback = EvaluationFeedback(
            issue="Claim not supported by evidence",
            suggestion="Add more context about timeframe",
            affected_claim="Progress has been steady",
        )
        assert feedback.issue == "Claim not supported by evidence"
        assert feedback.suggestion == "Add more context about timeframe"
        assert feedback.affected_claim == "Progress has been steady"

    def test_evaluation_feedback_optional_claim(self) -> None:
        """EvaluationFeedback affected_claim is optional."""
        feedback = EvaluationFeedback(
            issue="General issue",
            suggestion="General suggestion",
        )
        assert feedback.affected_claim is None

    def test_sub_query_validation(self) -> None:
        """SubQuery validates all required fields."""
        sub_query = SubQuery(
            id=1,
            question="What did I bench yesterday?",
            retrieval_strategy="date_range",
            retrieval_params={"start_date": "2024-01-01", "end_date": "2024-01-01"},
        )
        assert sub_query.id == 1
        assert sub_query.question == "What did I bench yesterday?"
        assert sub_query.retrieval_strategy == "date_range"
        assert sub_query.retrieval_params == {"start_date": "2024-01-01", "end_date": "2024-01-01"}

    def test_sub_query_question_min_length(self) -> None:
        """SubQuery question must have min_length=1."""
        with pytest.raises(ValidationError):
            SubQuery(
                id=1,
                question="",
                retrieval_strategy="keyword",
                retrieval_params={},
            )

    def test_planner_input_query_min_length(self) -> None:
        """PlannerInput query must have min_length=1."""
        with pytest.raises(ValidationError):
            PlannerInput(
                query="",
                domain_context=create_minimal_domain_context(),
            )

    def test_planner_input_valid(self) -> None:
        """PlannerInput accepts valid input."""
        planner_input = PlannerInput(
            query="What did I eat yesterday?",
            query_type=QueryType.SIMPLE,
            domain_context=create_sample_domain_context(),
            global_context_summary="User is tracking fitness",
        )
        assert planner_input.query == "What did I eat yesterday?"
        assert planner_input.query_type == QueryType.SIMPLE
        assert planner_input.global_context_summary == "User is tracking fitness"

    def test_planner_input_with_gaps(self) -> None:
        """PlannerInput accepts gaps_from_analyzer."""
        gap = Gap(
            description="Missing yesterday's data",
            gap_type=GapType.TEMPORAL,
            severity="critical",
        )
        planner_input = PlannerInput(
            query="What did I eat yesterday?",
            domain_context=create_minimal_domain_context(),
            gaps_from_analyzer=[gap],
        )
        assert len(planner_input.gaps_from_analyzer) == 1

    def test_planner_input_with_feedback(self) -> None:
        """PlannerInput accepts evaluation_feedback."""
        feedback = EvaluationFeedback(
            issue="Missing context",
            suggestion="Expand date range",
        )
        planner_input = PlannerInput(
            query="What did I eat yesterday?",
            domain_context=create_minimal_domain_context(),
            evaluation_feedback=feedback,
        )
        assert planner_input.evaluation_feedback is not None

    def test_planner_output_validation(self) -> None:
        """PlannerOutput validates all required fields."""
        output = PlannerOutput(
            original_query="What did I eat yesterday?",
            query_type=QueryType.SIMPLE,
            sub_queries=[
                SubQuery(
                    id=1,
                    question="What did I eat yesterday?",
                    retrieval_strategy="date_range",
                    retrieval_params={"start_date": "2024-01-01", "end_date": "2024-01-01"},
                )
            ],
            dependencies=[],
            execution_strategy=DependencyType.COUPLED,
            execution_order=[1],
            retrieval_instructions=[{"strategy": "date_range", "params": {}, "sub_query_id": 1}],
            gaps_status={},
            next_action="retrieve",
            reasoning="Simple query about yesterday's food",
        )
        assert output.original_query == "What did I eat yesterday?"
        assert output.query_type == QueryType.SIMPLE
        assert output.execution_strategy == DependencyType.COUPLED
        assert output.next_action == "retrieve"

    def test_planner_output_with_expansion(self) -> None:
        """PlannerOutput can include domain expansion request."""
        output = PlannerOutput(
            original_query="How did my sleep affect my workout?",
            query_type=QueryType.INSIGHT,
            sub_queries=[
                SubQuery(
                    id=1,
                    question="How did my sleep affect my workout?",
                    retrieval_strategy="topical",
                    retrieval_params={"topics": ["sleep", "workout"]},
                )
            ],
            dependencies=[],
            execution_strategy=DependencyType.COUPLED,
            execution_order=[1],
            retrieval_instructions=[],
            gaps_status={},
            domain_expansion_request=["sleep"],
            expansion_reasoning="Query requires sleep data not currently loaded",
            next_action="expand_domain",
            reasoning="Need to expand to sleep domain",
        )
        assert output.domain_expansion_request == ["sleep"]
        assert output.expansion_reasoning is not None
        assert output.next_action == "expand_domain"

    def test_planner_output_with_clarify(self) -> None:
        """PlannerOutput can include clarify questions."""
        output = PlannerOutput(
            original_query="How am I doing?",
            query_type=QueryType.INSIGHT,
            sub_queries=[
                SubQuery(
                    id=1,
                    question="How am I doing?",
                    retrieval_strategy="topical",
                    retrieval_params={"topics": ["progress"]},
                )
            ],
            dependencies=[],
            execution_strategy=DependencyType.COUPLED,
            execution_order=[1],
            retrieval_instructions=[],
            gaps_status={},
            clarify_questions=["What aspect would you like to know about?"],
            next_action="clarify",
            reasoning="Query is too broad, need clarification",
        )
        assert output.clarify_questions == ["What aspect would you like to know about?"]
        assert output.next_action == "clarify"

    def test_active_domain_context_valid(self) -> None:
        """ActiveDomainContext accepts all fields."""
        context = create_sample_domain_context()
        assert "strength" in context.domains_loaded
        assert context.vocabulary["bench"] == "bench press"
        assert len(context.available_domains) == 2


# =============================================================================
# Test PlannerAgent Constants
# =============================================================================


class TestPlannerAgentConstants:
    """Tests for PlannerAgent class constants."""

    def test_agent_name_constant(self) -> None:
        """PlannerAgent has correct AGENT_NAME constant."""
        client = create_mock_llm_client({})
        planner = PlannerAgent(client)
        assert planner.AGENT_NAME == "planner"
        assert PlannerAgent.AGENT_NAME == "planner"


# =============================================================================
# Test Planner Classification (Task 3)
# =============================================================================


class TestPlannerClassification:
    """Tests for dependency classification (AC: #1, #2)."""

    @pytest.mark.asyncio
    async def test_simple_query_coupled(self) -> None:
        """Simple query returns COUPLED classification (AC: #1)."""
        response: dict[str, Any] = {
            "original_query": "What did I eat yesterday?",
            "query_type": "simple",
            "sub_queries": [
                {
                    "id": 1,
                    "question": "What did I eat yesterday?",
                    "retrieval_strategy": "date_range",
                    "retrieval_params": {"start_date": "2024-01-01", "end_date": "2024-01-01"},
                }
            ],
            "dependencies": [],
            "execution_strategy": "coupled",
            "execution_order": [1],
            "retrieval_instructions": [{"strategy": "date_range", "params": {}, "sub_query_id": 1}],
            "gaps_status": {},
            "next_action": "retrieve",
            "reasoning": "Single simple query",
        }
        client = create_mock_llm_client(response)
        planner = PlannerAgent(client)

        result = await planner.plan(
            PlannerInput(
                query="What did I eat yesterday?",
                domain_context=create_sample_domain_context(),
            )
        )

        assert result.execution_strategy == DependencyType.COUPLED
        assert len(result.sub_queries) == 1

    @pytest.mark.asyncio
    async def test_multi_part_independent(self) -> None:
        """Multi-part query with independent topics returns INDEPENDENT (AC: #2)."""
        response: dict[str, Any] = {
            "original_query": "How much did I bench and squat yesterday?",
            "query_type": "simple",
            "sub_queries": [
                {
                    "id": 1,
                    "question": "How much did I bench yesterday?",
                    "retrieval_strategy": "keyword",
                    "retrieval_params": {"keywords": ["bench"], "semantic_expansion": True},
                },
                {
                    "id": 2,
                    "question": "How much did I squat yesterday?",
                    "retrieval_strategy": "keyword",
                    "retrieval_params": {"keywords": ["squat"], "semantic_expansion": True},
                },
            ],
            "dependencies": [],
            "execution_strategy": "independent",
            "execution_order": [1, 2],
            "retrieval_instructions": [
                {"strategy": "keyword", "params": {"keywords": ["bench"]}, "sub_query_id": 1},
                {"strategy": "keyword", "params": {"keywords": ["squat"]}, "sub_query_id": 2},
            ],
            "gaps_status": {},
            "next_action": "retrieve",
            "reasoning": "Two independent queries about different exercises",
        }
        client = create_mock_llm_client(response)
        planner = PlannerAgent(client)

        result = await planner.plan(
            PlannerInput(
                query="How much did I bench and squat yesterday?",
                domain_context=create_sample_domain_context(),
            )
        )

        assert result.execution_strategy == DependencyType.INDEPENDENT
        assert len(result.sub_queries) == 2

    @pytest.mark.asyncio
    async def test_multi_part_dependent(self) -> None:
        """Multi-part query with causal chain returns DEPENDENT (AC: #2)."""
        response: dict[str, Any] = {
            "original_query": "Why was bench heavy and how to fix it?",
            "query_type": "insight",
            "sub_queries": [
                {
                    "id": 1,
                    "question": "Why was bench heavy?",
                    "retrieval_strategy": "topical",
                    "retrieval_params": {"topics": ["bench press", "difficulty"]},
                },
                {
                    "id": 2,
                    "question": "How to fix it?",
                    "retrieval_strategy": "topical",
                    "retrieval_params": {"topics": ["improvement", "technique"]},
                },
            ],
            "dependencies": [{"from": 1, "to": 2, "reason": "Need to understand why before fixing"}],
            "execution_strategy": "dependent",
            "execution_order": [1, 2],
            "retrieval_instructions": [
                {"strategy": "topical", "params": {}, "sub_query_id": 1},
                {"strategy": "topical", "params": {}, "sub_query_id": 2},
            ],
            "gaps_status": {},
            "next_action": "retrieve",
            "reasoning": "Sequential queries - need to understand cause before solution",
        }
        client = create_mock_llm_client(response)
        planner = PlannerAgent(client)

        result = await planner.plan(
            PlannerInput(
                query="Why was bench heavy and how to fix it?",
                domain_context=create_sample_domain_context(),
            )
        )

        assert result.execution_strategy == DependencyType.DEPENDENT
        assert len(result.dependencies) == 1
        assert result.dependencies[0]["from"] == 1
        assert result.dependencies[0]["to"] == 2


# =============================================================================
# Test Retrieval Strategies (Task 4)
# =============================================================================


class TestPlannerStrategies:
    """Tests for retrieval strategy generation (AC: #3)."""

    @pytest.mark.asyncio
    async def test_date_range_strategy(self) -> None:
        """Query with time period gets DATE_RANGE strategy (AC: #3)."""
        response: dict[str, Any] = {
            "original_query": "What did I eat last week?",
            "query_type": "simple",
            "sub_queries": [
                {
                    "id": 1,
                    "question": "What did I eat last week?",
                    "retrieval_strategy": "date_range",
                    "retrieval_params": {"start_date": "2024-01-01", "end_date": "2024-01-07"},
                }
            ],
            "dependencies": [],
            "execution_strategy": "coupled",
            "execution_order": [1],
            "retrieval_instructions": [
                {
                    "strategy": "date_range",
                    "params": {"start_date": "2024-01-01", "end_date": "2024-01-07"},
                    "sub_query_id": 1,
                }
            ],
            "gaps_status": {},
            "next_action": "retrieve",
            "reasoning": "Time-based query needs date range retrieval",
        }
        client = create_mock_llm_client(response)
        planner = PlannerAgent(client)

        result = await planner.plan(
            PlannerInput(
                query="What did I eat last week?",
                domain_context=create_sample_domain_context(),
            )
        )

        assert result.sub_queries[0].retrieval_strategy == "date_range"
        assert "start_date" in result.sub_queries[0].retrieval_params

    @pytest.mark.asyncio
    async def test_keyword_strategy(self) -> None:
        """Query with specific items gets KEYWORD strategy (AC: #3)."""
        response: dict[str, Any] = {
            "original_query": "Show me bench press workouts",
            "query_type": "simple",
            "sub_queries": [
                {
                    "id": 1,
                    "question": "Show me bench press workouts",
                    "retrieval_strategy": "keyword",
                    "retrieval_params": {"keywords": ["bench", "press"], "semantic_expansion": True},
                }
            ],
            "dependencies": [],
            "execution_strategy": "coupled",
            "execution_order": [1],
            "retrieval_instructions": [
                {
                    "strategy": "keyword",
                    "params": {"keywords": ["bench", "press"], "semantic_expansion": True},
                    "sub_query_id": 1,
                }
            ],
            "gaps_status": {},
            "next_action": "retrieve",
            "reasoning": "Specific activity query needs keyword retrieval",
        }
        client = create_mock_llm_client(response)
        planner = PlannerAgent(client)

        result = await planner.plan(
            PlannerInput(
                query="Show me bench press workouts",
                domain_context=create_sample_domain_context(),
            )
        )

        assert result.sub_queries[0].retrieval_strategy == "keyword"
        assert "keywords" in result.sub_queries[0].retrieval_params

    @pytest.mark.asyncio
    async def test_topical_strategy(self) -> None:
        """Query about patterns gets TOPICAL strategy (AC: #3)."""
        response: dict[str, Any] = {
            "original_query": "How is my progress?",
            "query_type": "insight",
            "sub_queries": [
                {
                    "id": 1,
                    "question": "How is my progress?",
                    "retrieval_strategy": "topical",
                    "retrieval_params": {"topics": ["progress", "trend"], "related_terms": ["improvement"]},
                }
            ],
            "dependencies": [],
            "execution_strategy": "coupled",
            "execution_order": [1],
            "retrieval_instructions": [
                {
                    "strategy": "topical",
                    "params": {"topics": ["progress", "trend"]},
                    "sub_query_id": 1,
                }
            ],
            "gaps_status": {},
            "next_action": "retrieve",
            "reasoning": "Progress query needs topical retrieval",
        }
        client = create_mock_llm_client(response)
        planner = PlannerAgent(client)

        result = await planner.plan(
            PlannerInput(
                query="How is my progress?",
                domain_context=create_sample_domain_context(),
            )
        )

        assert result.sub_queries[0].retrieval_strategy == "topical"
        assert "topics" in result.sub_queries[0].retrieval_params


# =============================================================================
# Test Domain Expansion (Task 5)
# =============================================================================


class TestPlannerDomainExpansion:
    """Tests for domain expansion detection (AC: #4)."""

    @pytest.mark.asyncio
    async def test_outside_expertise_triggers_expansion(self) -> None:
        """Gap with outside_current_expertise triggers domain expansion (AC: #4)."""
        response: dict[str, Any] = {
            "original_query": "How did my sleep affect my workout?",
            "query_type": "insight",
            "sub_queries": [
                {
                    "id": 1,
                    "question": "How did my sleep affect my workout?",
                    "retrieval_strategy": "topical",
                    "retrieval_params": {"topics": ["sleep", "workout"]},
                }
            ],
            "dependencies": [],
            "execution_strategy": "coupled",
            "execution_order": [1],
            "retrieval_instructions": [],
            "gaps_status": {"sleep_data": {"searched": False, "found": False}},
            "domain_expansion_request": ["sleep"],
            "expansion_reasoning": "Sleep data required but sleep domain not loaded",
            "next_action": "expand_domain",
            "reasoning": "Need sleep domain for this query",
        }
        client = create_mock_llm_client(response)
        planner = PlannerAgent(client)

        gap = Gap(
            description="Missing sleep data",
            gap_type=GapType.CONTEXTUAL,
            severity="critical",
            outside_current_expertise=True,
            suspected_domain="sleep",
        )

        result = await planner.plan(
            PlannerInput(
                query="How did my sleep affect my workout?",
                domain_context=create_sample_domain_context(),
                gaps_from_analyzer=[gap],
            )
        )

        assert result.domain_expansion_request == ["sleep"]
        assert result.expansion_reasoning is not None
        assert result.next_action == "expand_domain"

    @pytest.mark.asyncio
    async def test_subjective_gap_triggers_clarify(self) -> None:
        """Gap with SUBJECTIVE type triggers clarify (AC: #6)."""
        response: dict[str, Any] = {
            "original_query": "Am I feeling tired?",
            "query_type": "insight",
            "sub_queries": [
                {
                    "id": 1,
                    "question": "Am I feeling tired?",
                    "retrieval_strategy": "topical",
                    "retrieval_params": {"topics": ["fatigue"]},
                }
            ],
            "dependencies": [],
            "execution_strategy": "coupled",
            "execution_order": [1],
            "retrieval_instructions": [],
            "gaps_status": {},
            "clarify_questions": ["How are you feeling right now?"],
            "next_action": "clarify",
            "reasoning": "Only user knows current state - need clarification",
        }
        client = create_mock_llm_client(response)
        planner = PlannerAgent(client)

        gap = Gap(
            description="Current energy level",
            gap_type=GapType.SUBJECTIVE,
            severity="critical",
        )

        result = await planner.plan(
            PlannerInput(
                query="Am I feeling tired?",
                domain_context=create_sample_domain_context(),
                gaps_from_analyzer=[gap],
            )
        )

        assert result.clarify_questions is not None
        assert len(result.clarify_questions) > 0
        assert result.next_action == "clarify"

    def test_should_expand_domain_helper(self) -> None:
        """should_expand_domain returns True for outside_expertise gaps."""
        client = create_mock_llm_client({})
        planner = PlannerAgent(client)

        gaps_with_expansion = [
            Gap(
                description="Need sleep data",
                gap_type=GapType.CONTEXTUAL,
                severity="critical",
                outside_current_expertise=True,
            )
        ]
        assert planner.should_expand_domain(gaps_with_expansion) is True

        gaps_without_expansion = [
            Gap(
                description="Need more data",
                gap_type=GapType.TEMPORAL,
                severity="critical",
                outside_current_expertise=False,
            )
        ]
        assert planner.should_expand_domain(gaps_without_expansion) is False

    def test_should_clarify_helper(self) -> None:
        """should_clarify returns True for SUBJECTIVE/CLARIFICATION gaps."""
        client = create_mock_llm_client({})
        planner = PlannerAgent(client)

        subjective_gaps = [
            Gap(
                description="Current feeling",
                gap_type=GapType.SUBJECTIVE,
                severity="critical",
            )
        ]
        assert planner.should_clarify(subjective_gaps) is True

        clarification_gaps = [
            Gap(
                description="Ambiguous query",
                gap_type=GapType.CLARIFICATION,
                severity="critical",
            )
        ]
        assert planner.should_clarify(clarification_gaps) is True

        temporal_gaps = [
            Gap(
                description="Need different time range",
                gap_type=GapType.TEMPORAL,
                severity="critical",
            )
        ]
        assert planner.should_clarify(temporal_gaps) is False

    def test_determine_next_action_helper(self) -> None:
        """determine_next_action returns correct action based on gaps."""
        client = create_mock_llm_client({})
        planner = PlannerAgent(client)

        # Expansion takes priority
        expansion_gaps = [
            Gap(
                description="Need sleep",
                gap_type=GapType.CONTEXTUAL,
                severity="critical",
                outside_current_expertise=True,
            )
        ]
        assert planner.determine_next_action(expansion_gaps, True) == "expand_domain"

        # Clarify when subjective
        clarify_gaps = [
            Gap(
                description="Current feeling",
                gap_type=GapType.SUBJECTIVE,
                severity="critical",
            )
        ]
        assert planner.determine_next_action(clarify_gaps, True) == "clarify"

        # Retrieve when no blocking gaps
        normal_gaps = [
            Gap(
                description="Need more data",
                gap_type=GapType.TEMPORAL,
                severity="nice_to_have",
            )
        ]
        assert planner.determine_next_action(normal_gaps, True) == "retrieve"

        # Synthesize when no gaps and no retrieval
        assert planner.determine_next_action([], False) == "synthesize"

    def test_determine_next_action_expansion_beats_clarify(self) -> None:
        """Expansion takes priority over clarify when gap has both flags."""
        client = create_mock_llm_client({})
        planner = PlannerAgent(client)

        # Gap with BOTH outside_current_expertise=True AND gap_type=SUBJECTIVE
        # Expansion should win (solvable by adding domain)
        mixed_gap = [
            Gap(
                description="Need sleep mood data",
                gap_type=GapType.SUBJECTIVE,
                severity="critical",
                outside_current_expertise=True,
                suspected_domain="sleep",
            )
        ]
        # Expansion takes priority because it's a solvable gap
        assert planner.determine_next_action(mixed_gap, True) == "expand_domain"

    def test_determine_next_action_multiple_gaps_expansion_wins(self) -> None:
        """When multiple gaps present, expansion gap takes priority."""
        client = create_mock_llm_client({})
        planner = PlannerAgent(client)

        # Mix of gaps: one needs clarification, one needs expansion
        mixed_gaps = [
            Gap(
                description="Query is ambiguous",
                gap_type=GapType.CLARIFICATION,
                severity="critical",
            ),
            Gap(
                description="Need sleep data",
                gap_type=GapType.CONTEXTUAL,
                severity="critical",
                outside_current_expertise=True,
            ),
        ]
        # Expansion should take priority
        assert planner.determine_next_action(mixed_gaps, True) == "expand_domain"


# =============================================================================
# Test Re-planning on Feedback (Task 6)
# =============================================================================


class TestPlannerReplanning:
    """Tests for re-planning on feedback (AC: #5, #6)."""

    @pytest.mark.asyncio
    async def test_replanning_with_evaluation_feedback(self) -> None:
        """Planner adjusts plan based on evaluation feedback (AC: #5)."""
        response: dict[str, Any] = {
            "original_query": "How is my bench progress?",
            "query_type": "insight",
            "sub_queries": [
                {
                    "id": 1,
                    "question": "How is my bench progress?",
                    "retrieval_strategy": "date_range",
                    "retrieval_params": {"start_date": "2024-01-01", "end_date": "2024-03-01"},
                }
            ],
            "dependencies": [],
            "execution_strategy": "coupled",
            "execution_order": [1],
            "retrieval_instructions": [
                {
                    "strategy": "date_range",
                    "params": {"start_date": "2024-01-01", "end_date": "2024-03-01"},
                    "sub_query_id": 1,
                }
            ],
            "gaps_status": {},
            "next_action": "retrieve",
            "reasoning": "Expanded date range based on feedback that original range was too narrow",
        }
        client = create_mock_llm_client(response)
        planner = PlannerAgent(client)

        feedback = EvaluationFeedback(
            issue="Date range too narrow",
            suggestion="Expand to 3 months for trend analysis",
            affected_claim="Progress is steady",
        )

        result = await planner.plan(
            PlannerInput(
                query="How is my bench progress?",
                domain_context=create_sample_domain_context(),
                evaluation_feedback=feedback,
                retrieval_history=[
                    {
                        "strategy": "date_range",
                        "params": {"start_date": "2024-02-01", "end_date": "2024-02-28"},
                        "result_summary": "Found 5 entries",
                    }
                ],
            )
        )

        assert result.next_action == "retrieve"
        assert "feedback" in result.reasoning.lower() or "expanded" in result.reasoning.lower()

    @pytest.mark.asyncio
    async def test_replanning_with_analyzer_gaps(self) -> None:
        """Planner creates retrieval instructions for analyzer gaps (AC: #6)."""
        response: dict[str, Any] = {
            "original_query": "Why am I not making progress?",
            "query_type": "insight",
            "sub_queries": [
                {
                    "id": 1,
                    "question": "What has my training looked like?",
                    "retrieval_strategy": "date_range",
                    "retrieval_params": {"start_date": "2024-01-01", "end_date": "2024-02-01"},
                },
                {
                    "id": 2,
                    "question": "What has my nutrition been?",
                    "retrieval_strategy": "topical",
                    "retrieval_params": {"topics": ["nutrition", "diet"]},
                },
            ],
            "dependencies": [],
            "execution_strategy": "independent",
            "execution_order": [1, 2],
            "retrieval_instructions": [
                {"strategy": "date_range", "params": {}, "sub_query_id": 1},
                {"strategy": "topical", "params": {}, "sub_query_id": 2},
            ],
            "gaps_status": {
                "nutrition_data": {"searched": False, "found": False},
            },
            "next_action": "retrieve",
            "reasoning": "Added nutrition retrieval to address identified gap",
        }
        client = create_mock_llm_client(response)
        planner = PlannerAgent(client)

        gaps = [
            Gap(
                description="Missing nutrition data",
                gap_type=GapType.TOPICAL,
                severity="critical",
                searched=False,
                found=False,
            )
        ]

        result = await planner.plan(
            PlannerInput(
                query="Why am I not making progress?",
                domain_context=create_sample_domain_context(),
                gaps_from_analyzer=gaps,
            )
        )

        assert len(result.sub_queries) == 2
        assert result.next_action == "retrieve"

    @pytest.mark.asyncio
    async def test_clarify_questions_for_clarification_gaps(self) -> None:
        """Planner generates clarify_questions for CLARIFICATION gaps (AC: #6)."""
        response: dict[str, Any] = {
            "original_query": "How am I doing?",
            "query_type": "insight",
            "sub_queries": [
                {
                    "id": 1,
                    "question": "How am I doing?",
                    "retrieval_strategy": "topical",
                    "retrieval_params": {"topics": ["progress"]},
                }
            ],
            "dependencies": [],
            "execution_strategy": "coupled",
            "execution_order": [1],
            "retrieval_instructions": [],
            "gaps_status": {},
            "clarify_questions": [
                "Which area would you like to know about? (strength, nutrition, running)",
                "What timeframe are you interested in?",
            ],
            "next_action": "clarify",
            "reasoning": "Query is ambiguous - need to clarify scope",
        }
        client = create_mock_llm_client(response)
        planner = PlannerAgent(client)

        gaps = [
            Gap(
                description="Query is ambiguous",
                gap_type=GapType.CLARIFICATION,
                severity="critical",
            )
        ]

        result = await planner.plan(
            PlannerInput(
                query="How am I doing?",
                domain_context=create_sample_domain_context(),
                gaps_from_analyzer=gaps,
            )
        )

        assert result.clarify_questions is not None
        assert len(result.clarify_questions) >= 1
        assert result.next_action == "clarify"


# =============================================================================
# Test Input Validation (Task 9)
# =============================================================================


class TestPlannerInputValidation:
    """Tests for PlannerAgent input validation."""

    @pytest.mark.asyncio
    async def test_empty_query_raises_value_error(self) -> None:
        """Empty query raises ValueError."""
        response: dict[str, Any] = {
            "original_query": "",
            "query_type": "simple",
            "sub_queries": [],
            "dependencies": [],
            "execution_strategy": "coupled",
            "execution_order": [],
            "retrieval_instructions": [],
            "gaps_status": {},
            "next_action": "retrieve",
            "reasoning": "test",
        }
        client = create_mock_llm_client(response)
        planner = PlannerAgent(client)

        # Note: Pydantic will catch empty string first with min_length=1
        with pytest.raises(ValidationError):
            await planner.plan(
                PlannerInput(
                    query="",
                    domain_context=create_minimal_domain_context(),
                )
            )

    @pytest.mark.asyncio
    async def test_whitespace_only_query_raises_value_error(self) -> None:
        """Whitespace-only query raises ValueError in plan() method."""
        response: dict[str, Any] = {
            "original_query": "   ",
            "query_type": "simple",
            "sub_queries": [],
            "dependencies": [],
            "execution_strategy": "coupled",
            "execution_order": [],
            "retrieval_instructions": [],
            "gaps_status": {},
            "next_action": "retrieve",
            "reasoning": "test",
        }
        client = create_mock_llm_client(response)
        planner = PlannerAgent(client)

        # Whitespace-only passes Pydantic min_length but fails in plan()
        with pytest.raises(ValueError, match="empty or whitespace"):
            await planner.plan(
                PlannerInput(
                    query="   \n\t  ",
                    domain_context=create_minimal_domain_context(),
                )
            )

    @pytest.mark.asyncio
    async def test_valid_query_does_not_raise(self) -> None:
        """Valid query does not raise any errors."""
        response: dict[str, Any] = {
            "original_query": "What did I eat?",
            "query_type": "simple",
            "sub_queries": [
                {
                    "id": 1,
                    "question": "What did I eat?",
                    "retrieval_strategy": "topical",
                    "retrieval_params": {},
                }
            ],
            "dependencies": [],
            "execution_strategy": "coupled",
            "execution_order": [1],
            "retrieval_instructions": [],
            "gaps_status": {},
            "next_action": "retrieve",
            "reasoning": "Simple query",
        }
        client = create_mock_llm_client(response)
        planner = PlannerAgent(client)

        result = await planner.plan(
            PlannerInput(
                query="What did I eat?",
                domain_context=create_minimal_domain_context(),
            )
        )

        assert result.original_query == "What did I eat?"


# =============================================================================
# Test Prompt Building
# =============================================================================


class TestPlannerPrompt:
    """Tests for PlannerAgent prompt building."""

    def test_prompt_includes_domain_context(self) -> None:
        """Prompt includes domain context information."""
        client = create_mock_llm_client({})
        planner = PlannerAgent(client)

        planner_input = PlannerInput(
            query="What did I eat?",
            domain_context=create_sample_domain_context(),
        )
        prompt = planner.build_prompt(planner_input)

        assert "strength" in prompt
        assert "nutrition" in prompt
        assert "bench press" in prompt  # vocabulary

    def test_prompt_includes_available_domains(self) -> None:
        """Prompt includes available domains for expansion."""
        client = create_mock_llm_client({})
        planner = PlannerAgent(client)

        planner_input = PlannerInput(
            query="What did I eat?",
            domain_context=create_sample_domain_context(),
        )
        prompt = planner.build_prompt(planner_input)

        assert "running" in prompt
        assert "sleep" in prompt

    def test_prompt_handles_empty_context(self) -> None:
        """Prompt handles empty domain context."""
        client = create_mock_llm_client({})
        planner = PlannerAgent(client)

        planner_input = PlannerInput(
            query="What did I eat?",
            domain_context=create_minimal_domain_context(),
        )
        prompt = planner.build_prompt(planner_input)

        assert "(No vocabulary defined)" in prompt
        assert "(No additional domains available)" in prompt

    def test_prompt_includes_gaps(self) -> None:
        """Prompt includes gaps from analyzer."""
        client = create_mock_llm_client({})
        planner = PlannerAgent(client)

        gap = Gap(
            description="Missing yesterday's data",
            gap_type=GapType.TEMPORAL,
            severity="critical",
        )
        planner_input = PlannerInput(
            query="What did I eat?",
            domain_context=create_minimal_domain_context(),
            gaps_from_analyzer=[gap],
        )
        prompt = planner.build_prompt(planner_input)

        assert "Missing yesterday's data" in prompt
        assert "temporal" in prompt

    def test_prompt_includes_evaluation_feedback(self) -> None:
        """Prompt includes evaluation feedback."""
        client = create_mock_llm_client({})
        planner = PlannerAgent(client)

        feedback = EvaluationFeedback(
            issue="Date range too narrow",
            suggestion="Expand range",
        )
        planner_input = PlannerInput(
            query="What did I eat?",
            domain_context=create_minimal_domain_context(),
            evaluation_feedback=feedback,
        )
        prompt = planner.build_prompt(planner_input)

        assert "Date range too narrow" in prompt
        assert "Expand range" in prompt

    def test_prompt_includes_retrieval_history(self) -> None:
        """Prompt includes retrieval history."""
        client = create_mock_llm_client({})
        planner = PlannerAgent(client)

        planner_input = PlannerInput(
            query="What did I eat?",
            domain_context=create_minimal_domain_context(),
            retrieval_history=[
                {
                    "strategy": "date_range",
                    "params": {"start_date": "2024-01-01"},
                    "result_summary": "Found 3 entries",
                }
            ],
        )
        prompt = planner.build_prompt(planner_input)

        assert "date_range" in prompt
        assert "Found 3 entries" in prompt

    def test_prompt_includes_query_type_hint(self) -> None:
        """Prompt includes pre-classified query type."""
        client = create_mock_llm_client({})
        planner = PlannerAgent(client)

        planner_input = PlannerInput(
            query="What did I eat?",
            query_type=QueryType.SIMPLE,
            domain_context=create_minimal_domain_context(),
        )
        prompt = planner.build_prompt(planner_input)

        assert "Pre-classified query type: simple" in prompt


# =============================================================================
# Integration Tests (Task 10)
# =============================================================================


class TestPlannerIntegration:
    """Integration tests with real Ollama (AC: #8).

    Run with: pytest --use-real-ollama -k TestPlannerIntegration
    Or via: make test-ollama

    Uses llm-config.yaml from project root to match production config.
    """

    @pytest.mark.asyncio
    async def test_real_simple_query_planning(self, use_real_ollama: bool, integration_llm_config_path: Path) -> None:
        """Test simple query planning with real Ollama."""
        if not use_real_ollama:
            pytest.skip("Requires --use-real-ollama flag")

        config = load_llm_config(integration_llm_config_path)
        real_llm_client = LLMClient(config)
        planner = PlannerAgent(real_llm_client)

        result = await planner.plan(
            PlannerInput(
                query="What did I eat yesterday?",
                domain_context=create_sample_domain_context(),
            )
        )

        # Simple query should have at least one sub-query
        assert len(result.sub_queries) >= 1
        # Execution strategy should be valid (LLM may interpret differently)
        assert result.execution_strategy in [
            DependencyType.COUPLED,
            DependencyType.INDEPENDENT,
            DependencyType.DEPENDENT,
        ]
        assert result.next_action in ["retrieve", "synthesize", "clarify", "expand_domain"]

    @pytest.mark.asyncio
    async def test_real_multi_part_query_classification(
        self, use_real_ollama: bool, integration_llm_config_path: Path
    ) -> None:
        """Test multi-part query classification with real Ollama."""
        if not use_real_ollama:
            pytest.skip("Requires --use-real-ollama flag")

        config = load_llm_config(integration_llm_config_path)
        real_llm_client = LLMClient(config)
        planner = PlannerAgent(real_llm_client)

        result = await planner.plan(
            PlannerInput(
                query="How much did I bench and squat yesterday?",
                domain_context=create_sample_domain_context(),
            )
        )

        # Either decomposed into 2 or kept as coupled (both valid)
        assert len(result.sub_queries) >= 1
        assert result.execution_strategy in [
            DependencyType.INDEPENDENT,
            DependencyType.COUPLED,
        ]

    @pytest.mark.asyncio
    async def test_real_retrieval_strategy_generation(
        self, use_real_ollama: bool, integration_llm_config_path: Path
    ) -> None:
        """Test retrieval strategy generation with real Ollama."""
        if not use_real_ollama:
            pytest.skip("Requires --use-real-ollama flag")

        config = load_llm_config(integration_llm_config_path)
        real_llm_client = LLMClient(config)
        planner = PlannerAgent(real_llm_client)

        result = await planner.plan(
            PlannerInput(
                query="Show me my bench press workouts from last week",
                domain_context=create_sample_domain_context(),
            )
        )

        assert len(result.sub_queries) >= 1
        # Should use date_range or keyword strategy
        valid_strategies = ["date_range", "keyword", "topical"]
        assert result.sub_queries[0].retrieval_strategy in valid_strategies
