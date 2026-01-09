"""Tests for JournalDomain module instantiation and validation.

Validates that JournalDomain correctly implements DomainModule interface
and that JournalEntry schema validates against expected outputs.
"""

import json
from pathlib import Path

import pytest
from quilto import DomainModule

from tests.corpus.schemas import JournalEntry
from tests.domains import JournalDomain, journal_domain

JOURNAL_EXPECTED_DIR: Path = (
    Path(__file__).parent.parent
    / "corpus"
    / "multi_domain"
    / "expected"
    / "parser"
    / "journal"
)


class TestJournalDomainInstantiation:
    """Test JournalDomain instantiates correctly as test infrastructure."""

    def test_instantiates_without_error(self) -> None:
        """JournalDomain singleton exists and is valid."""
        assert journal_domain is not None
        assert isinstance(journal_domain, DomainModule)

    def test_is_journal_domain_class(self) -> None:
        """journal_domain is an instance of JournalDomain class."""
        assert isinstance(journal_domain, JournalDomain)

    def test_name_defaults_to_class_name(self) -> None:
        """Name field defaults to 'JournalDomain'."""
        assert journal_domain.name == "JournalDomain"

    def test_description_is_populated(self) -> None:
        """Description field is non-empty."""
        assert journal_domain.description
        assert "journal" in journal_domain.description.lower()

    def test_log_schema_is_journal_entry(self) -> None:
        """log_schema is JournalEntry class."""
        assert journal_domain.log_schema is JournalEntry

    def test_vocabulary_is_populated(self) -> None:
        """Vocabulary contains expected terms."""
        assert journal_domain.vocabulary
        assert isinstance(journal_domain.vocabulary, dict)

    def test_vocabulary_has_english_terms(self) -> None:
        """Vocabulary includes English emotional terms."""
        english_terms = ["felt", "stressed", "anxious", "happy", "sad", "tired"]
        for term in english_terms:
            assert term in journal_domain.vocabulary, f"Missing English term: {term}"

    def test_vocabulary_has_korean_terms(self) -> None:
        """Vocabulary includes Korean emotional terms."""
        korean_terms = ["기분", "스트레스", "피곤", "행복"]
        for term in korean_terms:
            assert term in journal_domain.vocabulary, f"Missing Korean term: {term}"

    def test_vocabulary_has_activity_terms(self) -> None:
        """Vocabulary includes activity terms (English and Korean)."""
        activity_terms = ["met", "talked", "만남"]
        for term in activity_terms:
            assert term in journal_domain.vocabulary, f"Missing activity term: {term}"

    def test_expertise_is_populated(self) -> None:
        """Expertise field is non-empty."""
        assert journal_domain.expertise
        assert "emotional" in journal_domain.expertise.lower()

    def test_optional_fields_have_defaults(self) -> None:
        """Optional DomainModule fields have expected default values."""
        assert journal_domain.response_evaluation_rules == []
        assert journal_domain.context_management_guidance == ""

    def test_direct_instantiation(self) -> None:
        """JournalDomain can be instantiated directly (not just singleton)."""
        custom = JournalDomain(
            description="Test description",
            log_schema=JournalEntry,
            vocabulary={"test": "value"},
        )
        assert custom.name == "JournalDomain"
        assert custom.description == "Test description"
        assert custom.log_schema is JournalEntry


class TestJournalEntryValidation:
    """Test JournalEntry validates expected outputs."""

    def test_expected_dir_has_json_files(self) -> None:
        """Verify expected directory exists and contains JSON files."""
        assert JOURNAL_EXPECTED_DIR.exists(), f"Directory not found: {JOURNAL_EXPECTED_DIR}"
        json_files = list(JOURNAL_EXPECTED_DIR.glob("*.json"))
        assert len(json_files) > 0, f"No JSON files found in {JOURNAL_EXPECTED_DIR}"

    @pytest.mark.parametrize(
        "json_file",
        sorted(JOURNAL_EXPECTED_DIR.glob("*.json")),
        ids=lambda p: p.stem,
    )
    def test_expected_output_validates(self, json_file: Path) -> None:
        """Each journal expected JSON validates against JournalEntry schema."""
        with open(json_file) as f:
            data = json.load(f)
        entry = JournalEntry.model_validate(data)
        assert entry is not None
