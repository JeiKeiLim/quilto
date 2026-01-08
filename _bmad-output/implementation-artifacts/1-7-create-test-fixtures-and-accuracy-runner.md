# Story 1.7: Create Test Fixtures and Accuracy Runner

Status: done

## Story

As a **Swealog developer**,
I want **pytest fixtures and an accuracy test runner**,
So that **I can run parser accuracy tests locally with semantic exercise name comparison**.

## Quick Reference

| Item | Path |
|------|------|
| conftest.py output | `tests/conftest.py` |
| Accuracy runner | `tests/accuracy/test_parser_accuracy.py` |
| Exercise equivalences | `tests/corpus/exercise_equivalences.yaml` (34 exercises) |
| Expected outputs (from_csv) | `tests/corpus/fitness/expected/parser/*.json` (93 files) |
| Expected outputs (synthetic) | `tests/corpus/fitness/expected/parser/synthetic/*.json` (50 files) |
| Test schemas | `tests/corpus/schemas/expected_output.py` |
| `is_synthetic()` utility | `tests/corpus/schemas/expected_output.py` |
| LLMClient | `packages/quilto/quilto/llm/client.py` |
| DomainModule | `packages/quilto/quilto/domain.py` |

## Acceptance Criteria

1. **Given** pytest is configured in the monorepo (Story 1.1)
   **When** I run the accuracy test suite
   **Then** `conftest.py` provides core fixtures: `mock_llm`, `storage_fixture`, `domain_fixture`

2. **Given** accuracy tests are running
   **When** expected outputs are loaded
   **Then** accuracy runner loads expected JSON from `tests/corpus/fitness/expected/parser/`

3. **Given** exercise name comparison is performed
   **When** comparing parser output to expected
   **Then** accuracy runner uses `exercise_equivalences.yaml` for exercise name comparison

4. **Given** numeric field comparison is performed
   **When** comparing weight, reps, sets
   **Then** numeric fields (weight, reps, sets) use exact match comparison

5. **Given** accuracy tests complete
   **When** results are reported
   **Then** test output reports field-level accuracy (per field) and entry-level accuracy (all fields correct)

6. **Given** integration testing is needed
   **When** running pytest
   **Then** `--use-real-ollama` pytest option is available for integration testing

## Tasks / Subtasks

- [x] Task 1: Create `tests/conftest.py` with core fixtures (AC: #1)
  - [x] 1.1 Create `mock_llm` fixture that returns canned LLM responses
    - **CRITICAL:** Check if `packages/quilto/tests/conftest.py` fixtures can be imported first
    - If import fails, create compatible fixture that patches `litellm.acompletion`
    - Use `unittest.mock.AsyncMock` for async method mocking
    - Store canned responses in `tests/fixtures/llm_responses/` as JSON files
  - [x] 1.2 Create `storage_fixture` providing isolated file storage per test
    - Use `pytest.tmp_path` for isolation
    - Create `logs/(raw|parsed)/{YYYY}/{MM}/` directory structure (per AR2)
    - Stub implementation initially (real StorageRepository comes in Story 2.1)
  - [x] 1.3 Create `domain_fixture` providing test domain module instances
    - Return `general_fitness` singleton from `swealog.domains.general_fitness`
    - Support parameterized domains for future subdomain testing via `pytest.param`
  - [x] 1.4 Register `--use-real-ollama` pytest option via `pytest_addoption` hook
    - Add `use_real_ollama` fixture that returns boolean based on CLI flag
    - Use with `@pytest.mark.integration` marker for real LLM tests

- [x] Task 2: Create exercise name comparison utility (AC: #3)
  - [x] 2.1 Create `tests/accuracy/comparators.py` with `ExerciseEquivalenceChecker` class
    - Load `exercise_equivalences.yaml` once at initialization using:
      ```python
      import yaml
      with open(yaml_path, encoding="utf-8") as f:
          data = yaml.safe_load(f)
      ```
    - Provide `is_equivalent(actual: str, expected: str) -> bool` method
    - Canonical form lookup: check if actual matches any equivalent of expected's canonical
    - Build reverse lookup dict at init: `{variant.lower(): canonical for canonical, variants in data.items() for variant in variants}`
  - [x] 2.2 Handle case-insensitive comparison (normalize to lowercase before lookup)
  - [x] 2.3 Handle missing exercises (return False, not error - unknown exercises don't match)

- [x] Task 3: Create numeric field comparison utilities (AC: #4)
  - [x] 3.1 Add `compare_weight(actual: float | None, expected: float | None) -> bool` to comparators.py
    - Exact match for non-None values
    - Both None = match, one None = no match
  - [x] 3.2 Add `compare_reps(actual: int | None, expected: int | None) -> bool`
    - Exact match comparison
  - [x] 3.3 Add `compare_sets(actual: int, expected: int) -> bool`
    - Exact match comparison

- [x] Task 4: Create accuracy runner test module (AC: #2, #5)
  - [x] 4.1 Create `tests/accuracy/__init__.py`
  - [x] 4.2 Create `tests/accuracy/test_parser_accuracy.py`
    - Load all expected JSON from `tests/corpus/fitness/expected/parser/*.json` using:
      ```python
      from pathlib import Path
      from tests.corpus.schemas import ExpectedParserOutput, is_synthetic

      corpus_path = Path(__file__).parent.parent / "corpus" / "fitness" / "expected" / "parser"
      for json_file in corpus_path.glob("*.json"):
          if is_synthetic(json_file):
              continue  # Skip synthetic entries
          expected = ExpectedParserOutput.model_validate_json(json_file.read_text())
      ```
    - Filter out synthetic entries using `is_synthetic()` function
    - Compare against mock parser output (placeholder until Parser exists in Story 2.3)
  - [x] 4.3 Implement `AccuracyMetrics` dataclass:
    ```python
    @dataclass
    class AccuracyMetrics:
        total_entries: int
        correct_entries: int  # All fields correct
        field_metrics: dict[str, FieldAccuracy]  # Per-field stats

    @dataclass
    class FieldAccuracy:
        total: int
        correct: int
        accuracy: float
    ```
  - [x] 4.4 Implement field-level accuracy calculation:
    - `exercise_name_accuracy`: Uses `ExerciseEquivalenceChecker`
    - `sets_accuracy`: Exact match on set count
    - `weight_accuracy`: Exact match per set_detail
    - `reps_accuracy`: Exact match per set_detail
  - [x] 4.5 Implement entry-level accuracy (all fields must be correct)
  - [x] 4.6 Create test output report showing:
    - Total entries tested (from_csv only, excluding synthetic)
    - Entry-level accuracy percentage
    - Field-level accuracy breakdown

- [x] Task 5: Create placeholder parser output generator (AC: #2)
  - [x] 5.1 Create `tests/accuracy/mock_parser.py` with placeholder implementation
    - Returns empty/default `ExpectedParserOutput` structure
    - Will be replaced with real Parser output in Story 2.3
    - Interface must match expected Parser signature:
      ```python
      async def parse_entry(raw_text: str, domain: DomainModule) -> ExpectedParserOutput:
          """Placeholder - returns empty workout until Parser exists."""
          return ExpectedParserOutput(exercises=[], date="placeholder")
      ```
  - [x] 5.2 Mark accuracy tests to skip until Parser exists:
    ```python
    @pytest.mark.skip(reason="Parser not implemented - Story 2.3")
    @pytest.mark.accuracy
    class TestParserAccuracy:
        ...
    ```

- [x] Task 6: Add pytest markers and configuration (AC: #6)
  - [x] 6.1 Add `accuracy` marker in `pyproject.toml`:
    ```toml
    [tool.pytest.ini_options]
    markers = [
        "accuracy: marks tests as accuracy tests (deselect with '-m \"not accuracy\"')",
        "integration: marks tests that require real Ollama (run with --use-real-ollama)",
    ]
    ```
  - [x] 6.2 Add integration marker for real Ollama tests
  - [x] 6.3 Create helper fixture to conditionally skip integration tests

- [x] Task 7: Run linting and type checking (AC: all)
  - [x] 7.1 Run `uv run ruff check tests/conftest.py tests/accuracy/`
  - [x] 7.2 Run `uv run pyright tests/conftest.py tests/accuracy/`
  - [x] 7.3 Run `uv run pytest tests/ -v` to verify test discovery
  - [x] 7.4 Verify existing tests still pass

## Dev Notes

### Architecture Compliance

This story implements **test infrastructure** for NFR-F4 (parsing accuracy > 90%):
- Accuracy metrics use `from_csv/` entries (93 files) as gold standard
- Synthetic entries (50 files) are **excluded** from primary accuracy via `is_synthetic()`
- Full accuracy testing requires Parser agent (Story 2.3)

### Technical Constraints

| Constraint | Requirement |
|------------|-------------|
| Python | 3.13+ (from pyproject.toml) |
| pytest | >= 8.0.0 |
| pytest-asyncio | >= 0.24.0 |
| Docstrings | Google-style, strict pydocstyle |
| Type hints | Full typing, pyright strict |
| Linting | ruff must pass |

### CRITICAL: Existing Test Infrastructure to Extend

**Existing `mock_llm` Fixtures (MUST REUSE):**
`packages/quilto/tests/conftest.py` already has LLM mocking fixtures:
```python
# Existing pattern - DO NOT recreate, extend for root tests/conftest.py
@pytest.fixture
def mock_llm() -> Generator[Callable[[dict[str, str]], None], None, None]:
    # Patches litellm.acompletion with canned responses
    # Returns set_responses(dict) to configure responses per model
    # Exposes _mock and _call_history for advanced testing
```

**Story 1.7 Action:** Create `tests/conftest.py` that either:
1. Imports and re-exports quilto fixtures, OR
2. Creates compatible fixtures with same interface

### Existing Infrastructure to Reuse

**From Story 1.5 (expected outputs):**
- `ExpectedParserOutput`, `ExpectedExerciseRecord`, `ExpectedSetDetail` schemas
- 93 expected JSON files in `tests/corpus/fitness/expected/parser/`
- Import: `from tests.corpus.schemas import ExpectedParserOutput, is_synthetic`

**From Story 1.6 (synthetic entries):**
- `is_synthetic()` function for filtering synthetic entries
- 50 synthetic entries (to be excluded from accuracy)

**From Story 1.3 (LLM client):**
- `LLMClient` class from `quilto.llm.client`
- `LLMConfig`, `AgentConfig`, `ProviderConfig`, `TierModels` from `quilto.llm.config`

**From Story 1.4 (GeneralFitness):**
- `general_fitness` singleton from `swealog.domains.general_fitness`
- `DomainModule` base class from `quilto.domain`

### File Structure After This Story

```
tests/
├── __init__.py                    # (may need to create)
├── conftest.py                    # NEW - core fixtures
├── fixtures/
│   └── llm_responses/             # NEW - canned LLM responses
│       └── parser_response.json   # NEW - example canned response
├── accuracy/
│   ├── __init__.py                # NEW
│   ├── comparators.py             # NEW - exercise equivalence checker
│   ├── mock_parser.py             # NEW - placeholder parser
│   └── test_parser_accuracy.py    # NEW - accuracy test runner
├── corpus/                        # (existing)
│   ├── schemas/
│   │   └── expected_output.py     # (existing - is_synthetic())
│   ├── exercise_equivalences.yaml # (existing - 34 exercises)
│   └── fitness/expected/parser/   # (existing - 93 JSON files)
├── test_generate_expected_outputs.py  # (existing)
└── corpus/test_expected_schemas.py    # (existing)
```

### Previous Story Learnings (Story 1.6)

From synthetic entry generation:
- `is_synthetic()` checks path for `/synthetic/` OR `date == "synthetic"`
- Use `ExpectedParserOutput.model_validate()` for JSON loading
- YAML files use `yaml.safe_load()` with UTF-8 encoding

### Exercise Equivalences Structure

34 exercises in `exercise_equivalences.yaml`:
```yaml
"Bench Press (Barbell)":
  - "Bench Press (Barbell)"  # canonical (first entry)
  - "바벨 벤치프레스"
  - "벤치프레스"
```

**ExerciseEquivalenceChecker implementation:**
```python
from pathlib import Path
import yaml

class ExerciseEquivalenceChecker:
    """Check exercise name equivalence using YAML mapping."""

    def __init__(self, yaml_path: Path) -> None:
        """Load exercise equivalences from YAML file."""
        with open(yaml_path, encoding="utf-8") as f:
            data: dict[str, list[str]] = yaml.safe_load(f)

        # Build reverse lookup: variant.lower() -> canonical
        self._to_canonical: dict[str, str] = {}
        for canonical, variants in data.items():
            for variant in variants:
                self._to_canonical[variant.lower()] = canonical

    def is_equivalent(self, actual: str, expected: str) -> bool:
        """Check if two exercise names are semantically equivalent."""
        actual_canonical = self._to_canonical.get(actual.lower())
        expected_canonical = self._to_canonical.get(expected.lower())
        if actual_canonical is None or expected_canonical is None:
            return False
        return actual_canonical == expected_canonical
```

### Mock LLM Fixture Design

**Option A - Reuse quilto fixtures (PREFERRED):**
```python
# tests/conftest.py
import sys
from pathlib import Path

# Add quilto tests to path for fixture import
quilto_tests = Path(__file__).parent.parent / "packages" / "quilto" / "tests"
sys.path.insert(0, str(quilto_tests))

from conftest import mock_llm, mock_llm_json, mock_llm_error  # noqa: E402

__all__ = ["mock_llm", "mock_llm_json", "mock_llm_error"]
```

**Option B - Create compatible fixtures (if import doesn't work):**
```python
from collections.abc import Callable, Generator
from typing import Any
from unittest.mock import AsyncMock, patch

import pytest

@pytest.fixture
def mock_llm() -> Generator[Callable[[dict[str, str]], None], None, None]:
    """Provide mocked litellm.acompletion that returns canned responses."""
    responses: dict[str, str] = {}
    call_history: list[dict[str, Any]] = []

    async def mock_completion(**kwargs: Any) -> Any:
        call_history.append(kwargs)
        model = kwargs.get("model", "")
        # Check exact match, then substring, then default
        for key, response in responses.items():
            if key == model or key in model:
                return type("Response", (), {"choices": [type("Choice", (), {"message": type("Msg", (), {"content": response})()})]})()
        if "_default" in responses:
            return type("Response", (), {"choices": [type("Choice", (), {"message": type("Msg", (), {"content": responses["_default"]})()})]})()
        return type("Response", (), {"choices": [type("Choice", (), {"message": type("Msg", (), {"content": "{}"})()})]})()

    def set_responses(new_responses: dict[str, str]) -> None:
        responses.clear()
        responses.update(new_responses)

    with patch("litellm.acompletion", AsyncMock(side_effect=mock_completion)) as mock:
        set_responses._mock = mock  # type: ignore[attr-defined]
        set_responses._call_history = call_history  # type: ignore[attr-defined]
        yield set_responses
```

### Storage Fixture Design (Stub)

```python
from datetime import datetime

@pytest.fixture
def storage_fixture(tmp_path: Path) -> Path:
    """Provide isolated storage directory with proper directory structure.

    Creates logs/(raw|parsed)/{YYYY}/{MM}/ structure per AR2 architecture decision.
    """
    now = datetime.now()
    year, month = now.strftime("%Y"), now.strftime("%m")

    for subdir in ["raw", "parsed"]:
        (tmp_path / "logs" / subdir / year / month).mkdir(parents=True)

    return tmp_path
```

**Note:** This is a stub. Real `StorageRepository` comes in Story 2.1.

### Domain Fixture Design

```python
from swealog.domains.general_fitness import general_fitness
from quilto import DomainModule

@pytest.fixture
def domain_fixture() -> DomainModule:
    """Provide GeneralFitness domain module for tests."""
    return general_fitness


@pytest.fixture
def use_real_ollama(request: pytest.FixtureRequest) -> bool:
    """Return True if --use-real-ollama flag was passed."""
    return request.config.getoption("--use-real-ollama", default=False)


def pytest_addoption(parser: pytest.Parser) -> None:
    """Add custom pytest CLI options."""
    parser.addoption(
        "--use-real-ollama",
        action="store_true",
        default=False,
        help="Run integration tests with real Ollama instead of mocks",
    )
```

### Accuracy Report Format

```
=== Parser Accuracy Report ===
Total entries: 93 (from_csv only, synthetic excluded)
Entry-level accuracy: 0.0% (0/93 fully correct)

Field-level accuracy:
  exercise_name: 0.0% (0/93)
  sets: 0.0% (0/93)
  weight: 0.0% (0/93)
  reps: 0.0% (0/93)

Note: Parser not implemented - accuracy tests will pass once Story 2.3 is complete.
```

### Dependencies & Sequencing

| Dependency | Source | Status |
|------------|--------|--------|
| `ExpectedParserOutput` schema | Story 1.5 | Done |
| `is_synthetic()` function | Story 1.6 | Done |
| `LLMClient` class | Story 1.3 | Done |
| `GeneralFitness` domain | Story 1.4 | Done |
| Parser agent | Story 2.3 | Future - tests will skip |
| StorageRepository | Story 2.1 | Future - use stub |

### Critical Implementation Notes

1. **Accuracy tests are infrastructure** - They scaffold the test harness; real accuracy testing happens after Parser (Story 2.3)
2. **Use `is_synthetic()` for filtering** - Primary accuracy uses only `from_csv/` entries
3. **Exercise equivalence is semantic** - "벤치프레스" == "Bench Press (Barbell)" if in same equivalence group
4. **Stub storage is acceptable** - Real StorageRepository comes in Story 2.1
5. **Mock LLM is for isolation** - Use `--use-real-ollama` for integration testing

### Anti-Patterns to Avoid

- DO NOT include synthetic entries in accuracy metrics (use `is_synthetic()` filter)
- DO NOT use LLM to generate expected outputs (circular validation)
- DO NOT hard-code exercise mappings in code (use YAML file)
- DO NOT skip type hints or docstrings
- DO NOT create real LLM calls in unit tests (use mock, reserve `--use-real-ollama` for integration)
- DO NOT duplicate `ExpectedParserOutput` schema (import from `tests.corpus.schemas`)
- DO NOT recreate mock_llm from scratch if quilto fixture can be imported
- DO NOT use `json.load()` for Pydantic models (use `model_validate_json()`)

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 1.7]
- [Source: _bmad-output/planning-artifacts/architecture.md#Testing Strategy]
- [Source: tests/corpus/README.md - Corpus structure and is_synthetic() usage]
- [Source: tests/corpus/schemas/expected_output.py - Schema and is_synthetic() function]
- [Source: tests/corpus/exercise_equivalences.yaml - 34 exercise mappings]
- [Source: packages/quilto/quilto/llm/client.py - LLMClient interface]
- [Source: packages/quilto/tests/conftest.py - EXISTING mock_llm fixtures to reuse]
- [Source: packages/swealog/swealog/domains/general_fitness.py - general_fitness singleton]
- [Source: Story 1.6 Dev Notes - is_synthetic() implementation details]

### Key File Paths

| Component | Path |
|-----------|------|
| Existing quilto conftest | `packages/quilto/tests/conftest.py` |
| LLMClient | `packages/quilto/quilto/llm/client.py` |
| LLMConfig types | `packages/quilto/quilto/llm/config.py` |
| DomainModule | `packages/quilto/quilto/domain.py` |
| GeneralFitness | `packages/swealog/swealog/domains/general_fitness.py` |
| Expected schemas | `tests/corpus/schemas/expected_output.py` |
| Exercise equivalences | `tests/corpus/exercise_equivalences.yaml` |
| pyproject.toml | `pyproject.toml` (root) |

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

N/A

### Completion Notes List

- Created `tests/conftest.py` with `mock_llm`, `storage_fixture`, `domain_fixture`, `use_real_ollama`, and `skip_without_real_ollama` fixtures
- Created compatible `mock_llm` fixture (Option B) since quilto fixtures use import mode that conflicts when running all test paths together
- Created `tests/accuracy/comparators.py` with `ExerciseEquivalenceChecker` class for semantic exercise name comparison using the 34 exercise equivalences from YAML
- Added `compare_weight`, `compare_reps`, `compare_sets` functions for exact numeric comparison
- Created `tests/accuracy/test_parser_accuracy.py` with `AccuracyRunner`, `AccuracyMetrics`, `FieldAccuracy` classes
- Accuracy runner loads 93 from_csv expected outputs (excludes 50 synthetic entries)
- Created `tests/accuracy/mock_parser.py` with placeholder `parse_entry` function
- Marked `TestParserAccuracy` class with `@pytest.mark.skip` and `@pytest.mark.accuracy` until Parser is implemented in Story 2.3
- Added `accuracy` and `integration` markers to `pyproject.toml`
- All tests pass: 66 passed, 3 skipped in root tests; 78 passed in quilto; 19 passed in swealog
- Linting (ruff) and type checking (pyright) pass with 0 errors

### File List

**New files:**
- `tests/conftest.py` - Core pytest fixtures for Swealog tests
- `tests/fixtures/__init__.py` - Fixtures package initialization
- `tests/fixtures/llm_responses/parser_response.json` - Example canned LLM response
- `tests/accuracy/__init__.py` - Accuracy module initialization
- `tests/accuracy/comparators.py` - Exercise equivalence checker and numeric comparators
- `tests/accuracy/mock_parser.py` - Placeholder parser for accuracy testing
- `tests/accuracy/test_parser_accuracy.py` - Accuracy runner and tests
- `tests/accuracy/test_comparators.py` - Unit tests for comparators
- `tests/test_conftest_fixtures.py` - Tests for conftest fixtures

**Modified files:**
- `pyproject.toml` - Added accuracy and integration pytest markers

### Code Review (Senior Developer Review - AI)

**Reviewer:** Claude Opus 4.5
**Date:** 2026-01-08
**Outcome:** Approved with fixes applied

**Issues Found and Fixed:**
1. **[HIGH]** `tests/test_conftest_fixtures.py` - Added missing type annotations for fixture parameters (mock_llm, storage_fixture, domain_fixture, use_real_ollama, tmp_path). Pyright now passes with 0 errors.
2. **[MEDIUM]** `tests/fixtures/__init__.py` - Created missing package initialization file.

**Verification:**
- `uv run pytest tests/ -v`: 66 passed, 3 skipped
- `uv run ruff check tests/`: All checks passed
- `uv run pyright tests/test_conftest_fixtures.py`: 0 errors
