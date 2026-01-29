# Story 22.3: Add Observer Validation - Prevent Hallucinated Facts

Status: done

## Story

As a **developer**,
I want **validation that Observer only stores user-stated information**,
so that **hallucinated facts are prevented from polluting global context**.

## Acceptance Criteria

1. **Given** Observer output with a fact not in user input
   **When** validation runs
   **Then** fact is filtered out with warning logged

2. **Given** Observer output with correctly sourced fact
   **When** validation runs
   **Then** fact passes validation and is stored

3. **Given** Observer generates update with vague source
   **When** validated
   **Then** update is rejected (source must quote exact user text)

4. **Given** Observer validation implementation
   **When** unit tests run
   **Then** hallucination prevention tests pass

## Tasks / Subtasks

- [x] Task 1: Add `_validate_update()` method to ObserverAgent (AC: #1, #2, #3)
  - [x] 1.1: Add logger import at top of `observer.py`: `import logging` and `logger = logging.getLogger(__name__)`
  - [x] 1.2: Create method signature `def _validate_update(self, update: ContextUpdate, user_input: str) -> bool`
  - [x] 1.3: Implement `_extract_quoted_text()` helper to extract text between single quotes
  - [x] 1.4: Implement source field validation - must contain quoted text
  - [x] 1.5: Implement user input tracing - quoted text must appear in user_input (case-insensitive)
  - [x] 1.6: Return False with warning log if validation fails
  - [x] 1.7: Return True if validation passes

- [x] Task 2: Add `_validate_output()` method to filter ObserverOutput (AC: #1, #2)
  - [x] 2.1: Create method `def _validate_output(self, output: ObserverOutput, user_input: str) -> ObserverOutput`
  - [x] 2.2: Call `_validate_update()` for each update in output.updates
  - [x] 2.3: Filter out invalid updates, keeping only validated ones
  - [x] 2.4: If all updates filtered, set should_update=False
  - [x] 2.5: Log warning for each filtered update

- [x] Task 3: Add `_get_user_input()` helper method (AC: #1, #2, #3)
  - [x] 3.1: Create method `def _get_user_input(self, observer_input: ObserverInput) -> str`
  - [x] 3.2: Extract user input based on trigger type: query, correction, or raw_content from new_entry
  - [x] 3.3: Handle `new_entry` being `Any` type - check `isinstance(entry, dict)` before calling `.get()`

- [x] Task 4: Integrate validation into `observe()` method (AC: #1, #2, #3)
  - [x] 4.1: After line 333 (`assert isinstance(result, ObserverOutput)`), call `_get_user_input()`
  - [x] 4.2: Call `_validate_output(result, user_input)` to filter invalid updates
  - [x] 4.3: Return the validated output

- [x] Task 5: Add unit tests for validation (AC: #4)
  - [x] 5.1: Create `TestObserverValidation` class in `test_observer.py` (after `TestGlobalContextScopeRestriction`)
  - [x] 5.2: Use existing `create_mock_llm_client()` helper from line 45
  - [x] 5.3: `test_validate_update_accepts_correctly_sourced_fact()` - quoted text in user_input
  - [x] 5.4: `test_validate_update_rejects_missing_quote()` - source without quoted text
  - [x] 5.5: `test_validate_update_rejects_unmatched_quote()` - quoted text not in user_input
  - [x] 5.6: `test_validate_update_rejects_empty_user_input()` - empty user_input rejects all
  - [x] 5.7: `test_validate_output_filters_invalid_updates()` - invalid updates removed
  - [x] 5.8: `test_validate_output_sets_should_update_false_when_all_filtered()`
  - [x] 5.9: `test_observe_returns_validated_output()` - integration test with mock LLM

- [x] Task 6: Run validation (AC: #1-#4)
  - [x] 6.1: `make check` - 0 lint/type errors
  - [x] 6.2: `make validate` - all tests pass

## Dev Notes

### Problem Statement

**Hallucination Example (from iter-008-pre/dd9b77f4.json):**
```json
User Query: "Tell me about my last workout"

Observer Output:
{
  "should_update": true,
  "updates": [{
    "category": "fact",
    "key": "last_workout_2026-01-28",
    "value": "3 km run logged on 2026-01-28; user reported feeling sluggish, possibly due to cold weather.",
    "confidence": "certain",
    "source": "post_query: run log"
  }]
}
```

**Problems:**
1. User never mentioned "3 km run" - fabricated
2. User never mentioned "feeling sluggish" - fabricated
3. User never mentioned "cold weather" - fabricated
4. Source is vague "post_query: run log" - no actual quote

**Expected (after validation):**
```json
{
  "should_update": false,
  "updates": [],
  "insights_captured": []
}
```
Warning logged: "Filtered update 'last_workout_2026-01-28': source '3 km run' not found in user input"

### Validation Logic

**CRITICAL: Model is `ContextUpdate`, NOT `ObserverUpdate`**
```python
from quilto.agents.models import ContextUpdate  # NOT ObserverUpdate!
```

**Step 1: Add logging at top of observer.py (after existing imports)**
```python
import logging
import re

logger = logging.getLogger(__name__)
```

**Step 2: Extract quoted text from source field**
```python
def _extract_quoted_text(self, source: str) -> str | None:
    """Extract text between single quotes from source field.

    Args:
        source: The source field from ContextUpdate.

    Returns:
        The quoted text if found, None otherwise.
    """
    match = re.search(r"'([^']+)'", source)
    return match.group(1) if match else None
```

**Step 3: Validate individual update**
```python
def _validate_update(self, update: ContextUpdate, user_input: str) -> bool:
    """Validate that update source quotes text found in user input.

    Args:
        update: The ContextUpdate to validate.
        user_input: The original user input text.

    Returns:
        True if valid, False if hallucinated.
    """
    # Empty user_input means nothing can be validated
    if not user_input.strip():
        logger.warning(
            "Observer validation filtered update '%s': empty user input",
            update.key,
        )
        return False

    quoted = self._extract_quoted_text(update.source)
    if quoted is None:
        logger.warning(
            "Observer validation filtered update '%s': source has no quoted text",
            update.key,
        )
        return False

    if quoted.lower() not in user_input.lower():
        logger.warning(
            "Observer validation filtered update '%s': quoted text '%s' not in user input",
            update.key,
            quoted,
        )
        return False

    return True
```

**Step 4: Get user_input from ObserverInput**
```python
def _get_user_input(self, observer_input: ObserverInput) -> str:
    """Extract user input text based on trigger type.

    Args:
        observer_input: The ObserverInput to extract from.

    Returns:
        The user input text for validation.
    """
    if observer_input.trigger == "post_query":
        return observer_input.query or ""
    elif observer_input.trigger == "user_correction":
        return observer_input.correction or ""
    else:  # significant_log
        # new_entry is Any type - defensive check required
        entry = observer_input.new_entry
        if entry is None:
            return ""
        if isinstance(entry, dict):
            return str(entry.get("raw_content", ""))
        return str(entry)
```

**Step 5: Filter output updates**
```python
def _validate_output(self, output: ObserverOutput, user_input: str) -> ObserverOutput:
    """Filter out invalid updates from ObserverOutput.

    Args:
        output: The raw ObserverOutput from LLM.
        user_input: The original user input text.

    Returns:
        ObserverOutput with only validated updates.
    """
    valid_updates = [
        update for update in output.updates
        if self._validate_update(update, user_input)
    ]

    return ObserverOutput(
        should_update=len(valid_updates) > 0,
        updates=valid_updates,
        insights_captured=output.insights_captured if valid_updates else [],
    )
```

### Key Files

| File | Location | Change |
|------|----------|--------|
| `packages/quilto/quilto/agents/observer.py` | After line 11 | Add `import logging`, `import re`, and `logger = logging.getLogger(__name__)` |
| `packages/quilto/quilto/agents/observer.py` | After line 302 (before `observe()`) | Add `_extract_quoted_text()`, `_validate_update()`, `_validate_output()`, `_get_user_input()` methods |
| `packages/quilto/quilto/agents/observer.py` | In `observe()` after line 333 | Add validation call before return |
| `packages/quilto/tests/test_observer.py` | After `TestGlobalContextScopeRestriction` (line ~1357) | Add `TestObserverValidation` class with 8 tests |

### Architecture Compliance

| Check | Status |
|-------|--------|
| Changes in Quilto (not Swealog) | ✅ Yes |
| Domain-agnostic | ✅ Yes |
| Follows Story 22.1/22.2 pattern | ✅ Yes - builds on prompt-level fixes with runtime validation |
| Uses existing models | ✅ Yes - ObserverUpdate has source field |

### Design Decision: Prompt + Validation Defense-in-Depth

Stories 22.1 and 22.2 added prompt-level instructions. This story adds runtime validation as a second layer:

```
Layer 1 (Prompt): "source field MUST quote exact user text"
                   ↓
Layer 2 (Code):   _validate_update() verifies quote exists in input
```

This defense-in-depth approach catches LLM non-compliance.

### Test Patterns (from Story 22.1/22.2)

**IMPORTANT: Use existing `create_mock_llm_client()` from `test_observer.py` line 45**
**IMPORTANT: Model is `ContextUpdate`, NOT `ObserverUpdate`**

```python
# Use existing imports and helper from test_observer.py
from quilto.agents.models import ContextUpdate  # NOT ObserverUpdate!

# create_mock_llm_client already exists at line 45 - reuse it


class TestObserverValidation:
    """Tests for Observer output validation (Story 22.3)."""

    def test_validate_update_accepts_correctly_sourced_fact(self) -> None:
        """Update with quoted text found in user input passes validation."""
        client = create_mock_llm_client({"should_update": False})
        observer = ObserverAgent(client)

        update = ContextUpdate(
            category="preference",
            key="morning_workout",
            value="prefers morning workouts",
            confidence="certain",
            source="user said 'I prefer morning workouts'"
        )
        user_input = "I prefer morning workouts and running outdoors"

        result = observer._validate_update(update, user_input)
        assert result is True

    def test_validate_update_rejects_missing_quote(self) -> None:
        """Update with no quoted text in source fails validation."""
        client = create_mock_llm_client({"should_update": False})
        observer = ObserverAgent(client)

        update = ContextUpdate(
            category="fact",
            key="last_workout",
            value="3 km run",
            confidence="certain",
            source="post_query: run log"  # No quotes!
        )
        user_input = "Tell me about my last workout"

        result = observer._validate_update(update, user_input)
        assert result is False

    def test_validate_update_rejects_unmatched_quote(self) -> None:
        """Update with quoted text NOT in user input fails validation."""
        client = create_mock_llm_client({"should_update": False})
        observer = ObserverAgent(client)

        update = ContextUpdate(
            category="fact",
            key="sluggish_feeling",
            value="user felt sluggish",
            confidence="certain",
            source="user said '3 km run feeling sluggish'"  # Fabricated!
        )
        user_input = "Tell me about my last workout"

        result = observer._validate_update(update, user_input)
        assert result is False

    def test_validate_update_rejects_empty_user_input(self) -> None:
        """Update with empty user input always fails validation."""
        client = create_mock_llm_client({"should_update": False})
        observer = ObserverAgent(client)

        update = ContextUpdate(
            category="preference",
            key="morning_workout",
            value="prefers morning workouts",
            confidence="certain",
            source="user said 'I prefer morning workouts'"
        )
        user_input = ""  # Empty!

        result = observer._validate_update(update, user_input)
        assert result is False
```

### Edge Cases to Handle

| Edge Case | Handling | Code |
|-----------|----------|------|
| Empty user_input | Return False for all updates | `if not user_input.strip(): return False` |
| Case mismatch | Case-insensitive comparison | `quoted.lower() not in user_input.lower()` |
| Partial match | Require quoted text to appear verbatim | substring match is sufficient |
| Multiple quotes | Use first quoted match | `re.search()` returns first match |
| Escaped quotes | Not expected in LLM output | ignore - regex won't match |
| `new_entry` not a dict | Convert to string | `isinstance(entry, dict)` check |

### Logging Requirements

Use standard Python logging at WARNING level for filtered updates:
```python
import logging
logger = logging.getLogger(__name__)

# In _validate_update():
logger.warning(
    "Observer validation filtered update '%s': %s",
    update.key,
    reason
)
```

### Anti-Patterns to Avoid

| Anti-Pattern | Correct Approach |
|--------------|------------------|
| Raise exception on invalid | Filter silently with warning log |
| Validate only fact category | Validate ALL categories |
| Strict exact match | Case-insensitive substring match |
| Skip validation for corrections | Validate all triggers equally |

### Integration into `observe()` Method

After line 333 in `observe()`, add:
```python
        # Validate output to filter hallucinated facts
        user_input = self._get_user_input(observer_input)
        validated_result = self._validate_output(result, user_input)

        return validated_result
```

Replace the current `return result` (line 335) with the above.

### Import Updates Required

At top of `observer.py`, after line 11 (`from quilto.llm import LLMClient`):
```python
import logging
import re

logger = logging.getLogger(__name__)
```

Also update the model imports (line 7-10):
```python
from quilto.agents.models import (
    ContextUpdate,  # ADD THIS
    ObserverInput,
    ObserverOutput,
)
```

### References

- `tests/eval/feedback/archive/iter-008-pre/2026-01-29_dd9b77f4.json` - Hallucination example
- `_bmad-output/implementation-artifacts/epic-22/22-1-observer-only-persists-user-stated-info.md` - SOURCE FIELD REQUIREMENTS
- `_bmad-output/implementation-artifacts/epic-22/22-2-restrict-global-context-scope.md` - GLOBAL CONTEXT SCOPE
- `packages/quilto/quilto/agents/observer.py:276-286` - Current source field requirements in prompt
- `packages/quilto/tests/test_observer.py:45-63` - `create_mock_llm_client()` helper (REUSE)
- `packages/quilto/tests/test_observer.py:1172-1357` - TestGlobalContextScopeRestriction pattern
- `packages/quilto/quilto/agents/models.py:937-971` - `ContextUpdate` model definition (NOT ObserverUpdate)

### Project Structure Notes

- All changes in `packages/quilto/` (framework, not application)
- Tests follow existing `test_observer.py` patterns
- Uses `ObserverUpdate` model from `quilto/agents/models.py`

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

None

### Completion Notes List

- Added `import logging`, `import re`, and `logger = logging.getLogger(__name__)` to observer.py
- Added `ContextUpdate` to imports from `quilto.agents.models`
- Implemented `_extract_quoted_text()` helper method using regex to extract text between single quotes
- Implemented `_validate_update()` method that validates source field has quoted text matching user input (case-insensitive)
- Implemented `_get_user_input()` helper method to extract user input based on trigger type (post_query→query, user_correction→correction, significant_log→raw_content from new_entry)
- Implemented `_validate_output()` method to filter out invalid updates and set should_update=False when all filtered
- Integrated validation into `observe()` method after LLM response, before return
- Added 17 new tests in `TestObserverValidation` class covering all validation scenarios
- Fixed existing `test_observe_returns_observer_output` to use properly quoted source field
- All tests pass (2238 passed, 112 skipped)
- **Design decision:** For `significant_log` trigger, `_get_user_input()` returns `raw_content` from dict entries or stringified non-dict entries. If no `raw_content` exists, validation rejects all updates. This is intentional - without explicit user text to validate against, we cannot verify the source quotes are accurate.
- **Code review (2026-01-30):** Added `test_validate_update_logs_warning_on_rejection()` to verify logging behavior per AC #1

### File List

- `packages/quilto/quilto/agents/observer.py` - Added validation methods and integrated into observe()
- `packages/quilto/tests/test_observer.py` - Added TestObserverValidation class with 18 tests (17 original + 1 logging test), fixed existing test
