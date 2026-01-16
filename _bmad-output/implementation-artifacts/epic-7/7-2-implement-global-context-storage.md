# Story 7.2: Implement Global Context Storage

Status: done

## Story

As a **Quilto developer**,
I want **global context stored as markdown with size management**,
so that **personalization persists across sessions**.

## Background

This is the second story in Epic 7 (Learning & Personalization) and implements the global context storage layer that Observer uses to persist learned patterns. Story 7.1 implemented the Observer agent which generates `ContextUpdate` objects - this story provides the infrastructure to:

1. **Persist updates** to the global context markdown file
2. **Manage size** to stay within ~2k tokens (configurable)
3. **Archive old insights** when the active context grows too large
4. **Format context** consistently using the defined markdown structure

**Key Characteristics:**
- **Markdown with YAML frontmatter:** Human-readable, git-friendly format
- **Organized sections:** Preferences, Patterns, Facts, Insights (grouped by confidence)
- **Size management:** ~2k tokens target with archival strategy
- **Incremental updates:** Apply `ContextUpdate` objects without rewriting entire context

**Architecture Context:**
- Uses `StorageRepository.get_global_context()` and `update_global_context()` (already implemented in Story 2.1)
- File location: `logs/context/global.md` (relative to storage base_path)
- Archive location: `logs/context/archive/global-{date}.md`
- Observer produces updates; this module applies them to the file

## Acceptance Criteria

1. **Given** global context file (`logs/context/global.md`)
   **When** Observer updates it
   **Then** format is markdown with YAML frontmatter
   **And** size stays within ~2k tokens (configurable)
   **And** archival strategy moves old insights to archive file

2. **Given** the GlobalContextManager class
   **When** instantiated
   **Then** it accepts a StorageRepository instance
   **And** provides methods for reading, updating, and archiving context

3. **Given** the GlobalContext model
   **When** parsed from markdown
   **Then** it validates frontmatter fields:
   - `last_updated`: str (ISO date)
   - `version`: int (increments on each update)
   - `token_estimate`: int (current token count estimate)
   **And** parses sections into structured data

4. **Given** the ContextSection model
   **When** instantiated
   **Then** it groups items by category:
   - `preferences`: list of key-value pairs with confidence "certain"
   - `patterns`: list of key-value pairs with confidence "likely"
   - `facts`: list of key-value pairs with confidence "certain"
   - `insights`: list of key-value pairs with confidence "tentative"

5. **Given** GlobalContextManager.apply_updates(updates)
   **When** called with a list of ContextUpdate objects
   **Then** it applies each update to the appropriate section
   **And** supersedes existing entries with the same key
   **And** increments the version number
   **And** updates the last_updated timestamp

6. **Given** a context update that would exceed the token limit
   **When** apply_updates is called
   **Then** it triggers archival of oldest insights
   **And** moves archived items to `logs/context/archive/global-{date}.md`
   **And** keeps active context under the limit

7. **Given** GlobalContextManager.read_context()
   **When** the global context file exists
   **Then** it returns a GlobalContext object
   **And** parses markdown into structured sections

8. **Given** GlobalContextManager.read_context()
   **When** the global context file does not exist
   **Then** it returns an empty GlobalContext with defaults

9. **Given** GlobalContextManager.write_context(context)
   **When** called with a GlobalContext object
   **Then** it serializes to markdown with YAML frontmatter
   **And** organizes sections by category and confidence
   **And** writes to the storage repository

10. **Given** the configurable token limit (default ~2000)
    **When** estimating token count
    **Then** use simple word-based estimation (words * 1.3)
    **And** allow limit to be configured via constructor

## Tasks / Subtasks

- [x] Task 1: Create GlobalContext and ContextEntry models (AC: #3, #4)
  - [x] 1.1: Create `packages/quilto/quilto/storage/context.py` module
  - [x] 1.2: Define `ContextEntry` model with:
    - `key: str = Field(min_length=1)`
    - `value: str = Field(min_length=1)`
    - `confidence: Literal["certain", "likely", "tentative"]`
    - `source: str = Field(min_length=1)`
    - `category: Literal["preference", "pattern", "fact", "insight"]`
    - `added_date: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}$")` (ISO date when first added)
  - [x] 1.3: Define `GlobalContextFrontmatter` model with:
    - `last_updated: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}$")`
    - `version: int = Field(ge=1)`
    - `token_estimate: int = Field(ge=0)`
  - [x] 1.4: Add `@field_validator` for `last_updated` and `added_date` to validate actual date validity (not just format):
    ```python
    @field_validator("last_updated", "added_date", mode="after")
    @classmethod
    def validate_date_string(cls, v: str) -> str:
        date.fromisoformat(v)  # Raises ValueError if invalid date
        return v
    ```
  - [x] 1.5: Define `GlobalContext` model with:
    - `frontmatter: GlobalContextFrontmatter`
    - `preferences: list[ContextEntry] = Field(default_factory=list)`
    - `patterns: list[ContextEntry] = Field(default_factory=list)`
    - `facts: list[ContextEntry] = Field(default_factory=list)`
    - `insights: list[ContextEntry] = Field(default_factory=list)`
  - [x] 1.6: Use `ConfigDict(strict=True)` for all models
  - [x] 1.7: Add comprehensive docstrings following project conventions

- [x] Task 2: Create GlobalContextManager class (AC: #2)
  - [x] 2.1: Define `GlobalContextManager` class in `packages/quilto/quilto/storage/context.py`
  - [x] 2.2: Implement `__init__(self, storage: StorageRepository, token_limit: int = 2000)`
  - [x] 2.3: Store token_limit as instance variable for size management

- [x] Task 3: Implement read_context method (AC: #7, #8)
  - [x] 3.1: Create `def read_context(self) -> GlobalContext`
  - [x] 3.2: Call `self.storage.get_global_context()` to get raw markdown
  - [x] 3.3: Parse YAML frontmatter from `---` delimiters
  - [x] 3.4: Parse markdown sections (## Preferences, ## Patterns, ## Facts, ## Insights)
  - [x] 3.5: Extract key-value pairs from bullet points (`- key: value`)
  - [x] 3.6: Return empty GlobalContext with default frontmatter if file empty/missing:
    - `last_updated`: today's date (ISO format)
    - `version`: 1
    - `token_estimate`: 0
  - [x] 3.7: Create `_create_default_context()` helper method for empty/new context

- [x] Task 4: Implement write_context method (AC: #9)
  - [x] 4.1: Create `def write_context(self, context: GlobalContext) -> None`
  - [x] 4.2: Serialize frontmatter to YAML between `---` delimiters
  - [x] 4.3: Serialize each section with `## {Section}` header
  - [x] 4.4: Format entries as `- {key}: {value}` bullet points
  - [x] 4.5: Call `self.storage.update_global_context(markdown)` to persist

- [x] Task 5: Implement apply_updates method (AC: #5)
  - [x] 5.1: Create `def apply_updates(self, updates: list[ContextUpdate]) -> GlobalContext`
  - [x] 5.2: Read current context via `read_context()`
  - [x] 5.3: For each update, find the matching section by category:
    - "preference" → preferences list
    - "pattern" → patterns list
    - "fact" → facts list
    - "insight" → insights list
  - [x] 5.4: Convert `ContextUpdate` to `ContextEntry` (add `added_date` as today's date for new entries)
  - [x] 5.5: Supersede existing entry if key matches (update in place, preserve original `added_date`)
  - [x] 5.6: Add new entry if key not found
  - [x] 5.7: Increment version number and update last_updated
  - [x] 5.8: Update token_estimate via `estimate_tokens()` - **BEFORE archival check**
  - [x] 5.9: Call `_archive_if_needed()` to manage size - **AFTER token estimation**
  - [x] 5.10: Write updated context via `write_context()`
  - [x] 5.11: Return the updated GlobalContext

- [x] Task 6: Implement token estimation (AC: #10)
  - [x] 6.1: Create `def estimate_tokens(self, context: GlobalContext) -> int`
  - [x] 6.2: Serialize context to markdown string
  - [x] 6.3: Count words and multiply by 1.3 (approximate tokens)
  - [x] 6.4: Return integer token estimate

- [x] Task 7: Implement archival strategy (AC: #6)
  - [x] 7.1: Create `def _archive_if_needed(self, context: GlobalContext) -> GlobalContext`
  - [x] 7.2: Check if token_estimate exceeds token_limit
  - [x] 7.3: If over limit, identify oldest insights (by `added_date`)
  - [x] 7.4: Move oldest insights to archive file
  - [x] 7.5: Archive file path: `logs/context/archive/global-{archival_date}.md`
    - `{archival_date}` is the date when archival occurs (today), NOT the entry's added_date
    - Example: `global-2026-01-16.md` for archival on Jan 16, 2026
  - [x] 7.6: Create archive directory via `self.storage.base_path / "logs" / "context" / "archive"`
  - [x] 7.7: Append to existing archive file if same-day archival, else create new
  - [x] 7.8: Remove archived items from active context
  - [x] 7.9: Recalculate token_estimate after removal
  - [x] 7.10: Repeat until under limit or no more archivable items (insights first, then patterns)
  - [x] 7.11: Return modified context (archival already applied in-place)

- [x] Task 8: Update package exports
  - [x] 8.1: Add imports to `packages/quilto/quilto/storage/__init__.py`:
    - `from quilto.storage.context import ContextEntry, GlobalContext, GlobalContextFrontmatter, GlobalContextManager`
  - [x] 8.2: Add to `__all__` list (alphabetical)
  - [x] 8.3: Update module docstring to include context management

- [x] Task 9: Create unit tests
  - [x] 9.1: Create `packages/quilto/tests/test_context.py`
  - [x] 9.2: Test ContextEntry validation:
    - All Literal values for confidence ("certain", "likely", "tentative")
    - All Literal values for category ("preference", "pattern", "fact", "insight")
    - Empty key/value/source fail validation
    - Valid ISO date for added_date passes
    - Invalid added_date fails (e.g., "2026-99-99" - format valid but date invalid)
  - [x] 9.3: Test GlobalContextFrontmatter validation:
    - Valid ISO date format passes
    - Invalid date format fails (e.g., "not-a-date")
    - Format-valid but semantically invalid date fails (e.g., "2026-13-45")
    - Version must be >= 1 (test 0 fails, 1 passes)
    - token_estimate must be >= 0 (test -1 fails, 0 passes)
  - [x] 9.4: Test GlobalContext parsing:
    - Parse valid markdown with all sections
    - Parse markdown with missing sections (empty lists for missing)
    - Parse empty file returns default context with today's date
  - [x] 9.5: Test write_context serialization:
    - Output matches expected markdown format
    - YAML frontmatter is valid and parseable
    - Sections are ordered: Preferences, Patterns, Facts, Insights
    - Round-trip: write → read returns equivalent context
  - [x] 9.6: Test apply_updates:
    - New entries are added with today's added_date
    - Existing entries are superseded (key match, preserve added_date)
    - Version increments by 1
    - last_updated is set to today
    - token_estimate is recalculated
    - Multiple updates in single call work correctly
  - [x] 9.7: Test token estimation:
    - Empty context returns small token count (frontmatter only)
    - Reasonable approximation: ~1.3x word count
    - Test boundary: 2000 tokens threshold
  - [x] 9.8: Test archival:
    - Triggers when token_estimate > token_limit
    - Oldest insights (by added_date) archived first
    - Then oldest patterns if still over limit
    - Preferences and facts NEVER archived
    - Archive file created at `logs/context/archive/global-{today}.md`
    - Active context reduced after archival
    - Multiple archival operations on same day append to same file
  - [x] 9.9: Test read_context with non-existent file returns default context
  - [x] 9.10: Test _create_default_context helper returns valid defaults

- [x] Task 10: Run validation
  - [x] 10.1: Run `make check` (lint + typecheck)
  - [x] 10.2: Run `make test` (unit tests)
  - [x] 10.3: Run `make test-ollama` (integration tests with real Ollama)

## Dev Notes

### Global Context Format

The global context file uses markdown with YAML frontmatter, organized by section:

```markdown
---
last_updated: 2026-01-16
version: 15
token_estimate: 450
---

# Global Context

## Preferences (certain)
- unit_preference: metric
- response_style: concise
- language: English

## Patterns (likely)
- typical_active_days: [Monday, Wednesday, Friday]
- usual_time_of_day: morning
- preferred_exercises: compound movements

## Facts (certain)
- records: {bench_press: 185x5, squat: 225x5, deadlift: 315x3}
- current_routine: push-pull-legs
- training_start_date: 2024-03-15

## Insights (tentative)
- Performance tends to drop when sleep is below 7 hours
- Best workouts on Wednesday evenings
- Recovery seems faster with protein intake > 150g
```

### Section Mapping

| Category | Section | Confidence | Archival Priority |
|----------|---------|------------|-------------------|
| preference | Preferences | certain | Never (user explicit) |
| pattern | Patterns | likely | Low (behavioral) |
| fact | Facts | certain | Never (objective) |
| insight | Insights | tentative | High (speculative) |

### Archival Strategy

When context exceeds token limit:
1. Archive `tentative` insights first (most speculative)
2. Then archive older `likely` patterns (if still over)
3. Never archive `certain` preferences or facts

Archive file format:
```markdown
---
archived_from: global.md
archived_date: 2026-01-16
reason: size_management
---

# Archived Context (2026-01-16)

## Archived Insights
- [2025-12-01] old_insight_1: value
- [2025-11-15] old_insight_2: value
```

### Token Estimation

Simple word-based estimation:
```python
def estimate_tokens(content: str) -> int:
    """Estimate token count from text.

    Uses word count * 1.3 as approximation.
    This is intentionally simple - not accurate but good enough
    for size management purposes.
    """
    words = len(content.split())
    return int(words * 1.3)
```

### Storage Integration

Uses existing `StorageRepository` methods:
- `get_global_context()` - Returns content of `logs/context/global.md`
- `update_global_context(content)` - Writes to `logs/context/global.md`

For archive files, use direct file operations since archive is a new location:
```python
archive_path = self.storage.base_path / "logs" / "context" / "archive" / f"global-{date}.md"
archive_path.parent.mkdir(parents=True, exist_ok=True)
```

### Key Design Decisions

**Why Markdown?**
- Human-readable (users can inspect and edit)
- Git-friendly (diffs are meaningful)
- Matches raw log format convention
- Easy for LLMs to read and understand

**Why ~2k Token Limit?**
- NFR-F9: Global context ~2k tokens with archival strategy
- Balances personalization depth with prompt length
- Keeps context injection cost reasonable

**Why Simple Token Estimation?**
- Actual tokenization varies by model
- Simplicity over precision for this use case
- Avoid heavy dependencies (tiktoken, etc.)
- Conservative estimate prevents overflow

### Common Mistakes to Avoid

| Mistake | Correct Pattern | Source |
|---------|-----------------|--------|
| Missing `Field(min_length=1)` on required strings | Always use `Field(min_length=1)` | project-context.md |
| Creating archive in wrong location | Use `logs/context/archive/` path | Story 7.2 spec |
| Overwriting archive file | Append to existing archive on same day | Preserve history |
| Archiving preferences/facts | Only archive tentative/likely items | Design decision |
| Not incrementing version | Always increment on any update | AC #5 |
| Forgetting to update token_estimate | Recalculate after every update | AC #5 |
| Using only regex pattern for dates | Add `@field_validator` to catch "2026-99-99" | Validation rigor |
| Confusing ContextUpdate vs ContextEntry | ContextUpdate has no added_date; ContextEntry does | Model design |
| Archiving before token estimation | Estimate tokens FIRST, then check archival | Task order |
| Archive date = entry added_date | Archive date = archival operation date (today) | Naming convention |

### Project Structure Notes

- GlobalContextManager lives in Quilto (domain-agnostic framework)
- Uses StorageRepository (already implemented in Story 2.1)
- Context format is framework-defined, content is application-specific
- Story 7.4 will add fitness-specific context guidance in Swealog

### File Structure

```
packages/quilto/quilto/storage/
├── __init__.py          # Add context exports
├── repository.py        # Existing - has get/update_global_context
└── context.py           # NEW: GlobalContextManager + models

packages/quilto/tests/
├── __init__.py
├── conftest.py
├── test_storage.py      # Existing StorageRepository tests
└── test_context.py      # NEW: GlobalContextManager tests
```

### ContextUpdate vs ContextEntry Distinction

**ContextUpdate** (from Story 7.1, in `quilto.agents.models`):
- Represents an UPDATE REQUEST from Observer agent
- Does NOT have `added_date` - that's storage metadata
- Used as input to `apply_updates()`

**ContextEntry** (NEW in this story, in `quilto.storage.context`):
- Represents a PERSISTED entry in global context file
- HAS `added_date` - tracks when entry was first added
- Used for storage, archival, and size management

The `apply_updates()` method converts `ContextUpdate` → `ContextEntry` by adding `added_date`.

### Model Implementation Reference

```python
"""Global context storage and management.

This module provides classes for persisting and managing
the global user context that Observer generates.
"""

from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from quilto.agents.models import ContextUpdate
from quilto.storage import StorageRepository


class ContextEntry(BaseModel):
    """A single entry in the global context.

    Note: This is DISTINCT from ContextUpdate (agents.models).
    ContextUpdate is the INPUT from Observer.
    ContextEntry is the PERSISTED form with added_date metadata.

    Attributes:
        key: Unique identifier for this entry.
        value: The value to store.
        confidence: Confidence level (certain, likely, tentative).
        source: What triggered this entry.
        category: Entry category.
        added_date: ISO date when first added.

    Example:
        >>> entry = ContextEntry(
        ...     key="unit_preference",
        ...     value="metric",
        ...     confidence="certain",
        ...     source="user_correction: changed lbs to kg",
        ...     category="preference",
        ...     added_date="2026-01-16"
        ... )
    """

    model_config = ConfigDict(strict=True)

    key: str = Field(min_length=1)
    value: str = Field(min_length=1)
    confidence: Literal["certain", "likely", "tentative"]
    source: str = Field(min_length=1)
    category: Literal["preference", "pattern", "fact", "insight"]
    added_date: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}$")

    @field_validator("added_date", mode="after")
    @classmethod
    def validate_added_date(cls, v: str) -> str:
        """Validate added_date is a real date, not just format-valid."""
        date.fromisoformat(v)  # Raises ValueError if invalid
        return v


class GlobalContextFrontmatter(BaseModel):
    """YAML frontmatter for global context file.

    Attributes:
        last_updated: ISO date of last update.
        version: Incremental version number.
        token_estimate: Estimated token count.

    Example:
        >>> fm = GlobalContextFrontmatter(
        ...     last_updated="2026-01-16",
        ...     version=15,
        ...     token_estimate=450
        ... )
    """

    model_config = ConfigDict(strict=True)

    last_updated: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}$")
    version: int = Field(ge=1)
    token_estimate: int = Field(ge=0)

    @field_validator("last_updated", mode="after")
    @classmethod
    def validate_last_updated(cls, v: str) -> str:
        """Validate last_updated is a real date, not just format-valid."""
        date.fromisoformat(v)  # Raises ValueError if invalid
        return v


class GlobalContext(BaseModel):
    """Complete global context with all sections.

    Attributes:
        frontmatter: YAML frontmatter metadata.
        preferences: User preferences (certain confidence).
        patterns: Behavioral patterns (likely confidence).
        facts: Objective facts (certain confidence).
        insights: Observations (tentative confidence).

    Example:
        >>> ctx = GlobalContext(
        ...     frontmatter=GlobalContextFrontmatter(...),
        ...     preferences=[entry1],
        ...     facts=[entry2]
        ... )
    """

    model_config = ConfigDict(strict=True)

    frontmatter: GlobalContextFrontmatter
    preferences: list[ContextEntry] = Field(default_factory=list)  # pyright: ignore[reportUnknownVariableType]
    patterns: list[ContextEntry] = Field(default_factory=list)  # pyright: ignore[reportUnknownVariableType]
    facts: list[ContextEntry] = Field(default_factory=list)  # pyright: ignore[reportUnknownVariableType]
    insights: list[ContextEntry] = Field(default_factory=list)  # pyright: ignore[reportUnknownVariableType]


class GlobalContextManager:
    """Manager for global context persistence and size management.

    Handles reading, writing, updating, and archiving the global
    context markdown file. Integrates with StorageRepository.

    Attributes:
        storage: StorageRepository instance for file operations.
        token_limit: Maximum tokens before archival (default 2000).

    Example:
        >>> from quilto.storage import StorageRepository
        >>> storage = StorageRepository(Path("/data"))
        >>> manager = GlobalContextManager(storage, token_limit=2000)
        >>> context = manager.read_context()
        >>> updated = manager.apply_updates(observer_output.updates)
    """

    def __init__(self, storage: StorageRepository, token_limit: int = 2000) -> None:
        """Initialize the GlobalContextManager.

        Args:
            storage: StorageRepository for file operations.
            token_limit: Maximum estimated tokens before archival.
        """
        self.storage = storage
        self.token_limit = token_limit

    # ... implementation follows
```

### References

- [Source: _bmad-output/planning-artifacts/epics.md:1022-1035] Story 7.2 acceptance criteria
- [Source: _bmad-output/planning-artifacts/agent-system-design.md:2040-2065] Global context structure
- [Source: _bmad-output/planning-artifacts/agent-system-design.md:990-998] Context size management
- [Source: _bmad-output/planning-artifacts/architecture.md:73-77] NFR-F9 reference
- [Source: packages/quilto/quilto/storage/repository.py:365-384] get_global_context/update_global_context methods
- [Source: packages/quilto/quilto/agents/models.py:902-950] ContextUpdate model from Story 7.1
- [Source: packages/quilto/quilto/agents/observer.py] Observer agent implementation
- [Source: _bmad-output/implementation-artifacts/epic-7/7-1-implement-observer-agent.md] Previous story for context

### Story Dependencies

| Story | Dependency Type | Notes |
|-------|-----------------|-------|
| 2-1 (done) | Upstream | StorageRepository with get_global_context/update_global_context |
| 7-1 (done) | Upstream | Observer agent produces ContextUpdate objects |
| 7-3 (backlog) | Downstream | Observer triggers will use GlobalContextManager |
| 7-4 (backlog) | Downstream | Fitness context management uses this infrastructure |

## Dev Agent Record

### Agent Model Used

claude-opus-4-5-20251101

### Debug Log References

None

### Completion Notes List

- All 10 tasks completed successfully
- Created `ContextEntry`, `GlobalContextFrontmatter`, `GlobalContext` models with strict validation
- Implemented `GlobalContextManager` with read/write/apply_updates/archival methods
- Token estimation uses simple word * 1.3 approximation
- Archival strategy: insights first, then patterns, never preferences/facts
- Added date prefix to markdown format (`- [YYYY-MM-DD] key: value`) to preserve added_date on round-trip
- 51 unit tests pass in `test_context.py`
- All 1464 unit tests pass
- All 1494 integration tests pass with Ollama
- Lint and typecheck pass for new files

### Senior Developer Review (AI)

**Reviewed by:** claude-opus-4-5-20251101
**Date:** 2026-01-16

**Issues Found and Fixed:**
1. **M1/M2: Round-trip data loss** - Source and confidence fields were not persisted to markdown. Fixed by changing format to `- [date|confidence|source] key: value` with backward-compatible legacy format support.
2. **M3: Import inside function** - Moved `import re` from inside `_parse_section` to module level.
3. **L1: Duplicate sort key** - Extracted inline sort key functions to single `_entry_date_key` helper.
4. Added new test `test_round_trip_preserves_source_and_confidence` to verify fix.

**Tests After Review:** 52 passed (1 new test added)

### File List

- `packages/quilto/quilto/storage/context.py` (NEW) - GlobalContextManager and models
- `packages/quilto/quilto/storage/__init__.py` (MODIFIED) - Added exports
- `packages/quilto/tests/test_context.py` (NEW) - 52 unit tests
