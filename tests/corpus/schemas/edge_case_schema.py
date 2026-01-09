"""Edge case expected output schema.

This schema validates expected outputs for domain-agnostic edge case entries.
Unlike ExpectedParserOutput (which validates fitness domain parsing), this
schema focuses on Parser robustness testing with invalid/edge inputs.
"""

from pydantic import BaseModel, ConfigDict


class EdgeCaseExpectedOutput(BaseModel):
    """Expected output for edge case test entries.

    Edge cases typically result in:
    - parseable=False with a reason for truly invalid inputs
    - parseable=True with empty/minimal extraction for edge-valid inputs

    Attributes:
        parseable: Whether the input could be parsed at all.
        reason: Reason for parse failure (if parseable=False).
        extracted_text: Any text successfully extracted (may be empty).
        warnings: Non-fatal warnings during parsing.
        category: Edge case category for classification.
    """

    model_config = ConfigDict(strict=True)

    parseable: bool
    """Whether the input could be parsed at all."""

    reason: str | None = None
    """Reason for parse failure (if parseable=False)."""

    extracted_text: str | None = None
    """Any text that was successfully extracted (may be empty)."""

    warnings: list[str] = []
    """Non-fatal warnings during parsing (e.g., 'truncated long input')."""

    category: str
    """Edge case category: empty, unicode, length, markdown, injection."""
