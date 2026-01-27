# Story 15.1: Create Quilto Public API Models

Status: done

## Story

As a **Quilto framework developer**,
I want **well-defined Pydantic models for the public API**,
So that **applications have a clear, type-safe contract for interacting with Quilto**.

## Background

**Origin:** Quilto Public API Design Session (2026-01-27)
**Source:** `_bmad-output/planning-artifacts/quilto-api-design-session.md`
**Priority:** High | **Effort:** Small (1-2 hours)
**Type:** New code - foundation for Epic 15 public API

This is the first story in Epic 15 which creates Quilto's single entry point. The models created here will be used by:
- `quilto/quilto.py` (Quilto class) - Story 15.3
- `quilto/session/` (Session management) - Story 15.2
- Application code (Swealog migration) - Story 15.4

The current Swealog implementation returns `dict[str, Any]` from the query pipeline (~400 lines of manual wiring). The new public API requires proper Pydantic models for type safety and clear contracts.

## Acceptance Criteria

1. **Given** a LOG input processed by Quilto
   **When** the result is returned
   **Then** `ProcessResult.parsed_data` contains the structured data and `input_type` is "log"

2. **Given** a QUERY input processed by Quilto
   **When** the result is returned
   **Then** `ProcessResult.response`, `confidence`, and `source_entry_ids` are populated

3. **Given** a query requiring clarification
   **When** the agent needs more information
   **Then** `ProcessResult.clarification_questions` contains `ClarificationQuestion` objects with optional options list

4. **Given** debug mode enabled
   **When** processing completes
   **Then** `ProcessResult.debug` contains `ProcessDebug` with agent execution traces

5. **Given** a ProgressHandler implementation
   **When** registered with Quilto
   **Then** async methods (`on_agent_start`, `on_agent_complete`, `on_retry`, `on_stage`) can be called during processing

## Tasks / Subtasks

- [x] Task 1: Create `packages/quilto/quilto/models.py` (AC: #1, #2, #3, #4)
  - [x] 1.1: Define `ClarificationQuestion` model with `question: str = Field(min_length=1)` and `options: list[str] | None`
  - [x] 1.2: Define `AgentTrace` model with `agent_name: str = Field(min_length=1)` and other fields
  - [x] 1.3: Define `ProcessDebug` model for aggregating agent traces (default `traces: list[AgentTrace] = []`)
  - [x] 1.4: Define `ProcessResult` model with all required fields
  - [x] 1.5: Add model validation (Field constraints, ConfigDict(strict=True))
  - [x] 1.6: Add comprehensive docstrings (Google style)

- [x] Task 2: Create `packages/quilto/quilto/handlers.py` (AC: #5)
  - [x] 2.1: Define `ProgressHandler` Protocol class with async methods
  - [x] 2.2: Add proper type hints for all method parameters
  - [x] 2.3: Add docstrings explaining each callback's purpose and timing

- [x] Task 3: Update `packages/quilto/quilto/__init__.py` (AC: all)
  - [x] 3.1: Export new classes: `ProcessResult`, `ClarificationQuestion`, `ProcessDebug`, `AgentTrace`, `ProgressHandler`
  - [x] 3.2: Add to `__all__` list
  - [x] 3.3: Verify imports: `from quilto import ProcessResult, ClarificationQuestion, ProcessDebug, AgentTrace, ProgressHandler`

- [x] Task 4: Write unit tests in `packages/quilto/tests/`
  - [x] 4.1: Create `packages/quilto/tests/test_models.py`
  - [x] 4.2: Test `ProcessResult` validation (valid LOG, valid QUERY, invalid confidence bounds)
  - [x] 4.3: Test `ClarificationQuestion` with options, without options, empty question rejection
  - [x] 4.4: Test `ProcessDebug` with empty traces list and with populated traces
  - [x] 4.5: Test `AgentTrace` field validation (empty agent_name rejection, negative elapsed_ms rejection)
  - [x] 4.6: Create `packages/quilto/tests/test_handlers.py`
  - [x] 4.7: Verify `ProgressHandler` Protocol can be implemented (create mock implementation)

- [x] Task 5: Run validation
  - [x] 5.1: `make check` passes (lint + typecheck)
  - [x] 5.2: `make validate` passes (lint + format + typecheck + test)

## Dev Notes

### Model Definitions from Design Session

From `_bmad-output/planning-artifacts/quilto-api-design-session.md`:

```python
# quilto/models.py

from pydantic import BaseModel, ConfigDict, Field
from typing import Any, Literal
from datetime import datetime


class ClarificationQuestion(BaseModel):
    """A question to ask the user for clarification.

    Attributes:
        question: The clarification question text.
        options: Optional predefined answer choices. None means free-form input.
    """
    model_config = ConfigDict(strict=True)

    question: str = Field(min_length=1)
    options: list[str] | None = None


class AgentTrace(BaseModel):
    """Trace of a single agent execution for debugging.

    Attributes:
        agent_name: Name of the agent (e.g., "router", "planner").
        input_summary: Summary of input provided to agent.
        output_summary: Summary of agent output.
        elapsed_ms: Execution time in milliseconds.
        timestamp: When the agent started execution.
    """
    model_config = ConfigDict(strict=True)

    agent_name: str = Field(min_length=1)
    input_summary: str
    output_summary: str
    elapsed_ms: float = Field(ge=0)
    timestamp: datetime


class ProcessDebug(BaseModel):
    """Debug information for a processing run.

    Attributes:
        traces: List of agent execution traces in order.
        total_elapsed_ms: Total processing time in milliseconds.
        retry_count: Number of retries attempted.
    """
    model_config = ConfigDict(strict=True)

    traces: list[AgentTrace] = []
    total_elapsed_ms: float = Field(ge=0)
    retry_count: int = Field(ge=0, default=0)


class ProcessResult(BaseModel):
    """Result of processing user input through Quilto.

    This is the primary return type for session.process().

    For QUERY inputs:
        - response, confidence, source_entry_ids are populated
    For LOG inputs:
        - parsed_data is populated
    For BOTH inputs:
        - Both response and parsed_data may be populated
    When clarification needed:
        - clarification_questions is populated

    Attributes:
        response: Generated response text (for QUERY).
        confidence: Confidence score 0.0-1.0 (for QUERY).
        source_entry_ids: IDs of entries used to generate response.
        parsed_data: Structured data extracted (for LOG).
        input_type: Classification of the input.
        selected_domains: Domains that were activated.
        clarification_questions: Questions needing user answers.
        debug: Debug traces if debug mode enabled.
    """
    model_config = ConfigDict(strict=True)

    # Core response (for QUERY)
    response: str | None = None
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    source_entry_ids: list[str] = []

    # For LOG inputs
    parsed_data: dict[str, Any] | None = None

    # Classification
    input_type: Literal["log", "query", "both", "correction"]
    selected_domains: list[str] = []

    # Clarification (if needed)
    clarification_questions: list[ClarificationQuestion] | None = None

    # Debug (if enabled)
    debug: ProcessDebug | None = None
```

```python
# quilto/handlers.py

from typing import Protocol


class ProgressHandler(Protocol):
    """Protocol for progress callbacks during Quilto processing.

    Implement methods you care about. All methods are optional due to
    Protocol semantics - just implement what you need.

    Example:
        class MyUIHandler:
            async def on_agent_start(self, agent: str, input_summary: str) -> None:
                print(f"Starting {agent}...")

            async def on_agent_complete(self, agent: str, elapsed: float) -> None:
                print(f"{agent} done in {elapsed:.2f}s")
    """

    async def on_agent_start(self, agent: str, input_summary: str) -> None:
        """Called when an agent begins execution.

        Args:
            agent: Name of the agent starting (e.g., "router", "planner").
            input_summary: Brief summary of input being processed.
        """
        ...

    async def on_agent_complete(self, agent: str, elapsed: float) -> None:
        """Called when an agent completes execution.

        Args:
            agent: Name of the agent that completed.
            elapsed: Execution time in seconds.
        """
        ...

    async def on_retry(self, attempt: int, reason: str) -> None:
        """Called when a retry is attempted.

        Args:
            attempt: Current retry attempt number (1-based).
            reason: Why the retry is happening.
        """
        ...

    async def on_stage(self, stage: str) -> None:
        """Called when processing enters a new stage.

        Args:
            stage: Name of the stage (e.g., "routing", "planning", "retrieving").
        """
        ...
```

### Existing Patterns in Quilto Codebase

Based on exploration of `packages/quilto/quilto/`:

1. **Model configuration**: All models use `ConfigDict(strict=True)`
2. **Field validation**: Use `Field(ge=0.0, le=1.0)` for ranges, `Field(min_length=1)` for strings
3. **Type hints**: Modern syntax `list[str] | None` throughout
4. **Docstrings**: Google-style docstrings on all classes and methods
5. **Module exports**: Public classes listed in `__all__` in `__init__.py`

### Two Different ClarificationQuestion Models (DO NOT MODIFY EXISTING)

**CRITICAL**: There's an existing `ClarificationQuestion` in `quilto/agents/models.py` - **DO NOT modify it**.

| Model | Location | Purpose | Key Fields |
|-------|----------|---------|------------|
| **Internal** | `quilto/agents/models.py` | Agent logic | `question`, `priority`, `gap_addressed`, `required` |
| **Public API** | `quilto/models.py` (NEW) | UI rendering | `question`, `options` |

The public API version is simpler - just question + optional answer choices. Synthesizer will convert internal → public format when creating ProcessResult. Story 15.3 handles this conversion.

### Circular Import Considerations

The new `quilto/models.py` should NOT import from `quilto/agents/models.py` to avoid circular imports. If types need to be shared, use forward references or keep them separate.

### File Locations (All Paths Absolute from Project Root)

| File | Action | Purpose |
|------|--------|---------|
| `packages/quilto/quilto/models.py` | CREATE | ProcessResult, ClarificationQuestion, ProcessDebug, AgentTrace |
| `packages/quilto/quilto/handlers.py` | CREATE | ProgressHandler protocol |
| `packages/quilto/quilto/__init__.py` | UPDATE | Add imports and `__all__` entries |
| `packages/quilto/tests/test_models.py` | CREATE | Unit tests for new models |
| `packages/quilto/tests/test_handlers.py` | CREATE | Protocol implementation tests |

### Expected `__init__.py` Changes

Add to `packages/quilto/quilto/__init__.py`:
```python
# Near top, with other imports
from quilto.models import (
    AgentTrace,
    ClarificationQuestion,
    ProcessDebug,
    ProcessResult,
)
from quilto.handlers import ProgressHandler

# Add to existing __all__ list
__all__ = [
    # ... existing items ...
    "AgentTrace",
    "ClarificationQuestion",
    "ProcessDebug",
    "ProcessResult",
    "ProgressHandler",
]
```

Verify with: `from quilto import ProcessResult, ClarificationQuestion, ProcessDebug, AgentTrace, ProgressHandler`

### Recent Git Context

Last 5 commits:
- c4f2ae7 Update epics.md with Epic 15 and mark Epic 14 as skipped
- 539c88e Add Epic 15: Quilto Public API design and implementation stories
- 1dfa85e Update critical issue doc: Framework decision made, focus on API design
- 048166a Add Epic 13 retrospective and critical orchestration design issue
- 3d65641 Reconcile Epic 14 with human review findings from Iteration 3

This story is the first implementation work for Epic 15. No code changes yet.

### Validation Checklist (Run Before Marking Done)

**Code Quality:**
- [ ] All models have `ConfigDict(strict=True)`
- [ ] All required string fields use `Field(min_length=1)`: `question`, `agent_name`
- [ ] Range validation uses `Field(ge=, le=)`: `confidence` (0.0-1.0), `elapsed_ms` (ge=0), `retry_count` (ge=0)
- [ ] Modern type hints: `list[str]` not `List[str]`, `X | None` not `Optional[X]`
- [ ] Google-style docstrings on all classes and public methods

**Exports:**
- [ ] All 5 classes exported in `__init__.py`: `ProcessResult`, `ClarificationQuestion`, `ProcessDebug`, `AgentTrace`, `ProgressHandler`
- [ ] All 5 classes added to `__all__` list
- [ ] Import verification: `from quilto import ProcessResult, ClarificationQuestion, ProcessDebug, AgentTrace, ProgressHandler`

**Tests:**
- [ ] `ProcessResult` valid LOG case (parsed_data populated, input_type="log")
- [ ] `ProcessResult` valid QUERY case (response + confidence populated, input_type="query")
- [ ] `ProcessResult` invalid confidence bounds (< 0, > 1 rejected)
- [ ] `ClarificationQuestion` with options list
- [ ] `ClarificationQuestion` with None options
- [ ] `ClarificationQuestion` empty question rejected
- [ ] `ProcessDebug` with empty traces list (default)
- [ ] `ProcessDebug` with populated traces
- [ ] `AgentTrace` empty agent_name rejected
- [ ] `AgentTrace` negative elapsed_ms rejected
- [ ] `ProgressHandler` Protocol mock implementation works

**Final Validation:**
- [ ] `make check` passes (lint + typecheck)
- [ ] `make validate` passes (lint + format + typecheck + test)

### References

| Source | Content |
|--------|---------|
| `_bmad-output/planning-artifacts/quilto-api-design-session.md` | Full API design session with all model definitions |
| `_bmad-output/planning-artifacts/architecture.md#Quilto Public API` | Architecture decision documentation |
| `packages/quilto/quilto/agents/models.py` | Existing model patterns (1054 lines) |
| `packages/quilto/quilto/__init__.py` | Current export patterns (82 lines) |
| `_bmad-output/project-context.md` | Validation rules and common mistakes to avoid |

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

N/A

### Completion Notes List

- Created `quilto/models.py` with 4 Pydantic models: `ClarificationQuestion`, `AgentTrace`, `ProcessDebug`, `ProcessResult`
- Created `quilto/handlers.py` with `@runtime_checkable` `ProgressHandler` Protocol (required for `isinstance()` checks)
- All models use `ConfigDict(strict=True)` per codebase patterns
- All Field constraints implemented: `min_length=1` for strings, `ge=0`/`le=1.0` for ranges
- Modern type hints used throughout (`list[str] | None`, not `Optional[List[str]]`)
- Google-style docstrings on all classes and methods
- 27 unit tests in `test_models.py`, 2 async tests in `test_handlers.py`
- All 5 classes exported in `quilto/__init__.py` and added to `__all__`
- `make validate` passes: 1952 passed, 101 skipped

### Senior Developer Review (AI)

**Reviewed by:** Amelia (Dev Agent) | **Date:** 2026-01-27

**Issues Found & Fixed:**

| ID | Severity | Issue | Fix Applied |
|----|----------|-------|-------------|
| H1 | HIGH | `ProcessDebug.total_elapsed_ms` required but had no default | Added `default=0` |
| H2 | HIGH | Test didn't verify `isinstance()` behavior for partial Protocol impl | Fixed test to assert `not isinstance()` |
| M1 | MEDIUM | `AgentTrace.input_summary`/`output_summary` missing `min_length=1` | Added `Field(min_length=1)` |
| M2 | MEDIUM | Mutable default lists not using `Field(default_factory=...)` | Changed to typed lambda factories |
| M3 | MEDIUM | Missing test for mutable default isolation | Added `test_default_lists_are_isolated` |

**New Tests Added:**
- `test_default_instantiation` - ProcessDebug can be created with all defaults
- `test_empty_input_summary_rejected` - AgentTrace validates input_summary
- `test_empty_output_summary_rejected` - AgentTrace validates output_summary
- `test_default_lists_are_isolated` - ProcessResult list isolation verified

**Validation:** `make validate` passes - 1952 passed, 101 skipped

### File List

| File | Action |
|------|--------|
| `packages/quilto/quilto/models.py` | CREATE |
| `packages/quilto/quilto/handlers.py` | CREATE |
| `packages/quilto/quilto/__init__.py` | UPDATE |
| `packages/quilto/tests/test_models.py` | CREATE |
| `packages/quilto/tests/test_handlers.py` | CREATE |
