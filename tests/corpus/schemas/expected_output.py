"""Test schemas for expected parser outputs.

These schemas extend application schemas with set_details for precise
per-set accuracy testing. NOT part of application code.
"""

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
