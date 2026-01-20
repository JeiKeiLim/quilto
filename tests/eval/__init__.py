"""E2E Evaluation Dataset package.

This package provides infrastructure for evaluating Quilto agent quality
against Claude baseline responses using pairwise LLM-as-judge methodology.

Main Components:
    - Schema classes for test cases and evaluation results
    - PairwiseEvaluator for running LLM-as-judge evaluations
    - PairwiseComparisonMetric for DeepEval integration (requires deepeval)
    - CLI runner for batch evaluations

Example:
    from tests.eval import PairwiseEvaluator, TestCase

    evaluator = PairwiseEvaluator(judge_model="gpt-4o-mini")
    result = await evaluator.evaluate_with_swap(test_case, quilto_response, claude_response)
"""

from tests.eval.pairwise_judge import (
    PairwiseEvaluator,
    clear_quilto_cache,
    generate_quilto_response,
    generate_quilto_response_cached,
)
from tests.eval.schema import (
    BaselineResponse,
    CategoryMetrics,
    CriterionScore,
    EvaluationMetrics,
    EvaluationRun,
    GoldenDataset,
    JudgeResult,
    ModelParams,
    PairwiseResult,
    Rubric,
    TestCase,
)

# Optional deepeval integration
# PairwiseComparisonMetric requires deepeval package (pip install deepeval)
# The dynamic _DEEPEVAL_EXPORTS pattern allows graceful handling when deepeval
# is not installed, while still exporting the metric when it is available.
try:
    from tests.eval.metrics import PairwiseComparisonMetric  # noqa: F401

    _DEEPEVAL_EXPORTS = ["PairwiseComparisonMetric"]
except ImportError:
    _DEEPEVAL_EXPORTS = []

__all__ = [
    # Schema classes
    "BaselineResponse",
    "CategoryMetrics",
    "CriterionScore",
    "EvaluationMetrics",
    "EvaluationRun",
    "GoldenDataset",
    "JudgeResult",
    "ModelParams",
    "PairwiseResult",
    "Rubric",
    "TestCase",
    # Evaluator classes
    "PairwiseEvaluator",
    # Helper functions
    "generate_quilto_response",
    "generate_quilto_response_cached",
    "clear_quilto_cache",
    # Optional (requires deepeval)
    *_DEEPEVAL_EXPORTS,
]
