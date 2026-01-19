# Story 9.2: Unified Auto Command

Status: done

## Story

As a **Swealog user**,
I want **a unified command that automatically routes my input**,
So that **I don't need to decide whether to use `log` or `ask` - the system figures it out**.

## Background

The Router agent already classifies input as `LOG`, `QUERY`, `BOTH`, or `CORRECTION`. Currently:
- `swealog log` forces log flow (suggests `ask` if QUERY detected)
- `swealog ask` forces query flow

A unified `auto` command would leverage Router classification to automatically execute the appropriate flow, providing a simpler UX while keeping explicit commands for users who want direct control.

## Acceptance Criteria

1. **AC1: Auto Command Routes LOG**
   - Given `swealog auto "bench 185x5"`
   - When Router classifies as LOG
   - Then entry is logged (same as `swealog log`)
   - And success message shows "Logged entry: {id}"

2. **AC2: Auto Command Routes QUERY**
   - Given `swealog auto "how's my bench progress?"`
   - When Router classifies as QUERY
   - Then query pipeline executes (same as `swealog ask`)
   - And response panel is displayed

3. **AC3: Auto Command Handles BOTH**
   - Given `swealog auto "bench 185x5, how does this compare to last week?"`
   - When Router classifies as BOTH
   - Then entry is logged first
   - And query pipeline executes with query_portion
   - And both results are shown (log success + query response)

4. **AC4: Auto Command Handles CORRECTION**
   - Given `swealog auto "actually yesterday was 195x5 not 185x5"`
   - When Router classifies as CORRECTION
   - Then correction flow executes (same as log with correction_mode)

5. **AC5: Debug Flag Support**
   - Given `swealog auto --debug "bench 185x5"`
   - When command executes
   - Then all agent timing is shown (Router, Parser, and/or query pipeline agents)
   - And debug output follows AC5 format from Story 9.1

6. **AC6: Existing Commands Unchanged**
   - `swealog log` continues to work as before
   - `swealog ask` continues to work as before
   - Both support `--debug` flag (already implemented in 9.1)

## Tasks / Subtasks

- [x] Task 1: Create auto_cmd.py module (AC: 1-5)
  - [x] Create `packages/swealog/swealog/cli/auto_cmd.py`
  - [x] Implement `auto` function with same options as log/ask (--config, --storage, --debug)
  - [x] Route based on router_output.input_type:
    - LOG → execute log flow
    - QUERY → execute query flow
    - BOTH → execute log flow, then query flow with query_portion
    - CORRECTION → execute correction flow

- [x] Task 2: Refactor shared logic (AC: 1-4)
  - [x] Extract log flow logic into reusable async function (e.g., `_execute_log_flow`)
  - [x] Extract query flow logic into reusable async function (e.g., `_execute_query_flow`)
  - [x] Both functions accept DebugLogger for debug support
  - [x] Update log_cmd.py and ask_cmd.py to use shared functions

- [x] Task 3: Register auto command (AC: 1-5)
  - [x] Import auto_cmd in cli/app.py
  - [x] Register with `app.command()(auto)`
  - [x] Export from cli/__init__.py

- [x] Task 4: Write unit tests (AC: 1-6)
  - [x] Test auto routes LOG correctly
  - [x] Test auto routes QUERY correctly
  - [x] Test auto handles BOTH (logs then queries)
  - [x] Test auto handles CORRECTION
  - [x] Test --debug flag shows all agent timing
  - [x] Test existing log/ask commands still work

- [x] Task 5: Update CLI help text
  - [x] Add examples showing auto usage in docstring
  - [x] Ensure help text explains auto vs explicit commands

## Dev Notes

### Project Identity

This story modifies **Swealog** CLI (the application), not Quilto framework.

**Location:** `packages/swealog/swealog/cli/`

### File Structure

```
packages/swealog/swealog/cli/
├── __init__.py       # Export auto
├── app.py            # Register auto command
├── auto_cmd.py       # NEW: Unified auto command
├── log_cmd.py        # Refactor to use shared flow
├── ask_cmd.py        # Refactor to use shared flow
├── flows.py          # NEW (optional): Shared flow functions
└── ...
```

### Design Decision: Shared Flows

Option A: Extract flows into `flows.py`
```python
# flows.py
async def execute_log_flow(text, llm_client, storage, domains, dbg) -> str:
    """Execute log flow, return entry_id."""
    ...

async def execute_query_flow(query, llm_client, storage, domains, dbg) -> dict:
    """Execute query flow, return result dict."""
    ...
```

Option B: Keep inline in auto_cmd.py, call existing functions
- Less refactoring but more code duplication

**Recommendation:** Option A for cleaner architecture, but Option B is acceptable if time-constrained.

### Auto Command Flow

```
auto(text)
  → Router.classify(text)
  → match input_type:
      LOG → execute_log_flow(text) → success
      QUERY → execute_query_flow(text) → response
      BOTH → execute_log_flow(text) → execute_query_flow(query_portion) → both
      CORRECTION → execute_log_flow(text, correction=True) → success
```

### Example Usage

```bash
# Auto-detect and route
swealog auto "bench 185x5"                    # → LOG flow
swealog auto "how's my progress?"             # → QUERY flow
swealog auto "ran 5k, how does that compare?" # → BOTH flows

# With debug
swealog auto --debug "bench 185x5"

# Explicit commands still work
swealog log "bench 185x5"
swealog ask "how's my progress?"
```

### Validation Commands

```bash
# During development
make check        # lint + typecheck

# Before completion
make validate     # lint + format + typecheck + test

# Integration testing
make test-ollama
```

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Completion Notes List

- Implemented `swealog auto` command that automatically routes input based on Router classification
- Created `flows.py` with `execute_log_flow()` function for shared log flow logic
- Refactored `log_cmd.py` to use the shared `execute_log_flow()` function
- Reused existing `execute_query_pipeline()` from API routes for query flow
- Auto command handles all four input types: LOG, QUERY, BOTH, CORRECTION
- Debug flag (--debug/-d) shows Router timing and delegates to inner flows for Parser/pipeline timing
- All 1741 tests pass (9 tests for auto command)
- `make validate` passes (lint, format, typecheck, tests)
- `make test-ollama` passes (1778 integration tests)

### Code Review Fixes (2026-01-19)

Fixed 4 issues identified during adversarial code review:
- **M1**: Extracted duplicate `_create_debug_callback` to shared `create_debug_callback` in `debug.py`
- **M2**: Extracted duplicate query result display to `_display_query_result` helper in `auto_cmd.py`
- **M3**: Fixed double `datetime.now()` call in `flows.py` - now uses single timestamp
- **L4**: Added test for unexpected input_type fallback behavior

### Change Log

- 2026-01-19: Created Story 9.2 - Unified Auto Command
- 2026-01-19: Implemented unified auto command with shared flow refactoring
- 2026-01-19: Code review fixes - extracted shared functions, fixed datetime consistency

### File List

- packages/swealog/swealog/cli/auto_cmd.py (NEW)
- packages/swealog/swealog/cli/flows.py (NEW)
- packages/swealog/swealog/cli/debug.py (MODIFIED - added create_debug_callback)
- packages/swealog/swealog/cli/log_cmd.py (MODIFIED - refactored to use execute_log_flow)
- packages/swealog/swealog/cli/ask_cmd.py (MODIFIED - use shared create_debug_callback)
- packages/swealog/swealog/cli/app.py (MODIFIED - registered auto command)
- packages/swealog/swealog/cli/__init__.py (MODIFIED - exported auto, execute_log_flow, create_debug_callback)
- packages/swealog/tests/test_cli_auto.py (NEW)
- packages/swealog/tests/test_cli_log.py (MODIFIED - updated mocks)
- packages/swealog/tests/test_cli_debug.py (MODIFIED - updated mocks)
