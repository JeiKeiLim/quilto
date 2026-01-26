"""Data models for the storage module."""

from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator


class StorageSummary(BaseModel):
    """Summary of storage contents for Planner awareness.

    Provides date range and entry counts to help Planner make informed
    date-range decisions when generating retrieval instructions.

    Attributes:
        earliest_date: Date of first log entry (None if no entries).
        latest_date: Date of most recent log entry (None if no entries).
        total_entries: Total number of entries across all dates.
        entries_by_month: Count of entries per month (YYYY-MM format).
    """

    model_config = ConfigDict(strict=True)

    earliest_date: date | None = None
    latest_date: date | None = None
    total_entries: int = 0
    entries_by_month: dict[str, int] = Field(default_factory=dict)


class Entry(BaseModel):
    """A single log entry with raw and parsed content.

    Attributes:
        id: Unique identifier in format {YYYY-MM-DD}_{HH-MM-SS} or {YYYY-MM-DD}_{index}.
        date: The date of the entry.
        timestamp: Full timestamp when entry was created.
        raw_content: Original markdown content of the entry.
        parsed_data: Domain-specific parsed data, None if not yet parsed.
    """

    model_config = ConfigDict(strict=True)

    id: str
    date: date
    timestamp: datetime
    raw_content: str
    parsed_data: dict[str, Any] | None = None


class DateRange(BaseModel):
    """Date range for filtering queries.

    Attributes:
        start: Start date (inclusive).
        end: End date (inclusive).
    """

    model_config = ConfigDict(strict=True)

    start: date
    end: date

    @model_validator(mode="after")
    def validate_range(self) -> "DateRange":
        """Validate that start date is not after end date.

        Returns:
            The validated DateRange instance.

        Raises:
            ValueError: If start date is after end date.
        """
        if self.start > self.end:
            raise ValueError("start must be <= end")
        return self


class ParserOutput(BaseModel):
    """Stub for Parser agent output - full definition in Epic 2 Story 3.

    Attributes:
        is_correction: Whether this output represents a correction.
        target_entry_id: ID of the entry being corrected (if is_correction=True).
        correction_delta: Fields to update in the parsed data.
    """

    model_config = ConfigDict(strict=True)

    is_correction: bool = False
    target_entry_id: str | None = None
    correction_delta: dict[str, Any] | None = None
