"""StorageRepository implementation for entry persistence and retrieval."""

import json
import logging
import re
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, cast

from quilto.storage.models import DateRange, Entry, ParserOutput

logger = logging.getLogger(__name__)


class StorageRepository:
    """Repository for storing and retrieving log entries.

    Provides methods for CRUD operations on entries stored in a hierarchical
    file structure with separate raw markdown and parsed JSON files.

    Directory Structure:
        {base_path}/logs/
        ├── raw/{YYYY}/{MM}/{YYYY-MM-DD}.md      # Human + agent readable
        ├── parsed/{YYYY}/{MM}/{YYYY-MM-DD}.json  # App consumption
        └── context/global.md                     # Observer's global context

    Attributes:
        base_path: Root directory for all storage operations.
    """

    def __init__(self, base_path: Path) -> None:
        """Initialize the StorageRepository.

        Args:
            base_path: Root directory for storage. Will be created if it doesn't exist.

        Raises:
            NotADirectoryError: If base_path exists but is not a directory.
        """
        if base_path.exists() and not base_path.is_dir():
            raise NotADirectoryError(f"base_path must be a directory, got file: {base_path}")
        self.base_path = base_path
        self._ensure_directories()

    def _ensure_directories(self) -> None:
        """Create required directory structure if it doesn't exist."""
        (self.base_path / "logs" / "raw").mkdir(parents=True, exist_ok=True)
        (self.base_path / "logs" / "parsed").mkdir(parents=True, exist_ok=True)
        (self.base_path / "logs" / "context").mkdir(parents=True, exist_ok=True)

    def _get_raw_path(self, entry_date: date) -> Path:
        """Get the path for a raw markdown file for a given date.

        Args:
            entry_date: The date to get the path for.

        Returns:
            Path to the raw markdown file.
        """
        return (
            self.base_path
            / "logs"
            / "raw"
            / str(entry_date.year)
            / f"{entry_date.month:02d}"
            / f"{entry_date.isoformat()}.md"
        )

    def _get_parsed_path(self, entry_date: date) -> Path:
        """Get the path for a parsed JSON file for a given date.

        Args:
            entry_date: The date to get the path for.

        Returns:
            Path to the parsed JSON file.
        """
        return (
            self.base_path
            / "logs"
            / "parsed"
            / str(entry_date.year)
            / f"{entry_date.month:02d}"
            / f"{entry_date.isoformat()}.json"
        )

    def _parse_raw_file(self, file_path: Path) -> list[Entry]:
        """Parse a raw markdown file into Entry objects.

        The expected format is:
            ## HH:MM
            Content here

            ## HH:MM [correction]
            Correction content

        Args:
            file_path: Path to the raw markdown file.

        Returns:
            List of Entry objects parsed from the file.
        """
        if not file_path.exists():
            return []

        content = file_path.read_text(encoding="utf-8")
        entries: list[Entry] = []

        # Extract date from filename (YYYY-MM-DD.md)
        entry_date = date.fromisoformat(file_path.stem)

        # Parse sections: ## HH:MM or ## HH:MM [correction]
        section_pattern = r"^## (\d{2}):(\d{2})(?:\s*\[correction\])?\s*$"
        sections = re.split(section_pattern, content, flags=re.MULTILINE)

        # sections[0] is any content before the first ##
        # Then groups of 3: (hour, minute, content)
        i = 1
        while i < len(sections) - 2:
            hour = int(sections[i])
            minute = int(sections[i + 1])
            section_content = sections[i + 2].strip()

            if section_content:
                timestamp = datetime(
                    entry_date.year,
                    entry_date.month,
                    entry_date.day,
                    hour,
                    minute,
                )
                entry_id = f"{entry_date.isoformat()}_{hour:02d}-{minute:02d}-00"

                # Load parsed data if available
                parsed_data = self._load_parsed_data(entry_date, entry_id)

                entries.append(
                    Entry(
                        id=entry_id,
                        date=entry_date,
                        timestamp=timestamp,
                        raw_content=section_content,
                        parsed_data=parsed_data,
                    )
                )

            i += 3

        return entries

    def _load_parsed_data(self, entry_date: date, entry_id: str) -> dict[str, Any] | None:
        """Load parsed data for a specific entry from the JSON file.

        Args:
            entry_date: Date of the entry.
            entry_id: ID of the entry to load.

        Returns:
            Parsed data dictionary if available, None otherwise.
        """
        parsed_path = self._get_parsed_path(entry_date)
        if not parsed_path.exists():
            return None

        try:
            with parsed_path.open(encoding="utf-8") as f:
                all_parsed: dict[str, Any] = json.load(f)

            if entry_id in all_parsed:
                result = all_parsed[entry_id]
                if isinstance(result, dict):
                    return cast(dict[str, Any], result)
            return None
        except (json.JSONDecodeError, OSError) as e:
            logger.error("Failed to load parsed data from %s: %s", parsed_path, e)
            return None

    def get_entries_by_date_range(self, start: date, end: date) -> list[Entry]:
        """Get all entries between start and end dates (inclusive).

        Args:
            start: Start date (inclusive).
            end: End date (inclusive).

        Returns:
            List of Entry objects in the date range, sorted by timestamp.
        """
        entries: list[Entry] = []
        current = start

        while current <= end:
            raw_path = self._get_raw_path(current)
            entries.extend(self._parse_raw_file(raw_path))
            current += timedelta(days=1)

        return sorted(entries, key=lambda e: e.timestamp)

    def get_entries_by_pattern(self, pattern: str) -> list[Entry]:
        """Get entries matching a glob pattern.

        The pattern is resolved relative to logs/raw/.

        Args:
            pattern: Glob pattern (e.g., "2026/01/**/*.md").

        Returns:
            List of Entry objects from matching files.
        """
        raw_base = self.base_path / "logs" / "raw"
        entries: list[Entry] = []

        for file_path in raw_base.glob(pattern):
            if file_path.is_file() and file_path.suffix == ".md":
                entries.extend(self._parse_raw_file(file_path))

        return sorted(entries, key=lambda e: e.timestamp)

    def search_entries(
        self,
        keywords: list[str],
        date_range: DateRange | None = None,
        match_all: bool = False,
    ) -> list[Entry]:
        """Search entries for keywords.

        Args:
            keywords: List of keywords to search for (case-insensitive).
                Must contain at least one keyword.
            date_range: DateRange to filter entries before searching, or None
                to search all entries.
            match_all: If True, all keywords must match (AND logic).
                      If False, any keyword match (OR logic).

        Returns:
            List of Entry objects matching the search criteria.

        Raises:
            ValueError: If keywords list is empty.
        """
        if not keywords:
            raise ValueError("keywords list must not be empty")

        # Get entries to search
        if date_range:
            candidates = self.get_entries_by_date_range(date_range.start, date_range.end)
        else:
            # Search all entries
            candidates = self.get_entries_by_pattern("**/*.md")

        # Normalize keywords for case-insensitive search
        keywords_lower = [kw.lower() for kw in keywords]

        matching: list[Entry] = []
        for entry in candidates:
            content_lower = entry.raw_content.lower()

            if match_all:
                # AND logic: all keywords must be present
                if all(kw in content_lower for kw in keywords_lower):
                    matching.append(entry)
            else:
                # OR logic: any keyword present
                if any(kw in content_lower for kw in keywords_lower):
                    matching.append(entry)

        return matching

    def save_entry(self, entry: Entry, correction: ParserOutput | None = None) -> None:
        """Save an entry to storage.

        For new entries, creates or appends to the raw markdown file and
        creates/updates the parsed JSON file.

        For corrections, appends a correction note to the raw file and
        updates the parsed JSON with the correction delta.

        Args:
            entry: The Entry to save.
            correction: Optional ParserOutput for correction flow.
        """
        raw_path = self._get_raw_path(entry.date)
        parsed_path = self._get_parsed_path(entry.date)

        # Ensure directories exist
        raw_path.parent.mkdir(parents=True, exist_ok=True)
        parsed_path.parent.mkdir(parents=True, exist_ok=True)

        # Handle raw markdown
        time_str = entry.timestamp.strftime("%H:%M")

        if correction and correction.is_correction:
            # Correction flow: append correction note
            correction_content = f"\n\n## {time_str} [correction]\n{entry.raw_content}"
            with raw_path.open("a", encoding="utf-8") as f:
                f.write(correction_content)
        else:
            # New entry: create or append
            entry_content = f"## {time_str}\n{entry.raw_content}\n"

            if raw_path.exists():
                with raw_path.open("a", encoding="utf-8") as f:
                    f.write(f"\n{entry_content}")
            else:
                raw_path.write_text(entry_content, encoding="utf-8")

        # Handle parsed JSON
        if correction and correction.is_correction and correction.correction_delta:
            # Update existing parsed data with correction delta
            self._update_parsed_json(
                parsed_path,
                correction.target_entry_id or entry.id,
                correction.correction_delta,
            )
        elif entry.parsed_data:
            # Save new parsed data
            self._save_parsed_json(parsed_path, entry.id, entry.parsed_data)

    def _save_parsed_json(self, parsed_path: Path, entry_id: str, parsed_data: dict[str, Any]) -> None:
        """Save parsed data for an entry.

        Args:
            parsed_path: Path to the parsed JSON file.
            entry_id: ID of the entry.
            parsed_data: Data to save.
        """
        existing: dict[str, Any] = {}
        if parsed_path.exists():
            try:
                with parsed_path.open(encoding="utf-8") as f:
                    existing = json.load(f)
            except (json.JSONDecodeError, OSError):
                existing = {}

        existing[entry_id] = parsed_data

        with parsed_path.open("w", encoding="utf-8") as f:
            json.dump(existing, f, indent=2, ensure_ascii=False, default=str)

    def _update_parsed_json(self, parsed_path: Path, entry_id: str, correction_delta: dict[str, Any]) -> None:
        """Update parsed data with a correction delta (upsert semantics).

        Args:
            parsed_path: Path to the parsed JSON file.
            entry_id: ID of the entry to update.
            correction_delta: Fields to update.
        """
        existing: dict[str, Any] = {}
        if parsed_path.exists():
            try:
                with parsed_path.open(encoding="utf-8") as f:
                    existing = json.load(f)
            except (json.JSONDecodeError, OSError):
                existing = {}

        if entry_id not in existing:
            existing[entry_id] = {}

        # Upsert: update existing with correction delta
        existing[entry_id].update(correction_delta)

        with parsed_path.open("w", encoding="utf-8") as f:
            json.dump(existing, f, indent=2, ensure_ascii=False, default=str)

    def get_global_context(self) -> str:
        """Get the global context content.

        Returns:
            Content of logs/context/global.md, or empty string if not found.
        """
        context_path = self.base_path / "logs" / "context" / "global.md"
        if context_path.exists():
            return context_path.read_text(encoding="utf-8")
        return ""

    def update_global_context(self, content: str) -> None:
        """Update the global context content.

        Args:
            content: New content to write to logs/context/global.md.
        """
        context_path = self.base_path / "logs" / "context" / "global.md"
        context_path.parent.mkdir(parents=True, exist_ok=True)
        context_path.write_text(content, encoding="utf-8")
