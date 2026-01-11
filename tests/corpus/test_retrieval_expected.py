"""Tests for retrieval expected output schemas and test case validation.

These tests verify:
1. RetrievalTestCase schema validates correctly
2. All retrieval test case JSON files parse against schema
3. All expected_entry_ids reference existing entries
4. Minimum 15 test cases exist per AC requirements
"""

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from tests.corpus.schemas import RetrievalStrategy, RetrievalTestCase

CORPUS_ROOT = Path(__file__).parent
RETRIEVAL_DIR = CORPUS_ROOT / "fitness" / "expected" / "retrieval"
FROM_CSV_DIR = CORPUS_ROOT / "fitness" / "entries" / "from_csv"
SYNTHETIC_DIR = CORPUS_ROOT / "fitness" / "entries" / "synthetic"


class TestRetrievalStrategy:
    """Tests for RetrievalStrategy model."""

    def test_creates_date_range_strategy(self) -> None:
        """Test creating a date range strategy."""
        strategy = RetrievalStrategy(
            type="date_range",
            start="2019-01-01",
            end="2019-01-31",
        )
        assert strategy.type == "date_range"
        assert strategy.start == "2019-01-01"
        assert strategy.end == "2019-01-31"
        assert strategy.keywords == []
        assert strategy.pattern is None

    def test_creates_keyword_strategy(self) -> None:
        """Test creating a keyword strategy."""
        strategy = RetrievalStrategy(
            type="keyword",
            keywords=["deadlift", "데드리프트"],
        )
        assert strategy.type == "keyword"
        assert strategy.keywords == ["deadlift", "데드리프트"]
        assert strategy.start is None
        assert strategy.end is None

    def test_creates_pattern_strategy(self) -> None:
        """Test creating a pattern strategy."""
        strategy = RetrievalStrategy(
            type="pattern",
            pattern="Entries with weight >= 180kg",
            keywords=["deadlift"],
        )
        assert strategy.type == "pattern"
        assert strategy.pattern == "Entries with weight >= 180kg"
        assert strategy.keywords == ["deadlift"]

    def test_strict_mode_rejects_wrong_types(self) -> None:
        """Test that strict mode rejects incorrect types."""
        with pytest.raises(ValidationError):
            RetrievalStrategy(type=123)  # type: ignore[arg-type]


class TestRetrievalTestCase:
    """Tests for RetrievalTestCase model."""

    def test_creates_with_all_fields(self) -> None:
        """Test creating a test case with all fields."""
        test_case = RetrievalTestCase(
            query="deadlift workouts in January 2019",
            strategy=RetrievalStrategy(
                type="date_range",
                start="2019-01-01",
                end="2019-01-31",
                keywords=["deadlift"],
            ),
            expected_entry_ids=["2019-01-28"],
        )
        assert test_case.query == "deadlift workouts in January 2019"
        assert test_case.strategy.type == "date_range"
        assert test_case.expected_entry_ids == ["2019-01-28"]

    def test_strict_mode_rejects_wrong_types(self) -> None:
        """Test that strict mode rejects incorrect types."""
        with pytest.raises(ValidationError):
            RetrievalTestCase(
                query="test",
                strategy="not a strategy",  # type: ignore[arg-type]
                expected_entry_ids=[],
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


class TestRetrievalTestCaseValidation:
    """Tests validating all retrieval test case JSON files."""

    def test_retrieval_directory_exists(self) -> None:
        """Verify retrieval directory exists."""
        assert RETRIEVAL_DIR.exists(), f"Directory not found: {RETRIEVAL_DIR}"
        assert RETRIEVAL_DIR.is_dir(), f"Path is not a directory: {RETRIEVAL_DIR}"

    def test_minimum_test_cases_exist(self) -> None:
        """Verify at least 15 test cases exist per AC requirements."""
        json_files = list(RETRIEVAL_DIR.glob("*.json"))
        assert len(json_files) >= 15, f"Expected at least 15 test cases, found {len(json_files)}"

    def test_all_json_files_validate_against_schema(self) -> None:
        """Verify all JSON files parse correctly against RetrievalTestCase schema."""
        json_files = list(RETRIEVAL_DIR.glob("*.json"))

        for json_file in json_files:
            data = json.loads(json_file.read_text())
            test_case = RetrievalTestCase.model_validate(data)
            assert test_case.query, f"Empty query in {json_file.name}"
            assert test_case.strategy, f"Missing strategy in {json_file.name}"
            assert test_case.expected_entry_ids, f"Empty expected_entry_ids in {json_file.name}"

    def test_all_expected_entry_ids_exist(self) -> None:
        """Verify all expected_entry_ids reference existing entries."""
        valid_entry_ids = _get_all_valid_entry_ids()
        json_files = list(RETRIEVAL_DIR.glob("*.json"))

        missing_entries: dict[str, list[str]] = {}

        for json_file in json_files:
            data = json.loads(json_file.read_text())
            test_case = RetrievalTestCase.model_validate(data)

            missing = [entry_id for entry_id in test_case.expected_entry_ids if entry_id not in valid_entry_ids]

            if missing:
                missing_entries[json_file.name] = missing

        if missing_entries:
            error_msg = "Missing entry IDs found:\n"
            for filename, ids in missing_entries.items():
                error_msg += f"  {filename}: {ids}\n"
            pytest.fail(error_msg)

    def test_strategy_types_are_valid(self) -> None:
        """Verify all strategy types are one of: date_range, keyword, pattern."""
        valid_types = {"date_range", "keyword", "pattern"}
        json_files = list(RETRIEVAL_DIR.glob("*.json"))

        for json_file in json_files:
            data = json.loads(json_file.read_text())
            test_case = RetrievalTestCase.model_validate(data)
            assert test_case.strategy.type in valid_types, (
                f"Invalid strategy type '{test_case.strategy.type}' in {json_file.name}"
            )

    def test_date_range_strategies_have_dates(self) -> None:
        """Verify date_range strategies have start and end dates."""
        json_files = list(RETRIEVAL_DIR.glob("*.json"))

        for json_file in json_files:
            data = json.loads(json_file.read_text())
            test_case = RetrievalTestCase.model_validate(data)

            if test_case.strategy.type == "date_range":
                assert test_case.strategy.start, f"date_range missing start in {json_file.name}"
                assert test_case.strategy.end, f"date_range missing end in {json_file.name}"

    def test_keyword_strategies_have_keywords(self) -> None:
        """Verify keyword strategies have keywords list."""
        json_files = list(RETRIEVAL_DIR.glob("*.json"))

        for json_file in json_files:
            data = json.loads(json_file.read_text())
            test_case = RetrievalTestCase.model_validate(data)

            if test_case.strategy.type == "keyword":
                assert test_case.strategy.keywords, f"keyword strategy missing keywords in {json_file.name}"

    def test_pattern_strategies_have_pattern(self) -> None:
        """Verify pattern strategies have pattern description."""
        json_files = list(RETRIEVAL_DIR.glob("*.json"))

        for json_file in json_files:
            data = json.loads(json_file.read_text())
            test_case = RetrievalTestCase.model_validate(data)

            if test_case.strategy.type == "pattern":
                assert test_case.strategy.pattern, f"pattern strategy missing pattern in {json_file.name}"


class TestRetrievalTestCaseRobustness:
    """Tests verifying schema handles edge cases correctly."""

    def test_rejects_invalid_strategy_type(self) -> None:
        """Verify invalid strategy type is rejected by Literal constraint."""
        with pytest.raises(ValidationError):
            RetrievalStrategy(type="invalid_type")  # type: ignore[arg-type]

    def test_rejects_empty_json_object(self) -> None:
        """Verify empty JSON object fails validation."""
        with pytest.raises(ValidationError):
            RetrievalTestCase.model_validate({})


class TestRetrievalTestCaseCoverage:
    """Tests verifying coverage of different retrieval scenarios."""

    def test_date_range_test_cases_exist(self) -> None:
        """Verify date-based retrieval test cases exist."""
        json_files = list(RETRIEVAL_DIR.glob("date-range-*.json"))
        assert len(json_files) >= 3, f"Expected at least 3 date-range test cases, found {len(json_files)}"

    def test_keyword_test_cases_exist(self) -> None:
        """Verify keyword-based retrieval test cases exist."""
        json_files = list(RETRIEVAL_DIR.glob("keyword-*.json"))
        assert len(json_files) >= 3, f"Expected at least 3 keyword test cases, found {len(json_files)}"

    def test_pattern_test_cases_exist(self) -> None:
        """Verify pattern matching test cases exist."""
        json_files = list(RETRIEVAL_DIR.glob("pattern-*.json"))
        assert len(json_files) >= 3, f"Expected at least 3 pattern test cases, found {len(json_files)}"
