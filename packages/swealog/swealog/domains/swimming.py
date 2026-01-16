"""Swimming domain module for Swealog.

This module provides the Swimming subdomain for pool and open water activities,
including laps, strokes, intervals, and workout tracking.
"""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field
from quilto import DomainModule


class SwimmingLap(BaseModel):
    """A single lap within a swim session.

    Attributes:
        lap_number: Lap number (1-indexed).
        stroke_type: Stroke used for this lap.
        duration_seconds: Time taken for this lap in seconds.
        notes: Lap-specific notes.
    """

    model_config = ConfigDict(strict=True)

    lap_number: int = Field(ge=1)
    stroke_type: Literal["freestyle", "backstroke", "breaststroke", "butterfly", "im"] | None = None
    duration_seconds: float | None = Field(default=None, ge=0.0)
    notes: str | None = None


class SwimmingInterval(BaseModel):
    """A structured interval within a swim workout.

    Attributes:
        repetitions: Number of reps (e.g., 10 in "10x100m").
        distance: Distance per rep (e.g., 100 in "10x100m").
        distance_unit: Unit for distance (meters, yards, or lap count).
        stroke_type: Stroke for this interval set.
        interval_seconds: Send-off interval (e.g., 90s for "on 1:30").
        rest_seconds: Rest between reps.
        notes: Interval-specific notes.
    """

    model_config = ConfigDict(strict=True)

    repetitions: int = Field(ge=1)
    distance: float = Field(ge=0.0)
    distance_unit: Literal["m", "y", "laps"] | None = None
    stroke_type: Literal["freestyle", "backstroke", "breaststroke", "butterfly", "im", "choice"] | None = None
    interval_seconds: float | None = Field(default=None, ge=0.0)
    rest_seconds: float | None = Field(default=None, ge=0.0)
    notes: str | None = None


class SwimmingEntry(BaseModel):
    """Parsed structure for a swimming log entry.

    Attributes:
        laps: Total lap count.
        distance: Total distance covered.
        distance_unit: Unit for distance (meters, yards, or lap count).
        duration_minutes: Total duration in minutes (float for fractional minutes).
        stroke_type: Primary stroke used.
        workout_type: Type of swim workout.
        pool_length: Pool size (25, 50, etc.).
        pool_length_unit: Unit for pool length (meters or yards).
        open_water: True for lake/ocean swimming.
        lap_times: Individual lap data.
        intervals: Structured interval sets.
        equipment: Equipment used (paddles, fins, pull buoy, etc.).
        average_pace: Pace per 100m/y (e.g., "1:45 per 100m").
        average_heart_rate: Average heart rate during swim.
        max_heart_rate: Maximum heart rate during swim.
        perceived_exertion: Overall effort level (1-10 scale).
        water_temperature: Water temperature (for open water).
        notes: General notes about the swim.
        date: ISO date string if provided in the log.
    """

    model_config = ConfigDict(strict=True)

    laps: int | None = Field(default=None, ge=0)
    distance: float | None = Field(default=None, ge=0.0)
    distance_unit: Literal["m", "y", "laps"] | None = None
    duration_minutes: float | None = Field(default=None, ge=0.0)
    stroke_type: Literal["freestyle", "backstroke", "breaststroke", "butterfly", "im", "mixed"] | None = None
    workout_type: Literal["endurance", "sprint", "drill", "technique", "recovery", "race", "open_water"] | None = None
    pool_length: float | None = Field(default=None, ge=0.0)
    pool_length_unit: Literal["m", "y"] | None = None
    open_water: bool = Field(default=False)
    lap_times: list[SwimmingLap] = []
    intervals: list[SwimmingInterval] = []
    equipment: list[str] = []
    average_pace: str | None = None
    average_heart_rate: int | None = Field(default=None, ge=0)
    max_heart_rate: int | None = Field(default=None, ge=0)
    perceived_exertion: int | None = Field(default=None, ge=1, le=10)
    water_temperature: float | None = None
    notes: str | None = None
    date: str | None = None


class Swimming(DomainModule):
    """Domain module for swimming activities.

    This domain covers swimming activities including pool swimming, open water swimming,
    and various stroke types. Tracks laps, distance, time, pace, intervals, and
    various physiological metrics.
    """


# Singleton instance
swimming = Swimming(
    description=(
        "Swimming activities including pool swimming and open water. Tracks laps, "
        "distance (meters, yards), duration, pace per 100m/y, strokes (freestyle, "
        "backstroke, breaststroke, butterfly, individual medley), and intervals. "
        "Covers workout types: endurance, sprint, drill, technique, recovery, race, "
        "and open water. Handles common notations like 'swam 40 laps freestyle', "
        "'10x100m free on 1:30', 'used paddles and pull buoy'. Tracks pool length "
        "(25m short course, 50m Olympic/long course), heart rate zones, equipment "
        "(fins, paddles, pull buoy, kickboard, snorkel), and water temperature for "
        "comprehensive swimming analysis."
    ),
    log_schema=SwimmingEntry,
    vocabulary={
        # ========================================
        # Stroke name normalizations (English)
        # ========================================
        "free": "freestyle",
        "front crawl": "freestyle",
        "back": "backstroke",
        "breast": "breaststroke",
        "fly": "butterfly",
        "butterfly stroke": "butterfly",
        "im": "individual medley",
        "medley": "individual medley",
        # ========================================
        # Stroke name normalizations (Korean)
        # ========================================
        "자유형": "freestyle",
        "배영": "backstroke",
        "평영": "breaststroke",
        "접영": "butterfly",
        "개인혼영": "individual medley",
        # ========================================
        # Distance/unit normalizations (English)
        # ========================================
        "m": "meters",
        "y": "yards",
        "olympic": "50 meters",
        "short course": "25 meters",
        "sc": "25 meters",
        "long course": "50 meters",
        "lc": "50 meters",
        # ========================================
        # Distance/unit normalizations (Korean)
        # ========================================
        "미터": "meters",
        "야드": "yards",
        # ========================================
        # Equipment normalizations (English)
        # ========================================
        "hand paddles": "paddles",
        "flippers": "fins",
        "pull": "pull buoy",
        "kick": "kickboard",
        "center snorkel": "snorkel",
        # ========================================
        # Equipment normalizations (Korean)
        # ========================================
        "패들": "paddles",
        "오리발": "fins",
        "풀부이": "pull buoy",
        "킥보드": "kickboard",
        # ========================================
        # Activity normalizations (English)
        # ========================================
        "swam": "swimming",
        "swim": "swimming",
        # ========================================
        # Activity normalizations (Korean)
        # ========================================
        "수영": "swimming",
        "랩": "laps",
        # ========================================
        # Workout type normalizations
        # ========================================
        "easy swim": "endurance",
        "speed": "sprint",
        "sprints": "sprint",
        "drills": "drill",
        "technique work": "technique",
        "warmup": "recovery",
        "warm up": "recovery",
        "cooldown": "recovery",
        "cool down": "recovery",
        # ========================================
        # Heart rate zones
        # ========================================
        "hr": "heart rate",
        "bpm": "beats per minute",
        # ========================================
        # Common swimming terms
        # ========================================
        "css": "critical swim speed",
        "swolf": "swim golf",
        "stroke count": "strokes per length",
        "spl": "strokes per length",
        "dps": "distance per stroke",
    },
    expertise=(
        "Swimming training principles: building aerobic base through consistent "
        "distance, progressive overload (10% weekly volume increase), specificity "
        "for race distances. Pace zones: Critical Swim Speed (CSS) as threshold "
        "pace, aerobic zone (conversation pace), anaerobic zone (race pace). "
        "Common metrics: SWOLF (stroke count + time), strokes per length (SPL), "
        "distance per stroke (DPS), pace per 100m/y. Stroke mechanics: freestyle "
        "(high elbow catch, bilateral breathing), backstroke (body rotation, "
        "consistent kick), breaststroke (timing of pull-breath-kick), butterfly "
        "(undulation, simultaneous arm recovery). Workout structures: pyramid "
        "(100-200-300-200-100), ladder (50-100-150-200), descending (fastest on "
        "last rep), negative split (second half faster). Interval notation: "
        "'10x100 on 1:30' = 10 reps of 100m with 90-second send-off. Equipment: "
        "paddles (catch power, shoulder stress), pull buoy (isolate upper body), "
        "fins (kick development, ankle flexibility), kickboard (kick isolation), "
        "snorkel (stroke focus without breathing). Open water considerations: "
        "sighting, drafting, navigation, water temperature, currents. Common "
        "distances: 50m (sprint), 100m, 200m, 400m (middle), 800m/1500m (distance), "
        "open water (1km, 2.5km, 5km, 10km)."
    ),
    response_evaluation_rules=[
        "Never recommend increasing weekly swim volume by more than 10% without context",
        "Always consider swimmer's current level for pace recommendations",
        "Flag potential shoulder injury risk with high paddle usage",
        "Recommend technique focus over volume for beginners",
        "Never recommend open water swimming without safety considerations",
        "Consider water temperature and conditions for open water advice",
        "Flag imbalanced stroke training (all freestyle, no IM work)",
        "Recommend rest days between hard swim sessions",
    ],
    context_management_guidance=(
        "Track: weekly distance totals and trends, stroke distribution (% freestyle "
        "vs other strokes), equipment usage frequency, pace progression per 100m. "
        "Flag: weekly volume spikes (>10% increase), consecutive hard sessions, "
        "sudden pace declines (>5% slower per 100m), training gaps >7 days, "
        "excessive paddle usage (shoulder risk), imbalanced stroke training. "
        "Correlate: pace vs equipment (faster with fins, slower with paddles), "
        "performance vs rest days, technique notes vs pace improvement, "
        "open water performance vs pool times."
    ),
    clarification_patterns={
        "SUBJECTIVE": [
            "How did your stroke feel - smooth or labored?",
            "Did you feel tired by the end of the set?",
            "How was the water temperature?",
            "Were you breathing comfortably throughout?",
        ],
        "CLARIFICATION": [
            "What stroke did you primarily use?",
            "What pool length - 25m or 50m?",
            "Were you using any equipment (fins, paddles, pull buoy)?",
            "Is this training for a specific race or event?",
        ],
    },
)
