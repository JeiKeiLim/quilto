# Story 17.6: Protect State Dict Access

Status: done

## Story

As a **Quilto framework developer**,
I want all state dict access to use `.get()` with defaults,
so that missing keys cause graceful degradation, not crashes.

## Acceptance Criteria

1. **Given** `state["user_input"]` access
   **When** key is missing
   **Then** default value is used (not KeyError)

2. **Given** `state["_quilto"]` access
   **When** key is missing
   **Then** error is logged and handled gracefully

3. **Given** all direct `state["key"]` patterns
   **When** audited
   **Then** converted to `state.get("key", default)`

## Tasks

**Target File:** `packages/quilto/quilto/orchestration.py`

- [x] Task 1: Create helper function `_get_quilto()` for centralized `_quilto` access with logging (AC: #2)
  - Place after `_add_trace()` function (around line 255), before node functions
  - Return `Quilto | None` with error logging when missing
- [x] Task 2: Replace all `state["_quilto"]` direct access with helper + error handling (AC: #2)
  - All 10 locations: lines 271, 345, 436, 490, 567, 651, 751, 809, 873, 973
  - Return `{"error": "Internal error: orchestration not initialized"}` when None
- [x] Task 3: Replace all `state["user_input"]` direct access with `.get("user_input", "")` (AC: #1)
  - All 7 locations: lines 272, 346, 491, 568, 652, 752, 904
- [x] Task 4: Add unit tests for missing key handling (AC: #1, #2, #3)
- [x] Task 5: Run validation - `make check` during dev, `make validate` before commit (AC: All)

## Dev Notes

### Root Cause

Multiple locations in `orchestration.py` use direct dict access `state["key"]` which raises `KeyError` if the key is missing. This can occur when:
1. Graph state is corrupted
2. A node is called in isolation (testing)
3. State initialization is incomplete

### Current Problem Locations

From grep analysis, 17 direct `state["key"]` accesses exist (excluding the write on line 1170):

| Line | Access | Node |
|------|--------|------|
| 271 | `state["_quilto"]` | `route_node` |
| 272 | `state["user_input"]` | `route_node` |
| 345 | `state["_quilto"]` | `plan_node` |
| 346 | `state["user_input"]` | `plan_node` |
| 436 | `state["_quilto"]` | `retrieve_node` |
| 490 | `state["_quilto"]` | `analyze_node` |
| 491 | `state["user_input"]` | `analyze_node` |
| 567 | `state["_quilto"]` | `synthesize_node` |
| 568 | `state["user_input"]` | `synthesize_node` |
| 651 | `state["_quilto"]` | `evaluate_node` |
| 652 | `state["user_input"]` | `evaluate_node` |
| 751 | `state["_quilto"]` | `parse_node` |
| 752 | `state["user_input"]` | `parse_node` |
| 809 | `state["_quilto"]` | `correction_node` |
| 873 | `state["_quilto"]` | `observe_node` |
| 904 | `state["user_input"]` | `observe_node` |
| 973 | `state["_quilto"]` | `retry_node` |
| 1170 | `state["_quilto"] = ...` | `run()` (write, not read - OK) |

### Implementation Strategy

**Strategy A: Direct `.get()` for `user_input`**

Simple replacement with empty string default:

```python
# Before (line 272)
user_input: str = state["user_input"]  # type: ignore[typeddict-item]

# After
user_input: str = state.get("user_input", "")
```

**Strategy B: Helper Function for `_quilto` (REQUIRED)**

Create centralized helper since `_quilto` is required in every node:

```python
def _get_quilto(state: QuiltoState, node_name: str) -> "Quilto | None":
    """Get Quilto instance from state with error logging.

    Args:
        state: Current orchestration state.
        node_name: Name of the calling node for error messages.

    Returns:
        Quilto instance or None if missing.
    """
    quilto = state.get("_quilto")
    if quilto is None:
        logger.error("%s: Missing _quilto in state - graph not initialized", node_name)
    return quilto
```

**Node Pattern After Fix:**

Each node that requires `_quilto` must check for None and return error state:

```python
async def route_node(state: QuiltoState) -> dict[str, Any]:
    """Route node - classifies input and selects domains."""
    quilto = _get_quilto(state, "route_node")
    if quilto is None:
        return {"error": "Internal error: orchestration not initialized"}

    user_input: str = state.get("user_input", "")
    # ... rest of node
```

### Type Ignore Comments

After these changes, the `# type: ignore[typeddict-item]` comments should be **REMOVED** for:
- `user_input` access (now using `.get()` with default)
- `_quilto` access (now using helper that returns Optional)

Some type ignores may still be needed for the TypedDict optional field access pattern, but test by removing first.

### Helper Function Placement

Place `_get_quilto()` helper function:
- After `_add_trace()` (around line 255)
- Before the node functions section (before line 260)
- This follows the existing pattern of placing utility functions before the nodes that use them

### Test Strategy

**New file:** `packages/quilto/tests/test_orchestration_state_access.py`

**Test Pattern:** Follow established approach from Story 17.4 and 17.5:
- Create helper functions that mimic orchestration behavior
- Test helpers directly rather than calling actual async orchestration nodes
- Reference `test_orchestration_eval_feedback.py` and `test_orchestration_observer_errors.py` as templates

**Test Classes:**

```python
class TestGetQuiltoHelper:
    """Tests for _get_quilto helper function."""

    def test_returns_quilto_when_present(self):
        """Verify helper returns Quilto when present in state."""
        # Create mock Quilto, add to state, verify return value

    def test_returns_none_when_missing(self):
        """Verify helper returns None when _quilto missing."""

    def test_logs_error_when_missing(self, caplog):
        """Verify error is logged with node name when _quilto missing."""


class TestNodeMissingQuilto:
    """Tests for node error handling when _quilto is missing."""

    def test_node_returns_error_state_when_quilto_none(self):
        """Verify nodes return error state when _quilto is None."""
        # Test the pattern: if quilto is None: return {"error": ...}


class TestUserInputDefaults:
    """Tests for user_input default value handling."""

    def test_empty_string_default_when_missing(self):
        """Verify user_input defaults to empty string."""

    def test_preserves_value_when_present(self):
        """Verify user_input value preserved when present."""
```

### Project Structure

- **Package:** Quilto (`packages/quilto/`)
- **File:** `quilto/orchestration.py`
- **Tests:** `packages/quilto/tests/test_orchestration_state_access.py`

### Previous Story Intelligence

Stories 17.2-17.5 established patterns:
- Simple, targeted fixes without over-engineering
- Clear before/after code blocks in dev notes
- Minimal changes to achieve goal
- Test file structure with clear test class names
- Helper functions mimic orchestration behavior for isolated testing
- Reference existing test files as templates

### Validation Commands

```bash
# 1. Run quick check during development
make check

# 2. Run full validation before commit
make validate
```

### Architecture Compliance

- **No new dependencies** - Uses existing patterns
- **Backward compatible** - Existing code paths unchanged
- **Follows existing logging pattern** - Uses `logger.error/warning`
- **Error state return** - Uses existing `{"error": "..."}` pattern from other nodes

### References

- [Source: `17-1-query-flow-investigation.md` - Issue 9: Unprotected State Dict Access]
- [Source: `epics.md#story-176-protect-state-dict-access`]
- [Source: `project-context.md`]
- [Source: `orchestration.py` - lines 271, 272, 345, 346, 436, 490, 491, 567, 568, 651, 652, 751, 752, 809, 873, 904, 973]
- [Template: `test_orchestration_eval_feedback.py` - helper function pattern]
- [Template: `test_orchestration_observer_errors.py` - test class structure]

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

N/A

### Completion Notes List

1. Created `_get_quilto()` helper function at line 257 (after `_add_trace()`) that returns `Quilto | None` with error logging
2. Replaced all 10 `state["_quilto"]` direct accesses in nodes: `route_node`, `plan_node`, `retrieve_node`, `analyze_node`, `synthesize_node`, `evaluate_node`, `parse_node`, `correction_node`, `observe_node`, `retry_node`
3. Each node now checks for `None` and returns `{"error": "Internal error: orchestration not initialized"}` on failure
4. Replaced all 7 `state["user_input"]` direct accesses with `.get("user_input", "")` pattern
5. Removed `# type: ignore[typeddict-item]` comments where no longer needed
6. Created comprehensive unit tests following established patterns from `test_orchestration_eval_feedback.py` and `test_orchestration_observer_errors.py`
7. All 2048 tests pass, 0 lint errors, 0 type errors

### File List

- `packages/quilto/quilto/orchestration.py` (modified)
- `packages/quilto/tests/test_orchestration_state_access.py` (created)
