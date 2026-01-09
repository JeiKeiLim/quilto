"""Tests for multi-domain expected output validation.

Validates that all expected JSON files in multi_domain/expected/parser/
can be successfully validated by their corresponding Pydantic schemas.
"""

import json
from pathlib import Path

import pytest

from tests.corpus.schemas import CookingEntry, JournalEntry, StudyEntry

CORPUS_PATH = Path(__file__).parent.parent / "multi_domain" / "expected" / "parser"


def get_json_files(domain: str) -> list[Path]:
    """Get all JSON files for a domain."""
    domain_path = CORPUS_PATH / domain
    if not domain_path.exists():
        return []
    return sorted(domain_path.glob("*.json"))


class TestJournalValidation:
    """Test journal expected outputs validate against JournalEntry schema."""

    @pytest.mark.parametrize(
        "json_file",
        get_json_files("journal"),
        ids=lambda p: p.stem,
    )
    def test_journal_entry_validates(self, json_file: Path) -> None:
        """Each journal JSON file validates against JournalEntry schema."""
        with open(json_file) as f:
            data = json.load(f)
        entry = JournalEntry.model_validate(data)
        assert entry is not None


class TestCookingValidation:
    """Test cooking expected outputs validate against CookingEntry schema."""

    @pytest.mark.parametrize(
        "json_file",
        get_json_files("cooking"),
        ids=lambda p: p.stem,
    )
    def test_cooking_entry_validates(self, json_file: Path) -> None:
        """Each cooking JSON file validates against CookingEntry schema."""
        with open(json_file) as f:
            data = json.load(f)
        entry = CookingEntry.model_validate(data)
        assert entry is not None
        assert entry.dish_name  # dish_name is required


class TestStudyValidation:
    """Test study expected outputs validate against StudyEntry schema."""

    @pytest.mark.parametrize(
        "json_file",
        get_json_files("study"),
        ids=lambda p: p.stem,
    )
    def test_study_entry_validates(self, json_file: Path) -> None:
        """Each study JSON file validates against StudyEntry schema."""
        with open(json_file) as f:
            data = json.load(f)
        entry = StudyEntry.model_validate(data)
        assert entry is not None
        assert entry.subject  # subject is required


class TestFileCount:
    """Test that all expected files exist."""

    def test_journal_file_count(self) -> None:
        """Verify 12 journal expected output files exist."""
        files = get_json_files("journal")
        assert len(files) == 12, f"Expected 12 journal files, found {len(files)}"

    def test_cooking_file_count(self) -> None:
        """Verify 12 cooking expected output files exist."""
        files = get_json_files("cooking")
        assert len(files) == 12, f"Expected 12 cooking files, found {len(files)}"

    def test_study_file_count(self) -> None:
        """Verify 12 study expected output files exist."""
        files = get_json_files("study")
        assert len(files) == 12, f"Expected 12 study files, found {len(files)}"

    def test_total_file_count(self) -> None:
        """Verify 36 total expected output files exist."""
        journal = get_json_files("journal")
        cooking = get_json_files("cooking")
        study = get_json_files("study")
        total = len(journal) + len(cooking) + len(study)
        assert total == 36, f"Expected 36 total files, found {total}"
