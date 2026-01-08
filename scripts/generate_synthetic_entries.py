#!/usr/bin/env python3
"""Validation script for synthetic test entries.

This script validates synthetic entries against expected outputs
and reports validation status for human review workflow.

Usage:
    uv run scripts/generate_synthetic_entries.py validate
    uv run scripts/generate_synthetic_entries.py stats
    uv run scripts/generate_synthetic_entries.py list-unvalidated
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

import yaml

# Add tests to path for importing corpus schemas
sys.path.insert(0, str(Path(__file__).parent.parent))

from pydantic import ValidationError

from tests.corpus.schemas.expected_output import ExpectedParserOutput

# Constants
SYNTHETIC_ENTRIES_DIR = Path("tests/corpus/fitness/entries/synthetic")
SYNTHETIC_EXPECTED_DIR = Path("tests/corpus/fitness/expected/parser/synthetic")
FRONTMATTER_PATTERN = re.compile(r"^---\n(.+?)\n---", re.DOTALL)


def parse_frontmatter(content: str) -> dict[str, Any]:
    """Extract YAML frontmatter from markdown content.

    Args:
        content: Full markdown file content with frontmatter.

    Returns:
        Parsed frontmatter as dictionary.
    """
    match = FRONTMATTER_PATTERN.match(content)
    if match:
        return yaml.safe_load(match.group(1))
    return {}


def get_entry_files() -> list[Path]:
    """Get all synthetic entry markdown files.

    Returns:
        List of paths to synthetic entry files.
    """
    if not SYNTHETIC_ENTRIES_DIR.exists():
        return []
    return sorted(SYNTHETIC_ENTRIES_DIR.glob("*.md"))


def get_expected_file(entry_path: Path) -> Path:
    """Get expected output JSON path for an entry.

    Args:
        entry_path: Path to the entry markdown file.

    Returns:
        Path to corresponding expected JSON file.
    """
    return SYNTHETIC_EXPECTED_DIR / entry_path.with_suffix(".json").name


def validate_entry(entry_path: Path, verbose: bool = False) -> list[str]:
    """Validate a single synthetic entry.

    Args:
        entry_path: Path to the entry markdown file.
        verbose: Whether to print detailed validation info.

    Returns:
        List of validation error messages (empty if valid).
    """
    errors: list[str] = []

    # Read entry content
    try:
        content = entry_path.read_text(encoding="utf-8")
    except OSError as e:
        errors.append(f"Cannot read entry file: {e}")
        return errors

    # Parse frontmatter
    frontmatter = parse_frontmatter(content)
    if not frontmatter:
        errors.append("Missing frontmatter")

    # Check required frontmatter fields
    if "validated_by" not in frontmatter:
        errors.append("Missing 'validated_by' field in frontmatter")
    elif frontmatter.get("validated_by") != "human":
        errors.append(
            f"'validated_by' must be 'human', got '{frontmatter.get('validated_by')}'"
        )

    if "category" not in frontmatter:
        errors.append("Missing 'category' field in frontmatter")

    # Check expected output exists
    expected_path = get_expected_file(entry_path)
    if not expected_path.exists():
        errors.append(f"Missing expected output: {expected_path}")
        return errors

    # Validate expected output format
    try:
        expected_data = json.loads(expected_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        errors.append(f"Invalid JSON in expected output: {e}")
        return errors

    # Validate against schema
    try:
        expected_output = ExpectedParserOutput.model_validate(expected_data)
    except ValidationError as e:
        errors.append(f"Expected output schema validation failed: {e}")
        return errors

    # Check date is "synthetic"
    if expected_output.date != "synthetic":
        errors.append(
            f"Expected output 'date' must be 'synthetic', got '{expected_output.date}'"
        )

    if verbose and not errors:
        print(f"  OK: {entry_path.name}")

    return errors


def cmd_validate(args: argparse.Namespace) -> int:
    """Validate all synthetic entries.

    Args:
        args: Command line arguments.

    Returns:
        Exit code (0 for success, 1 for failures).
    """
    entry_files = get_entry_files()

    if not entry_files:
        print("No synthetic entries found.")
        return 1

    if args.category:
        entry_files = [
            f for f in entry_files if f.stem.startswith(args.category + "-")
        ]

    total = len(entry_files)
    failed = 0
    all_errors: dict[str, list[str]] = {}

    print(f"Validating {total} synthetic entries...")

    for entry_path in entry_files:
        errors = validate_entry(entry_path, verbose=args.verbose)
        if errors:
            failed += 1
            all_errors[entry_path.name] = errors
            if args.verbose:
                print(f"  FAIL: {entry_path.name}")
                for error in errors:
                    print(f"    - {error}")

    print()
    print(f"Validation complete: {total - failed}/{total} passed")

    if all_errors:
        print()
        print("Failed entries:")
        for name, errors in all_errors.items():
            print(f"  {name}:")
            for error in errors:
                print(f"    - {error}")
        return 1

    return 0


def cmd_stats(args: argparse.Namespace) -> int:
    """Show statistics about synthetic entries.

    Args:
        args: Command line arguments.

    Returns:
        Exit code (always 0).
    """
    entry_files = get_entry_files()

    if not entry_files:
        print("No synthetic entries found.")
        return 0

    # Count by category
    categories: dict[str, int] = {}
    validated = 0
    unvalidated = 0

    for entry_path in entry_files:
        content = entry_path.read_text(encoding="utf-8")
        frontmatter = parse_frontmatter(content)

        category = frontmatter.get("category", "unknown")
        categories[category] = categories.get(category, 0) + 1

        if frontmatter.get("validated_by") == "human":
            validated += 1
        else:
            unvalidated += 1

    print("Synthetic Entry Statistics")
    print("=" * 40)
    print(f"Total entries: {len(entry_files)}")
    print(f"Validated: {validated}")
    print(f"Unvalidated: {unvalidated}")
    print()
    print("By category:")
    for category, count in sorted(categories.items()):
        print(f"  {category}: {count}")

    return 0


def cmd_list_unvalidated(args: argparse.Namespace) -> int:
    """List entries missing human validation.

    Args:
        args: Command line arguments.

    Returns:
        Exit code (0 for success).
    """
    entry_files = get_entry_files()

    if not entry_files:
        print("No synthetic entries found.")
        return 0

    unvalidated: list[str] = []

    for entry_path in entry_files:
        content = entry_path.read_text(encoding="utf-8")
        frontmatter = parse_frontmatter(content)

        if frontmatter.get("validated_by") != "human":
            unvalidated.append(entry_path.name)

    if not unvalidated:
        print("All entries are validated by human.")
        return 0

    print(f"Entries missing 'validated_by: human' ({len(unvalidated)}):")
    for name in unvalidated:
        print(f"  {name}")

    return 0


def main() -> int:
    """Main entry point.

    Returns:
        Exit code.
    """
    parser = argparse.ArgumentParser(
        description="Validate synthetic test entries for parser testing."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # validate command
    validate_parser = subparsers.add_parser(
        "validate", help="Validate all synthetic entries"
    )
    validate_parser.add_argument(
        "--category", help="Filter by category (e.g., typo, minimal)"
    )
    validate_parser.add_argument(
        "--verbose", "-v", action="store_true", help="Show detailed output"
    )
    validate_parser.set_defaults(func=cmd_validate)

    # stats command
    stats_parser = subparsers.add_parser(
        "stats", help="Show entry distribution statistics"
    )
    stats_parser.set_defaults(func=cmd_stats)

    # list-unvalidated command
    list_parser = subparsers.add_parser(
        "list-unvalidated", help="List entries missing human validation"
    )
    list_parser.set_defaults(func=cmd_list_unvalidated)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
