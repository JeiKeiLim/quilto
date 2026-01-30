# Story 23.2: Fix LOG Persistence

Status: done

## Story

As a **Swealog user**,
I want **LOG entries to be saved to storage files when processed**,
so that **my fitness logs are persisted and queryable in future sessions**.

## Acceptance Criteria

1. **Given** a LOG input processed through `session.process("I did 10 pushups", mode="log")`
   **When** processing completes successfully
   **Then** a raw markdown file is created/appended at `logs/raw/YYYY/MM/YYYY-MM-DD.md`

2. **Given** a LOG input with parseable domain data
   **When** processing completes successfully
   **Then** parsed JSON is created/updated at `logs/parsed/YYYY/MM/YYYY-MM-DD.json`

3. **Given** the LOG persistence fix is implemented
   **When** running CORRECTION flow
   **Then** existing CORRECTION functionality continues to work unchanged

4. **Given** a unit test for `parse_node`
   **When** the test runs
   **Then** it verifies `storage.save_entry()` is called with a valid Entry object

5. **Given** an integration test for LOG flow
   **When** the test runs
   **Then** it verifies actual file creation on the file system

## Tasks / Subtasks

- [x] Task 1: Add save_entry call to parse_node (AC: #1, #2)
  - [x] 1.1: Add import at top of orchestration.py:
    ```python
    from quilto.storage.models import Entry
    ```
  - [x] 1.2: After parser.parse() returns and progress handler is called (after line ~983), create Entry object using UUID for uniqueness:
    ```python
    import uuid
    from datetime import datetime, UTC

    entry = Entry(
        id=f"{datetime.now(UTC).strftime('%Y-%m-%d_%H-%M-%S')}_{uuid.uuid4().hex[:6]}",
        date=datetime.now(UTC).date(),
        timestamp=datetime.now(UTC),
        raw_content=user_input,
        parsed_data=parser_output.domain_data,
    )
    ```
  - [x] 1.3: Call `quilto.storage.save_entry(entry)` before the return statement (note: `quilto` is the Quilto orchestration instance from `_get_quilto(state)`)
  - [x] 1.4: Add logging for save operation (DEBUG level)
  - [x] 1.5: Add try/except around save_entry to log errors but not fail the parse operation (save failures should not block parsing)

- [x] Task 2: Add unit test for parse_node save behavior (AC: #4)
  - [x] 2.1: Create `packages/quilto/tests/test_orchestration_parse_save.py` (flat structure matches existing tests)
  - [x] 2.2: Test `test_parse_node_calls_save_entry()`:
    - Mock storage.save_entry
    - Invoke parse_node with valid state
    - Assert save_entry called once with Entry object
  - [x] 2.3: Test `test_parse_node_saves_correct_entry_fields()`:
    - Verify Entry has correct id format (YYYY-MM-DD_HH-MM-SS_xxxxxx), date, timestamp, raw_content, parsed_data
  - [x] 2.4: Test `test_parse_node_handles_save_error_gracefully()`:
    - Mock storage.save_entry to raise exception
    - Verify parse_node still returns successfully with parsed data

- [x] Task 3: Add integration test for LOG file creation (AC: #5)
  - [x] 3.1: Create `packages/quilto/tests/test_log_persistence.py`
  - [x] 3.2: Test `test_log_creates_raw_file()`:
    - Setup temp storage directory using `tmp_path` fixture
    - Mock LLM client to return valid parser response
    - Run parse_node through LangGraph
    - Assert raw file exists at expected path
  - [x] 3.3: Test `test_log_creates_parsed_json()`:
    - Same setup as 3.2
    - Assert parsed JSON file exists and contains entry

- [x] Task 4: Verify CORRECTION flow unchanged (AC: #3)
  - [x] 4.1: Run existing correction tests: `pytest packages/quilto/tests/test_correction_flow.py -v`
  - [x] 4.2: Manual verification that correction still edits in-place (not duplicates)

- [x] Task 5: Validation
  - [x] 5.1: Run `make check` - lint + typecheck
  - [x] 5.2: Run `make validate` - full validation suite
  - [x] 5.3: Manual dogfooding verification per CLAUDE.md rules:
    ```bash
    # Before
    ls -la logs/raw/2026/01/ 2>/dev/null | wc -l

    # Run LOG
    uv run swealog run --config ./llm-config-openai.yaml --storage ./logs --debug "I did 10 pushups"

    # After - must show 1 more file
    ls -la logs/raw/2026/01/ 2>/dev/null | wc -l
    cat logs/raw/2026/01/$(date +%Y-%m-%d).md  # Verify content
    ```

## Dev Notes

### Root Cause (From Investigation 23.1)

**Location:** `packages/quilto/quilto/orchestration.py`, function `parse_node()` (lines 942-998)

The `parse_node()` function parses input correctly but returns immediately without calling `storage.save_entry()`. The graph edge at line 1374 goes directly from `parse` to `observe` with no save step.

**CORRECTION flow works** because `correction_node()` calls `process_correction()` which explicitly saves via `storage.edit_raw_section()` and `storage._save_parsed_json()`.

### Required Code Changes

**File:** `packages/quilto/quilto/orchestration.py`

**Location:** Inside `parse_node()`, after line 983 (after progress handler call), before the return statement.

**Imports to add at module level:**
```python
import uuid
from quilto.storage.models import Entry
```

**Code to add in parse_node() after progress handler:**
```python
# Save entry to storage for LOG persistence
try:
    entry = Entry(
        id=f"{datetime.now(UTC).strftime('%Y-%m-%d_%H-%M-%S')}_{uuid.uuid4().hex[:6]}",
        date=datetime.now(UTC).date(),
        timestamp=datetime.now(UTC),
        raw_content=user_input,
        parsed_data=parser_output.domain_data,
    )
    quilto.storage.save_entry(entry)
    logging.debug(f"Saved LOG entry: {entry.id}")
except Exception as e:
    logging.warning(f"Failed to save LOG entry to storage: {e}")
    # Continue - save failure should not block parse response
```

### Entry ID Format

The Entry ID uses format `YYYY-MM-DD_HH-MM-SS_xxxxxx` where `xxxxxx` is 6 hex characters from UUID, which:
- Is human-readable (date/time prefix)
- Is file-system safe (no colons)
- Guarantees uniqueness even within the same second (UUID suffix)
- Matches the existing ID pattern concept in storage/models.py docstring

### Error Handling Strategy

Save failures are logged but do not fail the parse operation because:
- User should still see their parsed data even if storage fails
- Storage issues can be transient (disk full, permissions)
- Critical path is parsing; persistence is secondary

### Existing Patterns

**CORRECTION flow (reference for save pattern):**
- `correction_node()` at line 1042 calls `process_correction(storage=quilto.storage, ...)`
- `process_correction()` at correction.py:151 calls `storage.edit_raw_section()`
- `process_correction()` at correction.py:179 calls `storage._save_parsed_json()`

**StorageRepository.save_entry() (lines 264-307):**
- Accepts `Entry` object
- Creates/appends to `raw/YYYY/MM/YYYY-MM-DD.md`
- Creates/updates `parsed/YYYY/MM/YYYY-MM-DD.json`
- Already handles directory creation

### Test Patterns to Follow

See `packages/quilto/tests/test_storage.py`:
- Uses `tmp_path` fixture for isolated file system
- Uses `create_parser_output()` helper for test data
- Tests both model validation and file operations

### Project Structure Notes

- **Quilto package:** All code changes in `packages/quilto/quilto/`
- **Entry model:** Already exists in `quilto.storage.models`
- **StorageRepository:** Has `save_entry()` method already implemented
- **No changes to Swealog** needed - this is a Quilto framework fix

### Pre-Review Checklist (From CLAUDE.md)

- [x] `make check` passes (lint + typecheck)
- [x] All new functions have Google-style docstrings
- [x] Unit tests cover new functionality
- [x] File-level verification performed (not just intermediate outputs)

### References

- [Source: `orchestration.py:942-998`, parse_node() - where fix goes]
- [Source: `orchestration.py:1374`, graph edge parse→observe]
- [Source: `correction.py:151`, edit_raw_section() - CORRECTION save pattern]
- [Source: `repository.py:264-307`, save_entry() implementation]
- [Source: `_bmad-output/implementation-artifacts/epic-23/23-1-investigation-report.md`]
- [Source: `CLAUDE.md`, Dogfooding Verification Rules]

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

- Dogfooding test session: `834ce2f7-bc53-46f9-a164-a1a6fb2cc921`
- Raw file created: `logs/raw/2026/01/2026-01-30.md`
- Parsed JSON created: `logs/parsed/2026/01/2026-01-30.json`
- Entry ID: `2026-01-30_01-33-35_123cf6`

### Completion Notes List

1. Added `uuid` import and `Entry` import to orchestration.py
2. Added save_entry call in parse_node() after parser completes and progress handler is called
3. Used try/except to ensure save failures don't block parsing
4. Created 4 unit tests in test_orchestration_parse_save.py
5. Created 4 integration tests in test_log_persistence.py
6. All 2247 tests pass (112 skipped)
7. Correction flow unchanged - 42 passed, 2 skipped
8. Dogfooding verified: LOG creates both raw and parsed files

### File List

| File | Action | Purpose |
|------|--------|---------|
| `packages/quilto/quilto/orchestration.py` | Modified | Added uuid import, Entry import, and save_entry call in parse_node |
| `packages/quilto/tests/test_orchestration_parse_save.py` | Created | 4 unit tests for parse_node save behavior |
| `packages/quilto/tests/test_log_persistence.py` | Created | 4 integration tests for LOG file creation |

## Senior Developer Review (AI)

**Reviewer:** Claude Opus 4.5 | **Date:** 2026-01-30

### Issues Found & Fixed

| Severity | Issue | Fix Applied |
|----------|-------|-------------|
| HIGH | Timestamp drift - `datetime.now(UTC)` called 3x independently in Entry creation could cause inconsistent data at second boundaries | Captured `now = datetime.now(UTC)` once and reused |
| MEDIUM | Test timing sensitivity - assertion could fail at midnight boundary | Captured expected date before/after call, allow either |

### Review Outcome

**APPROVED** - All HIGH/MEDIUM issues fixed. Code review complete.

