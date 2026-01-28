# Story 17.10: Add Logging to Broad Exception Handlers

Status: done

## Story

As a **Quilto framework developer**,
I want broad exception handlers to log what they catch,
so that unexpected errors are visible during development.

## Acceptance Criteria

1. **Given** `llm/client.py` line 315 (JSON extraction fallback)
   **When** an exception is caught during `model_validate_json(extracted)`
   **Then** `logger.debug("Fallback JSON parse failed for agent '%s': %s", agent, e)` logs the error before falling through

## Tasks / Subtasks

- [x] Task 1: Add logging to `complete_structured` fallback (AC: #1)
  - [x] Subtask 1.1: Change `except Exception:` to `except Exception as e:` at line 315
  - [x] Subtask 1.2: Replace `pass` with `logger.debug("Fallback JSON parse failed for agent '%s': %s", agent, e)`
  - [x] Subtask 1.3: Keep the `# Fall through to original error` comment after the log statement

- [x] Task 2: Run `make check` during development, `make validate` before commit

## Dev Notes

### Context

Issue 10 from Story 17.1 investigation identified `except Exception: pass` that silently swallows errors. Location: `llm/client.py:315`. This is a fallback JSON extraction attempt - if both direct parse and extracted parse fail, the original error is raised with logging at lines 318-323. The `pass` is intentional "fall through" behavior. Adding `logger.debug` makes the fallback attempt visible in debug mode.

### Why Debug Level (Not Warning)

The fallback failing is **expected behavior** when JSON is truly malformed. The original error already logs at `logger.error` level (lines 318-323) with full context. Debug level avoids cluttering normal logs while making the fallback visible when debugging.

### Code Location

```python
# packages/quilto/quilto/llm/client.py:313-316 (CURRENT)
try:
    return response_model.model_validate_json(extracted)
except Exception:
    pass  # Fall through to original error
```

### Expected Change

```python
# packages/quilto/quilto/llm/client.py:313-316 (AFTER)
try:
    return response_model.model_validate_json(extracted)
except Exception as e:
    logger.debug("Fallback JSON parse failed for agent '%s': %s", agent, e)
    # Fall through to original error
```

### Existing Logger Pattern (lines 318-323)

Follow the existing error logging pattern immediately after:
```python
logger.error(
    "Failed to parse structured response for agent '%s'. Expected schema: %s. Raw response: %s",
    agent,
    response_model.__name__,
    response[:500] if len(response) > 500 else response,
)
```

### In-Scope Variable Confirmation

- `agent` - String parameter passed to `complete_structured()` (line 275)
- `logger` - Module-level logger at line 28: `logger = logging.getLogger(__name__)`
- `e` - Exception captured by `except Exception as e:`

### Out of Scope

- `llm/client.py:386-410` (`_retry_with_backoff`) - Already has logging at lines 399-405
- `cli/app.py:55` (Swealog version check) - Not Quilto framework code

### Test Strategy

Observability improvement - no new tests required.

```bash
make check      # During development
make validate   # Before commit
```

### Project Structure

- **Package:** Quilto (`packages/quilto/`)
- **File:** `quilto/llm/client.py`

### Previous Story Context

Story 17.9 modified `llm/client.py` (added TypeVar pattern). Logger is already imported and used throughout the file.

### Architecture Compliance

- Non-breaking: Adding debug logging doesn't change runtime behavior
- Pattern-compliant: Uses existing `logger.debug/warning/error` pattern

### References

- Story 17.1: Investigation Issue 10 (Broad Exception Handling)
- `llm/client.py:318-323`: Existing error logging pattern

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

N/A - Observability improvement, no new tests required per story spec.

### Completion Notes List

- Changed `except Exception:` to `except Exception as e:` at line 315
- Added `logger.debug("Fallback JSON parse failed for agent '%s': %s", agent, e)` before fall-through comment
- Preserved `# Fall through to original error` comment after the debug log
- `make check` passed (lint + typecheck: 0 errors)
- `make validate` passed (2064 tests passed, 101 skipped)

### File List

- `packages/quilto/quilto/llm/client.py` - Added debug logging to fallback exception handler
