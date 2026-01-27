# Story 16.7: Review Batch Import Command

Status: done

## Story

As a **Swealog developer**,
I want **to decide if batch import stays as a separate command**,
so that **the CLI design is consistent with the new single-command architecture**.

## Background

**Origin:** Epic 16 - Clean Swealog Implementation
**Priority:** LOW | **Effort:** Small (1 hour)
**Status:** Optional - can defer

**Problem Statement:**
After Story 16.4 introduced the single `swealog run` command for all interactive processing (LOG, QUERY, BOTH, CORRECTION), the batch import command (`swealog import`) remains as a separate command. We need to decide whether this is the right design or if it should be unified.

**Current State:**
- `swealog run "text"` - Single command for all interactive flows via Quilto orchestration
- `swealog import path` - Separate command for batch file import
- `swealog serve` - Separate command for API server

**Design Question:**
Should `swealog import` be:
1. **Option A:** Keep as separate `swealog import file.txt` command (batch processing is special)
2. **Option B:** Add `swealog run --batch file.txt` flag to main command (more unified)
3. **Option C:** Keep as-is for now, revisit later (pragmatic deferral)

## Analysis

### Option A: Keep Separate Command ✅ SELECTED

**Rationale:**
- Batch import has fundamentally different semantics:
  - Processes multiple entries from files, not a single interactive input
  - Uses file-based progress tracking (`Rich.Progress`)
  - Has batch-specific options (`--dry-run`, `--delimiter`, `--error-log`)
  - No session context or multi-turn conversation
  - Bypasses Quilto orchestration, uses Router+Parser directly (intentionally)
- `serve` is already a separate command, establishing precedent for distinct operations
- Clear separation of concerns: `run` = interactive, `import` = batch, `serve` = server
- No user confusion: `import` is clearly about files, `run` is clearly about text

**Implementation:** No code changes required. Document the rationale.

### Option B: Unified `--batch` Flag

**Rationale:**
- Single entry point philosophy ("one command to rule them all")
- Discoverable via `swealog run --help`

**Issues:**
- Awkward semantics: `swealog run --batch file.txt` vs `swealog run "text"`
  - `run` implies single input execution, not batch processing
- Would need to make `text` argument optional when `--batch` is present
- Creates conditional behavior based on flag (more complex than separate commands)
- Batch-specific options (`--delimiter`, `--error-log`) would clutter `run --help`

**Implementation:** Not recommended - adds complexity without benefit.

### Option C: Defer Decision

**Rationale:**
- Current design works and is not broken
- Dogfooding will reveal if users are confused

**Issues:**
- Leaves uncertainty in design documentation

## Acceptance Criteria

1. **Given** batch import functionality exists
   **When** design decision is made
   **Then** document the rationale in this story

2. **Given** the chosen approach
   **When** implemented (if any changes)
   **Then** batch import still works correctly

3. **Given** the decision is "keep as-is" (Option A)
   **When** story is marked done
   **Then** no code changes are required, just verification

## Tasks / Subtasks

- [x] Task 1: Verify current batch import works correctly (AC: 2, 3)
  - [x] 1.1: Run `swealog import --help` and verify options: `--dry-run`, `--delimiter`, `--error-log`, `--verbose`
  - [x] 1.2: Test dry-run mode with sample file: `swealog import --dry-run <test-file>`
  - [x] 1.3: Confirm `import_cmd.py` handles LOG, BOTH, CORRECTION (skips QUERY)

- [x] Task 2: Document design decision (AC: 1)
  - [x] 2.1: Confirm Option A (Keep Separate Command) is selected in Dev Notes
  - [x] 2.2: Verify no code changes required (note: bugs found during verification were fixed)

- [x] Task 3: Run validation (AC: 2)
  - [x] 3.1: `make check` passes (lint + typecheck)
  - [x] 3.2: `uv run pytest packages/swealog/tests/test_cli_import.py -v` passes (34 tests)

## Dev Notes

### Decision: Option A (Keep Separate Command) ✅ SELECTED

The batch import command should remain as `swealog import` for the following reasons:

1. **Different Execution Model:**
   - `run`: Single input → Quilto orchestration → single result
   - `import`: Multiple inputs → Router+Parser loop → batch results

2. **Different Options:**
   - `run`: `--session`, `--debug`, `--non-interactive`
   - `import`: `--dry-run`, `--delimiter`, `--error-log`, `--verbose`

3. **Precedent:**
   - `swealog serve` is already a separate command for API server
   - Standard CLI design: distinct operations = distinct commands

4. **User Experience:**
   - `swealog import logs.txt` is immediately clear
   - `swealog run --batch logs.txt` requires mental parsing

### Current CLI Structure (Keep This)

```bash
swealog run "text"              # Interactive processing (LOG/QUERY/BOTH/CORRECTION)
swealog import file.txt         # Batch import from file/directory
swealog serve                   # Start API server
swealog --version               # Show version
```

### Files to Review (No Changes Expected)

| File | Purpose | Status |
|------|---------|--------|
| `packages/swealog/swealog/cli/import_cmd.py` | Batch import implementation (417 lines) | Verified |
| `packages/swealog/swealog/cli/app.py:406` | Command registration | Verified |
| `packages/swealog/tests/test_cli_import.py` | Import tests (596 lines, comprehensive) | Verified |

### Key Differences: `run` vs `import`

| Aspect | `swealog run` | `swealog import` |
|--------|---------------|------------------|
| Input | Single text string | File(s) with multiple entries |
| Processing | Quilto orchestration | Direct Router + Parser |
| Output | Single response/confirmation | Progress bar + summary |
| Session | Supports multi-turn | No session support |
| Debug | Full traces via ProgressHandler | Verbose mode only |
| Observer | Triggers post-query | Not triggered |

### Batch Import Does NOT Use Quilto

This is intentional. The batch import:
- Processes historical/bulk data
- Only needs LOG flow (Router classify → Parser parse → Storage save)
- No need for Planner, Retriever, Analyzer, Synthesizer (query agents)
- No session context (each entry is independent)
- Observer would create noise for bulk imports

If we wanted Observer learning from batch imports, that would be a separate story.

### References

| Source | Purpose |
|--------|---------|
| `packages/swealog/swealog/cli/app.py` | Main CLI app with `run` command |
| `packages/swealog/swealog/cli/import_cmd.py` | Batch import implementation |
| `packages/swealog/tests/test_cli_import.py` | Comprehensive import tests (20+ cases) |
| Story 16.4 file | Single `swealog run` command implementation |
| `_bmad-output/planning-artifacts/epics.md:2596-2622` | Original story definition |

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

N/A

### Bugs Found During Verification

#### Bug 1: Timestamp Parsing with Batch Counter Suffix

**Location:** `import_cmd.py:199-202`

**Issue:** When batch import generates entry_id with counter suffix (e.g., `2026-01-27_15-54-51-0001`), the timestamp parsing logic incorrectly extracted the date part, producing malformed timestamps like `2026-01-27_15_15-54-51`.

**Root Cause:** The old logic `entry_id.split("-", 3)[:3]` included the underscore and hour in the date part.

**Fix:** Changed to `entry_id.split("_")[0]` to correctly extract just the date portion.

**Test Added:** `test_import_entry_timestamp_parsing_with_batch_suffix`

#### Bug 2: Test Leakage to Feedback Directory

**Location:** `test_cli_auto.py:231`

**Issue:** Test `test_debug_shows_traces` used `--debug` flag but didn't mock `FeedbackRecorder`, causing test runs to write files to the real `tests/eval/feedback/active/` directory.

**Fix:** Added `patch("swealog.cli.app.FeedbackRecorder")` to the test's context manager.

**Cleanup:** Removed 15 leaked JSON files from feedback directory.

### Completion Notes List

- Option A (Keep Separate Command) selected as design decision
- Rationale documented in Dev Notes
- Manual verification: `swealog import --help` confirmed options
- Manual verification: `swealog import --dry-run` tested (found and fixed timestamp bug)
- Tests verified: 34 import tests pass, 22 CLI auto tests pass
- Command structure verified: `swealog import`, `swealog run`, `swealog serve`

### File List

| File | Action |
|------|--------|
| `packages/swealog/swealog/cli/import_cmd.py:199-202` | Bug fix (timestamp parsing) |
| `packages/swealog/tests/test_cli_import.py` | Added timestamp parsing test |
| `packages/swealog/tests/test_cli_auto.py:231` | Fixed mock (FeedbackRecorder) |
| `tests/eval/feedback/active/2026-01-27_*.json` | Deleted (leaked test files) |
