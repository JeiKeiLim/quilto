"""State-related models for Quilto framework.

This module defines Pydantic models used for state management,
particularly for human-in-the-loop interactions.
"""

from pydantic import BaseModel, ConfigDict, model_validator


class UserClarificationResponse(BaseModel):
    """User's response to clarification questions.

    This is what the user provides when resuming from WAIT_USER state.
    Distinct from ClarifierOutput which is what the Clarifier agent produces.

    Attributes:
        responses: Mapping of gap_addressed to user's answer.
        declined: If True, user declined to answer and responses are cleared.

    Example:
        >>> response = UserClarificationResponse(
        ...     responses={"energy_level": "tired", "sleep_quality": "poor"},
        ...     declined=False
        ... )
        >>> response.responses
        {'energy_level': 'tired', 'sleep_quality': 'poor'}

        >>> declined_response = UserClarificationResponse(
        ...     responses={"energy_level": "tired"},
        ...     declined=True
        ... )
        >>> declined_response.responses  # Cleared by validator
        {}
    """

    model_config = ConfigDict(strict=True, extra="forbid")

    responses: dict[str, str]
    declined: bool = False

    @model_validator(mode="after")
    def validate_declined_responses(self) -> "UserClarificationResponse":
        """Clear responses when user declines.

        If declined is True, responses are ignored and cleared to empty dict.
        This ensures consistent state when user declines to answer.

        Returns:
            The validated UserClarificationResponse with responses cleared if declined.
        """
        if self.declined and self.responses:
            object.__setattr__(self, "responses", {})
        return self
