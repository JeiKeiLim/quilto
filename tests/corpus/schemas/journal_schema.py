"""Test schema for expected journal parser outputs.

This schema is for multi-domain testing infrastructure, NOT application code.
"""

from pydantic import BaseModel, ConfigDict


class JournalEntry(BaseModel):
    """Expected parser output for journal entries.

    Attributes:
        mood: Emotional state or feeling (e.g., "happy", "anxious", "stressed").
        topics: List of topics or themes mentioned in the entry.
        date: Date in YYYY-MM-DD format if extractable, None otherwise.
        notes: Additional context or observations from the entry.
    """

    model_config = ConfigDict(strict=True)

    mood: str | None = None
    topics: list[str] = []
    date: str | None = None
    notes: str | None = None
