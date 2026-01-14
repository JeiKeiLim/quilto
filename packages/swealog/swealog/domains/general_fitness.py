"""GeneralFitness domain module for Swealog.

This module provides the base fitness domain covering general workouts,
exercise logging, and health tracking activities.
"""

from pydantic import BaseModel, ConfigDict, field_validator
from quilto import DomainModule


class ExerciseRecord(BaseModel):
    """A single exercise performed in a workout.

    Attributes:
        name: Exercise name (required).
        sets: Number of sets performed.
        reps: Number of repetitions per set.
        weight: Weight used (in user's preferred unit).
        weight_unit: Unit for weight ("kg" or "lbs").
        duration_seconds: Duration for timed exercises.
        distance: Distance for distance-based exercises.
        distance_unit: Unit for distance ("km", "miles", "meters").
    """

    model_config = ConfigDict(strict=True)

    name: str
    sets: int | None = None
    reps: int | None = None
    weight: float | None = None
    weight_unit: str | None = None
    duration_seconds: int | None = None
    distance: float | None = None
    distance_unit: str | None = None


class GeneralFitnessEntry(BaseModel):
    """Parsed structure for a general fitness log entry.

    Attributes:
        activity_type: Type of activity (required). E.g., "workout", "cardio".
        exercises: List of exercises performed in this entry.
        duration_minutes: Total duration of the activity.
        notes: Freeform notes about the entry.
        perceived_effort: Subjective effort rating (1-10 scale).
        date: ISO date string if provided in the log.
    """

    model_config = ConfigDict(strict=True)

    activity_type: str
    exercises: list[ExerciseRecord] = []
    duration_minutes: int | None = None
    notes: str | None = None
    perceived_effort: int | None = None
    date: str | None = None

    @field_validator("perceived_effort")
    @classmethod
    def validate_effort_range(cls, v: int | None) -> int | None:
        """Validate perceived_effort is within 1-10 range.

        Args:
            v: The effort value to validate.

        Returns:
            The validated value.

        Raises:
            ValueError: If value is outside 1-10 range.
        """
        if v is not None and (v < 1 or v > 10):
            raise ValueError("perceived_effort must be between 1 and 10")
        return v


class GeneralFitness(DomainModule):
    """Base domain module for general fitness activities.

    This domain covers general fitness logging including workouts, cardio,
    strength training, flexibility, and health tracking. It serves as the
    foundation that specialized subdomains (Strength, Running, Nutrition)
    extend.
    """


# Create the singleton instance with all required fields
general_fitness = GeneralFitness(
    description=(
        "General fitness activities including workouts, cardio, strength training, "
        "flexibility exercises, and health tracking. Covers exercise logging, "
        "workout duration, perceived effort, and general fitness notes."
    ),
    log_schema=GeneralFitnessEntry,
    vocabulary={
        "workout": "training session",
        "lifting": "weight training",
        "cardio": "cardiovascular exercise",
        "stretching": "flexibility training",
        "warmup": "warm up",
        "warm-up": "warm up",
        "cooldown": "cool down",
        "cool-down": "cool down",
        "pr": "personal record",
        "PR": "personal record",
        "pb": "personal best",
        "PB": "personal best",
    },
    expertise=(
        "General fitness principles: progressive overload, adequate recovery, "
        "consistency over intensity. Activity categorization: strength (resistance), "
        "cardio (aerobic), flexibility (mobility), mixed (circuit/HIIT). "
        "Effort interpretation: RPE 1-4 easy, 5-6 moderate, 7-8 hard, 9-10 max. "
        "Common patterns: deload weeks, periodization, workout splits."
    ),
    response_evaluation_rules=[
        "Never recommend specific exercises without understanding user's fitness level",
        "Always consider recovery time when analyzing workout frequency",
        "Flag potential overtraining patterns with appropriate caution",
        "Avoid medical advice - suggest consulting professionals for injuries",
    ],
    context_management_guidance=(
        "Track: workout frequency (days per week), activity type distribution "
        "(strength vs cardio ratio), effort level trends (average RPE over time), "
        "general engagement patterns (consistency, gaps). Flag: sudden intensity "
        "spikes, extended rest periods, dramatic volume changes."
    ),
    clarification_patterns={
        "SUBJECTIVE": [
            "How's your energy level right now - feeling fresh or fatigued?",
            "How well did you sleep last night (roughly)?",
            "Are you dealing with any stress or life factors affecting your training?",
            "On a scale of 1-10, how motivated are you for today's workout?",
        ],
        "CLARIFICATION": [
            "Which specific workout or activity are you asking about?",
            "What time period should I focus on - today, this week, or longer?",
            "Are you asking about a specific type of exercise (cardio, strength, flexibility)?",
        ],
    },
)
