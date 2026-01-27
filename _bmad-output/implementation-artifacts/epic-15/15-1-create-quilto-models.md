# Story 15.1: Create Quilto Public API Models

Status: backlog

## Story

As a **Quilto framework developer**,
I want **well-defined Pydantic models for the public API**,
So that **applications have a clear, type-safe contract for interacting with Quilto**.

## Background

**Origin:** Quilto Public API Design Session (2026-01-27)
**Source:** `_bmad-output/planning-artifacts/quilto-api-design-session.md`
**Priority:** High | **Effort:** Small (1-2 hours)
**Type:** New code - foundation for public API

The current Swealog implementation returns `dict[str, Any]` from the query pipeline. The new public API requires proper Pydantic models for type safety and clear contracts.

## Acceptance Criteria

1. **Given** a LOG input processed by Quilto
   **When** the result is returned
   **Then** `ProcessResult.parsed_data` contains the structured data

2. **Given** a QUERY input processed by Quilto
   **When** the result is returned
   **Then** `ProcessResult.response`, `confidence`, and `source_entry_ids` are populated

3. **Given** a query requiring clarification
   **When** the agent needs more information
   **Then** `ProcessResult.clarification_questions` contains `ClarificationQuestion` objects with optional options

4. **Given** debug mode enabled
   **When** processing completes
   **Then** `ProcessResult.debug` contains `ProcessDebug` with agent traces

## Tasks / Subtasks

- [ ] Task 1: Create `quilto/models.py` with core models
  - [ ] 1.1: Create `ClarificationQuestion` model (question: str, options: list[str] | None)
  - [ ] 1.2: Create `ProcessDebug` model (traces: list[AgentTrace], retries: int)
  - [ ] 1.3: Create `AgentTrace` model (agent: str, input_summary: str, output: dict, elapsed: float)
  - [ ] 1.4: Create `ProcessResult` model with all fields per design doc

- [ ] Task 2: Create `quilto/handlers.py` with progress protocol
  - [ ] 2.1: Create `ProgressHandler` Protocol with async methods
  - [ ] 2.2: Methods: on_agent_start, on_agent_complete, on_retry, on_stage

- [ ] Task 3: Write unit tests
  - [ ] 3.1: Test ProcessResult serialization/deserialization
  - [ ] 3.2: Test ClarificationQuestion with and without options
  - [ ] 3.3: Test ProcessDebug structure

- [ ] Task 4: Export from `quilto/__init__.py`
  - [ ] 4.1: Add exports for ProcessResult, ClarificationQuestion, ProcessDebug, ProgressHandler
  - [ ] 4.2: Verify `from quilto import ProcessResult` works

- [ ] Task 5: Run validation
  - [ ] 5.1: Run `make check` (lint + typecheck)
  - [ ] 5.2: Run `make validate` (full validation)

## Dev Notes

### ProcessResult Model

```python
class ProcessResult(BaseModel):
    # Core response (for QUERY)
    response: str | None = None
    confidence: float | None = None
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

### ProgressHandler Protocol

```python
class ProgressHandler(Protocol):
    async def on_agent_start(self, agent: str, input_summary: str) -> None: ...
    async def on_agent_complete(self, agent: str, elapsed: float) -> None: ...
    async def on_retry(self, attempt: int, reason: str) -> None: ...
    async def on_stage(self, stage: str) -> None: ...
```

### File Locations

| File | Purpose |
|------|---------|
| `packages/quilto/quilto/models.py` | NEW - ProcessResult, ClarificationQuestion, ProcessDebug, AgentTrace |
| `packages/quilto/quilto/handlers.py` | NEW - ProgressHandler protocol |
| `packages/quilto/quilto/__init__.py` | UPDATE - add exports |
| `packages/quilto/tests/test_models.py` | NEW - unit tests |

## Test Strategy

Unit tests only - no LLM calls needed. Test Pydantic model validation and serialization.
