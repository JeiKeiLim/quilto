"""Pytest integration for LLM-as-Judge evaluation.

This module provides parametrized pytest tests for evaluating Quilto responses
against Claude baselines using pairwise comparison with position swap.

Usage:
    pytest tests/eval/test_llm_evaluation.py -v -m llm_eval
    LLM_EVAL_THRESHOLD=0.4 pytest tests/eval/test_llm_evaluation.py
    pytest tests/eval/test_llm_evaluation.py --use-cache
    pytest tests/eval/test_llm_evaluation.py --no-cache
"""

from pathlib import Path
from typing import Any

import pytest

from tests.eval.conftest import (
    load_cached_result,
    save_cached_result,
    update_session_cost,
)
from tests.eval.generate_baseline import load_golden_dataset
from tests.eval.metrics import DEEPEVAL_AVAILABLE
from tests.eval.pairwise_judge import generate_quilto_response_cached
from tests.eval.run_evaluation import load_baseline_response
from tests.eval.schema import GoldenDataset, TestCase

# Dataset version - update when new golden dataset is released
DATASET_VERSION = "v2026-01-19"

# Skip entire module if deepeval not installed
pytestmark = [
    pytest.mark.llm_eval,
    pytest.mark.slow,
    pytest.mark.skipif(not DEEPEVAL_AVAILABLE, reason="deepeval not installed"),
]


def get_test_case_ids() -> list[str]:
    """Get all test case IDs for parametrization."""
    try:
        dataset = load_golden_dataset(DATASET_VERSION)
        return [case.id for case in dataset.test_cases]
    except FileNotFoundError:
        return []


def get_test_case_by_id(dataset: GoldenDataset, case_id: str) -> TestCase | None:
    """Find test case by ID in dataset.

    Args:
        dataset: The golden dataset.
        case_id: Test case identifier.

    Returns:
        TestCase or None if not found.
    """
    for tc in dataset.test_cases:
        if tc.id == case_id:
            return tc
    return None


@pytest.fixture(scope="module")
def golden_dataset() -> GoldenDataset:
    """Load the golden dataset."""
    return load_golden_dataset(DATASET_VERSION)


@pytest.mark.parametrize("case_id", get_test_case_ids())
@pytest.mark.asyncio
async def test_quilto_vs_claude(
    case_id: str,
    golden_dataset: GoldenDataset,
    cache_dir: Path,
    session_results: list[dict[str, Any]],
    session_cost: dict[str, float],
    use_cache: bool,
) -> None:
    """Test Quilto response quality against Claude baseline.

    This test performs pairwise LLM-as-judge evaluation with position swap
    to reduce systematic bias. Individual tests always pass - the aggregate
    win-rate threshold is checked at the session level.

    Args:
        case_id: Test case identifier.
        golden_dataset: Loaded golden dataset fixture.
        cache_dir: Cache directory for results.
        session_results: Shared storage for aggregate metrics.
        session_cost: Shared storage for cost tracking.
        use_cache: Whether to use cached results.
    """
    # Find test case
    test_case = get_test_case_by_id(golden_dataset, case_id)
    assert test_case is not None, f"Test case not found: {case_id}"

    # Check cache first
    if use_cache:
        cached = load_cached_result(cache_dir, DATASET_VERSION, case_id)
        if cached is not None:
            # Record cached result
            session_results.append(
                {
                    "case_id": case_id,
                    "category": test_case.category,
                    "winner": cached.get("winner", "error"),
                    "score": cached.get("score", 0.0),
                    "cached": True,
                }
            )
            return

    # Load Claude baseline
    baseline = load_baseline_response(DATASET_VERSION, case_id)
    if baseline is None:
        session_results.append(
            {
                "case_id": case_id,
                "category": test_case.category,
                "winner": "error",
                "score": 0.0,
                "reason": "Missing baseline response",
            }
        )
        pytest.skip(f"Missing baseline for {case_id}")
        return

    # Generate Quilto response
    quilto_response = await generate_quilto_response_cached(test_case)
    if quilto_response is None:
        session_results.append(
            {
                "case_id": case_id,
                "category": test_case.category,
                "winner": "error",
                "score": 0.0,
                "reason": "Quilto generation failed",
            }
        )
        pytest.skip(f"Quilto generation failed for {case_id}")
        return

    # Import DeepEval components (only here since module might be skipped)
    from deepeval.test_case import LLMTestCase

    from tests.eval.metrics import PairwiseComparisonMetric

    # Create DeepEval test case
    deepeval_case = LLMTestCase(
        input=test_case.query,
        actual_output=quilto_response,
        expected_output=baseline.response,
        additional_metadata={
            "id": case_id,
            "category": test_case.category,
            "context_entries": test_case.context_entries,
            "should_mention": test_case.evaluation_hints.should_mention,
            "should_not": test_case.evaluation_hints.should_not,
        },
    )

    # Run pairwise evaluation
    metric = PairwiseComparisonMetric(threshold=0.0)  # Don't fail individual tests
    score = await metric.a_measure(deepeval_case)

    # Determine winner
    if score == 1.0:
        winner = "quilto"
    elif score == 0.5:
        winner = "tie"
    else:
        winner = "claude"

    # Record result
    result = {
        "case_id": case_id,
        "category": test_case.category,
        "winner": winner,
        "score": score,
        "reason": metric.reason,
    }
    session_results.append(result)

    # Update session cost tracking
    update_session_cost(metric)

    # Save to cache if enabled
    if use_cache:
        save_cached_result(cache_dir, DATASET_VERSION, case_id, result)

    # Log result (test always passes - threshold checked at session level)
    print(f"\n{case_id} ({test_case.category}): {winner} (score={score})")
    print(f"  Reason: {metric.reason}")
