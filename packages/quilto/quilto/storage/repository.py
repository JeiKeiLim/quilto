"""StorageRepository implementation for entry persistence and retrieval."""

import json
import logging
import re
import tempfile
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, cast

from quilto.agents.models import ParserOutput
from quilto.storage.models import DateRange, Entry, StorageSummary

logger = logging.getLogger(__name__)


class StorageRepository:
    """Repository for storing and retrieving log entries.

    Provides methods for CRUD operations on entries stored in a hierarchical
    file structure with separate raw markdown and parsed JSON files.

    Directory Structure:
        {base_path}/
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
        (self.base_path / "raw").mkdir(parents=True, exist_ok=True)
        (self.base_path / "parsed").mkdir(parents=True, exist_ok=True)
        (self.base_path / "context").mkdir(parents=True, exist_ok=True)

    def _get_raw_path(self, entry_date: date) -> Path:
        """Get the path for a raw markdown file for a given date.

        Args:
            entry_date: The date to get the path for.

        Returns:
            Path to the raw markdown file.
        """
        return (
            self.base_path / "raw" / str(entry_date.year) / f"{entry_date.month:02d}" / f"{entry_date.isoformat()}.md"
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
        raw_base = self.base_path / "raw"
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

        Note: Correction flow now uses edit_raw_section() for in-place edits.
        The correction parameter is kept for backward compatibility with
        parsed JSON updates only.

        Args:
            entry: The Entry to save.
            correction: Optional ParserOutput for parsed JSON updates only.
                Raw markdown corrections are now handled via edit_raw_section().
        """
        raw_path = self._get_raw_path(entry.date)
        parsed_path = self._get_parsed_path(entry.date)

        # Ensure directories exist
        raw_path.parent.mkdir(parents=True, exist_ok=True)
        parsed_path.parent.mkdir(parents=True, exist_ok=True)

        # Handle raw markdown - always append new entries
        # (corrections now use edit_raw_section() for in-place edits)
        time_str = entry.timestamp.strftime("%H:%M")
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
        context_path = self.base_path / "context" / "global.md"
        if context_path.exists():
            return context_path.read_text(encoding="utf-8")
        return ""

    def update_global_context(self, content: str) -> None:
        """Update the global context content.

        Args:
            content: New content to write to logs/context/global.md.
        """
        context_path = self.base_path / "context" / "global.md"
        context_path.parent.mkdir(parents=True, exist_ok=True)
        context_path.write_text(content, encoding="utf-8")

    def find_raw_entry_section(self, entry_id: str) -> tuple[Path, int, int] | None:
        """Locate the raw file and line boundaries for an entry.

        Parses the entry_id format `{YYYY-MM-DD}_{HH-MM-SS}` to find the
        corresponding raw file and the section starting with `## HH:MM`.

        Args:
            entry_id: Entry ID in format `YYYY-MM-DD_HH-MM-SS`.

        Returns:
            Tuple of (file_path, start_line, end_line) where:
            - file_path: Path to the raw markdown file
            - start_line: 0-indexed line number of the `## HH:MM` header
            - end_line: 0-indexed line number of the line before the next
              `## ` section header or EOF (exclusive, Python slice convention)
            Returns None if entry not found (file missing, no matching section,
            or multiple sections match the same time).

        Example:
            >>> result = repo.find_raw_entry_section("2026-01-26_18-33-00")
            >>> if result:
            ...     file_path, start, end = result
            ...     print(f"Section at lines {start}-{end} in {file_path}")
        """
        # Parse entry_id format: YYYY-MM-DD_HH-MM-SS
        try:
            date_part, time_part = entry_id.split("_")
            entry_date = date.fromisoformat(date_part)
            # Time part is HH-MM-SS, we need HH:MM for header matching
            time_components = time_part.split("-")
            if len(time_components) != 3:
                logger.warning("Invalid entry_id time format: %s", entry_id)
                return None
            target_hour = int(time_components[0])
            target_minute = int(time_components[1])
        except (ValueError, IndexError) as e:
            logger.warning("Failed to parse entry_id '%s': %s", entry_id, e)
            return None

        # Get raw file path
        raw_path = self._get_raw_path(entry_date)
        if not raw_path.exists():
            logger.debug("Raw file not found for entry_id '%s': %s", entry_id, raw_path)
            return None

        # Read file and find section
        content = raw_path.read_text(encoding="utf-8")
        lines = content.splitlines(keepends=True)

        # Pattern for section headers: ## HH:MM or ## HH:MM [correction]
        section_pattern = re.compile(r"^## (\d{2}):(\d{2})(?:\s*\[correction\])?\s*$")

        # Find all section headers and their line numbers
        section_starts: list[tuple[int, int, int]] = []  # (line_num, hour, minute)
        for line_num, line in enumerate(lines):
            match = section_pattern.match(line.rstrip("\n\r"))
            if match:
                hour = int(match.group(1))
                minute = int(match.group(2))
                section_starts.append((line_num, hour, minute))

        # Find matching section
        matching_sections = [
            (line_num, hour, minute)
            for line_num, hour, minute in section_starts
            if hour == target_hour and minute == target_minute
        ]

        if len(matching_sections) == 0:
            logger.debug("No section found for entry_id '%s' in %s", entry_id, raw_path)
            return None

        if len(matching_sections) > 1:
            # Multiple sections with same timestamp - ambiguous, return None
            logger.warning(
                "Multiple sections match entry_id '%s' in %s, returning None",
                entry_id,
                raw_path,
            )
            return None

        # Found exactly one match
        start_line = matching_sections[0][0]

        # Find end line (next section or EOF)
        end_line = len(lines)  # Default to end of file
        for line_num, _, _ in section_starts:
            if line_num > start_line:
                end_line = line_num
                break

        logger.debug(
            "Found section for entry_id '%s': %s lines %d-%d",
            entry_id,
            raw_path,
            start_line,
            end_line,
        )
        return (raw_path, start_line, end_line)

    def edit_raw_section(
        self,
        file_path: Path,
        start: int,
        end: int,
        new_content: str,
    ) -> None:
        r"""Edit a section of a raw markdown file in-place.

        Replaces lines[start:end] with the new content. Uses atomic write
        (tempfile + rename) to prevent data loss if process crashes mid-write.

        Args:
            file_path: Path to the raw markdown file to edit.
            start: Starting line number (0-indexed, inclusive).
            end: Ending line number (0-indexed, exclusive).
            new_content: New content to replace the section with. MUST include
                the `## HH:MM` header line (caller provides complete section).

        Raises:
            FileNotFoundError: If file_path does not exist.
            ValueError: If start >= end or start < 0.

        Example:
            >>> repo.edit_raw_section(
            ...     Path("raw/2026/01/2026-01-26.md"),
            ...     start=12,
            ...     end=18,
            ...     new_content="## 18:33\n40 minutes at 8kph, 3km\n",
            ... )
        """
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        if start < 0:
            raise ValueError(f"start must be >= 0, got {start}")

        if start >= end:
            raise ValueError(f"start must be < end, got start={start}, end={end}")

        # Read file preserving line endings
        content = file_path.read_text(encoding="utf-8")
        lines = content.splitlines(keepends=True)

        original_line_count = len(lines)
        original_byte_count = len(content.encode("utf-8"))

        logger.debug(
            "edit_raw_section: %s start=%d end=%d (file has %d lines, %d bytes)",
            file_path,
            start,
            end,
            original_line_count,
            original_byte_count,
        )

        # Ensure new_content ends with newline for consistency
        if new_content and not new_content.endswith("\n"):
            new_content = new_content + "\n"

        # Convert new_content to lines
        new_lines = new_content.splitlines(keepends=True)

        # Replace section: lines[start:end] with new_lines
        modified_lines = lines[:start] + new_lines + lines[end:]

        # Join back to content
        modified_content = "".join(modified_lines)
        modified_byte_count = len(modified_content.encode("utf-8"))

        logger.debug(
            "edit_raw_section: replacing lines %d-%d with %d new lines (%d bytes -> %d bytes)",
            start,
            end,
            len(new_lines),
            original_byte_count,
            modified_byte_count,
        )

        # Atomic write: write to temp file, then rename
        temp_path = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                dir=file_path.parent,
                delete=False,
            ) as temp_fd:
                temp_path = Path(temp_fd.name)
                temp_fd.write(modified_content)

            # Atomic rename
            temp_path.replace(file_path)
            logger.debug("edit_raw_section: atomic write complete to %s", file_path)
        except Exception:
            # Clean up temp file on error
            if temp_path is not None and temp_path.exists():
                temp_path.unlink()
            raise

    def get_storage_summary(self) -> StorageSummary:
        """Get summary of storage contents for Planner awareness.

        Scans the raw log directory structure to determine:
        - Date range of available logs (earliest and latest)
        - Total number of entries
        - Entry count per month

        Returns:
            StorageSummary with date range and entry counts.
            Returns empty summary if no logs exist.
        """
        raw_path = self.base_path / "raw"
        if not raw_path.exists():
            return StorageSummary()

        dates: list[date] = []
        entries_by_month: dict[str, int] = {}
        total_entries = 0

        # Scan year/month/day structure
        for year_dir in raw_path.iterdir():
            if not year_dir.is_dir():
                continue
            for month_dir in year_dir.iterdir():
                if not month_dir.is_dir():
                    continue
                for day_file in month_dir.glob("*.md"):
                    # Parse date from filename (YYYY-MM-DD.md)
                    try:
                        entry_date = date.fromisoformat(day_file.stem)
                        dates.append(entry_date)
                        month_key = entry_date.strftime("%Y-%m")
                        # Count entries in file (each entry starts with "## ")
                        content = day_file.read_text(encoding="utf-8")
                        entry_count = content.count("## ")
                        entries_by_month[month_key] = entries_by_month.get(month_key, 0) + entry_count
                        total_entries += entry_count
                    except ValueError:
                        continue

        if not dates:
            return StorageSummary()

        return StorageSummary(
            earliest_date=min(dates),
            latest_date=max(dates),
            total_entries=total_entries,
            entries_by_month=entries_by_month,
        )
