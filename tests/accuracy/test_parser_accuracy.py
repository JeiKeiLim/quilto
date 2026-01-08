"""Parser accuracy test runner.

This module provides accuracy testing for the parser against expected outputs
from the test corpus. Tests are marked to skip until Parser is implemented
in Story 2.3.

Primary accuracy metrics use only from_csv entries (93 files), excluding
synthetic entries which are used for robustness testing only.
"""

from dataclasses import dataclass, field
from pathlib import Path

import pytest

from tests.accuracy.comparators import (
    ExerciseEquivalenceChecker,
    compare_reps,
    compare_sets,
    compare_weight,
)
from tests.accuracy.mock_parser import parse_entry
from tests.corpus.schemas import (
    ExpectedExerciseRecord,
    ExpectedParserOutput,
    ExpectedSetDetail,
    is_synthetic,
)


@dataclass
class FieldAccuracy:
    """Per-field accuracy statistics.

    Attributes:
        total: Total number of comparisons.
        correct: Number of correct comparisons.
        accuracy: Accuracy percentage (0.0 - 100.0).
    """

    total: int = 0
    correct: int = 0
    accuracy: float = 0.0

    def compute_accuracy(self) -> None:
        """Compute accuracy percentage from total and correct counts."""
        if self.total > 0:
            self.accuracy = (self.correct / self.total) * 100.0
        else:
            self.accuracy = 0.0


@dataclass
class AccuracyMetrics:
    """Overall accuracy metrics for parser evaluation.

    Attributes:
        total_entries: Total number of entries tested.
        correct_entries: Number of entries with all fields correct.
        field_metrics: Per-field accuracy statistics.
    """

    total_entries: int = 0
    correct_entries: int = 0
    field_metrics: dict[str, FieldAccuracy] = field(
        default_factory=lambda: {
            "exercise_name": FieldAccuracy(),
            "sets": FieldAccuracy(),
            "weight": FieldAccuracy(),
            "reps": FieldAccuracy(),
        }
    )

    @property
    def entry_accuracy(self) -> float:
        """Calculate entry-level accuracy percentage."""
        if self.total_entries > 0:
            return (self.correct_entries / self.total_entries) * 100.0
        return 0.0

    def compute_all_accuracy(self) -> None:
        """Compute accuracy for all field metrics."""
        for field_accuracy in self.field_metrics.values():
            field_accuracy.compute_accuracy()


class AccuracyRunner:
    """Runs accuracy tests against expected parser outputs.

    This class loads expected outputs from the test corpus and compares
    parser output against them, calculating field-level and entry-level
    accuracy metrics.
    """

    def __init__(self) -> None:
        """Initialize the accuracy runner."""
        self.corpus_path = (
            Path(__file__).parent.parent / "corpus" / "fitness" / "expected" / "parser"
        )
        self.equivalence_path = (
            Path(__file__).parent.parent / "corpus" / "exercise_equivalences.yaml"
        )
        self.checker = ExerciseEquivalenceChecker(self.equivalence_path)
        self.metrics = AccuracyMetrics()

    def load_expected_outputs(self) -> list[tuple[Path, ExpectedParserOutput]]:
        """Load all expected outputs, excluding synthetic entries.

        Returns:
            List of (path, expected_output) tuples for from_csv entries only.
        """
        results: list[tuple[Path, ExpectedParserOutput]] = []

        for json_file in self.corpus_path.glob("*.json"):
            # Skip synthetic directory entries (they're in subdirectory)
            if is_synthetic(json_file):
                continue

            expected = ExpectedParserOutput.model_validate_json(
                json_file.read_text(encoding="utf-8")
            )

            # Double-check it's not synthetic by date
            if is_synthetic(json_file, expected):
                continue

            results.append((json_file, expected))

        return results

    def compare_exercise(
        self,
        actual: ExpectedExerciseRecord,
        expected: ExpectedExerciseRecord,
    ) -> bool:
        """Compare a single exercise record.

        Args:
            actual: Exercise record from parser output.
            expected: Exercise record from ground truth.

        Returns:
            True if all fields match, False otherwise.
        """
        all_correct = True

        # Exercise name (semantic comparison)
        self.metrics.field_metrics["exercise_name"].total += 1
        if self.checker.is_equivalent(actual.name, expected.name):
            self.metrics.field_metrics["exercise_name"].correct += 1
        else:
            all_correct = False

        # Set count (exact match)
        self.metrics.field_metrics["sets"].total += 1
        if compare_sets(actual.sets, expected.sets):
            self.metrics.field_metrics["sets"].correct += 1
        else:
            all_correct = False

        # Compare set details
        actual_details = {d.set_num: d for d in actual.set_details}
        expected_details = {d.set_num: d for d in expected.set_details}

        for set_num, expected_detail in expected_details.items():
            actual_detail = actual_details.get(set_num, ExpectedSetDetail(set_num=set_num))

            # Weight (exact match)
            self.metrics.field_metrics["weight"].total += 1
            if compare_weight(actual_detail.weight, expected_detail.weight):
                self.metrics.field_metrics["weight"].correct += 1
            else:
                all_correct = False

            # Reps (exact match)
            self.metrics.field_metrics["reps"].total += 1
            if compare_reps(actual_detail.reps, expected_detail.reps):
                self.metrics.field_metrics["reps"].correct += 1
            else:
                all_correct = False

        return all_correct

    def compare_entry(
        self,
        actual: ExpectedParserOutput,
        expected: ExpectedParserOutput,
    ) -> bool:
        """Compare a full entry (all exercises).

        Args:
            actual: Parser output for the entry.
            expected: Ground truth expected output.

        Returns:
            True if all exercises match, False otherwise.
        """
        # Build lookup by name for actual exercises
        actual_by_name: dict[str, ExpectedExerciseRecord] = {}
        for ex in actual.exercises:
            # Find canonical name for lookup
            actual_by_name[ex.name.lower()] = ex

        all_correct = True

        for expected_ex in expected.exercises:
            # Try to find matching actual exercise
            actual_ex: ExpectedExerciseRecord | None = None

            # First try exact name match
            if expected_ex.name.lower() in actual_by_name:
                actual_ex = actual_by_name[expected_ex.name.lower()]
            else:
                # Try semantic match
                for actual_name, candidate in actual_by_name.items():
                    if self.checker.is_equivalent(actual_name, expected_ex.name):
                        actual_ex = candidate
                        break

            if actual_ex is None:
                # No matching exercise found - create empty one for comparison
                actual_ex = ExpectedExerciseRecord(name="", sets=0, set_details=[])

            if not self.compare_exercise(actual_ex, expected_ex):
                all_correct = False

        return all_correct

    async def run(self) -> AccuracyMetrics:
        """Run accuracy tests against all expected outputs.

        Returns:
            AccuracyMetrics with field-level and entry-level accuracy.
        """
        expected_outputs = self.load_expected_outputs()
        self.metrics = AccuracyMetrics()  # Reset metrics

        for _path, expected in expected_outputs:
            self.metrics.total_entries += 1

            # Get parser output (placeholder for now)
            actual = await parse_entry("", None)  # type: ignore[arg-type]

            if self.compare_entry(actual, expected):
                self.metrics.correct_entries += 1

        self.metrics.compute_all_accuracy()
        return self.metrics

    def format_report(self) -> str:
        """Format accuracy metrics as a human-readable report.

        Returns:
            Formatted report string.
        """
        lines = [
            "=== Parser Accuracy Report ===",
            f"Total entries: {self.metrics.total_entries} (from_csv only, synthetic excluded)",
            f"Entry-level accuracy: {self.metrics.entry_accuracy:.1f}% "
            f"({self.metrics.correct_entries}/{self.metrics.total_entries} fully correct)",
            "",
            "Field-level accuracy:",
        ]

        for field_name, field_acc in self.metrics.field_metrics.items():
            lines.append(
                f"  {field_name}: {field_acc.accuracy:.1f}% "
                f"({field_acc.correct}/{field_acc.total})"
            )

        lines.append("")
        lines.append(
            "Note: Parser not implemented - accuracy tests will pass once Story 2.3 is complete."
        )

        return "\n".join(lines)


@pytest.mark.skip(reason="Parser not implemented - Story 2.3")
@pytest.mark.accuracy
class TestParserAccuracy:
    """Accuracy tests for parser evaluation.

    These tests are skipped until Parser agent is implemented in Story 2.3.
    """

    @pytest.fixture
    def runner(self) -> AccuracyRunner:
        """Create accuracy runner instance."""
        return AccuracyRunner()

    async def test_load_expected_outputs(self, runner: AccuracyRunner) -> None:
        """Should load expected outputs excluding synthetic entries."""
        outputs = runner.load_expected_outputs()
        # Should have 93 from_csv entries
        assert len(outputs) == 93

        # Verify no synthetic entries
        for path, output in outputs:
            assert not is_synthetic(path, output)

    async def test_accuracy_report_generated(self, runner: AccuracyRunner) -> None:
        """Should generate accuracy report after run."""
        await runner.run()
        report = runner.format_report()

        assert "Parser Accuracy Report" in report
        assert "from_csv only" in report
        assert "Entry-level accuracy" in report
        assert "Field-level accuracy" in report

    async def test_field_metrics_initialized(self, runner: AccuracyRunner) -> None:
        """Should have all required field metrics."""
        await runner.run()

        assert "exercise_name" in runner.metrics.field_metrics
        assert "sets" in runner.metrics.field_metrics
        assert "weight" in runner.metrics.field_metrics
        assert "reps" in runner.metrics.field_metrics


class TestAccuracyMetrics:
    """Unit tests for AccuracyMetrics dataclass."""

    def test_entry_accuracy_calculation(self):
        """Should calculate entry accuracy correctly."""
        metrics = AccuracyMetrics(total_entries=100, correct_entries=85)
        assert metrics.entry_accuracy == 85.0

    def test_entry_accuracy_zero_entries(self):
        """Should return 0.0 for zero entries."""
        metrics = AccuracyMetrics(total_entries=0, correct_entries=0)
        assert metrics.entry_accuracy == 0.0

    def test_field_accuracy_computation(self):
        """Should compute field accuracy correctly."""
        field_acc = FieldAccuracy(total=100, correct=90)
        field_acc.compute_accuracy()
        assert field_acc.accuracy == 90.0

    def test_field_accuracy_zero_total(self):
        """Should return 0.0 for zero total."""
        field_acc = FieldAccuracy(total=0, correct=0)
        field_acc.compute_accuracy()
        assert field_acc.accuracy == 0.0


class TestAccuracyRunnerLoading:
    """Tests for AccuracyRunner loading functionality (non-skipped)."""

    def test_corpus_path_exists(self):
        """Corpus path should exist."""
        runner = AccuracyRunner()
        assert runner.corpus_path.exists()

    def test_equivalence_path_exists(self):
        """Equivalence YAML path should exist."""
        runner = AccuracyRunner()
        assert runner.equivalence_path.exists()

    def test_loads_expected_outputs(self):
        """Should load expected outputs from corpus."""
        runner = AccuracyRunner()
        outputs = runner.load_expected_outputs()
        # Should have 93 from_csv entries based on story
        assert len(outputs) == 93

    def test_excludes_synthetic(self):
        """Should exclude synthetic entries from outputs."""
        runner = AccuracyRunner()
        outputs = runner.load_expected_outputs()

        for path, output in outputs:
            assert not is_synthetic(path, output), f"Synthetic entry loaded: {path}"
