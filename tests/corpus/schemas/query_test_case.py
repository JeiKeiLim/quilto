"""Query test case schema for end-to-end query flow testing.

This module defines the schema for expected outputs used to validate
query accuracy in Epic 3 (Planner Agent) and Epic 4 (Analysis & Response).
"""

from typing import Literal

from pydantic import BaseModel, ConfigDict

AnalysisPointType = Literal[
    "weight_progression_identified",
    "rep_range_noted",
    "time_span_mentioned",
    "volume_analysis",
    "frequency_pattern",
    "strength_comparison",
    "data_gap_identified",
    "peak_performance_found",
    "trend_direction",
    "exercise_variation_noted",
]

ResponseElementType = Literal[
    "mentions_starting_weight",
    "mentions_current_weight",
    "provides_trend_assessment",
    "includes_specific_dates",
    "acknowledges_data_limitation",
    "suggests_next_steps",
    "compares_exercises",
    "quantifies_improvement",
    "mentions_consistency",
]


class QueryTestCase(BaseModel):
    """Expected output for end-to-end query flow testing.

    Used to validate query accuracy in Epic 3 (Story 3-2: Implement Planner Agent)
    and Epic 4 (Stories 4-1, 4-2: Analysis & Response).

    Attributes:
        query: Natural language query from user.
        context_entries: List of entry IDs (dates) that provide context for the query.
        expected_analysis_points: List of key analysis points that should be identified.
        expected_response_elements: List of elements that should appear in the response.
    """

    model_config = ConfigDict(strict=True)

    query: str
    context_entries: list[str]
    expected_analysis_points: list[AnalysisPointType]
    expected_response_elements: list[ResponseElementType]
