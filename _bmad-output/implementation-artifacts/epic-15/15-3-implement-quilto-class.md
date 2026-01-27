# Story 15.3: Implement Quilto Class with LangGraph Orchestration

Status: backlog

## Story

As a **Quilto framework developer**,
I want **a Quilto class that orchestrates all agents via LangGraph**,
So that **applications have a single entry point and new agents automatically propagate**.

## Background

**Origin:** Quilto Public API Design Session (2026-01-27)
**Source:** `_bmad-output/planning-artifacts/quilto-api-design-session.md`
**Priority:** Critical | **Effort:** Large (6-8 hours)
**Type:** New code - core orchestration

This is the main deliverable of Epic 15. The Quilto class:
- Accepts LLMClient, StorageRepository, DomainModules
- Creates sessions for multi-round conversations
- Orchestrates agents via LangGraph (Router → Planner → Retriever → Analyzer → Synthesizer → Evaluator → Observer)
- Handles retry loops when Evaluator fails
- Invokes Observer triggers automatically

Current manual wiring in `swealog/api/routes/query.py` (~400 lines) will be replaced by this.

## Acceptance Criteria

1. **Given** a Quilto instance configured with llm_client, storage, and domains
   **When** `q.create_session()` is called
   **Then** a new Session is returned, ready for processing

2. **Given** a session and user input
   **When** `session.process("text")` is called
   **Then** Router classifies input and appropriate flow executes (LOG/QUERY/CORRECTION)

3. **Given** a QUERY input
   **When** processed through the pipeline
   **Then** all agents run in order: Router → Planner → Retriever → Analyzer → Synthesizer → Evaluator

4. **Given** Evaluator returns INSUFFICIENT verdict
   **When** retry limit not reached
   **Then** Planner re-plans and Retriever re-retrieves with updated instructions

5. **Given** Observer triggers enabled
   **When** query completes successfully
   **Then** Observer is invoked with post_query trigger

6. **Given** a ProgressHandler configured
   **When** agents execute
   **Then** handler methods are called (on_agent_start, on_agent_complete, on_stage)

7. **Given** conversation history in session
   **When** user provides follow-up
   **Then** agents receive conversation context for continuity

## Tasks / Subtasks

- [ ] Task 1: Create `quilto/quilto.py` with Quilto class
  - [ ] 1.1: `__init__` accepting llm_client, storage, domains, observer, max_retries, debug, progress_handler
  - [ ] 1.2: Initialize SessionManager with SQLiteSessionStore
  - [ ] 1.3: Store configuration for agent orchestration

- [ ] Task 2: Implement `create_session()` method
  - [ ] 2.1: Delegate to SessionManager.create_session()
  - [ ] 2.2: Return Session wrapper with process() method

- [ ] Task 3: Implement LangGraph state machine
  - [ ] 3.1: Define state schema (query, input_type, conversation_history, agent_outputs, etc.)
  - [ ] 3.2: Create nodes for each agent (router_node, planner_node, retriever_node, etc.)
  - [ ] 3.3: Define edges and conditional routing (LOG vs QUERY, retry loops)
  - [ ] 3.4: Wire Observer trigger after EVALUATE node

- [ ] Task 4: Implement Session.process() method
  - [ ] 4.1: Add user turn to conversation
  - [ ] 4.2: Build LangGraph state from session context
  - [ ] 4.3: Execute graph
  - [ ] 4.4: Add agent turn to conversation
  - [ ] 4.5: Return ProcessResult

- [ ] Task 5: Implement progress callbacks
  - [ ] 5.1: Call handler.on_stage() at each pipeline stage
  - [ ] 5.2: Call handler.on_agent_start/complete around each agent
  - [ ] 5.3: Call handler.on_retry() when retry loop triggers

- [ ] Task 6: Implement debug mode
  - [ ] 6.1: When debug=True, collect AgentTrace for each agent
  - [ ] 6.2: Populate ProcessResult.debug with traces

- [ ] Task 7: Write integration tests
  - [ ] 7.1: Test full QUERY flow with mock LLM
  - [ ] 7.2: Test retry loop behavior
  - [ ] 7.3: Test Observer trigger invocation
  - [ ] 7.4: Test multi-turn conversation context

- [ ] Task 8: Export from `quilto/__init__.py`
  - [ ] 8.1: Add `Quilto` to exports as primary entry point

- [ ] Task 9: Run validation
  - [ ] 9.1: Run `make check` (lint + typecheck)
  - [ ] 9.2: Run `make validate` (full validation)
  - [ ] 9.3: Run `make test-ollama` (integration with real LLM)

## Dev Notes

### Quilto Constructor Signature

```python
class Quilto:
    def __init__(
        self,
        llm_client: LLMClient,
        storage: StorageRepository,
        domains: list[DomainModule],
        observer: ObserverTriggerConfig | None = None,
        max_retries: int = 2,
        debug: bool = False,
        progress_handler: ProgressHandler | None = None,
        session_config: SessionConfig | None = None,
    ) -> None: ...

    def create_session(self) -> Session: ...
```

### LangGraph State

```python
class PipelineState(TypedDict):
    # Input
    raw_input: str
    mode: str | None  # "log", "query", or None for auto
    conversation_history: list[dict]

    # Router output
    input_type: str  # "log", "query", "both", "correction"
    selected_domains: list[str]

    # Pipeline state
    planner_output: dict | None
    retriever_output: dict | None
    analyzer_output: dict | None
    synthesizer_output: dict | None
    evaluator_output: dict | None

    # Control flow
    retry_count: int
    needs_clarification: bool
    clarification_questions: list[dict] | None

    # Final output
    response: str | None
    parsed_data: dict | None
```

### File Locations

| File | Purpose |
|------|---------|
| `packages/quilto/quilto/quilto.py` | NEW - Quilto class |
| `packages/quilto/quilto/__init__.py` | UPDATE - export Quilto |
| `packages/quilto/tests/test_quilto.py` | NEW - integration tests |

### Reference: Current Manual Wiring

See `packages/swealog/swealog/api/routes/query.py` for current implementation to migrate:
- `execute_query_pipeline()` function (lines 93-296)
- Retry loop logic (lines 196-275)
- Debug callback handling (lines 55-90)

## Test Strategy

- Unit tests with mock LLMClient (fast, deterministic)
- Integration tests with Ollama (slower, real behavior)
- Test Observer triggers are invoked (check logs/context/ directory)
