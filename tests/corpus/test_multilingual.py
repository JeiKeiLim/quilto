"""Tests for multilingual corpus entries.

Validates the structure and integrity of domain-agnostic multilingual test entries.
"""

from pathlib import Path

import pytest

from tests.corpus.schemas import MultilingualExpectedOutput

MULTILINGUAL_DIR = Path(__file__).parent / "generic" / "multilingual"
EXPECTED_DIR = MULTILINGUAL_DIR / "expected"

VALID_CATEGORIES = {"lang", "mixed", "number", "date"}
VALID_LANGUAGES = {"en", "ko"}  # Only these two languages in this corpus


class TestMultilingualCorpusIntegrity:
    """Verify multilingual corpus structure and content."""

    def test_minimum_entry_count(self) -> None:
        """Ensure at least 15 multilingual entries exist."""
        entries = list(MULTILINGUAL_DIR.glob("multi-*.md"))
        assert len(entries) >= 15, f"Expected >= 15 entries, found {len(entries)}"

    def test_all_entries_have_expected_outputs(self) -> None:
        """Verify every entry has a matching expected output."""
        entries = list(MULTILINGUAL_DIR.glob("multi-*.md"))
        for entry in entries:
            expected_path = EXPECTED_DIR / f"{entry.stem}.json"
            assert expected_path.exists(), f"Missing expected output for {entry.name}"

    def test_no_orphan_expected_files(self) -> None:
        """Verify no expected output exists without a corresponding entry."""
        expected_files = list(EXPECTED_DIR.glob("*.json"))
        for expected_file in expected_files:
            entry_path = MULTILINGUAL_DIR / f"{expected_file.stem}.md"
            assert entry_path.exists(), f"Orphan expected output: {expected_file.name}"

    def test_expected_outputs_are_valid(self) -> None:
        """Verify all expected outputs match schema."""
        expected_files = list(EXPECTED_DIR.glob("*.json"))
        for expected_file in expected_files:
            output = MultilingualExpectedOutput.model_validate_json(expected_file.read_text(encoding="utf-8"))
            assert output.category in VALID_CATEGORIES, f"Invalid category '{output.category}' in {expected_file.name}"

    @pytest.mark.parametrize(
        ("category", "min_count"),
        [
            ("lang", 4),
            ("mixed", 4),
            ("number", 4),
            ("date", 5),  # date has 5 entries (01-05)
        ],
    )
    def test_category_coverage(self, category: str, min_count: int) -> None:
        """Verify each category has minimum required entries."""
        entries = list(MULTILINGUAL_DIR.glob(f"multi-{category}-*.md"))
        assert len(entries) >= min_count, f"Expected >= {min_count} {category} entries, found {len(entries)}"

    def test_files_are_utf8_readable(self) -> None:
        """Verify all entry files can be read as UTF-8."""
        entries = list(MULTILINGUAL_DIR.glob("multi-*.md"))
        for entry in entries:
            try:
                content = entry.read_text(encoding="utf-8")
                assert len(content) > 0, f"Entry {entry.name} is empty"
            except UnicodeDecodeError as e:
                pytest.fail(f"Entry {entry.name} is not valid UTF-8: {e}")

    def test_language_detected_valid(self) -> None:
        """Verify all expected outputs have valid languages detected."""
        expected_files = list(EXPECTED_DIR.glob("*.json"))
        for expected_file in expected_files:
            output = MultilingualExpectedOutput.model_validate_json(expected_file.read_text(encoding="utf-8"))
            assert len(output.language_detected) > 0, f"No language detected in {expected_file.name}"
            for lang in output.language_detected:
                assert lang in VALID_LANGUAGES, f"Invalid language '{lang}' in {expected_file.name}"

    def test_mixed_category_has_multiple_languages(self) -> None:
        """Verify mixed category entries detect both languages."""
        mixed_expected = list(EXPECTED_DIR.glob("multi-mixed-*.json"))
        for expected_file in mixed_expected:
            output = MultilingualExpectedOutput.model_validate_json(expected_file.read_text(encoding="utf-8"))
            assert len(output.language_detected) >= 2, (
                f"Mixed entry {expected_file.name} should detect multiple languages"
            )

    def test_files_have_trailing_newline(self) -> None:
        """Verify all text files end with a trailing newline."""
        all_files = list(MULTILINGUAL_DIR.glob("*.md")) + list(EXPECTED_DIR.glob("*.json"))
        for file_path in all_files:
            content = file_path.read_bytes()
            if len(content) > 0:
                assert content.endswith(b"\n"), f"File {file_path.name} missing trailing newline"
