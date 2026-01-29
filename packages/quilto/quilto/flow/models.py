"""Models for correction flow processing.

This module defines Pydantic models used in the correction flow,
including CorrectionResult which represents the outcome of processing
a user correction request.
"""

from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, model_validator

__all__ = ["CorrectionEdit", "CorrectionResult"]


class CorrectionEdit(BaseModel):
    r"""Represent a surgical edit to a raw markdown file.

    Contains the information needed to locate and replace a specific
    section in a raw log file. Line numbers are 0-indexed (Python convention).

    Attributes:
        target_file: Path to the raw markdown file to edit.
        section_start: Starting line number of the section (0-indexed, inclusive).
        section_end: Ending line number of the section (0-indexed, exclusive).
        original_content: The original content of the section being replaced.
        new_content: The new content to replace the section with.

    Example:
        >>> edit = CorrectionEdit(
        ...     target_file=Path("raw/2026/01/2026-01-26.md"),
        ...     section_start=12,
        ...     section_end=18,
        ...     original_content="## 18:33\n40 minutes at 8kph, 5km",
        ...     new_content="## 18:33\n40 minutes at 8kph, 3km",
        ... )
    """

    model_config = ConfigDict(strict=True)

    target_file: Path
    section_start: int
    section_end: int
    original_content: str
    new_content: str


class CorrectionResult(BaseModel):
    """Result of correction flow processing.

    Represents the outcome of processing a user's request to correct
    a previous log entry. Contains success status, target entry info,
    and the correction delta applied.

    Attributes:
        success: Whether the correction was successfully processed.
        target_entry_id: ID of the entry that was corrected.
            Required when success is True.
        correction_delta: Dictionary of only the fields that changed.
            Contains the specific corrections applied.
        original_entry_id: ID of the original entry before correction.
            Used for audit trail purposes.
        error_message: Description of what went wrong.
            Required when success is False.
        modified_file: Path to the raw file that was modified (if successful).
        edited_lines: Tuple of (start, end) line numbers that were edited
            (0-indexed, if successful).

    Example:
        >>> # Successful correction
        >>> result = CorrectionResult(
        ...     success=True,
        ...     target_entry_id="2026-01-14_10-30-00",
        ...     correction_delta={"weight": 185},
        ...     original_entry_id="2026-01-14_10-30-00",
        ...     modified_file=Path("raw/2026/01/2026-01-14.md"),
        ...     edited_lines=(12, 18),
        ... )
        >>> # Failed correction
        >>> result = CorrectionResult(
        ...     success=False,
        ...     error_message="Could not identify target entry",
        ... )
    """

    model_config = ConfigDict(strict=True)

    success: bool
    target_entry_id: str | None = None
    correction_delta: dict[str, Any] | None = None
    original_entry_id: str | None = None
    error_message: str | None = None
    modified_file: Path | None = None
    edited_lines: tuple[int, int] | None = None

    @model_validator(mode="after")
    def validate_success_requires_target(self) -> "CorrectionResult":
        """Validate that success=True requires target_entry_id.

        Also validates that success=False requires error_message.

        Returns:
            Self if validation passes.

        Raises:
            ValueError: If validation fails.
        """
        if self.success and not self.target_entry_id:
            raise ValueError("success=True requires target_entry_id")
        if not self.success and not self.error_message:
            raise ValueError("success=False requires error_message")
        return self
