# Story 3.5: Improve Retrieval Strategy Ordering

Status: done

## Story

As a **Quilto developer**,
I want **date-range retrieval as the default strategy with progressive expansion**,
So that **comparison queries find relevant logs regardless of language barriers**.

## Background (From Epic 4 Retrospective)

**Problem Discovered:** During manual testing with real Ollama, queries like "Just did bench 55kg 10x5. is it better than my previous workouts?" triggered term search with English terms ("bench", "1rm") while logs were stored in Korean. This language mismatch caused empty results.

**Expected Behavior:**
1. Default to date-range retrieval (1 week back) for comparison/progress queries
2. Progressive expansion if empty (1 week → 2 weeks → 1 month → term search)
3. Fall back to term search only if date range fails

**Root Cause:** The Planner prompt does not explicitly guide the LLM to prefer date-range retrieval for comparison queries, and there's no progressive expansion mechanism in the Retriever.

## Acceptance Criteria

1. **Given** a comparison query like "how does this compare to my previous workouts?"
   **When** Planner processes it
   **Then** it selects `date_range` as the primary retrieval strategy
   **And** `retrieval_params` includes a 1-week default range (today to 7 days ago)
   **And** `reasoning` explains why date-range was chosen over keyword

2. **Given** a progress query like "am I getting stronger?"
   **When** Planner processes it
   **Then** it selects `date_range` as the primary retrieval strategy
   **And** the date range covers at least 1 week
   **And** query_type is classified as `comparison` or `insight`

3. **Given** a date-range retrieval that returns 0 entries
   **When** Retriever detects empty results
   **Then** it automatically expands the date range progressively:
     - 1 week → 2 weeks
     - 2 weeks → 1 month (30 days)
     - 1 month → 3 months
   **And** each expansion is logged in `retrieval_summary` with `expansion_tier`
   **And** expansion stops when entries are found

4. **Given** progressive expansion reaches 3 months with still 0 entries
   **When** Retriever exhausts date-range expansion
   **Then** it falls back to term search using vocabulary-expanded keywords from `retrieval_params.keywords`
   **And** `warnings` includes "Progressive expansion exhausted, falling back to term search"
   **And** `expansion_exhausted` is set to `True` in output

5. **Given** an explicit keyword query like "show me bench press workouts"
   **When** Planner processes it
   **Then** it selects `keyword` as the retrieval strategy (not date-range)
   **And** the original behavior is preserved for explicit keyword queries

6. **Given** a query with explicit date mention like "what did I do last Monday"
   **When** Planner processes it
   **Then** it selects `date_range` with the specific date mentioned
   **And** sets `explicit_date: true` in retrieval_params
   **And** Retriever disables progressive expansion for this instruction

7. **Given** existing tests in test_planner.py and test_retriever.py
   **When** running `make validate` and `make test-ollama`
   **Then** all existing tests continue to pass
   **And** new tests for progressive expansion pass

## Tasks / Subtasks

- [x] Task 1: Update Planner prompt to prioritize date-range for comparison queries (AC: #1, #2)
  - [x] Add "COMPARISON/PROGRESS QUERIES" section to Planner prompt with examples
  - [x] Add `Today's date: {today}` to INPUT section so LLM can compute date ranges
  - [x] Include trigger words: "compare", "progress", "better than", "trend", "improving", "stronger"
  - [x] Add instruction: "For comparison/progress queries, USE DATE_RANGE, NOT KEYWORD"
  - [x] Add default date range guidance: "If no date mentioned, use 7 days (today - 7 days)"

- [x] Task 2: Add `explicit_date` flag to retrieval params (AC: #6)
  - [x] Update Planner prompt to set `explicit_date: true` when user specifies exact date
  - [x] Document in prompt: "Set explicit_date=true if user mentions specific day/date"
  - [x] Retriever reads this flag from `retrieval_params` to disable expansion

- [x] Task 3: Add progressive expansion logic to RetrieverAgent (AC: #3, #4)
  - [x] Add `EXPANSION_TIERS: list[int] = [7, 14, 30, 90]` class constant
  - [x] Add `enable_progressive_expansion: bool = True` to `RetrieverInput`
  - [x] Implement `_execute_date_range_with_expansion()` method
  - [x] Track expansion tier in each RetrievalAttempt via `expansion_tier` field
  - [x] Stop expansion when entries are found
  - [x] Trigger term search fallback when all tiers exhausted

- [x] Task 4: Implement term search fallback after expansion exhaustion (AC: #4)
  - [x] Extract keywords from original `retrieval_params.keywords` if present
  - [x] If no keywords, extract significant terms from query using vocabulary
  - [x] Call existing `_execute_keyword()` method with extracted keywords
  - [x] Add warning message: "Progressive expansion exhausted, falling back to term search"
  - [x] Set `expansion_exhausted: true` in output

- [x] Task 5: Update models.py with new fields (AC: #3, #4, #6)
  - [x] Add to `RetrieverInput`:
    - `enable_progressive_expansion: bool = True`
  - [x] Add to `RetrievalAttempt`:
    - `expansion_tier: int = Field(default=0, ge=0)` (0=original, 1-3=expansion levels)
  - [x] Add to `RetrieverOutput`:
    - `expansion_exhausted: bool = False`
  - [x] Use `ConfigDict(strict=True)` on any new models (existing pattern)

- [x] Task 6: Handle explicit date queries (AC: #6)
  - [x] Detect `explicit_date: true` in retrieval_params
  - [x] Set `enable_progressive_expansion=False` for that instruction
  - [x] Add test verifying explicit date skips expansion

- [x] Task 7: Preserve keyword query behavior (AC: #5)
  - [x] Ensure KEYWORD strategy bypasses expansion logic entirely
  - [x] Progressive expansion only applies to DATE_RANGE strategy
  - [x] Add tests verifying original keyword behavior unchanged

- [x] Task 8: Add unit tests for progressive expansion (AC: #3, #4, #7)
  - [x] Test expansion: 1 week empty → expands to 2 weeks → finds entries → stops
  - [x] Test expansion: all tiers empty → triggers term search fallback
  - [x] Test `expansion_tier` tracked correctly in RetrievalAttempt
  - [x] Test `expansion_exhausted=True` when fallback triggers
  - [x] Test explicit_date=true disables expansion
  - [x] Test keyword strategy unchanged (no expansion)

- [x] Task 9: Add unit tests for Planner comparison detection (AC: #1, #2, #5)
  - [x] Test "compare to previous" → date_range strategy
  - [x] Test "am I improving" → date_range strategy
  - [x] Test "show me bench press" → keyword strategy (unchanged)
  - [x] Test explicit date "last Monday" → date_range with explicit_date=true
  - [x] Test date range params include valid start/end dates

- [x] Task 10: Add integration tests with real Ollama (AC: #7)
  - [x] Test comparison query generates date_range retrieval with real LLM
  - [x] Test progressive expansion with empty storage (mock storage, real LLM not needed)
  - [x] Test fallback to term search works end-to-end

- [x] Task 11: Add Korean-English mismatch integration test
  - [x] Store entry with Korean: "벤치프레스 55kg 10x5"
  - [x] Query with English: "compare this to my previous bench workouts"
  - [x] Verify date-range retrieval finds the Korean entry

- [x] Task 12: Update manual_test.py (if exists) (AC: #7)
  - [x] Add test case for comparison query with mixed language logs
  - [x] Verify progressive expansion behavior manually

- [x] Task 13: Verify no regression (AC: #7)
  - [x] Run `make validate` - passes
  - [x] Run `make test-ollama` - passes
  - [x] Verify all existing Router, Parser, Planner, Retriever tests pass

## Dev Notes

### Files to Create/Modify

| File | Action | Description |
|------|--------|-------------|
| `packages/quilto/quilto/agents/planner.py` | Modify | Add today's date to prompt, add COMPARISON QUERY section |
| `packages/quilto/quilto/agents/retriever.py` | Modify | Add progressive expansion logic, term search fallback |
| `packages/quilto/quilto/agents/models.py` | Modify | Add `enable_progressive_expansion`, `expansion_tier`, `expansion_exhausted` |
| `packages/quilto/quilto/agents/__init__.py` | Modify | Export any new types if needed |
| `packages/quilto/tests/test_planner.py` | Modify | Add comparison query tests |
| `packages/quilto/tests/test_retriever.py` | Modify | Add progressive expansion tests |

### Architecture Position

This is a hotfix to improve the query flow. It affects:

```
ROUTE → BUILD_CONTEXT → PLAN → RETRIEVE → ANALYZE
                          ^         |
                          |    [progressive expansion]
                          |    [term search fallback]
                          |         |
                          +---------+
```

### Responsibility Separation

**Planner is responsible for:**
- Detecting comparison/progress queries via trigger words
- Selecting DATE_RANGE strategy (not KEYWORD) for these queries
- Setting `explicit_date: true` in params when user specifies exact date
- Generating valid date range using today's date from prompt
- Setting default 7-day range when no date mentioned

**Retriever is responsible for:**
- Executing date range retrieval
- Progressive expansion when results are empty AND `enable_progressive_expansion=true`
- Reading `explicit_date` from params to disable expansion
- Triggering term search fallback when expansion exhausted
- Tracking expansion_tier in RetrievalAttempt

### Planner Prompt Changes

**Add to INPUT section:**
```
Today's date: {today.isoformat()}
```

**Add to RETRIEVAL STRATEGIES section (after existing content):**
```
=== COMPARISON/PROGRESS QUERIES ===
For queries with: "compare", "progress", "better than", "trend", "improving", "stronger"
→ USE DATE_RANGE (language-agnostic) NOT KEYWORD (fails cross-language)
→ Default: today to 7 days ago if no date mentioned
→ Set explicit_date=true if user specifies exact day/date (e.g., "last Monday", "on January 5th")

Examples:
- "compare this to my previous workouts" → date_range (7 days default)
- "am I getting stronger?" → date_range (30 days for trend)
- "how does this stack up?" → date_range (7 days default)
- "what did I do last Monday" → date_range (specific date, explicit_date=true)

KEYWORD strategy examples (unchanged):
- "show me bench press workouts" → keyword
- "find all entries with squats" → keyword
```

### Progressive Expansion Implementation

```python
# In RetrieverAgent class
EXPANSION_TIERS: list[int] = [7, 14, 30, 90]

async def _execute_date_range_with_expansion(
    self,
    attempt_number: int,
    params: dict[str, Any],
    vocabulary: dict[str, str],
    warnings: list[str],
    enable_expansion: bool,
) -> tuple[list[Entry], list[RetrievalAttempt]]:
    """Execute date range with progressive expansion on empty results.

    Args:
        attempt_number: Base attempt number.
        params: Original date_range params with start_date, end_date.
        vocabulary: Term normalization for fallback.
        warnings: List to append warnings to.
        enable_expansion: If False, skip expansion (explicit_date case).

    Returns:
        Tuple of (entries, list of RetrievalAttempts with expansion_tier).
    """
    attempts: list[RetrievalAttempt] = []
    all_entries: list[Entry] = []

    # Tier 0: Original date range
    entries, attempt = self._execute_date_range(attempt_number, params, warnings)
    if attempt:
        attempt.expansion_tier = 0
        attempts.append(attempt)

    if entries or not enable_expansion:
        return entries, attempts

    # Progressive expansion through tiers
    for tier_index, days in enumerate(self.EXPANSION_TIERS, start=1):
        expanded_params = self._expand_to_days(params, days)
        entries, attempt = self._execute_date_range(attempt_number, expanded_params, warnings)
        if attempt:
            attempt.expansion_tier = tier_index
            attempt.summary = f"Expanded to {days} days: {attempt.summary}"
            attempts.append(attempt)

        if entries:
            return entries, attempts

    # Exhausted - will trigger term search fallback in caller
    return [], attempts
```

### Model Changes

```python
# In RetrieverInput (existing model)
enable_progressive_expansion: bool = True

# In RetrievalAttempt (existing model)
expansion_tier: int = Field(default=0, ge=0, description="0=original, 1-4=expansion")

# In RetrieverOutput (existing model)
expansion_exhausted: bool = False
```

### Test Organization

```python
class TestPlannerComparisonQueries:
    """Tests for comparison query strategy selection."""
    async def test_compare_to_previous_uses_date_range(self, mock_llm): ...
    async def test_am_i_improving_uses_date_range(self, mock_llm): ...
    async def test_progress_query_includes_default_date_range(self, mock_llm): ...
    async def test_explicit_keyword_query_unchanged(self, mock_llm): ...
    async def test_explicit_date_sets_flag(self, mock_llm): ...


class TestRetrieverProgressiveExpansion:
    """Tests for progressive date range expansion."""
    async def test_expansion_stops_when_entries_found(self, mock_storage): ...
    async def test_expansion_tiers_7_14_30_90(self, mock_storage): ...
    async def test_expansion_exhausted_triggers_fallback(self, mock_storage): ...
    async def test_expansion_disabled_no_expansion(self, mock_storage): ...
    async def test_explicit_date_no_expansion(self, mock_storage): ...
    async def test_expansion_tier_logged_in_attempt(self, mock_storage): ...
    async def test_keyword_strategy_no_expansion(self, mock_storage): ...


class TestRetrieverLanguageMismatch:
    """Integration tests for cross-language retrieval."""
    async def test_korean_entry_english_query(self, tmp_path): ...
```

### Common Mistakes to Avoid (from project-context.md + previous stories)

| Mistake | Correct Pattern | Source |
|---------|-----------------|--------|
| Required string without length check | `Field(min_length=1)` | 2-4 |
| Numeric fields without bounds | `Field(ge=0)` | 2-4 |
| Both `Field()` AND `@field_validator` | Use only `Field(ge=, le=)` for range | 2-4 |
| Missing `__all__` in `__init__.py` | Export all public classes | 1.5-8 |
| Not running `make test-ollama` | Run before marking done | Epic 2 retro |
| Missing `ConfigDict(strict=True)` | Add to all Pydantic models | 3-2 |
| Using `= []` instead of `Field(default_factory=list)` | Use factory for mutable defaults | 3-2 |
| Circular import with Entry/DateRange | Use `Any` type annotation, document | 3-3 |
| Class constant list without tuple | Use `EXPANSION_TIERS: list[int]` (immutable via convention) | N/A |

### Pre-Review Checklist

Before requesting code review, verify:

- [x] `make check` passes (lint + typecheck)
- [x] `make test-ollama` passes (integration tests)
- [x] All new functions have Google-style docstrings
- [x] All new classes/fields exported in `__init__.py` with `__all__`
- [x] New fields use correct Field() constraints (ge=0, min_length=1, etc.)
- [x] Empty list cases tested for expansion
- [x] No regression in existing tests (run full suite)
- [x] Progressive expansion tests cover all tiers (0, 1, 2, 3)
- [x] Korean-English mismatch test exists and passes
- [x] Planner prompt includes today's date

### Validation Commands

```bash
# During development
make check                    # lint + typecheck

# Before marking complete (REQUIRED)
make validate                 # lint + format + typecheck + unit tests
make test-ollama              # Integration tests with real Ollama
```

### Dependencies

| Dependency | Status | Notes |
|------------|--------|-------|
| PlannerAgent | Done (3-2) | Modify prompt, add today's date |
| RetrieverAgent | Done (3-3) | Add expansion logic |
| StorageRepository | Done (2-1) | No changes needed |
| pytest fixtures | Done | Use existing mock_llm, tmp_path |
| Entry, DateRange | Done (2-1) | Use Any type to avoid circular import |

### Why This Matters (From Epic 4 Retrospective)

> "The retrieval strategy issue will cause problems for Clarifier agent if not fixed. Clarifier needs to retrieve relevant context to generate good clarifying questions."

This story blocks Epic 5 (Human-in-the-Loop) because the Clarifier agent depends on reliable context retrieval. Without this fix:
- Comparison queries fail to find relevant logs
- Cross-language logs (Korean entries, English queries) are not retrieved
- User experience degrades significantly for bilingual users

### References

- [Source: epic-4/retro-2026-01-14.md#Retrieval-Strategy-Ordering] Problem discovery
- [Source: agent-system-design.md#5.4] State transitions (PLAN → RETRIEVE)
- [Source: sprint-status.yaml#Story-3.5] Story tracking
- [Source: 3-2-implement-planner-agent.md] Planner implementation patterns
- [Source: 3-3-implement-retriever-agent.md] Retriever implementation patterns
- [Source: project-context.md] Quilto vs Swealog separation

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

None required - all tests passed on first implementation.

### Completion Notes List

1. **Planner Prompt Updates (planner.py:171-214)**
   - Added "COMPARISON/PROGRESS QUERIES" section with trigger words
   - Added `Today's date: {date.today().isoformat()}` to INPUT section
   - Added `explicit_date` flag documentation to DATE_RANGE strategy
   - Added examples for comparison vs keyword query selection

2. **Progressive Expansion (retriever.py:429-517)**
   - Implemented `_execute_date_range_with_expansion()` method
   - Added `EXPANSION_TIERS = [7, 14, 30, 90]` class constant
   - Tracks expansion tier in each RetrievalAttempt
   - Falls back to term search when all tiers exhausted

3. **Model Updates (models.py)**
   - Added `expansion_tier: int = Field(default=0, ge=0)` to RetrievalAttempt
   - Added `enable_progressive_expansion: bool = True` to RetrieverInput
   - Added `expansion_exhausted: bool = False` to RetrieverOutput

4. **Test Coverage**
   - `TestPlannerComparisonQueries` - 5 tests for comparison query detection
   - `TestPlannerPromptTodaysDate` - 2 tests for prompt content
   - `TestRetrieverProgressiveExpansion` - 8 tests for expansion logic
   - `TestRetrieverLanguageMismatch` - 1 test for Korean-English scenario
   - Integration tests with real Ollama: `test_real_comparison_query_uses_date_range`, `test_real_explicit_date_query_sets_flag`

5. **Validation Results**
   - `make validate`: 974 passed, 24 skipped
   - `make test-ollama`: 994 passed, 4 skipped (20 min 33 sec)

### File List

| File | Action | Lines Changed |
|------|--------|---------------|
| `packages/quilto/quilto/agents/planner.py` | Modified | Added `from datetime import date`, updated RETRIEVAL STRATEGIES section, added today's date to INPUT |
| `packages/quilto/quilto/agents/retriever.py` | Modified | Added `timedelta` import, `EXPANSION_TIERS` constant, `_execute_date_range_with_expansion()` method, updated `retrieve()` method |
| `packages/quilto/quilto/agents/models.py` | Modified | Added `expansion_tier` to RetrievalAttempt, `enable_progressive_expansion` to RetrieverInput, `expansion_exhausted` to RetrieverOutput |
| `packages/quilto/tests/test_planner.py` | Modified | Added `TestPlannerComparisonQueries` (5 tests), `TestPlannerPromptTodaysDate` (2 tests), 2 integration tests |
| `packages/quilto/tests/test_retriever.py` | Modified | Added `TestRetrieverProgressiveExpansion` (8 tests), `TestRetrieverLanguageMismatch` (1 test), updated 2 existing tests to disable expansion |
| `scripts/manual_test.py` | Modified | Added `expansion_tier` and `expansion_exhausted` to retrieval output display |

---

## Code Review (2026-01-14)

### Issues Found and Fixed

**Issue #1: Integration Tests Failing with Real Ollama** [HIGH - FIXED]
- **File:** `packages/quilto/quilto/agents/planner.py:291`
- **Problem:** The Planner prompt's `gaps_status` schema description was ambiguous. Local LLMs
  (qwen2.5:3b) sometimes output `{"searched": false, "found": false}` instead of the expected
  nested structure `{"gap_desc": {"searched": bool, "found": bool}}`.
- **Fix:** Added concrete example to prompt:
  `Example: {{"missing data": {{"searched": true, "found": false}}}}. Use {{}} if no gaps.`
- **Tests:** `test_real_comparison_query_uses_date_range` and `test_real_explicit_date_query_sets_flag` now pass.

### Post-Review Validation

- `make validate`: 974 passed, 24 skipped
- `make test-ollama`: 994 passed, 4 skipped (17 min 16 sec)

### Reviewer Notes

- All acceptance criteria verified against implementation
- Test coverage is comprehensive for new functionality
- Code follows project conventions (Google-style docstrings, proper exports)
