"""Running domain module for Swealog.

This module provides the Running subdomain for running/cardio activities,
including distance, time, pace, splits, intervals, and workout tracking.
"""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field
from quilto import DomainModule


class RunningSplit(BaseModel):
    """A single lap or split within a run.

    Attributes:
        split_number: Split/lap number (1-indexed).
        distance: Distance covered in this split.
        duration_seconds: Time taken for this split in seconds.
        pace: Calculated pace for this split (e.g., "5:00 min/km").
    """

    model_config = ConfigDict(strict=True)

    split_number: int = Field(ge=1)
    distance: float = Field(ge=0.0)
    duration_seconds: float = Field(ge=0.0)
    pace: str | None = None


class RunningInterval(BaseModel):
    """A structured interval within a workout.

    Attributes:
        work_distance: Distance for work portion of interval.
        work_duration_seconds: Duration of work portion in seconds.
        rest_duration_seconds: Duration of rest portion in seconds.
        repetitions: Number of times this interval was repeated.
        notes: Notes about this interval set.
    """

    model_config = ConfigDict(strict=True)

    work_distance: float | None = Field(default=None, ge=0.0)
    work_duration_seconds: float | None = Field(default=None, ge=0.0)
    rest_duration_seconds: float | None = Field(default=None, ge=0.0)
    repetitions: int | None = Field(default=None, ge=1)
    notes: str | None = None


class RunningEntry(BaseModel):
    """Parsed structure for a running log entry.

    Attributes:
        distance: Distance covered in the run.
        distance_unit: Unit of distance (km, mi, or m).
        duration_minutes: Total duration of the run in minutes.
        pace: Average pace (e.g., "5:30 min/km").
        pace_unit: Unit for pace (min/km or min/mi).
        workout_type: Type of run workout.
        terrain: Surface/route type for the run.
        splits: List of lap/split times.
        intervals: List of interval workout segments.
        average_heart_rate: Average heart rate during run.
        max_heart_rate: Maximum heart rate during run.
        cadence: Average steps per minute.
        elevation_gain: Total elevation gained in meters.
        elevation_loss: Total elevation lost in meters.
        perceived_exertion: Overall effort level (1-10 scale).
        weather: Weather conditions during the run.
        notes: General notes about the run.
        date: ISO date string if provided in the log.
    """

    model_config = ConfigDict(strict=True)

    distance: float | None = Field(default=None, ge=0.0)
    distance_unit: Literal["km", "mi", "m"] | None = None
    duration_minutes: int | None = Field(default=None, ge=0)
    pace: str | None = None
    pace_unit: Literal["min/km", "min/mi"] | None = None
    workout_type: (
        Literal["easy", "tempo", "threshold", "interval", "long_run", "recovery", "race", "fartlek"] | None
    ) = None
    terrain: Literal["road", "trail", "track", "treadmill", "mixed"] | None = None
    splits: list[RunningSplit] = []
    intervals: list[RunningInterval] = []
    average_heart_rate: int | None = Field(default=None, ge=0)
    max_heart_rate: int | None = Field(default=None, ge=0)
    cadence: int | None = Field(default=None, ge=0)
    elevation_gain: float | None = Field(default=None, ge=0.0)
    elevation_loss: float | None = Field(default=None, ge=0.0)
    perceived_exertion: int | None = Field(default=None, ge=1, le=10)
    weather: str | None = None
    notes: str | None = None
    date: str | None = None


class Running(DomainModule):
    """Domain module for running and cardio activities.

    This domain covers running activities including road running, trail running,
    track workouts, and treadmill sessions. Tracks distance, time, pace, splits,
    intervals, and various physiological metrics.
    """


# Singleton instance
running = Running(
    description=(
        "Running and cardio activities including road running, trail running, track "
        "workouts, and treadmill sessions. Tracks distance (km, mi, m), duration, pace, "
        "splits, and intervals. Covers workout types: easy runs, tempo, threshold, "
        "intervals, long runs, recovery, races, and fartlek. Handles common notations "
        "like '5k in 25:30', 'ran 10 miles', '4x800m intervals'. Tracks heart rate zones, "
        "cadence, and elevation for comprehensive running analysis."
    ),
    log_schema=RunningEntry,
    vocabulary={
        # ========================================
        # Distance abbreviations (English)
        # ========================================
        "5k": "5 kilometers",
        "10k": "10 kilometers",
        "15k": "15 kilometers",
        "21k": "21 kilometers",
        "hm": "half marathon",
        "half": "half marathon",
        "fm": "full marathon",
        "marathon": "full marathon",
        "mi": "miles",
        "mile": "miles",
        "km": "kilometers",
        "m": "meters",
        # ========================================
        # Activity variations (English)
        # ========================================
        "ran": "running",
        "run": "running",
        "jog": "jogging",
        "jogged": "jogging",
        "sprint": "sprinting",
        "sprinted": "sprinting",
        "tempo": "tempo run",
        "intervals": "interval training",
        "easy": "easy run",
        "recovery": "recovery run",
        "long": "long run",
        # ========================================
        # Korean running terms
        # ========================================
        "러닝": "running",
        "달리기": "running",
        "조깅": "jogging",
        "뛰기": "running",
        "템포런": "tempo",
        "인터벌": "interval",
        "롱런": "long_run",
        "이지런": "easy run",
        "회복런": "recovery run",
        "스프린트": "sprinting",
        "파틀렉": "fartlek",
        # ========================================
        # Korean distance/unit terms
        # ========================================
        "킬로미터": "kilometers",
        "킬로": "kilometers",
        "마일": "miles",
        "미터": "meters",
        "페이스": "pace",
        "분당": "per minute",
        # ========================================
        # Korean terrain terms
        # ========================================
        "트레일": "trail",
        "트랙": "track",
        "러닝머신": "treadmill",
        "트레드밀": "treadmill",
        "야외": "outdoor",
        "도로": "road",
        "노면": "road",
        # ========================================
        # Terrain/route terms (English)
        # ========================================
        "hills": "hilly",
        "flat": "flat terrain",
        # ========================================
        # Workout type normalizations
        # ========================================
        "easy run": "easy",
        "recovery run": "recovery",
        "tempo run": "tempo",
        "threshold": "threshold",
        "speed work": "interval",
        "speedwork": "interval",
        "track workout": "interval",
        "race": "race",
        "time trial": "race",
        "tt": "race",
        # ========================================
        # Pace/time notations
        # ========================================
        "min/km": "min/km",
        "min/mi": "min/mi",
        "/km": "min/km",
        "/mi": "min/mi",
        "pace": "pace",
        # ========================================
        # Heart rate zones
        # ========================================
        "hr": "heart rate",
        "bpm": "beats per minute",
        "zone": "heart rate zone",
        "z1": "zone 1",
        "z2": "zone 2",
        "z3": "zone 3",
        "z4": "zone 4",
        "z5": "zone 5",
        # ========================================
        # Cadence terms
        # ========================================
        "spm": "steps per minute",
        "cadence": "cadence",
        "turnover": "cadence",
        # ========================================
        # Korean heart rate and metric terms
        # ========================================
        "심박수": "heart rate",
        "심박": "heart rate",
        "케이던스": "cadence",
        "보폭": "stride length",
        "고도": "elevation",
    },
    expertise=(
        "Running training principles: base building through consistent easy mileage, "
        "progressive overload (10% weekly increase rule), specificity for race distances. "
        "Pace zones: Zone 1 recovery (very easy conversation), Zone 2 easy (comfortable "
        "conversation), Zone 3 tempo (sentences only), Zone 4 threshold (few words), "
        "Zone 5 interval/race (no talking). Common metrics: cadence (ideal 170-180 spm), "
        "stride length, vertical oscillation, ground contact time. Heart rate zones: "
        "calculated from max HR or lactate threshold. Workout types: easy runs (70-80% "
        "of weekly volume), long runs (20-30% of weekly mileage), tempo runs (lactate "
        "threshold pace), intervals (VO2max development), fartlek (unstructured speed play). "
        "Race distances: 5K, 10K, half marathon (21.1km), marathon (42.2km). Common "
        "injury prevention: adequate recovery, proper warmup/cooldown, strength training, "
        "gradual mileage increases. Environmental factors: heat acclimatization, altitude "
        "adjustment, hydration strategies."
    ),
    response_evaluation_rules=[
        "Never recommend increasing weekly mileage by more than 10% without context",
        "Always consider user's current fitness level for pace recommendations",
        "Flag potential overtraining: high mileage + high intensity + insufficient recovery",
        "Recommend rest days between hard sessions (intervals, tempo, long runs)",
        "Never suggest running through sharp or localized pain",
        "Consider environmental factors (heat, humidity, altitude) when analyzing pace",
        "Flag rapid mileage buildup without adequate base building period",
        "Recommend professional evaluation for persistent injuries or pain",
    ],
    context_management_guidance=(
        "Track: weekly mileage totals and trends, average pace progression by workout type, "
        "long run distance progression, interval/tempo session frequency, rest day patterns. "
        "Flag: weekly mileage spikes (>10% increase), consecutive hard workout days, "
        "sudden pace declines (>10% slower), training gaps >7 days, workout type imbalance "
        "(too much intensity, not enough easy running). "
        "Correlate: pace vs heart rate (cardiac drift), performance vs sleep/recovery notes, "
        "injury mentions vs training load, race performance vs training volume."
    ),
    clarification_patterns={
        "SUBJECTIVE": [
            "How did your breathing feel during the run - comfortable or labored?",
            "Did your legs feel fresh or heavy?",
            "Were you well-hydrated before and during?",
            "How did the temperature/weather affect your run?",
        ],
        "CLARIFICATION": [
            "Are you focusing on distance, time, or pace for this run?",
            "What type of terrain - road, trail, or track?",
            "Is this training for a specific race or event?",
            "Should I compare to your recent runs or your best times?",
        ],
    },
)
