# Story 1.5: Generate Expected Parser Outputs from Ground Truth

Status: done

## Story

As a **Swealog developer**,
I want **expected ParserOutput JSON generated from Strong CSV**,
So that **Parser accuracy can be validated against real structured data (NFR-F4)**.

## Quick Reference

| Item | Path |
|------|------|
| Input CSV | `tests/corpus/fitness/ground_truth/strong_workouts.csv` |
| Input entries | `tests/corpus/fitness/entries/from_csv/` (93 files) |
| Output JSON | `tests/corpus/fitness/expected/parser/{YYYY-MM-DD}.json` |
| Output YAML | `tests/corpus/exercise_equivalences.yaml` |
| Schema file | `tests/corpus/schemas/expected_output.py` |
| Script | `scripts/generate_expected_outputs.py` |

## Acceptance Criteria

1. **Given** the 93 synthesized entries in `tests/corpus/fitness/entries/from_csv/`
   **When** I run the corpus generation script
   **Then** each entry has matching expected JSON in `tests/corpus/fitness/expected/parser/`

2. **Given** the expected outputs are being generated
   **When** the script processes the CSV ground truth
   **Then** expected outputs are derived from `strong_workouts.csv` (not LLM-generated)

3. **Given** the expected outputs are generated
   **When** I check the field mapping
   **Then** field mapping covers exercise, weight, reps, sets, date

4. **Given** the script completes
   **When** I check `tests/corpus/`
   **Then** `exercise_equivalences.yaml` exists with all unique exercises from CSV (~25-30 entries)

5. **Given** the equivalence file is created
   **When** I check each entry
   **Then** each equivalence entry starts with the CSV exercise name as the canonical form

## Tasks / Subtasks

- [x] Task 1: Analyze CSV structure and design expected output format (AC: #2, #3)
  - [x] 1.1 Parse `tests/corpus/fitness/ground_truth/strong_workouts.csv` to understand all columns
  - [x] 1.2 Design `ParserOutput` JSON schema matching `GeneralFitnessEntry` structure
  - [x] 1.3 Define field mapping: CSV columns → expected JSON fields (see CSV Column Constants below)
  - [x] 1.4 Document edge cases: bodyweight exercises (weight=0→None), reps as decimals (convert float→int), missing RPE (ignore)
  - [x] 1.5 Create `tests/corpus/schemas/expected_output.py` with `ExpectedSetDetail`, `ExpectedExerciseRecord`, `ExpectedParserOutput` models

- [x] Task 2: Create expected output directory structure (AC: #1)
  - [x] 2.1 Create `tests/corpus/fitness/expected/` directory
  - [x] 2.2 Create `tests/corpus/fitness/expected/parser/` directory
  - [x] 2.3 Verify structure matches corpus README.md expectations

- [x] Task 3: Build CSV-to-expected-JSON generation script (AC: #1, #2, #3)
  - [x] 3.1 Create `scripts/generate_expected_outputs.py`
  - [x] 3.2 Parse CSV using Python csv module with `encoding='utf-8-sig'` (handles Excel BOM)
  - [x] 3.3 Extract date from CSV datetime: `datetime.strptime(row[CSV_DATE], '%Y-%m-%d %H:%M:%S').date().isoformat()`
  - [x] 3.4 Group CSV rows by date (each date = one entry file in `from_csv/`)
  - [x] 3.5 For each date, aggregate exercises:
    - Group by exercise name (preserve order from CSV)
    - Collect all sets with weight/reps
    - Convert reps: `int(float(row[CSV_REPS]))` (truncate decimal)
    - Handle weight: `None if float(row[CSV_WEIGHT]) == 0 else float(row[CSV_WEIGHT])`
  - [x] 3.6 Generate `ExpectedParserOutput`-compatible JSON:
    - `activity_type`: "workout"
    - `exercises`: list with `set_details` for per-set accuracy
    - `date`: from CSV datetime (YYYY-MM-DD)
  - [x] 3.7 Write expected JSON to `tests/corpus/fitness/expected/parser/{YYYY-MM-DD}.json`
  - [x] 3.8 Add CLI flags: `--dry-run` (preview without writing), `--verbose` (detailed logging)

- [x] Task 4: Extract unique exercises and create equivalences file (AC: #4, #5)
  - [x] 4.1 Collect all unique exercise names from CSV (English names) - strip whitespace (note: "Ab Mat Sit-up " has trailing space)
  - [x] 4.2 Create `tests/corpus/exercise_equivalences.yaml` with structure:
    ```yaml
    # Exercise name equivalences for semantic comparison
    # Canonical name (from CSV) → list of equivalent forms
    "Trap Bar Deadlift":
      - "Trap Bar Deadlift"  # canonical
      - "트랩바 데드리프트"    # Korean
    "Bench Press (Barbell)":
      - "Bench Press (Barbell)"
      - "바벨 벤치프레스"
      - "벤치프레스"
    # ... etc
    ```
  - [x] 4.3 Include Korean translations from SYNTHESIS_RULES.md (20+ exercises listed)
  - [x] 4.4 Ensure each entry has canonical form as first item
  - [x] 4.5 Validate: all exercises from SYNTHESIS_RULES.md translation table appear in equivalences file

- [x] Task 5: Handle special cases in expected output generation (AC: #2, #3)
  - [x] 5.1 Handle bodyweight exercises: `if float(row[CSV_WEIGHT]) == 0: weight = None`
  - [x] 5.2 Handle high rep counts (e.g., Ab Mat Sit-up 120.0): treat as reps count, convert `int(float(value))`
  - [x] 5.3 Handle empty/null RPE: skip field entirely (not in expected output)
  - [x] 5.4 Handle decimal weights: preserve as-is (84.8, 77.5, etc.) - do NOT round
  - [x] 5.5 Handle multiple exercises per workout: group by exercise name within each date, preserve CSV order

- [x] Task 6: Validate generated expected outputs (AC: #1, #2)
  - [x] 6.1 Verify expected JSON count matches `from_csv/` entry count: `assert len(expected_files) == len(from_csv_files) == 93`
  - [x] 6.2 Verify each JSON is valid and parseable with `ExpectedParserOutput.model_validate_json()`
  - [x] 6.3 Verify JSON structure matches `ExpectedParserOutput` schema (NOT `GeneralFitnessEntry` - uses extended schema)
  - [x] 6.4 Spot-check: 2019-01-28 should have 2 exercises (Trap Bar Deadlift 5 sets, Push Press 5 sets)

- [x] Task 7: Run linting and type checking (AC: all)
  - [x] 7.1 Run `uv run ruff check scripts/` (if script placed there)
  - [x] 7.2 Run `uv run pyright scripts/`
  - [x] 7.3 Ensure script passes all quality checks

## Dev Notes

### Architecture Compliance

This story implements NFR-F4 from architecture document:
- **NFR-F4**: Parsing accuracy > 90% (requires test corpus validation)

This is **test infrastructure**, not application code:
- Scripts go in `scripts/` directory
- Expected outputs are test fixtures, not runtime data
- `exercise_equivalences.yaml` enables semantic comparison in accuracy tests (Story 1.7)
- Test schemas go in `tests/corpus/schemas/` (NOT in application packages)

### CSV Column Constants

Define these constants at script top for maintainability:

```python
# CSV column names (Korean headers)
CSV_DATE = "날짜"
CSV_WORKOUT_NAME = "워크아웃 이름"
CSV_DURATION = "지속 시간"
CSV_EXERCISE = "운동 이름"
CSV_SET_NUM = "세트 순서"
CSV_WEIGHT = "체중"
CSV_REPS = "렙"
CSV_DISTANCE = "거리"
CSV_SECONDS = "초"
CSV_RPE = "RPE"
```

### CSV Ground Truth Structure

From `tests/corpus/fitness/ground_truth/strong_workouts.csv`:

| Column | Type | Description | Handling |
|--------|------|-------------|----------|
| 날짜 | datetime | "2019-01-28 19:00:00" | Extract date: `strptime(...).date().isoformat()` |
| 워크아웃 이름 | string | Session name | NOT used in expected output |
| 지속 시간 | string | "1시간", "36분" | NOT used in expected output |
| 운동 이름 | string | English exercise name | Strip whitespace (trailing space exists) |
| 세트 순서 | int | Set number (1, 2, 3...) | Use for `set_details[].set_num` |
| 체중 | float | Weight in kg | `None if value == 0 else value` |
| 렙 | float | Reps count | `int(float(value))` - always treat as reps |
| 거리 | int | Distance (always 0) | Skip - unused |
| 초 | float | Seconds (always 0.0) | Skip - unused |
| RPE | empty | Unused in data | Skip - unused |

**CSV Parsing Requirement:** Use `encoding='utf-8-sig'` to handle Excel BOM marker.

### Expected Output Format

Expected outputs use a **test-specific schema** (`ExpectedParserOutput`) that extends `GeneralFitnessEntry` with `set_details` for per-set accuracy testing.

**Example:** `tests/corpus/fitness/expected/parser/2019-01-28.json`
```json
{
  "activity_type": "workout",
  "exercises": [
    {
      "name": "Trap Bar Deadlift",
      "sets": 5,
      "weight_unit": "kg",
      "set_details": [
        {"set_num": 1, "weight": 180.0, "reps": 8},
        {"set_num": 2, "weight": 190.0, "reps": 6},
        {"set_num": 3, "weight": 190.0, "reps": 4},
        {"set_num": 4, "weight": 180.0, "reps": 6},
        {"set_num": 5, "weight": 180.0, "reps": 6}
      ]
    },
    {
      "name": "Push Press",
      "sets": 5,
      "weight_unit": "kg",
      "set_details": [
        {"set_num": 1, "weight": 40.0, "reps": 8},
        {"set_num": 2, "weight": 50.0, "reps": 8},
        {"set_num": 3, "weight": 50.0, "reps": 6},
        {"set_num": 4, "weight": 45.0, "reps": 6},
        {"set_num": 5, "weight": 45.0, "reps": 6}
      ]
    }
  ],
  "date": "2019-01-28"
}
```

**Design Decision:** Use separate `ExpectedParserOutput` schema (Option 2) to keep application code clean while enabling precise per-set accuracy testing.


### Exercise Equivalences from SYNTHESIS_RULES.md

The following mappings are already documented in `tests/corpus/variation_rules/SYNTHESIS_RULES.md`:

| English (CSV) | Korean |
|---------------|--------|
| Trap Bar Deadlift | 트랩바 데드리프트 |
| Push Press | 푸쉬프레스 |
| Bench Press (Barbell) | 바벨 벤치프레스 / 벤치프레스 |
| Front Squat (Barbell) | 프론트 스쿼트 |
| Incline Bench Press (Barbell) | 인클라인 벤치프레스 |
| Sumo Deadlift (Barbell) | 스모 데드리프트 |
| Seated Overhead Press (Barbell) | 시티드 프레스 |
| T Bar Row | 티바로우 |
| Iso-Lateral Chest Press (Machine) | 머신 체스트프레스 |
| Pull Up | 풀업 |
| Ab Mat Sit-up | 싯업 |
| ... (see SYNTHESIS_RULES.md for full list) |

### Unique Exercises in CSV (to extract)

Based on CSV sample, unique exercises include (at minimum):
- Trap Bar Deadlift
- Push Press
- Bench Press (Barbell)
- Ab Mat Sit-up
- Front Squat (Barbell)
- Seated Overhead Press (Barbell)
- Incline Bench Press (Barbell)
- T Bar Row
- Sumo Deadlift (Barbell)
- Iso-Lateral Chest Press (Machine)

Full list will be extracted by script.

### Technical Constraints

| Constraint | Requirement |
|------------|-------------|
| Python | 3.13+ |
| Dependencies | Minimal (csv, yaml, json modules only) |
| Docstrings | Google-style for all functions |
| Type hints | Full typing, pyright strict |
| Linting | ruff must pass |

### File Structure After This Story

```
tests/corpus/
├── README.md                          # (existing)
├── exercise_equivalences.yaml         # NEW - semantic comparison map
├── schemas/                           # NEW
│   ├── __init__.py                   # NEW - exports test schemas
│   └── expected_output.py            # NEW - ExpectedParserOutput, etc.
├── variation_rules/
│   └── SYNTHESIS_RULES.md            # (existing)
└── fitness/
    ├── ground_truth/
    │   └── strong_workouts.csv       # (existing)
    ├── entries/
    │   └── from_csv/                 # (existing - 93 files)
    │       └── {YYYY-MM-DD}.md
    └── expected/                      # NEW
        └── parser/                    # NEW
            └── {YYYY-MM-DD}.json      # 93 expected output files

scripts/
└── generate_expected_outputs.py       # NEW - generation script with CLI
```

### Previous Story Learnings (Story 1.4)

From GeneralFitness implementation:
- Use `ConfigDict(strict=True)` for Pydantic models
- All public functions need Google-style docstrings
- Tests should validate structure, not just existence
- `pyproject.toml` has `--import-mode=importlib` for pytest
- pyright and ruff must pass with 0 errors

### Git Intelligence

Recent commits show:
- Story 1.4: Created `GeneralFitness`, `GeneralFitnessEntry`, `ExerciseRecord` schemas
- Story 1.3: LLM client abstraction with tiered config
- Story 1.2: `DomainModule` interface with Pydantic

Files created in Story 1.4:
- `packages/swealog/swealog/domains/general_fitness.py`
- `packages/swealog/tests/test_general_fitness.py`

### Test Schema Definition

Create `tests/corpus/schemas/expected_output.py`:

```python
"""Test schemas for expected parser outputs.

These schemas extend application schemas with set_details for precise
per-set accuracy testing. NOT part of application code.
"""

from pydantic import BaseModel, ConfigDict


class ExpectedSetDetail(BaseModel):
    """Per-set details for accuracy testing."""

    model_config = ConfigDict(strict=True)

    set_num: int
    weight: float | None = None
    reps: int | None = None


class ExpectedExerciseRecord(BaseModel):
    """Exercise with per-set details for accuracy testing."""

    model_config = ConfigDict(strict=True)

    name: str
    sets: int
    set_details: list[ExpectedSetDetail] = []
    weight_unit: str = "kg"


class ExpectedParserOutput(BaseModel):
    """Expected parser output for accuracy comparison."""

    model_config = ConfigDict(strict=True)

    activity_type: str = "workout"
    exercises: list[ExpectedExerciseRecord]
    date: str
```

Also create `tests/corpus/schemas/__init__.py` exporting these classes.

### Critical Implementation Notes

1. **Do NOT use LLM** - derive expected outputs directly from CSV (ground truth)
2. **Idempotent** - running multiple times produces identical output
3. **CSV encoding** - use `encoding='utf-8-sig'` for Korean characters with BOM
4. **Date from CSV** - extract YYYY-MM-DD from datetime column, NOT from filename
5. **Validate count** - assert 93 expected outputs match 93 `from_csv/` entries
6. **Strip exercise names** - CSV has trailing whitespace (e.g., "Ab Mat Sit-up ")

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 1.5]
- [Source: _bmad-output/planning-artifacts/architecture.md#Testing Strategy]
- [Source: tests/corpus/README.md - Corpus structure]
- [Source: tests/corpus/variation_rules/SYNTHESIS_RULES.md - Exercise translations]
- [Source: packages/swealog/swealog/domains/general_fitness.py - Schema reference]

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

- Handled CSV edge case: "F" (failed set marker) in set_num column - row 628 skipped

### Completion Notes List

- Created `ExpectedSetDetail`, `ExpectedExerciseRecord`, `ExpectedParserOutput` Pydantic models in `tests/corpus/schemas/`
- Built `scripts/generate_expected_outputs.py` with --dry-run and --verbose CLI flags
- Generated 93 expected JSON files matching 93 from_csv entries
- Created `exercise_equivalences.yaml` with 34 unique exercises and Korean translations
- All edge cases handled: bodyweight (weight=None), decimal reps (int truncation), decimal weights (preserved), failed set markers (skipped)
- Spot-check verified: 2019-01-28.json has Trap Bar Deadlift (5 sets) and Push Press (5 sets)
- All 93 JSON files validated against ExpectedParserOutput schema
- ruff check: passed, pyright: 0 errors
- Full test suite: 97 tests passed

### File List

- tests/corpus/schemas/__init__.py (new)
- tests/corpus/schemas/expected_output.py (new)
- tests/corpus/fitness/expected/parser/*.json (93 new files)
- tests/corpus/exercise_equivalences.yaml (new)
- scripts/generate_expected_outputs.py (new)
- tests/__init__.py (new - for package import)
- tests/corpus/__init__.py (new - for package import)
- tests/corpus/test_expected_schemas.py (new - code review fix)
- tests/test_generate_expected_outputs.py (new - code review fix)

### Code Review Fixes Applied

1. **Added unit tests for test schema models** - `tests/corpus/test_expected_schemas.py` (12 tests)
2. **Added tests for script output validation** - `tests/test_generate_expected_outputs.py` (13 tests)
3. **Fixed empty `__init__.py` files** - Added docstrings to `tests/__init__.py` and `tests/corpus/__init__.py`
4. Full test suite: 122 tests passed, ruff check passed, pyright 0 errors
