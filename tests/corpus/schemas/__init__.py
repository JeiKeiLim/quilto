"""Test schemas for expected parser outputs.

This module exports Pydantic models for validating expected parser output
JSON files in the test corpus.
"""

from tests.corpus.schemas.edge_case_schema import EdgeCaseExpectedOutput
from tests.corpus.schemas.expected_output import (
    ExpectedExerciseRecord,
    ExpectedParserOutput,
    ExpectedSetDetail,
    is_synthetic,
)
from tests.corpus.schemas.multilingual_schema import MultilingualExpectedOutput

__all__ = [
    "EdgeCaseExpectedOutput",
    "ExpectedSetDetail",
    "ExpectedExerciseRecord",
    "ExpectedParserOutput",
    "MultilingualExpectedOutput",
    "is_synthetic",
]
