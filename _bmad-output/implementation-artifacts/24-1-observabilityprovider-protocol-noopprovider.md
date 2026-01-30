# Story 24.1: ObservabilityProvider Protocol + NoOpProvider

Status: done

## Story

As a **Quilto developer**,
I want **a clean observability interface**,
so that **I can swap providers without changing application code**.

## Acceptance Criteria

1. **Given** new directory `quilto/observability/`
   **When** created
   **Then** contains `__init__.py`, `provider.py`, `noop.py`

2. **Given** `ObservabilityProvider` protocol
   **When** defined
   **Then** includes: `get_langgraph_callback()`, `span()`, `log_event()`, `log_error()`, `is_enabled()`, `flush()`

3. **Given** `NoOpProvider` implementation
   **When** observability is disabled
   **Then** all methods are safe no-ops (span returns null context manager)

4. **Given** `SpanContext` dataclass
   **When** created
   **Then** contains `span_id` and `trace_id` fields

## Tasks / Subtasks

- [x] Task 1: Create observability module structure (AC: #1)
  - [x] Create `packages/quilto/quilto/observability/` directory
  - [x] Create `__init__.py` with public exports

- [x] Task 2: Define ObservabilityProvider protocol (AC: #2, #4)
  - [x] Create `packages/quilto/quilto/observability/provider.py`
  - [x] Define `SpanContext` dataclass with `span_id` and `trace_id` fields
  - [x] Define `ObservabilityProvider` Protocol with all required methods
  - [x] Use `@runtime_checkable` decorator (consistent with `ProgressHandler`)

- [x] Task 3: Implement NoOpProvider (AC: #3)
  - [x] Create `packages/quilto/quilto/observability/noop.py`
  - [x] Implement `NoOpProvider` class that satisfies `ObservabilityProvider` protocol
  - [x] Implement `span()` as null context manager using `@contextmanager`
  - [x] Ensure all methods are safe no-ops (no exceptions)

- [x] Task 4: Write unit tests
  - [x] Test NoOpProvider.span() works as context manager (no exception)
  - [x] Test NoOpProvider.is_enabled() returns False
  - [x] Test NoOpProvider.get_langgraph_callback() returns None
  - [x] Verify protocol is properly defined (pyright passes)

- [x] Task 5: Export from quilto package
  - [x] Update `packages/quilto/quilto/__init__.py` to export `ObservabilityProvider`, `NoOpProvider`, `SpanContext`

## Dev Notes

### Architecture Compliance

**Location:** `quilto/observability/` (top-level module, NOT under `llm/`)

**Rationale from Architecture:**
> Top-level module (not nested under `llm/`) because observability spans:
> - LLM calls (via LangGraph's Langfuse integration)
> - Agent execution flow (graph nodes, state transitions)
> - Tool calls (storage operations, external APIs)

**Source:** [_bmad-output/planning-artifacts/architecture.md#LLM Observability - Location]

### Protocol Specification

The `ObservabilityProvider` protocol MUST match the architecture specification exactly:

```python
# quilto/observability/provider.py
from typing import Protocol, Any, ContextManager, runtime_checkable
from dataclasses import dataclass

@dataclass
class SpanContext:
    """Context for an active span."""
    span_id: str
    trace_id: str

@runtime_checkable
class ObservabilityProvider(Protocol):
    """Protocol for observability backends."""

    # LangGraph integration
    def get_langgraph_callback(self) -> Any | None:
        """Return callback handler for LangGraph execution.

        Returns None if observability is disabled.
        """
        ...

    # Manual span creation (for tool calls)
    def span(
        self,
        name: str,
        metadata: dict[str, Any] | None = None,
        input: Any | None = None,
    ) -> ContextManager[SpanContext]:
        """Create a span for tracing an operation.

        Usage: with provider.span("operation_name"): ...
        """
        ...

    # Event logging
    def log_event(self, name: str, metadata: dict[str, Any] | None = None) -> None:
        """Log an event within the current trace context."""
        ...

    # Error tracking (FR63)
    def log_error(self, error: Exception, metadata: dict[str, Any] | None = None) -> None:
        """Log an error with correlation to current span."""
        ...

    # Lifecycle
    def is_enabled(self) -> bool:
        """Check if observability is active."""
        ...

    def flush(self) -> None:
        """Ensure all traces are sent (call before shutdown)."""
        ...
```

**Source:** [_bmad-output/planning-artifacts/architecture.md#LLM Observability - Provider Interface]

### NoOpProvider Requirements

NoOpProvider MUST:
1. Return `False` from `is_enabled()`
2. Return `None` from `get_langgraph_callback()`
3. Implement `span()` as a null context manager that yields a `SpanContext` with empty/dummy values
4. Make `log_event()` and `log_error()` silent no-ops
5. Make `flush()` a silent no-op

### Codebase Patterns to Follow

**Protocol Pattern (from handlers.py:10-11):**
```python
@runtime_checkable
class ProgressHandler(Protocol):
```

**Imports Pattern:**
```python
from typing import Any, Protocol, runtime_checkable
```

**Docstring Style:** Google-style docstrings with Args/Returns sections

**Model Config:** Use `model_config = ConfigDict(extra="forbid")` for Pydantic models (not applicable here - using dataclass)

### Project Structure Notes

**Files to Create:**
```
packages/quilto/quilto/observability/
├── __init__.py          # Exports: ObservabilityProvider, NoOpProvider, SpanContext
├── provider.py          # Protocol + SpanContext dataclass
└── noop.py              # NoOpProvider implementation
```

**Exports to Add to quilto/__init__.py:**
- `ObservabilityProvider`
- `NoOpProvider`
- `SpanContext`

### Testing Requirements

**Location:** `packages/quilto/tests/observability/test_noop.py`

**Required Tests:**
1. `test_noop_provider_span_context_manager()` - Verify span() works as context manager without raising
2. `test_noop_provider_is_enabled_returns_false()` - Verify is_enabled() returns False
3. `test_noop_provider_get_langgraph_callback_returns_none()` - Verify get_langgraph_callback() returns None
4. `test_noop_provider_log_event_no_exception()` - Verify log_event() doesn't raise
5. `test_noop_provider_log_error_no_exception()` - Verify log_error() doesn't raise
6. `test_noop_provider_flush_no_exception()` - Verify flush() doesn't raise
7. `test_noop_provider_satisfies_protocol()` - Verify isinstance(NoOpProvider(), ObservabilityProvider) is True

**Type Checking:** Run `make check` (pyright) to verify protocol is properly defined

### Context Manager Implementation

For the null context manager, use `contextlib.contextmanager`:

```python
from contextlib import contextmanager
from typing import Generator

@contextmanager
def span(
    self,
    name: str,
    metadata: dict[str, Any] | None = None,
    input: Any | None = None,
) -> Generator[SpanContext, None, None]:
    """No-op span that yields a dummy SpanContext."""
    yield SpanContext(span_id="", trace_id="")
```

### References

- [Source: _bmad-output/planning-artifacts/architecture.md#LLM Observability]
- [Source: _bmad-output/planning-artifacts/prd-quilto.md#FR59-FR63, NFR9]
- [Source: _bmad-output/planning-artifacts/epics.md#Story 24.1]
- [Source: packages/quilto/quilto/handlers.py - Protocol pattern reference]

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

- All 14 unit tests pass
- `make check` passes (lint + pyright 0 errors)
- Full test suite: 2229 passed, 60 skipped

### Completion Notes List

- Created `quilto/observability/` module with `__init__.py`, `provider.py`, `noop.py`
- Implemented `ObservabilityProvider` protocol with all 6 required methods
- Implemented `SpanContext` dataclass with `span_id` and `trace_id` fields
- Implemented `NoOpProvider` class satisfying the protocol
- Used `@runtime_checkable` decorator consistent with `ProgressHandler` pattern
- Used modern Python imports (`AbstractContextManager` from `contextlib`, `Generator` from `collections.abc`)
- Wrote 14 comprehensive unit tests covering all acceptance criteria
- Exported `ObservabilityProvider`, `NoOpProvider`, `SpanContext` from `quilto` package

### File List

- packages/quilto/quilto/observability/__init__.py (new)
- packages/quilto/quilto/observability/provider.py (new)
- packages/quilto/quilto/observability/noop.py (new)
- packages/quilto/quilto/__init__.py (modified - added exports)
- packages/quilto/tests/observability/__init__.py (new)
- packages/quilto/tests/observability/test_noop.py (new)

## Senior Developer Review (AI)

**Reviewer:** Claude Opus 4.5 (claude-opus-4-5-20251101)
**Date:** 2026-01-30
**Outcome:** ✅ APPROVED

### AC Verification

| AC | Status | Evidence |
|----|--------|----------|
| #1 | ✅ | Directory `quilto/observability/` contains all 3 required files |
| #2 | ✅ | `provider.py:26-112` - Protocol with all 6 methods |
| #3 | ✅ | `noop.py:14-86` - Safe no-ops with null context manager |
| #4 | ✅ | `provider.py:13-23` - SpanContext with both fields |

### Task Verification

All 5 tasks and 13 subtasks verified as **ACTUALLY DONE** - code matches claims.

### Issues Found & Fixed

| Severity | Issue | Fix |
|----------|-------|-----|
| MEDIUM | Architecture doc used old `data` param vs implementation's `metadata` | Updated architecture.md |
| MEDIUM | Architecture doc missing `@runtime_checkable` decorator | Updated architecture.md |
| MEDIUM | Architecture doc used `ContextManager` vs `AbstractContextManager` | Updated architecture.md |

### Test Results

- 14/14 observability tests pass
- `make check` passes (lint + pyright 0 errors)

### Final Notes

Implementation is clean, well-documented, follows established patterns (`ProgressHandler` protocol), and correctly uses modern Python idioms. Architecture doc updated to match implementation.

## Change Log

- 2026-01-30: Story implemented - Created ObservabilityProvider protocol, SpanContext dataclass, and NoOpProvider implementation with full test coverage
- 2026-01-30: Code reviewed - Architecture doc updated to match implementation; Status → done
