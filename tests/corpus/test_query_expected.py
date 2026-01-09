"""Tests for query expected output schemas and test case validation.

These tests verify:
1. QueryTestCase schema validates correctly
2. All query test case JSON files parse against schema
3. All context_entries reference existing entries
4. Minimum 10 test cases exist per AC requirements
5. Schema robustness (invalid types rejected, empty objects rejected)
"""

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from tests.corpus.schemas import QueryTestCase

CORPUS_ROOT = Path(__file__).parent
QUERY_DIR = CORPUS_ROOT / "fitness" / "expected" / "query"
FROM_CSV_DIR = CORPUS_ROOT / "fitness" / "entries" / "from_csv"
SYNTHETIC_DIR = CORPUS_ROOT / "fitness" / "entries" / "synthetic"


class TestQueryTestCase:
    """Tests for QueryTestCase model."""

    def test_creates_with_all_fields(self) -> None:
        """Test creating a test case with all required fields."""
        test_case = QueryTestCase(
            query="How has my bench press progressed?",
            context_entries=["2019-01-29", "2019-02-01"],
            expected_analysis_points=["weight_progression_identified", "rep_range_noted"],
            expected_response_elements=["mentions_starting_weight", "provides_trend_assessment"],
        )
        assert test_case.query == "How has my bench press progressed?"
        assert test_case.context_entries == ["2019-01-29", "2019-02-01"]
        assert test_case.expected_analysis_points == [
            "weight_progression_identified",
            "rep_range_noted",
        ]
        assert test_case.expected_response_elements == [
            "mentions_starting_weight",
            "provides_trend_assessment",
        ]

    def test_strict_mode_rejects_wrong_types(self) -> None:
        """Test that strict mode rejects incorrect types."""
        with pytest.raises(ValidationError):
            QueryTestCase(
                query=123,  # type: ignore[arg-type]
                context_entries=["2019-01-29"],
                expected_analysis_points=["weight_progression_identified"],
                expected_response_elements=["mentions_starting_weight"],
            )


def _get_all_valid_entry_ids() -> set[str]:
    """Get all valid entry IDs from corpus."""
    entry_ids: set[str] = set()

    # from_csv entries (date-based)
    for entry_file in FROM_CSV_DIR.glob("*.md"):
        entry_ids.add(entry_file.stem)

    # synthetic entries
    for entry_file in SYNTHETIC_DIR.glob("*.md"):
        entry_ids.add(entry_file.stem)

    return entry_ids


class TestQueryTestCaseValidation:
    """Tests validating all query test case JSON files."""

    def test_query_directory_exists(self) -> None:
        """Verify query directory exists."""
        assert QUERY_DIR.exists(), f"Directory not found: {QUERY_DIR}"
        assert QUERY_DIR.is_dir(), f"Path is not a directory: {QUERY_DIR}"

    def test_minimum_test_cases_exist(self) -> None:
        """Verify at least 10 test cases exist per AC requirements."""
        json_files = list(QUERY_DIR.glob("*.json"))
        assert len(json_files) >= 10, (
            f"Expected at least 10 test cases, found {len(json_files)}"
        )

    def test_all_json_files_validate_against_schema(self) -> None:
        """Verify all JSON files parse correctly against QueryTestCase schema."""
        json_files = list(QUERY_DIR.glob("*.json"))

        for json_file in json_files:
            data = json.loads(json_file.read_text())
            test_case = QueryTestCase.model_validate(data)
            assert test_case.query, f"Empty query in {json_file.name}"
            assert test_case.context_entries, (
                f"Empty context_entries in {json_file.name}"
            )
            assert test_case.expected_analysis_points, (
                f"Empty expected_analysis_points in {json_file.name}"
            )
            assert test_case.expected_response_elements, (
                f"Empty expected_response_elements in {json_file.name}"
            )

    def test_all_context_entries_exist(self) -> None:
        """Verify all context_entries reference existing entries."""
        valid_entry_ids = _get_all_valid_entry_ids()
        json_files = list(QUERY_DIR.glob("*.json"))

        missing_entries: dict[str, list[str]] = {}

        for json_file in json_files:
            data = json.loads(json_file.read_text())
            test_case = QueryTestCase.model_validate(data)

            missing = [
                entry_id
                for entry_id in test_case.context_entries
                if entry_id not in valid_entry_ids
            ]

            if missing:
                missing_entries[json_file.name] = missing

        if missing_entries:
            error_msg = "Missing entry IDs found:\n"
            for filename, ids in missing_entries.items():
                error_msg += f"  {filename}: {ids}\n"
            pytest.fail(error_msg)


class TestQueryTestCaseRobustness:
    """Tests verifying schema handles edge cases correctly."""

    def test_rejects_invalid_analysis_point_type(self) -> None:
        """Verify invalid analysis point type is rejected by Literal constraint."""
        with pytest.raises(ValidationError):
            QueryTestCase(
                query="test query",
                context_entries=["2019-01-29"],
                expected_analysis_points=["invalid_analysis_point"],  # type: ignore[list-item]
                expected_response_elements=["mentions_starting_weight"],
            )

    def test_rejects_invalid_response_element_type(self) -> None:
        """Verify invalid response element type is rejected by Literal constraint."""
        with pytest.raises(ValidationError):
            QueryTestCase(
                query="test query",
                context_entries=["2019-01-29"],
                expected_analysis_points=["weight_progression_identified"],
                expected_response_elements=["invalid_response_element"],  # type: ignore[list-item]
            )

    def test_rejects_empty_json_object(self) -> None:
        """Verify empty JSON object fails validation."""
        with pytest.raises(ValidationError):
            QueryTestCase.model_validate({})


class TestQueryTestCaseCoverage:
    """Tests verifying coverage of different query types."""

    def test_simple_query_test_cases_exist(self) -> None:
        """Verify simple query test cases exist."""
        json_files = list(QUERY_DIR.glob("simple-*.json"))
        file_names = [f.name for f in json_files]
        assert len(json_files) >= 3, (
            f"Expected at least 3 simple test cases, found {len(json_files)}: {file_names}"
        )

    def test_complex_query_test_cases_exist(self) -> None:
        """Verify complex multi-part query test cases exist."""
        json_files = list(QUERY_DIR.glob("complex-*.json"))
        file_names = [f.name for f in json_files]
        assert len(json_files) >= 4, (
            f"Expected at least 4 complex test cases, found {len(json_files)}: {file_names}"
        )

    def test_insufficient_data_test_cases_exist(self) -> None:
        """Verify insufficient data query test cases exist."""
        json_files = list(QUERY_DIR.glob("insufficient-*.json"))
        file_names = [f.name for f in json_files]
        assert len(json_files) >= 3, (
            f"Expected at least 3 insufficient data test cases, found {len(json_files)}: {file_names}"
        )
