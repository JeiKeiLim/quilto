"""Multilingual expected output schema.

This schema validates expected outputs for domain-agnostic multilingual test entries.
Tests Parser's handling of language variations, number formats, and date formats.
"""

from pydantic import BaseModel, ConfigDict


class MultilingualExpectedOutput(BaseModel):
    """Expected output for multilingual test entries.

    Unlike edge cases (which test invalid inputs), multilingual entries are valid
    content that tests locale-aware parsing and text extraction.

    Attributes:
        language_detected: Primary language(s) detected in the content.
        extracted_text: Normalized text extracted from the entry.
        numbers_detected: Numbers found with their original and normalized forms.
        dates_detected: Dates found with their original and normalized (ISO) forms.
        category: Test category: lang, mixed, number, date.
    """

    model_config = ConfigDict(strict=True)

    language_detected: list[str]
    """Primary language(s) detected: 'en', 'ko', 'mixed', etc."""

    extracted_text: str
    """Normalized text extracted from the entry."""

    numbers_detected: list[dict[str, str]]
    """Numbers found: [{"original": "1,000", "normalized": "1000"}, ...]."""

    dates_detected: list[dict[str, str]]
    """Dates found: [{"original": "2026년 1월 9일", "normalized": "2026-01-09"}, ...]."""

    category: str
    """Test category: lang, mixed, number, date."""
