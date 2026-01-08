# Story 1.4: Create GeneralFitness Base Domain

Status: done

## Story

As a **Swealog developer**,
I want a **GeneralFitness base domain module**,
So that **the DomainModule interface is validated with a real implementation**.

## Acceptance Criteria

1. **Given** the GeneralFitness domain module is defined
   **When** I instantiate it
   **Then** all DomainModule fields are populated

2. **Given** the GeneralFitness domain is instantiated
   **When** I check its `description`
   **Then** it covers general fitness activities (workouts, exercise, health tracking)

3. **Given** the GeneralFitness domain is instantiated
   **When** I check its `log_schema`
   **Then** it defines a basic fitness entry structure with exercise, duration, notes, and optional metrics

4. **Given** the GeneralFitness domain is instantiated
   **When** I check its `vocabulary`
   **Then** it includes common fitness terms and normalizations (e.g., "workout" → "training session")

## Tasks / Subtasks

- [x] Task 1: Create GeneralFitness log schema (AC: #3)
  - [x] 1.1 Create `packages/swealog/swealog/domains/` module directory
  - [x] 1.2 Create `packages/swealog/swealog/domains/__init__.py` exporting domain modules
  - [x] 1.3 Create `packages/swealog/swealog/domains/general_fitness.py`
  - [x] 1.4 Define `GeneralFitnessEntry` Pydantic model with:
    - `activity_type: str` (required) - e.g., "workout", "cardio", "stretching"
    - `exercises: list[ExerciseRecord]` (optional) - list of exercises performed
    - `duration_minutes: int | None` (optional) - total duration
    - `notes: str | None` (optional) - freeform notes
    - `perceived_effort: int | None` (optional) - 1-10 scale
    - `date: str | None` (optional) - ISO date if provided
  - [x] 1.5 Define `ExerciseRecord` Pydantic model with:
    - `name: str` (required) - exercise name
    - `sets: int | None` (optional)
    - `reps: int | None` (optional)
    - `weight: float | None` (optional) - in user's preferred unit
    - `weight_unit: str | None` (optional) - "kg" or "lbs"
    - `duration_seconds: int | None` (optional) - for timed exercises
    - `distance: float | None` (optional) - for distance-based exercises
    - `distance_unit: str | None` (optional) - "km", "miles", "meters"

- [x] Task 2: Define GeneralFitness domain module (AC: #1, #2, #4)
  - [x] 2.1 Create `GeneralFitness` class inheriting from `DomainModule`
  - [x] 2.2 Set `description` to cover general fitness activities
  - [x] 2.3 Set `log_schema` to `GeneralFitnessEntry`
  - [x] 2.4 Define `vocabulary` with common fitness term normalizations:
    - "workout" → "training session"
    - "lifting" → "weight training"
    - "cardio" → "cardiovascular exercise"
    - "stretching" → "flexibility training"
    - "warmup" / "warm-up" → "warm up"
    - "cooldown" / "cool-down" → "cool down"
    - "pr" / "PR" → "personal record"
    - "pb" / "PB" → "personal best"
  - [x] 2.5 Set `expertise` with general fitness knowledge for agent prompts
  - [x] 2.6 Set `response_evaluation_rules` for fitness responses
  - [x] 2.7 Set `context_management_guidance` for Observer patterns

- [x] Task 3: Export domains from swealog package (AC: #1)
  - [x] 3.1 Update `packages/swealog/swealog/__init__.py` to export `GeneralFitness`, `GeneralFitnessEntry`, `ExerciseRecord`
  - [x] 3.2 Ensure `from swealog import GeneralFitness` works

- [x] Task 4: Write unit tests for GeneralFitness domain (AC: #1, #2, #3, #4)
  - [x] 4.1 Create `packages/swealog/tests/` directory
  - [x] 4.2 Create `packages/swealog/tests/__init__.py`
  - [x] 4.3 Create `packages/swealog/tests/test_general_fitness.py`
  - [x] 4.4 Test: GeneralFitness instantiates with all required fields
  - [x] 4.5 Test: GeneralFitnessEntry validates correctly with all fields
  - [x] 4.6 Test: GeneralFitnessEntry validates with minimal fields (activity_type only)
  - [x] 4.7 Test: ExerciseRecord validates correctly
  - [x] 4.8 Test: vocabulary contains expected normalizations
  - [x] 4.9 Test: description is non-empty and fitness-related
  - [x] 4.10 Test: log_schema is GeneralFitnessEntry class

- [x] Task 5: Validate integration (AC: #1, #2, #3, #4)
  - [x] 5.1 Run `uv run ruff check packages/swealog/`
  - [x] 5.2 Run `uv run pyright packages/swealog/`
  - [x] 5.3 Run `uv run pytest packages/swealog/tests/ -v`

## Dev Notes

### Architecture Compliance

This story implements FR-A1 from the epics document:
- **FR-A1**: Provide GeneralFitness base domain module

Key architecture decisions to follow:
- **AR3**: uv workspace monorepo with two packages (quilto + swealog)
- **AR5**: LiteLLM for unified LLM API (not directly used in this story but schema design should support future parsing)
- **Python 3.13**: Use modern type hints (`list[str]` not `List[str]`)
- **Pydantic v2**: Use `ConfigDict`, `field_validator`, `model_validator` as needed

### Linting Configuration (from pyproject.toml)

The following ruff rules apply:
```toml
[tool.ruff.lint]
select = ["E", "F", "W", "I", "D", "UP", "B", "SIM"]
# Google docstring convention is enforced
```
- **All public classes/methods require Google-style docstrings**
- **pyright strict mode**: Must pass with 0 errors

### DomainModule Interface (from Story 1.2)

The `DomainModule` class from `quilto` is imported as:
```python
from quilto import DomainModule
```

The interface expects these fields at **instantiation time** (NOT as class attributes):

```python
class DomainModule(BaseModel):
    name: str = ""  # Defaults to class name via model_validator
    description: str  # REQUIRED - for Router auto-selection
    log_schema: type[BaseModel]  # REQUIRED - Pydantic model class (not instance)
    vocabulary: dict[str, str]  # REQUIRED - term normalization
    expertise: str = ""  # Domain knowledge for agents
    response_evaluation_rules: list[str] = []  # Rules for Evaluator
    context_management_guidance: str = ""  # Instructions for Observer
```

**CRITICAL**: `DomainModule` fields are passed to the constructor, not defined as class attributes. The `name` field auto-defaults to the class name via a `model_validator`.

### Schema Design Summary

| Field | Purpose | Notes |
|-------|---------|-------|
| `activity_type` | Required classifier | "workout", "cardio", "stretching" |
| `exercises` | Multi-exercise support | Nested `ExerciseRecord` list |
| `perceived_effort` | Effort tracking | 1-10 scale, validated via `field_validator` |
| `ExerciseRecord` | Flexible exercise data | Supports sets/reps AND duration/distance |

**Key Design Decision:** Optional fields allow Parser to handle incomplete data gracefully. Subdomains (Strength, Running) will extend these schemas.

### Project Structure After This Story

```
packages/swealog/
├── pyproject.toml
├── swealog/
│   ├── __init__.py      # Exports: __version__, GeneralFitness, GeneralFitnessEntry, ExerciseRecord
│   ├── py.typed
│   └── domains/         # NEW
│       ├── __init__.py  # Exports: GeneralFitness, GeneralFitnessEntry, ExerciseRecord (use __all__)
│       └── general_fitness.py  # GeneralFitness domain + schemas
└── tests/               # NEW
    ├── __init__.py
    └── test_general_fitness.py
```

**Export Pattern (domains/__init__.py):**
```python
"""Domain modules for Swealog fitness application."""

from swealog.domains.general_fitness import (
    ExerciseRecord,
    GeneralFitness,
    GeneralFitnessEntry,
)

__all__ = [
    "ExerciseRecord",
    "GeneralFitness",
    "GeneralFitnessEntry",
]
```

**Top-level Export Pattern (swealog/__init__.py):**
```python
"""Swealog - Personal fitness logging with AI-powered insights."""

from swealog.domains import ExerciseRecord, GeneralFitness, GeneralFitnessEntry

__version__ = "0.1.0"

__all__ = [
    "__version__",
    "ExerciseRecord",
    "GeneralFitness",
    "GeneralFitnessEntry",
]
```

### Previous Story Learnings (Story 1.3)

From the LLM Client Abstraction implementation:
- **Pydantic v2 patterns**: Use `ConfigDict` for model configuration
- **Type hints**: Use modern `list[str]` syntax, not `List[str]`
- **Google docstrings**: Required for all public classes and methods
- **Strict pyright**: Must pass with 0 errors
- **Test patterns**: Use pytest with descriptive test names

### Testing Strategy

**Required Tests (test_general_fitness.py):**

```python
import pytest
from swealog import GeneralFitness, GeneralFitnessEntry, ExerciseRecord

class TestExerciseRecord:
    def test_creates_with_name_only(self):
        record = ExerciseRecord(name="Bench Press")
        assert record.name == "Bench Press"
        assert record.sets is None

    def test_creates_with_all_fields(self):
        record = ExerciseRecord(
            name="Squat", sets=3, reps=5, weight=100.0, weight_unit="kg"
        )
        assert record.sets == 3

class TestGeneralFitnessEntry:
    def test_creates_with_activity_type_only(self):
        entry = GeneralFitnessEntry(activity_type="workout")
        assert entry.exercises == []

    def test_validates_perceived_effort_range(self):
        with pytest.raises(ValueError, match="between 1 and 10"):
            GeneralFitnessEntry(activity_type="workout", perceived_effort=11)

    def test_accepts_valid_perceived_effort(self):
        entry = GeneralFitnessEntry(activity_type="workout", perceived_effort=7)
        assert entry.perceived_effort == 7

class TestGeneralFitness:
    def test_has_required_domain_fields(self):
        from swealog.domains.general_fitness import general_fitness
        assert general_fitness.description
        assert general_fitness.log_schema == GeneralFitnessEntry
        assert "workout" in general_fitness.vocabulary

    def test_name_defaults_to_class_name(self):
        domain = GeneralFitness(
            description="test", log_schema=GeneralFitnessEntry, vocabulary={}
        )
        assert domain.name == "GeneralFitness"

    def test_vocabulary_has_expected_normalizations(self):
        from swealog.domains.general_fitness import general_fitness
        assert general_fitness.vocabulary["pr"] == "personal record"
        assert general_fitness.vocabulary["cardio"] == "cardiovascular exercise"
```

**Test Execution:**
```bash
uv run pytest packages/swealog/tests/test_general_fitness.py -v
```

### Technical Constraints Summary

| Constraint | Requirement |
|------------|-------------|
| Python | 3.13+ (use `list[str]` not `List[str]`) |
| Pydantic | 2.10+ (use `ConfigDict`, `field_validator`) |
| Import | `from quilto import DomainModule` |
| Docstrings | Google-style, all public classes/methods |
| Type checking | pyright strict, 0 errors |
| Linting | ruff check must pass |

### Complete Implementation Example

```python
"""GeneralFitness domain module for Swealog."""

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
)
```

**Key Implementation Notes:**
1. `ConfigDict(strict=True)` enforces type validation
2. `field_validator` ensures `perceived_effort` stays in 1-10 range
3. Class inherits from `DomainModule` but fields are set at instantiation
4. Google docstrings required for all public classes/methods
5. The singleton `general_fitness` instance is what gets exported

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 1.4]
- [Source: _bmad-output/planning-artifacts/architecture.md#Technical Stack]
- [Source: packages/quilto/quilto/domain.py - DomainModule interface]
- [Source: _bmad-output/implementation-artifacts/1-3-implement-llm-client-abstraction.md - Previous story patterns]

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

- Fixed pytest test discovery issue by adding `--import-mode=importlib` to pytest options in root pyproject.toml
- All 93 tests pass (78 quilto + 15 swealog)
- Ruff check passes after auto-fix for import sorting
- Pyright passes with 0 errors

### Completion Notes List

- Implemented `ExerciseRecord` Pydantic model with all specified fields (name, sets, reps, weight, weight_unit, duration_seconds, distance, distance_unit)
- Implemented `GeneralFitnessEntry` Pydantic model with activity_type, exercises, duration_minutes, notes, perceived_effort (with 1-10 validation), and date
- Created `GeneralFitness` class inheriting from `DomainModule` with comprehensive description, vocabulary (12 term normalizations), expertise, response_evaluation_rules (4 rules), and context_management_guidance
- Created singleton `general_fitness` instance for easy import
- Exported all classes from `swealog.domains` and top-level `swealog` package
- Wrote 15 comprehensive unit tests covering all acceptance criteria
- All tests follow red-green-refactor cycle

### File List

- packages/swealog/swealog/domains/__init__.py (NEW)
- packages/swealog/swealog/domains/general_fitness.py (NEW)
- packages/swealog/swealog/__init__.py (MODIFIED - added exports)
- packages/swealog/tests/__init__.py (NEW)
- packages/swealog/tests/test_general_fitness.py (NEW)
- pyproject.toml (MODIFIED - added pytest import-mode=importlib)

## Change Log

- 2026-01-08: Story 1.4 implemented - GeneralFitness base domain module with schemas, vocabulary, and comprehensive tests
- 2026-01-08: Code review fixes applied - Added `general_fitness` singleton to top-level exports, added 4 new tests (strict mode validation, singleton import paths, response_evaluation_rules content validation)
