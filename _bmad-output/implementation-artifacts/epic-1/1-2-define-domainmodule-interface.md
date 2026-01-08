# Story 1.2: Define DomainModule Interface

Status: done

## Story

As a **Quilto developer**,
I want a **clear DomainModule interface with Pydantic validation**,
So that **application developers can define domain-specific configuration**.

## Acceptance Criteria

1. **Given** I create a class inheriting from `DomainModule`
   **When** I define `description`, `log_schema`, `vocabulary`, and `expertise`
   **Then** Pydantic validates all fields correctly
   **And** optional fields (`response_evaluation_rules`, `context_management_guidance`) have sensible defaults
   **And** `name` defaults to class name if not provided

## Tasks / Subtasks

- [x] Task 1: Create DomainModule base class in quilto (AC: #1)
  - [x] 1.1 Create `packages/quilto/quilto/domain.py` module
  - [x] 1.2 Define `DomainModule` as a Pydantic `BaseModel` with required fields:
    - `name: str` (optional, defaults to class name via validator)
    - `description: str` (required - used by Router for domain selection)
    - `log_schema: type[BaseModel]` (required - Pydantic model for parsed entries)
    - `vocabulary: dict[str, str]` (required - term normalization mapping)
    - `expertise: str` (optional, defaults to empty string - domain knowledge for agents)
  - [x] 1.3 Add optional fields with sensible defaults:
    - `response_evaluation_rules: list[str] = []` (rules for Evaluator agent)
    - `context_management_guidance: str = ""` (guidance for Observer agent)
  - [x] 1.4 Implement `model_validator` to default `name` to class name if not provided

- [x] Task 2: Export DomainModule from quilto package (AC: #1)
  - [x] 2.1 Update `packages/quilto/quilto/__init__.py` to export `DomainModule`
  - [x] 2.2 Ensure `from quilto import DomainModule` works

- [x] Task 3: Write unit tests for DomainModule (AC: #1)
  - [x] 3.1 Create `packages/quilto/tests/test_domain.py`
  - [x] 3.2 Test: DomainModule requires `description`, `log_schema`, `vocabulary`
  - [x] 3.3 Test: `name` defaults to class name when not provided
  - [x] 3.4 Test: Optional fields have correct defaults (empty list, empty string)
  - [x] 3.5 Test: Pydantic validation rejects invalid `log_schema` (must be BaseModel subclass)
  - [x] 3.6 Test: Vocabulary dict is properly validated

- [x] Task 4: Validate integration (AC: #1)
  - [x] 4.1 Run `uv run ruff check packages/quilto/`
  - [x] 4.2 Run `uv run pyright packages/quilto/`
  - [x] 4.3 Run `uv run pytest packages/quilto/tests/test_domain.py -v`

## Dev Notes

### Architecture Compliance

This story implements the `DomainModule` interface defined in:
- `_bmad-output/planning-artifacts/agent-system-design.md` (Section 8.2)
- Functional requirement FR-F6: Support pluggable domain expertise modules

### DomainModule Interface Specification

From agent-system-design.md Section 8.2:

```python
from pydantic import BaseModel, model_validator
from typing import Self

class DomainModule(BaseModel):
    """Domain configuration provided to the framework.

    Applications register one or more domain modules to customize
    how the framework parses, analyzes, and evaluates domain-specific content.
    """

    # Required fields
    name: str = ""
    """Domain identifier. Defaults to class name if not provided."""

    description: str
    """Used by Router to auto-select relevant domain(s) for a given input.
    Write a clear description of what this domain covers so agents can match it.
    """

    log_schema: type[BaseModel]
    """Pydantic model defining structured output for parsed entries."""

    vocabulary: dict[str, str]
    """Term normalization mapping. E.g., {"bench": "bench press"}"""

    expertise: str = ""
    """Domain knowledge injected into agent prompts (Analyzer, Planner).
    Can include retrieval guidance, pattern recognition hints, domain principles."""

    response_evaluation_rules: list[str] = []
    """Rules for evaluating Synthesizer's response before returning to user.
    E.g., "Never recommend exercises for injured body parts" """

    context_management_guidance: str = ""
    """Instructions for Observer agent on what patterns to track over time.
    E.g., "Track personal records, workout frequency, recovery patterns" """

    @model_validator(mode='after')
    def set_default_name(self) -> Self:
        if not self.name:
            self.name = self.__class__.__name__
        return self
```

### Field Usage by Agents

| Field | Used By | Purpose |
|-------|---------|---------|
| `name` | Framework | Identifier, defaults to class name |
| `description` | Router | Auto-select relevant domains based on input matching |
| `log_schema` | Parser | Structure for parsed entries (Pydantic model) |
| `vocabulary` | Parser, Retriever | Term normalization, keyword expansion |
| `expertise` | Analyzer, Planner | Domain knowledge injected into prompts |
| `response_evaluation_rules` | Evaluator | Domain-specific quality checks |
| `context_management_guidance` | Observer | Long-term pattern tracking guidance |

### Implementation Notes

1. **Pydantic v2 Syntax**: Use `model_validator(mode='after')` not the deprecated `@validator`
2. **Type Annotation for log_schema**: Use `type[BaseModel]` to indicate it expects a class, not an instance
3. **Self Type**: Import `Self` from `typing` (Python 3.11+) for validator return type
4. **Model Config**: Consider adding `model_config = ConfigDict(arbitrary_types_allowed=True)` if needed for `type[BaseModel]`

### Example Usage (for reference, not implementation)

```python
from pydantic import BaseModel
from quilto import DomainModule

class StrengthLogEntry(BaseModel):
    exercise: str
    weight: float | None = None
    reps: int | None = None
    sets: int | None = None
    notes: str = ""

class StrengthDomain(DomainModule):
    name: str = "strength"
    description: str = "Strength training and weightlifting workouts"
    log_schema: type[BaseModel] = StrengthLogEntry
    vocabulary: dict[str, str] = {
        "bench": "bench press",
        "squat": "barbell squat",
        "dl": "deadlift",
        "ohp": "overhead press",
    }
    expertise: str = """
    Progressive overload is key for strength gains.
    Look for patterns in volume, intensity, and recovery.
    """
```

### Project Structure After This Story

```
packages/quilto/
├── pyproject.toml
├── quilto/
│   ├── __init__.py      # Exports: __version__, DomainModule
│   ├── py.typed
│   └── domain.py        # NEW: DomainModule class
└── tests/
    ├── __init__.py
    └── test_domain.py   # NEW: Unit tests for DomainModule
```

### Testing Strategy

1. **Unit Tests** (this story): Validate Pydantic model behavior
   - Required field validation
   - Default value behavior
   - Type validation for `log_schema`

2. **Integration Tests** (Story 1.4): Validate with GeneralFitness domain
   - Actual domain instantiation
   - Field population verification

### Previous Story Context (1.1)

From Story 1-1 completion notes:
- Workspace is set up with quilto and swealog packages
- `uv sync` installs all dependencies including pydantic>=2.10.0
- Ruff and pyright are configured and passing
- Empty `quilto/__init__.py` exists with just `__version__`

### Technical Constraints

1. **Python 3.13+**: Use modern type hints (`list[str]` not `List[str]`)
2. **Pydantic 2.10+**: Use v2 API (`model_validator`, `ConfigDict`)
3. **Google Docstrings**: Required for all public classes and methods
4. **Strict Pyright**: Must pass with 0 errors

### References

- [Source: _bmad-output/planning-artifacts/agent-system-design.md#8.2 DomainModule Interface]
- [Source: _bmad-output/planning-artifacts/agent-system-design.md#Section 8 Field Usage Table]
- [Source: _bmad-output/planning-artifacts/epics.md#Story 1.2]
- [Source: _bmad-output/planning-artifacts/architecture.md#Technical Stack]
- [Source: Pydantic v2 docs - https://docs.pydantic.dev/latest/concepts/validators/]

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

### Completion Notes List

- Story created via YOLO mode create-story workflow
- This is story 2 of 7 in Epic 1 (Foundation & First Domain)
- Previous story 1-1 established monorepo structure with quilto package
- DomainModule is the foundational interface that all domain modules will inherit from
- Story 1.4 (GeneralFitness) depends on this story's completion
- Implementation complete: DomainModule base class with Pydantic validation
- Added `field_validator` for log_schema to reject non-BaseModel classes and instances
- Added `ConfigDict(arbitrary_types_allowed=True)` for `type[BaseModel]` field
- 19 unit tests covering all acceptance criteria
- All validations passing: ruff, pyright (0 errors), pytest (19/19)
- Code review fixes (2025-01-08): Added 4 tests for vocabulary validation (M1-M4)
  - test_vocabulary_rejects_non_dict_type
  - test_vocabulary_rejects_list_type
  - test_vocabulary_rejects_non_string_keys
  - test_vocabulary_rejects_non_string_values

### File List

Files created:
- `packages/quilto/quilto/domain.py`
- `packages/quilto/tests/test_domain.py`

Files modified:
- `packages/quilto/quilto/__init__.py`
