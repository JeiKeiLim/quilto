# Story 12.3: Add LLM Timeout and Retry Configuration

Status: done

## Story

As a **Quilto developer**,
I want **configurable LLM timeout with smart retry behavior for malformed JSON**,
So that **the system doesn't hang and handles intermittent failures gracefully**.

## Background

**Origin:** Dogfooding Iteration 1 Analysis (2026-01-24)
**Source:** `tests/eval/feedback/archive/iter-001/analysis.md`
**Priority:** Medium | **Effort:** Small (1-2 hours)

**Problems Identified:**

1. **LLM Timeout Too Long (Pattern 3):**
   - litellm's default timeout is 600 seconds (10 minutes)
   - When OpenRouter hangs, users wait excessively before retry/fallback triggers
   - No explicit timeout configuration in `LLMConfig`
   - Decision: Set 45-second default timeout as balance between quick response and allowing complex reasoning

2. **Malformed JSON Crashes Application (Pattern 4):**
   - OpenRouter free-tier models produce intermittent malformed JSON
   - Currently `JSONDecodeError` and `ValidationError` are treated as PERMANENT errors in `classify_error()`
   - This means NO retry on same provider - immediate fallback
   - If fallback also fails, application crashes
   - The malformed JSON is often TRANSIENT (same query works on retry)

**Evidence from Iteration 1:**
- Record `f89c6142`: Planner output contained `"2026-?..."` malformed date
- Record `e16dbc36_190829`: Router output contained `["The.", "I", "", "...", ".....", "...", "I"]`

**Impact:** Non-deterministic failures degrade user trust. Long waits frustrate users.

## Acceptance Criteria

1. **Given** `LLMConfig`
   **When** timeout is not specified
   **Then** default is 45 seconds (not litellm's 600s default)

2. **Given** `LLMConfig` with explicit timeout value
   **When** creating LLMClient
   **Then** that timeout is used for all LLM calls

3. **Given** LLM returns malformed JSON (JSONDecodeError, ValidationError)
   **When** `schema_retry_count < max_schema_retries` (default: 2)
   **Then** retry same provider (treat as TRANSIENT, not PERMANENT)

4. **Given** malformed JSON after max_schema_retries exhausted
   **When** fallback provider is configured
   **Then** try fallback provider before degradation

5. **Given** existing `max_retries` config (for TRANSIENT errors like timeout, rate limit)
   **When** schema errors occur
   **Then** `max_schema_retries` is separate from `max_retries` (schema errors are special case)

6. **Given** backward compatibility requirement
   **When** no new config fields are set
   **Then** system uses reasonable defaults (timeout=45s, max_schema_retries=2)

## Tasks / Subtasks

- [x] Task 1: Add `timeout` field to `LLMConfig` in `packages/quilto/quilto/llm/config.py` (AC: #1, #2, #6)
  - [x] 1.1: Add `timeout: float = 45.0` field with docstring
  - [x] 1.2: Add validator to ensure timeout > 0
  - [x] 1.3: Update class docstring to document new field

- [x] Task 2: Add `max_schema_retries` field to `LLMConfig` (AC: #3, #5, #6)
  - [x] 2.1: Add `max_schema_retries: int = 2` field with docstring
  - [x] 2.2: Add validator to ensure max_schema_retries >= 0
  - [x] 2.3: Explain separation from `max_retries` in docstring

- [x] Task 3: Pass `timeout` to litellm calls in `client.py` (AC: #1, #2)
  - [x] 3.1: In `complete()`, add `timeout` parameter to `completion_kwargs`
  - [x] 3.2: Get timeout from `self.config.timeout`
  - [x] 3.3: Verify timeout is passed through `complete_structured()` via kwargs

- [x] Task 4: Update `_retry_structured_with_backoff()` to retry schema errors (AC: #3, #4)
  - [x] 4.1: Track schema retry attempts separately from connection retries
  - [x] 4.2: On JSONDecodeError or ValidationError, check against `max_schema_retries`
  - [x] 4.3: If within limit, retry same provider (don't immediately fallback)
  - [x] 4.4: If exceeds limit, THEN trigger fallback (existing behavior)
  - [x] 4.5: Log schema retry attempts distinctly from connection retries

- [x] Task 5: Schema Error Handling (AC: #3) - **Use Option B per Dev Notes**
  - [x] 5.1: Keep JSONDecodeError and ValidationError as PERMANENT in `classify_error()` (no change needed)
  - [x] 5.2: Handle schema errors explicitly in `_retry_structured_with_backoff()` BEFORE calling `classify_error()`
  - [x] 5.3: Add comment in `errors.py` explaining schema errors are handled specially in client.py

- [x] Task 6: Add unit tests for new config fields (AC: #1, #2, #6)
  - [x] 6.1: Test default timeout is 45.0 when not specified
  - [x] 6.2: Test custom timeout is used when specified
  - [x] 6.3: Test default max_schema_retries is 2
  - [x] 6.4: Test validator rejects timeout <= 0 (boundary: 0.0, -1.0)
  - [x] 6.5: Test validator rejects max_schema_retries < 0 (boundary: -1)
  - [x] 6.6: Test validator accepts max_schema_retries = 0 (disables schema retries)

- [x] Task 7: Add unit tests for timeout propagation (AC: #1, #2)
  - [x] 7.1: Test `complete()` passes timeout to litellm.acompletion
  - [x] 7.2: Test `complete_structured()` passes timeout through

- [x] Task 8: Add unit tests for schema retry behavior (AC: #3, #4, #5)
  - [x] 8.1: Test JSONDecodeError triggers retry (up to max_schema_retries)
  - [x] 8.2: Test ValidationError triggers retry (up to max_schema_retries)
  - [x] 8.3: Test after max_schema_retries, fallback is tried
  - [x] 8.4: Test schema retries are separate from connection retries
  - [x] 8.5: Test logging shows schema retry attempts

- [x] Task 9: Integration test verification with real Ollama (AC: #1, #3)
  - [x] 9.1: Verify timeout parameter is passed in LLM calls (check logs or use short timeout)
  - [x] 9.2: Verify existing integration tests still pass with new config defaults
  - [x] 9.3: Run `make test-ollama` to confirm no regressions
  - [x] 9.4: Note: Actual timeout enforcement is tested by litellm, not our code

- [x] Task 10: Run validation
  - [x] 10.1: Run `make check` (lint + typecheck)
  - [x] 10.2: Run `make validate` (full validation including unit tests)
  - [x] 10.3: Run `make test-ollama` (integration tests with real Ollama)

## Dev Notes

### Current Error Classification (errors.py:61-118)

```python
def classify_error(exception: Exception) -> ErrorType:
    # Schema/parsing errors are permanent - no point retrying
    if isinstance(exception, (json.JSONDecodeError, ValidationError)):
        return ErrorType.PERMANENT  # <-- CHANGE THIS BEHAVIOR
```

**Problem:** Schema errors ARE worth retrying because LLM responses are non-deterministic. Same prompt can produce valid JSON on second attempt.

### Design Decision: SCHEMA_ERROR vs Special Handling

**Option A: Add SCHEMA_ERROR enum value**
- Cleaner classification
- Requires updating all callers of `classify_error()`
- More explicit

**Option B: Keep PERMANENT but handle in retry methods**
- Less invasive change
- Schema retry logic stays in `_retry_structured_with_backoff()`
- Track schema retries separately from classify_error()

**Recommendation:** Option B - Keep changes localized to `_retry_structured_with_backoff()`. Check for schema errors explicitly before calling `classify_error()`, and maintain separate retry counter.

### Implementation Pattern (Suggested)

```python
# In _retry_structured_with_backoff()
schema_retries = 0
for attempt in range(self.config.max_retries):
    try:
        result = await self.complete_structured(...)
        return result, None, attempt + 1
    except (json.JSONDecodeError, ValidationError) as e:
        # Schema errors: retry up to max_schema_retries
        schema_retries += 1
        if schema_retries >= self.config.max_schema_retries:
            return None, e, attempt + 1  # Exhaust schema retries, try fallback
        logger.warning(
            "Schema error (attempt %d/%d): %s",
            schema_retries, self.config.max_schema_retries, str(e)
        )
        # Apply backoff before schema retry
        delay = self.config.base_retry_delay * (2 ** schema_retries)
        await asyncio.sleep(delay)
        continue  # Stay on same attempt count, retry same provider
    except Exception as e:
        # Other errors: use existing classify_error() logic
        ...
```

### Timeout Implementation (litellm)

litellm supports timeout via the `timeout` parameter:

```python
response = await litellm.acompletion(
    model=resolution.litellm_model,
    messages=messages,
    timeout=self.config.timeout,  # Add this
    **kwargs,
)
```

### Key Files

| File | Purpose | Lines to Modify |
|------|---------|-----------------|
| `packages/quilto/quilto/llm/config.py` | Add timeout and max_schema_retries fields | 173-266 (LLMConfig class) |
| `packages/quilto/quilto/llm/client.py` | Pass timeout, update schema retry logic | 217-253 (complete), 576-633 (_retry_structured_with_backoff) |
| `packages/quilto/quilto/llm/errors.py` | Add comment explaining schema error handling | 73-75 (no code changes, just comment) |
| `packages/quilto/tests/test_llm_client.py` | Add tests for timeout and schema retries | New test classes: `TestTimeoutConfig`, `TestSchemaRetry` |
| `packages/quilto/tests/test_llm_config.py` | Add tests for new config fields | Add to `TestLLMConfig` class |

### Config Examples

```yaml
# llm-config.yaml
default_provider: "ollama"
timeout: 45  # seconds (default is 45 if not specified)
max_retries: 3  # for transient errors (timeout, rate limit)
max_schema_retries: 2  # for malformed JSON (default is 2 if not specified)
```

### Previous Story Learnings

**From Story 11.1 (JSON Schema Structured Output):**
- Schema errors are common with OpenRouter models
- `_extract_json()` fallback already exists but doesn't prevent all failures
- Schema errors should be retried (handled separately from TRANSIENT vs PERMANENT classification)

**From Story 12.1 & 12.2:**
- Follow existing test patterns in `test_routing.py` and `test_planner.py`
- Add tests to existing test files when appropriate
- Use `make test-ollama` for integration validation

### Testing Checklist

- [ ] Test default timeout (45s) when not in config
- [ ] Test custom timeout is passed to litellm
- [ ] Test timeout <= 0 raises ValidationError (boundary: 0.0, -1.0)
- [ ] Test default max_schema_retries (2) when not in config
- [ ] Test max_schema_retries < 0 raises ValidationError (boundary: -1)
- [ ] Test max_schema_retries = 0 disables schema retries (boundary: 0)
- [ ] Test JSONDecodeError triggers schema retry (up to max_schema_retries)
- [ ] Test ValidationError triggers schema retry (up to max_schema_retries)
- [ ] Test max_schema_retries exhausted → fallback
- [ ] Test schema retries separate from connection retries
- [ ] Test logging shows "Schema retry" vs "Connection retry" distinctly
- [ ] Run `make validate` before marking done
- [ ] Run `make test-ollama` before marking done

### References

| Source | Content |
|--------|---------|
| `tests/eval/feedback/archive/iter-001/analysis.md` | Pattern 3: LLM Timeout Too Long, Pattern 4: Malformed JSON Crashes |
| `packages/quilto/quilto/llm/config.py` | Current LLMConfig definition |
| `packages/quilto/quilto/llm/client.py:576-633` | Current _retry_structured_with_backoff() |
| `packages/quilto/quilto/llm/errors.py:61-118` | Current classify_error() |
| `_bmad-output/implementation-artifacts/epic-11/11-1-implement-json-schema-structured-output.md` | Related story on JSON handling |

### Anti-Patterns to Avoid

| Mistake | Correct |
|---------|---------|
| Using same counter for schema and connection retries | Separate counters: `max_retries` vs `max_schema_retries` |
| Not logging retry type distinctly | Log "Schema retry" vs "Connection retry" |
| Breaking existing max_retries behavior | Schema retry is additional, not replacement |
| Forgetting to pass timeout to all litellm calls | Check both `complete()` and `complete_with_cascade()` paths |
| Negative timeout or retry values | Add validators to reject invalid values |

### Commit Message Template

```
Add LLM timeout and schema retry configuration

Story 12.3: Adds two new LLMConfig fields:
- timeout (default 45s) - prevents excessive waits on slow LLM providers
- max_schema_retries (default 2) - retries malformed JSON before fallback

Malformed JSON (JSONDecodeError, ValidationError) is now retried on same
provider before triggering fallback, since LLM responses are non-deterministic.

Evidence: Records f89c6142, e16dbc36_190829 had malformed JSON from OpenRouter.
```

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

N/A

### Completion Notes List

1. **Implementation Decision:** Used Option B as recommended - kept schema errors as PERMANENT in `classify_error()` but handled them specially in `_retry_structured_with_backoff()`. This keeps the change localized and maintains backward compatibility.

2. **Schema Retry Logic:** Changed from `for` loop to `while` loop in `_retry_structured_with_backoff()` to properly handle schema retries independently from connection retries. The schema retry counter doesn't increment the main `attempt` counter, allowing independent retry budgets for each error type.

3. **Test Updates:** Updated `test_schema_error_skips_retry` test in `test_error_cascade.py` to reflect new behavior - schema errors now DO retry (renamed to `test_schema_error_retries_then_degrades`).

4. **Integration Test Results:** `make test-ollama` shows 18 pre-existing failures unrelated to this story (Planner, Evaluator, Analyzer issues). All LLM client and config tests pass. No timeout or schema_retries related errors in integration tests.

5. **Validation Results:**
   - `make check`: PASS (lint + typecheck)
   - `make validate`: PASS (1899 passed, 100 skipped)
   - `make test-ollama`: 18 pre-existing failures unrelated to this story

6. **Code Review Fixes (2026-01-24):**
   - Fixed confusing docstring for `max_schema_retries` - clarified that with `max_schema_retries=2`, there are 2 total attempts (1 initial + 1 retry)
   - Fixed incorrect math in test comment (`test_error_cascade.py:684`)
   - Added `TestSchemaRetryLogging` test class to verify schema retry log messages (Task 8.5)
   - Reverted unrelated change to `scripts/story-pipeline.sh`

### File List

| File | Changes |
|------|---------|
| `packages/quilto/quilto/llm/config.py` | Added `timeout: float = 45.0` and `max_schema_retries: int = 2` fields with validators, updated docstring (code review: clarified docstring) |
| `packages/quilto/quilto/llm/client.py` | Pass timeout to litellm calls, added `_is_schema_error()` method, rewrote `_retry_structured_with_backoff()` with while loop (code review: improved docstring clarity) |
| `packages/quilto/quilto/llm/errors.py` | Added comment explaining schema errors are handled specially in client.py |
| `packages/quilto/tests/test_llm_config.py` | Added 8 tests for timeout and max_schema_retries config fields |
| `packages/quilto/tests/test_llm_client.py` | Added tests for timeout propagation, added `TestSchemaRetryBehavior`, `TestIsSchemaError`, and `TestSchemaRetryLogging` test classes |
| `packages/quilto/tests/test_error_cascade.py` | Updated `test_schema_error_skips_retry` to `test_schema_error_retries_then_degrades` (code review: fixed comment)

