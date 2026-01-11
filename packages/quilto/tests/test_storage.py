"""Comprehensive tests for the storage module."""

import json
from datetime import date, datetime
from pathlib import Path
from typing import Any

import pytest
from quilto.agents.models import ParserOutput
from quilto.storage import DateRange, Entry, StorageRepository


def create_parser_output(
    is_correction: bool = False,
    target_entry_id: str | None = None,
    correction_delta: dict[str, Any] | None = None,
) -> ParserOutput:
    """Create a valid ParserOutput for testing correction flows.

    Args:
        is_correction: Whether this is a correction output.
        target_entry_id: ID of entry being corrected.
        correction_delta: Fields that changed.

    Returns:
        Valid ParserOutput instance.
    """
    return ParserOutput(
        date=date(2026, 1, 1),
        timestamp=datetime(2026, 1, 1, 10, 30, 0),
        domain_data={},
        raw_content="test content",
        confidence=0.9,
        is_correction=is_correction,
        target_entry_id=target_entry_id,
        correction_delta=correction_delta,
    )


class TestStorageRepositoryInit:
    """Tests for StorageRepository initialization."""

    def test_init_creates_directories(self, tmp_path: Path) -> None:
        """Test that initialization creates required directory structure."""
        repo = StorageRepository(tmp_path)

        assert (tmp_path / "logs" / "raw").exists()
        assert (tmp_path / "logs" / "parsed").exists()
        assert (tmp_path / "logs" / "context").exists()
        assert repo.base_path == tmp_path

    def test_init_with_existing_directories(self, tmp_path: Path) -> None:
        """Test initialization doesn't fail when directories already exist."""
        (tmp_path / "logs" / "raw").mkdir(parents=True)
        (tmp_path / "logs" / "parsed").mkdir(parents=True)
        (tmp_path / "logs" / "context").mkdir(parents=True)

        repo = StorageRepository(tmp_path)
        assert repo.base_path == tmp_path


class TestEntryModel:
    """Tests for Entry model validation."""

    def test_entry_creation(self) -> None:
        """Test creating a valid Entry."""
        entry = Entry(
            id="2026-01-01_10-30-00",
            date=date(2026, 1, 1),
            timestamp=datetime(2026, 1, 1, 10, 30),
            raw_content="Test content",
        )
        assert entry.id == "2026-01-01_10-30-00"
        assert entry.parsed_data is None

    def test_entry_with_parsed_data(self) -> None:
        """Test Entry with parsed data."""
        entry = Entry(
            id="2026-01-01_10-30-00",
            date=date(2026, 1, 1),
            timestamp=datetime(2026, 1, 1, 10, 30),
            raw_content="Test content",
            parsed_data={"exercise": "bench press", "weight": 100},
        )
        assert entry.parsed_data == {"exercise": "bench press", "weight": 100}


class TestDateRangeModel:
    """Tests for DateRange model validation."""

    def test_valid_date_range(self) -> None:
        """Test creating a valid DateRange."""
        dr = DateRange(start=date(2026, 1, 1), end=date(2026, 1, 31))
        assert dr.start == date(2026, 1, 1)
        assert dr.end == date(2026, 1, 31)

    def test_same_start_end(self) -> None:
        """Test DateRange with same start and end date."""
        dr = DateRange(start=date(2026, 1, 1), end=date(2026, 1, 1))
        assert dr.start == dr.end

    def test_invalid_date_range(self) -> None:
        """Test that start > end raises ValueError."""
        with pytest.raises(ValueError, match="start must be <= end"):
            DateRange(start=date(2026, 1, 31), end=date(2026, 1, 1))


class TestParserOutputModel:
    """Tests for ParserOutput model (full version from agents)."""

    def test_default_correction_values(self) -> None:
        """Test ParserOutput default correction values."""
        output = create_parser_output()
        assert output.is_correction is False
        assert output.target_entry_id is None
        assert output.correction_delta is None

    def test_correction_output(self) -> None:
        """Test ParserOutput with correction data."""
        output = create_parser_output(
            is_correction=True,
            target_entry_id="2026-01-01_10-30-00",
            correction_delta={"weight": 185},
        )
        assert output.is_correction is True
        assert output.target_entry_id == "2026-01-01_10-30-00"
        assert output.correction_delta == {"weight": 185}


class TestGetEntriesByDateRange:
    """Tests for date range retrieval."""

    def test_empty_date_range(self, tmp_path: Path) -> None:
        """Test retrieving from empty storage returns empty list."""
        repo = StorageRepository(tmp_path)
        entries = repo.get_entries_by_date_range(date(2026, 1, 1), date(2026, 1, 5))
        assert entries == []

    def test_single_day_entries(self, tmp_path: Path) -> None:
        """Test retrieving entries from a single day."""
        repo = StorageRepository(tmp_path)

        # Create raw file
        raw_dir = tmp_path / "logs" / "raw" / "2026" / "01"
        raw_dir.mkdir(parents=True)
        raw_file = raw_dir / "2026-01-01.md"
        raw_file.write_text("## 10:30\nFirst entry\n\n## 14:00\nSecond entry\n")

        entries = repo.get_entries_by_date_range(date(2026, 1, 1), date(2026, 1, 1))

        assert len(entries) == 2
        assert entries[0].raw_content == "First entry"
        assert entries[1].raw_content == "Second entry"
        assert entries[0].timestamp < entries[1].timestamp

    def test_multiple_days(self, tmp_path: Path) -> None:
        """Test retrieving entries across multiple days."""
        repo = StorageRepository(tmp_path)

        # Create raw files for two days
        raw_dir = tmp_path / "logs" / "raw" / "2026" / "01"
        raw_dir.mkdir(parents=True)

        (raw_dir / "2026-01-01.md").write_text("## 10:30\nDay 1 entry\n")
        (raw_dir / "2026-01-02.md").write_text("## 09:00\nDay 2 entry\n")

        entries = repo.get_entries_by_date_range(date(2026, 1, 1), date(2026, 1, 2))

        assert len(entries) == 2
        assert entries[0].date == date(2026, 1, 1)
        assert entries[1].date == date(2026, 1, 2)

    def test_with_parsed_data(self, tmp_path: Path) -> None:
        """Test that parsed data is loaded when available."""
        repo = StorageRepository(tmp_path)

        # Create raw file
        raw_dir = tmp_path / "logs" / "raw" / "2026" / "01"
        raw_dir.mkdir(parents=True)
        (raw_dir / "2026-01-01.md").write_text("## 10:30\nBench press 185\n")

        # Create parsed file
        parsed_dir = tmp_path / "logs" / "parsed" / "2026" / "01"
        parsed_dir.mkdir(parents=True)
        parsed_data = {"2026-01-01_10-30-00": {"exercise": "bench press", "weight": 185}}
        (parsed_dir / "2026-01-01.json").write_text(json.dumps(parsed_data))

        entries = repo.get_entries_by_date_range(date(2026, 1, 1), date(2026, 1, 1))

        assert len(entries) == 1
        assert entries[0].parsed_data == {"exercise": "bench press", "weight": 185}


class TestGetEntriesByPattern:
    """Tests for pattern-based retrieval."""

    def test_specific_month_pattern(self, tmp_path: Path) -> None:
        """Test glob pattern for specific month."""
        repo = StorageRepository(tmp_path)

        # Create files in two months
        jan_dir = tmp_path / "logs" / "raw" / "2026" / "01"
        feb_dir = tmp_path / "logs" / "raw" / "2026" / "02"
        jan_dir.mkdir(parents=True)
        feb_dir.mkdir(parents=True)

        (jan_dir / "2026-01-15.md").write_text("## 10:00\nJanuary entry\n")
        (feb_dir / "2026-02-15.md").write_text("## 10:00\nFebruary entry\n")

        entries = repo.get_entries_by_pattern("2026/01/**/*.md")

        assert len(entries) == 1
        assert entries[0].raw_content == "January entry"

    def test_wildcard_year_pattern(self, tmp_path: Path) -> None:
        """Test wildcard pattern across years."""
        repo = StorageRepository(tmp_path)

        # Create files in different years
        dir_2025 = tmp_path / "logs" / "raw" / "2025" / "12"
        dir_2026 = tmp_path / "logs" / "raw" / "2026" / "01"
        dir_2025.mkdir(parents=True)
        dir_2026.mkdir(parents=True)

        (dir_2025 / "2025-12-31.md").write_text("## 10:00\n2025 entry\n")
        (dir_2026 / "2026-01-01.md").write_text("## 10:00\n2026 entry\n")

        entries = repo.get_entries_by_pattern("**/*.md")

        assert len(entries) == 2

    def test_no_matches(self, tmp_path: Path) -> None:
        """Test pattern with no matches returns empty list."""
        repo = StorageRepository(tmp_path)
        entries = repo.get_entries_by_pattern("2099/**/*.md")
        assert entries == []


class TestSearchEntries:
    """Tests for keyword search."""

    def test_single_keyword_match(self, tmp_path: Path) -> None:
        """Test searching with a single keyword."""
        repo = StorageRepository(tmp_path)

        raw_dir = tmp_path / "logs" / "raw" / "2026" / "01"
        raw_dir.mkdir(parents=True)
        (raw_dir / "2026-01-01.md").write_text("## 10:00\nBench press 185\n\n## 11:00\nSquat 200\n")

        entries = repo.search_entries(["bench"])

        assert len(entries) == 1
        assert "bench" in entries[0].raw_content.lower()

    def test_match_all_true(self, tmp_path: Path) -> None:
        """Test AND logic with match_all=True."""
        repo = StorageRepository(tmp_path)

        raw_dir = tmp_path / "logs" / "raw" / "2026" / "01"
        raw_dir.mkdir(parents=True)
        (raw_dir / "2026-01-01.md").write_text("## 10:00\nBench press 185\n\n## 11:00\nBench and squat workout\n")

        entries = repo.search_entries(["bench", "squat"], match_all=True)

        assert len(entries) == 1
        assert "bench" in entries[0].raw_content.lower()
        assert "squat" in entries[0].raw_content.lower()

    def test_match_all_false(self, tmp_path: Path) -> None:
        """Test OR logic with match_all=False."""
        repo = StorageRepository(tmp_path)

        raw_dir = tmp_path / "logs" / "raw" / "2026" / "01"
        raw_dir.mkdir(parents=True)
        (raw_dir / "2026-01-01.md").write_text("## 10:00\nBench press 185\n\n## 11:00\nSquat 200\n")

        entries = repo.search_entries(["bench", "squat"], match_all=False)

        assert len(entries) == 2

    def test_case_insensitive(self, tmp_path: Path) -> None:
        """Test that search is case-insensitive."""
        repo = StorageRepository(tmp_path)

        raw_dir = tmp_path / "logs" / "raw" / "2026" / "01"
        raw_dir.mkdir(parents=True)
        (raw_dir / "2026-01-01.md").write_text("## 10:00\nBENCH PRESS workout\n")

        entries = repo.search_entries(["bench"])

        assert len(entries) == 1

    def test_with_date_range_filter(self, tmp_path: Path) -> None:
        """Test search with date_range parameter."""
        repo = StorageRepository(tmp_path)

        raw_dir = tmp_path / "logs" / "raw" / "2026" / "01"
        raw_dir.mkdir(parents=True)
        (raw_dir / "2026-01-01.md").write_text("## 10:00\nBench press\n")
        (raw_dir / "2026-01-15.md").write_text("## 10:00\nBench press again\n")

        date_range = DateRange(start=date(2026, 1, 1), end=date(2026, 1, 10))
        entries = repo.search_entries(["bench"], date_range=date_range)

        assert len(entries) == 1
        assert entries[0].date == date(2026, 1, 1)

    def test_no_matches(self, tmp_path: Path) -> None:
        """Test search with no matches."""
        repo = StorageRepository(tmp_path)

        raw_dir = tmp_path / "logs" / "raw" / "2026" / "01"
        raw_dir.mkdir(parents=True)
        (raw_dir / "2026-01-01.md").write_text("## 10:00\nBench press 185\n")

        entries = repo.search_entries(["deadlift"])

        assert entries == []


class TestSaveEntry:
    """Tests for saving entries."""

    def test_save_new_entry(self, tmp_path: Path) -> None:
        """Test saving a new entry creates files."""
        repo = StorageRepository(tmp_path)

        entry = Entry(
            id="2026-01-01_10-30-00",
            date=date(2026, 1, 1),
            timestamp=datetime(2026, 1, 1, 10, 30),
            raw_content="Bench press 185 lbs",
            parsed_data={"exercise": "bench press", "weight": 185},
        )

        repo.save_entry(entry)

        # Check raw file
        raw_path = tmp_path / "logs" / "raw" / "2026" / "01" / "2026-01-01.md"
        assert raw_path.exists()
        content = raw_path.read_text()
        assert "## 10:30" in content
        assert "Bench press 185 lbs" in content

        # Check parsed file
        parsed_path = tmp_path / "logs" / "parsed" / "2026" / "01" / "2026-01-01.json"
        assert parsed_path.exists()
        parsed_data = json.loads(parsed_path.read_text())
        assert "2026-01-01_10-30-00" in parsed_data

    def test_append_to_existing_day(self, tmp_path: Path) -> None:
        """Test appending entry to existing day."""
        repo = StorageRepository(tmp_path)

        # Save first entry
        entry1 = Entry(
            id="2026-01-01_10-30-00",
            date=date(2026, 1, 1),
            timestamp=datetime(2026, 1, 1, 10, 30),
            raw_content="First entry",
        )
        repo.save_entry(entry1)

        # Save second entry
        entry2 = Entry(
            id="2026-01-01_14-00-00",
            date=date(2026, 1, 1),
            timestamp=datetime(2026, 1, 1, 14, 0),
            raw_content="Second entry",
        )
        repo.save_entry(entry2)

        raw_path = tmp_path / "logs" / "raw" / "2026" / "01" / "2026-01-01.md"
        content = raw_path.read_text()

        assert "## 10:30" in content
        assert "First entry" in content
        assert "## 14:00" in content
        assert "Second entry" in content

    def test_save_without_parsed_data(self, tmp_path: Path) -> None:
        """Test saving entry without parsed data doesn't create parsed file."""
        repo = StorageRepository(tmp_path)

        entry = Entry(
            id="2026-01-01_10-30-00",
            date=date(2026, 1, 1),
            timestamp=datetime(2026, 1, 1, 10, 30),
            raw_content="Just a note",
        )
        repo.save_entry(entry)

        parsed_path = tmp_path / "logs" / "parsed" / "2026" / "01" / "2026-01-01.json"
        assert not parsed_path.exists()


class TestCorrections:
    """Tests for correction flow."""

    def test_save_correction_appends_note(self, tmp_path: Path) -> None:
        """Test that corrections append a note to raw markdown."""
        repo = StorageRepository(tmp_path)

        # Save original entry
        original = Entry(
            id="2026-01-01_10-30-00",
            date=date(2026, 1, 1),
            timestamp=datetime(2026, 1, 1, 10, 30),
            raw_content="Bench press 85 lbs",
            parsed_data={"exercise": "bench press", "weight": 85},
        )
        repo.save_entry(original)

        # Save correction
        correction_entry = Entry(
            id="2026-01-01_10-45-00",
            date=date(2026, 1, 1),
            timestamp=datetime(2026, 1, 1, 10, 45),
            raw_content="Correction: bench weight was 185, not 85",
        )
        correction = create_parser_output(
            is_correction=True,
            target_entry_id="2026-01-01_10-30-00",
            correction_delta={"weight": 185},
        )
        repo.save_entry(correction_entry, correction=correction)

        # Check raw file has correction marker
        raw_path = tmp_path / "logs" / "raw" / "2026" / "01" / "2026-01-01.md"
        content = raw_path.read_text()
        assert "[correction]" in content

        # Check parsed data was updated
        parsed_path = tmp_path / "logs" / "parsed" / "2026" / "01" / "2026-01-01.json"
        parsed = json.loads(parsed_path.read_text())
        assert parsed["2026-01-01_10-30-00"]["weight"] == 185

    def test_correction_upsert_creates_if_missing(self, tmp_path: Path) -> None:
        """Test correction creates parsed entry if it doesn't exist."""
        repo = StorageRepository(tmp_path)

        # Create raw file manually (no save_entry)
        raw_dir = tmp_path / "logs" / "raw" / "2026" / "01"
        raw_dir.mkdir(parents=True)
        (raw_dir / "2026-01-01.md").write_text("## 10:30\nOriginal content\n")

        # Save correction for entry that has no parsed data
        correction_entry = Entry(
            id="2026-01-01_10-45-00",
            date=date(2026, 1, 1),
            timestamp=datetime(2026, 1, 1, 10, 45),
            raw_content="Correction note",
        )
        correction = create_parser_output(
            is_correction=True,
            target_entry_id="2026-01-01_10-30-00",
            correction_delta={"weight": 185},
        )
        repo.save_entry(correction_entry, correction=correction)

        parsed_path = tmp_path / "logs" / "parsed" / "2026" / "01" / "2026-01-01.json"
        parsed = json.loads(parsed_path.read_text())
        assert parsed["2026-01-01_10-30-00"]["weight"] == 185


class TestGlobalContext:
    """Tests for global context operations."""

    def test_get_empty_context(self, tmp_path: Path) -> None:
        """Test getting context when file doesn't exist."""
        repo = StorageRepository(tmp_path)
        context = repo.get_global_context()
        assert context == ""

    def test_update_and_get_context(self, tmp_path: Path) -> None:
        """Test updating and retrieving context."""
        repo = StorageRepository(tmp_path)

        repo.update_global_context("User prefers kg over lbs.")
        context = repo.get_global_context()

        assert context == "User prefers kg over lbs."

    def test_update_overwrites(self, tmp_path: Path) -> None:
        """Test that update overwrites existing content."""
        repo = StorageRepository(tmp_path)

        repo.update_global_context("First content")
        repo.update_global_context("Second content")

        context = repo.get_global_context()
        assert context == "Second content"
        assert "First" not in context

    def test_context_file_location(self, tmp_path: Path) -> None:
        """Test context is saved to correct location."""
        repo = StorageRepository(tmp_path)
        repo.update_global_context("Test content")

        context_path = tmp_path / "logs" / "context" / "global.md"
        assert context_path.exists()
        assert context_path.read_text() == "Test content"


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_init_with_file_raises_error(self, tmp_path: Path) -> None:
        """Test that initializing with a file path raises NotADirectoryError."""
        file_path = tmp_path / "not_a_directory.txt"
        file_path.write_text("I am a file")

        with pytest.raises(NotADirectoryError, match="must be a directory"):
            StorageRepository(file_path)

    def test_empty_keywords_raises_error(self, tmp_path: Path) -> None:
        """Test that empty keywords list raises ValueError."""
        repo = StorageRepository(tmp_path)

        with pytest.raises(ValueError, match="keywords list must not be empty"):
            repo.search_entries([])

    def test_date_range_spanning_year_boundary(self, tmp_path: Path) -> None:
        """Test retrieval across year boundary."""
        repo = StorageRepository(tmp_path)

        # Create files in two years
        dec_dir = tmp_path / "logs" / "raw" / "2025" / "12"
        jan_dir = tmp_path / "logs" / "raw" / "2026" / "01"
        dec_dir.mkdir(parents=True)
        jan_dir.mkdir(parents=True)

        (dec_dir / "2025-12-31.md").write_text("## 23:59\nLast entry of 2025\n")
        (jan_dir / "2026-01-01.md").write_text("## 00:01\nFirst entry of 2026\n")

        entries = repo.get_entries_by_date_range(date(2025, 12, 31), date(2026, 1, 1))

        assert len(entries) == 2
        assert entries[0].date == date(2025, 12, 31)
        assert entries[1].date == date(2026, 1, 1)

    def test_date_range_spanning_month_boundary(self, tmp_path: Path) -> None:
        """Test retrieval across month boundary."""
        repo = StorageRepository(tmp_path)

        # Create files in two months
        jan_dir = tmp_path / "logs" / "raw" / "2026" / "01"
        feb_dir = tmp_path / "logs" / "raw" / "2026" / "02"
        jan_dir.mkdir(parents=True)
        feb_dir.mkdir(parents=True)

        (jan_dir / "2026-01-31.md").write_text("## 10:00\nLast day of January\n")
        (feb_dir / "2026-02-01.md").write_text("## 10:00\nFirst day of February\n")

        entries = repo.get_entries_by_date_range(date(2026, 1, 31), date(2026, 2, 1))

        assert len(entries) == 2
        assert entries[0].date == date(2026, 1, 31)
        assert entries[1].date == date(2026, 2, 1)

    def test_empty_section_is_skipped(self, tmp_path: Path) -> None:
        """Test that sections with empty content are skipped."""
        repo = StorageRepository(tmp_path)

        raw_dir = tmp_path / "logs" / "raw" / "2026" / "01"
        raw_dir.mkdir(parents=True)
        # Second section has only whitespace
        (raw_dir / "2026-01-01.md").write_text("## 10:00\nActual content\n\n## 11:00\n   \n\n## 12:00\nAnother entry\n")

        entries = repo.get_entries_by_date_range(date(2026, 1, 1), date(2026, 1, 1))

        # Only 2 entries (10:00 and 12:00), 11:00 is skipped
        assert len(entries) == 2
        assert entries[0].raw_content == "Actual content"
        assert entries[1].raw_content == "Another entry"

    def test_pattern_with_correction_entries(self, tmp_path: Path) -> None:
        """Test that pattern retrieval handles correction entries."""
        repo = StorageRepository(tmp_path)

        raw_dir = tmp_path / "logs" / "raw" / "2026" / "01"
        raw_dir.mkdir(parents=True)
        (raw_dir / "2026-01-01.md").write_text("## 10:00\nOriginal entry\n\n## 10:30 [correction]\nCorrected entry\n")

        entries = repo.get_entries_by_pattern("2026/01/*.md")

        assert len(entries) == 2
        assert entries[0].raw_content == "Original entry"
        assert entries[1].raw_content == "Corrected entry"

    def test_corrupted_json_returns_none(self, tmp_path: Path) -> None:
        """Test that corrupted JSON returns None for parsed_data."""
        repo = StorageRepository(tmp_path)

        # Create raw file
        raw_dir = tmp_path / "logs" / "raw" / "2026" / "01"
        raw_dir.mkdir(parents=True)
        (raw_dir / "2026-01-01.md").write_text("## 10:30\nTest entry\n")

        # Create corrupted parsed file
        parsed_dir = tmp_path / "logs" / "parsed" / "2026" / "01"
        parsed_dir.mkdir(parents=True)
        (parsed_dir / "2026-01-01.json").write_text("not valid json{")

        entries = repo.get_entries_by_date_range(date(2026, 1, 1), date(2026, 1, 1))

        assert len(entries) == 1
        assert entries[0].parsed_data is None

    def test_entry_id_format(self, tmp_path: Path) -> None:
        """Test entry IDs are generated correctly."""
        repo = StorageRepository(tmp_path)

        raw_dir = tmp_path / "logs" / "raw" / "2026" / "01"
        raw_dir.mkdir(parents=True)
        (raw_dir / "2026-01-01.md").write_text("## 08:05\nEarly morning entry\n")

        entries = repo.get_entries_by_date_range(date(2026, 1, 1), date(2026, 1, 1))

        assert len(entries) == 1
        assert entries[0].id == "2026-01-01_08-05-00"

    def test_utf8_content(self, tmp_path: Path) -> None:
        """Test UTF-8 content is handled correctly."""
        repo = StorageRepository(tmp_path)

        entry = Entry(
            id="2026-01-01_10-30-00",
            date=date(2026, 1, 1),
            timestamp=datetime(2026, 1, 1, 10, 30),
            raw_content="Workout notes: 운동 메모",
        )
        repo.save_entry(entry)

        entries = repo.get_entries_by_date_range(date(2026, 1, 1), date(2026, 1, 1))

        assert len(entries) == 1
        assert "운동 메모" in entries[0].raw_content
