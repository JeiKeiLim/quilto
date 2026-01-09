"""Test schemas for expected parser outputs.

This module exports Pydantic models for validating expected parser output
JSON files in the test corpus.
"""

from tests.corpus.schemas.cooking_schema import CookingEntry
from tests.corpus.schemas.edge_case_schema import EdgeCaseExpectedOutput
from tests.corpus.schemas.expected_output import (
    ExpectedExerciseRecord,
    ExpectedParserOutput,
    ExpectedSetDetail,
    is_synthetic,
)
from tests.corpus.schemas.journal_schema import JournalEntry
from tests.corpus.schemas.multilingual_schema import MultilingualExpectedOutput
from tests.corpus.schemas.study_schema import StudyEntry

__all__ = [
    "CookingEntry",
    "EdgeCaseExpectedOutput",
    "ExpectedSetDetail",
    "ExpectedExerciseRecord",
    "ExpectedParserOutput",
    "JournalEntry",
    "MultilingualExpectedOutput",
    "StudyEntry",
    "is_synthetic",
]
