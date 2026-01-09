"""Tests for edge case corpus entries.

Validates the structure and integrity of domain-agnostic edge case test entries.
"""

from pathlib import Path

import pytest

from tests.corpus.schemas import EdgeCaseExpectedOutput

EDGE_CASES_DIR = Path(__file__).parent / "generic" / "edge_cases"
EXPECTED_DIR = EDGE_CASES_DIR / "expected"

VALID_CATEGORIES = {"empty", "unicode", "length", "markdown", "injection"}


class TestEdgeCaseCorpusIntegrity:
    """Verify edge case corpus structure and content."""

    def test_minimum_entry_count(self) -> None:
        """Ensure at least 20 edge case entries exist."""
        entries = list(EDGE_CASES_DIR.glob("edge-*.md"))
        assert len(entries) >= 20, f"Expected >= 20 entries, found {len(entries)}"

    def test_all_entries_have_expected_outputs(self) -> None:
        """Verify every entry has a matching expected output."""
        entries = list(EDGE_CASES_DIR.glob("edge-*.md"))
        for entry in entries:
            expected_path = EXPECTED_DIR / f"{entry.stem}.json"
            assert expected_path.exists(), f"Missing expected output for {entry.name}"

    def test_expected_outputs_are_valid(self) -> None:
        """Verify all expected outputs match schema."""
        expected_files = list(EXPECTED_DIR.glob("*.json"))
        for expected_file in expected_files:
            output = EdgeCaseExpectedOutput.model_validate_json(expected_file.read_text(encoding="utf-8"))
            assert output.category in VALID_CATEGORIES, f"Invalid category '{output.category}' in {expected_file.name}"

    @pytest.mark.parametrize(
        ("category", "min_count"),
        [
            ("empty", 5),
            ("unicode", 5),
            ("length", 4),
            ("markdown", 4),
            ("injection", 4),
        ],
    )
    def test_category_coverage(self, category: str, min_count: int) -> None:
        """Verify each category has minimum required entries."""
        entries = list(EDGE_CASES_DIR.glob(f"edge-{category}-*.md"))
        assert len(entries) >= min_count, f"Expected >= {min_count} {category} entries, found {len(entries)}"

    def test_entries_are_readable(self) -> None:
        """Verify all entries can be read as UTF-8."""
        entries = list(EDGE_CASES_DIR.glob("edge-*.md"))
        for entry in entries:
            try:
                _ = entry.read_text(encoding="utf-8")
            except UnicodeDecodeError as e:
                pytest.fail(f"Entry {entry.name} is not valid UTF-8: {e}")

    def test_expected_dir_exists(self) -> None:
        """Verify expected directory exists."""
        assert EXPECTED_DIR.exists(), "Expected directory does not exist"
        assert EXPECTED_DIR.is_dir(), "Expected path is not a directory"

    def test_no_orphan_expected_outputs(self) -> None:
        """Verify all expected outputs have matching entries."""
        expected_files = list(EXPECTED_DIR.glob("*.json"))
        for expected_file in expected_files:
            entry_path = EDGE_CASES_DIR / f"{expected_file.stem}.md"
            assert entry_path.exists(), f"Orphan expected output: {expected_file.name} has no entry"

    def test_parseable_reason_consistency(self) -> None:
        """Verify parseable=false has reason, parseable=true has reason=null."""
        expected_files = list(EXPECTED_DIR.glob("*.json"))
        for expected_file in expected_files:
            output = EdgeCaseExpectedOutput.model_validate_json(expected_file.read_text(encoding="utf-8"))
            if not output.parseable:
                assert output.reason is not None, f"{expected_file.name}: parseable=false but reason is null"
            else:
                assert output.reason is None, f"{expected_file.name}: parseable=true but reason is not null"
