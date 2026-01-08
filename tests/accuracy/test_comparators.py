"""Tests for accuracy comparison utilities.

RED phase tests for ExerciseEquivalenceChecker and numeric comparators.
"""

from pathlib import Path

import pytest

from tests.accuracy.comparators import (
    ExerciseEquivalenceChecker,
    compare_reps,
    compare_sets,
    compare_weight,
)


class TestExerciseEquivalenceChecker:
    """Tests for ExerciseEquivalenceChecker class."""

    @pytest.fixture
    def checker(self) -> ExerciseEquivalenceChecker:
        """Create checker with test corpus equivalences."""
        yaml_path = (
            Path(__file__).parent.parent / "corpus" / "exercise_equivalences.yaml"
        )
        return ExerciseEquivalenceChecker(yaml_path)

    def test_exact_match_canonical(
        self, checker: ExerciseEquivalenceChecker
    ) -> None:
        """Canonical name should match itself."""
        assert checker.is_equivalent("Bench Press (Barbell)", "Bench Press (Barbell)")

    def test_korean_to_english_equivalent(
        self, checker: ExerciseEquivalenceChecker
    ) -> None:
        """Korean variant should match English canonical."""
        assert checker.is_equivalent("벤치프레스", "Bench Press (Barbell)")
        assert checker.is_equivalent("바벨 벤치프레스", "Bench Press (Barbell)")

    def test_english_to_korean_equivalent(
        self, checker: ExerciseEquivalenceChecker
    ) -> None:
        """English canonical should match Korean variant."""
        assert checker.is_equivalent("Bench Press (Barbell)", "벤치프레스")

    def test_case_insensitive(self, checker: ExerciseEquivalenceChecker) -> None:
        """Comparison should be case-insensitive."""
        assert checker.is_equivalent("bench press (barbell)", "BENCH PRESS (BARBELL)")
        assert checker.is_equivalent("PULL UP", "풀업")

    def test_non_equivalent_exercises(
        self, checker: ExerciseEquivalenceChecker
    ) -> None:
        """Different exercises should not match."""
        assert not checker.is_equivalent("Bench Press (Barbell)", "Pull Up")
        assert not checker.is_equivalent("벤치프레스", "풀업")

    def test_unknown_exercise_returns_false(
        self, checker: ExerciseEquivalenceChecker
    ) -> None:
        """Unknown exercise should return False, not raise error."""
        assert not checker.is_equivalent("Unknown Exercise", "Bench Press (Barbell)")
        assert not checker.is_equivalent("Bench Press (Barbell)", "Unknown Exercise")
        assert not checker.is_equivalent("Unknown 1", "Unknown 2")

    def test_empty_string_returns_false(
        self, checker: ExerciseEquivalenceChecker
    ) -> None:
        """Empty strings should return False."""
        assert not checker.is_equivalent("", "Bench Press (Barbell)")
        assert not checker.is_equivalent("Bench Press (Barbell)", "")
        assert not checker.is_equivalent("", "")

    def test_same_canonical_group(self, checker: ExerciseEquivalenceChecker) -> None:
        """Multiple variants in same group should all match each other."""
        # All variants of Squat (Barbell)
        variants = ["Squat (Barbell)", "바벨 스쿼트", "스쿼트"]
        for v1 in variants:
            for v2 in variants:
                assert checker.is_equivalent(v1, v2), f"{v1!r} should match {v2!r}"


class TestNumericComparators:
    """Tests for numeric field comparison functions."""

    class TestCompareWeight:
        """Tests for compare_weight function."""

        def test_exact_match(self):
            """Same weight values should match."""
            assert compare_weight(60.0, 60.0)
            assert compare_weight(100.5, 100.5)

        def test_both_none(self):
            """Both None should match (bodyweight exercises)."""
            assert compare_weight(None, None)

        def test_one_none_no_match(self):
            """One None should not match."""
            assert not compare_weight(60.0, None)
            assert not compare_weight(None, 60.0)

        def test_different_values_no_match(self):
            """Different weight values should not match."""
            assert not compare_weight(60.0, 70.0)
            assert not compare_weight(100.0, 100.1)

    class TestCompareReps:
        """Tests for compare_reps function."""

        def test_exact_match(self):
            """Same rep values should match."""
            assert compare_reps(10, 10)
            assert compare_reps(1, 1)

        def test_both_none(self):
            """Both None should match."""
            assert compare_reps(None, None)

        def test_one_none_no_match(self):
            """One None should not match."""
            assert not compare_reps(10, None)
            assert not compare_reps(None, 10)

        def test_different_values_no_match(self):
            """Different rep values should not match."""
            assert not compare_reps(10, 11)
            assert not compare_reps(8, 12)

    class TestCompareSets:
        """Tests for compare_sets function."""

        def test_exact_match(self):
            """Same set counts should match."""
            assert compare_sets(3, 3)
            assert compare_sets(5, 5)

        def test_different_values_no_match(self):
            """Different set counts should not match."""
            assert not compare_sets(3, 4)
            assert not compare_sets(5, 3)
