# Story 2.4: Create Strength Domain Module

Status: done

## Story

As a **Swealog developer**,
I want a **Strength subdomain with schema and vocabulary**,
So that **strength training logs are parsed correctly**.

## Acceptance Criteria

1. **Given** input like "bench 185x5 felt heavy"
   **When** parsed with Strength domain
   **Then** schema extracts exercise, weight, reps, and notes
   **And** vocabulary normalizes "bench" → "bench press"
   **And** parsed JSON includes all structured fields

2. **Given** the Strength domain module is defined
   **When** I instantiate it
   **Then** all DomainModule fields are populated (description, log_schema, vocabulary, expertise)
   **And** `name` defaults to "Strength" (class name)
   **And** `response_evaluation_rules` provides strength-specific guidance
   **And** `context_management_guidance` tracks strength-relevant patterns

3. **Given** a strength training log with sets and reps notation
   **When** parsed with StrengthEntry schema
   **Then** common formats are handled: "5x5", "3x10", "5 sets of 5"
   **And** weight formats are handled: "185", "185kg", "185lbs", "185#"
   **And** RPE/RIR notation is parsed when present: "RPE 8", "RIR 2", "@8"

4. **Given** input with exercise name variations
   **When** vocabulary normalization is applied
   **Then** abbreviations normalize to canonical names (e.g., "bp" → "bench press")
   **And** Korean terms normalize correctly (e.g., "벤치프레스" → "bench press")
   **And** common variations handled (e.g., "squats" → "squat", "deads" → "deadlift")

5. **Given** the Strength domain is registered with the framework
   **When** Router selects domains for strength-related input
   **Then** Strength domain is selected alongside GeneralFitness (base domain)
   **And** vocabulary from both domains is available to Parser

6. **Given** StrengthEntry Pydantic model
   **When** validating the schema
   **Then** `exercise` field is required (in StrengthExercise.name)
   **And** `sets`, `reps`, `weight`, `weight_unit` are optional
   **And** `rpe` and `rir` are mutually exclusive intensity metrics (one or other or neither, enforced by `@model_validator`)
   **And** `rpe` range is validated (1-10) using `Field(ge=1.0, le=10.0)`
   **And** `rir` is non-negative integer using `Field(ge=0)`

7. **Given** a strength log with multiple exercises
   **When** parsed with Strength domain
   **Then** each exercise is extracted as a separate item in `exercises` list
   **And** exercise order from input is preserved

8. **Given** StrengthSet with both `rpe` and `rir` values
   **When** validating the model
   **Then** validation fails with `ValueError("rpe and rir are mutually exclusive")`
   **And** only one intensity metric can be set at a time

## Tasks / Subtasks

- [x] Task 1: Define StrengthEntry Pydantic schema (AC: #1, #3, #6, #7, #8)
  - [x] Create `packages/swealog/swealog/domains/strength.py`
  - [x] Define `StrengthSet` model for individual set data (reps, weight, weight_unit, rpe, rir, notes)
  - [x] Define `StrengthExercise` model for exercise + sets
  - [x] Define `StrengthEntry` model as log_schema (exercises list, session_notes, date)
  - [x] Use `Field(ge=1.0, le=10.0)` for `rpe` range validation (NOT redundant `@field_validator`)
  - [x] Use `Field(ge=0)` for `rir` non-negative validation
  - [x] Add `@model_validator(mode="after")` on StrengthSet to enforce RPE/RIR mutual exclusivity (AC: #8)
  - [x] Use `ConfigDict(strict=True)` for all models
  - [x] Add Google-style docstrings for all classes and fields
  - [x] Follow exact pattern from `general_fitness.py` (see reference file below)

- [x] Task 2: Define Strength vocabulary (AC: #4)
  - [x] **Reference:** Use `tests/corpus/exercise_equivalences.yaml` as authoritative source for Korean terms
  - [x] Include exercise name abbreviations (bp → bench press, sq → squat, dl → deadlift)
  - [x] Include Korean exercise names from `exercise_equivalences.yaml` (exact mappings, not approximations)
  - [x] Include common plural/verb forms (squats → squat, pressing → press)
  - [x] Include slang terms (deads → deadlift, pulls → pull)
  - [x] Include notation shortcuts (@ → RPE, rpe → RPE, rir → RIR - case insensitive handling)
  - [x] **Note:** weight_unit normalization happens in vocabulary, schema only accepts `Literal["kg", "lbs"]`

- [x] Task 3: Create Strength DomainModule class (AC: #2)
  - [x] Create `Strength(DomainModule)` class in strength.py
  - [x] Define comprehensive `description` for Router matching
  - [x] Set `log_schema = StrengthEntry`
  - [x] Define `vocabulary` dict with all normalizations (single canonical location)
  - [x] Define `expertise` with strength training knowledge
  - [x] Define `response_evaluation_rules` for strength-specific advice safety
  - [x] Define `context_management_guidance` for Observer patterns

- [x] Task 4: Create singleton instance (AC: #2, #5)
  - [x] Create `strength` singleton instance at module level (follow `general_fitness` pattern)
  - [x] Ensure instance is importable from `swealog.domains`

- [x] Task 5: Export from swealog.domains (AC: #5)
  - [x] Add `Strength`, `StrengthEntry`, `StrengthExercise`, `StrengthSet` to `domains/__init__.py`
  - [x] Add `strength` singleton to exports
  - [x] Update `__all__` list
  - [x] **Follow exact import pattern:** `from swealog.domains.strength import (...)`

- [x] Task 6: Add comprehensive tests (AC: #1-8)
  - [x] Test StrengthEntry instantiation with valid data
  - [x] Test StrengthEntry exercises list populated correctly
  - [x] Test rpe validation (valid 1-10, invalid <1 or >10)
  - [x] Test rpe boundary values (exactly 1.0 succeeds, exactly 10.0 succeeds)
  - [x] Test rir validation (valid >=0, invalid <0)
  - [x] Test rir boundary value (exactly 0 succeeds)
  - [x] **Test rpe and rir mutual exclusivity (AC: #8):** both set raises ValueError
  - [x] **Test rpe alone succeeds, rir alone succeeds, neither succeeds**
  - [x] Test weight_unit accepts only Literal["kg", "lbs"] (not "lb", "pounds", etc.)
  - [x] Test Strength domain instantiation
  - [x] Test vocabulary contains expected mappings (sample check, not exhaustive)
  - [x] Test expertise is non-empty
  - [x] Test response_evaluation_rules populated
  - [x] Test context_management_guidance populated
  - [x] Test domain name defaults to "Strength"
  - [x] Test integration with GeneralFitness (both can coexist)

- [x] Task 7: Validation and cleanup (AC: all)
  - [x] Run `make check` (lint + typecheck)
  - [x] Run `make validate` (full validation)
  - [x] Run `make test-ollama` (integration tests with real Ollama)
  - [x] Verify all exports work correctly
  - [x] Verify imports: `from swealog.domains import Strength, StrengthEntry, strength`

## Dev Notes

### Project Structure

**Location:** `packages/swealog/swealog/domains/`

```
packages/swealog/swealog/domains/
├── __init__.py       # Exports: GeneralFitness, Strength, schemas, instances
├── general_fitness.py # GeneralFitness domain (implemented in Story 1.4)
└── strength.py       # Strength domain (this story)
```

**Test Location:** `packages/swealog/tests/test_strength_domain.py`

### Schema Design

**From epics.md FR-A2 and agent-system-design.md:**

The Strength domain captures weight training activities with:
- Exercise name (required)
- Sets and reps (various notation formats)
- Weight and units
- Intensity metrics (RPE or RIR) - **mutually exclusive**
- Session-level notes

**Schema Hierarchy:**

```python
from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator


class StrengthSet(BaseModel):
    """A single set within an exercise.

    Attributes:
        reps: Number of repetitions performed.
        weight: Weight used for this set.
        weight_unit: Unit of weight (kg or lbs only - vocabulary normalizes variants).
        rpe: Rate of Perceived Exertion (1-10 scale). Mutually exclusive with rir.
        rir: Reps in Reserve (how many more reps could be done). Mutually exclusive with rpe.
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
        name: Exercise name (normalized via vocabulary). REQUIRED.
        sets: List of individual sets performed.
        total_sets: Total number of sets (if not itemized).
        notes: Notes about this exercise (e.g., "felt heavy", "new PR").
    """

    model_config = ConfigDict(strict=True)

    name: str  # REQUIRED - no default
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
```

**Note on Validation:**
- `rpe` uses `Field(ge=1.0, le=10.0)` for range validation - NO redundant `@field_validator`
- `rir` uses `Field(ge=0)` for non-negative validation
- Mutual exclusivity uses `@model_validator(mode="after")` - follows Pydantic v2 best practices
- `weight_unit` only accepts `Literal["kg", "lbs"]` - vocabulary handles normalization of "lb", "pounds", "#", etc.

### Vocabulary Design

**Authoritative Source:** `tests/corpus/exercise_equivalences.yaml` contains ground truth Korean→English mappings from CSV.

**CRITICAL:** Korean exercise names in vocabulary MUST match `exercise_equivalences.yaml` exactly. Do not invent mappings.

```python
vocabulary = {
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
    "x": "×",  # multiplication in sets (5x5)
    "sets": "sets",
    "set": "sets",
    "reps": "reps",
    "rep": "reps",
}
```

**Vocabulary Usage Notes:**
1. Weight unit normalization maps "lb", "pounds", "#" → "lbs" for vocabulary, but schema only accepts `Literal["kg", "lbs"]`
2. Korean names map to canonical CSV names (with equipment specifier) for accuracy testing
3. Case-insensitive intensity notation: "rpe", "RPE", "rir", "RIR" all normalized

### Domain Expertise

**Strength training knowledge for agent prompts:**

```python
expertise = (
    "Strength training principles: progressive overload, specificity, recovery. "
    "Common rep ranges: 1-5 strength, 6-12 hypertrophy, 12+ endurance. "
    "RPE scale: 6 easy, 7 moderate, 8 challenging, 9 hard, 10 maximum effort. "
    "RIR (Reps in Reserve): 0=failure, 1=one more possible, 2-3=controlled. "
    "Key compound lifts: squat, bench press, deadlift, overhead press, row. "
    "Common notation: 5x5 = 5 sets of 5 reps, 185x5 = 185 units for 5 reps. "
    "Volume calculation: sets × reps × weight = total volume. "
    "Periodization: deload weeks, linear progression, undulating patterns. "
    "Recovery indicators: sleep quality, soreness (DOMS), performance trends."
)
```

### Response Evaluation Rules

**Safety guidelines for strength-related responses:**

```python
response_evaluation_rules = [
    "Never recommend max effort lifts (1RM testing) without proper warmup context",
    "Always consider user's stated experience level for weight recommendations",
    "Flag potential overtraining: high frequency + high volume + high intensity",
    "Avoid specific weight recommendations without historical context",
    "Recommend deload if user reports persistent fatigue or strength decline",
    "Never suggest training through sharp or acute pain",
    "Consider recovery factors (sleep, stress) when analyzing performance dips",
]
```

### Context Management Guidance

**Observer patterns for strength tracking:**

```python
context_management_guidance = (
    "Track: exercise PRs (weight × reps for major lifts), training frequency per muscle group, "
    "volume progression (weekly tonnage trends), intensity patterns (average RPE trends), "
    "exercise selection changes. "
    "Flag: sudden strength drops (>10% on major lifts), training gaps >7 days, "
    "persistent high RPE (>9 average over 2+ weeks), dramatic volume spikes. "
    "Correlate: performance vs sleep notes, strength trends vs bodyweight changes."
)
```

### Relationship to GeneralFitness

Strength is a **subdomain** of GeneralFitness:
- GeneralFitness provides base activity tracking (any workout)
- Strength provides specialized schema for weight training details
- Both domains can be selected for the same input (e.g., "did bench and ran")
- Vocabularies merge when both are active

**Domain Selection Example:**
```python
# Input: "bench 185x5, then 20 min jog"
# Router selects: ["general_fitness", "strength"]
# Parser extracts:
#   - Strength domain: {"exercises": [{"name": "bench press", ...}]}
#   - GeneralFitness domain: {"activity_type": "cardio", "duration_minutes": 20, ...}
```

### Test Strategy

**Test Class Organization:**

```python
class TestStrengthSetValidation:
    """Tests for StrengthSet model validation."""

    def test_valid_rpe_range(self): ...
    def test_rpe_boundary_one_succeeds(self): ...
    def test_rpe_boundary_ten_succeeds(self): ...
    def test_rpe_below_one_raises(self): ...
    def test_rpe_above_ten_raises(self): ...
    def test_valid_rir_non_negative(self): ...
    def test_rir_boundary_zero_succeeds(self): ...
    def test_rir_negative_raises(self): ...
    def test_weight_unit_kg_succeeds(self): ...
    def test_weight_unit_lbs_succeeds(self): ...
    def test_weight_unit_invalid_raises(self): ...  # "lb", "pounds" NOT accepted by schema

    # RPE/RIR mutual exclusivity (AC: #8)
    def test_rpe_and_rir_both_set_raises(self): ...
    def test_rpe_only_succeeds(self): ...
    def test_rir_only_succeeds(self): ...
    def test_neither_rpe_nor_rir_succeeds(self): ...


class TestStrengthExerciseModel:
    """Tests for StrengthExercise model."""

    def test_exercise_name_required(self): ...
    def test_exercise_missing_name_raises(self): ...
    def test_sets_list_default_empty(self): ...
    def test_notes_optional(self): ...


class TestStrengthEntryModel:
    """Tests for StrengthEntry log schema."""

    def test_exercises_list_default_empty(self): ...
    def test_valid_entry_with_exercises(self): ...
    def test_perceived_difficulty_range(self): ...
    def test_perceived_difficulty_boundary_one_succeeds(self): ...
    def test_perceived_difficulty_boundary_ten_succeeds(self): ...


class TestStrengthDomainModule:
    """Tests for Strength DomainModule configuration."""

    def test_instantiation(self): ...
    def test_name_defaults_to_class_name(self): ...
    def test_description_non_empty(self): ...
    def test_vocabulary_contains_abbreviations(self): ...
    def test_vocabulary_contains_korean_terms(self): ...
    def test_vocabulary_korean_maps_to_canonical_csv_names(self): ...  # Verify against exercise_equivalences.yaml
    def test_expertise_non_empty(self): ...
    def test_response_evaluation_rules_populated(self): ...
    def test_context_management_guidance_populated(self): ...


class TestStrengthSingleton:
    """Tests for strength singleton instance."""

    def test_singleton_importable(self): ...
    def test_singleton_is_strength_instance(self): ...


class TestStrengthIntegration:
    """Integration tests with GeneralFitness domain."""

    def test_strength_and_general_fitness_coexist(self): ...
    def test_imports_from_swealog_domains(self): ...  # from swealog.domains import Strength, strength
```

**Example Test Implementation (RPE/RIR Mutual Exclusivity):**

```python
import pytest
from swealog.domains.strength import StrengthSet

def test_rpe_and_rir_both_set_raises():
    """Test that setting both rpe and rir raises ValueError."""
    with pytest.raises(ValueError, match="rpe and rir are mutually exclusive"):
        StrengthSet(reps=5, weight=100.0, weight_unit="kg", rpe=8.0, rir=2)

def test_rpe_only_succeeds():
    """Test that rpe alone is valid."""
    s = StrengthSet(reps=5, weight=100.0, weight_unit="kg", rpe=8.0)
    assert s.rpe == 8.0
    assert s.rir is None

def test_rir_only_succeeds():
    """Test that rir alone is valid."""
    s = StrengthSet(reps=5, weight=100.0, weight_unit="kg", rir=2)
    assert s.rir == 2
    assert s.rpe is None
```

### Previous Story Learnings (Story 2.3)

**Patterns to Follow:**
- Use `ConfigDict(strict=True)` for all Pydantic models
- Google-style docstrings for all public classes/methods (required for ruff pydocstyle)
- Export all public classes in `__all__`
- Use `Field(ge=1, le=10)` for range validation - do NOT add redundant `@field_validator`
- Use `@model_validator(mode="after")` for cross-field validation (e.g., mutual exclusivity)
- Comprehensive test coverage including boundary value tests
- Follow `general_fitness.py` pattern exactly for domain module structure

**Code Review Common Issues to Avoid:**
- Missing docstrings on any public method or field
- Forgetting boundary value tests (exactly 1.0, exactly 10.0, exactly 0)
- Not testing validation error messages with `pytest.raises(ValueError, match="...")`
- Using both `Field(ge=..., le=...)` AND `@field_validator` for same constraint (redundant)
- Schema accepting raw user input variants (e.g., "lb") instead of normalized values only

**Reference Implementation:**
See `packages/swealog/swealog/domains/general_fitness.py` for exact pattern to follow.

### Architecture Compliance

**From architecture.md and epics.md:**
- Strength domain is a Swealog (application) component, NOT Quilto (framework)
- Lives in `packages/swealog/swealog/domains/`
- Uses DomainModule interface from Quilto
- Will be used by Parser agent for structured extraction

**From FR-A2:**
> FR-A2: Provide Strength subdomain (sets, reps, RPE, weight)

### Validation Commands

Run frequently during development:
```bash
# Quick validation
make check

# Full validation (before commits)
make validate

# Integration tests (REQUIRED before marking done)
make test-ollama
```

**Integration Test Requirements for Strength Domain:**
- `make test-ollama` must pass before marking story complete
- Integration tests verify Strength schema works with real LLM parsing
- No new integration test file needed - existing test infrastructure covers domain modules

### File Skeleton

Copy this as starting point for `packages/swealog/swealog/domains/strength.py`:

```python
"""Strength domain module for Swealog.

This module provides the Strength subdomain for weight training,
including sets, reps, RPE, weight, and exercise tracking.
"""

from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator
from quilto import DomainModule


class StrengthSet(BaseModel):
    """A single set within an exercise."""

    model_config = ConfigDict(strict=True)

    # TODO: Add fields and validation per schema design


class StrengthExercise(BaseModel):
    """A single exercise with its sets."""

    model_config = ConfigDict(strict=True)

    name: str  # REQUIRED
    # TODO: Add remaining fields


class StrengthEntry(BaseModel):
    """Parsed structure for a strength training log entry."""

    model_config = ConfigDict(strict=True)

    exercises: list[StrengthExercise] = []
    # TODO: Add remaining fields


class Strength(DomainModule):
    """Domain module for strength training activities."""


# Singleton instance
strength = Strength(
    description="...",
    log_schema=StrengthEntry,
    vocabulary={
        # TODO: Add vocabulary from design section
    },
    expertise="...",
    response_evaluation_rules=[
        # TODO: Add rules from design section
    ],
    context_management_guidance="...",
)
```

### Export Pattern for __init__.py

Add to `packages/swealog/swealog/domains/__init__.py`:

```python
from swealog.domains.strength import (
    Strength,
    StrengthEntry,
    StrengthExercise,
    StrengthSet,
    strength,
)

__all__ = [
    # ... existing exports ...
    "Strength",
    "StrengthEntry",
    "StrengthExercise",
    "StrengthSet",
    "strength",
]
```

### References

- [Source: epics.md#Story-2.4] Story definition
- [Source: epics.md#FR-A2] Functional requirement
- [Source: agent-system-design.md] Domain module interface usage
- [Source: architecture.md#Technical-Stack] Pydantic validation requirements
- [Source: project-context.md#Where-Code-Belongs] Swealog vs Quilto separation
- [Source: general_fitness.py] Existing domain module pattern - **follow this exactly**
- [Source: exercise_equivalences.yaml] Korean exercise name mappings - **authoritative source for Korean terms**
- [Source: 2-3-implement-parser-agent.md] Previous story patterns

---

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

None required.

### Completion Notes List

- Implemented StrengthSet, StrengthExercise, StrengthEntry Pydantic models with strict config
- RPE validation: Field(ge=1.0, le=10.0)
- RIR validation: Field(ge=0)
- RPE/RIR mutual exclusivity enforced via @model_validator(mode="after")
- weight_unit restricted to Literal["kg", "lbs"] - vocabulary handles normalization
- Comprehensive vocabulary with 60+ entries including Korean exercise names from exercise_equivalences.yaml
- Domain expertise, response_evaluation_rules, and context_management_guidance defined per story spec
- 44 unit tests covering all acceptance criteria including boundary values
- All validation passed: make check, make validate, make test-ollama (455 tests passed)

### File List

- packages/swealog/swealog/domains/strength.py (NEW)
- packages/swealog/swealog/domains/__init__.py (MODIFIED - added exports)
- packages/swealog/tests/test_strength_domain.py (NEW)

### Code Review (Amelia Dev Agent - 2026-01-12)

**Reviewer:** Amelia (Claude Opus 4.5)

**Findings & Fixes Applied:**
1. **[M3 FIXED]** Added `Field(min_length=1)` to `StrengthExercise.name` to prevent empty string names
2. **[M3 FIXED]** Added test `test_exercise_empty_name_raises` to validate empty name rejection
3. **[H2 FIXED]** Reverted unrelated formatting change to `tests/test_conftest_fixtures.py` (not part of story scope)

**Final Validation:**
- `make check`: ✅ passed
- `make validate`: ✅ 453 passed, 7 skipped
- `make test-ollama`: ✅ 456 passed, 4 skipped (integration tests with real Ollama)

