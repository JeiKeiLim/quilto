# Story 15.2: Implement Session Management with SQLite Storage

Status: done

## Story

As a **Quilto framework developer**,
I want **session management with SQLite persistence**,
So that **multi-round conversations are tracked and can survive process restarts**.

## Background

**Origin:** Quilto Public API Design Session (2026-01-26)
**Source:** `_bmad-output/planning-artifacts/quilto-api-design-session.md`
**Priority:** High | **Effort:** Medium (3-4 hours)
**Type:** New code - session infrastructure
**Depends On:** Story 15.1 (provides ProcessResult, ClarificationQuestion models)

Sessions enable multi-round conversations:
- User asks -> Agent responds
- User follows up -> Agent has full context
- Clarification questions -> User answers -> Agent continues

Sessions are persisted to SQLite by default, with an abstraction layer for future database backends (PostgresSessionStore, InMemorySessionStore).

**Key Design Decision:** Sessions track full conversation history, not just clarification rounds. The first turn is always preserved for context, then oldest middle turns are pruned when limit is exceeded.

## Acceptance Criteria

1. **Given** a new conversation
   **When** `session_manager.create_session()` is called
   **Then** a new Session is created with unique UUID and persisted to SQLite

2. **Given** an existing session ID
   **When** `session_manager.get_session(id)` is called
   **Then** the session is loaded from SQLite with full conversation history

3. **Given** a session with 25 conversation turns (exceeds max_conversation_turns=20)
   **When** a new turn is added
   **Then** conversation is pruned to `[first_turn] + last (max_turns - 1)` = 20 total turns

4. **Given** a conversation turn from the agent
   **When** the turn includes clarification questions
   **Then** the questions (with options) are stored in turn metadata

5. **Given** multiple sessions exist
   **When** `session_manager.list_sessions()` is called
   **Then** all sessions are returned with basic info (id, created_at, updated_at)

6. **Given** a session is no longer needed
   **When** `session_manager.delete_session(id)` is called
   **Then** the session is removed from SQLite and `True` is returned

## Tasks / Subtasks

- [x] Task 1: Create session models in `packages/quilto/quilto/session/models.py` (AC: #1, #2, #4)
  - [x] 1.1: Create `ConversationTurn` model with `role: Literal["user", "agent"]`, `content: str = Field(min_length=1)`, `timestamp: datetime`, `metadata: dict[str, Any] | None`
  - [x] 1.2: Create `SessionData` model with `session_id: str = Field(min_length=1)`, `created_at: datetime`, `updated_at: datetime`, `conversation: list[ConversationTurn]`
  - [x] 1.3: Create `SessionConfig` model with `max_conversation_turns: int = Field(default=20, ge=2)`
  - [x] 1.4: Create `SessionInfo` model with `session_id: str`, `created_at: datetime`, `updated_at: datetime`, `turn_count: int` (for list_sessions response)
  - [x] 1.5: Add `ConfigDict(strict=True)` to all models

- [x] Task 2: Create SessionStore protocol in `packages/quilto/quilto/session/stores/base.py` (AC: #1, #2, #5, #6)
  - [x] 2.1: Define `SessionStore` Protocol with `@runtime_checkable` decorator (REQUIRED for isinstance() support)
  - [x] 2.2: Add `save(session_data: SessionData) -> None` method
  - [x] 2.3: Add `load(session_id: str) -> SessionData | None` method
  - [x] 2.4: Add `list_all() -> list[SessionInfo]` method
  - [x] 2.5: Add `delete(session_id: str) -> bool` method
  - [x] 2.6: Add comprehensive docstrings explaining expected behavior
  - [x] 2.7: Verify `isinstance(SQLiteSessionStore(...), SessionStore)` returns True

- [x] Task 3: Implement SQLiteSessionStore in `packages/quilto/quilto/session/stores/sqlite.py` (AC: #1, #2, #5, #6)
  - [x] 3.1: Create `__init__(self, db_path: str = "quilto_sessions.db")` with schema initialization
  - [x] 3.2: Implement `save()` using INSERT OR REPLACE (upsert) with JSON serialization
  - [x] 3.3: Implement `load()` with JSON deserialization to SessionData
  - [x] 3.4: Implement `list_all()` returning SessionInfo list (no conversation loading for efficiency)
  - [x] 3.5: Implement `delete()` returning True if deleted, False if not found
  - [x] 3.6: Use `datetime.fromisoformat()` and `datetime.isoformat()` for timestamp handling
  - [x] 3.7: Handle SQLite path creation (parent directory must exist)

- [x] Task 4: Create Session class in `packages/quilto/quilto/session/session.py` (AC: #3, #4)
  - [x] 4.1: `__init__(self, data: SessionData, store: SessionStore, config: SessionConfig)` - stores references
  - [x] 4.2: `add_turn(role: Literal["user", "agent"], content: str, metadata: dict[str, Any] | None = None) -> None` - creates turn, enforces limit, auto-saves
  - [x] 4.3: `get_history() -> list[ConversationTurn]` - returns conversation list
  - [x] 4.4: Property `session_id: str` - returns session ID
  - [x] 4.5: Implement turn pruning: `[first_turn] + conversation[-(max_turns - 1):]`
  - [x] 4.6: Auto-update `updated_at` on each `add_turn()` call

- [x] Task 5: Create SessionManager in `packages/quilto/quilto/session/manager.py` (AC: #1, #2, #5, #6)
  - [x] 5.1: `__init__(self, store: SessionStore, config: SessionConfig | None = None)` - defaults config if None
  - [x] 5.2: `create_session() -> Session` - generates UUID, creates SessionData, persists, returns Session
  - [x] 5.3: `get_session(session_id: str) -> Session | None` - loads from store, returns None if not found
  - [x] 5.4: `list_sessions() -> list[SessionInfo]` - delegates to store
  - [x] 5.5: `delete_session(session_id: str) -> bool` - delegates to store

- [x] Task 6: Create package exports in `packages/quilto/quilto/session/__init__.py`
  - [x] 6.1: Export models: `ConversationTurn`, `SessionData`, `SessionConfig`, `SessionInfo`
  - [x] 6.2: Export manager: `SessionManager`
  - [x] 6.3: Export session: `Session`
  - [x] 6.4: Add `__all__` list

- [x] Task 7: Create stores subpackage exports in `packages/quilto/quilto/session/stores/__init__.py`
  - [x] 7.1: Export `SessionStore` protocol
  - [x] 7.2: Export `SQLiteSessionStore`
  - [x] 7.3: Add `__all__` list

- [x] Task 8: Update `packages/quilto/quilto/__init__.py` (AC: all)
  - [x] 8.1: Import from session: `Session`, `SessionManager`, `SessionConfig`, `SessionInfo`, `SessionData`, `ConversationTurn`
  - [x] 8.2: Import from session.stores: `SessionStore`, `SQLiteSessionStore`
  - [x] 8.3: Add all new classes to `__all__` list
  - [x] 8.4: Verify import: `from quilto import Session, SessionManager, SessionConfig, SQLiteSessionStore`

- [x] Task 9: Write unit tests in `packages/quilto/tests/test_session.py` (AC: all)
  - [x] 9.1: Test `ConversationTurn` model validation (empty content rejected, valid metadata)
  - [x] 9.2: Test `SessionData` model validation (empty session_id rejected)
  - [x] 9.3: Test `SessionConfig` default value (20 turns)
  - [x] 9.4: Test `SessionConfig` rejects `max_conversation_turns < 2` (boundary validation)
  - [x] 9.5: Test `SQLiteSessionStore` CRUD with `:memory:` database
  - [x] 9.6: Test `Session.add_turn()` adds turn and auto-saves
  - [x] 9.7: Test `Session.add_turn()` rejects empty content string
  - [x] 9.8: Test turn pruning when exceeding max_conversation_turns
  - [x] 9.9: Test `SessionManager.create_session()` generates unique UUID
  - [x] 9.10: Test `SessionManager.get_session()` loads existing session
  - [x] 9.11: Test `SessionManager.get_session()` returns None for non-existent ID
  - [x] 9.12: Test `SessionManager.list_sessions()` returns all sessions
  - [x] 9.13: Test `SessionManager.delete_session()` removes session
  - [x] 9.14: Test metadata storage with clarification questions (dict[str, Any])
  - [x] 9.15: Test `SessionInfo.session_id` empty string rejected

- [x] Task 10: Run validation
  - [x] 10.1: `make check` passes (lint + typecheck)
  - [x] 10.2: `make validate` passes (lint + format + typecheck + test)

## Dev Notes

### Model Definitions from Design Session

From `_bmad-output/planning-artifacts/quilto-api-design-session.md`:

```python
# quilto/session/models.py

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class ConversationTurn(BaseModel):
    """A single turn in a conversation.

    Attributes:
        role: Who produced this turn ("user" or "agent").
        content: The text content of the turn.
        timestamp: When this turn was created.
        metadata: Optional additional data (e.g., clarification_questions, parsed_data).
    """

    model_config = ConfigDict(strict=True)

    role: Literal["user", "agent"]
    content: str = Field(min_length=1)
    timestamp: datetime
    metadata: dict[str, Any] | None = None


class SessionData(BaseModel):
    """Complete session data for persistence.

    Attributes:
        session_id: Unique identifier for the session.
        created_at: When the session was created.
        updated_at: When the session was last modified.
        conversation: List of conversation turns in order.
    """

    model_config = ConfigDict(strict=True)

    session_id: str = Field(min_length=1)  # Required non-empty
    created_at: datetime
    updated_at: datetime
    conversation: list[ConversationTurn] = Field(
        default_factory=list
    )  # Mutable default pattern


class SessionConfig(BaseModel):
    """Configuration for session behavior.

    Attributes:
        max_conversation_turns: Maximum turns to keep (default 20).
            When exceeded, keeps first turn + last (N-1) turns.
    """

    model_config = ConfigDict(strict=True)

    max_conversation_turns: int = Field(default=20, ge=2)


class SessionInfo(BaseModel):
    """Summary info for session listing (without full conversation).

    Attributes:
        session_id: Unique identifier for the session.
        created_at: When the session was created.
        updated_at: When the session was last modified.
        turn_count: Number of turns in the conversation.
    """

    model_config = ConfigDict(strict=True)

    session_id: str = Field(min_length=1)  # Required non-empty
    created_at: datetime
    updated_at: datetime
    turn_count: int = Field(default=0, ge=0)  # Default 0 for new sessions
```

### SessionStore Protocol

**IMPORTANT:** Protocol MUST have `@runtime_checkable` decorator to support `isinstance()` checks.

```python
# quilto/session/stores/base.py

from typing import Protocol, runtime_checkable

from quilto.session.models import SessionData, SessionInfo


@runtime_checkable  # REQUIRED for isinstance() support
class SessionStore(Protocol):
    """Protocol for session persistence backends.

    Implementations must provide save, load, list_all, and delete operations.
    The default implementation is SQLiteSessionStore.

    Example:
        store = SQLiteSessionStore("./sessions.db")
        store.save(session_data)
        loaded = store.load(session_id)
    """

    def save(self, session_data: SessionData) -> None:
        """Save or update a session.

        Args:
            session_data: The complete session data to persist.
        """
        ...

    def load(self, session_id: str) -> SessionData | None:
        """Load a session by ID.

        Args:
            session_id: The unique session identifier.

        Returns:
            SessionData if found, None if session doesn't exist.
        """
        ...

    def list_all(self) -> list[SessionInfo]:
        """List all sessions with summary info.

        Returns:
            List of SessionInfo (does not load full conversations).
        """
        ...

    def delete(self, session_id: str) -> bool:
        """Delete a session by ID.

        Args:
            session_id: The unique session identifier.

        Returns:
            True if session was deleted, False if not found.
        """
        ...
```

### SQLite Database Schema

```sql
CREATE TABLE IF NOT EXISTS sessions (
    session_id TEXT PRIMARY KEY,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    conversation TEXT NOT NULL  -- JSON array of ConversationTurn
);
```

**Important:** Store timestamps as ISO format strings (`datetime.isoformat()`) and parse with `datetime.fromisoformat()`.

### Turn Pruning Logic

When `len(conversation) > max_conversation_turns`:
```python
# Keep first turn (provides initial context) + last (max_turns - 1) turns
first_turn = conversation[0]
recent_turns = conversation[-(max_turns - 1):]
pruned_conversation = [first_turn] + recent_turns
```

**Rationale:** First turn contains the original question/context which is crucial for understanding follow-ups. Middle turns (often clarification Q&A) can be pruned.

### Package Structure

```
quilto/session/
├── __init__.py          # Export Session, SessionManager, models
├── manager.py           # SessionManager class
├── session.py           # Session class
├── models.py            # SessionData, ConversationTurn, SessionConfig, SessionInfo
└── stores/
    ├── __init__.py      # Export SessionStore, SQLiteSessionStore
    ├── base.py          # SessionStore Protocol
    └── sqlite.py        # SQLiteSessionStore implementation
```

### File Locations (Absolute from Project Root)

| File | Action | Purpose |
|------|--------|---------|
| `packages/quilto/quilto/session/__init__.py` | CREATE | Package exports |
| `packages/quilto/quilto/session/models.py` | CREATE | Pydantic models |
| `packages/quilto/quilto/session/session.py` | CREATE | Session class |
| `packages/quilto/quilto/session/manager.py` | CREATE | SessionManager class |
| `packages/quilto/quilto/session/stores/__init__.py` | CREATE | Stores subpackage exports |
| `packages/quilto/quilto/session/stores/base.py` | CREATE | SessionStore Protocol |
| `packages/quilto/quilto/session/stores/sqlite.py` | CREATE | SQLiteSessionStore |
| `packages/quilto/quilto/__init__.py` | UPDATE | Add session exports |
| `packages/quilto/tests/test_session.py` | CREATE | Unit tests |

### Existing Patterns to Follow

Based on Story 15.1 implementation:

1. **Model configuration**: All models use `ConfigDict(strict=True)`
2. **Field validation**: Use `Field(min_length=1)` for required strings, `Field(ge=0)` for non-negative ints
3. **Type hints**: Modern syntax `list[str] | None` not `Optional[List[str]]`
4. **Docstrings**: Google-style on all classes and public methods
5. **Protocols**: Use `@runtime_checkable` decorator for Protocol classes (enables `isinstance()` checks)
6. **Default lists**: Use `Field(default_factory=list)` not `[]` for mutable defaults

### Previous Story Context (Story 15.1)

Story 15.1 created:
- `quilto/models.py` - ProcessResult, ClarificationQuestion, ProcessDebug, AgentTrace
- `quilto/handlers.py` - ProgressHandler protocol with `@runtime_checkable`

Key learnings:
- H1 issue: Required fields without defaults cause instantiation failures - always add `default=0` or similar
- H2 issue: Protocol `isinstance()` behavior - need `@runtime_checkable` decorator
- M2 issue: Mutable default lists - use `Field(default_factory=list)` pattern

### Git Context (Recent Commits)

```
430fba9 Implement Story 15.1: Create Quilto Public API models
c4f2ae7 Update epics.md with Epic 15 and mark Epic 14 as skipped
539c88e Add Epic 15: Quilto Public API design and implementation stories
```

### Test Strategy

Unit tests with in-memory SQLite (`:memory:`) for fast testing. No LLM calls needed.

```python
# Example test setup
@pytest.fixture
def store() -> SQLiteSessionStore:
    """In-memory SQLite store for testing."""
    return SQLiteSessionStore(":memory:")

@pytest.fixture
def manager(store: SQLiteSessionStore) -> SessionManager:
    """Session manager with in-memory store."""
    return SessionManager(store=store)

@pytest.fixture
def config() -> SessionConfig:
    """Default session config for testing."""
    return SessionConfig()  # max_conversation_turns=20
```

**Key Test Cases (from Story 15.1 learnings):**
- Test default list isolation (two SessionData instances don't share lists)
- Test `isinstance(store, SessionStore)` returns True for SQLiteSessionStore
- Test boundary values: `max_conversation_turns=2` (minimum valid), `max_conversation_turns=1` (rejected)

### Common Mistakes to Avoid

| Mistake | Correct Pattern | Source |
|---------|-----------------|--------|
| Missing `@runtime_checkable` on Protocol | Add decorator for `isinstance()` support | Story 15.1, H2 |
| Mutable default list `[]` | Use `Field(default_factory=list)` | Story 15.1, M2 |
| Required field without default | Add appropriate default or make Optional | Story 15.1, H1 |
| Missing `min_length=1` on required strings | Always add for session_id, content, etc. | project-context.md |
| SQLite path not created | Parent directory must exist before opening | New pattern |
| Missing `ge=` constraint on int fields | Add `Field(default=0, ge=0)` for turn_count | Story 15.1 |
| Test only partial Protocol behavior | Verify `isinstance()` returns False for partial impl | Story 15.1, H2 |

### Architecture Alignment

This story implements the Session layer from architecture.md:

```
SessionManager
└── SessionStore (Protocol)
    ├── SQLiteSessionStore (default) <- This story
    ├── PostgresSessionStore (future)
    └── InMemorySessionStore (future/testing)
```

The `Session` class created here will be used by `Quilto.create_session()` in Story 15.3.

### Validation Checklist (Run Before Marking Done)

**Code Quality:**
- [ ] All models have `ConfigDict(strict=True)`
- [ ] All required string fields use `Field(min_length=1)`
- [ ] `SessionStore` Protocol has `@runtime_checkable` decorator
- [ ] No mutable default lists (use `Field(default_factory=list)`)
- [ ] Modern type hints: `list[str]` not `List[str]`, `X | None` not `Optional[X]`
- [ ] Google-style docstrings on all classes and public methods

**Exports:**
- [ ] All models exported from `quilto/session/__init__.py`
- [ ] `SessionStore`, `SQLiteSessionStore` exported from `quilto/session/stores/__init__.py`
- [ ] All session classes exported from `quilto/__init__.py`
- [ ] All exports added to `__all__` lists
- [ ] Import verification: `from quilto import Session, SessionManager, SessionConfig, SQLiteSessionStore`

**Tests:**
- [ ] `ConversationTurn` empty content rejected
- [ ] `SessionData` empty session_id rejected
- [ ] `SessionInfo` empty session_id rejected
- [ ] `SessionConfig` defaults to 20 turns
- [ ] `SessionConfig` rejects max_conversation_turns < 2
- [ ] `SQLiteSessionStore` save/load roundtrip works
- [ ] `SQLiteSessionStore` list_all returns correct SessionInfo
- [ ] `SQLiteSessionStore` delete returns True/False correctly
- [ ] `Session.add_turn()` creates turn and saves
- [ ] `Session.add_turn()` rejects empty content
- [ ] Turn pruning keeps first + last (N-1)
- [ ] `SessionManager.create_session()` generates UUID
- [ ] `SessionManager.get_session()` returns None for missing ID
- [ ] Metadata storage works (dict[str, Any])

**Final Validation:**
- [ ] `make check` passes (lint + typecheck)
- [ ] `make validate` passes (lint + format + typecheck + test)

### References

| Source | Content |
|--------|---------|
| `_bmad-output/planning-artifacts/quilto-api-design-session.md` | Full API design session with session architecture |
| `_bmad-output/planning-artifacts/architecture.md#Quilto Public API` | Architecture decision documentation |
| `_bmad-output/implementation-artifacts/epic-15/15-1-create-quilto-models.md` | Previous story patterns and learnings |
| `_bmad-output/project-context.md` | Validation rules and common mistakes to avoid |

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

N/A

### Completion Notes List

- All session models implemented with strict Pydantic validation
- SessionStore protocol with @runtime_checkable for isinstance() support
- SQLiteSessionStore handles in-memory databases correctly by maintaining persistent connection
- Turn pruning preserves first turn + last (max_turns - 1) turns
- All 39 test cases pass (37 new session tests + 2 integration tests)
- Full validation passed: `make check` and `make validate`

### Code Review (2026-01-27)

**Reviewed by:** Claude Opus 4.5 (Adversarial Code Review)

**Issues Found:** 1 High, 3 Medium, 2 Low

**Fixes Applied:**
1. **H1 (HIGH):** `Session.get_history()` now returns a copy of the list to prevent external mutation that bypasses turn management
2. **M1 (MEDIUM):** Fixed `SessionData.conversation` default_factory to use standard pattern `lambda: []` instead of unusual `list[ConversationTurn]()`
3. **M2 (MEDIUM):** Updated `list_all()` docstring to accurately reflect that it parses conversation JSON (not truly efficient for large conversations)
4. **M3 (MEDIUM):** Added test `test_complex_nested_metadata_survives_workflow` to verify nested metadata survives full Session workflow
5. **Added test:** `test_get_history_returns_copy` to verify the H1 fix

**Final Status:** All 41 tests pass (39 original + 2 new). `make validate` passes.

### File List

| File | Action |
|------|--------|
| `packages/quilto/quilto/session/__init__.py` | CREATE |
| `packages/quilto/quilto/session/models.py` | CREATE |
| `packages/quilto/quilto/session/session.py` | CREATE |
| `packages/quilto/quilto/session/manager.py` | CREATE |
| `packages/quilto/quilto/session/stores/__init__.py` | CREATE |
| `packages/quilto/quilto/session/stores/base.py` | CREATE |
| `packages/quilto/quilto/session/stores/sqlite.py` | CREATE |
| `packages/quilto/quilto/__init__.py` | UPDATE |
| `packages/quilto/tests/test_session.py` | CREATE |
