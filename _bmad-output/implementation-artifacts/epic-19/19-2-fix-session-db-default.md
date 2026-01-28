# Story 19.2: Fix Session DB Path Default Logic

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **Swealog user**,
I want **my conversation sessions to persist by default**,
so that **I can continue multi-turn conversations across CLI invocations**.

## Acceptance Criteria

1. **Given** no `--session` flag is provided
   **When** a new session is created
   **Then** session is persisted to `quilto_sessions.db` (not `:memory:`)

2. **Given** a session was created in a previous run
   **When** user provides `--session <id>` in a subsequent run
   **Then** the session is retrieved with full conversation history

3. **Given** user wants ephemeral mode
   **When** an explicit `--no-persist` flag is provided
   **Then** `:memory:` is used and session data is discarded on exit

4. **Given** session DB path defaults to persistent
   **When** `_create_quilto()` is called without explicit `session_db_path`
   **Then** the default parameter is `"quilto_sessions.db"` (not `":memory:"`)

5. **Given** the API (`dependencies.py`) uses `:memory:` for stateless per-request behavior
   **When** API creates Quilto instance
   **Then** API continues to use `:memory:` (no change to API)

## Tasks / Subtasks

- [x] Task 1: Fix `_create_quilto()` default parameter (AC: #4)
  - [x] 1.1: In `_create_quilto()` function (`packages/swealog/swealog/cli/app.py`, currently line 75), change `session_db_path: str = ":memory:"` to `session_db_path: str = "quilto_sessions.db"`
  - [x] 1.2: Update the `session_db_path` parameter description in `_create_quilto()` docstring (currently line 85) to say: `"Path to session database. Defaults to 'quilto_sessions.db'."`

- [x] Task 2: Fix session persistence logic in `run_command()` (AC: #1, #2)
  - [x] 2.1: In `run_command()` (`packages/swealog/swealog/cli/app.py`, currently line 322), change the conditional:
    ```python
    # BEFORE (broken):
    session_db_path = "quilto_sessions.db" if session_id else ":memory:"
    # AFTER (fixed):
    session_db_path = ":memory:" if no_persist else "quilto_sessions.db"
    ```
  - [x] 2.2: Always use `"quilto_sessions.db"` by default, only use `":memory:"` when `--no-persist` flag is set
  - [x] 2.3: In the `else` branch (no `--session` flag, currently line 331-332), after `session = quilto.create_session()`, add session ID print so user can resume later:
    ```python
    else:
        session = quilto.create_session()
        print_info(f"Session: {session.session_id}")
    ```

- [x] Task 3: Add `--no-persist` CLI flag (AC: #3)
  - [x] 3.1: Add `no_persist` parameter to `run_command()` function signature in `app.py`:
    ```python
    no_persist: Annotated[
        bool,
        typer.Option("--no-persist", help="Use in-memory session (no persistence)"),
    ] = False,
    ```
  - [x] 3.2: Wire `no_persist` flag into `session_db_path` determination logic (Task 2.1 already covers the conditional change)
  - [x] 3.3: Ensure `--no-persist` takes precedence over `--session` if both are provided (no error, just use `:memory:`)

- [x] Task 4: Update tests (AC: #1-#5)
  - [x] 4.1: Update `TestUnifiedCommandSession.test_session_id_creates_persistent_session` in `test_cli_auto.py` (currently line 359) - verify it still passes with new logic
  - [x] 4.2: Add test: default run (no flags) creates Quilto with `session_db_path="quilto_sessions.db"`
  - [x] 4.3: Add test: default run (no flags) prints session ID in output (assert `"Session:"` in `result.output`)
  - [x] 4.4: Add test: `--no-persist` flag creates Quilto with `session_db_path=":memory:"`
  - [x] 4.5: Add test: `--session <id>` still uses `"quilto_sessions.db"` (regression guard - existing test covers this)
  - [x] 4.6: Verify API `dependencies.py` still uses `":memory:"` (read-only assertion, no code change)
  - [x] 4.7: Add test: `--session <id> --no-persist` - verify `--no-persist` takes precedence (uses `":memory:"`)

- [x] Task 5: Run validation (AC: #1-#5)
  - [x] 5.1: Run `make check` (lint + typecheck) -- 0 errors
  - [x] 5.2: Run `make validate` (full validation with unit tests) -- 27/27 in test_cli_auto.py pass, 9 pre-existing failures in test_feedback.py (unrelated to this story)

## Dev Notes

### Root Cause Analysis

The `run()` command at `packages/swealog/swealog/cli/app.py:322` has inverted default logic:

```python
session_db_path = "quilto_sessions.db" if session_id else ":memory:"
```

This creates a logical contradiction:
1. **No `--session` flag** -> `:memory:` -> new UUID session created -> lost on exit (can never resume)
2. **With `--session <id>`** -> `quilto_sessions.db` -> tries to load session that was never persisted

The Quilto framework defaults are correct (`session_db_path="quilto_sessions.db"` in both `quilto.py:66` and `sqlite.py:37`). The bug is only in the Swealog CLI override.

### Scope and Boundaries

**What to change:**
- `packages/swealog/swealog/cli/app.py` -- Fix defaults + add `--no-persist` flag
- `packages/swealog/tests/test_cli_auto.py` -- Update/add tests

**What NOT to change:**
- `packages/quilto/quilto/quilto.py` -- Quilto defaults are already correct
- `packages/quilto/quilto/session/stores/sqlite.py` -- SQLiteSessionStore defaults are correct
- `packages/swealog/swealog/api/dependencies.py` -- API intentionally uses `:memory:` for stateless per-request behavior (this is correct for an HTTP API where each request is independent)
- No Quilto framework changes -- this is a Swealog CLI-only fix

### Edge Case: `--session` + `--no-persist`

If the user provides both `--session <id>` and `--no-persist`, the `--no-persist` flag takes precedence. The session will be created/loaded in memory and discarded on exit. This is an unusual combination but should not error - it simply means the session won't survive the process.

### Session ID Display

When sessions are always persisted, the user needs to know their session ID to resume later. The CLI should always print the session ID when creating a new session (not just when `--session` is provided). The existing `print_info(f"Session: {session.session_id}")` at line 330 only fires when a non-existent session ID is provided. Add a similar print after line 332 for the default case.

### Project Structure Notes

- All changes are in Swealog (`packages/swealog/`), which is correct since this is CLI behavior, not framework behavior
- The Quilto framework defaults are already sensible (`"quilto_sessions.db"`)
- The API's `:memory:` usage is intentional and correct for stateless HTTP requests

### Architecture Compliance

| Requirement | Status |
|-------------|--------|
| Changes in Swealog (not Quilto) | Yes -- CLI-only fix |
| Quilto framework defaults preserved | Yes -- no changes to quilto.py |
| API behavior preserved | Yes -- dependencies.py unchanged |
| Google-style docstrings | Required for modified functions |
| Type hints complete | Required -- pyright strict mode |
| Existing test patterns followed | Yes -- uses mock Quilto pattern from test_cli_auto.py |

### Library/Framework Requirements

| Library | Version | Usage |
|---------|---------|-------|
| Typer | latest | CLI option definition (`--no-persist`) |
| Pydantic | 2.10+ | No changes needed |

### File Structure Requirements

```
packages/swealog/swealog/cli/
  app.py                    # MODIFY - Fix defaults + add --no-persist flag
packages/swealog/tests/
  test_cli_auto.py          # MODIFY - Update existing + add new tests
```

### Testing Requirements

- **Update:** `TestUnifiedCommandSession.test_session_id_creates_persistent_session` -- verify it still passes with new logic (Task 4.1)
- **New test:** Default run (no flags) uses `"quilto_sessions.db"` (Task 4.2)
- **New test:** Default run (no flags) prints session ID in output (Task 4.3)
- **New test:** `--no-persist` flag causes `":memory:"` to be used (Task 4.4)
- **New test:** `--session <id>` still uses `"quilto_sessions.db"` -- regression guard (Task 4.5)
- **Verify:** API `dependencies.py` still uses `":memory:"` (Task 4.6)
- **New test:** `--session <id> --no-persist` -- `--no-persist` takes precedence (Task 4.7)
- **Run:** `make validate` must pass

### Previous Story Intelligence

**Story 19.1 (Epic 19):** CORRECTION flow fix. Relevant patterns:
- Same `app.py` file was modified (line 322-323 is adjacent to the changes made in 19.1)
- `_display_result()` was updated -- be careful not to break that change
- `test_cli_auto.py` was updated -- build on existing test patterns

**Story 16.4 (Epic 16):** Implemented single `swealog` command. Key context:
- Created the current `run()` function structure
- Established `_create_quilto()` helper pattern
- The `session_db_path` conditional was written here (the original bug introduction)

**Story 15.2 (Epic 15):** Implemented session management. Key context:
- `Session`, `SessionManager`, `SQLiteSessionStore` were designed
- The default was always `"quilto_sessions.db"` -- the Quilto framework was correct from the start
- The `:memory:` option was explicitly documented as "useful for testing"

### Git Intelligence

Recent commits show stabilization focus:
- `f0d59f0` Story 19.1 -- just modified `app.py` and `test_cli_auto.py` (same files we'll touch)
- The `session_db_path` logic at line 322 was introduced in Epic 16 and hasn't been modified since
- No recent changes to Quilto session store or Quilto class constructor

### Current Code Snapshot

**Bug location** (`app.py:322`):
```python
session_db_path = "quilto_sessions.db" if session_id else ":memory:"
```

**`_create_quilto` default** (`app.py:75`):
```python
session_db_path: str = ":memory:",  # <-- Also wrong, should be "quilto_sessions.db"
```

**Quilto class default** (`quilto.py:66`):
```python
session_db_path: str = "quilto_sessions.db",  # <-- Correct
```

**SQLiteSessionStore default** (`sqlite.py:37`):
```python
def __init__(self, db_path: str = "quilto_sessions.db") -> None:  # <-- Correct
```

**API default** (`dependencies.py:104`):
```python
session_db_path=":memory:",  # <-- Intentionally stateless, keep as-is
```

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 19.2] - Story definition and acceptance criteria
- [Source: _bmad-output/implementation-artifacts/epic-18/epic-18-retro-2026-01-28.md] - Bug discovery
- [Source: packages/swealog/swealog/cli/app.py:322] - Bug location: inverted conditional
- [Source: packages/swealog/swealog/cli/app.py:75] - Bug location: wrong default in helper
- [Source: packages/quilto/quilto/quilto.py:66] - Correct Quilto framework default
- [Source: packages/quilto/quilto/session/stores/sqlite.py:37] - Correct SQLiteSessionStore default
- [Source: packages/swealog/swealog/api/dependencies.py:104] - API intentional `:memory:` (no change)
- [Source: packages/swealog/tests/test_cli_auto.py:386] - Existing session persistence test
- [Source: _bmad-output/project-context.md] - Project conventions

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

- `make check`: 0 errors (lint + typecheck pass)
- `make validate`: 9 pre-existing failures in `test_feedback.py` (Story 18.2 debug format change), 0 new failures
- `uv run pytest packages/swealog/tests/test_cli_auto.py -v`: 27/27 passed

### Completion Notes List

- Task 1: Changed `_create_quilto()` default from `":memory:"` to `"quilto_sessions.db"` and updated docstring
- Task 2: Fixed conditional from `"quilto_sessions.db" if session_id else ":memory:"` to `":memory:" if no_persist else "quilto_sessions.db"`. Added session ID print in default (no `--session`) branch
- Task 3: Added `--no-persist` Typer option to `run_command()`. `--no-persist` takes precedence over `--session` naturally via the conditional
- Task 4: Added 5 new tests + 1 API assertion test. Existing `test_session_id_creates_persistent_session` passes unchanged (regression guard)
- Task 5: `make check` passes (0 errors). All 27 tests in `test_cli_auto.py` pass. 9 pre-existing failures in `test_feedback.py` are from Story 18.2 debug format change (not this story)
- No changes to Quilto framework (`quilto.py`, `sqlite.py`) or API (`dependencies.py`) -- bug was CLI-only

### File List

- `packages/swealog/swealog/cli/app.py` -- Fixed `_create_quilto()` default, fixed `run_command()` conditional, added `--no-persist` flag, added session ID print, code review fixes (warning on not-found session, warning on `--no-persist` + `--session` override, always print session ID)
- `packages/swealog/tests/test_cli_auto.py` -- Added 5 new session tests + 1 API assertion test + 3 code review tests (existing session resume, session not found warning, no-persist override warning)

### Code Review Record

**Reviewer:** Amelia (Dev Agent, Claude Opus 4.5)
**Date:** 2026-01-29
**Verdict:** PASS with 5 issues found and fixed

| # | Issue | Severity | Fix Applied |
|---|-------|----------|-------------|
| 1 | Silent session ID discard on not-found | MEDIUM | Added `print_warning` when requested session not found |
| 2 | `--no-persist + --session` does pointless lookup | LOW | Skip `get_session()` when `no_persist=True`, print warning |
| 3 | Existing session found doesn't print session ID | LOW | Always print session ID after `get_session()` succeeds |
| 4 | Precedence test missing warning assertion | LOW | Updated test to assert warning + `get_session` not called |
| 5 | Missing test for existing session resume | MEDIUM | Added `test_existing_session_resume` + `test_session_not_found_warns_user` |

**Validation:** `make check` (0 errors), 29/29 tests passed in `test_cli_auto.py`
