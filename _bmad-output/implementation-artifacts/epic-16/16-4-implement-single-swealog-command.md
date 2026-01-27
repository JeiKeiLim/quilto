# Story 16.4: Implement Single `swealog` Command

Status: done

## Story

As a **Swealog user**,
I want **a single `swealog` command for all inputs**,
So that **I don't need to choose between `auto`, `ask`, or `log` commands**.

## Background

**Origin:** Epic 15 Retrospective (2026-01-27) + Story 15.6 Feedback Analysis
**Priority:** HIGH | **Effort:** Medium (3-4 hours)
**Type:** CLI Rewrite - major simplification

**Problem Statement:**
Story 15.4 only partially migrated Swealog to the Quilto API. Current issues:

1. **Router runs twice:** Swealog's `auto` command calls RouterAgent, then Quilto calls it again internally
2. **LOG flow bypasses Quilto entirely:** `log_cmd.py` and `execute_log_flow()` import agents directly
3. **CORRECTION flow bypasses Quilto entirely:** Same issue as LOG
4. **Observer never triggers for LOG inputs:** Only works for QUERY because LOG bypasses orchestration
5. **Multiple redundant commands:** `swealog auto`, `swealog ask`, `swealog log` - confusing for users
6. **~370 lines of CLI code** that duplicates Quilto's internal orchestration

**Solution:**
Replace all CLI commands with a single `swealog run "text"` command that delegates entirely to `session.process(text, mode="auto")`. Delete redundant command files.

## Acceptance Criteria

1. **Given** any text input
   **When** `swealog run "text"` is run
   **Then** Quilto classifies and processes appropriately (LOG/QUERY/BOTH/CORRECTION)

2. **Given** a multi-turn conversation
   **When** `swealog run --session ID "follow-up"` is run
   **Then** previous conversation context is used

3. **Given** the LOG flow is executed via Quilto
   **When** entry is saved
   **Then** Observer triggers and updates global context

4. **Given** `swealog log` or `swealog ask` commands
   **When** user runs them
   **Then** commands no longer exist (deleted)

5. **Given** the rewritten CLI
   **When** `make check` is run
   **Then** lint and typecheck pass

6. **Given** clarification is needed
   **When** Quilto returns clarification questions
   **Then** they are displayed and user is prompted to re-query with details

## Tasks / Subtasks

- [x] Task 1: Create unified main command in `app.py` (AC: #1, #2, #6)
  - [x] 1.1: Create `swealog run` command taking `text` as positional argument
  - [x] 1.2: Add `--session`/`-s` option for multi-turn conversations (uses persistent SQLite)
  - [x] 1.3: Add `--debug`/`-d` option (existing behavior)
  - [x] 1.4: Add `--non-interactive`/`-n` option (for auto-dogfood script)
  - [x] 1.5: Add `--config`/`-c` option for LLM config path
  - [x] 1.6: Add `--storage` option for storage path
  - [x] 1.7: Implement using `quilto.create_session()` + `session.process(text, mode="auto")`
  - [x] 1.8: Display result based on `input_type` (LOG/CORRECTION shows entry, QUERY shows response)
  - [x] 1.9: Handle clarification questions display

- [x] Task 2: Delete redundant command files (AC: #4)
  - [x] 2.1: Delete `packages/swealog/swealog/cli/ask_cmd.py`
  - [x] 2.2: Delete `packages/swealog/swealog/cli/log_cmd.py`
  - [x] 2.3: Delete `packages/swealog/swealog/cli/auto_cmd.py`
  - [x] 2.4: Delete `packages/swealog/swealog/cli/flows.py`
  - [x] 2.5: Update `packages/swealog/swealog/cli/app.py` imports (remove ask, log, auto, flows)
  - [x] 2.6: Update `packages/swealog/swealog/cli/__init__.py` exports

- [x] Task 3: Migrate helper functions from auto_cmd.py (AC: #1)
  - [x] 3.1: Move `_create_quilto()` to app.py
  - [x] 3.2: Move `_display_query_result_from_process_result()` to app.py
  - [x] 3.3: Move `_display_result()` to app.py (handles clarification)
  - [x] 3.4: Move `_prompt_for_feedback()` to app.py
  - [x] 3.5: Adapt `_record_simplified_feedback()` for new router trace extraction

- [x] Task 4: Validation (AC: #5)
  - [x] 4.1: `make check` passes (lint + typecheck)
  - [x] 4.2: `make validate` passes (all 2014 tests pass)
  - [x] 4.3: Updated tests for new CLI structure (`swealog run "text"`)

## Implementation Notes

### CLI Structure Change

The final implementation uses `swealog run "text"` instead of `swealog "text"` due to Typer's handling of positional arguments vs subcommands. With Typer, mixing a positional argument in a callback with subcommands (like `import`, `serve`) causes parsing conflicts where subcommand names get interpreted as the positional argument.

The `run` command structure provides:
- Clear separation between main processing and subcommands
- Proper option parsing (`--debug`, `--session`, etc.)
- Compatible with existing `import` and `serve` subcommands

### Usage Examples

```bash
swealog run "bench 185x5"                      # LOG - creates entry
swealog run "how's my progress?"               # QUERY - returns response
swealog run "ran 5k, how does that compare?"   # BOTH - log + response
swealog run --session abc123 "follow-up"       # Multi-turn conversation
swealog run --debug "text"                     # Show traces
swealog run --non-interactive "text"           # Skip feedback prompt
```

### Deleted Files

- `packages/swealog/swealog/cli/ask_cmd.py`
- `packages/swealog/swealog/cli/log_cmd.py`
- `packages/swealog/swealog/cli/auto_cmd.py`
- `packages/swealog/swealog/cli/flows.py`
- `packages/swealog/tests/test_cli_ask.py`
- `packages/swealog/tests/test_cli_log.py`

### Updated Test Files

- `packages/swealog/tests/test_cli_auto.py` - Rewritten for `swealog run` command
- `packages/swealog/tests/test_cli_debug.py` - Removed deleted module tests
- `packages/swealog/tests/test_cli_import.py` - Updated for new app structure
- `packages/swealog/tests/test_cli_app.py` - Updated help text assertions

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

N/A

### Completion Notes List

1. Implemented unified `swealog run` command delegating to Quilto
2. Deleted 4 redundant CLI files (~600 lines removed)
3. Updated `__init__.py` exports
4. Rewrote tests for new structure
5. All 2014 tests pass with `make validate`

### File List

| Action | File |
|--------|------|
| MODIFIED | `packages/swealog/swealog/cli/app.py` |
| MODIFIED | `packages/swealog/swealog/cli/__init__.py` |
| MODIFIED | `packages/swealog/tests/test_cli_auto.py` |
| MODIFIED | `packages/swealog/tests/test_cli_debug.py` |
| MODIFIED | `packages/swealog/tests/test_cli_import.py` |
| MODIFIED | `packages/swealog/tests/test_cli_app.py` |
| MODIFIED | `_bmad-output/implementation-artifacts/sprint-status.yaml` |
| DELETED | `packages/swealog/swealog/cli/ask_cmd.py` |
| DELETED | `packages/swealog/swealog/cli/log_cmd.py` |
| DELETED | `packages/swealog/swealog/cli/auto_cmd.py` |
| DELETED | `packages/swealog/swealog/cli/flows.py` |
| DELETED | `packages/swealog/tests/test_cli_ask.py` |
| DELETED | `packages/swealog/tests/test_cli_log.py` |
