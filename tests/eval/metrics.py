"""DeepEval custom metrics for pairwise evaluation.

This module provides DeepEval-compatible custom metrics for evaluating
Quilto responses against Claude baselines using pairwise comparison.

Usage:
    from deepeval import evaluate
    from deepeval.test_case import LLMTestCase
    from tests.eval.metrics import PairwiseComparisonMetric

    metric = PairwiseComparisonMetric(threshold=0.4)
    test_case = LLMTestCase(
        input="What was my max bench press?",
        actual_output=quilto_response,
        expected_output=claude_baseline,
    )
    metric.measure(test_case)
    assert metric.is_successful()

Note:
    Requires `deepeval` package to be installed. If not available,
    PairwiseComparisonMetric will not be importable.
"""

import asyncio
import logging
from typing import Any

# Handle optional deepeval dependency
try:
    from deepeval.metrics import BaseMetric
    from deepeval.test_case import LLMTestCase

    DEEPEVAL_AVAILABLE = True
except ImportError:
    DEEPEVAL_AVAILABLE = False
    BaseMetric = object  # type: ignore[misc,assignment]
    LLMTestCase = Any  # type: ignore[misc,assignment]

from tests.eval.pairwise_judge import PairwiseEvaluator
from tests.eval.schema import TestCase

logger = logging.getLogger(__name__)


def _check_deepeval() -> None:
    """Raise ImportError if deepeval is not available."""
    if not DEEPEVAL_AVAILABLE:
        raise ImportError(
            "deepeval package is required for PairwiseComparisonMetric. Install with: pip install deepeval"
        )


class PairwiseComparisonMetric(BaseMetric):
    """Custom DeepEval metric for pairwise evaluation against Claude baseline.

    This metric compares Quilto's actual_output against Claude's expected_output
    using LLM-as-judge with position swap for unbiased evaluation.

    Scoring:
    - 1.0: Quilto wins consistently
    - 0.5: Tie (inconsistent orderings or equal quality)
    - 0.0: Claude wins consistently

    Attributes:
        threshold: Minimum score to pass (default 0.4 means Quilto shouldn't
            lose more than 60% of comparisons).
        score: The computed score after measure() is called.
        reason: Human-readable explanation of the score.
    """

    def __init__(
        self,
        threshold: float = 0.4,
        judge_model: str = "gpt-4o-mini",
    ) -> None:
        """Initialize the metric.

        Args:
            threshold: Minimum score to pass (0.0-1.0).
            judge_model: LiteLLM model ID for the judge.

        Raises:
            ImportError: If deepeval package is not installed.
        """
        _check_deepeval()
        self.threshold = threshold
        self.judge_model = judge_model
        self._evaluator = PairwiseEvaluator(judge_model=judge_model)
        self.score: float = 0.0
        self.reason: str = ""

    def measure(self, test_case: LLMTestCase) -> float:
        """Synchronous wrapper for async evaluation.

        This method performs the pairwise comparison and sets the score.

        Args:
            test_case: DeepEval test case with:
                - input: The query
                - actual_output: Quilto's response
                - expected_output: Claude's baseline response

        Returns:
            Score: 1.0 (Quilto wins), 0.5 (tie), 0.0 (Claude wins).
        """
        # Convert DeepEval test case to our TestCase format
        eval_test_case = self._convert_test_case(test_case)

        quilto_response = test_case.actual_output or ""
        claude_response = test_case.expected_output or ""

        async def _run() -> tuple[float, str]:
            result = await self._evaluator.evaluate_with_swap(
                test_case=eval_test_case,
                quilto_response=quilto_response,
                claude_response=claude_response,
            )

            q_agg = result.quilto_aggregate
            c_agg = result.claude_aggregate
            q_str = f"{q_agg:.2f}" if q_agg is not None else "N/A"
            c_str = f"{c_agg:.2f}" if c_agg is not None else "N/A"
            if result.final_winner == "quilto":
                return 1.0, f"Quilto wins consistently (Q:{q_str} vs C:{c_str})"
            elif result.final_winner == "tie":
                consistency = "consistent" if result.is_consistent else "inconsistent"
                return 0.5, f"Tie ({consistency}) (Q:{q_str} vs C:{c_str})"
            elif result.final_winner == "error":
                return 0.0, f"Evaluation error: {result.error_message}"
            else:
                return 0.0, f"Claude wins consistently (Q:{q_str} vs C:{c_str})"

        # Run async in sync context
        self.score, self.reason = asyncio.run(_run())
        return self.score

    async def a_measure(self, test_case: LLMTestCase, _show_indicator: bool = True) -> float:
        """Async version of measure().

        Args:
            test_case: DeepEval test case.
            _show_indicator: Ignored (required by DeepEval interface).

        Returns:
            Score: 1.0 (Quilto wins), 0.5 (tie), 0.0 (Claude wins).
        """
        eval_test_case = self._convert_test_case(test_case)

        quilto_response = test_case.actual_output or ""
        claude_response = test_case.expected_output or ""

        result = await self._evaluator.evaluate_with_swap(
            test_case=eval_test_case,
            quilto_response=quilto_response,
            claude_response=claude_response,
        )

        q_agg = result.quilto_aggregate
        c_agg = result.claude_aggregate
        q_str = f"{q_agg:.2f}" if q_agg is not None else "N/A"
        c_str = f"{c_agg:.2f}" if c_agg is not None else "N/A"
        if result.final_winner == "quilto":
            self.score = 1.0
            self.reason = f"Quilto wins consistently (Q:{q_str} vs C:{c_str})"
        elif result.final_winner == "tie":
            self.score = 0.5
            consistency = "consistent" if result.is_consistent else "inconsistent"
            self.reason = f"Tie ({consistency}) (Q:{q_str} vs C:{c_str})"
        elif result.final_winner == "error":
            self.score = 0.0
            self.reason = f"Evaluation error: {result.error_message}"
        else:
            self.score = 0.0
            self.reason = f"Claude wins consistently (Q:{q_str} vs C:{c_str})"

        return self.score

    def is_successful(self) -> bool:
        """Check if the metric passes the threshold.

        Returns:
            True if score >= threshold.
        """
        return self.score >= self.threshold

    @property
    def __name__(self) -> str:
        """Return metric name for DeepEval reporting."""
        return "PairwiseComparisonMetric"

    def _convert_test_case(self, test_case: LLMTestCase) -> TestCase:
        """Convert DeepEval test case to our TestCase format.

        This creates a minimal TestCase with default values for fields
        not available in the DeepEval test case.

        Args:
            test_case: DeepEval test case.

        Returns:
            Our TestCase format.
        """
        # Try to extract category from additional_metadata
        additional_metadata: dict[str, Any] = getattr(test_case, "additional_metadata", {}) or {}
        category = additional_metadata.get("category", "simple")
        test_case_id = additional_metadata.get("id", "deepeval-test")

        # Use context dates from additional_metadata or default
        context_entries = additional_metadata.get("context_entries", ["2019-01-28"])

        # Extract evaluation hints if provided
        should_mention = additional_metadata.get("should_mention", ["relevant information"])
        should_not = additional_metadata.get("should_not", ["hallucinated data"])

        return TestCase(
            id=test_case_id,
            category=category,
            query=test_case.input or "",
            context_entries=context_entries,
            rubric_criteria=["accuracy", "completeness"],
            evaluation_hints={
                "should_mention": should_mention,
                "should_not": should_not,
            },
        )
