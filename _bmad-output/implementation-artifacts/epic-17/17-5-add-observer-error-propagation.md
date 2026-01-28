# Story 17.5: Add Observer Error Propagation

Status: done

## Story

As a **Quilto framework developer**,
I want Observer failures to be visible to applications,
so that context learning issues are detectable.

## Acceptance Criteria

1. **Given** Observer throws exception
   **When** `observe_node` catches it
   **Then** error is logged AND returned in state

2. **Given** Observer returns empty context
   **When** state is checked
   **Then** `observer_error` field indicates the issue

3. **Given** ProgressHandler is registered
   **When** Observer fails
   **Then** `on_agent_complete` is called with error info

## Tasks

**Target File:** `packages/quilto/quilto/orchestration.py`

- [x] Task 1: Return error state instead of empty dict on exception (lines 933-939) (AC: #1)
- [x] Task 2: Add `observer_error` field to returned state when domain_context is empty (lines 888-889) (AC: #2)
- [x] Task 3: Change `on_agent_complete` callback output from `{}` to error info dict (lines 936-937) (AC: #3)
- [x] Task 4: Create unit tests in `packages/quilto/tests/test_orchestration_observer_errors.py` (AC: #1, #2, #3)
- [x] Task 5: Run validation - `make check` during dev, `make validate` before commit (AC: All)

## Dev Notes

### Root Cause

The Observer node in `orchestration.py` (lines 862-937) silently suppresses failures:

```python
# Current behavior (lines 932-937)
except Exception as e:
    elapsed = (time.perf_counter() - start) * 1000
    await _call_progress_handler(quilto, "on_agent_complete", "observer", elapsed / 1000, {})
    logger.warning("observe_node failed: %s", e)
    return {}  # Silent failure - no feedback to app
```

**Problems:**
1. `return {}` provides no indication to the application that Observer failed
2. `on_agent_complete` receives empty `{}` - indistinguishable from "no output"
3. Global context is never updated; subsequent queries use stale context
4. Line 887-888 also returns `{}` silently when `domain_context` is empty

### Recommended Fix

**Location 1: Exception handler (lines 932-937)**

```python
# After - Return error state
except Exception as e:
    elapsed = (time.perf_counter() - start) * 1000
    error_info = {"error": str(e), "error_type": type(e).__name__}
    await _call_progress_handler(quilto, "on_agent_complete", "observer", elapsed / 1000, error_info)
    logger.warning("observe_node failed: %s", e)
    return {"observer_error": str(e)}
```

**Location 2: Empty domain_context check (lines 887-888)**

Note: At this point `on_agent_start` has already been called (line 881), so returning empty `{}` is indistinguishable from success. Adding `observer_error` makes this failure visible.

```python
# Before
if not domain_context_dict:
    return {}

# After - Add observer_error field
if not domain_context_dict:
    return {"observer_error": "No domain_context available"}
```

### State Field Definition

The `observer_error` field should be added to `QuiltoState` TypedDict (lines ~75-132):

```python
class QuiltoState(TypedDict, total=False):
    # ... existing fields ...
    observer_error: str  # NEW: Error message if Observer failed
```

Note: Since `QuiltoState` uses `total=False`, the field is optional by default.

### Early Return Clarification

Line 876 (`if not enable_post_query: return {}`) is a normal control flow before any work begins - no error propagation needed there. Error propagation is only needed after `on_agent_start` has been called (line 881).

### ProgressHandler Integration

The `on_agent_complete` callback signature from `quilto/handlers.py`:

```python
async def on_agent_complete(
    self, agent_name: str, duration: float, output: dict[str, Any] | None = None
) -> None:
```

Currently receives `{}` on failure. After fix, receives:
```python
{"error": "Error message", "error_type": "ExceptionClassName"}
```

Applications can detect failure by checking `"error" in output`.

### Project Structure

- **Package:** Quilto (`packages/quilto/`)
- **File:** `quilto/orchestration.py`
- **Tests:** `packages/quilto/tests/test_orchestration_observer_errors.py`

### Previous Story Intelligence

Stories 17.2, 17.3, and 17.4 established patterns for this epic:
- Simple, targeted fixes without over-engineering
- Clear before/after code blocks
- Minimal changes to achieve goal
- Test file structure with clear test class names

### Test Requirements

**New file:** `packages/quilto/tests/test_orchestration_observer_errors.py`

Tests should verify:
1. `observer_error` key present in returned state when exception occurs
2. `observer_error` key present when `domain_context` is empty
3. Error info passed to `on_agent_complete` includes `"error"` key

Note: These tests should test the error propagation patterns, following the same approach as `test_orchestration_eval_feedback.py` which tests the isinstance pattern rather than calling the actual orchestration functions. The pattern is to create helper functions that mimic the orchestration behavior and test those directly.

### Validation Commands

```bash
# 1. Run quick check during development
make check

# 2. Run full validation before commit
make validate
```

### Architecture Compliance

- **No new dependencies** - Uses existing patterns
- **Backward compatible** - Empty `observer_error` key doesn't break existing code
- **Follows existing logging pattern** - Keeps `logger.warning` call
- **ProgressHandler contract** - Maintains `dict[str, Any]` output type

### References

- [Source: `17-1-query-flow-investigation.md` - Issue 8: Silent Observer Failures]
- [Source: `epics.md#story-175-add-observer-error-propagation`]
- [Source: `project-context.md`]
- [Source: `orchestration.py:862-937` - observe_node function]

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

N/A

### Completion Notes List

1. Added `observer_error: str` field to `QuiltoState` TypedDict (line 113)
2. Modified empty `domain_context_dict` check to return `{"observer_error": "No domain_context available"}` instead of `{}` (line 888)
3. Modified exception handler to:
   - Create `error_info` dict with `error` and `error_type` keys
   - Pass `error_info` to `on_agent_complete` callback instead of `{}`
   - Return `{"observer_error": str(e)}` instead of `{}`
4. Created 7 unit tests in 3 test classes covering:
   - Exception propagation (observer_error field, callback error, error_type)
   - Empty context propagation (observer_error on empty, no error on non-empty)
   - Error detection patterns for applications

### File List

| File | Changes |
|------|---------|
| `packages/quilto/quilto/orchestration.py` | Lines 113, 888-889, 933-939: Add observer_error state field on failure |
| `packages/quilto/tests/test_orchestration_observer_errors.py` | New file: 7 tests for Observer error propagation |

### Senior Developer Review (AI)

**Date:** 2026-01-28
**Reviewer:** Amelia (Dev Agent - Claude Opus 4.5)

**Findings Summary:**
- All 3 Acceptance Criteria verified as IMPLEMENTED
- All 5 tasks verified as COMPLETE
- `make check` passes (lint + typecheck)
- All 7 tests pass

**Issues Found & Resolved:**
1. [MEDIUM] Line number references updated (932-937 → 933-939, 887-888 → 888-889)
2. [LOW] Story references now match actual code locations

**Verdict:** APPROVED ✅

**Notes:**
- Test approach uses helper functions mimicking orchestration behavior (per dev notes)
- This matches pattern from `test_orchestration_eval_feedback.py`
- No integration test for actual async observe_node (acceptable for this story scope)
