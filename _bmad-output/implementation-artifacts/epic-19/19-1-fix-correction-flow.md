# Story 19.1: Fix CORRECTION Input Type Flow

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **Swealog user**,
I want **to correct previously logged data**,
so that **my fitness records are accurate**.

## Acceptance Criteria

1. **Given** Router classifies input as CORRECTION
   **When** Parser receives the input with correction_target from Router
   **Then** Parser identifies the target entry and extracts the correction delta

2. **Given** Parser identifies a correction
   **When** correction is processed
   **Then** the target entry is updated in storage via upsert semantics

3. **Given** a correction is processed (success or failure)
   **When** final_response is generated
   **Then** user receives feedback about what was corrected (not empty string)

4. **Given** input "I logged 5 sets but it should be 4"
   **When** processed as CORRECTION
   **Then** the matching entry's set count is updated from 5 to 4 and user sees confirmation

## Tasks / Subtasks

- [x] Task 1: Fix Parser raw_input for CORRECTION flow (AC: #1, #2)
  - [x] 1.1: Add `user_input` parameter to `process_correction()` function signature
  - [x] 1.2: In `process_correction()`, change `raw_input` from `router_output.log_portion or router_output.reasoning` to the new `user_input` parameter
  - [x] 1.3: Pass `user_input` from `correction_node()` state (`state[StateKeys.USER_INPUT]`) to `process_correction()`
  - [x] 1.4: Verify Parser receives the actual correction text, not Router's reasoning
  - _Note: AC #2 (storage upsert) is implicitly fixed by this task — the existing storage code at `correction.py:104-123` already handles upsert correctly once Parser receives valid input_

- [x] Task 2: Add response generation for CORRECTION flow (AC: #3)
  - [x] 2.1: In `correction_node()`, generate a user-facing response based on `CorrectionResult`
  - [x] 2.2: On success: `f"Corrected entry {result.target_entry_id}: {result.correction_delta}"` (e.g., "Corrected entry 2026-01-27_10-30-00: {'sets': 4}")
  - [x] 2.3: On failure: "Could not process correction: {error_message}"
  - [x] 2.4: Set `StateKeys.RESPONSE` in `correction_node()` return dict so ProcessResult has response

- [x] Task 3: Add correction_result to ProcessResult (AC: #3)
  - [x] 3.1: Add `correction_result: dict[str, Any] | None = None` field to `ProcessResult` model
  - [x] 3.2: Update `_build_process_result()` in `session.py` to extract `StateKeys.CORRECTION_RESULT` from state
  - [x] 3.3: Map to the new `correction_result` field in ProcessResult

- [x] Task 4: Update CLI to display correction response (AC: #3)
  - [x] 4.1: Verify Swealog CLI handles `ProcessResult.response` for CORRECTION input_type
  - [x] 4.2: Ensure non-empty response is displayed to user

- [x] Task 5: Write tests for correction flow fixes (AC: #1, #2, #3, #4)
  - [x] 5.1: Update or remove existing `test_uses_reasoning_when_log_portion_is_none` in `packages/quilto/tests/test_correction_flow.py` — this test validates the **broken** behavior (expects `raw_input == reasoning`), must be rewritten to expect `raw_input == user_input`
  - [x] 5.2: Test that `process_correction()` receives actual user input (not Router reasoning)
  - [x] 5.3: Test that `correction_node()` sets `StateKeys.RESPONSE` on success
  - [x] 5.4: Test that `correction_node()` sets `StateKeys.RESPONSE` on failure
  - [x] 5.5: Test that `_build_process_result()` includes `correction_result`
  - [x] 5.6: Test end-to-end correction with mock LLM returns non-empty response

- [x] Task 6: Run validation (AC: #1-#4)
  - [x] 6.1: Run `make check` (lint + typecheck) — 0 errors
  - [x] 6.2: Run `make validate` (full validation with unit tests) — 2091 passed, 9 pre-existing failures in test_feedback.py (unrelated)

## Dev Notes

### Root Cause Analysis

Three distinct bugs combine to make the CORRECTION flow non-functional:

#### Bug 1: Parser receives wrong input text (CRITICAL)

**Location:** `packages/quilto/quilto/flow/correction.py:79`

```python
parser_input = ParserInput(
    raw_input=router_output.log_portion or router_output.reasoning,  # <-- BUG
    ...
)
```

**Problem:** For CORRECTION inputs, `router_output.log_portion` is `null` (Router only sets `log_portion` for LOG and BOTH types). The fallback `router_output.reasoning` is the Router's **classification explanation**, not the user's actual input. So Parser receives text like:

> "The statement explicitly revises previously logged data, indicating a correction..."

Instead of the actual user text:

> "I think I logged 5 sets yesterday but it should have been 4 sets of pull-ups"

The Parser cannot extract correction data from a classification reasoning string.

**Evidence:** `tests/eval/feedback/archive/iter-007/2026-01-28_54959ede.json`
- `router.log_portion: null`
- `router.reasoning: "The statement explicitly revises previously logged data..."` (classification reasoning)
- `correction.error_message: "Parser did not identify correction"`

**Fix:** Pass the original `user_input` from state through to `process_correction()`. The `correction_node()` at `orchestration.py:990` has access to `state[StateKeys.USER_INPUT]` which contains the actual user text.

```python
# In correction_node():
user_input = state.get(StateKeys.USER_INPUT, "")

result = await process_correction(
    router_output=router_output,
    parser_agent=parser,
    storage=quilto.storage,
    recent_entries=recent_entries,
    domain_schemas=domain_schemas,
    vocabulary=domain_context.vocabulary,
    user_input=user_input,  # NEW parameter
)

# In process_correction():
parser_input = ParserInput(
    raw_input=user_input,  # Use actual user input, not router reasoning
    ...
)
```

#### Bug 2: No response generated for CORRECTION flow (HIGH)

**Location:** `packages/quilto/quilto/orchestration.py:1300-1353` (graph wiring)

```
Graph: route -> correction -> observe -> END
```

**Problem:** The CORRECTION path goes `route -> correction -> observe -> END`. There is NO synthesizer node in the correction path. The `correction_node()` only sets `StateKeys.CORRECTION_RESULT` in state (line 1044) but does NOT set `StateKeys.RESPONSE`. Since `ProcessResult.response` defaults to `None`, the CLI shows an empty string.

**Fix:** In `correction_node()`, generate a user-facing response string and set `StateKeys.RESPONSE`:

```python
# In correction_node() after getting CorrectionResult:
if result.success:
    response = f"Corrected entry {result.target_entry_id}: {result.correction_delta}"
else:
    response = f"Could not process correction: {result.error_message}"

return {
    StateKeys.CORRECTION_RESULT: result.model_dump(),
    StateKeys.RESPONSE: response,  # NEW - ensures user gets feedback
    StateKeys.TRACES: _add_trace(...),
}
```

#### Bug 3: ProcessResult missing correction_result field (MEDIUM)

**Location:** `packages/quilto/quilto/session/session.py:238-304` and `packages/quilto/quilto/models.py:73-117`

**Problem:** `_build_process_result()` doesn't extract `StateKeys.CORRECTION_RESULT` from state. `ProcessResult` doesn't have a `correction_result` field. Even when correction succeeds, the application has no structured way to know what was corrected.

**Fix:** Add `correction_result` field to `ProcessResult` and extract it in `_build_process_result()`.

### Project Structure Notes

All changes are in the Quilto framework (`packages/quilto/`), which is correct since CORRECTION flow is domain-agnostic. The Swealog CLI should work without changes if `ProcessResult.response` is properly set.

- **Quilto changes:** `flow/correction.py`, `orchestration.py`, `models.py`, `session/session.py`
- **Swealog changes:** Likely none (CLI already displays `result.response`)
- **Test changes:** `packages/quilto/tests/test_correction_flow.py` (update existing + add new orchestration tests)

### Architecture Compliance

| Requirement | Status |
|-------------|--------|
| Changes in Quilto (not Swealog) | Yes - all changes are framework-level |
| Domain-agnostic | Yes - no fitness-specific logic |
| Existing patterns followed | Yes - same StateKeys pattern, Pydantic models |
| No new dependencies | Yes - uses existing modules |
| Google-style docstrings | Required for new/modified functions |
| Type hints complete | Required - pyright strict mode |

### Library/Framework Requirements

| Library | Version | Usage |
|---------|---------|-------|
| Pydantic | 2.10+ | ProcessResult model update |
| LangGraph | latest | Orchestration graph (no changes needed to graph structure) |
| litellm | latest | LLM calls via ParserAgent (no changes) |

### File Structure Requirements

```
packages/quilto/quilto/
  flow/
    correction.py          # MODIFY - Add user_input param, fix raw_input
  orchestration.py         # MODIFY - Pass user_input, generate response
  models.py                # MODIFY - Add correction_result to ProcessResult
  session/
    session.py             # MODIFY - Extract correction_result in _build_process_result
packages/quilto/tests/
  test_correction_flow.py  # MODIFY - Rewrite broken-behavior test + add new tests
```

### Testing Requirements

- **CRITICAL:** Existing test `test_uses_reasoning_when_log_portion_is_none` at `packages/quilto/tests/test_correction_flow.py:389` validates the **broken** behavior — it asserts `raw_input == reasoning`. This test MUST be rewritten to assert `raw_input == user_input` as part of Task 5.1.
- **Unit tests:** Test `process_correction()` with actual user input text
- **Unit tests:** Test `correction_node()` sets `StateKeys.RESPONSE`
- **Unit tests:** Test `_build_process_result()` includes `correction_result`
- **Integration tests:** Mock LLM end-to-end correction returns non-empty response
- **Boundary tests:** Empty `user_input`, null `correction_target`, no `recent_entries`
- **Run:** `make validate` must pass

### Previous Story Intelligence

**Story 5.3 (Epic 5):** Original CORRECTION flow implementation. Key learnings:
- `process_correction()` was designed for the pre-LangGraph era as a standalone orchestration function
- It expected `router_output.log_portion` which was set in the old manual wiring but is NOT set by Router for CORRECTION inputs
- The migration to Quilto API (Epic 15-16) preserved `process_correction()` but the calling context changed from manual wiring to LangGraph orchestration
- The `raw_input=router_output.log_portion or router_output.reasoning` pattern was a legacy assumption

**Story 18.1 (Epic 18):** Synthesizer fallback pattern. Relevant because:
- Shows how to generate fallback responses when upstream agents fail
- Pattern: Check for error state, generate synthetic response
- Used `StateKeys.RESPONSE` to ensure user always gets feedback

**Story 18.3 (Epic 18):** Type mismatch fix. Relevant because:
- `isinstance()` checks for defensive type handling
- Same defensive pattern should be used when building correction response text

### Git Intelligence

Recent commits (Epic 18) show the project is in a stabilization phase:
- `1b95a95` Epic 18 retrospective + iter-007 dogfooding (source of this bug)
- `9557fd8` Story 18.4 code review fixes
- `50e6a8f` Fix --debug to print full JSON (similar output visibility fix)
- `5b2eff8` Story 18.3 clarification questions type fix (similar type handling)

### Key Data Flow (Current - Broken)

```
User: "I logged 5 sets but should be 4 sets of pull-ups"
  |
  v
Router:
  input_type: CORRECTION (0.96)
  correction_target: "Number of pull-up sets (should be 4 sets instead of 5)"
  log_portion: null         <-- NOT SET for CORRECTION
  reasoning: "The statement explicitly revises..." <-- Classification text
  |
  v
correction_node():
  user_input = state["user_input"]  <-- "I logged 5 sets but should be 4"
  BUT passes router_output to process_correction (not user_input)
  |
  v
process_correction():
  raw_input = router_output.log_portion or router_output.reasoning
           = null or "The statement explicitly revises..."
           = "The statement explicitly revises..."  <-- WRONG! Parser gets reasoning
  |
  v
Parser:
  Tries to extract from "The statement explicitly revises..."
  Cannot identify correction -> is_correction: false
  |
  v
process_correction() returns: CorrectionResult(success=False, error="Parser did not identify correction")
  |
  v
correction_node() returns: { CORRECTION_RESULT: {...}, TRACES: [...] }
  NOTE: Does NOT set RESPONSE
  |
  v
observe_node() -> END
  |
  v
_build_process_result():
  response = state.get("response") = None  <-- Never set
  correction_result: NOT EXTRACTED
  |
  v
CLI: displays "" (empty string)
```

### Key Data Flow (Fixed)

```
User: "I logged 5 sets but should be 4 sets of pull-ups"
  |
  v
Router: (unchanged - works correctly)
  input_type: CORRECTION
  correction_target: "Number of pull-up sets (should be 4 not 5)"
  |
  v
correction_node():
  user_input = state["user_input"] = "I logged 5 sets but should be 4..."
  Passes user_input to process_correction()
  |
  v
process_correction(user_input="I logged 5 sets but should be 4..."):
  raw_input = user_input  <-- ACTUAL USER TEXT
  |
  v
Parser:
  Receives: "I logged 5 sets but should be 4 sets of pull-ups"
  correction_mode: true, correction_target from Router
  recent_entries: formatted list of last 7 days
  -> is_correction: true, target_entry_id: "2026-01-27_...", correction_delta: {sets: 4}
  |
  v
process_correction(): success! -> CorrectionResult(success=True, ...)
  |
  v
correction_node():
  response = "Corrected: pull-up sets updated from 5 to 4"
  Sets RESPONSE + CORRECTION_RESULT in state
  |
  v
observe_node() -> END
  |
  v
_build_process_result():
  response = "Corrected: pull-up sets updated from 5 to 4"
  correction_result = { success: true, target_entry_id: "...", ... }
  |
  v
CLI: displays "Corrected: pull-up sets updated from 5 to 4"
```

### References

- [Source: tests/eval/feedback/archive/iter-007/2026-01-28_54959ede.json] - Bug evidence
- [Source: _bmad-output/implementation-artifacts/epic-18/epic-18-retro-2026-01-28.md#Story 19.1] - Bug description
- [Source: _bmad-output/planning-artifacts/epics.md#Story 19.1] - Acceptance criteria
- [Source: packages/quilto/quilto/flow/correction.py:79] - Bug 1: wrong raw_input
- [Source: packages/quilto/quilto/orchestration.py:1043-1046] - Bug 2: no RESPONSE set
- [Source: packages/quilto/quilto/session/session.py:238-304] - Bug 3: no correction_result extraction
- [Source: packages/quilto/quilto/models.py:73-117] - ProcessResult missing correction_result
- [Source: packages/quilto/quilto/agents/parser.py:113-217] - Parser build_prompt with correction mode
- [Source: packages/quilto/quilto/orchestration.py:1300-1353] - Graph wiring (correction -> observe -> END)
- [Source: _bmad-output/implementation-artifacts/epic-5/5-3-implement-correction-flow.md] - Original implementation
- [Source: _bmad-output/project-context.md] - Project conventions

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

None

### Completion Notes List

- Bug 1 fix: Added `user_input` parameter to `process_correction()`, replaced `router_output.log_portion or router_output.reasoning` with actual user text from state
- Bug 2 fix: `correction_node()` now generates response string on success/failure/exception and sets `StateKeys.RESPONSE`
- Bug 3 fix: Added `correction_result: dict[str, Any] | None` field to `ProcessResult`, extracted in `_build_process_result()`
- CLI fix: Updated `_display_result()` to show `result.response` for CORRECTION type instead of generic "Corrected entry" message
- Rewrote broken test `test_uses_reasoning_when_log_portion_is_none` -> `test_uses_user_input_not_router_reasoning`
- Added 7 new tests: 3 for correction_node response (success/failure/exception), 3 for _build_process_result correction_result, 1 end-to-end
- Updated all existing process_correction test calls with new `user_input` parameter
- Updated CLI test `test_command_handles_correction` to match new behavior
- Pre-existing failures: 9 tests in `test_feedback.py` fail on main branch (debug output format mismatch from Story 18.2)

### File List

- `packages/quilto/quilto/flow/correction.py` — Added `user_input` parameter, use it for `raw_input`
- `packages/quilto/quilto/orchestration.py` — Pass `user_input` to `process_correction()`, generate response in `correction_node()`
- `packages/quilto/quilto/models.py` — Added `correction_result` field to `ProcessResult`
- `packages/quilto/quilto/session/session.py` — Extract `correction_result` from state in `_build_process_result()`
- `packages/swealog/swealog/cli/app.py` — Display `result.response` for CORRECTION input_type
- `packages/quilto/tests/test_correction_flow.py` — Rewrote broken test + added 7 new tests + updated existing calls
- `packages/swealog/tests/test_cli_auto.py` — Updated `test_command_handles_correction` for new behavior
