# Story 13.4: Fix Clarification Flow Routing

Status: done

## Story

As a **Quilto user**,
I want **the system to actually ask clarification questions when needed**,
So that **I can provide missing information for better responses**.

## Background

**Origin:** Dogfooding Iteration 3 (Epic 13)
**Source:** `tests/eval/feedback/archive/iter-002/analysis.md` - Pattern 10: Clarification Questions Not Asked
**Priority:** Medium | **Effort:** Small (1-2 hours)
**Type:** Bug Fix - Routing logic missing in pipeline

**Key Evidence (Record `8628f945`):**
- User query: "How do I do?" (vague follow-up after stating "I'd like to run a full marathon")
- Planner output: `next_action: "clarify"` with `clarify_questions` populated
- Actual behavior: Clarification questions were **never asked** - pipeline proceeded to Retriever → Analyzer → Synthesizer
- User feedback: "I saw Planner generated clarification question but it did not ask me a clarification questions"

**Root Cause:** `execute_query_pipeline()` has a **hardcoded linear flow** that ignores `planner_output.next_action`. The routing infrastructure exists in `packages/quilto/quilto/state/routing.py` but is NOT used in the current synchronous pipeline.

## Acceptance Criteria

1. **Given** Planner sets `next_action: "clarify"` with `clarify_questions` populated
   **When** the flow processes this output
   **Then** the pipeline returns early with `needs_clarification: True` and the questions (does not proceed to Retriever)

2. **Given** Planner generates clarification questions
   **When** the CLI receives them
   **Then** the questions are displayed to the user and an info message suggests re-querying with more detail

3. **Given** a vague query like "How do I do?"
   **When** Planner identifies critical subjective/clarification gaps
   **Then** the user receives the clarification questions before a response is generated

4. **Given** Planner sets `next_action: "retrieve"` (normal case)
   **When** the flow processes this output
   **Then** the pipeline proceeds to Retriever as before (no regression)

## Tasks / Subtasks

- [x] Task 1: Modify `execute_query_pipeline()` to check Planner's `next_action` (AC: #1, #4)
  - [x] 1.1: After Planner step, check `planner_output.next_action`
  - [x] 1.2: If `next_action == "clarify"` and `clarify_questions` is truthy (not None and not empty), return early with clarification result
  - [x] 1.3: Add `needs_clarification: bool` and `clarification_questions: list[str] | None` to return dict
  - [x] 1.4: If `next_action == "retrieve"` or `"synthesize"`, proceed as normal (existing flow)
  - [x] 1.5: If `next_action == "expand_domain"`, proceed to retrieve for now (domain expansion out of scope)
  - [x] 1.6: Include `router` output in `intermediate_outputs` when returning early for debug consistency

- [x] Task 2: Update CLI `auto_cmd.py` to handle clarification (AC: #2, #3)
  - [x] 2.1: Check result for `needs_clarification: True`
  - [x] 2.2: If True, display clarification questions to user using rich.console
  - [x] 2.3: Print info message: "Please re-query with more specific details"
  - [x] 2.4: Return normally (exit code 0) - user re-queries with more context

- [x] Task 3: Add unit tests (AC: #1, #4)
  - [x] 3.1: In `packages/swealog/tests/test_api_routes.py`: Test `execute_query_pipeline` returns `needs_clarification: True` when Planner outputs `next_action="clarify"` with questions
  - [x] 3.2: Test condition logic for various `next_action` values
  - [x] 3.3: Test result dict always contains `needs_clarification` and `clarification_questions` fields
  - [x] 3.4: Test edge case: `next_action="clarify"` but `clarify_questions=[]` (should NOT return clarification)

- [x] Task 4: Run validation
  - [x] 4.1: Run `make check` (lint + typecheck)
  - [x] 4.2: Run `make validate` (full validation)

## Dev Notes

### Design Decision: Minimal Clarification (Phase 1)

This story implements **Phase 1** of clarification support:
- Return clarification questions to caller instead of proceeding with query
- CLI displays questions and exits (user re-queries with more detail)
- No interactive pause/resume flow

**Why this approach:**
1. **Minimal code change:** Add condition in pipeline, update return structure
2. **No state persistence:** Clarification is "fire and forget" (user provides context in next query)
3. **CLI simplicity:** Display questions, exit - user naturally re-queries with more info
4. **Foundation for Phase 2:** Can add interactive flow later (WAIT_USER state, LangGraph graph)

**Phase 2 (out of scope):**
- Interactive prompt for user to answer questions mid-flow
- Resume flow with user's answers
- Track `previous_clarifications` to avoid re-asking
- Full LangGraph integration with WAIT_USER state

### Implementation Approach

**File 1: `packages/swealog/swealog/api/routes/query.py`**

After Planner step (around line 154), add clarification check:

```python
# After: timer.log_output("Planner", planner_output.model_dump())

# Check if Planner requests clarification
if planner_output.next_action == "clarify" and planner_output.clarify_questions:
    result: dict[str, Any] = {
        "response": "",
        "sources": [],
        "confidence": 0.0,
        "is_partial": False,
        "needs_clarification": True,
        "clarification_questions": planner_output.clarify_questions,
    }
    if collect_outputs:
        result["intermediate_outputs"] = {
            "planner": planner_output.model_dump(),
        }
    return result
```

Also add to normal result return (around line 260):
```python
result: dict[str, Any] = {
    "response": final_response,
    "sources": sources,
    "confidence": confidence,
    "is_partial": is_partial,
    "needs_clarification": False,
    "clarification_questions": None,
}
```

**File 2: `packages/swealog/swealog/cli/auto_cmd.py`**

After `_display_query_result(result)` in QUERY branch (around line 205):

```python
# Check if clarification needed (before _display_query_result)
if result.get("needs_clarification"):
    console.print("\n[bold yellow]Clarification needed:[/bold yellow]")
    questions = result.get("clarification_questions", [])
    for i, question in enumerate(questions, 1):
        console.print(f"  {i}. {question}")
    console.print("\n[dim]Please re-query with more specific details.[/dim]")
    return  # Exit without response
```

### Edge Cases

| Case | Handling |
|------|----------|
| `next_action="clarify"` but `clarify_questions` is None | Treat as retrieve (defensive) |
| `next_action="clarify"` but `clarify_questions` is `[]` | Treat as retrieve (defensive) |
| `next_action="expand_domain"` | Proceed to retrieve (expansion not implemented) |
| `next_action="synthesize"` | Proceed to retrieve (rare case, let full flow run) |
| Multiple retry iterations | Clarification only checked on first Planner call |

### API Endpoint Note

The `process_query()` API endpoint (`POST /query`) and `QueryResponse` model are **not updated** in this story. The API returns the normal response structure. Clarification handling is CLI-only for Phase 1. If API clarification support is needed, it should be a separate story.

### File Changes Summary

| File | Change Type | Lines Impact |
|------|-------------|--------------|
| `packages/swealog/swealog/api/routes/query.py` | MODIFY | ~15 lines |
| `packages/swealog/swealog/cli/auto_cmd.py` | MODIFY | ~10 lines |
| `packages/swealog/tests/test_api_routes.py` | MODIFY | ~30 lines |

### Validation Checklist

Before marking complete:
- [x] `make check` passes (lint + typecheck)
- [x] `make validate` passes (all unit tests)
- [x] Pipeline returns `needs_clarification: True` when Planner outputs `next_action="clarify"` with questions
- [x] Pipeline returns `needs_clarification: False` for normal queries
- [x] CLI displays clarification questions when `needs_clarification: True`
- [x] Edge case: `clarify_questions=[]` does NOT trigger clarification flow
- [x] No regression: normal queries still work

### What This Does NOT Do

- **No ClarifierAgent call:** Planner already generates `clarify_questions`, so we use those directly
- **No interactive flow:** User is shown questions and must re-query (no pause/resume)
- **No domain expansion:** `next_action="expand_domain"` falls through to retrieve
- **No LangGraph integration:** Stays synchronous, no state machine
- **No API changes:** `QueryResponse` model unchanged

### References

| Source | Content |
|--------|---------|
| `tests/eval/feedback/archive/iter-002/records/2026-01-26_8628f945.json` | Evidence of routing failure |
| `packages/quilto/quilto/agents/models.py:411` | PlannerOutput `next_action` field |
| `packages/swealog/swealog/api/routes/query.py:93-277` | Current `execute_query_pipeline` |
| `_bmad-output/implementation-artifacts/epic-13/13-3-implement-conversation-context.md` | Previous story pattern |

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5

### Debug Log References

N/A

### Completion Notes List

- Implemented clarification flow routing in `execute_query_pipeline()`:
  - Added check after Planner step to detect `next_action == "clarify"` with truthy `clarify_questions`
  - Returns early with `needs_clarification: True` and questions instead of proceeding to Retriever
  - Normal flow result now includes `needs_clarification: False` and `clarification_questions: None`
- Updated CLI `auto_cmd.py` to handle clarification in both QUERY and BOTH flows:
  - Displays clarification questions using `print_warning()` and `print_info()`
  - Exits normally after displaying questions (user re-queries with more context)
- Added 7 unit tests covering clarification routing logic:
  - Integration test with mocked pipeline
  - Condition logic tests for all edge cases
  - Result structure validation tests
- All validation passes: lint, typecheck, and 1896 tests passed

### File List

| File | Change Type |
|------|-------------|
| `packages/swealog/swealog/api/routes/query.py` | MODIFY |
| `packages/swealog/swealog/cli/auto_cmd.py` | MODIFY |
| `packages/swealog/tests/test_api_routes.py` | MODIFY |
