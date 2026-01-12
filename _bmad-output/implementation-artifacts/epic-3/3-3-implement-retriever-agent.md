# Story 3.3: Implement Retriever Agent

Status: done

## Story

As a **Quilto developer**,
I want a **Retriever agent that fetches entries using StorageRepository**,
So that **relevant context is gathered for analysis based on Planner's retrieval strategy**.

## Acceptance Criteria

1. **Given** Planner's retrieval instructions with `DATE_RANGE` strategy
   **When** Retriever executes it
   **Then** entries are fetched via `StorageRepository.get_entries_by_date_range()`
   **And** all entries in the date range are returned without pre-filtering
   **And** `retrieval_summary` documents the search attempt with entries_found count

2. **Given** Planner's retrieval instructions with `KEYWORD` strategy
   **When** Retriever executes it
   **Then** entries are fetched via `StorageRepository.search_entries()`
   **And** vocabulary is used to expand search terms (e.g., "pr" → "personal record")
   **And** `semantic_expansion` param triggers additional related terms

3. **Given** Planner's retrieval instructions with `TOPICAL` strategy
   **When** Retriever executes it
   **Then** entries are fetched via `StorageRepository.search_entries()` with expanded topics
   **And** `related_terms` from retrieval_params are included in the search

4. **Given** multiple retrieval instructions from Planner
   **When** Retriever processes them
   **Then** each instruction is executed in order
   **And** `retrieval_summary` contains a `RetrievalAttempt` for each instruction
   **And** all unique entries are returned (no duplicates)

5. **Given** a retrieval that returns no results
   **When** Retriever completes
   **Then** `warnings` list includes a message about the empty result
   **And** `entries` is an empty list (not an error)
   **And** processing continues with remaining instructions

6. **Given** retrieval would return more than `max_entries` (default 100)
   **When** Retriever hits the limit
   **Then** `truncated` is set to `True`
   **And** `warnings` includes message about truncation
   **And** only `max_entries` entries are returned

7. **Given** the existing agent patterns from Router, Parser, Planner
   **When** implementing Retriever
   **Then** it follows the same patterns: AGENT_NAME, async method, Pydantic models
   **And** uses `StorageRepository` directly (no LLM call - pure retrieval)
   **And** is exported from `quilto.agents` module

8. **Given** integration tests with real storage
   **When** run with pytest
   **Then** Retriever correctly fetches entries by date range
   **And** Retriever correctly applies vocabulary expansion
   **And** Retriever correctly handles empty results

## Tasks / Subtasks

- [x] Task 1: Define Retriever-related models in models.py (AC: #1, #4, #6)
  - [x] Create `RetrievalAttempt` model with attempt_number (Field(ge=1)), strategy (Field(min_length=1)), params, entries_found (Field(ge=0)), summary (Field(min_length=1)), expanded_terms (default_factory=list)
  - [x] Create `RetrieverInput` model with instructions (list of dict), vocabulary (dict[str, str]), max_entries (int, default 100)
  - [x] Create `RetrieverOutput` model with entries, retrieval_summary, total_entries_found, date_range_covered, warnings (default_factory=list), truncated (default False)
  - [x] Use existing `Entry` and `DateRange` models from `quilto.storage.models`
  - [x] Use `Field(min_length=1)` for required string fields
  - [x] Use `Field(ge=0)` or `Field(ge=1)` for numeric bounds
  - [x] Use `ConfigDict(strict=True)` for all models

- [x] Task 2: Implement RetrieverAgent class (AC: #1, #2, #3, #7)
  - [x] Create `retriever.py` with RetrieverAgent class
  - [x] Implement `__init__(self, storage: StorageRepository)` - takes storage, NOT llm_client
  - [x] Implement `async retrieve(input: RetrieverInput) -> RetrieverOutput` main method
  - [x] Add Google-style docstrings for all methods

- [x] Task 3: Implement DATE_RANGE strategy execution (AC: #1)
  - [x] Parse `start_date` and `end_date` from retrieval_params
  - [x] Call `storage.get_entries_by_date_range(start, end)`
  - [x] Create RetrievalAttempt record with entries_found count

- [x] Task 4: Implement KEYWORD strategy with vocabulary expansion (AC: #2)
  - [x] Parse `keywords` list from retrieval_params
  - [x] Expand keywords using vocabulary dict (add synonyms/full forms)
  - [x] Handle `semantic_expansion` param at Retriever level (expand via vocabulary before storage call)
  - [x] Call `storage.search_entries(expanded_keywords, date_range)` with expanded terms
  - [x] Create RetrievalAttempt record with original and expanded terms

- [x] Task 5: Implement TOPICAL strategy (AC: #3)
  - [x] Parse `topics` and `related_terms` from retrieval_params
  - [x] Combine topics + related_terms into keyword list
  - [x] Call `storage.search_entries()` with combined terms
  - [x] Create RetrievalAttempt record

- [x] Task 6: Implement multi-instruction processing (AC: #4)
  - [x] Loop through all instructions in order
  - [x] Execute each based on strategy type
  - [x] Collect all entries, deduplicate by entry.id
  - [x] Build retrieval_summary with all attempts

- [x] Task 7: Implement warning and limit handling (AC: #5, #6)
  - [x] Add warning when instruction returns 0 entries
  - [x] Enforce max_entries limit with truncation
  - [x] Set truncated=True when limit is hit
  - [x] Add warning about truncation with entry counts

- [x] Task 8: Export from agents module (AC: #7)
  - [x] Add RetrieverAgent, RetrieverInput, RetrieverOutput, RetrievalAttempt to `__init__.py`
  - [x] Update `__all__` list with all new public symbols
  - [x] Ensure py.typed marker is present

- [x] Task 9: Add unit tests for Retriever models (AC: #1-#6)
  - [x] Test RetrievalAttempt validation (all fields, boundary values)
  - [x] Test RetrievalAttempt attempt_number >= 1, entries_found >= 0
  - [x] Test RetrievalAttempt strategy/summary min_length=1
  - [x] Test RetrieverInput with default max_entries (100)
  - [x] Test RetrieverInput max_entries >= 1 constraint
  - [x] Test RetrieverInput vocabulary default empty dict
  - [x] Test RetrieverOutput with all fields
  - [x] Test RetrieverOutput total_entries_found >= 0
  - [x] Test empty entries list is valid
  - [x] Test truncated flag behavior
  - [x] Test warnings default to empty list

- [x] Task 10: Add unit tests for RetrieverAgent (AC: #1-#6)
  - [x] Test DATE_RANGE strategy execution with mock storage
  - [x] Test KEYWORD strategy with vocabulary expansion (verify expanded_terms in RetrievalAttempt)
  - [x] Test KEYWORD strategy with semantic_expansion=True (more aggressive expansion)
  - [x] Test TOPICAL strategy with related terms
  - [x] Test multi-instruction processing and deduplication
  - [x] Test empty result warning generation
  - [x] Test max_entries truncation (verify truncated=True and warning)
  - [x] Test unknown strategy handling (warning added, instruction skipped)
  - [x] Test missing required params warning (e.g., date_range without start_date)

- [x] Task 11: Add integration tests with real storage (AC: #8)
  - [x] Create test fixture with sample entries in temp storage
  - [x] Test real date range retrieval
  - [x] Test real keyword search with vocabulary
  - [x] Test real topical search
  - [x] Use `tmp_path` fixture for isolated storage

- [x] Task 12: Verify no regression (AC: #7)
  - [x] Run `make validate` - passes lint + typecheck + unit tests
  - [x] Run `make test-ollama` - passes integration tests
  - [x] Verify all existing Router, Parser, Planner tests still pass

## Dev Notes

### Files to Create/Modify

| File | Action | Description |
|------|--------|-------------|
| `packages/quilto/quilto/agents/retriever.py` | Create | RetrieverAgent class |
| `packages/quilto/quilto/agents/models.py` | Modify | Add RetrievalAttempt, RetrieverInput, RetrieverOutput |
| `packages/quilto/quilto/agents/__init__.py` | Modify | Export new types |
| `packages/quilto/tests/test_retriever.py` | Create | Unit and integration tests |

### Required Imports

```python
# In retriever.py
from quilto.storage.models import DateRange, Entry
from quilto.storage.repository import StorageRepository
from quilto.agents.models import (
    RetrievalAttempt,
    RetrieverInput,
    RetrieverOutput,
)

# In models.py - add these imports
from typing import Any
from pydantic import BaseModel, ConfigDict, Field

# Entry and DateRange should NOT be re-exported from agents.models
# They belong to storage.models
```

### What This Story Does

This story implements the Retriever agent which is the data-fetching component of the query flow. It:
1. Receives retrieval instructions from Planner (not from LLM)
2. Executes retrieval using StorageRepository methods
3. Applies vocabulary expansion for better search coverage
4. Returns all matching entries without filtering/judging relevance
5. Tracks retrieval attempts for debugging/transparency

### What This Story Does NOT Include

- LLM calls - Retriever is pure retrieval, no LLM involved
- Relevance filtering - that's Analyzer's job
- Strategy creation - that's Planner's job
- Result analysis - that's Analyzer's job

### Key Design Decision: No LLM

Unlike Router, Parser, and Planner which all use LLM calls, the Retriever is **deterministic**:
- It receives explicit instructions from Planner
- It executes those instructions against StorageRepository
- No judgment calls are made
- This is intentional per agent-system-design.md Section 7.1

### Architecture Position

From agent-system-design.md:
```
Router -> BUILD_CONTEXT -> Planner -> Retriever -> Analyzer
```

**State Machine Transitions:**
```
RETRIEVE -> ANALYZE (entries found)
RETRIEVE -> PLAN (no entries, re-plan with gaps)
```

### Retriever Input Model

```python
class RetrieverInput(BaseModel):
    """Input to Retriever agent.

    Attributes:
        instructions: Retrieval instructions from Planner's retrieval_instructions.
            Structure: [{"strategy": str, "params": dict, "sub_query_id": int}, ...]
        vocabulary: Term normalization mapping for vocabulary expansion.
        max_entries: Maximum entries to return (safety limit).
    """

    model_config = ConfigDict(strict=True)

    instructions: list[dict[str, Any]]  # From Planner's retrieval_instructions
    # Structure: [{"strategy": str, "params": dict, "sub_query_id": int}, ...]
    vocabulary: dict[str, str] = Field(default_factory=dict)  # For term expansion
    max_entries: int = Field(default=100, ge=1)  # Safety limit
```

### Retriever Output Model

```python
class RetrieverOutput(BaseModel):
    """Output from Retriever agent.

    Attributes:
        entries: Retrieved entries (deduplicated, up to max_entries).
        retrieval_summary: Record of each retrieval attempt.
        total_entries_found: Total entries before deduplication and truncation.
        date_range_covered: Actual date range of returned entries.
        warnings: List of warning messages (empty results, truncation, errors).
        truncated: True if results were limited by max_entries.
    """

    model_config = ConfigDict(strict=True)

    entries: list[Entry]
    retrieval_summary: list[RetrievalAttempt]
    total_entries_found: int = Field(ge=0)
    date_range_covered: DateRange | None = None
    warnings: list[str] = Field(default_factory=list)
    truncated: bool = False
```

### RetrievalAttempt Model

```python
class RetrievalAttempt(BaseModel):
    """Record of a single retrieval attempt.

    Attributes:
        attempt_number: Sequential number of this attempt (1-based).
        strategy: The strategy used ("date_range", "keyword", "topical").
        params: Strategy-specific parameters used.
        entries_found: Number of entries returned.
        summary: Brief human-readable description of the attempt.
        expanded_terms: Terms after vocabulary expansion (for keyword/topical).
    """

    model_config = ConfigDict(strict=True)

    attempt_number: int = Field(ge=1)
    strategy: str = Field(min_length=1)  # "date_range", "keyword", "topical"
    params: dict[str, Any]  # Strategy-specific parameters
    entries_found: int = Field(ge=0)
    summary: str = Field(min_length=1)  # Brief description
    expanded_terms: list[str] = Field(default_factory=list)  # For keyword/topical strategies
```

**Note:** `expanded_terms` tracks which terms were actually searched after vocabulary expansion. This aids debugging and transparency.

### Vocabulary Expansion Logic

When executing KEYWORD or TOPICAL strategies:

```python
def expand_terms(
    terms: list[str],
    vocabulary: dict[str, str],
    semantic_expansion: bool = False,
) -> list[str]:
    """Expand terms using vocabulary mapping.

    Args:
        terms: Original search terms.
        vocabulary: Term normalization mapping (abbreviation -> full form).
        semantic_expansion: If True, include related terms more aggressively.

    Returns:
        Expanded list of terms (deduplicated).

    Example:
        vocabulary = {"pr": "personal record", "bench": "bench press"}
        terms = ["pr", "bench"]
        result = ["pr", "personal record", "bench", "bench press"]
    """
    expanded = []
    for term in terms:
        expanded.append(term)
        # Add expansion if exists
        if term.lower() in vocabulary:
            expanded.append(vocabulary[term.lower()])
        # Also check if term is a value (reverse lookup)
        for k, v in vocabulary.items():
            if term.lower() == v.lower() and k not in expanded:
                expanded.append(k)

    # If semantic_expansion is True, add more related terms
    if semantic_expansion:
        # Add partial matches from vocabulary values
        for k, v in vocabulary.items():
            for term in terms:
                if term.lower() in v.lower() and v not in expanded:
                    expanded.append(v)
                    expanded.append(k)

    return list(set(expanded))  # Deduplicate
```

**`semantic_expansion` Behavior:**
- When `False` (default): Only exact vocabulary matches are expanded
- When `True`: More aggressive expansion including partial matches and related terms
- This is controlled by the `semantic_expansion` param in retrieval_params, NOT by StorageRepository

### Strategy Execution Patterns

| Strategy | StorageRepository Method | Retriever Params | Notes |
|----------|--------------------------|------------------|-------|
| `date_range` | `get_entries_by_date_range(start, end)` | `start_date`, `end_date` | Direct date-based retrieval |
| `keyword` | `search_entries(keywords, date_range)` | `keywords`, `semantic_expansion`, `date_range` (optional) | `semantic_expansion` handled by Retriever's vocabulary expansion BEFORE calling storage |
| `topical` | `search_entries(topics + related, date_range)` | `topics`, `related_terms`, `date_range` (optional) | Topics + related_terms combined into keywords for storage search |

**Important:** The `StorageRepository.search_entries()` method signature is:
```python
def search_entries(
    self,
    keywords: list[str],
    date_range: DateRange | None = None,
    match_all: bool = False,
) -> list[Entry]:
```

Retriever handles `semantic_expansion` by expanding terms via vocabulary BEFORE calling storage. The storage layer does simple keyword matching; intelligence is in the Retriever.

### Deduplication Strategy

When multiple instructions are processed, entries may overlap:
- Use entry.id for deduplication
- Maintain order by timestamp
- Keep first occurrence (earlier instruction wins)

```python
seen_ids: set[str] = set()
unique_entries: list[Entry] = []
for entry in all_entries:
    if entry.id not in seen_ids:
        seen_ids.add(entry.id)
        unique_entries.append(entry)
```

### Warning Generation

| Condition | Warning Message |
|-----------|-----------------|
| Instruction returns 0 entries | "Retrieval instruction {n} ({strategy}) returned 0 entries" |
| Hit max_entries limit | "Results truncated: {total} entries found, returning {max_entries}" |
| Unknown strategy | "Unknown strategy '{strategy}' in instruction {n}, skipping" |
| Missing required params | "Missing required param '{param}' for {strategy} in instruction {n}" |

### Test Organization

```python
class TestRetrievalAttempt:
    """Tests for RetrievalAttempt model."""
    def test_valid_attempt(self): ...
    def test_required_fields(self): ...
    def test_attempt_number_minimum(self): ...  # ge=1
    def test_entries_found_minimum(self): ...  # ge=0
    def test_strategy_min_length(self): ...  # min_length=1
    def test_summary_min_length(self): ...  # min_length=1
    def test_expanded_terms_default_empty(self): ...


class TestRetrieverInput:
    """Tests for RetrieverInput model."""
    def test_default_max_entries(self): ...  # 100
    def test_custom_max_entries(self): ...
    def test_max_entries_minimum(self): ...  # ge=1
    def test_empty_instructions_valid(self): ...
    def test_vocabulary_default_empty_dict(self): ...


class TestRetrieverOutput:
    """Tests for RetrieverOutput model."""
    def test_empty_entries_valid(self): ...
    def test_truncated_flag(self): ...
    def test_warnings_default_empty(self): ...
    def test_total_entries_found_minimum(self): ...  # ge=0
    def test_date_range_covered_optional(self): ...


class TestRetrieverDateRange:
    """Tests for DATE_RANGE strategy."""
    async def test_date_range_retrieval(self, mock_storage): ...
    async def test_date_range_empty_result(self, mock_storage): ...


class TestRetrieverKeyword:
    """Tests for KEYWORD strategy."""
    async def test_keyword_retrieval(self, mock_storage): ...
    async def test_vocabulary_expansion(self, mock_storage): ...
    async def test_vocabulary_expansion_reverse_lookup(self, mock_storage): ...
    async def test_semantic_expansion_false(self, mock_storage): ...
    async def test_semantic_expansion_true(self, mock_storage): ...
    async def test_expanded_terms_in_attempt(self, mock_storage): ...


class TestRetrieverTopical:
    """Tests for TOPICAL strategy."""
    async def test_topical_retrieval(self, mock_storage): ...
    async def test_related_terms_included(self, mock_storage): ...


class TestRetrieverMultiInstruction:
    """Tests for multi-instruction processing."""
    async def test_multiple_instructions(self, mock_storage): ...
    async def test_deduplication(self, mock_storage): ...
    async def test_order_preservation(self, mock_storage): ...


class TestRetrieverLimits:
    """Tests for limits and warnings."""
    async def test_max_entries_truncation(self, mock_storage): ...
    async def test_max_entries_boundary_exact(self, mock_storage): ...
    async def test_empty_result_warning(self, mock_storage): ...
    async def test_unknown_strategy_warning(self, mock_storage): ...
    async def test_missing_required_param_warning(self, mock_storage): ...
    async def test_invalid_date_format_warning(self, mock_storage): ...


class TestRetrieverIntegration:
    """Integration tests with real StorageRepository."""
    async def test_real_date_range(self, tmp_path): ...
    async def test_real_keyword_search(self, tmp_path): ...
```

### Common Mistakes to Avoid (from project-context.md + Epic 2-3 learnings)

| Mistake | Correct Pattern | Story Source |
|---------|-----------------|--------------|
| Required string without length check | `Field(min_length=1)` | 2-4 |
| Numeric fields without bounds | `Field(ge=0)` or `Field(ge=1)` for counts | 2-4 |
| Missing boundary value tests | Test exact boundaries (0, 1, 100, max_entries) | 2-1, 2-2 |
| Empty list not tested | Test empty instructions, empty results | 2-2 |
| Missing `__all__` in `__init__.py` | Export all public classes | 1.5-8 |
| Not running `make test-ollama` | Run before marking done | Epic 2 retro |
| Forgetting Entry is in storage.models | Import from `quilto.storage.models` | 2-1 |
| Missing `ConfigDict(strict=True)` | Add to all Pydantic models | 3-2 |
| Using `= []` instead of `Field(default_factory=list)` | Use factory for mutable defaults | 3-2 |

### Pre-Review Checklist (from Epic 2 Retrospective)

Before requesting code review, verify:

- [ ] `make check` passes (lint + typecheck)
- [ ] `make test-ollama` passes (integration tests)
- [ ] All new functions have Google-style docstrings
- [ ] All new classes exported in `__init__.py` with `__all__`
- [ ] Required string fields use `Field(min_length=1)`
- [ ] Empty list cases tested
- [ ] No regression in existing tests (run full suite)

### Validation Commands

```bash
# During development
make check                    # lint + typecheck

# Before marking complete (REQUIRED)
make validate                 # lint + format + typecheck + unit tests
make test-ollama              # Integration tests with real Ollama
```

### Error Handling

| Error Case | Expected Behavior | Test Example |
|------------|-------------------|--------------|
| Empty instructions | Return empty entries | Valid input, no work done |
| Invalid date format | Skip instruction with warning | Log warning, continue |
| Storage error | Log error, add to warnings | Exception caught |
| Unknown strategy | Skip with warning | Warning added |

### Dependencies

| Dependency | Status | Notes |
|------------|--------|-------|
| StorageRepository | Done (2-1) | Use existing interface |
| Entry model | Done (2-1) | Import from storage.models |
| DateRange model | Done (2-1) | Import from storage.models |
| PlannerOutput | Done (3-2) | Provides retrieval_instructions |
| pytest fixtures | Done (2-2) | Use tmp_path for storage tests |

### Architecture Compliance

**From architecture.md:**
- Retriever is low-medium tier (minimal judgment)
- Does NOT use LLM - pure retrieval
- Returns all entries in scope (no filtering)
- Uses vocabulary expansion

### Epic 3 Context

This is the third story of Epic 3: Query & Retrieval. It enables query execution by fetching entries from storage.

**Epic 3 Dependencies:**
- Story 3-1 (Router QUERY/BOTH) - **Done** - Provides classification
- Story 3-2 (Planner) - **Done** - Provides retrieval_instructions
- Story 3-3 (Retriever) - **This story** - Executes retrieval
- Story 3-4 (Running domain) - Independent

### Previous Story Intelligence (from 3-2)

**Patterns to follow:**
- Agent class with `AGENT_NAME` constant
- Async main method returning Pydantic output
- Comprehensive unit tests + integration tests
- Export all new types in `__all__`
- Google-style docstrings throughout

**Code patterns established:**
- Use `Field(min_length=1)` for required strings
- Use `Field(default_factory=list)` for list defaults
- Test boundary values (0, 1, max)
- Test both valid and invalid inputs

**Testing patterns:**
- Class-based test organization by feature
- Mock dependencies for unit tests
- Real storage for integration tests
- Use pytest fixtures extensively

### Git Intelligence (from recent commits)

Recent commits show:
- Story 3-2 implemented PlannerAgent with same patterns we'll follow
- Story 3-1 extended Router - patterns established
- Epic 2 stories created the StorageRepository we'll use
- Integration tests with real Ollama are required

### References

- [Source: epics.md#Story-3.3] Story definition
- [Source: agent-system-design.md#7.1] Model C decision - read all in scope
- [Source: agent-system-design.md#11.4] RetrieverAgent interface
- [Source: agent-system-design.md#12.4] Retriever prompt (N/A - no LLM)
- [Source: state-machine-diagram.md] RETRIEVE state position
- [Source: project-context.md] Quilto vs Swealog separation
- [Source: 3-2-implement-planner-agent.md] Previous story patterns
- [Source: packages/quilto/quilto/storage/repository.py] StorageRepository interface

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

N/A

### Completion Notes List

- Implemented RetrieverAgent as a pure retrieval component (no LLM calls)
- Added comprehensive vocabulary expansion with `expand_terms()` function
- Support for three retrieval strategies: DATE_RANGE, KEYWORD, TOPICAL
- Multi-instruction processing with deduplication by entry.id
- Warning generation for empty results, truncation, unknown strategies, missing params
- 69 new tests added covering models and agent functionality
- All tests pass: `make validate` (653 passed) and `make test-ollama` (663 passed)

### File List

| File | Action | Description |
|------|--------|-------------|
| `packages/quilto/quilto/agents/models.py` | Modified | Added RetrievalAttempt, RetrieverInput, RetrieverOutput models; Fixed type annotations |
| `packages/quilto/quilto/agents/retriever.py` | Created | RetrieverAgent class with expand_terms function |
| `packages/quilto/quilto/agents/__init__.py` | Modified | Export RetrieverAgent, related models, and expand_terms |
| `packages/quilto/tests/test_retriever.py` | Created | 72 unit and integration tests |

### Senior Developer Review (AI)

**Reviewed by:** Amelia (Dev Agent)
**Date:** 2026-01-12

**Issues Found and Fixed:**

| Severity | Issue | Status |
|----------|-------|--------|
| HIGH | `RetrieverOutput.entries` used `list[Any]` without explanation | Fixed - added comment explaining circular import constraint |
| HIGH | `RetrieverOutput.date_range_covered` used `Any` without explanation | Fixed - added comment explaining circular import constraint |
| HIGH | `expand_terms` function not exported from agents module | Fixed - added to `__init__.py` and `__all__` |
| MEDIUM | Test deduplication assertion was always True | Fixed - uses proper set comparison |
| MEDIUM | Missing test for non-matching vocabulary | Fixed - added test |
| MEDIUM | Missing test for all instructions failing | Fixed - added test |
| LOW | Unused `sub_query_id` parameter | Noted - intentional for future use |
| LOW | Integration test data is fitness-specific | Noted - acceptable for this story |

**Note on Type Annotations:**
The `Any` type in `RetrieverOutput` is required due to circular import: `storage.repository` imports `ParserOutput` from `agents.models`. Attempting to import `Entry` and `DateRange` from `storage.models` causes circular import error. The comments now document this constraint.

**Verification:**
- `make validate`: 655 passed
- `make test-ollama`: 665 passed

**Outcome:** Approved with fixes applied
