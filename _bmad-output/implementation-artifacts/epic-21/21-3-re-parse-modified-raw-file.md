# Story 21.3: Re-Parse Modified Raw File After Correction

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **Swealog user**,
I want **the parsed entry to update after raw file correction**,
so that **structured data reflects the correction**.

## Acceptance Criteria

1. **Given** raw file has been corrected
   **When** re-parsing is triggered
   **Then** Parser processes the modified section

2. **Given** Parser output for corrected section
   **When** compared to existing parsed entry
   **Then** existing parsed entry is **replaced** (not merged via delta)

3. **Given** other sections in the same raw file
   **When** re-parsing runs
   **Then** their parsed entries are unchanged

4. **Given** a field was removed in the correction (e.g., original had `notes`, correction doesn't)
   **When** parsed JSON is updated
   **Then** the removed field is NOT in the final parsed entry (replace semantics, not merge)

## Tasks / Subtasks

- [x] Task 1: Analyze current re-parse behavior (AC: #1, #2, #4)
  - [x] 1.1: Read `packages/quilto/quilto/flow/correction.py:166-187` to understand current re-parse flow
  - [x] 1.2: Read `packages/quilto/quilto/storage/repository.py:330-353` to confirm `_update_parsed_json` uses `.update()` merge semantics
  - [x] 1.3: Identify the bug: correction flow calls `_update_parsed_json(parsed_path, target_entry_id, reparse_output.domain_data)` but `.update()` merges instead of replaces - old fields may persist
  - [x] 1.4: Document in Dev Notes: need `_replace_parsed_json()` or change call to `_save_parsed_json()`

- [x] Task 2: Fix parsed entry update to use replace semantics (AC: #2, #4)
  - [x] 2.1: In `packages/quilto/quilto/flow/correction.py` line 179, change from `_update_parsed_json()` to `_save_parsed_json()` which uses assignment (`existing[entry_id] = parsed_data`) not merge
  - [x] 2.2: Update docstring comment at line 176-177 to clarify: "Replace (not update) the parsed JSON entry with fresh parse"
  - [x] 2.3: Verify `_save_parsed_json()` at repository.py:309-328 uses `existing[entry_id] = parsed_data` (assignment, not `.update()`)

- [x] Task 3: Add test for field removal scenario (AC: #4) — **can run in parallel with Task 4**
  - [x] 3.1: Add test `test_correction_reparse_removes_old_fields` in `packages/quilto/tests/test_correction_flow.py` under `TestStorageRepositoryCorrectionIntegration` class
    - Create entry with fields: `{"exercise": "bench press", "weight_kg": 80, "notes": "felt good"}`
    - Edit raw section to content that doesn't mention notes (e.g., "bench press 85kg")
    - Re-parse using Parser (or simulate with direct domain_data)
    - Update parsed JSON with re-parse output: `{"exercise": "bench press", "weight_kg": 85}` (no notes)
    - Assert `"notes" not in parsed_data` - field should be gone (replace semantics)

- [x] Task 4: Add test for multi-section isolation (AC: #3) — **can run in parallel with Task 3**
  - [x] 4.1: Add test `test_reparse_only_updates_target_entry` in `packages/quilto/tests/test_correction_flow.py`
    - Create raw file with 2 entries: `2026-01-14_08-30-00` and `2026-01-14_18-30-00`
    - Save both to parsed JSON
    - Edit only the second entry's raw section
    - Re-parse and update only the second entry
    - Assert first entry's parsed data is unchanged (byte-identical)
    - Assert second entry's parsed data reflects the correction

- [x] Task 5: Verify existing tests still pass (AC: #1, #2)
  - [x] 5.1: Run `uv run pytest packages/quilto/tests/test_correction_flow.py -v` - all tests pass
  - [x] 5.2: Run `uv run pytest packages/quilto/tests/test_storage.py::TestCorrections -v` - all tests pass

- [x] Task 6: Run validation (AC: #1-#4)
  - [x] 6.1: Run `make check` (lint + typecheck) - 0 errors
  - [x] 6.2: Run `make validate` (full validation with unit tests) - all tests pass

## Dev Notes

### Problem Statement

**Current Behavior (Potentially Buggy):**
```python
# correction.py:179
storage._update_parsed_json(parsed_path, target_entry_id, reparse_output.domain_data)

# repository.py:350
existing[entry_id].update(correction_delta)  # MERGE semantics
```

If original entry has `{"exercise": "bench press", "weight_kg": 80, "notes": "felt good"}` and the corrected re-parse output is `{"exercise": "bench press", "weight_kg": 85}`, the **current** behavior would produce:
```json
{"exercise": "bench press", "weight_kg": 85, "notes": "felt good"}  // notes STILL THERE!
```

**Expected Behavior:**
```json
{"exercise": "bench press", "weight_kg": 85}  // notes GONE
```

### Root Cause

`_update_parsed_json()` was designed for partial delta updates (e.g., "just update weight_kg to 84"). But after re-parsing a corrected raw file, we have the **complete** new parsed data and should **replace** the entire entry, not merge.

### Solution

Change `correction.py:179` from:
```python
storage._update_parsed_json(parsed_path, target_entry_id, reparse_output.domain_data)
```

To:
```python
storage._save_parsed_json(parsed_path, target_entry_id, reparse_output.domain_data)
```

`_save_parsed_json()` uses assignment: `existing[entry_id] = parsed_data` (repository.py:325)

### Why This Is a Separate Story

Story 21.1 implemented the re-parse flow but used `_update_parsed_json()` which was already available. This story specifically addresses the **semantic difference** between merge and replace, which wasn't explicitly validated in 21.1.

### Existing Code References

| File | Line | Purpose |
|------|------|---------|
| `correction.py` | 166-174 | Re-parse flow (reads modified section) |
| `correction.py` | 176-187 | Update parsed JSON (CHANGE THIS) |
| `repository.py` | 309-328 | `_save_parsed_json()` - uses assignment |
| `repository.py` | 330-353 | `_update_parsed_json()` - uses `.update()` merge |

### Test Strategy

1. **Field Removal Test**: Verify that fields in original but not in re-parse are removed
2. **Multi-Entry Isolation Test**: Verify other entries in same day file are unchanged
3. **Regression Tests**: All existing correction tests must pass

### Anti-Patterns to Avoid

| Anti-Pattern | Correct Approach |
|--------------|------------------|
| Add new method when existing works | Use `_save_parsed_json()` instead of creating `_replace_parsed_json()` |
| Test only happy path | Test field removal (the bug scenario) |
| Assume current tests cover this | Add explicit test for replace-not-merge |

### Architecture Compliance

| Requirement | Status |
|-------------|--------|
| Changes in Quilto (not Swealog) | Yes - all changes are framework-level |
| Minimal change | Yes - single line change + 2 new tests |
| Existing patterns followed | Yes - uses existing `_save_parsed_json()` |

### File Structure Requirements

```
packages/quilto/quilto/
  flow/
    correction.py          # MODIFY - Change line 179 from _update to _save
packages/quilto/tests/
  test_correction_flow.py  # MODIFY - Add 2 new tests in TestStorageRepositoryCorrectionIntegration
```

### References

| Document | Line/Section | Purpose |
|----------|--------------|---------|
| `epics.md` | Story 21.3 (line ~3622) | Acceptance criteria source |
| `21-1-*.md` | Completion Notes | Previous story - implemented re-parse flow |
| `21-2-*.md` | Completion Notes | Previous story - surgical edit verified |
| `correction.py` | Line 179 | **CHANGE THIS** |
| `repository.py` | Line 325 | `_save_parsed_json()` uses assignment |
| `repository.py` | Line 350 | `_update_parsed_json()` uses `.update()` |

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

N/A

### Completion Notes List

1. **Bug Confirmed**: `correction.py:179` called `_update_parsed_json()` which at `repository.py:350` does `existing[entry_id].update(correction_delta)` (merge semantics). Old fields persisted after re-parse.

2. **Fix Applied**: Changed `correction.py:179` from `_update_parsed_json()` to `_save_parsed_json()` which uses `existing[entry_id] = parsed_data` (assignment = replace semantics).

3. **Tests Added**:
   - `test_correction_reparse_removes_old_fields`: Verifies AC #4 - fields in original but not in re-parse output are removed
   - `test_reparse_only_updates_target_entry`: Verifies AC #3 - other entries in same day file remain unchanged

4. **Validation Results**:
   - 42/42 correction flow tests pass
   - 2/2 storage correction tests pass
   - `make check`: 0 lint/type errors
   - `make validate`: 2174 passed, 101 skipped

### File List

- `packages/quilto/quilto/flow/correction.py` — Changed `_update_parsed_json()` to `_save_parsed_json()` at line 179
- `packages/quilto/tests/test_correction_flow.py` — Added 2 new tests in `TestStorageRepositoryCorrectionIntegration`
- `packages/quilto/tests/test_storage.py` — Formatting changes from linter (no functional changes)
