"""Tests for human-curated fitness corpus entries.

Validates the structure and integrity of human-written fitness test entries
that test Parser handling of natural human writing styles.
"""

from pathlib import Path

import pytest

from tests.corpus.schemas import ExpectedParserOutput

HUMAN_ENTRIES_DIR = Path(__file__).parent / "fitness" / "entries" / "human"
HUMAN_EXPECTED_DIR = Path(__file__).parent / "fitness" / "expected" / "parser" / "human"


class TestHumanEntriesCorpusIntegrity:
    """Verify human entry corpus structure and content."""

    def test_directories_exist(self) -> None:
        """Verify entry and expected directories exist (AC #1, #2)."""
        assert HUMAN_ENTRIES_DIR.exists(), "Human entries directory does not exist"
        assert HUMAN_ENTRIES_DIR.is_dir(), "Human entries path is not a directory"
        assert HUMAN_EXPECTED_DIR.exists(), "Human expected directory does not exist"
        assert HUMAN_EXPECTED_DIR.is_dir(), "Human expected path is not a directory"

    def test_minimum_entry_count(self) -> None:
        """Ensure at least 15 human entries exist (AC #9)."""
        entries = list(HUMAN_ENTRIES_DIR.glob("human-*.md"))
        assert len(entries) >= 15, f"Expected >= 15 entries, found {len(entries)}"

    @pytest.mark.parametrize(
        ("category", "min_count"),
        [
            ("stream", 5),
            ("casual", 5),
            ("detailed", 5),
        ],
    )
    def test_category_coverage(self, category: str, min_count: int) -> None:
        """Verify each category has minimum required entries (AC #4, #5, #6)."""
        entries = list(HUMAN_ENTRIES_DIR.glob(f"human-{category}-*.md"))
        assert (
            len(entries) >= min_count
        ), f"Expected >= {min_count} {category} entries, found {len(entries)}"

    def test_all_entries_have_expected_outputs(self) -> None:
        """Verify every entry has a matching expected output (AC #8)."""
        entries = list(HUMAN_ENTRIES_DIR.glob("human-*.md"))
        for entry in entries:
            expected_path = HUMAN_EXPECTED_DIR / f"{entry.stem}.json"
            assert expected_path.exists(), f"Missing expected output for {entry.name}"

    def test_expected_outputs_are_valid(self) -> None:
        """Verify all expected outputs match ExpectedParserOutput schema (AC #8)."""
        expected_files = list(HUMAN_EXPECTED_DIR.glob("*.json"))
        for expected_file in expected_files:
            output = ExpectedParserOutput.model_validate_json(
                expected_file.read_text(encoding="utf-8")
            )
            assert (
                output.date == "human"
            ), f"{expected_file.name}: date should be 'human'"

    def test_no_orphan_expected_outputs(self) -> None:
        """Verify all expected outputs have matching entries."""
        expected_files = list(HUMAN_EXPECTED_DIR.glob("*.json"))
        for expected_file in expected_files:
            entry_path = HUMAN_ENTRIES_DIR / f"{expected_file.stem}.md"
            assert (
                entry_path.exists()
            ), f"Orphan expected output: {expected_file.name} has no entry"

    def test_entries_are_readable(self) -> None:
        """Verify all entries can be read as UTF-8."""
        entries = list(HUMAN_ENTRIES_DIR.glob("human-*.md"))
        for entry in entries:
            try:
                _ = entry.read_text(encoding="utf-8")
            except UnicodeDecodeError as e:
                pytest.fail(f"Entry {entry.name} is not valid UTF-8: {e}")
