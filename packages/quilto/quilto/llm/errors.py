"""Error types and classification for LLM error cascade.

This module provides error classification and partial result models
for graceful degradation when LLM providers fail.
"""

import json
from enum import Enum

import litellm.exceptions
from pydantic import BaseModel, ConfigDict, Field, ValidationError


class ErrorType(str, Enum):
    """Classification of LLM errors for retry decisions.

    Attributes:
        TRANSIENT: Temporary error, should retry same provider.
        PERMANENT: Non-recoverable error, skip to fallback immediately.
        UNKNOWN: Unknown error type, treated as transient by default.
    """

    TRANSIENT = "transient"
    PERMANENT = "permanent"
    UNKNOWN = "unknown"


class PartialResult(BaseModel):
    """Result returned when graceful degradation is triggered.

    When all providers fail and graceful degradation is enabled,
    this model is returned instead of raising an exception.

    Attributes:
        success: Always False for partial results.
        content: Partial content if any was received.
        error_message: Human-readable error description.
        error_type: Classification of the final error.
        providers_attempted: List of providers that were tried.
        retry_count: Total retry attempts made across all providers.
    """

    model_config = ConfigDict(frozen=True)

    success: bool = Field(default=False, description="Always False for partial results")
    content: str | None = Field(default=None, description="Partial content if available")
    error_message: str = Field(..., description="Human-readable error description")
    error_type: str = Field(..., description="Error classification")
    providers_attempted: list[str] = Field(default_factory=list)
    retry_count: int = Field(default=0, ge=0)

    def is_partial(self) -> bool:
        """Check if this is a partial result.

        Returns:
            True, indicating this is a partial/degraded result.
        """
        return True


def classify_error(exception: Exception) -> ErrorType:
    """Classify an exception to determine retry behavior.

    Determines whether an error is transient (worth retrying),
    permanent (skip to fallback), or unknown (default to retry).

    Args:
        exception: The exception that occurred during LLM call.

    Returns:
        ErrorType indicating whether to retry, fallback, or degrade.
    """
    # Schema/parsing errors are permanent - no point retrying
    if isinstance(exception, (json.JSONDecodeError, ValidationError)):
        return ErrorType.PERMANENT

    # ValueError with schema validation message is permanent
    if isinstance(exception, ValueError):
        msg = str(exception).lower()
        if "schema validation" in msg or "validation error" in msg:
            return ErrorType.PERMANENT

    # Transient errors - should retry
    transient_types = (
        litellm.exceptions.RateLimitError,
        litellm.exceptions.Timeout,
        litellm.exceptions.APIConnectionError,
        litellm.exceptions.ServiceUnavailableError,
        litellm.exceptions.InternalServerError,
        litellm.exceptions.BadGatewayError,
    )
    if isinstance(exception, transient_types):
        return ErrorType.TRANSIENT

    # Permanent errors - skip to fallback
    permanent_types = (
        litellm.exceptions.AuthenticationError,
        litellm.exceptions.InvalidRequestError,
        litellm.exceptions.NotFoundError,
        litellm.exceptions.BadRequestError,
        litellm.exceptions.PermissionDeniedError,
        litellm.exceptions.ContentPolicyViolationError,
    )
    if isinstance(exception, permanent_types):
        return ErrorType.PERMANENT

    # Check for HTTP status codes in generic errors
    if hasattr(exception, "status_code"):
        status = exception.status_code  # type: ignore[union-attr]
        if status == 429:  # Rate limit
            return ErrorType.TRANSIENT
        if status in (401, 403, 400, 404):
            return ErrorType.PERMANENT
        if 500 <= status < 600:
            return ErrorType.TRANSIENT

    # Default: treat unknown as unknown (will be treated as transient for retry)
    return ErrorType.UNKNOWN
