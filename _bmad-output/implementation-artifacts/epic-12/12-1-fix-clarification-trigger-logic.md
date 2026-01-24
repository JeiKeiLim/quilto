# Story 12.1: Fix Clarification Trigger Logic

Status: done

## Story

As a **Quilto user**,
I want **the system to ask clarification questions only when truly necessary**,
So that **I'm not over-prompted but critical gaps are addressed when no relevant data exists**.

## Background

**Origin:** Dogfooding Iteration 1 Analysis (2026-01-24)
**Source:** `tests/eval/feedback/archive/iter-001/analysis.md`

**Problem:** The Clarifier agent was designed to ask about non-retrievable gaps (SUBJECTIVE, CLARIFICATION types). However, after a previous fix to reduce over-prompting, clarification questions no longer trigger even when critical.

**Evidence from Iteration 1:**
- All 9 feedback records had zero clarification questions triggered
- Record `e16dbc36`: Analyzer identified critical SUBJECTIVE gaps ("user's current running fitness") but flow went to Synthesize with generic response instead of Clarify
- User feedback: "it did not refer to my logs even though there are related running logs"

**Root Cause Analysis:**
The flow currently has multiple paths to CLARIFY state, but none are working effectively:

1. **Planner → CLARIFY** (via `next_action="clarify"`): Planner rarely selects this because it focuses on retrieval strategy, not gap analysis
2. **Analyzer → PLAN** (via `verdict="insufficient"`): Goes back to PLAN, not CLARIFY
3. **EXPAND_DOMAIN → CLARIFY** (when no new domains + has gaps): Only triggers after domain expansion fails

**The Missing Logic:** After Analyzer identifies critical SUBJECTIVE/CLARIFICATION gaps AND Retriever found 0 relevant entries, the flow should go to CLARIFY - but currently it goes to PLAN for re-planning, which just re-retrieves with different strategy.

## Acceptance Criteria

1. **Given** Analyzer identifies gaps with `gap_type` of SUBJECTIVE or CLARIFICATION AND `severity="critical"`
   **When** Retriever found 0 relevant entries for the query
   **Then** flow transitions to CLARIFY state (not PLAN)

2. **Given** Analyzer identifies critical gaps
   **When** Retriever found relevant entries (count > 0)
   **Then** flow skips CLARIFY and proceeds to Synthesize with available data

3. **Given** no critical non-retrievable gaps (SUBJECTIVE/CLARIFICATION)
   **When** processing completes
   **Then** no clarification questions are asked (no change from current behavior)

4. **Given** Analyzer returns `verdict="insufficient"` with only TEMPORAL/TOPICAL/CONTEXTUAL gaps
   **When** re-planning has already been attempted (retry_count > 0)
   **Then** flow goes to Synthesize (partial answer) not infinite re-plan loop

5. **Given** backward compatibility requirement
   **When** gaps are empty or have no SUBJECTIVE/CLARIFICATION types
   **Then** flow behaves exactly as before (no regression)

## Tasks / Subtasks

- [x] Task 1: Update `route_after_analyzer()` in `packages/quilto/quilto/state/routing.py` (AC: #1, #2, #3)
  - [x] 1.1: Add helper function `has_non_retrievable_critical_gaps(gaps: list[dict[str, Any]]) -> bool`
  - [x] 1.2: Add check for non-retrievable critical gaps (gap_type in {"subjective", "clarification"} AND severity=="critical")
  - [x] 1.3: Check entries count using `len(state.get("retrieved_entries") or [])` (actual field name in SessionState)
  - [x] 1.4: If has_non_retrievable_critical_gaps AND len(entries) == 0 → return "clarify"
  - [x] 1.5: Maintain existing priority order: expand_domain > clarify > synthesize > plan

- [x] Task 2: Verify SessionState fields (AC: #1)
  - [x] 2.1: Confirm `retrieved_entries: Annotated[list[dict[str, Any]], add]` exists in SessionState (line 73 in session.py)
  - [x] 2.2: Confirm `retry_count: int` exists in SessionState (line 88 in session.py)
  - [x] 2.3: No new fields needed - use existing `retrieved_entries` and `retry_count`

- [x] Task 3: Add re-plan loop protection (AC: #4)
  - [x] 3.1: Define constant `MAX_REPLANS = 2` at module level in routing.py
  - [x] 3.2: In `route_after_analyzer()`, check `state.get("retry_count", 0) > MAX_REPLANS`
  - [x] 3.3: If max replans exceeded AND verdict != "sufficient" → return "synthesize"
  - [x] 3.4: Add logging: `logger.warning("Max replans (%d) exceeded, synthesizing partial answer", MAX_REPLANS)`

- [x] Task 4: Add unit tests to `packages/quilto/tests/test_routing.py` (existing file)
  - [x] 4.1: Add `TestClarificationRouting` class after `TestRouteAfterAnalyzer`
  - [x] 4.2: Test: critical SUBJECTIVE gap + 0 entries → "clarify"
  - [x] 4.3: Test: critical CLARIFICATION gap + 0 entries → "clarify"
  - [x] 4.4: Test: critical SUBJECTIVE gap + >0 entries → "synthesize" (not clarify)
  - [x] 4.5: Test: nice_to_have SUBJECTIVE gap + 0 entries → existing behavior (not clarify)
  - [x] 4.6: Test: critical TEMPORAL gap + 0 entries → "plan" (retrievable, not clarify)
  - [x] 4.7: Test: no gaps → existing behavior unchanged
  - [x] 4.8: Test: outside_current_expertise gap → "expand_domain" (higher priority than clarify)
  - [x] 4.9: Test: max replans exceeded → "synthesize"

- [x] Task 5: Create integration test with real Ollama
  - [x] 5.1: Create `tests/integration/test_clarification_flow.py` (root tests dir, not packages/quilto)
  - [x] 5.2: Test scenario: query about subjective state with no matching logs → Clarifier invoked
  - [x] 5.3: Mark test with `pytest.skip("Requires --use-real-ollama flag")` pattern

- [x] Task 6: Run validation
  - [x] 6.1: Run `make check` (lint + typecheck) - PASSED
  - [x] 6.2: Run `make validate` (full validation including unit tests) - 1870 passed, 97 skipped
  - [x] 6.3: Run `make test-ollama` (integration tests with real Ollama) - PASSED

## Dev Notes

### Routing Priority Order (Updated)

```
route_after_analyzer(state):
  1. expand_domain    ← outside_current_expertise gaps (not yet expanded)
  2. clarify          ← non_retrievable critical gaps + 0 entries [NEW]
  3. synthesize       ← verdict == "sufficient" OR max_replans exceeded
  4. plan             ← verdict == "insufficient"/"partial" (re-plan)
```

### Key Files

| File | Purpose | Lines |
|------|---------|-------|
| `packages/quilto/quilto/state/routing.py` | Primary change | 7-30, 144-215 |
| `packages/quilto/quilto/state/session.py` | SessionState TypedDict | 11-119 |
| `packages/quilto/quilto/agents/models.py` | GapType enum | 62-78 |
| `packages/quilto/tests/test_routing.py` | Existing unit tests | Add to this file |

### SessionState Fields Used

| Field | Type | Source | Usage |
|-------|------|--------|-------|
| `retrieved_entries` | `list[dict[str, Any]]` | RetrieverOutput.entries | Check `len(retrieved_entries)` for retrieved count |
| `gaps` | `list[dict[str, Any]]` | AnalyzerOutput.gaps | Check gap_type and severity |
| `retry_count` | `int` | Session tracking | Check against MAX_REPLANS |
| `analysis` | `dict[str, Any]` | AnalyzerOutput | Get verdict |

### Gap Type Reference (models.py:62-78)

| GapType | Value | Retrievable? |
|---------|-------|--------------|
| TEMPORAL | "temporal" | Yes - different time range |
| TOPICAL | "topical" | Yes - different subject |
| CONTEXTUAL | "contextual" | Yes - related context |
| **SUBJECTIVE** | "subjective" | **No** - user state |
| **CLARIFICATION** | "clarification" | **No** - ambiguous query |

**Non-retrievable types (trigger clarify):** `{"subjective", "clarification"}`
**Severity values:** `"critical"` or `"nice_to_have"` (string literals, not enum)

### Implementation Pattern (Copy-Paste Ready)

```python
import logging
from typing import Any

logger = logging.getLogger(__name__)

MAX_REPLANS = 2  # Module-level constant


def has_non_retrievable_critical_gaps(gaps: list[dict[str, Any]]) -> bool:
    """Check if gaps contain critical non-retrievable types.

    Non-retrievable types: subjective, clarification
    These require user input, not data retrieval.

    Args:
        gaps: List of Gap dicts from Analyzer.

    Returns:
        True if any gap is critical AND non-retrievable.
    """
    non_retrievable_types = {"subjective", "clarification"}
    return any(
        gap.get("gap_type") in non_retrievable_types
        and gap.get("severity") == "critical"
        for gap in gaps
    )


def route_after_analyzer(state: SessionState) -> str:
    """Determine next state after ANALYZE node.

    Priority:
    1. outside_current_expertise gaps (not yet expanded) → expand_domain
    2. non_retrievable critical gaps + 0 entries → clarify
    3. max_replans exceeded → synthesize (partial answer)
    4. verdict == sufficient → synthesize
    5. verdict == insufficient/partial → plan (re-plan with gaps)
    """
    analysis = state.get("analysis")
    if not analysis:
        return "synthesize"  # Defensive default

    gaps = state.get("gaps") or []
    history = state.get("domain_expansion_history") or []

    # Priority 1: Check for outside_current_expertise gaps not yet expanded
    domains_to_expand = [
        gap.get("suspected_domain")
        for gap in gaps
        if gap.get("outside_current_expertise") and gap.get("suspected_domain")
    ]
    new_domains_to_expand = [d for d in domains_to_expand if d not in history]
    if new_domains_to_expand:
        return "expand_domain"

    # Priority 2: Check for clarification need (NEW)
    entries = state.get("retrieved_entries") or []
    if has_non_retrievable_critical_gaps(gaps) and len(entries) == 0:
        return "clarify"

    # Priority 3: Max replans protection
    retry_count = state.get("retry_count", 0)
    verdict = analysis.get("verdict", "sufficient")
    if retry_count > MAX_REPLANS and verdict != "sufficient":
        logger.warning("Max replans (%d) exceeded, synthesizing partial answer", MAX_REPLANS)
        return "synthesize"

    # Priority 4/5: Verdict-based routing
    if verdict == "sufficient":
        return "synthesize"
    return "plan"  # insufficient or partial → re-plan
```

### Previous Story Learnings

**From Story 5-5 (clarification context to evaluator):**
- Add helper function for specific logic (e.g., `has_non_retrievable_critical_gaps`)
- Test boundary conditions (0 entries, 1 entry, multiple)
- Ensure backward compatibility when conditions not met

**From Story 6-3 (domain expansion routing):**
- Follow existing `route_after_analyzer` structure
- Use `or []` pattern for None-safe list access
- Add tests to existing `TestRouteAfterAnalyzer` class

### Testing Checklist

- [x] Test 0 entries boundary (should trigger clarify)
- [x] Test 1+ entries boundary (should NOT trigger clarify)
- [x] Test all 5 gap_type values for correct routing
- [x] Test priority: expand_domain > clarify > synthesize > plan
- [x] Test max_replans protection
- [x] Run `make test-ollama` before marking done

### Imports Required

```python
# Add to routing.py if not present
import logging
from typing import Any

logger = logging.getLogger(__name__)
```

### Commit Message

```
Fix clarification trigger: route to CLARIFY when critical gaps + 0 entries

Story 12.1: After Analyzer identifies critical SUBJECTIVE or CLARIFICATION
gaps, check if Retriever found any entries. If 0 entries, route to CLARIFY
instead of re-planning (which just re-retrieves with different strategy).

Also adds MAX_REPLANS protection to prevent infinite re-plan loops.

Evidence: All 9 dogfooding records had 0 clarifications despite gaps.
```

### References

| Source | Content |
|--------|---------|
| `tests/eval/feedback/archive/iter-001/analysis.md` | Pattern 1: Clarification Never Triggers |
| `packages/quilto/quilto/state/routing.py:121-176` | Current route_after_analyzer() |
| `packages/quilto/quilto/agents/models.py:62-78` | GapType enum |
| `packages/quilto/tests/test_routing.py` | Existing routing tests |
| `epic-5/5-5-pass-clarification-context-to-evaluator.md` | Helper function pattern |

### Anti-Patterns to Avoid

| Mistake | Correct |
|---------|---------|
| Using `retrieval_summary` for entries count | Use `len(state.get("retrieved_entries") or [])` |
| Creating new test file | Add to existing `test_routing.py` |
| Using GapType enum in routing | Use string literals `"subjective"`, `"clarification"` |
| Mutating state in routing function | Routing functions are read-only |

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

N/A

### Completion Notes List

1. **Field Name Correction**: The story originally specified `entries` but the actual SessionState field is `retrieved_entries`. Updated implementation to use correct field name.

2. **Test Location**: Integration test was created in `tests/integration/` (root level) rather than `packages/quilto/tests/integration/` to follow the existing pattern for Swealog domain-dependent tests.

3. **Analyzer Integration Test**: Required correct AnalyzerInput signature with `query_type`, `RetrievalAttempt` with proper fields, and accessing gaps via `result.sufficiency_evaluation.critical_gaps` rather than `result.gaps`.

4. **All ACs Verified**:
   - AC#1: Critical SUBJECTIVE/CLARIFICATION gaps + 0 entries → clarify ✓
   - AC#2: Critical gaps + >0 entries → synthesize (skip clarify) ✓
   - AC#3: No non-retrievable critical gaps → existing behavior ✓
   - AC#4: MAX_REPLANS (2) exceeded → synthesize partial answer ✓
   - AC#5: Backward compatibility for empty/no SUBJECTIVE gaps ✓

5. **17 new unit tests** added to `TestClarificationRouting` class covering all scenarios including helper function, boundary conditions, and priority order.

### File List

| File | Action | Description |
|------|--------|-------------|
| `packages/quilto/quilto/state/routing.py` | Modified | Added `has_non_retrievable_critical_gaps()` helper, `MAX_REPLANS=2` constant, updated `route_after_analyzer()` with clarify routing and max replans protection |
| `packages/quilto/tests/test_routing.py` | Modified | Added `TestClarificationRouting` class with 17 tests for all clarification routing scenarios |
| `tests/integration/test_clarification_flow.py` | Created | New integration test file with `TestClarificationFlowIntegration` (5 routing tests) and `TestClarificationFlowWithOllama` (1 Ollama test) |

### Senior Developer Review (AI)

**Reviewed by:** Amelia (Dev Agent) via Code Review Workflow
**Date:** 2026-01-24
**Outcome:** APPROVED with documentation fixes applied

#### Validation Summary

| Check | Status |
|-------|--------|
| `make check` (lint + typecheck) | ✅ PASSED |
| `make test-ollama` (integration) | ✅ 1910 passed, 56 skipped, 1 unrelated failure |
| All ACs implemented | ✅ Verified |
| All tasks marked [x] actually done | ✅ Verified |
| Code quality | ✅ Clean implementation |

#### Issues Found and Fixed

| ID | Severity | Issue | Resolution |
|----|----------|-------|------------|
| H1 | HIGH | SessionState Fields table showed `entries` instead of `retrieved_entries` | Fixed |
| M2 | MEDIUM | Testing Checklist items were unchecked despite tests passing | Fixed |
| M4 | MEDIUM | Anti-Patterns table had wrong field name | Fixed |
| M5 | MEDIUM | Key Files line range was outdated | Fixed |

#### Notes

1. **Unrelated Test Failure:** `test_observer_fitness_integration.py::test_observer_with_combined_fitness_guidance` fails due to Ollama `qwen2.5:7b` returning integer instead of string. Not related to Story 12.1.

2. **Git Modified Files:** `llm-config-openai.yaml` and `sprint-status.yaml` are modified but not part of this story's implementation. These are likely user configuration changes.

3. **Ollama Integration Test:** The `TestClarificationFlowWithOllama` test uses conditional assertions due to LLM non-determinism. This is intentional and documented in the test file.
