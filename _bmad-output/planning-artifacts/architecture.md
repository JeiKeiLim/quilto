---
stepsCompleted: [1, 2, 3]
inputDocuments:
  - '_bmad-output/swealog-project-context-v2.md'
  - '_bmad-output/swealog-bmad-context.md'
  - '_bmad-output/analysis/brainstorming-session-2025-12-31.md'
  - '_bmad-output/architecture-draft.md'
  - '_bmad-output/planning-artifacts/research/technical-swealog-foundational-research-2026-01-02.md'
  - '_bmad-output/research-questions.md'
  - '_bmad-output/planning-artifacts/prd-quilto.md'
workflowType: 'architecture'
project_name: 'swealog'
user_name: 'Jongkuk Lim'
date: '2026-01-02'
last_updated: '2026-01-30'
status: 'complete'
next_action: 'Create implementation epic for Observability support'
editHistory:
  - date: '2026-01-30'
    changes: 'Added LLM Observability architecture - Langfuse integration, ObservabilityProvider protocol, dual integration pattern'
---

# Architecture Decision Document

_This document builds collaboratively through step-by-step discovery. Sections are appended as we work through each architectural decision together._

## Project Context Analysis

### Requirements Overview

**Core Philosophy:**
"Organization is output, not input" - Users write messy scribbles, agents handle structuring and insight extraction.

**Functional Requirements:**
1. Accept unstructured text input (any domain, any format)
2. Store raw notes preserving original content
3. Parse and extract structured data asynchronously (for app consumption)
4. Retrieve relevant context based on queries
5. Generate insights from accumulated history
6. Support optional domain expertise modules for enhanced extraction

**Non-Functional Requirements:**

| Requirement | Target |
|-------------|--------|
| Local-first | Must run on Ollama, no cloud dependency required |
| Hardware | MacBook (M1/M2/M3) |
| Parsing latency | < 5 seconds |
| Parsing accuracy | > 90% (requires test corpus validation) |
| Storage | Human-readable, git-friendly |
| LLM flexibility | Local default, cloud API option for comparison |

### Key Architectural Decisions

**1. Separate Raw Notes from Parsed Data**
- `raw/` → Human + agent readable (plain markdown)
- `parsed/` → App consumption (JSON)
- LLM agents read raw directly; parsed data serves applications

**2. Directory Structure**
```
logs/
├── raw/{YYYY}/{MM}/{YYYY-MM-DD}.md
└── parsed/{YYYY}/{MM}/{YYYY-MM-DD}.json
```

**3. Plain Markdown Format**
- Daily files with `## HH:MM` sections (server-generated timestamps)
- Multiple entries per day (append model)
- Mixed content types (domain logs + random notes)

**4. No Embeddings for v1**
- Data scale fits within context windows (~109k chars/year)
- Date/keyword retrieval + summarization sufficient
- Add embeddings later only if retrieval quality degrades

**5. Immediate Async Parsing**
- Save raw synchronously (user doesn't wait)
- Parse to JSON asynchronously in background
- Retry on transient failures; error state for persistent failures
- Applications handle missing JSON gracefully

**6. Storage Abstraction Layer**
- Define `StorageInterface` early
- File-based implementation for v1
- Database-ready for future multi-user scenarios
- Same logical structure, swappable backend

### Cross-Cutting Concerns

| Concern | Approach |
|---------|----------|
| Context management | Date-based retrieval + hierarchical summarization |
| LLM abstraction | Local (Ollama) default, cloud API for experimentation |
| Domain expertise | Optional plug-in modules (enhance, not require) |
| Error handling | Retry + error state + graceful fallback |
| Multi-user future | Storage interface abstraction |

### Testing Strategy

| Priority | Item |
|----------|------|
| High | Build test corpus (start 50-100, grow to 500+) |
| High | Define accuracy metrics (field-level F1 vs exact match) |
| Medium | Treat every parse failure as new test case |

---

## Technical Stack

### Confirmed Choices

| Area | Choice | Rationale |
|------|--------|-----------|
| Package Manager | **uv** | Fast, modern, handles packages + venvs |
| Python Version | **3.13** | Latest stable |
| Testing | **pytest** + pytest-asyncio | Standard, async support |
| Layout | **Flat** (`quilto/`) | Clean imports, package-ready |

### Linting & Formatting

| Tool | Purpose | Configuration |
|------|---------|---------------|
| **Ruff** | Linting + formatting | Replaces black, isort, flake8 |
| **Ruff pydocstyle** | Docstring enforcement | Google convention, strict (D100-D417) |
| **pyright** | Type checking | Strict mode |

```toml
[tool.ruff.lint]
select = ["E", "F", "W", "I", "D", "UP", "B", "SIM"]

[tool.ruff.lint.pydocstyle]
convention = "google"
```

**Docstring Policy:** Required for all functions, classes, and methods including private. Variable docstrings where necessary.

### LLM Integration

| Component | Choice | Rationale |
|-----------|--------|-----------|
| **LLM Client** | litellm | Unified API for Ollama + cloud providers |
| **Async** | asyncio | Standard library, I/O bound operations |
| **Structured Output** | Pydantic | Validation, schema generation |

**litellm features used:**
- `api_base` for custom endpoints (local Ollama)
- `acompletion` for async calls
- Provider switching without code changes

```python
# Local
response = await litellm.acompletion(model="ollama/llama3.2", api_base="http://localhost:11434", ...)

# Cloud comparison
response = await litellm.acompletion(model="claude-sonnet-4-20250514", ...)
```

### CLI & Future Web

| Phase | Technology | Notes |
|-------|------------|-------|
| Phase 1 | **typer** + **rich** | CLI interface, beautiful output |
| Phase 2 | **FastAPI** | Web API, same async patterns |

### Repository Structure

**Phase 1: uv workspace monorepo**
```
swealog-workspace/
├── pyproject.toml              # Workspace root
├── packages/
│   ├── quilto/                 # Generic framework
│   │   ├── pyproject.toml
│   │   └── quilto/
│   └── swealog/                # Fitness app
│       ├── pyproject.toml
│       └── swealog/
```

**Naming:**
- **Quilto** - The open-source framework
- **Quiltr** - Future SaaS product name (reserved)

**Phase 2: Split when mature**
- Framework becomes standalone package
- Swealog depends on published framework

### Agent Framework Decision

**Status: DECIDED - LangGraph**

The agent system design revealed significant complexity requiring a framework:
- 13 states with 4 distinct cycles
- Human-in-the-loop (WAIT_USER state)
- Conditional routing based on verdicts
- Parallel execution (BOTH → PARSE + PLAN)
- 20+ field state management

**Decision:** Use **LangGraph** for orchestration with the following constraints:
- Use LangGraph core only, avoid langchain extras
- Keep agents as pure functions with clean interfaces
- Use LiteLLM directly in nodes (not LangChain wrappers)
- Test agents independently before graph integration

See: `_bmad-output/planning-artifacts/agent-system-design.md` (Sections 14-15)

### Quilto Public API (Orchestration)

**Status: DECIDED**

Quilto provides a single entry point for applications. Internal orchestration uses LangGraph; apps interact via clean public API.

See: `_bmad-output/planning-artifacts/quilto-api-design-session.md` (full design session)

**Entry Point:**
```python
from quilto import Quilto, load_config, StorageRepository

config = load_config("./config.yaml")  # LLM + observability config
storage = StorageRepository(base_path="./logs")

q = Quilto(
    config=config,
    storage=storage,
    domains=[FitnessDomain()],
    progress_handler=MyUIHandler(),  # Optional
    debug=False,                      # Optional
)
```

**Session-based Conversation:**
```python
session = q.create_session()
result = await session.process("How was my workout?")  # Auto-detects LOG/QUERY
result = await session.process("The bench press one")  # Clarification answer
result = await session.process("Why was Wednesday harder?")  # Follow-up
```

**Key Design Decisions:**

| Decision | Choice |
|----------|--------|
| Entry point | `Quilto` class |
| Main method | `session.process()` with auto-detect (LOG/QUERY/CORRECTION) |
| Configuration | Unified `config.yaml`; accepts config object + `StorageRepository` instance |
| Observability | `ObservabilityProvider` protocol; Langfuse default, swappable |
| Progress callbacks | `ProgressHandler` protocol (async methods) |
| Customization | Closed orchestration - apps configure via DomainModules + config flags |
| Return type | `ProcessResult` (Pydantic BaseModel) |
| Sessions | SQLite-backed via `SessionStore` abstraction |
| Conversation history | Full history with 20-turn limit (first + last N-1) |
| Clarification | LLM interprets answers (handles "1", "one", "하나", etc.) |

**Session Storage Architecture:**
```
SessionManager
└── SessionStore (Protocol)
    ├── SQLiteSessionStore (default)
    ├── PostgresSessionStore (future)
    └── InMemorySessionStore (testing)
```

**Package Structure:**
```
quilto/
├── agents/           # Individual agents
├── llm/              # LLM client abstraction
├── observability/    # Observability abstraction (see LLM Observability section)
├── state/            # Observer triggers
├── storage/          # Storage abstraction
├── session/          # Session management
│   ├── manager.py    # SessionManager
│   ├── session.py    # Session class
│   ├── models.py     # SessionData, ConversationTurn
│   └── stores/       # SessionStore implementations
├── config.py         # Unified config loading (LLM + observability)
├── quilto.py         # Quilto class (public entry point)
├── models.py         # ProcessResult, ClarificationQuestion
└── handlers.py       # ProgressHandler protocol
```

### LLM Client Abstraction

**Status: DECIDED - Tiered Configuration**

LLM calls abstracted via tiered configuration for easy provider switching:
- Per-agent model tier configuration (low/medium/high)
- Support for Ollama, Anthropic, OpenAI, Azure, OpenRouter
- Automatic fallback on failure
- No code changes required to switch providers

See: `_bmad-output/planning-artifacts/agent-system-design.md` (Section 15)

### LLM Observability

**Status: DECIDED - Langfuse with Provider Abstraction**

Observability for LLM calls and agent execution flow, enabling debugging, performance analysis, and error correlation across the 9-agent system.

See: `prd-quilto.md` (FR59-63, NFR9)

#### Location

**Decision:** `quilto/observability/`

Top-level module (not nested under `llm/`) because observability spans:
- LLM calls (via LangGraph's Langfuse integration)
- Agent execution flow (graph nodes, state transitions)
- Tool calls (storage operations, external APIs)

#### Integration Pattern

**Decision:** Dual Integration

| Layer | Integration | What Gets Traced |
|-------|-------------|------------------|
| **LangGraph** | Native Langfuse callback | Agent nodes, state transitions, LLM calls within nodes |
| **Tool calls** | Manual span instrumentation | Storage reads/writes, external operations |

**Trace structure (example query):**
```
Trace: "user query: why is my bench stuck?"
├── Span: Router (verdict: QUERY)
├── Span: Planner (extracted hints, retrieval plan)
│   └── LLM Call: planning
├── Span: Retriever
│   ├── Tool: storage.read_entries (date_range: 2026-01)
│   └── LLM Call: context summarization
├── Span: Analyzer
│   └── LLM Call: pattern analysis
├── Span: Synthesizer
│   └── LLM Call: response composition
└── Span: Evaluator (verdict: SUFFICIENT)
    └── LLM Call: quality check
```

**Tool calls requiring instrumentation:**

| Agent | Tool Operations |
|-------|-----------------|
| **Retriever** | `storage.read_entries()`, file access |
| **Parser** | `storage.write_raw()`, `storage.write_parsed()` |
| **Observer** | `storage.read_context()`, `storage.write_context()` |

#### Provider Interface

Abstraction for swappable observability backends (Langfuse MVP, future: LangSmith, Arize, OpenTelemetry):

```python
# quilto/observability/provider.py
from contextlib import AbstractContextManager
from dataclasses import dataclass
from typing import Any, Protocol, runtime_checkable

@dataclass
class SpanContext:
    """Context for an active span."""
    span_id: str
    trace_id: str

@runtime_checkable
class ObservabilityProvider(Protocol):
    """Protocol for observability backends."""

    # LangGraph integration
    def get_langgraph_callback(self) -> Any | None:
        """Return callback handler for LangGraph execution.

        Returns None if observability is disabled.
        """
        ...

    # Manual span creation (for tool calls)
    def span(
        self,
        name: str,
        metadata: dict[str, Any] | None = None,
        input: Any | None = None,
    ) -> AbstractContextManager[SpanContext]:
        """Create a span for tracing an operation.

        Usage:
            with provider.span("storage.read", metadata={"path": "..."}):
                result = storage.read(...)
        """
        ...

    # Event logging within current span
    def log_event(self, name: str, metadata: dict[str, Any] | None = None) -> None:
        """Log an event within the current trace context."""
        ...

    # Error tracking (FR63)
    def log_error(self, error: Exception, metadata: dict[str, Any] | None = None) -> None:
        """Log an error with correlation to current span."""
        ...

    # Lifecycle
    def is_enabled(self) -> bool:
        """Check if observability is active."""
        ...

    def flush(self) -> None:
        """Ensure all traces are sent (call before shutdown)."""
        ...
```

**Implementations:**
- `LangfuseProvider` - MVP implementation
- `NoOpProvider` - When observability disabled (graceful degradation per NFR9)
- `LangSmithProvider` - Future
- `ArizeProvider` - Future

#### Configuration

**Decision:** Config in `config.yaml` (renamed from `llm.yaml`)

```yaml
# config.yaml
llm:
  default_provider: ollama
  fallback_provider: anthropic
  # ... existing LLM config

observability:
  enabled: true
  provider: langfuse  # langfuse | langsmith | arize | none
  sample_rate: 1.0    # 1.0 = trace 100% of requests
```

**Credentials via environment variables:**
- `LANGFUSE_PUBLIC_KEY`
- `LANGFUSE_SECRET_KEY`
- `LANGFUSE_HOST` (optional, defaults to cloud.langfuse.com)

**Graceful degradation (NFR9):** System functions correctly when:
- `observability.enabled: false`
- Provider unavailable (connection errors)
- Missing credentials

#### Package Structure Update

```
quilto/
├── agents/           # Individual agents
├── llm/              # LLM client abstraction
├── observability/    # NEW: Observability abstraction
│   ├── __init__.py
│   ├── provider.py   # ObservabilityProvider protocol
│   ├── langfuse.py   # LangfuseProvider implementation
│   └── noop.py       # NoOpProvider (disabled/fallback)
├── state/            # Observer triggers
├── storage/          # Storage abstraction
├── session/          # Session management
├── config.py         # NEW: Unified config loading (replaces llm/loader.py)
├── quilto.py         # Quilto class (public entry point)
├── models.py         # ProcessResult, ClarificationQuestion
└── handlers.py       # ProgressHandler protocol
```

#### Public API Integration

Updated entry point with observability:

```python
from quilto import Quilto, load_config
from quilto.observability import LangfuseProvider

config = load_config("./config.yaml")  # Loads LLM + observability config

# Observability auto-configured from config, or override:
obs_provider = LangfuseProvider()  # Uses env vars for credentials

q = Quilto(
    config=config,
    storage=StorageRepository(base_path="./logs"),
    domains=[FitnessDomain()],
    observability=obs_provider,  # Optional, uses config default if omitted
)
```

#### Migration Notes

1. **Rename `llm.yaml` → `config.yaml`** - Separate story/task
2. **Update `load_llm_config()` → `load_config()`** - Returns unified config
3. **Add `observability` section to existing configs** - Backward compatible (defaults to disabled)

---

## Next Steps

1. **Create Implementation Epic for Observability**
   - `quilto/observability/provider.py` - Protocol definition
   - `quilto/observability/langfuse.py` - Langfuse implementation
   - `quilto/observability/noop.py` - NoOp implementation
   - `quilto/config.py` - Unified config loading
   - Rename `llm.yaml` → `config.yaml`
   - Instrument tool calls in agents (Retriever, Parser, Observer)

2. **Create Implementation Epic for Quilto Public API**
   - `quilto/models.py` - ProcessResult, ClarificationQuestion
   - `quilto/handlers.py` - ProgressHandler protocol
   - `quilto/session/` - Session, SessionManager, SQLiteSessionStore
   - `quilto/quilto.py` - Quilto class with LangGraph orchestration

3. **Migrate Swealog** - Replace manual agent wiring with `Quilto` usage
   - Remove ~400 lines from `swealog/api/routes/query.py`
   - Use `q = Quilto(...); session.process(...)` pattern

4. **Verify Observer** - Confirm `logs/context/` gets populated after migration

