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

__all__ = [
    "EdgeCaseExpectedOutput",
    "ExpectedSetDetail",
    "ExpectedExerciseRecord",
    "ExpectedParserOutput",
    "is_synthetic",
]
