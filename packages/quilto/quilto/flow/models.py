"""Models for correction flow processing.

This module defines Pydantic models used in the correction flow,
including CorrectionResult which represents the outcome of processing
a user correction request.
"""

from typing import Any

from pydantic import BaseModel, ConfigDict, model_validator

__all__ = ["CorrectionResult"]


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

    Example:
        >>> # Successful correction
        >>> result = CorrectionResult(
        ...     success=True,
        ...     target_entry_id="2026-01-14_10-30-00",
        ...     correction_delta={"weight": 185},
        ...     original_entry_id="2026-01-14_10-30-00",
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
