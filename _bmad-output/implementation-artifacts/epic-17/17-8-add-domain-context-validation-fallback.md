# Story 17.8: Add Domain Context Validation Fallback

Status: done

## Story

As a **Quilto framework developer**,
I want domain context validation to fail gracefully,
so that corrupted state doesn't crash the entire flow.

## Acceptance Criteria

1. **Given** corrupted `domain_context` dict in state
   **When** `ActiveDomainContext.model_validate()` fails
   **Then** default context is used with warning

2. **Given** validation failure
   **When** flow continues
   **Then** error is logged for debugging

## Tasks / Subtasks

- [x] Task 1: Create helper function for defensive domain context reconstruction (AC: #1, #2)
  - [x] Subtask 1.1: Add `_get_domain_context_with_fallback()` function after StateKeys class (~line 130)
  - [x] Subtask 1.2: Function wraps `ActiveDomainContext.model_validate()` in try/except
  - [x] Subtask 1.3: On `ValidationError`, log warning and return minimal valid `ActiveDomainContext`
  - [x] Subtask 1.4: Return tuple `(domain_context, was_fallback)` for caller awareness

- [x] Task 2: Replace unprotected `model_validate()` calls in orchestration.py (AC: #1)
  - [x] Subtask 2.1: Replace in `plan_node` (line ~460)
  - [x] Subtask 2.2: Replace in `analyze_node` (line ~608)
  - [x] Subtask 2.3: Replace in `synthesize_node` (line ~688)
  - [x] Subtask 2.4: Replace in `evaluate_node` (line ~775)
  - [x] Subtask 2.5: Replace in `parse_node` (line ~877)
  - [x] Subtask 2.6: Replace in `correction_node` (line ~936)
  - [x] Subtask 2.7: Replace in `observer_node` (line ~1009)

- [x] Task 3: Update observer_triggers.py with inline fallback (AC: #1, #2)
  - [x] Subtask 3.1: Add inline try/except at line ~535 (avoid circular imports)

- [x] Task 4: Add unit tests for fallback behavior (AC: #1, #2)
  - [x] Subtask 4.1: Test valid context passes through unchanged
  - [x] Subtask 4.2: Test corrupted context triggers fallback with warning
  - [x] Subtask 4.3: Test empty context triggers fallback
  - [x] Subtask 4.4: Test fallback returns minimal valid `ActiveDomainContext`

- [x] Task 5: Run validation - `make check` during dev, `make validate` before commit (AC: All)

## Dev Notes

### Problem Analysis

From Story 17.1 Investigation (Issue 12):
- 8 locations call `ActiveDomainContext.model_validate(domain_context_dict)` without try/except
- If `domain_context_dict` is corrupted in state, `ValidationError` is raised
- Error message is unhelpful; user sees "Synthesizer failed" instead of context issue
- Currently no graceful fallback - entire flow crashes

### Locations Requiring Fix

**orchestration.py** (use grep to verify exact lines before editing):

| Function | Pattern to Find |
|----------|-----------------|
| `plan_node` | `domain_context = ActiveDomainContext.model_validate(domain_context_dict)` |
| `analyze_node` | Same pattern |
| `synthesize_node` | Same pattern |
| `evaluate_node` | Same pattern |
| `parse_node` | Same pattern |
| `correction_node` | Same pattern |
| `observer_node` | Same pattern |

**observer_triggers.py:**

| Function | Pattern to Find |
|----------|-----------------|
| `trigger_observer_if_needed` | `active_domain_context = ActiveDomainContext.model_validate(...)` |

### Line Number Discovery

Use `grep -n "ActiveDomainContext.model_validate" packages/quilto/quilto/orchestration.py` to find current line numbers before editing.

### Minimal Valid ActiveDomainContext

From `quilto/agents/models.py`:

```python
class ActiveDomainContext(BaseModel):
    model_config = ConfigDict(strict=True)

    domains_loaded: list[str]  # Required
    vocabulary: dict[str, str]  # Required
    expertise: str  # Required
    evaluation_rules: list[str] = []  # Optional with default
    context_guidance: str = ""  # Optional with default
    available_domains: list[DomainInfo] = []  # Optional with default
    clarification_patterns: dict[str, list[str]] = {}  # Optional with default
```

**Minimal fallback:**
```python
ActiveDomainContext(
    domains_loaded=[],
    vocabulary={},
    expertise="General assistant",
)
```

### Implementation Pattern

**Helper Function (add after StateKeys class in orchestration.py):**

```python
def _get_domain_context_with_fallback(
    state: QuiltoState, caller: str
) -> tuple[ActiveDomainContext, bool]:
    """Get domain context from state with validation fallback.

    Args:
        state: Current orchestration state.
        caller: Name of the calling function for logging.

    Returns:
        Tuple of (domain_context, was_fallback). If was_fallback is True,
        the context is a minimal valid fallback due to validation failure.
    """
    from pydantic import ValidationError

    from quilto.agents.models import ActiveDomainContext

    domain_context_dict = state.get(StateKeys.DOMAIN_CONTEXT, {})

    try:
        return (ActiveDomainContext.model_validate(domain_context_dict), False)
    except ValidationError as e:
        logger.warning(
            "%s: domain_context validation failed, using fallback. Error: %s",
            caller,
            e.errors(),
        )
        return (
            ActiveDomainContext(
                domains_loaded=[],
                vocabulary={},
                expertise="General assistant",
            ),
            True,
        )
```

**Usage Pattern - Before:**

```python
# In plan_node
domain_context_dict = state.get(StateKeys.DOMAIN_CONTEXT, {})
domain_context = ActiveDomainContext.model_validate(domain_context_dict)
```

**Usage Pattern - After:**

```python
# In plan_node - replaces BOTH lines above
domain_context, _was_fallback = _get_domain_context_with_fallback(state, "plan_node")
```

### Special Case: synthesize_node

`synthesize_node` already has a try/except pattern for `AnalyzerOutput.model_validate()` (lines 692-709). Apply the same defensive pattern to `ActiveDomainContext` for consistency. The existing `AnalyzerOutput` fallback should remain unchanged.

### Special Case: observer_triggers.py

This file is in `quilto/state/observer_triggers.py`. To avoid circular imports with orchestration.py, **duplicate the pattern inline**:

```python
# In trigger_observer_if_needed, replace line ~535
active_domain_context_dict = state.get("active_domain_context")

if active_domain_context_dict is None:
    return {"next_state": "COMPLETE", "observer_output": None}

try:
    active_domain_context = ActiveDomainContext.model_validate(active_domain_context_dict)
except ValidationError as e:
    logger.warning(
        "trigger_observer_if_needed: domain_context validation failed, skipping observer. Error: %s",
        e.errors(),
    )
    return {"next_state": "COMPLETE", "observer_output": None}
```

Note: `observer_triggers.py` uses hardcoded `"active_domain_context"` string (not StateKeys) because StateKeys is in orchestration.py. This is acceptable as this file is a separate module.

### Test Strategy

**File:** `packages/quilto/tests/test_orchestration_domain_context_fallback.py`

Follow naming convention from Story 17.5 (`test_orchestration_observer_errors.py`).

```python
import pytest

from quilto.agents.models import ActiveDomainContext
from quilto.orchestration import StateKeys, _get_domain_context_with_fallback


class TestDomainContextFallback:
    """Tests for defensive domain context validation."""

    def test_valid_context_passes_through(self):
        """Valid domain context is returned unchanged."""
        valid_dict = {
            "domains_loaded": ["fitness"],
            "vocabulary": {"squat": "squat"},
            "expertise": "Fitness expert",
        }
        state = {StateKeys.DOMAIN_CONTEXT: valid_dict}

        context, was_fallback = _get_domain_context_with_fallback(state, "test")

        assert was_fallback is False
        assert context.domains_loaded == ["fitness"]
        assert context.vocabulary == {"squat": "squat"}

    def test_corrupted_context_triggers_fallback(self, caplog):
        """Corrupted context returns fallback with warning."""
        # Missing required field 'domains_loaded'
        corrupted_dict = {
            "vocabulary": {"squat": "squat"},
            "expertise": "Fitness expert",
        }
        state = {StateKeys.DOMAIN_CONTEXT: corrupted_dict}

        context, was_fallback = _get_domain_context_with_fallback(state, "test")

        assert was_fallback is True
        assert context.domains_loaded == []
        assert context.vocabulary == {}
        assert "validation failed" in caplog.text.lower()

    def test_empty_context_triggers_fallback(self, caplog):
        """Empty context dict triggers fallback."""
        state = {StateKeys.DOMAIN_CONTEXT: {}}

        context, was_fallback = _get_domain_context_with_fallback(state, "test")

        assert was_fallback is True
        assert context.expertise == "General assistant"

    def test_missing_context_key_triggers_fallback(self, caplog):
        """Missing context key triggers fallback."""
        state = {}  # No DOMAIN_CONTEXT key

        context, was_fallback = _get_domain_context_with_fallback(state, "test")

        assert was_fallback is True
        assert context.expertise == "General assistant"

    def test_wrong_type_triggers_fallback(self, caplog):
        """Wrong type in context dict triggers fallback."""
        # domains_loaded should be list[str], not str
        corrupted_dict = {
            "domains_loaded": "fitness",  # Wrong: should be list
            "vocabulary": {},
            "expertise": "Fitness expert",
        }
        state = {StateKeys.DOMAIN_CONTEXT: corrupted_dict}

        context, was_fallback = _get_domain_context_with_fallback(state, "test")

        assert was_fallback is True
        assert "validation failed" in caplog.text.lower()
```

### Project Structure

- **Package:** Quilto (`packages/quilto/`)
- **Files to Modify:**
  - `quilto/orchestration.py` - Add helper function, replace 7 occurrences
  - `quilto/state/observer_triggers.py` - Inline fallback pattern (1 occurrence)
- **Files to Create:**
  - `packages/quilto/tests/test_orchestration_domain_context_fallback.py` - Unit tests

### Previous Story Intelligence

Stories 17.4-17.7 established patterns:
- Simple helper functions with clear docstrings (Story 17.4)
- Tuple returns for caller awareness (Story 17.5 error_info pattern)
- `caplog` fixture for warning assertions (Story 17.5)
- `StateKeys` constants for all state access (Story 17.7)
- Consistent error logging with caller name (Story 17.5)
- Test file naming: `test_orchestration_*.py` (Story 17.5)

### Validation Commands

```bash
# 1. Run quick check during development
make check

# 2. Run full validation before commit
make validate
```

### Architecture Compliance

- **No new dependencies** - Uses existing `pydantic.ValidationError`
- **Follows existing patterns** - Similar to `AnalyzerOutput` fallback in `synthesize_node` (lines 692-709)
- **Non-breaking** - Fallback is backward compatible; normal flow unchanged
- **Logging** - Uses existing `logger` instance for warnings
- **StateKeys** - Uses `StateKeys.DOMAIN_CONTEXT` constant from Story 17.7

### Existing Fallback Pattern Reference

`synthesize_node` (lines 692-709) already implements this pattern for `AnalyzerOutput`:

```python
# Reconstruct AnalyzerOutput with defensive validation
analyzer_output_dict = state.get(StateKeys.ANALYZER_OUTPUT, {})
try:
    analyzer_output = AnalyzerOutput.model_validate(analyzer_output_dict)
except Exception as validation_err:
    logger.warning("Invalid analyzer_output, using minimal fallback: %s", validation_err)
    # Create minimal valid AnalyzerOutput for synthesizer
    analyzer_output = AnalyzerOutput(
        query_intent="Analysis unavailable",
        findings=[],
        patterns_identified=[],
        sufficiency_evaluation=SufficiencyEvaluation(
            critical_gaps=[],
            nice_to_have_gaps=[],
            evidence_check_passed=False,
            speculation_risk="high",
        ),
        verdict_reasoning="Analyzer output invalid or missing",
        verdict=Verdict.INSUFFICIENT,
    )
```

This story standardizes the pattern for `ActiveDomainContext` across all nodes.

### Related Issue: evaluate_node AnalyzerOutput

Note: `evaluate_node` (line ~779) also has unprotected `AnalyzerOutput.model_validate()`. Consider applying the same fallback pattern there for consistency, but this is out of scope for Story 17.8 (focus on `ActiveDomainContext` only).

### References

- Story 17.1: Investigation - Issue 12: Domain Context Validation Missing
- Story 17.5: Observer Error Propagation - test pattern and logging conventions
- Story 17.7: StateKeys class definition
- `orchestration.py:692-709`: Existing AnalyzerOutput fallback pattern (template)
- `project-context.md`: Quilto vs Swealog package guidelines

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

N/A

### Completion Notes List

1. Created `_get_domain_context_with_fallback()` helper function in orchestration.py (lines 137-168)
2. Function returns `tuple[ActiveDomainContext, bool]` where second value indicates fallback was used
3. On `ValidationError`, logs warning with caller name and error details, returns minimal valid context
4. Replaced all 7 `ActiveDomainContext.model_validate()` calls in orchestration.py nodes:
   - `plan_node`, `analyze_node`, `synthesize_node`, `evaluate_node`, `parse_node`, `correction_node`, `observer_node`
5. `observer_node` uses `was_fallback` to return error instead of continuing with invalid context
6. Added inline try/except in `observer_triggers.py` (lines 538-545) to avoid circular imports
7. Added `ValidationError` import and `logger` instance to observer_triggers.py
8. Created comprehensive unit test file with 7 test cases covering all scenarios
9. All 2062 tests pass, `make validate` successful

### File List

- `packages/quilto/quilto/orchestration.py` - Added helper function, updated 7 node functions
- `packages/quilto/quilto/state/observer_triggers.py` - Added inline fallback pattern
- `packages/quilto/tests/test_orchestration_domain_context_fallback.py` - New test file (7 tests)
- `packages/quilto/tests/test_observer_triggers.py` - Added 2 tests for inline fallback coverage

## Senior Developer Review (AI)

**Reviewer:** Claude Opus 4.5
**Date:** 2026-01-28
**Outcome:** APPROVED

### Review Summary

All tasks verified complete. Implementation follows established patterns from Stories 17.4-17.7.

### Issues Found and Fixed

| ID | Severity | Issue | Resolution |
|----|----------|-------|------------|
| M3 | MEDIUM | Missing tests for `observer_triggers.py` inline fallback | Added `test_corrupted_domain_context_skips_gracefully` and `test_missing_domain_context_skips_gracefully` to `test_observer_triggers.py` |

### Accepted Exceptions (Documented in Dev Notes)

1. `evaluate_node` unprotected `AnalyzerOutput.model_validate()` - Out of scope per story notes
2. Hardcoded `"active_domain_context"` in `observer_triggers.py` - Circular import avoidance documented

### Verification

- All 2064 tests pass (`make validate`)
- `make check` passes (lint + typecheck)
- File List matches git changes
