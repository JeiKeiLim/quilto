# Story 6.4: Create Swimming Domain Module

Status: done

## Story

As a **Swealog developer**,
I want a **Swimming subdomain with schema and vocabulary**,
so that **swimming workouts are parsed and analyzed correctly**.

## Background

This is the final story in Epic 6 (Domain Intelligence) and fulfills FR-A5: "Provide Swimming subdomain (laps, strokes, intervals) [Post-MVP]".

Swimming is distinct from Running (Story 3.4) and other fitness domains in several ways:
- **Laps and distance** are counted differently (laps, meters, yards vs km/miles)
- **Strokes** are a primary categorization (freestyle, backstroke, breaststroke, butterfly)
- **Pool vs open water** creates different metrics and context
- **Intervals and drills** are common training components
- **Equipment** (fins, paddles, pull buoy, kickboard) affects workouts

With Stories 6.1-6.3 complete, the domain auto-selection, multi-domain combination, and mid-flow domain expansion infrastructure is ready. The Swimming domain will benefit from cross-domain queries like "compare running vs swimming cardio" which was explicitly mentioned in the epics acceptance criteria.

## Acceptance Criteria

1. **Given** input like "swam 40 laps freestyle, 30 min"
   **When** parsed with Swimming domain
   **Then** schema extracts `laps=40`, `stroke_type="freestyle"`, `duration_minutes=30`
   **And** all fields are properly typed and validated

2. **Given** input with stroke variations like "fly", "free", "breast", "back"
   **When** vocabulary normalization is applied
   **Then** variations map to canonical stroke names: "butterfly", "freestyle", "breaststroke", "backstroke"
   **And** Korean stroke terms are also normalized

3. **Given** input with pool distance/size like "25m pool", "50y pool", "olympic"
   **When** parsed with Swimming domain
   **Then** schema extracts `pool_length` and `pool_length_unit`
   **And** "olympic" normalizes to 50 meters

4. **Given** input with swim intervals like "10x100m free on 1:30"
   **When** parsed with Swimming domain
   **Then** schema extracts intervals with `repetitions`, `distance`, `stroke_type`, `interval_time`
   **And** interval structure follows the pattern of RunningInterval from Running domain

5. **Given** input with swim equipment like "used paddles and pull buoy"
   **When** parsed with Swimming domain
   **Then** schema extracts `equipment` list
   **And** vocabulary normalizes equipment variations

6. **Given** a cross-domain query like "compare running vs swimming cardio this week"
   **When** the domain selection system processes it
   **Then** both Running and Swimming domains are auto-selected
   **And** the query can access both domains' vocabularies and expertise
   **And** no code changes are required (validates Story 6.1-6.3 infrastructure)

7. **Given** the Swimming domain module
   **When** I instantiate it
   **Then** all DomainModule fields are populated: `name`, `description`, `log_schema`, `vocabulary`, `expertise`, `response_evaluation_rules`, `context_management_guidance`, `clarification_patterns`
   **And** the singleton instance `swimming` is available from `swealog.domains`

8. **Given** the Swimming domain
   **When** integrated with existing fitness domains
   **Then** Swimming exports are in `swealog.domains.__all__`
   **And** Swimming coexists with GeneralFitness, Strength, Nutrition, Running
   **And** no import conflicts occur

## Tasks / Subtasks

- [x] Task 1: Create SwimmingEntry schema with Pydantic (AC: #1, #3, #4, #5)
  - [x] 1.1: Create `packages/swealog/swealog/domains/swimming.py`
  - [x] 1.2: Define `SwimmingLap` model for individual lap tracking
    - `lap_number: int = Field(ge=1)` - lap number (1-indexed)
    - `stroke_type: Literal["freestyle", "backstroke", "breaststroke", "butterfly", "im"] | None = None` - stroke for this lap
    - `duration_seconds: float | None = Field(default=None, ge=0.0)` - time for this lap
    - `notes: str | None = None` - lap-specific notes
  - [x] 1.3: Define `SwimmingInterval` model for structured training
    - `repetitions: int = Field(ge=1)` - number of reps (e.g., 10 in "10x100m")
    - `distance: float = Field(ge=0.0)` - distance per rep (e.g., 100 in "10x100m")
    - `distance_unit: Literal["m", "y", "laps"] | None = None` - meters, yards, or lap count
    - `stroke_type: Literal["freestyle", "backstroke", "breaststroke", "butterfly", "im", "choice"] | None = None`
    - `interval_seconds: float | None = Field(default=None, ge=0.0)` - send-off interval (e.g., 90s for "on 1:30")
    - `rest_seconds: float | None = Field(default=None, ge=0.0)` - rest between reps
    - `notes: str | None = None`
  - [x] 1.4: Define `SwimmingEntry` model (main log schema)
    - `laps: int | None = Field(default=None, ge=0)` - total lap count
    - `distance: float | None = Field(default=None, ge=0.0)` - total distance
    - `distance_unit: Literal["m", "y", "laps"] | None = None` - meters, yards, or lap count
    - `duration_minutes: float | None = Field(default=None, ge=0.0)` - total time (float to allow fractional minutes like 30.5)
    - `stroke_type: Literal["freestyle", "backstroke", "breaststroke", "butterfly", "im", "mixed"] | None = None` - primary stroke
    - `workout_type: Literal["endurance", "sprint", "drill", "technique", "recovery", "race", "open_water"] | None = None`
    - `pool_length: float | None = Field(default=None, ge=0.0)` - pool size (25, 50, etc.)
    - `pool_length_unit: Literal["m", "y"] | None = None`
    - `open_water: bool = Field(default=False)` - True for lake/ocean swimming
    - `lap_times: list[SwimmingLap] = []` - individual lap data
    - `intervals: list[SwimmingInterval] = []` - structured interval sets
    - `equipment: list[str] = []` - paddles, fins, pull buoy, etc.
    - `average_pace: str | None = None` - pace per 100m/y (e.g., "1:45 per 100m")
    - `average_heart_rate: int | None = Field(default=None, ge=0)`
    - `max_heart_rate: int | None = Field(default=None, ge=0)`
    - `perceived_exertion: int | None = Field(default=None, ge=1, le=10)`
    - `water_temperature: float | None = None` - for open water (no constraint - can be negative for cold water)
    - `notes: str | None = None`
    - `date: str | None = None`
  - [x] 1.5: Add `ConfigDict(strict=True)` to all models
  - [x] 1.6: Ensure all required numeric fields use `Field(ge=...)` for validation

- [x] Task 2: Create Swimming DomainModule class (AC: #7)
  - [x] 2.1: Define `class Swimming(DomainModule)` with docstring
  - [x] 2.2: Create singleton instance `swimming = Swimming(...)` with all fields:
    - `description`: Clear description for Router auto-selection
    - `log_schema`: SwimmingEntry
    - `vocabulary`: Comprehensive term mapping (see Task 3)
    - `expertise`: Swimming training knowledge
    - `response_evaluation_rules`: Safety and training rules
    - `context_management_guidance`: What patterns Observer should track
    - `clarification_patterns`: Example questions per gap type

- [x] Task 3: Create comprehensive vocabulary (AC: #2, #5)
  - [x] 3.1: Stroke name normalizations (English)
    - "free", "front crawl" → "freestyle"
    - "back" → "backstroke"
    - "breast" → "breaststroke"
    - "fly", "butterfly stroke" → "butterfly"
    - "im", "medley" → "individual medley"
  - [x] 3.2: Stroke name normalizations (Korean)
    - "자유형" → "freestyle"
    - "배영" → "backstroke"
    - "평영" → "breaststroke"
    - "접영" → "butterfly"
    - "개인혼영" → "individual medley"
  - [x] 3.3: Distance/unit normalizations (avoid redundant identity mappings)
    - "m" → "meters"
    - "y" → "yards"
    - "olympic" → "50 meters"
    - "short course", "sc" → "25 meters"
    - "long course", "lc" → "50 meters"
  - [x] 3.4: Equipment normalizations (avoid redundant identity mappings)
    - "hand paddles" → "paddles"
    - "flippers" → "fins"
    - "pull" → "pull buoy"
    - "kick" → "kickboard"
    - "center snorkel" → "snorkel"
  - [x] 3.5: Korean unit/equipment terms
    - "미터" → "meters"
    - "야드" → "yards"
    - "패들" → "paddles"
    - "오리발" → "fins"
    - "풀부이" → "pull buoy"
    - "킥보드" → "kickboard"
  - [x] 3.6: Activity normalizations
    - "swam" → "swimming"
    - "swim" → "swimming"
    - "수영" → "swimming"
    - "랩" → "laps"

- [x] Task 4: Add swimming expertise and evaluation rules (AC: #7)
  - [x] 4.1: Write `expertise` covering:
    - Stroke mechanics fundamentals
    - Training zones (CSS, aerobic, threshold)
    - Common workout structures (pyramid, ladder, descending)
    - Interval notation (e.g., "10x100 on 1:30")
    - Equipment usage guidance
    - Open water considerations
    - Common metrics (SWOLF, stroke count, pace per 100)
  - [x] 4.2: Write `response_evaluation_rules`:
    - Never recommend increasing weekly volume >10% without context
    - Consider swimmer's current level for pace recommendations
    - Flag shoulder injury risk with high paddle usage
    - Recommend technique focus over volume for beginners
    - Never recommend open water without safety considerations
  - [x] 4.3: Write `context_management_guidance`:
    - Track: weekly distance, stroke distribution, equipment usage
    - Flag: sudden distance increases, technique regressions, imbalanced stroke training
    - Correlate: pace vs equipment, performance vs rest days

- [x] Task 5: Add clarification patterns (AC: #7)
  - [x] 5.1: Add SUBJECTIVE patterns:
    - "How did your stroke feel - smooth or labored?"
    - "Did you feel tired by the end of the set?"
    - "How was the water temperature?"
  - [x] 5.2: Add CLARIFICATION patterns:
    - "What stroke did you primarily use?"
    - "What pool length - 25m or 50m?"
    - "Were you using any equipment (fins, paddles, pull buoy)?"
    - "Is this for a specific race or event?"

- [x] Task 6: Update package exports (AC: #8)
  - [x] 6.1: Add imports to `packages/swealog/swealog/domains/__init__.py`:
    - `from swealog.domains.swimming import Swimming, SwimmingEntry, SwimmingLap, SwimmingInterval, swimming`
  - [x] 6.2: Add to `__all__` list: `Swimming`, `SwimmingEntry`, `SwimmingLap`, `SwimmingInterval`, `swimming`

- [x] Task 7: Create unit tests (AC: #1, #2, #3, #4, #5, #7)
  - [x] 7.1: Create `packages/swealog/tests/test_swimming_domain.py`
  - [x] 7.2: Test SwimmingLap validation:
    - `lap_number` boundary (1 succeeds, 0 fails, -1 fails)
    - `duration_seconds` boundary (0.0 succeeds, negative fails)
    - `stroke_type` Literal values (all valid values + invalid fails)
    - Optional fields can be None
  - [x] 7.3: Test SwimmingInterval validation:
    - `repetitions` boundary (1 succeeds, 0 fails, -1 fails)
    - `distance` boundary (0.0 succeeds, negative fails)
    - `interval_seconds` and `rest_seconds` boundaries (0.0 succeeds, negative fails)
    - All Literal values for `stroke_type` including "choice"
    - All Literal values for `distance_unit` ("m", "y", "laps")
    - Optional fields can be None
  - [x] 7.4: Test SwimmingEntry validation:
    - `laps` boundary (0 succeeds, negative fails)
    - `distance` boundary (0.0 succeeds, negative fails)
    - `duration_minutes` boundary (0.0 succeeds, negative fails) - note: float type
    - `pool_length` boundary (0.0 succeeds, negative fails)
    - `perceived_exertion` boundary (1 succeeds, 10 succeeds, 0 fails, 11 fails)
    - `average_heart_rate` and `max_heart_rate` boundaries (0 succeeds, negative fails)
    - All Literal values for `stroke_type` (including "mixed")
    - All Literal values for `workout_type`
    - All Literal values for `distance_unit` and `pool_length_unit`
    - `open_water` defaults to False
    - Nested models (lap_times, intervals) default to empty list
    - `equipment` defaults to empty list
    - Optional string fields can be empty string "" or None
    - `water_temperature` can be negative (cold water)
  - [x] 7.5: Test Swimming domain module:
    - Instantiation succeeds
    - Name defaults to "Swimming"
    - Description is non-empty
    - log_schema is SwimmingEntry
  - [x] 7.6: Test vocabulary normalizations:
    - English stroke variations ("free" → "freestyle", etc.)
    - Korean stroke terms ("자유형" → "freestyle", etc.)
    - Equipment variations ("flippers" → "fins", etc.)
    - Distance/pool variations ("olympic" → "50 meters", etc.)
    - Activity variations ("swam" → "swimming", etc.)
    - Korean equipment and unit terms
  - [x] 7.7: Test expertise and rules are non-empty
  - [x] 7.8: Test coexistence with other domains (GeneralFitness, Strength, Running, Nutrition)
  - [x] 7.9: Test all exports in `__all__`

- [x] Task 8: Create integration tests (AC: #6)
  - [x] 8.1: Test cross-domain query selection (Running + Swimming) via DomainSelector
  - [x] 8.2: Test domain auto-selection for swimming-specific input (validates 6.1-6.3 infrastructure)
  - [x] 8.3: Test multi-domain context merge includes swimming vocabulary
  - [x] 8.4: Test Swimming domain works with existing domain integration tests
  - NOTE: These tests validate that Swimming integrates with the existing 6.1-6.3 infrastructure.
         They should NOT duplicate infrastructure tests, but confirm Swimming works as expected.

- [x] Task 9: Run validation
  - [x] 9.1: Run `make check` (lint + typecheck)
  - [x] 9.2: Run `make test` (unit tests)
  - [x] 9.3: Run `make test-ollama` (integration tests with real Ollama)

## Dev Notes

### Pattern Reference

Follow the exact pattern established in `running.py`:

```python
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
    """Parsed structure for a swimming log entry."""
    model_config = ConfigDict(strict=True)

    # Use Field(default_factory=list) for mutable defaults
    lap_times: list[SwimmingLap] = Field(default_factory=list)
    intervals: list[SwimmingInterval] = Field(default_factory=list)
    equipment: list[str] = Field(default_factory=list)

    # Use Field(default=False) for explicit defaults
    open_water: bool = Field(default=False)

    # duration_minutes is float to allow 30.5 minutes
    duration_minutes: float | None = Field(default=None, ge=0.0)

    # ... other fields follow same pattern


class Swimming(DomainModule):
    """Domain module for swimming activities."""


# Singleton instance
swimming = Swimming(
    description="...",
    log_schema=SwimmingEntry,
    vocabulary={...},  # Avoid identity mappings like "paddles" -> "paddles"
    expertise="...",
    response_evaluation_rules=[...],
    context_management_guidance="...",
    clarification_patterns={...},
)
```

### Key Design Decisions

**Stroke Types:** Use Literal types for stroke_type to ensure type safety:
- `"freestyle"`, `"backstroke"`, `"breaststroke"`, `"butterfly"`, `"im"` (individual medley)
- Add `"mixed"` for SwimmingEntry when multiple strokes used
- Add `"choice"` for SwimmingInterval when swimmer chooses stroke

**Distance Units:** Swimming uses meters, yards, OR laps:
- `"m"` for meters (standard in most of world)
- `"y"` for yards (common in US pools)
- `"laps"` when user doesn't specify distance per lap

**Pool Length:** Critical for calculating actual distance:
- 25m (short course meters)
- 50m (long course meters / Olympic)
- 25y (short course yards)
- Store both value and unit for flexibility

**Equipment:** List of strings rather than Literal because:
- Many equipment combinations possible
- New equipment types emerge
- Normalization happens in vocabulary, not schema
- Use `Field(default_factory=list)` for the mutable default, not `= []`

**Interval Notation:** Swimming interval notation is specific:
- "10x100 on 1:30" = 10 reps of 100m with 90-second send-off
- "interval_seconds" = send-off time (when to start next rep)
- "rest_seconds" = actual rest (alternative notation)

### Common Mistakes to Avoid

| Mistake | Correct Pattern | Source |
|---------|-----------------|--------|
| Required string field without length check | Use `Field(min_length=1)` only if truly required | project-context.md |
| Redundant `@field_validator` for range | Use `Field(ge=0, le=10)` instead | project-context.md |
| Missing boundary value tests | Always test exact boundaries (0, 1, 10) AND negative values | project-context.md |
| Missing `py.typed` marker | `py.typed` exists in swealog package | project-context.md |
| Not testing empty string separately from None | Test both `None` and `""` cases | project-context.md |
| Missing from `__all__` | Export all public classes in `__all__` list | project-context.md |
| Using `= []` for mutable defaults | Use `Field(default_factory=list)` instead | Pydantic best practice |
| Redundant identity vocabulary mappings | "paddles" → "paddles" is unnecessary; only map variations | Running domain pattern |
| Using `int` for duration when fractions needed | Use `float` for `duration_minutes` to allow 30.5 mins | Flexibility |

### File Structure

```
packages/swealog/swealog/domains/
├── __init__.py          # Add Swimming exports
├── general_fitness.py
├── strength.py
├── running.py
├── nutrition.py
└── swimming.py          # NEW

packages/swealog/tests/
├── test_general_fitness.py
├── test_strength_domain.py
├── test_running_domain.py
├── test_nutrition_domain.py
├── test_domain_integration.py
└── test_swimming_domain.py  # NEW
```

### References

- [Source: _bmad-output/planning-artifacts/epics.md:61] FR-A5: Swimming subdomain requirement
- [Source: _bmad-output/planning-artifacts/epics.md:986-999] Story 6.4 acceptance criteria
- [Source: packages/swealog/swealog/domains/running.py] Pattern reference for domain module
- [Source: packages/quilto/quilto/domain.py] DomainModule interface
- [Source: _bmad-output/project-context.md:180-214] Common mistakes to avoid
- [Source: _bmad-output/implementation-artifacts/epic-6/6-3-implement-mid-flow-domain-expansion.md] Domain expansion infrastructure

### Story Dependencies

| Story | Dependency Type | Notes |
|-------|-----------------|-------|
| 6-1 (done) | Upstream | Domain auto-selection - Swimming will be auto-selected for swim queries |
| 6-2 (done) | Upstream | Multi-domain combination - Swimming can be combined with other fitness domains |
| 6-3 (done) | Upstream | Mid-flow expansion - Can expand to Swimming mid-query if needed |
| 3-4 (done) | Pattern reference | Running domain module pattern to follow |
| 2-4 (done) | Pattern reference | Strength domain for nested model patterns |

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

N/A

### Completion Notes List

1. **SwimmingLap, SwimmingInterval, SwimmingEntry schemas**: Created with Pydantic BaseModel and ConfigDict(strict=True). All numeric fields use Field(ge=...) for validation.

2. **Swimming DomainModule**: Singleton instance `swimming` with complete fields: description, log_schema, vocabulary, expertise, response_evaluation_rules, context_management_guidance, clarification_patterns.

3. **Vocabulary**: Comprehensive stroke normalizations (English + Korean), distance/pool terms, equipment terms, activity terms. Avoided redundant identity mappings per story guidance.

4. **List fields**: Used `= []` instead of `Field(default_factory=list)` to match existing patterns in running.py and strength.py, which avoids pyright type inference issues.

5. **Test coverage**: 113 unit tests for Swimming domain module, plus integration tests with DomainSelector confirming cross-domain queries (Running + Swimming) work correctly.

6. **Ollama test**: 1389 passed (including all Swimming-related tests). 1 pre-existing flaky failure in test_clarification_patterns.py unrelated to Swimming domain.

### File List

- packages/swealog/swealog/domains/swimming.py (NEW)
- packages/swealog/swealog/domains/__init__.py (MODIFIED)
- packages/swealog/tests/test_swimming_domain.py (NEW)
- packages/swealog/tests/test_domain_integration.py (MODIFIED)
- tests/integration/test_domain_selector_integration.py (MODIFIED)
