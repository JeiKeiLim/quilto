"""Pydantic schema for validating E2E evaluation dataset files."""

from typing import Literal

from pydantic import BaseModel, Field, field_validator


class EvaluationHints(BaseModel):
    """Hints for evaluating response quality."""

    should_mention: list[str] = Field(..., min_length=1)
    should_not: list[str] = Field(..., min_length=1)


class TestCase(BaseModel):
    """A single test case in the golden dataset."""

    __test__ = False  # Prevent pytest collection warning

    id: str = Field(..., min_length=1)
    category: Literal[
        "simple",
        "complex",
        "insufficient",
        "retrieval",
        "reasoning",
        "edge",
        "domain",
    ]
    query: str = Field(..., min_length=1)
    context_entries: list[str] = Field(..., min_length=1)
    rubric_criteria: list[Literal["accuracy", "completeness", "conciseness", "domain_expertise"]] = Field(
        ..., min_length=1
    )
    evaluation_hints: EvaluationHints
    source: str | None = None

    @field_validator("context_entries")
    @classmethod
    def validate_sorted(cls, v: list[str]) -> list[str]:
        """Ensure context_entries are chronologically sorted."""
        if v != sorted(v):
            raise ValueError(f"context_entries must be sorted: {v}")
        return v

    @field_validator("context_entries")
    @classmethod
    def validate_date_format(cls, v: list[str]) -> list[str]:
        """Ensure dates are in YYYY-MM-DD format."""
        import re

        pattern = re.compile(r"^\d{4}-\d{2}-\d{2}$")
        for date in v:
            if not pattern.match(date):
                raise ValueError(f"Invalid date format: {date}")
        return v


class GoldenDataset(BaseModel):
    """The complete golden dataset structure."""

    version: str
    domain: str
    case_count: int = Field(..., gt=0)
    created_by: str
    categories: dict[str, int]
    test_cases: list[TestCase]

    @field_validator("test_cases")
    @classmethod
    def validate_case_count(cls, v: list[TestCase], info) -> list[TestCase]:
        """Ensure test_cases count matches case_count metadata."""
        # Note: info.data contains already validated fields
        if "case_count" in info.data and len(v) != info.data["case_count"]:
            raise ValueError(f"test_cases count ({len(v)}) != case_count ({info.data['case_count']})")
        return v

    @field_validator("test_cases")
    @classmethod
    def validate_unique_ids(cls, v: list[TestCase]) -> list[TestCase]:
        """Ensure all test case IDs are unique."""
        ids = [tc.id for tc in v]
        if len(ids) != len(set(ids)):
            duplicates = [id for id in ids if ids.count(id) > 1]
            raise ValueError(f"Duplicate test case IDs: {set(duplicates)}")
        return v


class ScoringGuidance(BaseModel):
    """Scoring guidance for a rubric criterion."""

    good: str
    medium: str
    poor: str


class RubricCriterion(BaseModel):
    """A single rubric criterion definition."""

    description: str
    weight: float = Field(..., gt=0)
    scoring: ScoringGuidance


class CriterionProfile(BaseModel):
    """Profile of which criteria apply to a category."""

    required: list[str]
    optional: list[str] = []
    notes: str | None = None


class Rubric(BaseModel):
    """The complete rubric structure."""

    criteria: dict[str, RubricCriterion]
    criterion_profiles: dict[str, CriterionProfile]


class ModelParams(BaseModel):
    """Parameters used for model generation."""

    max_tokens: int
    temperature: float


class BaselineResponse(BaseModel):
    """A baseline response from Claude for a test case."""

    test_case_id: str = Field(..., min_length=1)
    dataset_version: str
    model: str
    model_params: ModelParams
    generated_at: str  # ISO 8601 format
    query: str
    context_entries: list[str]
    context_provided: str
    response: str


# ============================================================================
# Story 10.3: Pairwise Evaluation Schemas
# ============================================================================


class CriterionScore(BaseModel):
    """Score for a single rubric criterion."""

    criterion: Literal["accuracy", "completeness", "conciseness", "domain_expertise"]
    score: int = Field(..., ge=1, le=5)
    reasoning: str


class JudgeResult(BaseModel):
    """Result from a single judge evaluation."""

    winner: Literal["A", "B", "Tie"]
    criterion_scores_a: list[CriterionScore]
    criterion_scores_b: list[CriterionScore]
    aggregate_score_a: float
    aggregate_score_b: float
    reasoning: str
    raw_output: str  # Full judge response for debugging


class PairwiseResult(BaseModel):
    """Result from position-swapped pairwise evaluation."""

    test_case_id: str
    quilto_response: str | None  # None if generation failed
    claude_response: str
    judgment_ab: JudgeResult | None  # None if evaluation failed
    judgment_ba: JudgeResult | None
    final_winner: Literal["quilto", "claude", "tie", "error"]
    is_consistent: bool
    quilto_aggregate: float | None
    claude_aggregate: float | None
    error_message: str | None = None


class CategoryMetrics(BaseModel):
    """Metrics for a single category."""

    quilto_wins: int = 0
    claude_wins: int = 0
    ties: int = 0
    errors: int = 0


class EvaluationMetrics(BaseModel):
    """Aggregate metrics for an evaluation run."""

    total_cases: int
    quilto_wins: int
    claude_wins: int
    ties: int
    errors: int
    consistent_count: int
    inconsistent_count: int
    win_rate: float  # quilto_wins / (total - errors)
    tie_rate: float
    inconsistency_rate: float
    per_category: dict[str, CategoryMetrics]


class EvaluationRun(BaseModel):
    """Complete evaluation run results."""

    version: str
    timestamp: str
    judge_model: str
    judge_params: ModelParams
    results: list[PairwiseResult]
    metrics: EvaluationMetrics
