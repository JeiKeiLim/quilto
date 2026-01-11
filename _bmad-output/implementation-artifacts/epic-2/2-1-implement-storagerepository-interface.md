# Story 2.1: Implement StorageRepository Interface

Status: completed

## Story

As a **Quilto developer**,
I want a **StorageRepository with 6 core methods**,
So that **agents can read/write entries without knowing file structure**.

## Acceptance Criteria

1. **Given** a configured `base_path`
   **When** I instantiate `StorageRepository(base_path)`
   **Then** the repository initializes without error
   **And** validates that `base_path` exists or creates it

2. **Given** a StorageRepository instance
   **When** I call `get_entries_by_date_range(start, end)`
   **Then** it returns all entries between start and end dates (inclusive)
   **And** entries are loaded from `logs/raw/{YYYY}/{MM}/{YYYY-MM-DD}.md`
   **And** parsed data is loaded from `logs/parsed/{YYYY}/{MM}/{YYYY-MM-DD}.json` if available

3. **Given** a StorageRepository instance
   **When** I call `get_entries_by_pattern("2026/01/**/*.md")`
   **Then** it returns entries matching the glob pattern
   **And** pattern is resolved relative to `logs/raw/`

4. **Given** a StorageRepository instance
   **When** I call `search_entries(keywords=["bench", "press"], match_all=True)`
   **Then** it returns entries containing ALL keywords
   **And** when `match_all=False` it returns entries containing ANY keyword
   **And** optional `date_range` parameter filters results

5. **Given** a new Entry to save
   **When** I call `save_entry(entry)`
   **Then** raw markdown is saved to `logs/raw/{YYYY}/{MM}/{YYYY-MM-DD}.md`
   **And** entry is appended to existing file if date already has entries
   **And** parsed JSON is saved to `logs/parsed/{YYYY}/{MM}/{YYYY-MM-DD}.json`

6. **Given** a correction Entry
   **When** I call `save_entry(entry, correction=ParserOutput(...))`
   **Then** correction note is appended to raw markdown (preserves history)
   **And** parsed JSON is updated with correction delta (upsert semantics)

7. **Given** global context operations
   **When** I call `get_global_context()`
   **Then** it returns the markdown content from `logs/context/global.md`
   **And** returns empty string if file doesn't exist

8. **Given** global context update
   **When** I call `update_global_context(content)`
   **Then** it overwrites `logs/context/global.md` with new content

## Tasks / Subtasks

- [x] Task 1: Create storage module structure (AC: #1)
  - [x] Create `packages/quilto/quilto/storage/` directory
  - [x] Create `__init__.py` with exports
  - [x] Create `repository.py` for StorageRepository class
  - [x] Create `models.py` for Entry, DateRange, and related types

- [x] Task 2: Define Entry and related models (AC: #2, #3, #4, #5)
  - [x] Define `Entry` model with: id, date, raw_content, parsed_data, timestamp
  - [x] Define `DateRange` model with: start, end dates
  - [x] Define `ParserOutput` model (stub for correction support)
  - [x] Add strict Pydantic validation with `ConfigDict(strict=True)`

- [x] Task 3: Implement StorageRepository initialization (AC: #1)
  - [x] Accept `base_path: Path` parameter
  - [x] Create required directories if missing (`raw/`, `parsed/`, `context/`)
  - [x] Store base_path as instance attribute

- [x] Task 4: Implement get_entries_by_date_range (AC: #2)
  - [x] Generate file paths for date range
  - [x] Load raw markdown files
  - [x] Load corresponding parsed JSON if exists
  - [x] Return list of Entry objects

- [x] Task 5: Implement get_entries_by_pattern (AC: #3)
  - [x] Use pathlib.glob with pattern relative to `logs/raw/`
  - [x] Load matching files as entries
  - [x] Return list of Entry objects

- [x] Task 6: Implement search_entries (AC: #4)
  - [x] Accept keywords, optional date_range, match_all flag
  - [x] If date_range provided, filter by date first
  - [x] Search content for keyword matches (case-insensitive)
  - [x] Implement AND (match_all=True) vs OR (match_all=False) logic

- [x] Task 7: Implement save_entry (AC: #5, #6)
  - [x] Create directory structure if needed
  - [x] For new entries: create/append to raw markdown
  - [x] For new entries: create/update parsed JSON
  - [x] For corrections: append correction note to raw markdown
  - [x] For corrections: update parsed JSON with correction delta

- [x] Task 8: Implement global context methods (AC: #7, #8)
  - [x] Implement `get_global_context()` - read or return empty string
  - [x] Implement `update_global_context()` - overwrite content

- [x] Task 9: Add comprehensive tests (AC: all)
  - [x] Test initialization with new and existing paths
  - [x] Test date range retrieval with edge cases
  - [x] Test pattern matching with various globs
  - [x] Test keyword search with AND/OR logic
  - [x] Test save_entry for new entries
  - [x] Test save_entry for corrections
  - [x] Test global context read/write
  - [x] Use tmp_path fixture for isolated testing

- [x] Task 10: Export from quilto package (AC: all)
  - [x] Add StorageRepository to `quilto/__init__.py`
  - [x] Add Entry, DateRange models to exports
  - [x] Verify `__all__` is complete

## Dev Notes

### Project Structure

**Location:** `packages/quilto/quilto/storage/`

```
packages/quilto/quilto/storage/
├── __init__.py       # Exports: StorageRepository, Entry, DateRange
├── repository.py     # StorageRepository class
└── models.py         # Entry, DateRange, ParserOutput stub
```

**Test Location:** `packages/quilto/tests/test_storage.py`

### Model Definitions

**Entry Model:**
```python
class Entry(BaseModel):
    """A single log entry with raw and parsed content."""
    model_config = ConfigDict(strict=True)

    id: str  # Format: {YYYY-MM-DD}_{HH-MM-SS} or {YYYY-MM-DD}_{index}
    date: date
    timestamp: datetime
    raw_content: str
    parsed_data: dict[str, Any] | None = None  # Domain-specific parsed data
```

**DateRange Model:**
```python
class DateRange(BaseModel):
    """Date range for filtering queries."""
    model_config = ConfigDict(strict=True)

    start: date
    end: date

    @model_validator(mode="after")
    def validate_range(self) -> "DateRange":
        if self.start > self.end:
            raise ValueError("start must be <= end")
        return self
```

**ParserOutput Stub (for correction support):**
```python
class ParserOutput(BaseModel):
    """Stub for Parser agent output - full definition in Epic 2 Story 3."""
    model_config = ConfigDict(strict=True)

    is_correction: bool = False
    target_entry_id: str | None = None
    correction_delta: dict[str, Any] | None = None
```

### Method Signatures (from agent-system-design.md Section 16.2)

```python
class StorageRepository:
    def __init__(self, base_path: Path): ...

    def get_entries_by_date_range(self, start: date, end: date) -> list[Entry]: ...
    def get_entries_by_pattern(self, pattern: str) -> list[Entry]: ...
    def search_entries(
        self,
        keywords: list[str],
        date_range: DateRange | None = None,
        match_all: bool = False
    ) -> list[Entry]: ...

    def save_entry(self, entry: Entry, correction: ParserOutput | None = None) -> None: ...

    def get_global_context(self) -> str: ...
    def update_global_context(self, content: str) -> None: ...
```

### Directory Structure

```
{base_path}/logs/
├── raw/{YYYY}/{MM}/{YYYY-MM-DD}.md      # Human + agent readable
├── parsed/{YYYY}/{MM}/{YYYY-MM-DD}.json  # App consumption
└── context/global.md                     # Observer's global context
```

### Raw Markdown Format

Daily files with `## HH:MM` section headers (server-generated timestamps):
```markdown
## 10:30
I benched 185 today and also squated 200 felt good

## 10:45
Had a protein shake after workout
```

- Multiple entries per day (append model)
- Mixed content types (domain logs + random notes)
- UTF-8 encoding required

### Correction Flow (Two Scenarios)

| Scenario | What Happened | Raw Action | Parsed Action |
|----------|---------------|------------|---------------|
| Parser Error | User wrote correctly, Parser extracted wrong | Keep raw as-is | Update parsed JSON |
| User Typo | User made typo in original | Append correction note | Update parsed JSON |

**Append Format (preserves history):**
```markdown
## 10:30
I benched 185 today and also squated 200 felt good

## 10:45 [correction]
Correction: bench weight recorded as 85 -> corrected to 185
```

**Parsed JSON Update:** Upsert semantics - update existing fields with `correction_delta`.

### search_entries Implementation Details

- **Search target:** Raw content (`raw_content` field)
- **Case-insensitive:** Convert both keywords and content to lowercase
- **match_all=True:** All keywords must be present (AND logic)
- **match_all=False:** Any keyword present (OR logic)
- **date_range filter:** If provided, first filter entries by date, then search

### Error Handling

| Error Case | Handling |
|------------|----------|
| Raw file missing | Skip entry, log warning |
| Parsed JSON missing | Return Entry with `parsed_data=None` |
| Parsed JSON corrupted | Return Entry with `parsed_data=None`, log error |
| Directory doesn't exist | Create it (init) or return empty list (read) |

### Pydantic Patterns (from Epic 1)

Use these established patterns:
- `model_config = ConfigDict(strict=True)` for all models
- `@field_validator` with Google-style docstrings
- `@model_validator(mode="after")` for cross-field validation
- Export all public classes in `__all__`

### Testing Requirements

- Use pytest with `tmp_path` fixture for isolated file operations
- Test edge cases: empty date ranges, no matches, corrupted JSON
- Update existing `storage_fixture` stub in `tests/conftest.py` to use real StorageRepository
- Test file location: `packages/quilto/tests/test_storage.py`

**Test Class Organization:**
```python
class TestStorageRepositoryInit:
    """Tests for StorageRepository initialization."""
    ...

class TestGetEntriesByDateRange:
    """Tests for date range retrieval."""
    ...

class TestSearchEntries:
    """Tests for keyword search."""
    ...

class TestSaveEntry:
    """Tests for saving entries."""
    ...

class TestCorrections:
    """Tests for correction flow."""
    ...

class TestGlobalContext:
    """Tests for global context operations."""
    ...
```

### Validation Commands

Run frequently during development:
```bash
# Quick validation
uv run ruff check . --fix && uv run pyright

# Full validation (before commits)
uv run ruff check . && uv run ruff format . && uv run pyright && uv run pytest
```

### Export Checklist

After implementation, verify exports:
```python
# packages/quilto/quilto/storage/__init__.py
__all__ = ["StorageRepository", "Entry", "DateRange", "ParserOutput"]

# packages/quilto/quilto/__init__.py - add to existing exports
from quilto.storage import StorageRepository, Entry, DateRange
```

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

None

### Completion Notes List

- Implemented full StorageRepository with 6 core methods as specified
- Entry, DateRange, and ParserOutput models defined with strict Pydantic validation
- All 34 comprehensive tests pass covering all acceptance criteria
- Full validation passes: ruff, pyright, pytest (326 total tests)
- Exported StorageRepository, Entry, DateRange, ParserOutput from quilto package

### File List

- `packages/quilto/quilto/storage/__init__.py` - Module exports
- `packages/quilto/quilto/storage/models.py` - Entry, DateRange, ParserOutput models
- `packages/quilto/quilto/storage/repository.py` - StorageRepository implementation
- `packages/quilto/quilto/__init__.py` - Updated with storage exports
- `packages/quilto/tests/test_storage.py` - Comprehensive test suite (40 tests)

## Senior Developer Review (AI)

**Date:** 2026-01-11
**Reviewer:** Claude Opus 4.5

### Review Outcome: APPROVED (with fixes applied)

### Issues Found & Fixed

| Severity | Issue | Fix Applied |
|----------|-------|-------------|
| HIGH | Unused `index` variable in `_parse_raw_file` (dead code) | Removed lines 114, 142 |
| HIGH | Empty keywords list in `search_entries` caused inconsistent behavior | Added `ValueError` for empty keywords |
| MEDIUM | No validation that `base_path` is a directory | Added `NotADirectoryError` check |
| MEDIUM | Missing tests for year/month boundary date ranges | Added `test_date_range_spanning_year_boundary`, `test_date_range_spanning_month_boundary` |
| MEDIUM | Missing test for empty section skipping | Added `test_empty_section_is_skipped` |
| MEDIUM | Missing test for pattern with correction entries | Added `test_pattern_with_correction_entries` |

### Test Coverage After Review

- **Before:** 34 tests
- **After:** 40 tests (+6 edge case tests)
- **All pass:** 332 passed, 3 skipped

### Validation Results

```
ruff check: All checks passed!
pyright: 0 errors, 0 warnings
pytest: 332 passed, 3 skipped
```

### Low-Priority Items (Not Fixed)

- L1: Docstring consistency (`Optional` vs `| None`) - minor style
- L2: `_get_raw_path` / `_get_parsed_path` duplication - acceptable, clear code
