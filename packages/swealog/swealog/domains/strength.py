"""Strength domain module for Swealog.

This module provides the Strength subdomain for weight training,
including sets, reps, RPE, weight, and exercise tracking.
"""

from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator
from quilto import DomainModule


class StrengthSet(BaseModel):
    """A single set within an exercise.

    Attributes:
        reps: Number of repetitions performed.
        weight: Weight used for this set.
        weight_unit: Unit of weight (kg or lbs only - vocabulary normalizes variants).
        rpe: Rate of Perceived Exertion (1-10 scale). Mutually exclusive with rir.
        rir: Reps in Reserve (how many more reps could be done). Mutually exclusive
            with rpe.
        notes: Notes specific to this set (e.g., "grinder", "paused").
    """

    model_config = ConfigDict(strict=True)

    reps: int | None = None
    weight: float | None = None
    weight_unit: Literal["kg", "lbs"] | None = None
    rpe: float | None = Field(default=None, ge=1.0, le=10.0)
    rir: int | None = Field(default=None, ge=0)
    notes: str | None = None

    @model_validator(mode="after")
    def validate_rpe_rir_mutual_exclusivity(self) -> Self:
        """Validate that rpe and rir are mutually exclusive.

        Returns:
            Self if validation passes.

        Raises:
            ValueError: If both rpe and rir are set.
        """
        if self.rpe is not None and self.rir is not None:
            raise ValueError("rpe and rir are mutually exclusive")
        return self


class StrengthExercise(BaseModel):
    """A single exercise with its sets.

    Attributes:
        name: Exercise name (normalized via vocabulary). REQUIRED and non-empty.
        sets: List of individual sets performed.
        total_sets: Total number of sets (if not itemized).
        notes: Notes about this exercise (e.g., "felt heavy", "new PR").
    """

    model_config = ConfigDict(strict=True)

    name: str = Field(min_length=1)
    sets: list[StrengthSet] = []
    total_sets: int | None = None
    notes: str | None = None


class StrengthEntry(BaseModel):
    """Parsed structure for a strength training log entry.

    Attributes:
        exercises: List of exercises performed in this session.
        session_notes: Overall notes about the training session.
        date: ISO date string if provided in the log.
        duration_minutes: Total session duration.
        perceived_difficulty: Overall session difficulty (1-10).
    """

    model_config = ConfigDict(strict=True)

    exercises: list[StrengthExercise] = []
    session_notes: str | None = None
    date: str | None = None
    duration_minutes: int | None = None
    perceived_difficulty: int | None = Field(default=None, ge=1, le=10)


class Strength(DomainModule):
    """Domain module for strength training activities.

    This domain covers weight training including barbell and dumbbell exercises,
    tracking sets, reps, weight, RPE, and RIR metrics. It provides specialized
    parsing for strength training logs.
    """


# Singleton instance
strength = Strength(
    description=(
        "Strength training and weight lifting activities including barbell, dumbbell, "
        "and machine exercises. Tracks sets, reps, weight, RPE (Rate of Perceived "
        "Exertion), and RIR (Reps in Reserve). Covers compound lifts (squat, bench, "
        "deadlift, overhead press, rows) and isolation exercises. Handles common "
        "notation like 5x5, 185x5, @8 for RPE."
    ),
    log_schema=StrengthEntry,
    vocabulary={
        # ========================================
        # Exercise abbreviations (English)
        # ========================================
        "bp": "bench press",
        "bench": "bench press",
        "sq": "squat",
        "squats": "squat",
        "dl": "deadlift",
        "deads": "deadlift",
        "ohp": "overhead press",
        "press": "overhead press",
        "row": "barbell row",
        "rows": "barbell row",
        "pull": "pull up",
        "pulls": "pull up",
        "chin": "chin up",
        "chins": "chin up",
        "dip": "dip",
        "dips": "dip",
        "curl": "bicep curl",
        "curls": "bicep curl",
        # ========================================
        # Korean exercise names (from exercise_equivalences.yaml)
        # MUST match canonical names in equivalences file
        # ========================================
        "벤치프레스": "Bench Press (Barbell)",
        "바벨 벤치프레스": "Bench Press (Barbell)",
        "스쿼트": "Squat (Barbell)",
        "바벨 스쿼트": "Squat (Barbell)",
        "데드리프트": "Deadlift (Barbell)",
        "오버헤드프레스": "Overhead Press (Barbell)",
        "풀업": "Pull Up",
        "트랩바 데드리프트": "Trap Bar Deadlift",
        "푸쉬프레스": "Push Press",
        "프론트 스쿼트": "Front Squat (Barbell)",
        "인클라인 벤치프레스": "Incline Bench Press (Barbell)",
        "시티드 프레스": "Seated Overhead Press (Barbell)",
        "티바로우": "T Bar Row",
        "스모 데드리프트": "Sumo Deadlift (Barbell)",
        "플로어프레스": "Floor Press (Barbell)",
        "원암 덤벨로우": "Bent Over One Arm Row (Dumbbell)",
        "랫풀다운": "Lat Pulldown (Cable)",
        "바벨컬": "Bicep Curl (Barbell)",
        "덤벨컬": "Bicep Curl (Dumbbell)",
        "아놀드프레스": "Arnold Press (Dumbbell)",
        "레터럴레이즈": "Lateral Raise (Dumbbell)",
        "시티드 로우": "Seated Row (Cable)",
        "인클라인 덤벨프레스": "Incline Bench Press (Dumbbell)",
        "덤벨 벤치프레스": "Bench Press (Dumbbell)",
        "밀리터리프레스": "Strict Military Press (Barbell)",
        "푸쉬업": "Push Up",
        "싯업": "Sit Up",
        "크런치": "Decline Crunch",
        "카프레이즈": "Standing Calf Raise (Dumbbell)",
        "덤벨로우": "Bent Over Row (Dumbbell)",
        "오버헤드 스쿼트": "Overhead Squat (Barbell)",
        "머신 체스트프레스": "Iso-Lateral Chest Press (Machine)",
        "머신 로우": "Iso-Lateral Row (Machine)",
        "케이블 레터럴레이즈": "Lateral Raise (Cable)",
        # ========================================
        # Equipment variations
        # ========================================
        "barbell": "barbell",
        "bb": "barbell",
        "dumbbell": "dumbbell",
        "db": "dumbbell",
        "덤벨": "dumbbell",
        "바벨": "barbell",
        # ========================================
        # Weight unit normalizations
        # Schema accepts Literal["kg", "lbs"] only - vocabulary normalizes variants
        # ========================================
        "lbs": "lbs",
        "lb": "lbs",
        "pounds": "lbs",
        "#": "lbs",
        "kg": "kg",
        "kilos": "kg",
        "kilograms": "kg",
        # ========================================
        # Intensity notations (case-insensitive handling)
        # ========================================
        "@": "RPE",
        "rpe": "RPE",
        "RPE": "RPE",
        "rir": "RIR",
        "RIR": "RIR",
        # ========================================
        # Set notation
        # ========================================
        "x": "×",
        "sets": "sets",
        "set": "sets",
        "reps": "reps",
        "rep": "reps",
    },
    expertise=(
        "Strength training principles: progressive overload, specificity, recovery. "
        "Common rep ranges: 1-5 strength, 6-12 hypertrophy, 12+ endurance. "
        "RPE scale: 6 easy, 7 moderate, 8 challenging, 9 hard, 10 maximum effort. "
        "RIR (Reps in Reserve): 0=failure, 1=one more possible, 2-3=controlled. "
        "Key compound lifts: squat, bench press, deadlift, overhead press, row. "
        "Common notation: 5x5 = 5 sets of 5 reps, 185x5 = 185 units for 5 reps. "
        "Volume calculation: sets × reps × weight = total volume. "
        "Periodization: deload weeks, linear progression, undulating patterns. "
        "Recovery indicators: sleep quality, soreness (DOMS), performance trends."
    ),
    response_evaluation_rules=[
        "Never recommend max effort lifts (1RM testing) without proper warmup context",
        "Always consider user's stated experience level for weight recommendations",
        "Flag potential overtraining: high frequency + high volume + high intensity",
        "Avoid specific weight recommendations without historical context",
        "Recommend deload if user reports persistent fatigue or strength decline",
        "Never suggest training through sharp or acute pain",
        "Consider recovery factors (sleep, stress) when analyzing performance dips",
    ],
    context_management_guidance=(
        "Track: exercise PRs (weight × reps for major lifts), training frequency per "
        "muscle group, volume progression (weekly tonnage trends), intensity patterns "
        "(average RPE trends), exercise selection changes. "
        "Flag: sudden strength drops (>10% on major lifts), training gaps >7 days, "
        "persistent high RPE (>9 average over 2+ weeks), dramatic volume spikes. "
        "Correlate: performance vs sleep notes, strength trends vs bodyweight changes."
    ),
    clarification_patterns={
        "SUBJECTIVE": [
            "How does your body feel today - any lingering soreness from previous workouts?",
            "Are any joints or muscles feeling off or tight?",
            "Did your warm-up sets feel smooth or did something feel heavy?",
            "How's your grip strength feeling today?",
        ],
        "CLARIFICATION": [
            "Which specific lift are you asking about (squat, bench, deadlift, etc.)?",
            "What rep range are you targeting - strength (1-5), hypertrophy (6-12), or endurance (12+)?",
            "Do you have access to your usual equipment, or are you working with substitutes?",
            "Are you comparing to a recent session or your all-time PR?",
        ],
    },
)
