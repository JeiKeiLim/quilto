# Story 17.2: Remove Storage Path Doubling

Status: done

## Story

As a **Quilto framework user**,
I want `--storage ./logs` to store data in `./logs/`,
so that the path I specify is the actual storage location.

## Acceptance Criteria

1. **Given** `StorageRepository(base_path=Path("logs"))`
   **When** `_get_raw_path()` is called
   **Then** returns `logs/raw/...` (not `logs/logs/raw/...`)

2. **Given** `StorageRepository(base_path=Path("."))`
   **When** `_get_parsed_path()` is called
   **Then** returns `parsed/...` (not `logs/parsed/...`)

3. **Given** existing data in `./logs/raw/`
   **When** Retriever searches with `--storage ./logs`
   **Then** entries are found (via `get_entries_by_pattern()`)

4. **Given** global context update
   **When** `update_global_context()` is called
   **Then** writes to `{base_path}/context/global.md` (not `{base_path}/logs/context/global.md`)

5. **Given** storage summary request
   **When** `get_storage_summary()` is called
   **Then** scans `{base_path}/raw/` (not `{base_path}/logs/raw/`)

6. **Given** class docstring
   **When** developer reads `StorageRepository`
   **Then** Directory Structure shows `{base_path}/raw/`, `{base_path}/parsed/`, `{base_path}/context/` (not `{base_path}/logs/...`)

## Tasks

Remove `/logs/` segment from all internal paths. This is a simple find-and-replace operation.

**Pattern:** Change `self.base_path / "logs" / X` to `self.base_path / X`

- [x] Task 1: `_ensure_directories()` - 3 mkdir() calls (raw, parsed, context)
- [x] Task 2: `_get_raw_path()` - path construction
- [x] Task 3: `_get_parsed_path()` - path construction
- [x] Task 4: `get_entries_by_pattern()` - raw_base assignment
- [x] Task 5: `get_global_context()` - context_path assignment
- [x] Task 6: `update_global_context()` - context_path assignment
- [x] Task 7: `get_storage_summary()` - raw_path assignment
- [x] Task 8: Class docstring - update Directory Structure example
- [x] Task 9: Tests - update all path assertions (see Test Modifications below)
- [x] Task 10: Validate - run `make validate`, verify reproduction command

## Files Modified

| File | Changes |
|------|---------|
| `packages/quilto/quilto/storage/repository.py` | 9 code lines + docstring |
| `packages/quilto/tests/test_storage.py` | ~50 path assertions |

## Code Changes (repository.py)

| Line | Current | New |
|------|---------|-----|
| 23-26 | `{base_path}/logs/raw/...` | `{base_path}/raw/...` |
| 48 | `self.base_path / "logs" / "raw"` | `self.base_path / "raw"` |
| 49 | `self.base_path / "logs" / "parsed"` | `self.base_path / "parsed"` |
| 50 | `self.base_path / "logs" / "context"` | `self.base_path / "context"` |
| 62-63 | `self.base_path / "logs" / "raw"` | `self.base_path / "raw"` |
| 80-81 | `self.base_path / "logs" / "parsed"` | `self.base_path / "parsed"` |
| 210 | `self.base_path / "logs" / "raw"` | `self.base_path / "raw"` |
| 371 | `self.base_path / "logs" / "context" / "global.md"` | `self.base_path / "context" / "global.md"` |
| 382 | `self.base_path / "logs" / "context" / "global.md"` | `self.base_path / "context" / "global.md"` |
| 398 | `self.base_path / "logs" / "raw"` | `self.base_path / "raw"` |

## Test Modifications (test_storage.py)

**Strategy:** Global find-replace in test file:
- Replace `tmp_path / "logs" / "raw"` with `tmp_path / "raw"`
- Replace `tmp_path / "logs" / "parsed"` with `tmp_path / "parsed"`
- Replace `tmp_path / "logs" / "context"` with `tmp_path / "context"`

**Test classes affected:**
- `TestStorageRepositoryInit` (lines 47-56) - directory assertions
- `TestGetEntriesByDateRange` (lines 144, 161, 178, 183) - raw dir creation
- `TestGetEntriesByPattern` (lines 202-205, 220-223) - raw dir creation
- `TestSearchEntries` (lines 246-247, 257-259, 273-275, 285-287, 297-299, 312-314) - raw dir creation
- `TestSaveEntry` (lines 339, 346, 373, 393) - path assertions
- `TestCorrections` (lines 429, 434, 443-445, 461) - path assertions
- `TestGlobalContext` (line 500) - context path assertion
- `TestEdgeCases` (lines 528-531, 547-550, 565-566, 581-582, 596-602, 614-615) - raw dir creation
- `TestStorageSummary` (lines 680-681, 695-696, 713-716, 732-735, 751-752, 769-772) - raw dir creation

**Total:** ~50 occurrences of `/ "logs" /` pattern

## Validation

```bash
# 1. Run full validation suite
make validate

# 2. Verify fix with Python REPL
uv run python3 -c "
from quilto.storage import StorageRepository
from pathlib import Path
from datetime import date

r = StorageRepository(Path('test_logs'))
print('raw path:', r._get_raw_path(date.today()))
print('parsed path:', r._get_parsed_path(date.today()))
# Expected: test_logs/raw/... (NOT test_logs/logs/raw/...)
"

# 3. Verify original reproduction command works
uv run swealog run --config ./llm-config-openai.yaml --storage ./logs --debug --non-interactive "How was my workout this week?"
```

## Dev Notes

### Root Cause
[Source: `17-1-query-flow-investigation.md`]

- `StorageRepository` internally adds `/logs/` to `base_path`
- When user passes `--storage ./logs`, result is `./logs/logs/raw/...`
- Data exists in `./logs/raw/` but storage looks in `./logs/logs/raw/`

### Breaking Change

| Before | After |
|--------|-------|
| `StorageRepository(Path("."))` | `StorageRepository(Path("logs"))` |
| `--storage .` | `--storage logs` |

**User Migration:** If user has data in `old_path/logs/raw/`, move to `new_path/raw/`.

### Architecture Alignment
[Source: `architecture.md#directory-structure`]

The architecture document shows:
```
logs/
├── raw/{YYYY}/{MM}/{YYYY-MM-DD}.md
├── parsed/{YYYY}/{MM}/{YYYY-MM-DD}.json
└── context/global.md
```

The `logs/` refers to the **storage root**, not an additional subdirectory. This fix aligns implementation with architectural intent.

### Project Structure

- **Package:** Quilto (`packages/quilto/`)
- **File:** `quilto/storage/repository.py`
- All changes are in the Quilto framework
- Swealog requires no changes (proper Quilto consumer)

### References

- [Source: `17-1-query-flow-investigation.md` - Issue 1: Storage Path Doubling]
- [Source: `architecture.md#directory-structure`]
- [Source: `epics.md#story-172-remove-storage-path-doubling`]

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

N/A - Straightforward find-and-replace implementation

### Completion Notes List

1. Removed `/logs/` path segment from all 9 code locations in `repository.py`
2. Updated class docstring to show `{base_path}/` instead of `{base_path}/logs/`
3. Updated ~50 test path assertions across 5 test files:
   - `packages/quilto/tests/test_storage.py` - main storage tests
   - `packages/quilto/tests/test_correction_flow.py` - correction flow integration
   - `packages/quilto/tests/test_observer_integration.py` - observer context tests
   - `packages/quilto/tests/test_retriever.py` - retriever integration tests
   - `packages/swealog/tests/test_cli_utils.py` - CLI dependency tests
4. All 2024 tests pass, 101 skipped (expected)
5. Verification command confirms fix: `StorageRepository(Path('test_logs'))` now creates `test_logs/raw/...` instead of `test_logs/logs/raw/...`

### File List

| File | Changes |
|------|---------|
| `packages/quilto/quilto/storage/repository.py` | Removed `/logs/` from 9 path constructions + updated docstring |
| `packages/quilto/tests/test_storage.py` | Updated ~50 path assertions |
| `packages/quilto/tests/test_correction_flow.py` | Updated 2 path assertions |
| `packages/quilto/tests/test_observer_integration.py` | Updated 6 path assertions |
| `packages/quilto/tests/test_retriever.py` | Updated 2 path assertions |
| `packages/swealog/tests/test_cli_utils.py` | Updated 3 path assertions + comment |
| `packages/swealog/tests/test_cli_import.py` | No changes required (no path assertions affected) |

### Code Review Notes

**Reviewed by:** Claude Opus 4.5 (Amelia - Dev Agent)
**Review Date:** 2026-01-28

**Findings Addressed:**
1. ✅ Status updated from `review` to `done`
2. ✅ Added `test_cli_import.py` to File List (git shows modified but no path assertions changed - file touched during testing)
3. ⚠️ `llm-config-openai.yaml` modified in git but unrelated to this story (user workspace change, not reverted)
