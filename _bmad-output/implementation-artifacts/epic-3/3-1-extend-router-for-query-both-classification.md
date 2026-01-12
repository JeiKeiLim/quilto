# Story 3.1: Extend Router for QUERY/BOTH Classification

Status: done

## Story

As a **Quilto developer**,
I want **Router to handle QUERY and BOTH input types with domain selection**,
So that **queries are routed correctly with relevant domains identified**.

## Acceptance Criteria

1. **Given** a query input containing question words (why, how, what, when, which) or question marks
   **When** Router processes it
   **Then** it returns `input_type: QUERY` with confidence score >= 0.7
   **And** `selected_domains` contains domains matching the query content
   **And** `domain_selection_reasoning` explains why each domain was selected

2. **Given** a query input and a list of available domains
   **When** Router selects domains
   **Then** domain selection matches input keywords/topics against domain descriptions
   **And** when uncertain, broader selection is preferred over missing relevant domains
   **And** multi-domain queries (e.g., "compare running with lifting") select multiple domains

3. **Given** a BOTH input that logs something AND asks a question
   **When** Router processes it
   **Then** it returns `input_type: BOTH`
   **And** `log_portion` contains the complete declarative statement portion
   **And** `query_portion` contains the complete question portion
   **And** `selected_domains` includes domains relevant to BOTH portions
   **And** portions are correctly extracted preserving original wording

4. **Given** a complex query spanning multiple topics
   **When** Router processes it
   **Then** all relevant domains are selected (not just the first match)
   **And** domain_selection_reasoning mentions each selected domain
   **And** confidence reflects certainty of the multi-domain match

5. **Given** Router processes a QUERY or BOTH input
   **When** the input mentions topics outside available domains
   **Then** `selected_domains` may be empty if no domain matches
   **And** `domain_selection_reasoning` explains why no domains matched
   **And** classification still succeeds (domain selection is independent of classification)

6. **Given** the existing Router tests from Story 2-2
   **When** all new tests are added
   **Then** existing LOG, CORRECTION, and validation tests still pass
   **And** no regression in existing functionality

7. **Given** integration tests with real Ollama
   **When** run with `--use-real-ollama` flag
   **Then** QUERY classification returns expected input_type with appropriate domains
   **And** BOTH classification returns both portions with appropriate domains
   **And** multi-domain queries select multiple relevant domains

## Tasks / Subtasks

- [x] Task 1: Enhance domain selection logic in Router prompt (AC: #2, #4)
  - [x] Update `build_prompt()` to emphasize multi-domain selection for complex queries
  - [x] Add examples of multi-domain scenarios to the prompt
  - [x] Add instruction for reasoning about each selected domain

- [x] Task 2: Add QUERY-specific test cases (AC: #1, #5)
  - [x] Test QUERY with question words: "why", "how", "what", "when", "which"
  - [x] Test QUERY with question mark only
  - [x] Test QUERY with complex multi-part questions
  - [x] Test QUERY selecting single relevant domain
  - [x] Test QUERY with no matching domains (returns empty selection)
  - [x] Test QUERY confidence is >= 0.7 for clear queries
  - [x] Test QUERY confidence boundary at exactly 0.7 (boundary value test)

- [x] Task 3: Add BOTH-specific test cases (AC: #3)
  - [x] Test BOTH with log statement then question
  - [x] Test BOTH with question then log statement
  - [x] Test BOTH with interleaved log and question
  - [x] Test BOTH portion extraction preserves exact wording
  - [x] Test BOTH selects domains relevant to both portions
  - [x] Test BOTH confidence score

- [x] Task 4: Add multi-domain selection tests (AC: #2, #4)
  - [x] Test selecting 2 domains for cross-domain query
  - [x] Test selecting 3+ domains for ambiguous/broad query
  - [x] Test domain_selection_reasoning mentions each selected domain (validates AC #4 explicitly)
  - [x] Test broader selection when confidence is lower
  - [x] Test uncertain query triggers broader domain selection (validates "prefer broader over missing")

- [x] Task 5: Add integration tests for QUERY/BOTH with real Ollama (AC: #7)
  - [x] Test real QUERY classification with single domain
  - [x] Test real QUERY classification with multiple domains
  - [x] Test real BOTH classification with portion extraction
  - [x] Test real multi-domain query selection
  - [x] Use `pytest.mark.asyncio` and `--use-real-ollama` fixture

- [x] Task 6: Verify no regression (AC: #6)
  - [x] Run full test suite: `make validate`
  - [x] Run integration tests: `make test-ollama`
  - [x] Verify all existing LOG, CORRECTION tests still pass (existing tests in `test_router.py` ARE regression tests)
  - [x] Verify validation tests still pass
  - [x] **Note:** No new regression test class needed - existing tests serve as regression suite

## Dev Notes

### What This Story Does NOT Include

This story extends the existing Router implementation from Story 2-2. It does **NOT**:
- Change the `RouterOutput` model structure (already complete)
- Add new input types (LOG, QUERY, BOTH, CORRECTION already exist)
- Implement Planner agent (that's Story 3-2)
- Implement state machine orchestration (framework-level, later stories)

The Router already handles all input types. This story ensures QUERY and BOTH handling is production-ready with comprehensive tests.

### Existing Router Implementation (Story 2-2)

**Location:** `packages/quilto/quilto/agents/router.py`

The current implementation already:
- Classifies LOG, QUERY, BOTH, CORRECTION
- Selects domains based on input
- Extracts log_portion and query_portion for BOTH
- Uses `complete_structured()` with RouterOutput schema

**What needs enhancement:**
1. Prompt improvements for better multi-domain selection
2. Additional test coverage for QUERY and BOTH scenarios
3. Integration tests with real LLM for QUERY/BOTH paths

### Router Prompt Enhancement

The current prompt already includes domain selection rules. Enhance with:

```
=== MULTI-DOMAIN SELECTION ===

For complex queries that span multiple topics:
- Select ALL domains that are relevant, not just the primary one
- Example: "Compare my running pace with my lifting progress" → [running, strength]
- Example: "How does my diet affect my workouts?" → [nutrition, strength]
- When uncertain, include more domains rather than fewer

For BOTH input type:
- Select domains relevant to BOTH the log and query portions
- Log portion may reference different domains than query portion
```

### Test Organization

Add tests to `packages/quilto/tests/test_router.py`:

```python
class TestQueryClassification:
    """Tests for QUERY input type classification and domain selection."""

    async def test_query_question_word_why(self, mock_llm): ...
    async def test_query_question_word_how(self, mock_llm): ...
    async def test_query_question_word_what(self, mock_llm): ...
    async def test_query_question_word_when(self, mock_llm): ...
    async def test_query_question_word_which(self, mock_llm): ...
    async def test_query_question_mark_only(self, mock_llm): ...
    async def test_query_complex_multipart(self, mock_llm): ...
    async def test_query_single_domain_selection(self, mock_llm): ...
    async def test_query_no_domain_match(self, mock_llm): ...
    async def test_query_confidence_threshold(self, mock_llm): ...
    async def test_query_confidence_at_exact_boundary_0_7(self, mock_llm): ...  # Boundary test


class TestBothClassification:
    """Tests for BOTH input type with log and query portions."""

    async def test_both_log_then_question(self, mock_llm): ...
    async def test_both_question_then_log(self, mock_llm): ...
    async def test_both_interleaved(self, mock_llm): ...
    async def test_both_portion_preservation(self, mock_llm): ...
    async def test_both_multi_domain_selection(self, mock_llm): ...
    async def test_both_confidence_score(self, mock_llm): ...


class TestMultiDomainSelection:
    """Tests for selecting multiple domains for complex queries."""

    async def test_two_domain_cross_query(self, mock_llm): ...
    async def test_three_domain_broad_query(self, mock_llm): ...
    async def test_reasoning_mentions_each_domain(self, mock_llm): ...
    async def test_broader_selection_lower_confidence(self, mock_llm): ...
    async def test_uncertain_query_triggers_broader_selection(self, mock_llm): ...  # "prefer broader over missing"
```

**Note:** Existing tests from Story 2-2 serve as regression tests - no separate regression class needed.

### Integration Test Requirements

**From Epic 2 Retrospective:** `make test-ollama` must pass before story completion.

Integration tests verify real LLM behavior. Uses fixture from `packages/quilto/tests/conftest.py`:

```python
class TestRouterQueryIntegration:
    """Integration tests for QUERY/BOTH with real Ollama.

    Run with: pytest --use-real-ollama -k TestRouterQueryIntegration
    Or via: make test-ollama
    """

    @pytest.mark.asyncio
    async def test_real_query_single_domain(self, use_real_ollama: bool) -> None:
        """Test QUERY classification with single domain using real Ollama."""
        if not use_real_ollama:
            pytest.skip("Requires --use-real-ollama flag")
        # Test: "How has my bench press progressed?"
        # Expected: QUERY, selected_domains includes "strength"

    @pytest.mark.asyncio
    async def test_real_query_multi_domain(self, use_real_ollama: bool) -> None:
        """Test QUERY classification with multiple domains using real Ollama."""
        if not use_real_ollama:
            pytest.skip("Requires --use-real-ollama flag")
        # Test: "Compare my running with my lifting this month"
        # Expected: QUERY, selected_domains includes both "running" and "strength"

    @pytest.mark.asyncio
    async def test_real_both_classification(self, use_real_ollama: bool) -> None:
        """Test BOTH classification with portion extraction using real Ollama."""
        if not use_real_ollama:
            pytest.skip("Requires --use-real-ollama flag")
        # Test: "Ran 5k today in 25 mins. Is that good progress?"
        # Expected: BOTH, log_portion about running, query_portion is question

    @pytest.mark.asyncio
    async def test_real_multi_domain_query_selection(self, use_real_ollama: bool) -> None:
        """Test multi-domain query selection using real Ollama."""
        if not use_real_ollama:
            pytest.skip("Requires --use-real-ollama flag")
        # Test: "How does my diet affect my strength training?"
        # Expected: QUERY, selected_domains includes both "nutrition" and "strength"
```

**Fixture Reference:** The `use_real_ollama` fixture is defined in `packages/quilto/tests/conftest.py` (created in Story 2-2).

### Project Structure Notes

**Package:** `packages/quilto/quilto/agents/` (Quilto framework, domain-agnostic)

**Files to modify:**
- `packages/quilto/quilto/agents/router.py` - Enhance prompt
- `packages/quilto/tests/test_router.py` - Add new test classes

**Files unchanged:**
- `packages/quilto/quilto/agents/models.py` - RouterOutput already correct
- `packages/quilto/quilto/agents/__init__.py` - Exports already complete

### Common Mistakes to Avoid (from project-context.md + Epic 2 Retrospective)

| Mistake | Correct Pattern | Story Source |
|---------|-----------------|--------------|
| Required string without length check | `Field(min_length=1)` | 2-4 |
| Redundant `@field_validator` for range | Use `Field(ge=0, le=10)` instead | 2-4 |
| Missing boundary value tests | Test exact boundaries (0.0, 0.7, 1.0) | 2-1, 2-2 |
| Missing `py.typed` marker | Add marker file (already exists from 2-2) | 2-2 |
| Empty string not tested separately | Test both `None` and `""` cases | 2-2 |
| Missing `__all__` in `__init__.py` | Export all public classes (already complete) | 1.5-8 |
| Both `Field()` AND `@field_validator` | Use only `Field(ge=, le=)` for range | 2-4 |
| Not running `make test-ollama` | Run before marking done | Epic 2 retro |

**This Story Specifically:**
- Test confidence at 0.7 boundary (AC #1)
- Test empty domain list returns empty selection (AC #5)
- Verify `domain_selection_reasoning` mentions each domain (AC #4)

### Pre-Review Checklist (from Epic 2 Retrospective Action Item #3)

Before requesting code review, verify:

- [x] `make check` passes (lint + typecheck)
- [x] `make test-ollama` passes (integration tests)
- [x] All new functions have Google-style docstrings
- [x] Boundary value tests exist (0.0, 0.7, 1.0 for confidence)
- [x] Empty string cases tested where applicable
- [x] `domain_selection_reasoning` mentions each selected domain (AC #4 validation)
- [x] All QUERY tests have confidence >= 0.7 (AC #1)
- [x] All BOTH tests have both portions extracted (AC #3)
- [x] No regression in existing tests (run full suite)

### Validation Commands

```bash
# During development
make check                    # lint + typecheck

# Before marking complete (REQUIRED)
make validate                 # lint + format + typecheck + unit tests
make test-ollama              # Integration tests with real Ollama
```

### References

- [Source: epics.md#Story-3.1] Story definition
- [Source: 2-2-implement-router-agent-log-classification.md] Previous Router story
- [Source: agent-system-design.md#8.4] Domain selection mechanism
- [Source: state-machine-diagram.md] ROUTE → BUILD_CONTEXT transition
- [Source: project-context.md] Quilto vs Swealog separation
- [Source: retro-2026-01-12.md] Epic 2 learnings

### Previous Story Intelligence (Story 2-2)

**Completion Notes from 2-2:**
- RouterAgent implemented with `classify()` method
- `InputType` enum: LOG, QUERY, BOTH, CORRECTION
- `@model_validator` for BOTH requires portions, CORRECTION requires target
- 36 tests (34 passed, 2 skipped integration tests)
- Public `build_prompt()` for testability

**Code Review Fixes Applied:**
- `py.typed` marker added for PEP 561
- `conftest.py` with `--use-real-ollama` hook
- Empty string validation tests added

### Dependencies

| Dependency | Status | Notes |
|------------|--------|-------|
| RouterAgent | Done (2-2) | Extend, don't rewrite |
| RouterOutput model | Done (2-2) | No changes needed |
| LLMClient | Done (1-3) | Use existing interface |
| pytest fixtures | Done (2-2) | Use existing mock_llm |

### Architecture Compliance

**From architecture.md:**
- Router is low-tier agent (tier: "low")
- Uses LiteLLM via LLMClient abstraction
- Returns structured Pydantic output (RouterOutput)

**State Machine Position:**
```
ROUTE → BUILD_CONTEXT (always, domains selected)
BUILD_CONTEXT → PLAN (if QUERY)
BUILD_CONTEXT → PLAN + PARSE (if BOTH)
```

Router's QUERY/BOTH classification determines the downstream flow.

### Error Handling

| Error Case | Expected Behavior |
|------------|-------------------|
| QUERY with no matching domains | Return empty selected_domains (valid) |
| BOTH with unclear separation | LLM extracts best-effort portions |
| Low confidence classification | Still return result, caller decides |

### Epic 3 Context

This is the first story of Epic 3: Query & Retrieval. It enables the query flow by ensuring Router correctly identifies QUERY/BOTH inputs and selects appropriate domains.

**Epic 3 Dependencies:**
- Story 3-2 (Planner) depends on Router QUERY classification
- Story 3-3 (Retriever) depends on Router domain selection
- Story 3-4 (Running domain) is independent

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

N/A

### Completion Notes List

1. **Task 1 (AC: #2, #4)**: Enhanced Router prompt with MULTI-DOMAIN SELECTION section:
   - Added examples for multi-domain queries (e.g., "Compare running with lifting" → ["running", "strength"])
   - Added instruction for BOTH type to select domains for both portions
   - Added explicit instruction that domain_selection_reasoning must mention each selected domain

2. **Task 2 (AC: #1, #5)**: Added 11 QUERY test cases in `TestQueryClassification` class:
   - Tests for all 5 question words: why, how, what, when, which
   - Test for question mark only
   - Test for complex multi-part questions
   - Test for single domain selection
   - Test for no domain match (returns empty selection)
   - Test for confidence threshold (>= 0.7)
   - Boundary test at exactly 0.7 confidence

3. **Task 3 (AC: #3)**: Added 6 BOTH test cases in `TestBothClassification` class:
   - Test log then question order
   - Test question then log order
   - Test interleaved content
   - Test portion preservation (exact wording)
   - Test multi-domain selection for both portions
   - Test confidence score

4. **Task 4 (AC: #2, #4)**: Added 5 multi-domain tests in `TestMultiDomainSelection` class:
   - Test 2-domain cross-domain query
   - Test 3+ domain broad query
   - Test reasoning mentions each selected domain (AC #4 validation)
   - Test broader selection with lower confidence
   - Test uncertain query triggers broader selection ("prefer broader over missing")

5. **Task 5 (AC: #7)**: Added 4 integration tests in `TestRouterQueryIntegration` class:
   - Real QUERY single domain test
   - Real QUERY multi-domain test
   - Real BOTH classification test
   - Real multi-domain query selection test

6. **Task 6 (AC: #6)**: Verified no regression:
   - `make validate`: All 534 unit tests pass (11 skipped integration tests)
   - `make test-ollama`: All 541 tests pass (4 skipped)
   - All existing LOG, CORRECTION tests still pass

7. **Additional fix**: Added `# noqa: E402` to `scripts/manual_test.py` imports to suppress lint warnings for intentional import ordering (path modification required before imports).

### File List

| File | Action | Description |
|------|--------|-------------|
| `packages/quilto/quilto/agents/router.py` | Modified | Enhanced prompt with MULTI-DOMAIN SELECTION section |
| `packages/quilto/tests/test_router.py` | Modified | Added 26 new tests (11 QUERY, 6 BOTH, 5 multi-domain, 4 integration); strengthened multi-domain assertions during code review |
| `scripts/manual_test.py` | Modified | Added noqa comments for E402 lint warnings |
| `_bmad-output/implementation-artifacts/sprint-status.yaml` | Modified | Updated story status tracking |

### Senior Developer Review (AI)

**Review Date:** 2026-01-12
**Reviewer:** Amelia (Dev Agent - Claude Opus 4.5)
**Outcome:** APPROVED (with fixes applied)

#### Review Summary

- **Validation:** `make check` ✅ | `make test-ollama` ✅ (541 passed, 4 skipped)
- **Issues Found:** 0 Critical, 3 Medium, 2 Low
- **Issues Fixed:** All Medium and Low issues addressed

#### Issues Identified and Fixed

1. **[MEDIUM] File List Missing sprint-status.yaml** - Added to File List
2. **[MEDIUM] Weak multi-domain test assertions** - Strengthened `test_real_query_multi_domain` and `test_real_multi_domain_query_selection` to assert BOTH expected domains are selected instead of just one
3. **[MEDIUM] Story Status premature** - Status was "done" before review completion (acceptable, now truly complete)
4. **[LOW] Pre-Review Checklist unchecked** - Updated to reflect completion
5. **[LOW] Epic-3 directory not documented** - Minor, directory is correctly created

#### AC Validation

| AC | Status | Evidence |
|----|--------|----------|
| AC #1 | ✅ | QUERY tests verify confidence >= 0.7, boundary test at exactly 0.7 |
| AC #2 | ✅ | Multi-domain tests, broader selection tests, reasoning mentions domains |
| AC #3 | ✅ | BOTH tests verify log_portion and query_portion extraction |
| AC #4 | ✅ | `test_reasoning_mentions_each_domain` validates domain_selection_reasoning |
| AC #5 | ✅ | `test_query_no_domain_match` returns empty selection with reasoning |
| AC #6 | ✅ | All 541 tests pass, no regression |
| AC #7 | ✅ | Integration tests with real Ollama pass |

