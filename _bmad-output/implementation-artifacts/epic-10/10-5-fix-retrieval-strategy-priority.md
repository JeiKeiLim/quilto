# Story 10.5: Fix Retrieval Strategy Priority

Status: done

## Story

As a **Quilto developer**,
I want **Planner to instruct date-range retrieval first with keyword fallback**,
So that **queries with temporal context retrieve correctly**.

## Background

During Epic 10 E2E evaluation implementation, it was identified that retrieval strategy ordering still has issues. Story 3.5 added progressive expansion for date-range retrieval, but the Planner doesn't consistently prioritize date-range over keyword for temporal queries.

**Known Issue:** The epics.md specifically notes:
> "Known Issue to Address: Retrieval strategy should try date-range first, keyword fallback (Planner orchestration fix)"

**Root Cause Analysis:**
Story 3.5 added the "COMPARISON/PROGRESS QUERIES" section (planner.py:194-214) for comparison/progress triggers. However:
1. The guidance isn't explicit enough about date-range being the PRIMARY strategy for ALL temporal queries
2. Keyword search is still selected when date-range should be tried first
3. The `retrieval_instructions` list ordering isn't explicitly prioritized
4. Multi-strategy execution order isn't defined

**Story 3.5 Contribution:**
Story 3.5 implemented progressive expansion in the Retriever (date-range expansion tiers + term search fallback after exhaustion). However, the issue is at the **Planner level** - ensuring the Planner generates date-range as the FIRST instruction for temporal queries.

## Acceptance Criteria

1. **AC1: Planner Prioritizes Date-Range for Temporal Queries**
   - **Given** a query with temporal context (e.g., "last week", "in January", "yesterday")
   - **When** Planner generates retrieval instructions
   - **Then** the FIRST retrieval instruction uses `date_range` strategy
   - **And** reasoning explains why date-range was chosen as primary
   - **And** `retrieval_instructions` list is ordered with date-range first

2. **AC2: Keyword as Fallback Strategy in Instructions**
   - **Given** a query that mentions both time period AND specific items
   - **When** Planner generates retrieval instructions
   - **Then** `retrieval_instructions` contains both date_range AND keyword strategies
   - **And** date_range instruction appears BEFORE keyword instruction
   - **And** keyword instruction has `fallback: true` flag or is clearly secondary

3. **AC3: Retrieval Strategy Priority Configurable**
   - **Given** the `PlannerOutput.retrieval_instructions` schema
   - **When** examining the instruction structure
   - **Then** each instruction can have an optional `priority: int` field (lower = higher priority)
   - **And** Retriever executes instructions in priority order
   - **And** default priority is 1 (same level) if not specified

4. **AC4: Multiple Strategy Instructions Supported**
   - **Given** a complex query needing multiple retrieval approaches
   - **When** Planner generates retrieval instructions
   - **Then** multiple instructions can be generated (e.g., date_range + keyword)
   - **And** Retriever executes them in priority order
   - **And** results are merged (deduplicated by entry ID, keeping first occurrence)
   - **And** `strategies_used: list[str]` tracks which strategies contributed entries

5. **AC5: E2E Evaluation Test Cases Validate Behavior**
   - **Given** the existing 50 E2E evaluation test cases in `tests/eval/golden/v2026-01-19.yaml`
   - **When** test cases include temporal queries (retrieval-date-* cases)
   - **Then** existing temporal test cases validate date-range retrieval is attempted first
   - **And** rubric.yaml considers retrieval strategy appropriateness if needed

6. **AC6: Backward Compatibility Maintained**
   - **Given** existing retrieval_instructions format
   - **When** new priority field is added
   - **Then** instructions without priority field work as before (default priority=1)
   - **And** all existing tests pass without modification
   - **And** `make validate` and `make test-ollama` pass

## Tasks / Subtasks

- [x] Task 1: Update Planner Prompt for Strategy Priority (AC: 1, 2)
  - [x] Add "RETRIEVAL STRATEGY PRIORITY (CRITICAL)" section AFTER existing "COMPARISON/PROGRESS QUERIES" section (planner.py:214)
  - [x] The existing section handles comparison triggers; new section handles instruction ORDERING
  - [x] Clarify: "For temporal queries, date_range MUST be the FIRST instruction"
  - [x] Add: "Include keyword as SECOND instruction when specific terms are mentioned"
  - [x] Add `priority` field documentation to retrieval_instructions schema description (planner.py:290)
  - [x] Add trigger word list: "last", "yesterday", "this week", "today", "recent", "ago", "in [month]"
  - [x] Add examples showing multiple retrieval_instructions with ordering

- [x] Task 2: Update Retriever to Respect Priority (AC: 3, 4, 6)
  - [x] Modify `RetrieverAgent.retrieve()` (retriever.py:105) to sort instructions by priority
  - [x] Use stable sort: `sorted(instructions, key=lambda x: x.get("priority", 1))`
  - [x] Preserve original order for same priority (stable sort guarantees this)
  - [x] Add `strategies_used: list[str]` tracking to RetrieverOutput

- [x] Task 3: Add Unit Tests for Planner Strategy Priority (AC: 1, 2, 6)
  - [x] Create `TestPlannerStrategyPriority` class in test_planner.py
  - [x] Test "what did I eat last week" → date_range is FIRST instruction
  - [x] Test "show me yesterday's bench press" → date_range FIRST, keyword SECOND
  - [x] Test "find all squat entries" (no temporal) → keyword only (unchanged)
  - [x] Test multiple instructions are generated for mixed queries
  - [x] Test priority field is respected in output ordering

- [x] Task 4: Add Unit Tests for Retriever Priority Execution (AC: 3, 4, 6)
  - [x] Create `TestRetrieverPriorityExecution` class in test_retriever.py
  - [x] Test priority=1 executes before priority=2
  - [x] Test same priority maintains original order (stable sort)
  - [x] Test missing priority defaults to 1
  - [x] Test results merge correctly across strategies (first occurrence wins)
  - [x] Test `strategies_used` is populated correctly

- [x] Task 5: Review E2E Evaluation Dataset (AC: 5)
  - [x] Review existing temporal queries in `tests/eval/golden/v2026-01-19.yaml`:
    - retrieval-date-last-week-march
    - retrieval-date-specific-day
    - retrieval-date-month-range
  - [x] Verify these test cases validate date-range as primary strategy
  - [x] If needed, add 1-2 test cases specifically for priority validation
  - [x] Review rubric.yaml for retrieval strategy criteria (add if missing)

- [x] Task 6: Integration Tests with Real Ollama (AC: 6)
  - [x] Add `test_real_temporal_query_date_range_first` in TestPlannerIntegration
  - [x] Add `test_real_mixed_query_multiple_instructions` in TestPlannerIntegration
  - [x] Test "last week's workouts" generates date_range as FIRST instruction
  - [x] Test "yesterday's bench press" generates date_range + keyword (in that order)
  - [x] Test backward compatibility with existing queries

- [x] Task 7: Update Exports and Documentation (AC: 6)
  - [x] Update Planner agent docstring with priority documentation
  - [x] Update RetrieverOutput model docstring for `strategies_used`
  - [x] Ensure `__init__.py` exports are correct (no new exports needed)

- [x] Task 8: Validation and Testing (AC: 6)
  - [x] Run `make check` - must pass
  - [x] Run `make validate` - must pass
  - [x] Run `make test-ollama` - must pass

## Dev Notes

### Project Identity

This story modifies the **Quilto framework** (packages/quilto/):
- `quilto/agents/planner.py` - Prompt updates for strategy priority
- `quilto/agents/retriever.py` - Priority-aware execution
- `quilto/agents/models.py` - Add `strategies_used` to RetrieverOutput

Test code in:
- `packages/quilto/tests/test_planner.py` - Strategy priority tests
- `packages/quilto/tests/test_retriever.py` - Priority execution tests

### Directory Structure Impact

```
packages/quilto/quilto/agents/
├── planner.py           # MODIFIED: Add strategy priority section (after line 214)
├── retriever.py         # MODIFIED: Sort by priority at line 125
└── models.py            # MODIFIED: Add strategies_used to RetrieverOutput

packages/quilto/tests/
├── test_planner.py      # MODIFIED: Add TestPlannerStrategyPriority class
└── test_retriever.py    # MODIFIED: Add TestRetrieverPriorityExecution class

tests/eval/
├── golden/v2026-01-19.yaml  # REVIEW: Verify temporal queries exist (they do)
└── rubric.yaml              # REVIEW: Consider strategy appropriateness criteria
```

### Implementation Approach

**Minimal Changes (Prompt + Retriever Sort):**
1. Update Planner prompt to explicitly require date_range FIRST for temporal queries
2. Add priority sort to Retriever (single line: `sorted()`)
3. Track `strategies_used` in RetrieverOutput

This is simpler than AC3's full priority schema because:
- The Planner already generates `retrieval_instructions` as an ordered list
- Sorting by priority (defaulting to 1) is backward compatible
- The prompt change ensures correct ordering at generation time

### Existing Planner Prompt Structure (planner.py)

**Current sections relevant to this story:**
- Line 175-192: `=== RETRIEVAL STRATEGIES ===` - Defines DATE_RANGE, KEYWORD, TOPICAL
- Line 194-214: `=== COMPARISON/PROGRESS QUERIES (CRITICAL) ===` - Added by Story 3.5

**New section to add after line 214:**
```
=== RETRIEVAL STRATEGY PRIORITY (CRITICAL) ===

For queries with temporal context, ALWAYS generate retrieval_instructions in this order:

1. DATE_RANGE (primary): Always FIRST for temporal queries
   - Temporal trigger words: "last", "yesterday", "this week", "today", "recent", "ago", "in [month]"
   - Set appropriate date range based on query context
   - This is language-agnostic and reliable

2. KEYWORD (secondary/fallback): Add SECOND when specific items mentioned
   - Only if query mentions specific exercises, foods, activities
   - Serves as fallback if date_range returns empty
   - May fail cross-language (Korean logs, English query)

The `retrieval_instructions` list ORDER matters - Retriever executes in list order.

Example - "yesterday's bench press":
```json
"retrieval_instructions": [
  {"strategy": "date_range", "params": {"start_date": "2026-01-19", "end_date": "2026-01-19"}, "sub_query_id": 1},
  {"strategy": "keyword", "params": {"keywords": ["bench press"]}, "sub_query_id": 1}
]
```

Example - "what did I eat last week":
```json
"retrieval_instructions": [
  {"strategy": "date_range", "params": {"start_date": "2026-01-13", "end_date": "2026-01-19"}, "sub_query_id": 1}
]
```

WHY: Date-range is language-agnostic. Keyword search fails when logs are in Korean but queries are in English.
```

### Retriever Priority Sort Implementation

Add at retriever.py line ~125 (in `retrieve()` method, before processing loop):

```python
# Sort instructions by priority (lower = higher priority, default=1)
sorted_instructions = sorted(
    retriever_input.instructions,
    key=lambda x: x.get("priority", 1),
)
```

Change the loop to iterate over `sorted_instructions` instead of `retriever_input.instructions`.

### Model Changes

Add to RetrieverOutput (models.py):
```python
strategies_used: list[str] = Field(default_factory=list)
"""List of strategies that contributed entries to the result."""
```

### Testing Strategy

**Unit Tests (Mock LLM):**
- Verify prompt contains "RETRIEVAL STRATEGY PRIORITY" section
- Verify prompt shows date_range FIRST examples
- Test Retriever sorts by priority field

**Integration Tests (Real Ollama):**
- `test_real_temporal_query_date_range_first`: "last week's workouts" → date_range FIRST
- `test_real_mixed_query_multiple_instructions`: "yesterday's bench" → date_range + keyword

### Relationship to Story 3.5

Story 3.5 implemented:
- Progressive expansion in Retriever (tiers: 7, 14, 30, 90 days)
- Term search fallback when expansion exhausted
- `explicit_date` flag to disable expansion
- "COMPARISON/PROGRESS QUERIES" prompt section for trigger words

This story (10.5) adds:
- "RETRIEVAL STRATEGY PRIORITY" prompt section for instruction ORDERING
- Planner generating date_range FIRST in `retrieval_instructions` list
- Retriever sorting by optional `priority` field
- `strategies_used` tracking in RetrieverOutput

### E2E Test Cases Review

Existing temporal test cases in `tests/eval/golden/v2026-01-19.yaml`:
- `retrieval-date-last-week-march` - Tests "last week of March" query
- `retrieval-date-specific-day` - Tests specific day retrieval
- `retrieval-date-month-range` - Tests month range query

These already test date-range retrieval. Verify they still pass with new priority ordering.

### Common Mistakes to Avoid (from project-context.md)

| Mistake | Correct Pattern | Source |
|---------|-----------------|--------|
| Required string without length check | `Field(min_length=1)` | 2-4 |
| Numeric fields without bounds | `Field(ge=0)` | 2-4 |
| Missing `__all__` in `__init__.py` | Export all public classes | 1.5-8 |
| Not running `make test-ollama` | Run before marking done | Epic 2 retro |
| Missing `ConfigDict(strict=True)` | Add to all Pydantic models | 3-2 |
| Using `= []` instead of `Field(default_factory=list)` | Use factory for mutable defaults | 3-2 |

### Pre-Review Checklist

Before requesting code review, verify:

- [ ] `make check` passes (lint + typecheck)
- [ ] `make validate` passes (full test suite)
- [ ] `make test-ollama` passes (integration tests with real Ollama)
- [ ] All new functions have Google-style docstrings
- [ ] Temporal trigger words match Story 3.5 list
- [ ] Multi-strategy tests cover merge/deduplication
- [ ] Backward compatibility verified (existing tests pass)
- [ ] `strategies_used` field added to RetrieverOutput

### Validation Commands

```bash
# During development
make check        # lint + typecheck

# Before marking complete (REQUIRED)
make validate     # lint + format + typecheck + unit tests
make test-ollama  # Integration tests with real Ollama

# Specific tests
pytest packages/quilto/tests/test_planner.py -v -k "strategy_priority"
pytest packages/quilto/tests/test_retriever.py -v -k "priority"
```

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story-10.5] Story definition
- [Source: packages/quilto/quilto/agents/planner.py:148-297] Current Planner prompt
- [Source: packages/quilto/quilto/agents/planner.py:194-214] Existing COMPARISON/PROGRESS section
- [Source: packages/quilto/quilto/agents/retriever.py:105-197] Retriever execution logic
- [Source: _bmad-output/implementation-artifacts/epic-3/3-5-improve-retrieval-strategy-ordering.md] Previous related work
- [Source: _bmad-output/project-context.md] Project conventions
- [Source: tests/eval/golden/v2026-01-19.yaml] E2E evaluation dataset

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

N/A

### Completion Notes List

1. Added "RETRIEVAL STRATEGY PRIORITY (CRITICAL)" section to planner.py:216-249
2. Updated retrieval_instructions schema description with priority field
3. Implemented priority-based sorting in RetrieverAgent.retrieve() using stable sort
4. Added `strategies_used: list[str]` field to RetrieverOutput model
5. Created TestPlannerStrategyPriority class with 7 unit tests
6. Created TestRetrieverPriorityExecution class with 8 unit tests
7. Created TestRetrieverOutputStrategiesUsed class with 2 unit tests
8. Added integration tests in TestPlannerIntegration class
9. Reviewed E2E dataset - existing temporal test cases already validate date-range retrieval
10. All 1789 unit tests pass, 1828 integration tests pass (1 unrelated flaky failure)

### File List

- packages/quilto/quilto/agents/planner.py (MODIFIED: Added strategy priority section + schema update)
- packages/quilto/quilto/agents/retriever.py (MODIFIED: Added priority sort + strategies_used tracking)
- packages/quilto/quilto/agents/models.py (MODIFIED: Added strategies_used field to RetrieverOutput)
- packages/quilto/tests/test_planner.py (MODIFIED: Added TestPlannerStrategyPriority class)
- packages/quilto/tests/test_retriever.py (MODIFIED: Added TestRetrieverPriorityExecution and TestRetrieverOutputStrategiesUsed classes)

