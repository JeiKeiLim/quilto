"""CLI runner for pairwise LLM-as-Judge evaluation.

Usage:
    python -m tests.eval.run_evaluation --dataset-version v2026-01-19
    python -m tests.eval.run_evaluation --dataset-version v2026-01-19 --cases case1,case2
    python -m tests.eval.run_evaluation --dataset-version v2026-01-19 --judge-model gpt-4o
    python -m tests.eval.run_evaluation --dataset-version v2026-01-19 --dry-run
    python -m tests.eval.run_evaluation --dataset-version v2026-01-19 --verbose
"""

import argparse
import asyncio
import json
import logging
import sys
from datetime import UTC, datetime
from pathlib import Path

from dotenv import load_dotenv
from rich.console import Console
from rich.progress import BarColumn, Progress, SpinnerColumn, TaskProgressColumn, TextColumn
from rich.table import Table

from tests.eval.generate_baseline import (
    get_response_path,
    load_golden_dataset,
)
from tests.eval.pairwise_judge import (
    PairwiseEvaluator,
    clear_quilto_cache,
    generate_quilto_response_cached,
)
from tests.eval.schema import (
    BaselineResponse,
    CategoryMetrics,
    EvaluationMetrics,
    EvaluationRun,
    ModelParams,
    PairwiseResult,
    TestCase,
)

logger = logging.getLogger(__name__)
console = Console()

# Constants
PROJECT_ROOT = Path(__file__).parent.parent.parent
RESULTS_DIR = PROJECT_ROOT / "tests" / "eval" / "results"

# Default settings
DEFAULT_JUDGE_MODEL = "gpt-4o-mini"
DEFAULT_TEMPERATURE = 0.0
DEFAULT_MAX_TOKENS = 2000


def load_baseline_response(version: str, case_id: str) -> BaselineResponse | None:
    """Load a baseline response for a test case.

    Args:
        version: Dataset version string.
        case_id: Test case ID.

    Returns:
        BaselineResponse or None if not found.
    """
    path = get_response_path(version, case_id)
    if not path.exists():
        return None

    try:
        data = json.loads(path.read_text())
        return BaselineResponse.model_validate(data)
    except Exception as e:
        logger.error("Failed to load baseline for %s: %s", case_id, e)
        return None


def calculate_metrics(results: list[PairwiseResult], test_cases: list[TestCase]) -> EvaluationMetrics:
    """Calculate aggregate metrics from evaluation results.

    Args:
        results: List of pairwise results.
        test_cases: List of test cases (for category mapping).

    Returns:
        EvaluationMetrics instance.
    """
    # Build category lookup
    case_categories = {tc.id: tc.category for tc in test_cases}

    # Initialize counters
    quilto_wins = 0
    claude_wins = 0
    ties = 0
    errors = 0
    consistent_count = 0
    inconsistent_count = 0
    per_category: dict[str, CategoryMetrics] = {}

    for result in results:
        category = case_categories.get(result.test_case_id, "unknown")

        if category not in per_category:
            per_category[category] = CategoryMetrics()

        cat_metrics = per_category[category]

        if result.final_winner == "error":
            errors += 1
            cat_metrics.errors += 1
        elif result.final_winner == "quilto":
            quilto_wins += 1
            cat_metrics.quilto_wins += 1
        elif result.final_winner == "claude":
            claude_wins += 1
            cat_metrics.claude_wins += 1
        else:  # tie
            ties += 1
            cat_metrics.ties += 1

        if result.is_consistent:
            consistent_count += 1
        else:
            inconsistent_count += 1

    total = len(results)
    valid = total - errors

    return EvaluationMetrics(
        total_cases=total,
        quilto_wins=quilto_wins,
        claude_wins=claude_wins,
        ties=ties,
        errors=errors,
        consistent_count=consistent_count,
        inconsistent_count=inconsistent_count,
        win_rate=quilto_wins / valid if valid > 0 else 0.0,
        tie_rate=ties / valid if valid > 0 else 0.0,
        inconsistency_rate=inconsistent_count / total if total > 0 else 0.0,
        per_category=per_category,
    )


def save_results(evaluation_run: EvaluationRun, output_dir: Path) -> Path:
    """Save evaluation results to JSON file.

    Args:
        evaluation_run: Complete evaluation results.
        output_dir: Output directory.

    Returns:
        Path to saved file.
    """
    version_dir = output_dir / evaluation_run.version
    version_dir.mkdir(parents=True, exist_ok=True)

    filename = f"{evaluation_run.timestamp.replace(':', '-').replace('.', '-')}.json"
    output_path = version_dir / filename

    output_path.write_text(
        json.dumps(evaluation_run.model_dump(), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    return output_path


def print_summary(metrics: EvaluationMetrics) -> None:
    """Print evaluation summary to console.

    Args:
        metrics: Evaluation metrics to display.
    """
    console.print("\n[bold]📊 Evaluation Summary[/bold]\n")

    # Overall stats table
    overall_table = Table(title="Overall Results", show_header=True)
    overall_table.add_column("Metric", style="cyan")
    overall_table.add_column("Value", justify="right")

    overall_table.add_row("Total Cases", str(metrics.total_cases))
    overall_table.add_row("Quilto Wins", f"[green]{metrics.quilto_wins}[/green]")
    overall_table.add_row("Claude Wins", f"[red]{metrics.claude_wins}[/red]")
    overall_table.add_row("Ties", f"[yellow]{metrics.ties}[/yellow]")
    overall_table.add_row("Errors", f"[red]{metrics.errors}[/red]" if metrics.errors else "0")
    overall_table.add_row("", "")
    overall_table.add_row("Win Rate", f"{metrics.win_rate:.1%}")
    overall_table.add_row("Tie Rate", f"{metrics.tie_rate:.1%}")
    overall_table.add_row("Inconsistency Rate", f"{metrics.inconsistency_rate:.1%}")

    console.print(overall_table)

    # Per-category table
    if metrics.per_category:
        console.print()
        category_table = Table(title="Per-Category Results", show_header=True)
        category_table.add_column("Category", style="cyan")
        category_table.add_column("Quilto", justify="right")
        category_table.add_column("Claude", justify="right")
        category_table.add_column("Ties", justify="right")
        category_table.add_column("Errors", justify="right")

        for category in sorted(metrics.per_category.keys()):
            cat = metrics.per_category[category]
            category_table.add_row(
                category,
                f"[green]{cat.quilto_wins}[/green]",
                f"[red]{cat.claude_wins}[/red]",
                f"[yellow]{cat.ties}[/yellow]",
                str(cat.errors) if cat.errors else "-",
            )

        console.print(category_table)


async def run_evaluation(
    dataset_version: str,
    judge_model: str,
    case_filter: set[str] | None,
    dry_run: bool,
    cache_quilto: bool,
    output_dir: Path,
) -> tuple[list[PairwiseResult], EvaluationMetrics]:
    """Run the pairwise evaluation process.

    Args:
        dataset_version: Dataset version string.
        judge_model: LiteLLM model ID for judge.
        case_filter: Optional set of case IDs to evaluate.
        dry_run: If True, only report what would be evaluated.
        cache_quilto: Whether to cache Quilto responses.
        output_dir: Directory to save results.

    Returns:
        Tuple of (results list, metrics).
    """
    # Load dataset
    dataset = load_golden_dataset(dataset_version)
    logger.info("Loaded dataset %s with %d test cases", dataset_version, len(dataset.test_cases))

    # Filter cases if specified
    test_cases = dataset.test_cases
    if case_filter:
        test_cases = [c for c in test_cases if c.id in case_filter]
        unknown = case_filter - {c.id for c in test_cases}
        if unknown:
            logger.warning("Unknown case IDs: %s", unknown)

    if not test_cases:
        logger.error("No test cases to evaluate")
        return [], EvaluationMetrics(
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
        )

    if dry_run:
        console.print(f"\n[yellow]DRY RUN[/yellow]: Would evaluate {len(test_cases)} cases\n")
        for case in test_cases:
            baseline = load_baseline_response(dataset_version, case.id)
            status = "[green]✓[/green]" if baseline else "[red]✗[/red]"
            console.print(f"  {status} {case.id} ({case.category})")
        return [], EvaluationMetrics(
            total_cases=len(test_cases),
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
        )

    # Initialize evaluator
    evaluator = PairwiseEvaluator(judge_model=judge_model)
    results: list[PairwiseResult] = []

    # Clear cache if not using it
    if not cache_quilto:
        clear_quilto_cache()

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("Evaluating...", total=len(test_cases))

        for case in test_cases:
            progress.update(task, description=f"Evaluating: {case.id[:30]}...")

            # Load baseline
            baseline = load_baseline_response(dataset_version, case.id)
            if baseline is None:
                logger.error("Missing baseline for %s", case.id)
                results.append(
                    PairwiseResult(
                        test_case_id=case.id,
                        quilto_response=None,
                        claude_response="",
                        judgment_ab=None,
                        judgment_ba=None,
                        final_winner="error",
                        is_consistent=False,
                        quilto_aggregate=None,
                        claude_aggregate=None,
                        error_message="Missing baseline response",
                    )
                )
                progress.advance(task)
                continue

            # Generate Quilto response
            quilto_response = await generate_quilto_response_cached(case, use_cache=cache_quilto)
            if quilto_response is None:
                logger.error("Quilto generation failed for %s", case.id)
                results.append(
                    PairwiseResult(
                        test_case_id=case.id,
                        quilto_response=None,
                        claude_response=baseline.response,
                        judgment_ab=None,
                        judgment_ba=None,
                        final_winner="error",
                        is_consistent=False,
                        quilto_aggregate=None,
                        claude_aggregate=None,
                        error_message="Quilto generation failed",
                    )
                )
                progress.advance(task)
                continue

            # Run pairwise evaluation
            result = await evaluator.evaluate_with_swap(
                test_case=case,
                quilto_response=quilto_response,
                claude_response=baseline.response,
            )
            results.append(result)

            # Log result
            logger.info(
                "%s: %s (consistent=%s)",
                case.id,
                result.final_winner,
                result.is_consistent,
            )

            progress.advance(task)

    # Calculate metrics
    metrics = calculate_metrics(results, dataset.test_cases)

    return results, metrics


def main() -> int:
    """Main entry point for evaluation CLI.

    Returns:
        Exit code (0 for success, 1 for errors).
    """
    parser = argparse.ArgumentParser(description="Run pairwise LLM-as-judge evaluation.")
    parser.add_argument("--dataset-version", required=True, help="Dataset version (e.g., v2026-01-19)")
    parser.add_argument("--cases", help="Comma-separated list of specific case IDs to evaluate")
    parser.add_argument(
        "--judge-model", default=DEFAULT_JUDGE_MODEL, help=f"Judge model (default: {DEFAULT_JUDGE_MODEL})"
    )
    parser.add_argument("--dry-run", action="store_true", help="Show what would be evaluated without running")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")
    parser.add_argument("--output-dir", type=Path, default=RESULTS_DIR, help="Output directory for results")
    parser.add_argument("--cache-quilto-responses", action="store_true", help="Cache Quilto responses")

    args = parser.parse_args()

    # Configure logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(level=log_level, format="%(levelname)s: %(message)s")

    # Load .env for API keys
    load_dotenv()

    case_filter = set(args.cases.split(",")) if args.cases else None

    try:
        results, metrics = asyncio.run(
            run_evaluation(
                dataset_version=args.dataset_version,
                judge_model=args.judge_model,
                case_filter=case_filter,
                dry_run=args.dry_run,
                cache_quilto=args.cache_quilto_responses,
                output_dir=args.output_dir,
            )
        )

        if not args.dry_run and results:
            # Save results
            timestamp = datetime.now(UTC).isoformat()
            evaluation_run = EvaluationRun(
                version=args.dataset_version,
                timestamp=timestamp,
                judge_model=args.judge_model,
                judge_params=ModelParams(max_tokens=DEFAULT_MAX_TOKENS, temperature=DEFAULT_TEMPERATURE),
                results=results,
                metrics=metrics,
            )

            output_path = save_results(evaluation_run, args.output_dir)
            console.print(f"\n[green]Results saved to:[/green] {output_path}")

            # Print summary
            print_summary(metrics)

        return 0 if metrics.errors == 0 else 1

    except FileNotFoundError as e:
        logger.error(str(e))
        return 1
    except Exception as e:
        logger.exception("Evaluation failed: %s", e)
        return 1


if __name__ == "__main__":
    sys.exit(main())
