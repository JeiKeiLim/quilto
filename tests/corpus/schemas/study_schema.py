"""Test schema for expected study parser outputs.

This schema is for multi-domain testing infrastructure, NOT application code.
"""

from pydantic import BaseModel, ConfigDict


class StudyEntry(BaseModel):
    """Expected parser output for study/learning entries.

    Attributes:
        subject: Subject or topic studied.
        duration_minutes: Time spent studying in minutes if specified.
        topics: Specific topics or concepts covered.
        comprehension: Assessment of understanding (e.g., "understood", "need review").
        next_steps: Follow-up items or future study plans.
    """

    model_config = ConfigDict(strict=True)

    subject: str
    duration_minutes: int | None = None
    topics: list[str] = []
    comprehension: str | None = None
    next_steps: str | None = None
