# Story 3-4: Create Running Domain Module

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **Swealog developer**,
I want a **Running subdomain with schema and vocabulary**,
so that **running/cardio logs are parsed and retrieved correctly**.

## Acceptance Criteria

1. **Given** input like "ran 5k in 25:30, felt good"
   **When** parsed with Running domain
   **Then** schema extracts distance, time, pace, and notes

2. **Given** running log input with distance
   **When** parsed with Running domain
   **Then** vocabulary normalizes "ran" -> "running", "5k" -> "5 kilometers"

3. **Given** the Running domain module
   **When** instantiated
   **Then** all DomainModule fields are populated (description, log_schema, vocabulary, expertise)

4. **Given** running activities in various formats
   **When** parsed with Running domain
   **Then** schema handles:
   - Distance with units (km, mi, meters)
   - Duration (HH:MM:SS, MM:SS, minutes)
   - Pace (min/km, min/mi)
   - Heart rate zones
   - Terrain/route type
   - Workout type (easy run, tempo, intervals, long run)

5. **Given** the Running domain module
   **When** response_evaluation_rules and context_management_guidance are checked
   **Then** they are populated with running-specific guidance

6. **Given** all Swealog domains
   **When** Running is added
   **Then** it coexists with GeneralFitness, Strength, and Nutrition without conflicts

## Tasks / Subtasks

- [x] Task 1: Create RunningEntry schema with nested models (AC: #1, #4)
  - [x] 1.1: Define `RunningSplit` model for lap/split tracking
    - Add `model_config = ConfigDict(strict=True)`
    - Fields: `split_number` (int, ge=1), `distance` (float, ge=0.0), `duration_seconds` (float, ge=0.0), `pace` (str|None)
  - [x] 1.2: Define `RunningInterval` model for interval workouts
    - Add `model_config = ConfigDict(strict=True)`
    - Fields: `work_distance` (float|None, ge=0.0), `work_duration_seconds` (float|None, ge=0.0), `rest_duration_seconds` (float|None, ge=0.0), `repetitions` (int|None, ge=1), `notes` (str|None)
  - [x] 1.3: Define `RunningEntry` main schema with all fields
    - Add `model_config = ConfigDict(strict=True)`
    - All numeric fields use `Field(ge=0)` or `Field(ge=0.0)` for non-negative constraint
    - `perceived_exertion` uses `Field(default=None, ge=1, le=10)` like StrengthEntry
  - [x] 1.4: Add Field constraints (ge=0.0 for floats, ge=0 for ints, min_length=1 for required strings)
  - [x] 1.5: Add Literal types:
    - `distance_unit`: `Literal["km", "mi", "m"]`
    - `pace_unit`: `Literal["min/km", "min/mi"]`
    - `workout_type`: `Literal["easy", "tempo", "threshold", "interval", "long_run", "recovery", "race", "fartlek"]`
    - `terrain`: `Literal["road", "trail", "track", "treadmill", "mixed"]`

- [x] Task 2: Create Running domain module class (AC: #3)
  - [x] 2.1: Create `Running` class inheriting from `DomainModule`
  - [x] 2.2: Define `description` covering running/cardio activities
  - [x] 2.3: Set `log_schema` to `RunningEntry`

- [x] Task 3: Define comprehensive vocabulary (AC: #2, #4)
  - [x] 3.1: Add English running abbreviations:
    - Distance: "5k" -> "5 kilometers", "10k" -> "10 kilometers", "hm" -> "half marathon", "fm" -> "full marathon"
    - Units: "mi" -> "miles", "km" -> "kilometers", "m" -> "meters"
  - [x] 3.2: Add activity variations:
    - "ran" -> "running", "run" -> "running", "jog" -> "jogging", "jogged" -> "jogging"
    - "sprint" -> "sprinting", "tempo" -> "tempo run", "intervals" -> "interval training"
  - [x] 3.3: Add Korean running terms:
    - "러닝" -> "running", "달리기" -> "running", "조깅" -> "jogging"
    - "템포런" -> "tempo run", "인터벌" -> "interval training", "롱런" -> "long run"
    - "킬로미터" -> "kilometers", "마일" -> "miles", "미터" -> "meters"
    - "페이스" -> "pace", "분당" -> "per minute"
  - [x] 3.4: Add terrain/route terms:
    - "trail" -> "trail", "track" -> "track", "road" -> "road"
    - "treadmill" -> "treadmill", "트레일" -> "trail", "트랙" -> "track"
    - "러닝머신" -> "treadmill", "야외" -> "outdoor"
  - [x] 3.5: Add workout type normalizations:
    - "easy run" -> "easy", "recovery run" -> "recovery"
    - "tempo run" -> "tempo", "threshold" -> "threshold"
    - "speed work" -> "interval", "fartlek" -> "fartlek"

- [x] Task 4: Define expertise content (AC: #3)
  - [x] 4.1: Document running training principles (base building, progressive overload)
  - [x] 4.2: Document pace zones (easy, tempo, threshold, interval)
  - [x] 4.3: Document common metrics (cadence, stride, HR zones)
  - [x] 4.4: Document injury prevention and recovery

- [x] Task 5: Define response_evaluation_rules (AC: #5)
  - [x] 5.1: Add rules for mileage increase limits
  - [x] 5.2: Add rules for recovery between hard sessions
  - [x] 5.3: Add rules for injury precautions

- [x] Task 6: Define context_management_guidance (AC: #5)
  - [x] 6.1: Track weekly mileage trends
  - [x] 6.2: Track pace progression
  - [x] 6.3: Track workout type distribution

- [x] Task 7: Create singleton instance (AC: #3)
  - [x] 7.1: Create `running` singleton with all fields populated

- [x] Task 8: Export from domains __init__.py (AC: #6)
  - [x] 8.1: Add Running, RunningEntry, RunningSplit, RunningInterval, running to __init__.py
  - [x] 8.2: Update __all__ list

- [x] Task 9: Create comprehensive unit tests
  - [x] 9.1: Test RunningSplit model validation
    - Test split_number boundary (ge=1): test 1 succeeds, 0 fails
    - Test distance boundary (ge=0): test 0.0 succeeds, -1.0 fails
    - Test duration_seconds boundary (ge=0): test 0.0 succeeds, -1.0 fails
  - [x] 9.2: Test RunningInterval model validation
    - Test repetitions boundary (ge=1): test 1 succeeds, 0 fails
    - Test work_distance boundary (ge=0): test 0.0 succeeds, -1.0 fails
    - Test rest_duration_seconds boundary (ge=0): test 0.0 succeeds, -1.0 fails
  - [x] 9.3: Test RunningEntry model validation with boundary values
    - Test perceived_exertion boundaries: 1 succeeds, 10 succeeds, 0 fails, 11 fails
    - Test distance boundary (ge=0): test 0.0 succeeds, -1.0 fails
    - Test duration_minutes boundary (ge=0): test 0 succeeds, -1 fails
    - Test average_heart_rate boundary (ge=0): test 0 succeeds, -1 fails
    - Test cadence boundary (ge=0): test 0 succeeds, -1 fails
    - Test elevation_gain boundary (ge=0): test 0.0 succeeds, -1.0 fails
  - [x] 9.4: Test RunningEntry Literal type validation
    - Test valid distance_unit values: "km", "mi", "m" succeed
    - Test invalid distance_unit: "kilometers" fails (must use vocabulary)
    - Test valid pace_unit values: "min/km", "min/mi" succeed
    - Test valid workout_type values: all 8 values succeed
    - Test valid terrain values: all 5 values succeed
    - Test invalid terrain: "mountain" fails
  - [x] 9.5: Test Running domain module instantiation
    - Test singleton `running` is not None
    - Test `running` is instance of `Running`
    - Test name defaults to "Running"
  - [x] 9.6: Test vocabulary contains all expected English terms
  - [x] 9.7: Test Korean running vocabulary terms
    - Test "러닝" -> "running"
    - Test "조깅" -> "jogging"
    - Test "템포런" -> "tempo run"
    - Test "러닝머신" -> "treadmill"
  - [x] 9.8: Test coexistence with other domains (GeneralFitness, Strength, Nutrition)
  - [x] 9.9: Test all exports importable from swealog.domains
    - Test Running, RunningEntry, RunningSplit, RunningInterval, running all importable

- [x] Task 10: Run validation
  - [x] 10.1: Run `make check` (lint + typecheck)
  - [x] 10.2: Run `make validate` (full validation)
  - [x] 10.3: Run `make test-ollama` (integration tests)

## Dev Notes

### Architecture Patterns

- **Location:** `packages/swealog/swealog/domains/running.py` (Swealog-specific, NOT Quilto)
- **Pattern:** Follow existing domain patterns from `strength.py` and `nutrition.py`
- **Singleton:** Create `running` lowercase singleton instance like other domains

### Schema Design Considerations

The Running schema should capture:

**Core Metrics (from epics.md):**
- Distance: `float | None = Field(default=None, ge=0.0)` with unit (km, mi, m)
- Time/Duration: `duration_minutes: int | None = Field(default=None, ge=0)` total duration
- Pace: `pace: str | None = None` calculated or explicit (min/km, min/mi)
- Notes: `notes: str | None = None` freeform text

**Extended Metrics (for comprehensive coverage):**
- Splits: `splits: list[RunningSplit] = []` for lap/split times
- Intervals: `intervals: list[RunningInterval] = []` for interval workouts
- Heart Rate: `average_heart_rate: int | None = Field(default=None, ge=0)`, `max_heart_rate: int | None = Field(default=None, ge=0)`
- Cadence: `cadence: int | None = Field(default=None, ge=0)` steps per minute
- Elevation: `elevation_gain: float | None = Field(default=None, ge=0.0)`, `elevation_loss: float | None = Field(default=None, ge=0.0)`
- Terrain/Route: `terrain: Literal["road", "trail", "track", "treadmill", "mixed"] | None = None`
- Workout Type: `workout_type: Literal["easy", "tempo", "threshold", "interval", "long_run", "recovery", "race", "fartlek"] | None = None`
- Perceived Exertion: `perceived_exertion: int | None = Field(default=None, ge=1, le=10)` (like StrengthEntry)
- Weather: `weather: str | None = None` conditions if noted
- Date: `date: str | None = None` ISO date string if provided

### Vocabulary Priorities

**English abbreviations:**
- Distance: 5k, 10k, hm (half marathon), fm (full marathon), mi, km, m
- Activities: ran, run, jog, jogged, sprint, tempo, intervals
- Pace: min/km, min/mi, pace, tempo
- Terrain: trail, track, road, treadmill, hills

**Korean terms (critical for user Jongkuk Lim):**
- 러닝, 달리기, 조깅 (running, jogging)
- 템포런, 인터벌, 롱런 (tempo run, interval, long run)
- 킬로미터, 마일 (kilometer, mile)
- 트레일, 트랙, 러닝머신 (trail, track, treadmill)
- 페이스, 분당 (pace, per minute)

### Testing Standards

- **Boundary tests:** Test ge=0 constraints at 0 and -1; Test ge=1 constraints at 1 and 0
- **Required fields:** Test min_length=1 with empty string
- **Literal types:** Test valid values pass, invalid values raise ValidationError
- **All exports:** Verify importable from `swealog.domains`
- **Empty vs None:** Test both `None` and `""` for optional string fields per project-context.md
- **ConfigDict:** Use `model_config = ConfigDict(strict=True)` for all models

### Project Structure Notes

- File: `packages/swealog/swealog/domains/running.py`
- Tests: `packages/swealog/tests/test_running_domain.py`
- This is **Swealog-specific** code (fitness domain), not Quilto framework code

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 3.4]
- [Source: packages/swealog/swealog/domains/strength.py] - Pattern reference
- [Source: packages/swealog/swealog/domains/nutrition.py] - Pattern reference
- [Source: _bmad-output/project-context.md#Common Mistakes to Avoid]

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

N/A

### Completion Notes List

- All 10 tasks completed successfully
- Created Running domain module with comprehensive schema (RunningSplit, RunningInterval, RunningEntry)
- Implemented extensive vocabulary covering English and Korean terms
- Added expertise content, response_evaluation_rules, and context_management_guidance
- Created 71 unit tests covering all boundary conditions and Literal type validations
- All validation passed: `make check`, `make validate`, `make test-ollama` (736 passed, 4 skipped)

### Code Review Fixes Applied (2026-01-13)

- **HIGH-1 Fixed:** Added `scripts/manual_test.py` to File List
- **HIGH-2 Verified:** `py.typed` marker exists at `packages/swealog/swealog/py.typed`
- **HIGH-3 Noted:** Integration test deferred (Running domain schema tested, real LLM parsing via `manual_test.py`)
- **MEDIUM-1 Fixed:** Added 4 empty string tests for optional fields (`notes`, `weather`, `pace`, `date`)
- **MEDIUM-2 Fixed:** Removed redundant `"fartlek": "fartlek"` identity mapping from vocabulary
- **MEDIUM-3 Fixed:** Korean workout terms now map to Literal values: `"템포런": "tempo"`, `"인터벌": "interval"`, `"롱런": "long_run"`
- **MEDIUM-4 Noted:** `sprint-status.yaml` modification is workflow-managed, not story-specific
- **LOW-1 Noted:** Heart rate ge=0 retained for schema flexibility (physiological validation is LLM responsibility)
- **LOW-2 Fixed:** Removed redundant terrain identity mappings (`"trail": "trail"`, etc.)
- Updated `scripts/manual_test.py` to include Running domain (RunningEntry, running module)
- Updated test assertions to match corrected vocabulary values
- Post-fix validation: `make validate` (730 passed), `make test-ollama` (740 passed, 4 skipped)

### File List

- `packages/swealog/swealog/domains/running.py` (new)
- `packages/swealog/swealog/domains/__init__.py` (modified - added Running exports)
- `packages/swealog/tests/test_running_domain.py` (new)
- `scripts/manual_test.py` (modified - added Running domain support)
