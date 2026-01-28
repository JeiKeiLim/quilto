# Story 17.7: Define State Key Constants

Status: done

## Story

As a **Quilto framework developer**,
I want state keys defined as constants,
so that typos are caught at compile time.

## Acceptance Criteria

1. **Given** a new `StateKeys` class or module
   **When** imported
   **Then** all keys are available as constants

2. **Given** all hardcoded state keys
   **When** replaced with constants
   **Then** no string literals for state keys in orchestration.py

3. **Given** a typo in key name
   **When** code is checked by pyright
   **Then** error is detected

## Tasks

**Target File:** `packages/quilto/quilto/orchestration.py`

- [x] Task 1: Create `StateKeys` class with all state key constants (AC: #1)
  - Place near top of file after imports, before `QuiltoState` TypedDict
  - Use `Final` type annotation for pyright detection
  - Include all 25 unique state keys identified in current usage
- [x] Task 2: Replace all hardcoded state keys in `state.get()` calls with `StateKeys.` constants (AC: #2)
  - 48 occurrences across 10 node functions
  - Maintain existing default values
- [x] Task 3: Replace the single `state["_quilto"] = ...` write with constant (AC: #2)
  - Line 1213: `state[StateKeys.QUILTO] = self._quilto`
- [x] Task 4: Add unit tests verifying constant usage and typo detection (AC: #3)
- [x] Task 5: Run validation - `make check` during dev, `make validate` before commit (AC: All)

## Dev Notes

### Problem Analysis

From grep analysis of `orchestration.py`, there are 48 `state.get("key")` calls using 25 unique string keys:

| Key | Occurrences | Usage |
|-----|-------------|-------|
| `_quilto` | 1 (write) + helper | Internal Quilto reference |
| `traces` | 1 | Debug traces list |
| `user_input` | 7 | User input string |
| `mode` | 1 | Processing mode |
| `conversation_context` | 1 | Previous conversation |
| `domain_context` | 7 | Domain-specific context |
| `eval_feedback` | 2 | Evaluator feedback |
| `retry_count` | 4 | Current retry attempt |
| `retrieval_summary` | 3 | Retrieval results |
| `retrieval_instructions` | 1 | Planner instructions |
| `entries` | 2 | Retrieved entries |
| `query_type` | 2 | Query classification |
| `analysis_verdict` | 1 | Analyzer verdict |
| `analyzer_output` | 3 | Analyzer output dict |
| `is_partial` | 1 | Partial response flag |
| `response` | 2 | Generated response |
| `router_output` | 1 | Router output dict |
| `eval_verdict` | 2 | Evaluator verdict |
| `max_retries` | 2 | Maximum retry count |
| `input_type` | 2 | Input classification |
| `next_action` | 1 | Planner next action |
| `storage_summary` | implied | Storage summary dict |
| `selected_domains` | implied | Selected domains |
| `error` | implied | Error message |
| `confidence` | implied | Confidence score |

### Implementation Pattern

**StateKeys Class Design:**

```python
from typing import Final

class StateKeys:
    """Constants for QuiltoState dictionary keys.

    Using constants instead of string literals enables:
    - Compile-time typo detection via pyright
    - IDE autocomplete and navigation
    - Single source of truth for key names
    """

    # Internal
    QUILTO: Final[str] = "_quilto"
    TRACES: Final[str] = "traces"

    # Input
    USER_INPUT: Final[str] = "user_input"
    MODE: Final[str] = "mode"
    CONVERSATION_CONTEXT: Final[str] = "conversation_context"

    # Router output
    INPUT_TYPE: Final[str] = "input_type"
    SELECTED_DOMAINS: Final[str] = "selected_domains"
    ROUTER_OUTPUT: Final[str] = "router_output"

    # Planner output
    QUERY_TYPE: Final[str] = "query_type"
    RETRIEVAL_INSTRUCTIONS: Final[str] = "retrieval_instructions"
    NEXT_ACTION: Final[str] = "next_action"
    CLARIFY_QUESTIONS: Final[str] = "clarify_questions"
    PLANNER_OUTPUT: Final[str] = "planner_output"

    # Retriever output
    ENTRIES: Final[str] = "entries"
    RETRIEVAL_SUMMARY: Final[str] = "retrieval_summary"
    SOURCE_ENTRY_IDS: Final[str] = "source_entry_ids"
    RETRIEVER_OUTPUT: Final[str] = "retriever_output"

    # Analyzer output
    ANALYSIS_VERDICT: Final[str] = "analysis_verdict"
    ANALYSIS_FINDINGS: Final[str] = "analysis_findings"
    ANALYZER_OUTPUT: Final[str] = "analyzer_output"

    # Synthesizer output
    RESPONSE: Final[str] = "response"
    SYNTHESIZER_OUTPUT: Final[str] = "synthesizer_output"

    # Evaluator output
    EVAL_VERDICT: Final[str] = "eval_verdict"
    EVAL_FEEDBACK: Final[str] = "eval_feedback"
    EVALUATOR_OUTPUT: Final[str] = "evaluator_output"

    # Parser output
    PARSED_DATA: Final[str] = "parsed_data"
    PARSER_OUTPUT: Final[str] = "parser_output"

    # Correction output
    CORRECTION_RESULT: Final[str] = "correction_result"

    # Observer output
    OBSERVER_OUTPUT: Final[str] = "observer_output"
    OBSERVER_ERROR: Final[str] = "observer_error"

    # Control
    RETRY_COUNT: Final[str] = "retry_count"
    MAX_RETRIES: Final[str] = "max_retries"
    IS_PARTIAL: Final[str] = "is_partial"
    ERROR: Final[str] = "error"

    # Context objects
    DOMAIN_CONTEXT: Final[str] = "domain_context"
    STORAGE_SUMMARY: Final[str] = "storage_summary"

    # Metrics
    CONFIDENCE: Final[str] = "confidence"
    TOTAL_ELAPSED_MS: Final[str] = "total_elapsed_ms"
```

**Usage Pattern - Before:**

```python
user_input: str = state.get("user_input", "")
domain_context_dict = state.get("domain_context", {})
retry_count = state.get("retry_count", 0)
```

**Usage Pattern - After:**

```python
user_input: str = state.get(StateKeys.USER_INPUT, "")
domain_context_dict = state.get(StateKeys.DOMAIN_CONTEXT, {})
retry_count = state.get(StateKeys.RETRY_COUNT, 0)
```

### Typo Detection Example

With string literals, this typo compiles silently:

```python
# Bug: typo in "user_input"
user_input = state.get("user_imput", "")  # Silently uses default
```

With constants, pyright catches it:

```python
# Error: "USER_IMPUT" is not a member of "StateKeys"
user_input = state.get(StateKeys.USER_IMPUT, "")
```

### Placement

Place `StateKeys` class:
- After imports (around line 50)
- Before `QuiltoState` TypedDict definition (currently at line 60)
- This allows `QuiltoState` to potentially reference `StateKeys` in future refactoring

### Test Strategy

**New file:** `packages/quilto/tests/test_state_keys.py`

**Test Pattern:** Verify constants match TypedDict and catch typos:

```python
class TestStateKeysConstants:
    """Tests for StateKeys constant definitions."""

    def test_all_quilto_state_fields_have_constants(self):
        """Verify StateKeys covers all QuiltoState TypedDict fields."""
        # Get QuiltoState __annotations__ keys
        # Compare against StateKeys values
        # Assert no missing constants

    def test_constant_values_match_typeddict_keys(self):
        """Verify constant values exactly match QuiltoState keys."""

    def test_no_duplicate_constant_values(self):
        """Verify no two constants have the same value."""


class TestStateKeysUsage:
    """Tests for StateKeys usage patterns."""

    def test_state_get_with_constant(self):
        """Verify state.get() works correctly with constants."""
        state = {"user_input": "test input"}
        result = state.get(StateKeys.USER_INPUT, "")
        assert result == "test input"

    def test_state_get_default_with_constant(self):
        """Verify default value works with constants."""
        state: dict[str, Any] = {}
        result = state.get(StateKeys.USER_INPUT, "default")
        assert result == "default"
```

### Project Structure

- **Package:** Quilto (`packages/quilto/`)
- **File:** `quilto/orchestration.py`
- **Tests:** `packages/quilto/tests/test_state_keys.py`

### Previous Story Intelligence

Stories 17.2-17.6 established patterns:
- Simple, targeted fixes without over-engineering
- Clear before/after code blocks in dev notes
- Minimal changes to achieve goal
- Test file structure with clear test class names
- Reference existing test files as templates

### Validation Commands

```bash
# 1. Run quick check during development
make check

# 2. Run full validation before commit
make validate
```

### Architecture Compliance

- **No new dependencies** - Uses `typing.Final` from stdlib
- **Backward compatible** - String values unchanged
- **Follows existing patterns** - Similar to confidence constant pattern at top of file
- **Pyright integration** - `Final` annotation enables static type checking

### References

- [Source: `17-1-query-flow-investigation.md` - Issue 10: Hardcoded State Keys]
- [Source: `epics.md#story-177-define-state-key-constants`]
- [Source: `project-context.md`]
- [Source: `orchestration.py` - 48 state.get() calls, 25 unique keys]
- [Template: `test_orchestration_state_access.py` - test patterns from Story 17.6]

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

N/A

### Completion Notes List

1. Created `StateKeys` class with 32 `Final[str]` constants covering all `QuiltoState` TypedDict fields
2. Replaced 48 hardcoded `state.get("key", ...)` calls across 10 node functions with `StateKeys.` constants
3. Replaced single `state["_quilto"] = ...` write in `QuiltoGraph.ainvoke` with `StateKeys.QUILTO`
4. Created comprehensive test suite in `test_state_keys.py`:
   - `TestStateKeysConstants`: Verifies all TypedDict fields have constants, no duplicates
   - `TestStateKeysUsage`: Verifies get/set patterns work correctly with constants
5. All validation passed: `make check` (lint + typecheck), `make validate` (2055 tests passed)

**Code Review Fixes Applied:**
6. Replaced ~50 hardcoded string keys in return dictionaries with `StateKeys.` constants (AC #2 complete)
7. Exported `StateKeys` in `quilto/__init__.py` for package consumers
8. Added pyright typo detection documentation example in test docstring (AC #3 documentation)

### File List

- `packages/quilto/quilto/orchestration.py` - Added `StateKeys` class, replaced all hardcoded keys (reads + writes)
- `packages/quilto/quilto/__init__.py` - Exported `StateKeys` for package consumers
- `packages/quilto/tests/test_state_keys.py` - New test file for StateKeys constants

