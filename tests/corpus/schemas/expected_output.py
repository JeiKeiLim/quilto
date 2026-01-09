"""Test schemas for expected parser outputs.

These schemas extend application schemas with set_details for precise
per-set accuracy testing. NOT part of application code.
"""

from pathlib import Path

from pydantic import BaseModel, ConfigDict


class ExpectedSetDetail(BaseModel):
    """Per-set details for accuracy testing.

    Attributes:
        set_num: The set number (1-indexed).
        weight: Weight in kg, or None for bodyweight exercises.
        reps: Number of repetitions.
    """

    model_config = ConfigDict(strict=True)

    set_num: int
    weight: float | None = None
    reps: int | None = None


class ExpectedExerciseRecord(BaseModel):
    """Exercise with per-set details for accuracy testing.

    Attributes:
        name: English exercise name from CSV.
        sets: Total number of sets.
        set_details: List of per-set weight/reps.
        weight_unit: Unit for weights (default: kg).
    """

    model_config = ConfigDict(strict=True)

    name: str
    sets: int
    set_details: list[ExpectedSetDetail] = []
    weight_unit: str = "kg"


class ExpectedParserOutput(BaseModel):
    """Expected parser output for accuracy comparison.

    Attributes:
        activity_type: Type of activity (default: workout).
        exercises: List of exercises with set details.
        date: Date in YYYY-MM-DD format.
    """

    model_config = ConfigDict(strict=True)

    activity_type: str = "workout"
    exercises: list[ExpectedExerciseRecord]
    date: str


def is_synthetic(entry_path: Path | str, expected_output: ExpectedParserOutput | None = None) -> bool:
    """Check if an entry is synthetic (for robustness testing, not accuracy metrics).

    Synthetic entries are used to test parser robustness with edge cases,
    typos, and unusual formatting. They are NOT included in primary accuracy
    metrics (Story 1.7) because their expected outputs are human-created
    specifically for testing edge cases.

    Args:
        entry_path: Path to the entry file.
        expected_output: Optional parsed expected output to check date field.

    Returns:
        True if entry is synthetic (path contains '/synthetic/' or date is 'synthetic').
    """
    path_str = str(entry_path)
    if "/synthetic/" in path_str:
        return True
    return expected_output is not None and expected_output.date == "synthetic"
