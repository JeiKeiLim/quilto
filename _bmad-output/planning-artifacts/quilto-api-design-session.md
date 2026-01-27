# Quilto Public API Design Session

**Date:** 2026-01-26
**Participants:** Jongkuk Lim, Mary (Business Analyst)
**Status:** Complete

---

## Problem Statement

Quilto framework lacks a public orchestration API. Swealog manually wires 6 agents (~400 lines). Observer infrastructure exists but is never invoked. New agents added to Quilto don't propagate to apps.

**Goal:** Design Quilto's public API so apps configure and call ONE thing.

---

## Design Questions

| # | Question | Status | Decision |
|---|----------|--------|----------|
| 1 | Entry point naming | **Done** | `Quilto` class, `q` variable |
| 2 | Public API shape | **Done** | Single `process()`, auto-detect, optional `mode=` |
| 3 | Configuration model | **Done** | Flat constructor, instances for llm_client/storage |
| 4 | Debug/Logging hooks | **Done** | ProgressHandler protocol + debug flag |
| 5 | Customization points | **Done** | Closed orchestration, config only, future concepts noted |
| 6 | Return type | **Done** | ProcessResult + Sessions + SessionManager |
| 7 | Package structure | **Done** | New modules + public exports via `__init__.py` |

---

## Discussion Log

### Session 1: 2026-01-26

#### Context Gathered

Files reviewed:
- `packages/swealog/swealog/api/routes/query.py` - Current manual wiring (394 lines)
- `packages/quilto/quilto/state/observer_triggers.py` - Observer infrastructure (unused)
- `_bmad-output/planning-artifacts/architecture.md` - Says LangGraph but not implemented
- `_bmad-output/planning-artifacts/agent-system-design.md` - 9 agents, state machine design

Key findings:
1. `execute_query_pipeline()` in Swealog does: Router → Planner → Retriever → Analyzer → Synthesizer → Evaluator
2. Observer agent exists but is NOT called anywhere in the pipeline
3. Retry loop logic (Evaluator fails → re-plan → re-retrieve) is in Swealog, not Quilto
4. `logs/logs/context/` is EMPTY - zero personalization happening

---

## Question 1: Entry Point Naming

**Discussion:**

Candidates considered:
- `QuiltoRuntime`, `Session`, `Pipeline`, `Orchestrator` - overcomplicated
- `Q`, `Quilt`, `Quilter`, `Client`, `Agent`, `Engine`, `App` - alternatives to avoid `quilto.Quilto()`

Key insight: SDK pattern (Anthropic, OpenAI, Stripe) uses brand name as class name. The "redundancy" of `quilto.Quilto()` is acceptable - most usage will be `from quilto import Quilto`.

**Decision: `Quilto`**

```python
from quilto import Quilto

q = Quilto(llm_client=..., storage=..., domains=[...])
result = await q.process("Why was my bench press heavy?")
```

Variable convention: `q` for brevity in application code.

---

## Question 2: Public API Shape

**Discussion:**

Options considered:
- **Option A: Single method, polymorphic** - `q.process()` with optional mode
- **Option B: Explicit methods** - `q.query()`, `q.log()`, `q.correct()`
- **Option C: Hybrid** - `q.process()` + explicit shortcuts

Decision factors:
- Auto-detection is core value (Router already classifies LOG/QUERY/CORRECTION)
- Forcing mode is escape hatch, not primary usage
- Corrections are conversational - require context, not explicit entry IDs
- Manual `q.correct()` has no clear use case now - defer to later

**Decision: Option A - Single `process()` method**

```python
# Primary usage - auto-detect
result = await q.process("Why was bench heavy?")         # → query
result = await q.process("Ran 5k in 22:30")              # → log
result = await q.process("Actually it was 21:30")        # → correction (from context)

# Escape hatch - force mode
result = await q.process("Ran 5k in 22:30", mode="log")
result = await q.process("...", mode="query")
```

Note: Correction auto-detection requires conversation context (addressed in Q3).

---

## Question 3: Configuration Model

**Discussion:**

Key insights:
1. `LLMClient` currently requires `LLMConfig` to construct - should be flattened
2. `ObserverTriggerConfig` exists and controls trigger behavior (post_query, user_correction, significant_log, periodic)
3. No need for separate `QuiltoConfig` class - flatten to constructor
4. Support both flat kwargs and `config_path` for file-based config

Design principles:
- `LLMClient` owns LLM configuration (separate concern)
- `StorageRepository` owns storage configuration (separate concern)
- `Quilto` accepts instances, doesn't build them
- `Quilto.config_path` only covers Quilto-specific settings

**Decision:**

```python
# Programmatic (flat)
q = Quilto(
    llm_client=llm_client,                    # LLMClient instance (required)
    storage=storage,                           # StorageRepository instance (required)
    domains=[FitnessDomain()],                 # List of DomainModule (required)
    observer=ObserverTriggerConfig(...),       # Optional, has sensible defaults
    max_retries=2,                             # Optional, default 2
    debug=False,                               # Optional, default False
)

# File-based (Quilto-specific settings only)
q = Quilto(
    llm_client=llm_client,
    storage=storage,
    domains=[...],
    config_path="./quilto.yaml",  # Loads observer, max_retries, debug
)
```

**Future refactor noted:** Flatten `LLMClient` constructor (accept flat kwargs or config_path, hide `LLMConfig` as internal)

---

## Question 4: Debug/Logging Hooks

**Discussion:**

Clarified two separate concerns:
1. **Progress callbacks** - Real-time UI updates ("Routing... Planning...")
2. **Debug mode** - Verbose logging for developer troubleshooting

Current `DebugCallback` in query.py is actually a progress callback - bad naming.

Callback interface design decisions:
- **Granularity:** Protocol/base class with multiple methods (like LangChain's BaseCallbackHandler)
- **Registration:** Constructor param for v1, single handler
- **Async vs sync:** Async from start (future-proof for streaming)

**Decision:**

```python
class ProgressHandler(Protocol):
    """Protocol for progress callbacks. Implement methods you care about."""
    async def on_agent_start(self, agent: str, input_summary: str) -> None: ...
    async def on_agent_complete(self, agent: str, elapsed: float) -> None: ...
    async def on_retry(self, attempt: int, reason: str) -> None: ...
    async def on_stage(self, stage: str) -> None: ...

# Usage
q = Quilto(
    ...,
    progress_handler=MyUIHandler(),  # Optional, single handler for v1
    debug=False,                      # Separate: verbose logging
)
```

**v1:** Single handler via constructor
**Future:** Add `add_handler()` / `remove_handler()` if multi-handler needed

---

## Question 5: Customization Points

**Discussion:**

Current customization via configuration:
- **DomainModules** - vocabulary, evaluation rules, context guidance
- **ObserverTriggerConfig** - which triggers are enabled
- **max_retries** - retry behavior

Potential future customization (not v1):
- Skip agents (e.g., skip Evaluator for speed)
- Add custom agents (e.g., custom post-processor)
- Override agent behavior (e.g., custom Analyzer)

**Decision: Keep orchestration closed for v1**

Quilto owns the pipeline. Apps configure via:
- DomainModules (influence agent behavior through data)
- Config flags (observer triggers, retries, debug)

Apps do NOT:
- Skip/reorder agents
- Inject custom agents
- Override agent implementations

**Future concepts (documented for later):**
- `skip_agents=["evaluator"]` - Performance mode
- `pre_hooks` / `post_hooks` - Custom logic injection points
- Agent registry pattern - Swap implementations

---

## Question 6: Return Type

**Discussion:**

Key design decisions made:

**1. ProcessResult structure**
- For QUERY: response, confidence, sources
- For LOG: parsed_data returned to app (app handles storage)
- Clarification questions included when needed

**2. Clarification questions with options**
- Questions can have predefined options or be free-form
- User might answer "1", "one", "하나", or "1 but also..."
- LLM resolves answer meaning (not deterministic parsing - too many variants)

**3. Sessions for multi-round conversation**
- Full conversation history, not just clarification rounds
- User asks → Agent responds → User follows up → ...
- Session tracks all turns with context

**4. Session storage**
- SessionManager with SQLite (default)
- Interface allows future backends (Postgres, etc.)
- No expiration - sessions persist until deleted
- No "completed" status - conversations can always continue

**5. Context length management**
- Hard limit on conversation turns (configurable, default 20)
- When exceeded: keep first turn + last N-1 turns
- Summarization deferred to v2

**Decision:**

```python
class ClarificationQuestion(BaseModel):
    question: str
    options: list[str] | None  # None = free-form

class ConversationTurn(BaseModel):
    role: Literal["user", "agent"]
    content: str
    timestamp: datetime
    metadata: dict[str, Any] | None  # clarification_questions, parsed_data, etc.

class SessionData(BaseModel):
    session_id: str
    created_at: datetime
    updated_at: datetime
    conversation: list[ConversationTurn]

class ProcessResult(BaseModel):
    # Core response (for QUERY)
    response: str | None
    confidence: float | None
    source_entry_ids: list[str]

    # For LOG inputs
    parsed_data: dict[str, Any] | None

    # Classification
    input_type: Literal["log", "query", "both", "correction"]
    selected_domains: list[str]

    # Clarification (if needed)
    clarification_questions: list[ClarificationQuestion] | None

    # Debug (if enabled)
    debug: ProcessDebug | None
```

**Session usage:**
```python
session = q.create_session()

result = await session.process("How was my workout?")
# Agent asks clarification → stored in conversation

result = await session.process("Bench")
# LLM interprets with full context

result = await session.process("Why was Wednesday harder?")
# Full conversation history available
```

**SessionManager:**
```python
class SessionManager:
    def create_session(self) -> Session: ...
    def get_session(self, session_id: str) -> Session | None: ...
    def list_sessions(self) -> list[SessionInfo]: ...
    def delete_session(self, session_id: str) -> bool: ...

class SessionConfig(BaseModel):
    max_conversation_turns: int = 20  # Hard limit, keeps first + last N-1
```

**SessionStore abstraction (database layer):**
```python
class SessionStore(Protocol):
    """Abstract storage backend for sessions. SQLite default, extensible."""
    def save(self, session_data: SessionData) -> None: ...
    def load(self, session_id: str) -> SessionData | None: ...
    def list_all(self) -> list[SessionInfo]: ...
    def delete(self, session_id: str) -> bool: ...

# Implementations
class SQLiteSessionStore(SessionStore):
    """Default SQLite-based storage."""
    def __init__(self, db_path: str = "quilto_sessions.db"): ...

# Future
class PostgresSessionStore(SessionStore): ...
class InMemorySessionStore(SessionStore): ...  # For testing
```

---

## Question 7: Package Structure

**Discussion:**

New code to add:
- `Quilto` class (main entry point)
- `Session` class
- `SessionManager` + `SessionStore` protocol
- `SQLiteSessionStore` (default implementation)
- `ProcessResult`, `ClarificationQuestion`, `ConversationTurn`
- `ProgressHandler` protocol
- Orchestration logic (moved from Swealog)

**Decision:**

```
quilto/
├── agents/                  # Existing - individual agents
├── llm/                     # Existing - LLM client
├── state/                   # Existing - observer triggers
├── storage/                 # Existing - storage abstraction
├── session/                 # NEW - session management
│   ├── __init__.py
│   ├── manager.py           # SessionManager
│   ├── session.py           # Session class
│   ├── models.py            # SessionData, ConversationTurn, SessionConfig
│   └── stores/
│       ├── __init__.py
│       ├── base.py          # SessionStore protocol
│       └── sqlite.py        # SQLiteSessionStore
├── domain.py                # Existing
├── domain_selector.py       # Existing
├── quilto.py                # NEW - Quilto class
├── models.py                # NEW - ProcessResult, ClarificationQuestion
├── handlers.py              # NEW - ProgressHandler protocol
└── __init__.py              # Updated - public exports
```

**Public exports (`quilto/__init__.py`):**
```python
from quilto.quilto import Quilto
from quilto.models import ProcessResult, ClarificationQuestion, ProcessDebug
from quilto.handlers import ProgressHandler
from quilto.session import Session, SessionManager, SessionConfig
from quilto.session.stores import SessionStore, SQLiteSessionStore

# Existing exports remain
from quilto.llm import LLMClient, LLMConfig
from quilto.storage import StorageRepository
from quilto.domain import DomainModule
from quilto.state import ObserverTriggerConfig

__all__ = [
    # Core
    "Quilto",
    "ProcessResult",
    "ClarificationQuestion",
    "ProcessDebug",
    "ProgressHandler",
    # Session
    "Session",
    "SessionManager",
    "SessionConfig",
    "SessionStore",
    "SQLiteSessionStore",
    # Dependencies (user provides these)
    "LLMClient",
    "LLMConfig",
    "StorageRepository",
    "DomainModule",
    "ObserverTriggerConfig",
]
```

**Usage:**
```python
from quilto import Quilto, LLMClient, StorageRepository, ProcessResult
```

---

## Final Design Summary

### Public API

```python
from quilto import Quilto, LLMClient, StorageRepository

# Setup
llm_client = LLMClient(config_path="./llm.yaml")
storage = StorageRepository(base_path="./logs")

q = Quilto(
    llm_client=llm_client,
    storage=storage,
    domains=[FitnessDomain()],
    progress_handler=MyUIHandler(),  # Optional
    debug=False,                      # Optional
)

# Multi-round conversation
session = q.create_session()

result = await session.process("How was my workout last week?")
# result.clarification_questions = [...]

result = await session.process("The bench press one")
# result.response = "Your bench press was strong..."

result = await session.process("Why was Wednesday harder?")
# Full context available
```

### Key Design Decisions

| Decision | Choice |
|----------|--------|
| Entry point | `Quilto` class |
| Main method | `session.process()` with auto-detect |
| Configuration | Flat constructor, accepts instances |
| Progress callbacks | `ProgressHandler` protocol (async) |
| Customization | Closed orchestration, config-only |
| Return type | `ProcessResult` (Pydantic) |
| Sessions | SQLite-backed, full conversation history |
| Context limits | Hard limit (20 turns), keep first + last N-1 |

### Architecture

```
Quilto (entry point)
├── SessionManager
│   └── SessionStore (SQLite default, extensible)
├── Orchestration (Router → Planner → Retriever → ... → Observer)
├── ProgressHandler (callbacks)
└── Dependencies
    ├── LLMClient (provided by app)
    ├── StorageRepository (provided by app)
    └── DomainModule[] (provided by app)
```

### Future Work (documented, not v1)

- Flatten `LLMClient` constructor
- Multi-handler support (`add_handler()`)
- Skip agents / custom hooks
- Conversation summarization
- PostgresSessionStore

---

## Next Steps

1. **Update architecture.md** - Add orchestration design to official architecture
2. **Create Epic** - Implementation stories for Quilto public API
3. **Implement** - Priority order:
   - `quilto/models.py` - ProcessResult, ClarificationQuestion
   - `quilto/handlers.py` - ProgressHandler protocol
   - `quilto/session/` - Session, SessionManager, SQLiteSessionStore
   - `quilto/quilto.py` - Quilto class with orchestration
4. **Migrate Swealog** - Replace manual wiring with `Quilto` usage
5. **Test Observer** - Verify `logs/logs/context/` gets populated
