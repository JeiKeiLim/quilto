# Story 13.2: Simplify Retrieval with Storage Awareness

Status: review

## Story

As a **Quilto developer**,
I want **retrieval to use date-range strategy with storage awareness and LLM-based relevance filtering**,
So that **Planner makes informed decisions and we eliminate keyword matching edge cases**.

## Background

**Origin:** Dogfooding Iteration 3 (Epic 13)
**Source:** `tests/eval/feedback/archive/iter-002/analysis.md` - Pattern 8: Keyword Retrieval Misses Exact Matches
**Priority:** High | **Effort:** Medium-Large (4-6 hours)
**Type:** Architecture simplification - remove keyword/topical, add storage awareness

**Key Insight from Architecture:**
> "Data scale fits within context windows (~109k chars/year). Date/keyword retrieval + summarization sufficient."
> "Date-based retrieval + hierarchical summarization" (architecture.md)

The original architecture envisioned date-based retrieval as primary. Keyword matching was added as optimization but introduced infinite edge cases (Korean spacing: "벤치 프레스" vs "벤치프레스", synonyms, abbreviations). This story returns to the architecture's core design: simple date-range retrieval with LLM-based filtering.

**User Feedback (Record `151de3d9`):**
- "I had benchpress records in 2026-01-12 and it failed to retrieve that."
- Keyword search failed due to Korean spacing variations

## Acceptance Criteria

**Part A: Storage Awareness (enables smart date-range selection)**

1. **Given** `StorageRepository`
   **When** `get_storage_summary()` is called
   **Then** it returns: date range with logs (first_date, last_date), entry count per month

2. **Given** Planner generates retrieval instructions
   **When** processing a query
   **Then** Planner first calls storage summary to know what dates have data

3. **Given** storage summary shows logs exist from 2026-01-01 to 2026-01-20
   **When** user asks "what did I do last month?"
   **Then** Planner generates date range within available data (not guessing blindly)

**Part B: Date-Range Only (remove keyword/topical)**

4. **Given** any query requiring context retrieval
   **When** Retriever executes
   **Then** only DATE_RANGE strategy is used (keyword and topical strategies removed)

5. **Given** Planner generates retrieval instructions
   **When** instructions are created
   **Then** only date_range strategy is specified (no keyword/topical instructions)

6. **Given** RetrieverAgent code
   **When** reviewing implementation
   **Then** `_execute_keyword()`, `_execute_topical()`, and `expand_terms()` are removed

**Part C: LLM-Based Relevance Filtering**

7. **Given** date-range returns entries
   **When** Analyzer processes them
   **Then** Analyzer filters entries by query relevance (LLM-based filtering replaces keyword pre-filtering)

8. **Given** a query for "bench press 1RM"
   **When** logs in date range contain "벤치 프레스 60kg"
   **Then** Analyzer identifies and uses that entry (no keyword matching required)

## Tasks / Subtasks

- [x] Task 1: Add StorageSummary model and get_storage_summary() method (AC: #1)
  - [x] 1.1: Create `StorageSummary` Pydantic model in `packages/quilto/quilto/storage/models.py`
  - [x] 1.2: Add `get_storage_summary()` method to `StorageRepository` (repository.py)
  - [x] 1.3: Export `StorageSummary` in `packages/quilto/quilto/storage/__init__.py` (add import and `__all__` entry)
  - [x] 1.4: Add unit tests in `test_storage.py` for `get_storage_summary()`

- [x] Task 2: Update RetrievalStrategy enum (AC: #4, #5)
  - [x] 2.1: Remove `KEYWORD` and `TOPICAL` from `RetrievalStrategy` enum (models.py)
  - [x] 2.2: Update docstring to explain DATE_RANGE only approach

- [x] Task 3: Simplify Retriever agent (AC: #4, #6)
  - [x] 3.1: Remove `_execute_keyword()` method from `retriever.py`
  - [x] 3.2: Remove `_execute_topical()` method from `retriever.py`
  - [x] 3.3: Remove `expand_terms()` function from `retriever.py`
  - [x] 3.4: Simplify `_execute_strategy()` to only handle DATE_RANGE
  - [x] 3.5: Keep `_execute_date_range_with_expansion()` for progressive date expansion
  - [x] 3.6: Remove `vocabulary` field from `RetrieverInput` model (no longer needed)
  - [x] 3.7: Remove `expanded_terms` field from `RetrievalAttempt` model (no longer needed)

- [x] Task 4: Update Planner for storage awareness (AC: #2, #3, #5)
  - [x] 4.1: Add `storage_summary` field to `PlannerInput` model (models.py)
  - [x] 4.2: Add `storage_summary` field to `SessionState` (state/session.py)
  - [x] 4.3: Update plan node to call `get_storage_summary()` and pass to Planner (state machine integration)
  - [x] 4.4: Update Planner prompt to remove KEYWORD/TOPICAL strategy sections
  - [x] 4.5: Add storage summary to Planner prompt for informed date-range decisions
  - [x] 4.6: Simplify retrieval instruction generation to only produce DATE_RANGE

- [x] Task 5: Enhance Analyzer for LLM-based relevance filtering (AC: #7, #8)
  - [x] 5.1: Add relevance filtering guidance to Analyzer prompt
  - [x] 5.2: Prompt should instruct: "Filter entries by query relevance regardless of language"
  - [x] 5.3: Handle cross-language matching (English query → Korean log entries)

- [x] Task 6: Update tests (AC: all)
  - [x] 6.1: Remove `TestRetrieverKeyword` class from `test_retriever.py`
  - [x] 6.2: Remove `TestRetrieverTopical` class from `test_retriever.py`
  - [x] 6.3: Remove `TestExpandTerms` class from `test_retriever.py`
  - [x] 6.4: Update tests referencing KEYWORD/TOPICAL strategy in `test_planner.py`
  - [x] 6.5: Update `test_models.py` for RetrievalStrategy enum changes
  - [x] 6.6: Add new tests for storage summary in `test_storage.py`
  - [x] 6.7: Add Analyzer relevance filtering tests in `test_analyzer.py`
  - [x] 6.8: Remove tests for `vocabulary` and `expanded_terms` fields

- [x] Task 7: Run validation
  - [x] 7.1: Run `make check` (lint + typecheck) - PASSED
  - [x] 7.2: Run `make validate` (full validation) - PASSED (1613 tests pass)
  - [ ] 7.3: Run `make test-ollama` (integration tests) - PENDING (requires running Ollama)

## Dev Notes

### Architectural Rationale

This change returns to the architecture's original intent:

| Original Design | What We Added | This Story |
|-----------------|---------------|------------|
| Date-based retrieval | Keyword search with vocabulary expansion | Remove keyword/topical |
| LLM does filtering | Regex/keyword pre-filtering | Analyzer filters by relevance |
| Simple, robust | Complex, edge-case prone | Simple, robust |

**Why keyword search failed:**
- Korean spacing: "벤치 프레스" vs "벤치프레스" (with/without space)
- Abbreviations: "BP" vs "bench press"
- Synonyms: "benchpress" vs "bench" vs "flat bench"
- Each edge case required vocabulary expansion → infinite maintenance

### File Changes Summary

| File | Change Type | Lines Impact |
|------|-------------|--------------|
| `packages/quilto/quilto/storage/models.py` | ADD | ~20 lines (StorageSummary model) |
| `packages/quilto/quilto/storage/repository.py` | ADD | ~30 lines (get_storage_summary method) |
| `packages/quilto/quilto/storage/__init__.py` | ADD | 2 lines (export) |
| `packages/quilto/quilto/agents/models.py` | MODIFY | Remove 2 enum values, remove RetrieverInput.vocabulary, RetrievalAttempt.expanded_terms |
| `packages/quilto/quilto/agents/retriever.py` | REMOVE | ~200 lines (keyword/topical methods, expand_terms) |
| `packages/quilto/quilto/agents/planner.py` | MODIFY | Simplify prompt, add storage awareness |
| `packages/quilto/quilto/agents/analyzer.py` | MODIFY | Add relevance filtering to prompt |
| `packages/quilto/quilto/state/session.py` | ADD | 1 field (storage_summary) |
| `packages/quilto/tests/test_retriever.py` | REMOVE | ~431 lines (keyword/topical/expand_terms tests: L312-397, L550-894) |
| `packages/quilto/tests/test_planner.py` | MODIFY | Update strategy tests |
| `packages/quilto/tests/test_storage.py` | ADD | ~50 lines (storage summary tests) |
| `packages/quilto/tests/test_analyzer.py` | ADD | ~30 lines (relevance filtering tests) |

### Implementation Details

#### 1. StorageSummary Model (models.py)

```python
from datetime import date

class StorageSummary(BaseModel):
    """Summary of storage contents for Planner awareness.

    Attributes:
        earliest_date: Date of first log entry (None if no entries).
        latest_date: Date of most recent log entry (None if no entries).
        total_entries: Total number of entries across all dates.
        entries_by_month: Count of entries per month (YYYY-MM format).
    """

    model_config = ConfigDict(strict=True)

    earliest_date: date | None = None
    latest_date: date | None = None
    total_entries: int = 0
    entries_by_month: dict[str, int] = Field(default_factory=dict)
```

#### 2. get_storage_summary() Method (repository.py)

```python
def get_storage_summary(self) -> StorageSummary:
    """Get summary of storage contents for Planner awareness.

    Returns:
        StorageSummary with date range and entry counts.
    """
    raw_path = self.base_path / "logs" / "raw"
    if not raw_path.exists():
        return StorageSummary()

    dates: list[date] = []
    entries_by_month: dict[str, int] = {}
    total_entries = 0

    # Scan year/month/day structure
    for year_dir in raw_path.iterdir():
        if not year_dir.is_dir():
            continue
        for month_dir in year_dir.iterdir():
            if not month_dir.is_dir():
                continue
            for day_file in month_dir.glob("*.md"):
                # Parse date from filename (YYYY-MM-DD.md)
                try:
                    entry_date = date.fromisoformat(day_file.stem)
                    dates.append(entry_date)
                    month_key = entry_date.strftime("%Y-%m")
                    # Count entries in file
                    content = day_file.read_text()
                    entry_count = content.count("## ")  # Each entry starts with timestamp header
                    entries_by_month[month_key] = entries_by_month.get(month_key, 0) + entry_count
                    total_entries += entry_count
                except ValueError:
                    continue

    if not dates:
        return StorageSummary()

    return StorageSummary(
        earliest_date=min(dates),
        latest_date=max(dates),
        total_entries=total_entries,
        entries_by_month=entries_by_month,
    )
```

#### 3. RetrievalStrategy Enum Update (models.py)

```python
class RetrievalStrategy(str, Enum):
    """Retrieval strategy for sub-queries.

    Only DATE_RANGE is supported. Keyword and topical searches were removed
    in Story 13.2 due to language/spacing edge cases. Analyzer performs
    LLM-based relevance filtering instead.

    Attributes:
        DATE_RANGE: Retrieve all entries within a date range.
    """

    DATE_RANGE = "date_range"
```

#### 4. PlannerInput Update (models.py)

Add storage_summary field to PlannerInput:

```python
class PlannerInput(BaseModel):
    """Input to Planner agent.

    Attributes:
        query: The user query to plan for.
        active_domain_context: Combined domain knowledge.
        global_context: User's accumulated context.
        storage_summary: Summary of storage contents for date range decisions.
    """

    model_config = ConfigDict(strict=True)

    query: str
    active_domain_context: ActiveDomainContext
    global_context: str
    storage_summary: StorageSummary | None = None  # NEW FIELD
```

#### 5. Planner Prompt Updates

**Remove from prompt:**
- "=== KEYWORD STRATEGY ===" section
- "=== TOPICAL STRATEGY ===" section
- Vocabulary expansion instructions
- Examples showing keyword/topical strategies

**Add to prompt:**
```
=== STORAGE AWARENESS ===

{storage_summary_text}

Use this to make informed date-range decisions:
- earliest_date and latest_date show the available log range
- entries_by_month shows data density
- If user asks "last week" but latest_date is older, adjust accordingly
- If user asks about a time with no logs, note this in retrieval_notes
```

**Simplify strategy section:**
```
=== RETRIEVAL STRATEGY ===

Only DATE_RANGE retrieval is available. Specify start_date and end_date.

Relevance filtering happens at Analyzer (LLM-based), not retrieval.
Retrieve broadly by date, let Analyzer determine what's relevant.

Examples:
- "How did my workout go last week?" → date_range: last 7 days
- "What's my bench press progress?" → date_range: last 30-90 days
- "What did I eat yesterday?" → date_range: yesterday only
```

#### 6. Analyzer Prompt Addition

Add after TEMPORAL CONTEXT section:

```
=== RELEVANCE FILTERING ===

The retrieved entries are from date-range retrieval. Your job includes:
1. FILTER: Identify which entries are actually relevant to the query
2. IGNORE: Skip entries that don't address the query intent
3. CROSS-LANGUAGE: Match regardless of language (English query → Korean log is OK)

Examples:
- Query: "bench press 1RM" → Log: "벤치 프레스 60kg x 5" → RELEVANT (same exercise)
- Query: "how was my run?" → Log: "bench press 80kg" → NOT RELEVANT (different activity)
- Query: "what did I eat?" → Log: "ran 5km" → NOT RELEVANT (fitness, not nutrition)

Include in your analysis which entries you considered relevant and why.
```

### Retriever Methods to Remove

From `retriever.py`, remove these methods entirely:

1. `expand_terms()` function (lines 20-62, ~43 lines)
2. `_execute_keyword()` method (lines 319-361, ~43 lines)
3. `_execute_topical()` method (lines 363-408, ~46 lines)

Total to remove: ~132 lines of implementation code

Update `_execute_strategy()`:
```python
def _execute_strategy(
    self,
    strategy: RetrievalStrategy,
    params: dict[str, Any],
) -> list[Entry]:
    """Execute a single retrieval strategy.

    Only DATE_RANGE is supported.
    """
    if strategy == RetrievalStrategy.DATE_RANGE:
        return self._execute_date_range(params)
    else:
        # Should never happen - only DATE_RANGE in enum
        msg = f"Unknown strategy: {strategy}"
        raise ValueError(msg)
```

### Test Updates Summary

**Remove entirely:**
- `TestRetrieverKeyword` class (~226 lines, L550-775)
- `TestRetrieverTopical` class (~119 lines, L776-894)
- `TestExpandTerms` class (~86 lines, L312-397)
- Total removal: ~431 lines

**Update:**
- `TestRetrievalStrategy` - expect only 1 value (DATE_RANGE)
- `TestRetrieverInput` - remove vocabulary field tests
- `TestRetrievalAttempt` - remove expanded_terms tests
- Any tests asserting KEYWORD or TOPICAL strategy generation
- Integration tests that set up keyword/topical scenarios

**Add:**
- `TestStorageSummary` in test_storage.py
- `TestAnalyzerRelevanceFiltering` in test_analyzer.py

### Edge Cases to Handle

1. **Empty storage:** `get_storage_summary()` returns empty summary, Planner notes no data available
2. **Single date:** earliest_date == latest_date, still valid
3. **Sparse data:** entries_by_month shows gaps, Planner can note this
4. **No entries in date range:** Retriever returns empty list, Analyzer handles gracefully

### Backward Compatibility

This is a **breaking change** to the retrieval API:
- `RetrievalStrategy.KEYWORD` and `TOPICAL` removed from enum
- Any code using these strategies will fail with AttributeError
- This is acceptable as Quilto is pre-1.0 and this is framework-internal

### State Machine Integration (Task 4.2, 4.3)

The Planner node needs access to storage summary. Add to `SessionState`:

```python
# In state/session.py
class SessionState(TypedDict, total=False):
    # ... existing fields ...

    # Storage awareness (Story 13.2)
    storage_summary: dict[str, Any] | None  # StorageSummary.model_dump()
```

The plan node (or a pre-plan step) must call `get_storage_summary()` and include it in `PlannerInput`. This ensures Planner knows what date ranges have data before generating retrieval instructions.

### Validation Checklist

```
- [ ] `make check` passes (lint + typecheck)
- [ ] `make validate` passes (all unit tests)
- [ ] `make test-ollama` passes (integration tests)
- [ ] StorageSummary model created and exported
- [ ] get_storage_summary() method works correctly
- [ ] RetrievalStrategy enum has only DATE_RANGE
- [ ] _execute_keyword() removed from Retriever
- [ ] _execute_topical() removed from Retriever
- [ ] expand_terms() removed from Retriever
- [ ] RetrieverInput.vocabulary field removed
- [ ] RetrievalAttempt.expanded_terms field removed
- [ ] SessionState has storage_summary field
- [ ] Planner prompt simplified to DATE_RANGE only
- [ ] Planner uses storage_summary for decisions
- [ ] Analyzer prompt has relevance filtering guidance
- [ ] ~431 lines of tests removed from test_retriever.py
- [ ] New tests for storage summary and relevance filtering
```

### Project Structure Notes

- All changes are in Quilto (`packages/quilto/`) - framework level
- No changes to Swealog (`packages/swealog/`) - application level
- Test rule: "Would this work for a cooking app?" → YES, this is domain-agnostic

### References

| Source | Content |
|--------|---------|
| `tests/eval/feedback/archive/iter-002/analysis.md` | Pattern 8: Keyword Retrieval Misses Exact Matches |
| `_bmad-output/planning-artifacts/architecture.md` | "Date-based retrieval + hierarchical summarization" |
| `_bmad-output/planning-artifacts/epics.md#Story 13.2` | Story definition with acceptance criteria |
| `_bmad-output/implementation-artifacts/epic-13/13-1-add-temporal-recency-awareness.md` | Previous story learnings |
| `packages/quilto/quilto/storage/repository.py` | Current StorageRepository implementation |
| `packages/quilto/quilto/agents/retriever.py` | Current Retriever with keyword/topical methods |
| `packages/quilto/quilto/agents/planner.py` | Current Planner with complex strategy instructions |

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

N/A

### Completion Notes List

- Removed `expand_terms()` function and `_execute_keyword()`, `_execute_topical()` methods from Retriever
- Removed `KEYWORD` and `TOPICAL` from RetrievalStrategy enum (now only DATE_RANGE)
- Removed `vocabulary` field from RetrieverInput model
- Removed `expanded_terms` field from RetrievalAttempt model
- Removed `expand_terms` export from `quilto/agents/__init__.py`
- Added StorageSummary model and get_storage_summary() method
- Updated Planner prompt with storage awareness and simplified to DATE_RANGE only
- Added relevance filtering section to Analyzer prompt for cross-language matching
- Removed ~1000 lines of keyword/topical test code from test_retriever.py
- Added tests for unknown strategy warnings (keyword/topical now generate warnings)
- Updated test_planner.py tests for simplified strategy handling
- Fixed Swealog API routes that still referenced vocabulary parameter

### File List

| File | Change Type | Summary |
|------|-------------|---------|
| `packages/quilto/quilto/storage/models.py` | MODIFIED | Added StorageSummary Pydantic model |
| `packages/quilto/quilto/storage/repository.py` | MODIFIED | Added get_storage_summary() method |
| `packages/quilto/quilto/storage/__init__.py` | MODIFIED | Exported StorageSummary |
| `packages/quilto/quilto/agents/models.py` | MODIFIED | Removed KEYWORD/TOPICAL from enum, removed vocabulary/expanded_terms fields |
| `packages/quilto/quilto/agents/retriever.py` | MODIFIED | Removed keyword/topical methods, simplified to DATE_RANGE only |
| `packages/quilto/quilto/agents/planner.py` | MODIFIED | Added storage awareness, simplified prompt to DATE_RANGE only |
| `packages/quilto/quilto/agents/analyzer.py` | MODIFIED | Added relevance filtering section to prompt |
| `packages/quilto/quilto/agents/__init__.py` | MODIFIED | Removed expand_terms export |
| `packages/quilto/quilto/state/session.py` | MODIFIED | Added storage_summary field |
| `packages/quilto/tests/test_retriever.py` | MODIFIED | Removed keyword/topical/expand_terms tests, added unknown strategy tests |
| `packages/quilto/tests/test_planner.py` | MODIFIED | Updated tests for simplified strategy handling |
| `packages/quilto/tests/test_storage.py` | MODIFIED | Added StorageSummary tests |
| `packages/quilto/tests/test_analyzer.py` | MODIFIED | Removed expanded_terms reference |
| `packages/quilto/tests/test_clarifier.py` | MODIFIED | Removed expanded_terms reference |
| `packages/swealog/swealog/api/routes/query.py` | MODIFIED | Removed vocabulary parameter from RetrieverInput calls |
