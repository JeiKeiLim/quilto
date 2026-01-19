"""Generate Claude baseline responses for E2E evaluation.

Usage:
    python -m tests.eval.generate_baseline --dataset-version v2026-01-19
    python -m tests.eval.generate_baseline --dataset-version v2026-01-19 --force
    python -m tests.eval.generate_baseline --dataset-version v2026-01-19 --dry-run
    python -m tests.eval.generate_baseline --dataset-version v2026-01-19 --cases case1,case2
    python -m tests.eval.generate_baseline --dataset-version v2026-01-19 --validate-only
"""

import argparse
import asyncio
import json
import logging
import sys
from datetime import UTC, datetime
from pathlib import Path

import litellm
import yaml
from dotenv import load_dotenv
from rich.progress import Progress, SpinnerColumn, TextColumn

from tests.eval.schema import BaselineResponse, GoldenDataset, ModelParams, TestCase

logger = logging.getLogger(__name__)

# Constants
PROJECT_ROOT = Path(__file__).parent.parent.parent
CORPUS_PATH = PROJECT_ROOT / "tests/corpus/fitness/entries/from_csv"
GOLDEN_DIR = PROJECT_ROOT / "tests/eval/golden"
BASELINE_DIR = GOLDEN_DIR / "baseline_responses"

MODEL = "openrouter/anthropic/claude-sonnet-4"
MAX_TOKENS = 1000
TEMPERATURE = 0.3
MAX_CONCURRENT = 2

SYSTEM_PROMPT = """You are a fitness assistant helping a user understand their workout history.
You have access to their logged workout entries provided below.

IMPORTANT:
- Base your response ONLY on the provided workout data
- If the data doesn't contain information to answer the question, say so clearly
- Use specific numbers and dates from the logs when relevant
- Be concise but complete
"""


def load_context_entries(dates: list[str]) -> str:
    """Load workout entries for given dates and format as context.

    Args:
        dates: List of date strings in YYYY-MM-DD format.

    Returns:
        Formatted context string with workout entries.
    """
    entries = []
    for date in dates:
        path = CORPUS_PATH / f"{date}.md"
        if path.exists():
            content = path.read_text().strip()
            entries.append(f"## Workout on {date}\n\n{content}")
        else:
            logger.warning("Missing entry for date: %s", date)
    return "\n\n---\n\n".join(entries)


def load_golden_dataset(version: str) -> GoldenDataset:
    """Load and validate a golden dataset by version.

    Args:
        version: Version string (e.g., "v2026-01-19").

    Returns:
        Validated GoldenDataset.

    Raises:
        FileNotFoundError: If dataset file doesn't exist.
        ValueError: If dataset fails validation.
    """
    dataset_path = GOLDEN_DIR / f"{version}.yaml"
    if not dataset_path.exists():
        raise FileNotFoundError(f"Dataset not found: {dataset_path}")

    with open(dataset_path) as f:
        data = yaml.safe_load(f)

    return GoldenDataset.model_validate(data)


def get_response_path(version: str, case_id: str) -> Path:
    """Get the file path for a baseline response.

    Args:
        version: Dataset version string.
        case_id: Test case ID.

    Returns:
        Path to the response JSON file.
    """
    return BASELINE_DIR / version / f"{case_id}.json"


def response_exists(version: str, case_id: str) -> bool:
    """Check if a baseline response already exists.

    Args:
        version: Dataset version string.
        case_id: Test case ID.

    Returns:
        True if response file exists.
    """
    return get_response_path(version, case_id).exists()


def save_response(response: BaselineResponse, version: str) -> None:
    """Save a baseline response to disk.

    Args:
        response: The baseline response to save.
        version: Dataset version string.
    """
    output_path = get_response_path(version, response.test_case_id)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(response.model_dump(), indent=2, ensure_ascii=False))


async def generate_response(
    case: TestCase,
    dataset_version: str,
    semaphore: asyncio.Semaphore,
) -> BaselineResponse:
    """Generate a single Claude response with concurrency control.

    Args:
        case: The test case to generate a response for.
        dataset_version: Version string for the dataset.
        semaphore: Asyncio semaphore for concurrency control.

    Returns:
        Generated BaselineResponse.
    """
    context = load_context_entries(case.context_entries)

    async with semaphore:
        response = await litellm.acompletion(
            model=MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"**Question:** {case.query}\n\n**My Workout Logs:**\n\n{context}"},
            ],
            max_tokens=MAX_TOKENS,
            temperature=TEMPERATURE,
        )

    return BaselineResponse(
        test_case_id=case.id,
        dataset_version=dataset_version,
        model=MODEL,
        model_params=ModelParams(max_tokens=MAX_TOKENS, temperature=TEMPERATURE),
        generated_at=datetime.now(UTC).isoformat(),
        query=case.query,
        context_entries=case.context_entries,
        context_provided=context,
        response=response.choices[0].message.content or "",
    )


def validate_responses(version: str, dataset: GoldenDataset) -> tuple[int, int, list[str]]:
    """Validate that all test cases have valid baseline responses.

    Args:
        version: Dataset version string.
        dataset: The golden dataset.

    Returns:
        Tuple of (valid_count, invalid_count, missing_ids).
    """
    valid = 0
    invalid = 0
    missing: list[str] = []

    for case in dataset.test_cases:
        path = get_response_path(version, case.id)
        if not path.exists():
            missing.append(case.id)
            continue

        try:
            data = json.loads(path.read_text())
            BaselineResponse.model_validate(data)
            valid += 1
        except Exception as e:
            logger.error("Invalid response for %s: %s", case.id, e)
            invalid += 1

    return valid, invalid, missing


async def run_generation(
    dataset: GoldenDataset,
    version: str,
    force: bool = False,
    dry_run: bool = False,
    case_filter: set[str] | None = None,
) -> tuple[int, int, int]:
    """Run the baseline generation process.

    Args:
        dataset: The golden dataset.
        version: Dataset version string.
        force: Whether to regenerate existing responses.
        dry_run: Whether to just report what would be generated.
        case_filter: Optional set of case IDs to generate (None = all).

    Returns:
        Tuple of (generated_count, skipped_count, failed_count).
    """
    semaphore = asyncio.Semaphore(MAX_CONCURRENT)
    generated = 0
    skipped = 0
    failed = 0

    cases_to_process = dataset.test_cases
    if case_filter:
        cases_to_process = [c for c in cases_to_process if c.id in case_filter]
        unknown_cases = case_filter - {c.id for c in cases_to_process}
        if unknown_cases:
            logger.warning("Unknown case IDs: %s", unknown_cases)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
    ) as progress:
        task = progress.add_task("Generating baseline responses...", total=len(cases_to_process))

        for case in cases_to_process:
            if response_exists(version, case.id) and not force:
                logger.debug("Skipping existing: %s", case.id)
                skipped += 1
                progress.advance(task)
                continue

            if dry_run:
                logger.info("[DRY RUN] Would generate: %s", case.id)
                generated += 1
                progress.advance(task)
                continue

            try:
                progress.update(task, description=f"Generating: {case.id}")
                response = await generate_response(case, version, semaphore)
                save_response(response, version)
                generated += 1
                logger.info("Generated: %s", case.id)
            except Exception as e:
                logger.error("Failed to generate %s: %s", case.id, e)
                failed += 1

            progress.advance(task)

    return generated, skipped, failed


def main() -> int:
    """Main entry point for baseline generation script.

    Returns:
        Exit code (0 for success, 1 for errors).
    """
    parser = argparse.ArgumentParser(description="Generate Claude baseline responses for E2E evaluation.")
    parser.add_argument("--dataset-version", required=True, help="Dataset version (e.g., v2026-01-19)")
    parser.add_argument("--force", action="store_true", help="Regenerate all responses (ignore existing)")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be generated without calling API")
    parser.add_argument("--cases", help="Comma-separated list of specific case IDs to generate")
    parser.add_argument("--validate-only", action="store_true", help="Only validate existing responses")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")

    args = parser.parse_args()

    # Configure logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(level=log_level, format="%(levelname)s: %(message)s")

    # Load .env for API keys
    load_dotenv()

    try:
        dataset = load_golden_dataset(args.dataset_version)
        logger.info("Loaded dataset %s with %d test cases", args.dataset_version, len(dataset.test_cases))
    except FileNotFoundError as e:
        logger.error(str(e))
        return 1
    except ValueError as e:
        logger.error("Invalid dataset: %s", e)
        return 1

    if args.validate_only:
        valid, invalid, missing = validate_responses(args.dataset_version, dataset)
        logger.info("Validation complete: %d valid, %d invalid, %d missing", valid, invalid, len(missing))
        if missing:
            logger.warning("Missing responses: %s", ", ".join(missing[:10]))
            if len(missing) > 10:
                logger.warning("... and %d more", len(missing) - 10)
        return 0 if invalid == 0 and len(missing) == 0 else 1

    case_filter = set(args.cases.split(",")) if args.cases else None

    generated, skipped, failed = asyncio.run(
        run_generation(
            dataset=dataset,
            version=args.dataset_version,
            force=args.force,
            dry_run=args.dry_run,
            case_filter=case_filter,
        )
    )

    logger.info("Summary: %d generated, %d skipped, %d failed", generated, skipped, failed)

    if failed > 0:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
