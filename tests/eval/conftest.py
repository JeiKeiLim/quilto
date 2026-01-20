"""Pytest configuration for LLM evaluation tests.

This module provides fixtures, hooks, and configuration for running
LLM-as-judge evaluation tests with win-rate threshold enforcement.
"""

import hashlib
import json
import os
from collections.abc import Generator
from pathlib import Path
from typing import Any

import pytest

# Configuration from environment
LLM_EVAL_THRESHOLD = float(os.getenv("LLM_EVAL_THRESHOLD", "0.4"))
LLM_EVAL_CACHE_DIR = Path(__file__).parent / ".cache"
LLM_EVAL_CACHE_ENABLED = os.getenv("LLM_EVAL_CACHE", "true").lower() == "true"

# Session-level storage for aggregate metrics
_session_results: list[dict[str, Any]] = []
_session_cost: dict[str, float] = {"input_tokens": 0, "output_tokens": 0, "estimated_cost": 0.0}


def pytest_configure(config: pytest.Config) -> None:
    """Register custom markers."""
    config.addinivalue_line("markers", "llm_eval: LLM evaluation tests (slow, requires LLM API)")
    config.addinivalue_line("markers", "slow: slow-running tests")


def pytest_addoption(parser: pytest.Parser) -> None:
    """Add custom command-line options."""
    parser.addoption("--use-cache", action="store_true", help="Use cached evaluation results")
    parser.addoption("--no-cache", action="store_true", help="Disable caching (force fresh evaluation)")
    parser.addoption("--full", action="store_true", help="Run full evaluation (all 50 cases)")


def pytest_terminal_summary(
    terminalreporter: Any,
    exitstatus: int,
    config: pytest.Config,
) -> None:
    """Display aggregate metrics and cost summary at end of session."""
    if not _session_results:
        return

    # Calculate aggregate win-rate
    quilto_wins = sum(1 for r in _session_results if r.get("winner") == "quilto")
    claude_wins = sum(1 for r in _session_results if r.get("winner") == "claude")
    ties = sum(1 for r in _session_results if r.get("winner") == "tie")
    errors = sum(1 for r in _session_results if r.get("winner") == "error")
    total = len(_session_results)
    valid = total - errors

    win_rate = quilto_wins / valid if valid > 0 else 0.0
    tie_rate = ties / valid if valid > 0 else 0.0

    terminalreporter.write_sep("=", "LLM Evaluation Summary")
    terminalreporter.write_line(f"Total: {total}, Quilto: {quilto_wins}, Claude: {claude_wins}, Ties: {ties}")
    if errors > 0:
        terminalreporter.write_line(f"Errors: {errors}")
    terminalreporter.write_line(f"Win Rate: {win_rate:.1%} (threshold: {LLM_EVAL_THRESHOLD:.1%})")
    terminalreporter.write_line(f"Tie Rate: {tie_rate:.1%}")

    # Cost summary
    if _session_cost["estimated_cost"] > 0:
        terminalreporter.write_line("")
        terminalreporter.write_line(
            f"Tokens: {int(_session_cost['input_tokens'])} input, {int(_session_cost['output_tokens'])} output"
        )
        terminalreporter.write_line(f"Estimated Cost: ${_session_cost['estimated_cost']:.4f}")

    # Threshold check
    if win_rate < LLM_EVAL_THRESHOLD:
        terminalreporter.write_line("")
        terminalreporter.write_line(
            f"FAILED: Win rate {win_rate:.1%} below threshold {LLM_EVAL_THRESHOLD:.1%}!", red=True, bold=True
        )

    # Per-category breakdown
    categories: dict[str, dict[str, int]] = {}
    for r in _session_results:
        cat = r.get("category", "unknown")
        if cat not in categories:
            categories[cat] = {"quilto": 0, "claude": 0, "tie": 0}
        winner = r.get("winner", "error")
        if winner in categories[cat]:
            categories[cat][winner] += 1

    if categories:
        terminalreporter.write_line("")
        terminalreporter.write_line("Per-Category Breakdown:")
        for cat in sorted(categories.keys()):
            counts = categories[cat]
            terminalreporter.write_line(
                f"  {cat}: Quilto={counts['quilto']}, Claude={counts['claude']}, Ties={counts['tie']}"
            )

    # Detailed failure reporting (Claude wins)
    failures = [r for r in _session_results if r.get("winner") == "claude"]
    if failures:
        terminalreporter.write_line("")
        terminalreporter.write_sep("-", "Failed Cases (Claude Wins)")
        for failure in failures:
            case_id = failure.get("case_id", "unknown")
            category = failure.get("category", "unknown")
            reason = failure.get("reason", "No reason provided")
            terminalreporter.write_line(f"  {case_id} ({category}):")
            terminalreporter.write_line(f"    {reason}")


def pytest_sessionfinish(session: pytest.Session, exitstatus: int) -> None:
    """Check aggregate win-rate threshold after all tests complete.

    Note: pytest_sessionfinish does not use return values.
    We must modify session.exitstatus directly to change exit code.
    """
    if not _session_results:
        return

    # Calculate win-rate
    errors = sum(1 for r in _session_results if r.get("winner") == "error")
    quilto_wins = sum(1 for r in _session_results if r.get("winner") == "quilto")
    total = len(_session_results)
    valid = total - errors

    win_rate = quilto_wins / valid if valid > 0 else 0.0

    # Fail if below threshold - modify session.exitstatus directly
    if win_rate < LLM_EVAL_THRESHOLD and session.exitstatus == 0:
        session.exitstatus = 1


@pytest.fixture(scope="session")
def eval_threshold() -> float:
    """Return configured win-rate threshold."""
    return LLM_EVAL_THRESHOLD


@pytest.fixture(scope="session")
def cache_dir() -> Path:
    """Return cache directory for evaluation results."""
    LLM_EVAL_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    return LLM_EVAL_CACHE_DIR


@pytest.fixture(scope="session")
def session_results() -> Generator[list[dict[str, Any]]]:
    """Provide shared results storage for aggregate metrics."""
    _session_results.clear()
    yield _session_results


@pytest.fixture(scope="session")
def session_cost() -> Generator[dict[str, float]]:
    """Provide shared cost tracking for the session.

    This fixture yields the session-level cost tracker. Tests should
    call update_session_cost() to add token usage from their evaluations.
    """
    _session_cost["input_tokens"] = 0
    _session_cost["output_tokens"] = 0
    _session_cost["estimated_cost"] = 0.0
    yield _session_cost


def update_session_cost(evaluator_or_metric: Any) -> None:
    """Update session cost from an evaluator or metric instance.

    This function extracts token usage from PairwiseEvaluator or
    PairwiseComparisonMetric and adds it to the session cost tracker.

    Args:
        evaluator_or_metric: A PairwiseEvaluator or PairwiseComparisonMetric instance.
    """
    # Get the evaluator (metric wraps one internally)
    evaluator = getattr(evaluator_or_metric, "_evaluator", evaluator_or_metric)

    if hasattr(evaluator, "get_token_usage"):
        usage = evaluator.get_token_usage()
        _session_cost["input_tokens"] += usage.get("input_tokens", 0)
        _session_cost["output_tokens"] += usage.get("output_tokens", 0)

    if hasattr(evaluator, "get_cost_estimate"):
        _session_cost["estimated_cost"] += evaluator.get_cost_estimate()


@pytest.fixture(scope="session")
def use_cache(request: pytest.FixtureRequest) -> bool:
    """Determine if caching should be used based on CLI options."""
    if request.config.getoption("--no-cache"):
        return False
    if request.config.getoption("--use-cache"):
        return True
    return LLM_EVAL_CACHE_ENABLED


def compute_cache_key(test_case_id: str, dataset_version: str, code_hash: str | None = None) -> str:
    """Compute cache key for evaluation result.

    Args:
        test_case_id: Test case identifier.
        dataset_version: Dataset version string.
        code_hash: Optional hash of relevant code (for invalidation).

    Returns:
        Cache key string.
    """
    key_parts = [test_case_id, dataset_version]
    if code_hash:
        key_parts.append(code_hash)
    return hashlib.sha256(":".join(key_parts).encode()).hexdigest()[:16]


def get_code_hash() -> str:
    """Compute hash of relevant evaluation code for cache invalidation.

    Returns:
        SHA256 hash of pairwise_judge.py content.
    """
    judge_path = Path(__file__).parent / "pairwise_judge.py"
    if judge_path.exists():
        content = judge_path.read_text()
        return hashlib.sha256(content.encode()).hexdigest()[:16]
    return "unknown"


def load_cached_result(cache_dir: Path, dataset_version: str, test_case_id: str) -> dict[str, Any] | None:
    """Load cached evaluation result if available and valid.

    Args:
        cache_dir: Cache directory path.
        dataset_version: Dataset version string.
        test_case_id: Test case identifier.

    Returns:
        Cached result dict or None if not available.
    """
    cache_key = compute_cache_key(test_case_id, dataset_version, get_code_hash())
    cache_path = cache_dir / dataset_version / f"{cache_key}.json"

    if not cache_path.exists():
        return None

    try:
        data = json.loads(cache_path.read_text())
        # Validate cache structure
        if data.get("test_case_id") == test_case_id and data.get("dataset_version") == dataset_version:
            return data
    except (json.JSONDecodeError, KeyError):
        pass

    return None


def save_cached_result(
    cache_dir: Path,
    dataset_version: str,
    test_case_id: str,
    result: dict[str, Any],
) -> None:
    """Save evaluation result to cache.

    Args:
        cache_dir: Cache directory path.
        dataset_version: Dataset version string.
        test_case_id: Test case identifier.
        result: Evaluation result to cache.
    """
    cache_key = compute_cache_key(test_case_id, dataset_version, get_code_hash())
    version_dir = cache_dir / dataset_version
    version_dir.mkdir(parents=True, exist_ok=True)
    cache_path = version_dir / f"{cache_key}.json"

    cache_data = {
        **result,
        "test_case_id": test_case_id,
        "dataset_version": dataset_version,
        "code_hash": get_code_hash(),
    }
    cache_path.write_text(json.dumps(cache_data, indent=2))
