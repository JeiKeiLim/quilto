# Story 15.2: Implement Session Management with SQLite Storage

Status: backlog

## Story

As a **Quilto framework developer**,
I want **session management with SQLite persistence**,
So that **multi-round conversations are tracked and can survive process restarts**.

## Background

**Origin:** Quilto Public API Design Session (2026-01-27)
**Source:** `_bmad-output/planning-artifacts/quilto-api-design-session.md`
**Priority:** High | **Effort:** Medium (3-4 hours)
**Type:** New code - session infrastructure

Sessions enable multi-round conversations:
- User asks → Agent responds
- User follows up → Agent has full context
- Clarification questions → User answers → Agent continues

Sessions are persisted to SQLite by default, with an abstraction layer for future database backends.

## Acceptance Criteria

1. **Given** a new conversation
   **When** `q.create_session()` is called
   **Then** a new Session is created with unique ID and persisted to SQLite

2. **Given** an existing session ID
   **When** `session_manager.get_session(id)` is called
   **Then** the session is loaded from SQLite with full conversation history

3. **Given** a session with 25 conversation turns
   **When** a new turn is added
   **Then** oldest turns are pruned to keep first + last 19 (20 total)

4. **Given** a conversation turn from the agent
   **When** the turn includes clarification questions
   **Then** the questions (with options) are stored in turn metadata

5. **Given** multiple sessions exist
   **When** `session_manager.list_sessions()` is called
   **Then** all sessions are returned with basic info (id, created_at, updated_at)

## Tasks / Subtasks

- [ ] Task 1: Create session models in `quilto/session/models.py`
  - [ ] 1.1: Create `ConversationTurn` model (role, content, timestamp, metadata)
  - [ ] 1.2: Create `SessionData` model (session_id, created_at, updated_at, conversation)
  - [ ] 1.3: Create `SessionConfig` model (max_conversation_turns=20)
  - [ ] 1.4: Create `SessionInfo` model (for list_sessions response)

- [ ] Task 2: Create SessionStore protocol in `quilto/session/stores/base.py`
  - [ ] 2.1: Define `SessionStore` Protocol with save, load, list_all, delete methods
  - [ ] 2.2: Document expected behavior for each method

- [ ] Task 3: Implement SQLiteSessionStore in `quilto/session/stores/sqlite.py`
  - [ ] 3.1: Create database schema (sessions table with JSON conversation column)
  - [ ] 3.2: Implement `save()` - upsert session data
  - [ ] 3.3: Implement `load()` - retrieve by session_id
  - [ ] 3.4: Implement `list_all()` - return all sessions
  - [ ] 3.5: Implement `delete()` - remove session by ID

- [ ] Task 4: Create Session class in `quilto/session/session.py`
  - [ ] 4.1: `__init__` with session_id, store reference, config
  - [ ] 4.2: `add_turn()` method - adds turn, enforces max_conversation_turns limit
  - [ ] 4.3: `get_history()` method - returns conversation list
  - [ ] 4.4: Implement turn pruning (keep first + last N-1)

- [ ] Task 5: Create SessionManager in `quilto/session/manager.py`
  - [ ] 5.1: `__init__` with SessionStore and SessionConfig
  - [ ] 5.2: `create_session()` - creates new Session with UUID
  - [ ] 5.3: `get_session()` - loads existing session
  - [ ] 5.4: `list_sessions()` - returns all SessionInfo
  - [ ] 5.5: `delete_session()` - removes session

- [ ] Task 6: Write unit tests
  - [ ] 6.1: Test ConversationTurn and SessionData models
  - [ ] 6.2: Test SQLiteSessionStore CRUD operations
  - [ ] 6.3: Test Session turn pruning logic
  - [ ] 6.4: Test SessionManager create/get/list/delete

- [ ] Task 7: Export from `quilto/__init__.py`
  - [ ] 7.1: Export Session, SessionManager, SessionConfig, SessionStore, SQLiteSessionStore

- [ ] Task 8: Run validation
  - [ ] 8.1: Run `make check` (lint + typecheck)
  - [ ] 8.2: Run `make validate` (full validation)

## Dev Notes

### Database Schema

```sql
CREATE TABLE IF NOT EXISTS sessions (
    session_id TEXT PRIMARY KEY,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    conversation TEXT NOT NULL  -- JSON array of ConversationTurn
);
```

### Turn Pruning Logic

When `len(conversation) > max_conversation_turns`:
```python
first_turn = conversation[0]
recent_turns = conversation[-(max_turns - 1):]
conversation = [first_turn] + recent_turns
```

### Package Structure

```
quilto/session/
├── __init__.py          # Export Session, SessionManager, etc.
├── manager.py           # SessionManager class
├── session.py           # Session class
├── models.py            # SessionData, ConversationTurn, SessionConfig, SessionInfo
└── stores/
    ├── __init__.py      # Export SessionStore, SQLiteSessionStore
    ├── base.py          # SessionStore Protocol
    └── sqlite.py        # SQLiteSessionStore implementation
```

### File Locations

| File | Purpose |
|------|---------|
| `packages/quilto/quilto/session/` | NEW - entire session package |
| `packages/quilto/quilto/__init__.py` | UPDATE - add session exports |
| `packages/quilto/tests/test_session.py` | NEW - unit tests |

## Test Strategy

Unit tests with in-memory SQLite (`:memory:`) for fast testing. No LLM calls needed.
