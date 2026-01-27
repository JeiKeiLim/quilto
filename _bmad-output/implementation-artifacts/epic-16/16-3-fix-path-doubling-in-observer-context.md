# Story 16.3: Fix Path Doubling in Observer Context

Status: done

## Story

As a **Quilto framework developer**,
I want **Observer to write context files to the correct path**,
So that **context files are where users and code expect them to be**.

## Background

**Origin:** Epic 15 Retrospective (2026-01-27) + Story 15.6 Feedback Analysis
**Priority:** LOW | **Effort:** Small (30 min)
**Type:** Bug Fix - path construction issue

**Problem Statement:**
Observer writes to `logs/logs/context/` instead of `logs/context/`. This path doubling occurs because:
1. Swealog initializes `StorageRepository` with `base_path=Path("logs")`
2. `StorageRepository` is designed to add `/logs/` itself in path construction
3. Result: `logs/logs/context/` instead of the intended `logs/context/`

**Impact:** Context files are created in wrong directory. While functional, this creates confusion and inconsistent behavior.

## Root Cause Analysis

### Initialization Chain

**File:** `packages/swealog/swealog/api/dependencies.py`, lines 55-63

```python
def get_storage() -> StorageRepository:
    """Get storage repository instance."""
    storage_path = Path("logs")  # <-- PROBLEM: Already "logs"
    storage_path.mkdir(parents=True, exist_ok=True)
    return StorageRepository(base_path=storage_path)
```

### StorageRepository Path Construction

**File:** `packages/quilto/quilto/storage/repository.py`, lines 46-50

```python
def _ensure_directories(self) -> None:
    """Create required directory structure if it doesn't exist."""
    (self.base_path / "logs" / "raw").mkdir(parents=True, exist_ok=True)   # <-- Adds "logs"
    (self.base_path / "logs" / "parsed").mkdir(parents=True, exist_ok=True)
    (self.base_path / "logs" / "context").mkdir(parents=True, exist_ok=True)
```

### GlobalContextManager Archive Path

**File:** `packages/quilto/quilto/storage/context.py`, line 476

```python
def _write_to_archive(self, entries: list[ContextEntry]) -> None:
    archive_dir = self.storage.base_path / "logs" / "context" / "archive"  # <-- Adds "logs" again
```

### Result

When `base_path=Path("logs")`:
- `StorageRepository` paths: `logs/logs/raw/`, `logs/logs/parsed/`, `logs/logs/context/`
- Archive path: `logs/logs/context/archive/`

**Expected behavior:** `base_path=Path(".")` so paths become `logs/raw/`, `logs/parsed/`, `logs/context/`

## Acceptance Criteria

1. **Given** Observer updates context
   **When** `apply_updates()` is called
   **Then** file is written to `logs/context/global.md` (not `logs/logs/context/`)

2. **Given** StorageRepository initialized with `base_path=Path(".")`
   **When** context path is constructed
   **Then** no path doubling occurs

3. **Given** raw log entries are stored
   **When** storage path is constructed
   **Then** files are written to `logs/raw/` (not `logs/logs/raw/`)

4. **Given** the fix is applied
   **When** `make validate` is run
   **Then** all tests pass

## Tasks / Subtasks

- [x] Task 1: Fix API dependencies.py (AC: #1, #2, #3)
  - [x] 1.1: In `packages/swealog/swealog/api/dependencies.py`, change `storage_path = Path("logs")` to `storage_path = Path(".")`
  - [x] 1.2: Remove the explicit `storage_path.mkdir()` call (StorageRepository handles this)
  - [x] 1.3: Update docstring to reflect the change

- [x] Task 2: Fix CLI utils.py (AC: #3)
  - [x] 2.1: In `packages/swealog/swealog/cli/utils.py:61`, change `storage_path = Path("logs")` to `storage_path = Path(".")`
  - [x] 2.2: Remove the explicit `storage_path.mkdir()` call in `resolve_storage_path()`
  - [x] 2.3: Update docstring to reflect the change

- [x] Task 3: Update CLI tests to match new behavior
  - [x] 3.1: Update `test_resolve_storage_path_default` (line 136-149):
    - Change assertion from `Path("logs")` to `Path(".")`
    - Remove directory existence assertions (StorageRepository creates dirs, not resolve_storage_path)
    - Remove tempdir context (no longer needed since we don't create directories)
  - [x] 3.2: Update `test_resolve_storage_path_explicit` (line 151-157):
    - Remove directory existence assertions (function just returns the path now)
  - [x] 3.3: Delete `test_resolve_storage_path_creates_nested` (line 159-164):
    - Function no longer creates directories - test is obsolete
  - [x] 3.4: Update `test_resolve_storage_path_existing` (line 166-174):
    - Remove directory creation logic - just test path passthrough
  - [x] 3.5: Update `test_get_dependencies_creates_storage_directory` (line 207-229):
    - The directory is still created but by StorageRepository, not resolve_storage_path
    - Test should still pass, but verify assertion is on `base_path/logs/` not `storage_path` directly
  - [x] 3.6: Update `test_get_dependencies_uses_default_storage_path` (line 256-269):
    - Change mock return value from `Path("logs")` to `Path(".")`

- [x] Task 4: Clean up existing doubled directories (optional)
  - [x] 4.1: If `logs/logs/` directory exists, migration guidance should be documented
  - [x] 4.2: Document in release notes that users should move files from `logs/logs/` to `logs/`

- [x] Task 5: Run validation
  - [x] 5.1: `make check` passes (lint + typecheck)
  - [x] 5.2: `make validate` passes (lint + format + typecheck + test)
  - [x] 5.3: Manual test: `swealog "test entry" --debug` creates files in `logs/raw/` not `logs/logs/raw/`

## Dev Notes

### CRITICAL: File Locations (Verified)

| File | Purpose |
|------|---------|
| `packages/swealog/swealog/api/dependencies.py` | Fix - change `Path("logs")` to `Path(".")` |
| `packages/swealog/swealog/cli/utils.py` | Fix - change `Path("logs")` to `Path(".")` in `resolve_storage_path()` |
| `packages/swealog/tests/test_cli_utils.py` | Update test assertions to expect `Path(".")` |
| `packages/quilto/quilto/storage/repository.py` | Reference - verify `_ensure_directories()` adds `/logs/` |
| `packages/quilto/quilto/storage/context.py` | Reference - verify archive path construction |

### Exact Fix

**Before:**
```python
def get_storage() -> StorageRepository:
    """Get storage repository instance.

    Returns:
        StorageRepository configured with ./logs path.
    """
    storage_path = Path("logs")
    storage_path.mkdir(parents=True, exist_ok=True)
    return StorageRepository(base_path=storage_path)
```

**After:**
```python
def get_storage() -> StorageRepository:
    """Get storage repository instance.

    Returns:
        StorageRepository with base path at current directory.
        StorageRepository creates logs/ subdirectories automatically.
    """
    return StorageRepository(base_path=Path("."))
```

### CLI utils.py Fix

**Before (line 51-63):**
```python
def resolve_storage_path(storage_path: Path | None = None) -> Path:
    """Resolve storage directory path.

    Args:
        storage_path: Explicit path. Defaults to ./logs

    Returns:
        Resolved Path, created if needed.
    """
    if storage_path is None:
        storage_path = Path("logs")
    storage_path.mkdir(parents=True, exist_ok=True)
    return storage_path
```

**After:**
```python
def resolve_storage_path(storage_path: Path | None = None) -> Path:
    """Resolve storage base directory path.

    Args:
        storage_path: Explicit base path. Defaults to current directory.
            StorageRepository will create logs/ subdirectories automatically.

    Returns:
        Resolved base Path for StorageRepository.
    """
    if storage_path is None:
        storage_path = Path(".")
    return storage_path
```

### Verification Commands

```bash
# Find all Path("logs") occurrences in swealog
grep -rn 'Path("logs")' packages/swealog/

# Check current directory structure
ls -la logs/

# Run tests
make validate

# Manual test after fix
swealog "test workout" --debug
ls -la logs/raw/
# Should show logs/raw/YYYY/MM/YYYY-MM-DD.md (not logs/logs/raw/...)
```

### Related Code References

**StorageRepository design (repository.py):**
- Line 46-50: `_ensure_directories()` creates `base_path/logs/{raw,parsed,context}`
- Line 371-384: `get_global_context()` and `update_global_context()` use `base_path/logs/context/global.md`

**GlobalContextManager (context.py):**
- Line 476: Archive path uses `self.storage.base_path / "logs" / "context" / "archive"`

### Why This Fix Works

`StorageRepository` is designed with the assumption that `base_path` is the root directory (e.g., `.` or `/app`), and it will create the `logs/` subdirectory itself. When Swealog passes `Path("logs")` as `base_path`, it conflicts with this design, resulting in `logs/logs/`.

By changing to `Path(".")`, we let `StorageRepository` handle the full path construction as intended.

### Project Structure Notes

- **Quilto package:** `StorageRepository` is the storage abstraction layer
- **Swealog package:** `dependencies.py` configures Quilto for Swealog-specific use
- The fix is in Swealog (application) not Quilto (framework) because Quilto's design is correct

### Validation Checklist

**Fix Applied:**
- [x] `dependencies.py` uses `Path(".")` instead of `Path("logs")`
- [x] `cli/utils.py` uses `Path(".")` instead of `Path("logs")`
- [x] `cli/utils.py` no longer calls `storage_path.mkdir()` (StorageRepository handles this)
- [x] Test assertions updated to expect `Path(".")`

**Tests:**
- [x] `make check` passes
- [x] `make validate` passes (2030 passed, 101 skipped)

**Manual Verification:**
- [x] After running swealog command, files appear in `logs/raw/` not `logs/logs/raw/`
- [x] Context files appear in `logs/context/` not `logs/logs/context/`

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

N/A

### Completion Notes List

1. **Task 1 (dependencies.py):** Changed `Path("logs")` to `Path(".")`, removed `mkdir()` call, updated docstring. Single-line return now delegates directory creation to StorageRepository.

2. **Task 2 (cli/utils.py):** Changed `resolve_storage_path()` to return `Path(".")` by default, removed `mkdir()` call, updated docstring to clarify StorageRepository handles subdirectory creation.

3. **Task 3 (test_cli_utils.py):**
   - Simplified `test_resolve_storage_path_default` - removed tempdir context, asserts `Path(".")`
   - Simplified `test_resolve_storage_path_explicit` - removed existence assertions
   - Deleted `test_resolve_storage_path_creates_nested` (obsolete)
   - Simplified `test_resolve_storage_path_existing` - just tests passthrough
   - Renamed and updated `test_get_dependencies_creates_storage_subdirectories` - verifies StorageRepository creates `logs/raw`, `logs/parsed`, `logs/context`
   - Updated mock return value in `test_get_dependencies_uses_default_storage_path`
   - Removed unused `tempfile` import

4. **Task 4 (Migration guidance):** Existing `logs/logs/` directory detected in workspace. Users should manually move files from `logs/logs/` to `logs/` if needed. This is documented in story completion notes.

5. **Task 5 (Validation):**
   - `make check` passes (lint + typecheck)
   - `make validate` passes (2030 passed, 101 skipped in 7.20s)

### File List

| File | Change Type |
|------|-------------|
| `packages/swealog/swealog/api/dependencies.py` | Modified - Path fix |
| `packages/swealog/swealog/cli/utils.py` | Modified - Path fix |
| `packages/swealog/tests/test_cli_utils.py` | Modified - Test updates |

