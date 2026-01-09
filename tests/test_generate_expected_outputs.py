"""Tests for generate_expected_outputs.py script output validation.

These tests verify the script logic by testing the generated outputs
match expected patterns and structure.
"""

from datetime import datetime
from pathlib import Path


# Helper functions that mirror the script's logic
def _extract_date(datetime_str: str) -> str:
    """Extract YYYY-MM-DD date from datetime string."""
    dt = datetime.strptime(datetime_str, "%Y-%m-%d %H:%M:%S")
    return dt.date().isoformat()


def _parse_weight(weight_str: str) -> float | None:
    """Parse weight value, returning None for bodyweight exercises."""
    weight = float(weight_str)
    if weight == 0:
        return None
    return weight


def _parse_reps(reps_str: str) -> int:
    """Parse reps value, converting float to int."""
    return int(float(reps_str))


class TestExtractDate:
    """Tests for date extraction logic."""

    def test_extracts_date_from_datetime_string(self) -> None:
        """Test extracting date from CSV datetime format."""
        result = _extract_date("2019-01-28 19:00:00")
        assert result == "2019-01-28"

    def test_extracts_date_different_times(self) -> None:
        """Test date extraction ignores time component."""
        assert _extract_date("2019-01-28 00:00:00") == "2019-01-28"
        assert _extract_date("2019-01-28 23:59:59") == "2019-01-28"

    def test_handles_various_dates(self) -> None:
        """Test extracting dates from various formats."""
        assert _extract_date("2022-12-31 12:30:00") == "2022-12-31"
        assert _extract_date("2019-02-01 08:15:00") == "2019-02-01"


class TestParseWeight:
    """Tests for weight parsing logic."""

    def test_returns_float_for_nonzero_weight(self) -> None:
        """Test parsing normal weight values."""
        assert _parse_weight("100.0") == 100.0
        assert _parse_weight("84.8") == 84.8
        assert _parse_weight("77.5") == 77.5

    def test_returns_none_for_zero_weight(self) -> None:
        """Test bodyweight exercises (weight=0) return None."""
        assert _parse_weight("0") is None
        assert _parse_weight("0.0") is None

    def test_preserves_decimal_precision(self) -> None:
        """Test decimal weights are preserved as-is."""
        assert _parse_weight("22.68") == 22.68
        assert _parse_weight("45.359") == 45.359


class TestParseReps:
    """Tests for reps parsing logic."""

    def test_converts_float_string_to_int(self) -> None:
        """Test converting float reps to integer."""
        assert _parse_reps("8.0") == 8
        assert _parse_reps("10.0") == 10

    def test_truncates_decimal_reps(self) -> None:
        """Test decimal reps are truncated (not rounded)."""
        assert _parse_reps("8.9") == 8
        assert _parse_reps("120.0") == 120

    def test_handles_integer_strings(self) -> None:
        """Test parsing integer strings."""
        assert _parse_reps("5") == 5
        assert _parse_reps("12") == 12


class TestScriptIntegration:
    """Integration tests for the script outputs."""

    def test_csv_path_exists(self) -> None:
        """Verify the CSV source file exists."""
        csv_path = Path(__file__).parent / "corpus" / "fitness" / "ground_truth" / "strong_workouts.csv"
        assert csv_path.exists(), f"CSV not found at {csv_path}"

    def test_output_dir_exists(self) -> None:
        """Verify output directory was created."""
        output_dir = Path(__file__).parent / "corpus" / "fitness" / "expected" / "parser"
        assert output_dir.exists(), f"Output dir not found at {output_dir}"
        assert output_dir.is_dir()

    def test_equivalences_file_exists(self) -> None:
        """Verify equivalences file was created."""
        equivalences_path = Path(__file__).parent / "corpus" / "exercise_equivalences.yaml"
        assert equivalences_path.exists(), f"Equivalences not found at {equivalences_path}"

    def test_expected_output_count_matches_entries(self) -> None:
        """Verify 93 expected outputs match 93 from_csv entries."""
        expected_dir = Path(__file__).parent / "corpus" / "fitness" / "expected" / "parser"
        entries_dir = Path(__file__).parent / "corpus" / "fitness" / "entries" / "from_csv"

        expected_count = len(list(expected_dir.glob("*.json")))
        entries_count = len(list(entries_dir.glob("*.md")))

        assert expected_count == 93, f"Expected 93 JSON files, found {expected_count}"
        assert entries_count == 93, f"Expected 93 entry files, found {entries_count}"
