"""Unit tests for pairwise LLM-as-judge evaluation.

These tests use mocked judge responses to test the evaluation logic
without requiring actual LLM API calls.
"""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from tests.eval.pairwise_judge import (
    PairwiseEvaluator,
    _build_judge_system_prompt,
    _build_judge_user_prompt,
    _calculate_weighted_score,
    _load_rubric,
    _parse_judge_response,
)
from tests.eval.schema import (
    CategoryMetrics,
    CriterionScore,
    EvaluationMetrics,
    EvaluationRun,
    JudgeResult,
    ModelParams,
    PairwiseResult,
    Rubric,
    TestCase,
)


@pytest.fixture
def sample_test_case() -> TestCase:
    """Create a sample test case for testing."""
    return TestCase(
        id="test-case-1",
        category="simple",
        query="What was my max bench press last week?",
        context_entries=["2019-01-28"],
        rubric_criteria=["accuracy", "completeness"],
        evaluation_hints={
            "should_mention": ["bench press", "weight"],
            "should_not": ["hallucinated data"],
        },
    )


@pytest.fixture
def sample_rubric() -> Rubric:
    """Load the actual rubric for testing."""
    return _load_rubric()


@pytest.fixture
def mock_judge_response_a_wins() -> dict:
    """Mock judge response where A wins."""
    return {
        "reasoning": "Response A is more accurate and complete.",
        "criterion_scores_a": [
            {"criterion": "accuracy", "score": 5, "reasoning": "Fully accurate"},
            {"criterion": "completeness", "score": 4, "reasoning": "Complete answer"},
        ],
        "criterion_scores_b": [
            {"criterion": "accuracy", "score": 3, "reasoning": "Some errors"},
            {"criterion": "completeness", "score": 3, "reasoning": "Missing details"},
        ],
        "aggregate_score_a": 4.5,
        "aggregate_score_b": 3.0,
        "winner": "A",
    }


@pytest.fixture
def mock_judge_response_b_wins() -> dict:
    """Mock judge response where B wins."""
    return {
        "reasoning": "Response B is more accurate.",
        "criterion_scores_a": [
            {"criterion": "accuracy", "score": 3, "reasoning": "Some errors"},
            {"criterion": "completeness", "score": 3, "reasoning": "Missing details"},
        ],
        "criterion_scores_b": [
            {"criterion": "accuracy", "score": 5, "reasoning": "Fully accurate"},
            {"criterion": "completeness", "score": 4, "reasoning": "Complete answer"},
        ],
        "aggregate_score_a": 3.0,
        "aggregate_score_b": 4.5,
        "winner": "B",
    }


@pytest.fixture
def mock_judge_response_tie() -> dict:
    """Mock judge response with tie."""
    return {
        "reasoning": "Both responses are equally good.",
        "criterion_scores_a": [
            {"criterion": "accuracy", "score": 4, "reasoning": "Accurate"},
            {"criterion": "completeness", "score": 4, "reasoning": "Complete"},
        ],
        "criterion_scores_b": [
            {"criterion": "accuracy", "score": 4, "reasoning": "Accurate"},
            {"criterion": "completeness", "score": 4, "reasoning": "Complete"},
        ],
        "aggregate_score_a": 4.0,
        "aggregate_score_b": 4.0,
        "winner": "Tie",
    }


class TestParseJudgeResponse:
    """Tests for JSON parsing from judge responses."""

    def test_parse_direct_json(self) -> None:
        """Test parsing direct JSON response."""
        raw = '{"winner": "A", "reasoning": "test"}'
        result = _parse_judge_response(raw)
        assert result is not None
        assert result["winner"] == "A"

    def test_parse_json_in_code_block(self) -> None:
        """Test parsing JSON in markdown code block."""
        raw = """Here's my evaluation:
```json
{"winner": "B", "reasoning": "test"}
```
"""
        result = _parse_judge_response(raw)
        assert result is not None
        assert result["winner"] == "B"

    def test_parse_json_in_code_block_no_lang(self) -> None:
        """Test parsing JSON in code block without language tag."""
        raw = """
```
{"winner": "Tie", "reasoning": "test"}
```
"""
        result = _parse_judge_response(raw)
        assert result is not None
        assert result["winner"] == "Tie"

    def test_parse_embedded_json(self) -> None:
        """Test parsing JSON embedded in text."""
        raw = 'Some text before {"winner": "A", "reasoning": "test"} and after'
        result = _parse_judge_response(raw)
        assert result is not None
        assert result["winner"] == "A"

    def test_parse_invalid_json_returns_none(self) -> None:
        """Test that invalid JSON returns None."""
        raw = "This is not JSON at all"
        result = _parse_judge_response(raw)
        assert result is None


class TestCalculateWeightedScore:
    """Tests for weighted score calculation."""

    def test_calculate_with_weights(self, sample_rubric: Rubric) -> None:
        """Test weighted score calculation."""
        scores = [
            CriterionScore(criterion="accuracy", score=5, reasoning="test"),
            CriterionScore(criterion="completeness", score=3, reasoning="test"),
        ]
        result = _calculate_weighted_score(scores, sample_rubric)

        # accuracy weight=1.5, completeness weight=1.0
        # (5*1.5 + 3*1.0) / (1.5 + 1.0) = 10.5 / 2.5 = 4.2
        assert result == pytest.approx(4.2, rel=0.01)

    def test_calculate_empty_scores(self, sample_rubric: Rubric) -> None:
        """Test empty scores returns 0."""
        result = _calculate_weighted_score([], sample_rubric)
        assert result == 0.0


class TestBuildPrompts:
    """Tests for prompt building functions."""

    def test_system_prompt_contains_criteria(self, sample_rubric: Rubric) -> None:
        """Test system prompt includes all criteria."""
        prompt = _build_judge_system_prompt(sample_rubric)

        assert "ACCURACY" in prompt
        assert "COMPLETENESS" in prompt
        assert "CONCISENESS" in prompt
        assert "DOMAIN_EXPERTISE" in prompt
        assert "weight:" in prompt

    def test_user_prompt_contains_query(self, sample_test_case: TestCase, sample_rubric: Rubric) -> None:
        """Test user prompt includes the query."""
        prompt = _build_judge_user_prompt(
            sample_test_case,
            "Response A text",
            "Response B text",
            sample_rubric,
        )

        assert sample_test_case.query in prompt
        assert "Response A text" in prompt
        assert "Response B text" in prompt
        assert "simple" in prompt.lower()

    def test_user_prompt_includes_hints(self, sample_test_case: TestCase, sample_rubric: Rubric) -> None:
        """Test user prompt includes evaluation hints."""
        prompt = _build_judge_user_prompt(
            sample_test_case,
            "Response A",
            "Response B",
            sample_rubric,
        )

        assert "bench press" in prompt
        assert "hallucinated data" in prompt


class TestPairwiseEvaluator:
    """Tests for the PairwiseEvaluator class."""

    @pytest.mark.asyncio
    async def test_evaluate_pair_success(
        self,
        sample_test_case: TestCase,
        mock_judge_response_a_wins: dict,
    ) -> None:
        """Test successful pair evaluation."""
        evaluator = PairwiseEvaluator(judge_model="test-model")

        with patch("litellm.acompletion", new_callable=AsyncMock) as mock_llm:
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = json.dumps(mock_judge_response_a_wins)
            mock_llm.return_value = mock_response

            result = await evaluator.evaluate_pair(
                sample_test_case,
                "Quilto response",
                "Claude response",
            )

        assert result is not None
        assert result.winner == "A"
        assert len(result.criterion_scores_a) == 2
        assert len(result.criterion_scores_b) == 2

    @pytest.mark.asyncio
    async def test_evaluate_pair_retry_on_parse_failure(
        self,
        sample_test_case: TestCase,
        mock_judge_response_a_wins: dict,
    ) -> None:
        """Test retry on JSON parse failure."""
        evaluator = PairwiseEvaluator(judge_model="test-model")

        with patch("litellm.acompletion", new_callable=AsyncMock) as mock_llm:
            # First call returns invalid JSON, second returns valid
            mock_response_bad = MagicMock()
            mock_response_bad.choices = [MagicMock()]
            mock_response_bad.choices[0].message.content = "Invalid JSON"

            mock_response_good = MagicMock()
            mock_response_good.choices = [MagicMock()]
            mock_response_good.choices[0].message.content = json.dumps(mock_judge_response_a_wins)

            mock_llm.side_effect = [mock_response_bad, mock_response_good]

            result = await evaluator.evaluate_pair(
                sample_test_case,
                "Quilto response",
                "Claude response",
            )

        assert result is not None
        assert mock_llm.call_count == 2

    @pytest.mark.asyncio
    async def test_evaluate_with_swap_quilto_consistent_win(
        self,
        sample_test_case: TestCase,
        mock_judge_response_a_wins: dict,
        mock_judge_response_b_wins: dict,
    ) -> None:
        """Test consistent Quilto win in position swap."""
        evaluator = PairwiseEvaluator(judge_model="test-model")

        with patch("litellm.acompletion", new_callable=AsyncMock) as mock_llm:
            # First call: Quilto=A wins, Second call: Quilto=B wins
            mock_response_a = MagicMock()
            mock_response_a.choices = [MagicMock()]
            mock_response_a.choices[0].message.content = json.dumps(mock_judge_response_a_wins)

            mock_response_b = MagicMock()
            mock_response_b.choices = [MagicMock()]
            mock_response_b.choices[0].message.content = json.dumps(mock_judge_response_b_wins)

            mock_llm.side_effect = [mock_response_a, mock_response_b]

            with patch("random.choice", return_value=True):  # Quilto first
                result = await evaluator.evaluate_with_swap(
                    sample_test_case,
                    "Quilto response",
                    "Claude response",
                )

        assert result.final_winner == "quilto"
        assert result.is_consistent is True

    @pytest.mark.asyncio
    async def test_evaluate_with_swap_inconsistent(
        self,
        sample_test_case: TestCase,
        mock_judge_response_a_wins: dict,
    ) -> None:
        """Test inconsistent results lead to tie."""
        evaluator = PairwiseEvaluator(judge_model="test-model")

        with patch("litellm.acompletion", new_callable=AsyncMock) as mock_llm:
            # Both calls say A wins (inconsistent: Quilto=A wins, then Claude=A wins)
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = json.dumps(mock_judge_response_a_wins)

            mock_llm.return_value = mock_response

            with patch("random.choice", return_value=True):  # Quilto first
                result = await evaluator.evaluate_with_swap(
                    sample_test_case,
                    "Quilto response",
                    "Claude response",
                )

        # Both say A wins: first Quilto=A wins, second Claude=A wins
        # This is inconsistent (one says Quilto, one says Claude)
        assert result.final_winner == "tie"
        assert result.is_consistent is False

    @pytest.mark.asyncio
    async def test_evaluate_with_swap_both_ties(
        self,
        sample_test_case: TestCase,
        mock_judge_response_tie: dict,
    ) -> None:
        """Test both orderings as tie results in consistent tie."""
        evaluator = PairwiseEvaluator(judge_model="test-model")

        with patch("litellm.acompletion", new_callable=AsyncMock) as mock_llm:
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = json.dumps(mock_judge_response_tie)

            mock_llm.return_value = mock_response

            result = await evaluator.evaluate_with_swap(
                sample_test_case,
                "Quilto response",
                "Claude response",
            )

        assert result.final_winner == "tie"
        assert result.is_consistent is True


class TestSchemas:
    """Tests for Pydantic schemas."""

    def test_criterion_score_validation(self) -> None:
        """Test CriterionScore validates score range."""
        # Valid score
        score = CriterionScore(criterion="accuracy", score=5, reasoning="test")
        assert score.score == 5

        # Invalid score (too high)
        with pytest.raises(ValueError):
            CriterionScore(criterion="accuracy", score=6, reasoning="test")

        # Invalid score (too low)
        with pytest.raises(ValueError):
            CriterionScore(criterion="accuracy", score=0, reasoning="test")

    def test_judge_result_schema(self) -> None:
        """Test JudgeResult schema."""
        result = JudgeResult(
            winner="A",
            criterion_scores_a=[
                CriterionScore(criterion="accuracy", score=4, reasoning="test"),
            ],
            criterion_scores_b=[
                CriterionScore(criterion="accuracy", score=3, reasoning="test"),
            ],
            aggregate_score_a=4.0,
            aggregate_score_b=3.0,
            reasoning="A is better",
            raw_output="{}",
        )
        assert result.winner == "A"

    def test_pairwise_result_schema(self) -> None:
        """Test PairwiseResult schema."""
        result = PairwiseResult(
            test_case_id="test-1",
            quilto_response="response",
            claude_response="baseline",
            judgment_ab=None,
            judgment_ba=None,
            final_winner="tie",
            is_consistent=True,
            quilto_aggregate=3.5,
            claude_aggregate=3.5,
        )
        assert result.final_winner == "tie"

    def test_evaluation_metrics_schema(self) -> None:
        """Test EvaluationMetrics schema."""
        metrics = EvaluationMetrics(
            total_cases=10,
            quilto_wins=4,
            claude_wins=3,
            ties=2,
            errors=1,
            consistent_count=8,
            inconsistent_count=1,
            win_rate=0.44,
            tie_rate=0.22,
            inconsistency_rate=0.1,
            per_category={"simple": CategoryMetrics(quilto_wins=2, claude_wins=1, ties=1)},
        )
        assert metrics.win_rate == pytest.approx(0.44)

    def test_evaluation_run_schema(self) -> None:
        """Test EvaluationRun schema."""
        run = EvaluationRun(
            version="v2026-01-19",
            timestamp="2026-01-19T10:00:00Z",
            judge_model="gpt-4o-mini",
            judge_params=ModelParams(max_tokens=2000, temperature=0.0),
            results=[],
            metrics=EvaluationMetrics(
                total_cases=0,
                quilto_wins=0,
                claude_wins=0,
                ties=0,
                errors=0,
                consistent_count=0,
                inconsistent_count=0,
                win_rate=0.0,
                tie_rate=0.0,
                inconsistency_rate=0.0,
                per_category={},
            ),
        )
        assert run.version == "v2026-01-19"


class TestPairwiseComparisonMetric:
    """Tests for PairwiseComparisonMetric (DeepEval integration)."""

    def test_metric_import_when_deepeval_available(self) -> None:
        """Test that metric can be imported when deepeval is available."""
        try:
            from tests.eval.metrics import DEEPEVAL_AVAILABLE, PairwiseComparisonMetric

            if DEEPEVAL_AVAILABLE:
                metric = PairwiseComparisonMetric(threshold=0.4)
                assert metric.threshold == 0.4
                assert metric.score == 0.0
                assert metric.__name__ == "PairwiseComparisonMetric"
            else:
                # deepeval not installed, skip test
                pytest.skip("deepeval not installed")
        except ImportError:
            pytest.skip("deepeval not installed")

    def test_metric_is_successful(self) -> None:
        """Test is_successful based on threshold."""
        try:
            from tests.eval.metrics import DEEPEVAL_AVAILABLE, PairwiseComparisonMetric

            if not DEEPEVAL_AVAILABLE:
                pytest.skip("deepeval not installed")

            metric = PairwiseComparisonMetric(threshold=0.5)
            metric.score = 0.6
            assert metric.is_successful() is True

            metric.score = 0.4
            assert metric.is_successful() is False
        except ImportError:
            pytest.skip("deepeval not installed")
