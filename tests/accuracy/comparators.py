"""Comparison utilities for accuracy testing.

This module provides semantic comparison for exercise names using
equivalence mappings, and exact match comparison for numeric fields.
"""

from pathlib import Path

import yaml


class ExerciseEquivalenceChecker:
    """Check exercise name equivalence using YAML mapping.

    Loads exercise equivalences from a YAML file and provides semantic
    comparison between exercise names, supporting multiple languages
    and naming conventions.

    Attributes:
        _to_canonical: Reverse lookup dict mapping variant.lower() to canonical name.
    """

    def __init__(self, yaml_path: Path) -> None:
        """Load exercise equivalences from YAML file.

        Args:
            yaml_path: Path to the exercise_equivalences.yaml file.
        """
        with open(yaml_path, encoding="utf-8") as f:
            data: dict[str, list[str]] = yaml.safe_load(f)

        # Build reverse lookup: variant.lower() -> canonical
        self._to_canonical: dict[str, str] = {}
        for canonical, variants in data.items():
            for variant in variants:
                self._to_canonical[variant.lower()] = canonical

    def is_equivalent(self, actual: str, expected: str) -> bool:
        """Check if two exercise names are semantically equivalent.

        Comparison is case-insensitive. Both names must exist in the
        equivalence mapping to be considered equivalent.

        Args:
            actual: The actual exercise name from parser output.
            expected: The expected exercise name from ground truth.

        Returns:
            True if both names map to the same canonical form, False otherwise.
            Returns False if either name is unknown (not in mapping).
        """
        if not actual or not expected:
            return False

        actual_canonical = self._to_canonical.get(actual.lower())
        expected_canonical = self._to_canonical.get(expected.lower())

        if actual_canonical is None or expected_canonical is None:
            return False

        return actual_canonical == expected_canonical


def compare_weight(actual: float | None, expected: float | None) -> bool:
    """Compare weight values for accuracy testing.

    Uses exact match comparison. Both None values match (for bodyweight
    exercises), but one None and one value do not match.

    Args:
        actual: Actual weight from parser output.
        expected: Expected weight from ground truth.

    Returns:
        True if values match exactly, False otherwise.
    """
    return actual == expected


def compare_reps(actual: int | None, expected: int | None) -> bool:
    """Compare rep values for accuracy testing.

    Uses exact match comparison. Both None values match,
    but one None and one value do not match.

    Args:
        actual: Actual rep count from parser output.
        expected: Expected rep count from ground truth.

    Returns:
        True if values match exactly, False otherwise.
    """
    return actual == expected


def compare_sets(actual: int, expected: int) -> bool:
    """Compare set count values for accuracy testing.

    Uses exact match comparison.

    Args:
        actual: Actual set count from parser output.
        expected: Expected set count from ground truth.

    Returns:
        True if values match exactly, False otherwise.
    """
    return actual == expected
