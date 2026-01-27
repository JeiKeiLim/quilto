# Story 16.5: Implement Feedback Recording via Callback

Status: done

## Story

As a **Swealog developer**,
I want **feedback recording to capture full agent outputs via ProgressHandler callbacks**,
so that **dogfooding analysis has complete intermediate data for debugging and quality improvements**.

## Background

**Origin:** Epic 15 Retrospective (2026-01-27)
**Priority:** MEDIUM | **Effort:** Small (1-2 hours)
**Depends On:** Story 16.1 (completed) - ProgressHandler now receives `output: dict[str, Any]`

**Problem Statement:**
The current feedback recording system (`_record_simplified_feedback` in `app.py`) only captures trace summaries from `ProcessResult.debug.traces`. These traces contain abbreviated `output_summary` strings, not full agent outputs. For thorough dogfooding analysis, we need the complete intermediate outputs (router decisions, planner strategies, retriever results, analyzer verdicts, etc.).

**Solution:**
Implement a `FeedbackProgressHandler` class that captures full agent outputs from `on_agent_complete` callbacks, then merge this data into feedback records.

## Acceptance Criteria

1. **Given** a ProgressHandler that captures outputs
   **When** query completes
   **Then** all agent outputs are available for feedback recording

2. **Given** `--debug` flag used
   **When** feedback is recorded
   **Then** full intermediate outputs are stored (not just trace summaries)

3. **Given** the new callback signature (from Story 16.1)
   **When** feedback recorder implements ProgressHandler
   **Then** it receives output dict from each agent

4. **Given** a QUERY flow completes
   **When** feedback is recorded
   **Then** `intermediate_outputs` contains router, planner, retriever, analyzer, synthesizer, evaluator outputs

5. **Given** a LOG flow completes
   **When** feedback is recorded
   **Then** `intermediate_outputs` contains router and parser outputs (planner/retriever/etc. are empty dicts)

6. **Given** a BOTH flow completes
   **When** feedback is recorded
   **Then** `intermediate_outputs` contains all query flow outputs plus parser output

7. **Given** an agent error occurs
   **When** feedback is recorded
   **Then** that agent's output is an empty dict `{}`

8. **Given** observer agent runs
   **When** feedback is recorded
   **Then** observer output is also captured (optional field, may be useful for debugging context updates)

## Tasks / Subtasks

- [x] Task 1: Create `FeedbackProgressHandler` class in `feedback.py` (AC: 1, 3)
  - [x] 1.1: Implement `ProgressHandler` Protocol with all 4 methods
  - [x] 1.2: Store outputs in dict keyed by agent name
  - [x] 1.3: Add `get_outputs()` method to retrieve captured data
  - [x] 1.4: Add `get_intermediate_outputs()` to convert captured data to `IntermediateOutputs`

- [x] Task 2: Update `IntermediateOutputs` model for optional fields (AC: 4, 5, 6, 7)
  - [x] 2.1: Change all fields to have `default_factory=dict` (not required)
  - [x] 2.2: Add `observer: dict[str, Any] = Field(default_factory=dict)` field
  - [x] 2.3: Add `parser: dict[str, Any] = Field(default_factory=dict)` field
  - [x] 2.4: Add `correction: dict[str, Any] = Field(default_factory=dict)` field

- [x] Task 3: Integrate handler into CLI flow in `app.py` (AC: 1, 2, 3)
  - [x] 3.1: Add `progress_handler` parameter to `_create_quilto()`
  - [x] 3.2: Pass handler to `Quilto` constructor
  - [x] 3.3: Create `FeedbackProgressHandler` in `run_command()` when debug=True
  - [x] 3.4: Replace `_record_simplified_feedback` with handler-based recording

- [x] Task 4: Write tests for `FeedbackProgressHandler` (AC: all)
  - [x] 4.1: Test output capture for each agent type (router, planner, etc.)
  - [x] 4.2: Test `get_intermediate_outputs()` returns correct model
  - [x] 4.3: Test empty dict on error case (agent not called)
  - [x] 4.4: Test integration with `FeedbackRecorder.record()`

- [x] Task 5: Run validation
  - [x] 5.1: `make check` passes (lint + typecheck)
  - [x] 5.2: `make validate` passes (lint + format + typecheck + test)

## Dev Notes

### Agent Names Reference

Agent names used in callbacks (from `orchestration.py`):
- `"router"` → RouterOutput
- `"planner"` → PlannerOutput
- `"retriever"` → RetrieverOutput
- `"analyzer"` → AnalyzerOutput
- `"synthesizer"` → SynthesizerOutput
- `"evaluator"` → EvaluatorOutput
- `"parser"` → ParserOutput
- `"observer"` → ObserverOutput
- `"correction"` → CorrectionResult

### FeedbackProgressHandler Implementation

```python
# packages/swealog/swealog/cli/feedback.py

from typing import Any
from quilto.handlers import ProgressHandler  # For type checking reference

class FeedbackProgressHandler:
    """ProgressHandler that captures agent outputs for feedback recording."""

    def __init__(self) -> None:
        self._outputs: dict[str, dict[str, Any]] = {}

    async def on_agent_start(self, agent: str, input_summary: str) -> None:
        """Track agent start (no-op for feedback recording)."""
        pass

    async def on_agent_complete(
        self, agent: str, elapsed: float, output: dict[str, Any]
    ) -> None:
        """Capture agent output."""
        self._outputs[agent] = output

    async def on_retry(self, attempt: int, reason: str) -> None:
        """Track retries (no-op for feedback recording)."""
        pass

    async def on_stage(self, stage: str) -> None:
        """Track stage transitions (no-op for feedback recording)."""
        pass

    def get_outputs(self) -> dict[str, dict[str, Any]]:
        """Get all captured outputs."""
        return self._outputs.copy()

    def get_intermediate_outputs(self) -> "IntermediateOutputs":
        """Convert captured outputs to IntermediateOutputs model."""
        return IntermediateOutputs(
            router=self._outputs.get("router", {}),
            planner=self._outputs.get("planner", {}),
            retriever=self._outputs.get("retriever", {}),
            analyzer=self._outputs.get("analyzer", {}),
            synthesizer=self._outputs.get("synthesizer", {}),
            evaluator=self._outputs.get("evaluator", {}),
            parser=self._outputs.get("parser", {}),
            observer=self._outputs.get("observer", {}),
            correction=self._outputs.get("correction", {}),
        )
```

### IntermediateOutputs Model Update

```python
class IntermediateOutputs(BaseModel):
    """Intermediate agent outputs from query pipeline.

    All fields default to empty dict - not all agents run in every flow.
    """
    model_config = ConfigDict(strict=True)

    router: dict[str, Any] = Field(default_factory=dict)
    planner: dict[str, Any] = Field(default_factory=dict)
    retriever: dict[str, Any] = Field(default_factory=dict)
    analyzer: dict[str, Any] = Field(default_factory=dict)
    synthesizer: dict[str, Any] = Field(default_factory=dict)
    evaluator: dict[str, Any] = Field(default_factory=dict)
    parser: dict[str, Any] = Field(default_factory=dict)
    observer: dict[str, Any] = Field(default_factory=dict)
    correction: dict[str, Any] = Field(default_factory=dict)
```

### CLI Integration (app.py)

```python
# Update _create_quilto signature
def _create_quilto(
    llm_client: LLMClient,
    storage: StorageRepository,
    domains: list[DomainModule],
    debug: bool = False,
    session_db_path: str = ":memory:",
    progress_handler: ProgressHandler | None = None,  # ADD
) -> Quilto:
    return Quilto(
        llm_client=llm_client,
        storage=storage,
        domains=domains,
        observer_config=ObserverTriggerConfig(enable_post_query=True),
        session_db_path=session_db_path,
        progress_handler=progress_handler,  # ADD
        debug=debug,
    )

# In run_command():
progress_handler = FeedbackProgressHandler() if debug else None
quilto = _create_quilto(..., progress_handler=progress_handler)
# ... processing ...
if debug and progress_handler:
    _record_feedback_with_handler(progress_handler, ...)
```

### Test Pattern for IntermediateOutputs

Update existing tests: `IntermediateOutputs` fields are now optional with defaults. Change test assertions from "missing field raises error" to "missing fields get empty dict".

```python
def test_fields_default_to_empty_dict(self) -> None:
    """Test that all fields default to empty dict."""
    outputs = IntermediateOutputs()  # No args needed now
    assert outputs.router == {}
    assert outputs.parser == {}
    # etc.
```

### Files to Modify

| File | Action |
|------|--------|
| `packages/swealog/swealog/cli/feedback.py` | Add FeedbackProgressHandler, update IntermediateOutputs defaults |
| `packages/swealog/swealog/cli/app.py` | Add progress_handler to _create_quilto, integrate handler |
| `packages/swealog/tests/cli/test_feedback.py` | Update tests for optional fields, add FeedbackProgressHandler tests |

### Test Update Note

The existing test `test_missing_field_raises_error` in `TestIntermediateOutputs` will need to be removed or changed to `test_fields_default_to_empty_dict` since all fields now have defaults.

### Import Requirements

```python
# feedback.py - no need to import ProgressHandler for runtime
# The class duck-types the protocol without explicit inheritance

# app.py - already imports what's needed, just add:
from swealog.cli.feedback import FeedbackProgressHandler
```

### References

| Source | Purpose |
|--------|---------|
| `packages/quilto/quilto/handlers.py` | ProgressHandler Protocol definition |
| `packages/quilto/quilto/orchestration.py:190-222` | _call_progress_handler and signature caching |
| `packages/swealog/swealog/cli/feedback.py` | Current feedback infrastructure |
| `packages/swealog/swealog/cli/app.py:69-96, 278-375` | _create_quilto and run_command |
| `packages/quilto/quilto/quilto.py:65` | Quilto constructor progress_handler param |

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

N/A

### Completion Notes List

1. Created `FeedbackProgressHandler` class implementing all 4 ProgressHandler Protocol methods
2. Updated `IntermediateOutputs` model with all fields defaulting to empty dict and added parser, observer, correction fields
3. Added `_record_feedback_with_handler()` function for full output recording
4. Integrated handler into `run_command()` - creates handler when debug=True and passes to Quilto
5. Handler-based recording now uses `FeedbackRecord` with full `IntermediateOutputs` instead of `SimplifiedFeedbackRecord` with traces
6. Added comprehensive tests for FeedbackProgressHandler (13 new test methods)
7. Updated 3 existing CLI tests that expected `record_simplified` to now expect `record` method

### File List

| File | Action |
|------|--------|
| `packages/swealog/swealog/cli/feedback.py` | Modified - Added FeedbackProgressHandler class, updated IntermediateOutputs with default_factory and new fields |
| `packages/swealog/swealog/cli/app.py` | Modified - Added progress_handler param to _create_quilto(), added _record_feedback_with_handler(), integrated handler in run_command() |
| `packages/swealog/tests/cli/test_feedback.py` | Modified - Added TestFeedbackProgressHandler class with 13 tests, updated existing test fixtures |
| `packages/swealog/tests/test_cli_auto.py` | Modified - Updated 3 tests to expect record() instead of record_simplified()

## Senior Developer Review (AI)

**Reviewed by:** Amelia (Dev Agent) | **Date:** 2026-01-27

### Review Summary

Code review identified 5 actionable issues (2 HIGH, 3 MEDIUM). All fixes applied and verified.

### Issues Fixed

| ID | Severity | Issue | Resolution |
|----|----------|-------|------------|
| H1 | HIGH | Unused import `SimplifiedFeedbackRecord` | Removed from app.py imports |
| H2 | HIGH | `_record_simplified_feedback` dead code (58 lines) | Removed function and fallback branch |
| M2 | MEDIUM | Missing thread-safety note in `FeedbackProgressHandler` docstring | Added "Note: Not thread-safe" to docstring |
| M3 | MEDIUM | Test `test_query_flow_no_feedback_prompt_without_debug` checked wrong method | Fixed to check `record.assert_not_called()` |
| - | - | Removed unused `Any` import after H1/H2 fixes | Fixed lint error |

### Issues Not Applied

| ID | Severity | Issue | Reason |
|----|----------|-------|--------|
| M1 | MEDIUM | Type annotation should use Protocol | FALSE POSITIVE - `FeedbackProgressHandler` type is correct because we call `get_intermediate_outputs()` which is class-specific, not in Protocol |

### Additional Changes

- Removed `TestRecordSimplifiedFeedback` test class (2 tests) - tested deleted function

### Validation

- `make validate` passes (lint + format + typecheck + test)
- 2023 passed, 101 skipped

### Review Verdict

**APPROVED** - All acceptance criteria verified, code quality issues fixed.

