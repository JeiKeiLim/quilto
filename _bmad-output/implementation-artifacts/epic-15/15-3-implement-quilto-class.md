# Story 15.3: Implement Quilto Class with LangGraph Orchestration

Status: done (code-reviewed)

## Story

As a **Quilto framework developer**,
I want **a Quilto class that orchestrates all agents via LangGraph**,
So that **applications have a single entry point and new agents automatically propagate**.

## Background

**Origin:** Quilto Public API Design Session (2026-01-26)
**Source:** `_bmad-output/planning-artifacts/quilto-api-design-session.md`
**Priority:** CRITICAL | **Effort:** Large (6-8 hours)
**Type:** New code - core framework orchestration
**Depends On:** Story 15.1 (ProcessResult, ClarificationQuestion), Story 15.2 (Session, SessionManager)

**Problem Statement:**
- Swealog manually wires 6 agents (~400 lines in `swealog/api/routes/query.py`)
- Observer infrastructure exists but is NEVER invoked (`logs/logs/context/` is EMPTY)
- New agents added to Quilto don't propagate to apps
- Every Quilto application would have to copy the same orchestration code

**Solution:**
- `Quilto` class as single entry point
- LangGraph for internal orchestration (Router → Planner → Retriever → Analyzer → Synthesizer → Evaluator → Observer)
- `Session` wraps conversation context and calls Quilto orchestration internally
- Observer triggers automatically on query completion

**Key Design Decision:** The `session.process()` method is the main entry point. It auto-detects input type (LOG/QUERY/BOTH/CORRECTION) via Router and executes the appropriate flow.

## Acceptance Criteria

1. **Given** a Quilto instance configured with llm_client, storage, and domains
   **When** `q.create_session()` is called
   **Then** a new Session is returned, ready for processing

2. **Given** a session and user input
   **When** `session.process("text")` is called
   **Then** Router classifies input and appropriate flow executes (LOG/QUERY/BOTH/CORRECTION)

3. **Given** a QUERY input
   **When** processed through the pipeline
   **Then** all agents run: Router → Planner → Retriever → Analyzer → Synthesizer → Evaluator

4. **Given** Evaluator returns INSUFFICIENT verdict
   **When** retry limit not reached
   **Then** Planner re-plans and Retriever re-retrieves with updated instructions

5. **Given** Observer triggers enabled
   **When** query completes successfully
   **Then** Observer is invoked with post_query trigger

6. **Given** a ProgressHandler configured
   **When** agents execute
   **Then** handler methods are called (on_agent_start, on_agent_complete, on_stage)

7. **Given** a LOG input
   **When** processed through the pipeline
   **Then** Router classifies, Parser runs, and result contains parsed_data

8. **Given** a session with existing conversation history
   **When** new input is processed
   **Then** conversation context is passed to Planner for continuity

9. **Given** a BOTH input (log + query combined)
   **When** processed through the pipeline
   **Then** query flow completes first, then parse flow runs sequentially

10. **Given** a CORRECTION input
    **When** processed through the pipeline
    **Then** treated as LOG variant with `process_correction` for upsert semantics

## Tasks / Subtasks

- [x] Task 1: Create Quilto class in `packages/quilto/quilto/quilto.py` (AC: #1)
  - [x] 1.1: Create `Quilto` class with constructor accepting `llm_client: LLMClient`, `storage: StorageRepository`, `domains: list[DomainModule]`
  - [x] 1.2: Add optional constructor params: `observer: ObserverTriggerConfig | None`, `max_retries: int = 2`, `debug: bool = False`, `progress_handler: ProgressHandler | None`
  - [x] 1.3: Add optional `session_db_path: str = "quilto_sessions.db"` param for SQLite location
  - [x] 1.4: Initialize internal `SessionManager` with `SQLiteSessionStore`
  - [x] 1.5: Implement `create_session() -> Session` that delegates to SessionManager (Session needs Quilto reference)
  - [x] 1.6: Store domains and initialize `DomainSelector` - use `selector.select_domains(query)` to get selected domains, then `selector.build_context(selected)` to get `ActiveDomainContext`
  - [x] 1.7: Add internal method `_get_storage_summary() -> dict` that calls `storage.get_storage_summary()` - required by PlannerAgent

- [x] Task 2: Extend Session class for processing (AC: #2, #7, #8, #9, #10)
  - [x] 2.1: Add `_quilto` reference to Session class (set via constructor or method)
  - [x] 2.2: Implement `async process(text: str, mode: Literal["auto", "log", "query"] | None = None) -> ProcessResult`
  - [x] 2.3: In `process()`, add user turn to conversation before processing
  - [x] 2.4: In `process()`, add agent turn with response after processing (include clarification questions in metadata if any)
  - [x] 2.5: Build conversation context string from history - use last 4 turns formatted as `{role}: {content}` (respects 20-turn overall limit via pruning)
  - [x] 2.6: When `mode="log"` or `mode="query"` is forced, bypass Router classification and set input_type directly

- [x] Task 3: Create orchestration graph with LangGraph (AC: #3, #4, #9, #10)
  - [x] 3.1: Create `packages/quilto/quilto/orchestration.py` with LangGraph StateGraph
  - [x] 3.2: Define `QuiltoState` TypedDict with all agent outputs and flow control (reuse fields from `quilto/state/models.py:SessionState` where applicable)
  - [x] 3.3: Create node functions: `route_node`, `plan_node`, `retrieve_node`, `analyze_node`, `synthesize_node`, `evaluate_node`
  - [x] 3.4: Add conditional edges based on Router classification and Evaluator verdict
  - [x] 3.5: Implement retry loop: Evaluator INSUFFICIENT → Planner (with feedback) → Retriever → Analyzer → Synthesizer → Evaluator
  - [x] 3.6: Add termination condition when max_retries reached (return partial response)
  - [x] 3.7: **BOTH flow**: After EVALUATE passes, conditionally route to `parse_node` if `input_type == "both"`, then to `observe_node`
  - [x] 3.8: **CORRECTION flow**: Route to `correction_node` that uses `process_correction()` from `quilto/flow.py` (already exists), with upsert semantics
  - [x] 3.9: Wrap all agent calls in try/except - on error, set `state["error"] = str(e)` and route to END with partial result

- [x] Task 4: Implement LOG flow in orchestration (AC: #7)
  - [x] 4.1: Create `parse_node` that invokes ParserAgent
  - [x] 4.2: Route to `parse_node` when Router classifies as LOG
  - [x] 4.3: Return ProcessResult with `parsed_data` populated

- [x] Task 5: Implement Observer integration (AC: #5)
  - [x] 5.1: Create `observe_node` that invokes ObserverAgent with post_query trigger
  - [x] 5.2: Add observe_node as final node in successful query completion path
  - [x] 5.3: Check `ObserverTriggerConfig.post_query` before invoking Observer
  - [x] 5.4: Pass query result context to Observer for learning

- [x] Task 6: Implement ProgressHandler callbacks (AC: #6)
  - [x] 6.1: Create wrapper to call `on_stage(stage)` at each flow transition
  - [x] 6.2: Call `on_agent_start(agent, input_summary)` before each agent
  - [x] 6.3: Call `on_agent_complete(agent, elapsed)` after each agent
  - [x] 6.4: Call `on_retry(attempt, reason)` when retry loop triggers
  - [x] 6.5: Handle None progress_handler gracefully (no-op)

- [x] Task 7: Build ProcessResult from orchestration output (AC: #2, #3, #7)
  - [x] 7.1: Map Router output to `input_type` field
  - [x] 7.2: Map Synthesizer output to `response` field
  - [x] 7.3: Map Retriever output to `source_entry_ids` field
  - [x] 7.4: Calculate `confidence` from Analyzer verdict and Evaluator scores
  - [x] 7.5: Map Parser output to `parsed_data` field (for LOG inputs)
  - [x] 7.6: Map Planner clarify_questions to `clarification_questions` field
  - [x] 7.7: Include debug traces in `ProcessResult.debug` if `debug=True`

- [x] Task 8: Handle clarification flow (AC: #2)
  - [x] 8.1: When Planner returns `next_action="clarify"`, set clarification_questions in ProcessResult
  - [x] 8.2: On next `session.process()` call, include conversation context for answer interpretation
  - [x] 8.3: Planner interprets user answer (handles "1", "one", "하나", free-form text via LLM)

- [x] Task 9: Update package exports (AC: all)
  - [x] 9.1: Export `Quilto` from `quilto/__init__.py`
  - [x] 9.2: Add `Quilto` to `__all__` list
  - [x] 9.3: Verify import: `from quilto import Quilto`

- [x] Task 10: Write unit tests in `packages/quilto/tests/test_quilto.py` (AC: all)
  - [x] 10.1: Test `Quilto` initialization with required params
  - [x] 10.2: Test `create_session()` returns valid Session with process method
  - [x] 10.3: Test `session.process()` with mock LLM for QUERY flow
  - [x] 10.4: Test `session.process()` with mock LLM for LOG flow
  - [x] 10.5: Test retry loop triggers when Evaluator returns INSUFFICIENT
  - [x] 10.6: Test ProgressHandler callbacks are invoked correctly
  - [x] 10.7: Test Observer is invoked on query completion (verify via mock)
  - [x] 10.8: Test conversation history is passed to subsequent process calls
  - [x] 10.9: Test debug mode includes traces in ProcessResult
  - [x] 10.10: Test partial response returned after max_retries
  - [x] 10.11: Test clarification questions flow
  - [x] 10.12: Test BOTH flow - query completes, then parse runs
  - [x] 10.13: Test CORRECTION flow - uses process_correction with upsert
  - [x] 10.14: Test forced `mode="log"` bypasses Router classification
  - [x] 10.15: Test error handling in node functions - partial result returned on agent failure

- [x] Task 11: Run validation
  - [x] 11.1: `make check` passes (lint + typecheck)
  - [x] 11.2: `make validate` passes (lint + format + typecheck + test)

## Dev Notes

### Public API (from Design Session)

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

### LangGraph State Machine Design

Based on `agent-system-design.md`, the orchestration has these states:

**QUERY Flow:**
```
ROUTE → PLAN → RETRIEVE → ANALYZE → SYNTHESIZE → EVALUATE → OBSERVE → END
                    ↑                                 │
                    └─────── INSUFFICIENT ────────────┘
```

**LOG Flow:**
```
ROUTE → PARSE → OBSERVE → END
```

**BOTH Flow (sequential - query first, then parse):**
```
ROUTE → PLAN → RETRIEVE → ANALYZE → SYNTHESIZE → EVALUATE → PARSE → OBSERVE → END
```

**CORRECTION Flow (LOG variant with upsert):**
```
ROUTE → CORRECTION → OBSERVE → END
```
Uses `process_correction()` from `quilto/flow.py` which handles raw content updates and re-parsing.

### QuiltoState TypedDict

**Note:** Reuse patterns from existing `quilto/state/models.py:SessionState` where applicable. Key fields:

```python
from typing import TypedDict, Any

class QuiltoState(TypedDict, total=False):
    # Input
    user_input: str
    mode: str | None  # "auto", "log", "query"
    conversation_context: str | None

    # Router output
    input_type: str  # "log", "query", "both", "correction"
    selected_domains: list[str]

    # Planner output
    query_type: str
    retrieval_instructions: list[dict]
    next_action: str  # "retrieve", "clarify"
    clarify_questions: list[dict] | None

    # Retriever output
    entries: list[dict]
    retrieval_summary: list[dict]
    source_entry_ids: list[str]

    # Analyzer output
    analysis_verdict: str
    analysis_findings: list[dict]

    # Synthesizer output
    response: str

    # Evaluator output
    eval_verdict: str
    eval_feedback: list[str]

    # Parser output (for LOG/BOTH)
    parsed_data: dict | None

    # Correction output (for CORRECTION)
    correction_result: dict | None  # CorrectionResult.model_dump()

    # Control
    retry_count: int
    max_retries: int
    is_partial: bool
    error: str | None  # Set when agent fails

    # Context objects (CRITICAL for agent calls)
    domain_context: Any  # ActiveDomainContext from DomainSelector.build_context()
    storage_summary: dict  # REQUIRED: from storage.get_storage_summary()

    # Debug
    traces: list[dict]
```

### Existing Code to Reuse

The orchestration logic already exists in `swealog/api/routes/query.py`:
- `execute_query_pipeline()` function (~200 lines) - lines 93-296
- Agent instantiation patterns
- Retry loop logic - lines 196-275
- Confidence calculation - `_calculate_confidence()` function
- Debug timer class - `_DebugTimer` class

This should be **moved** to Quilto, not copied. The migration story (15.4) will remove it from Swealog.

### Existing Quilto Agents (from `quilto/agents/`)

All agents already exist with consistent interfaces:

| Agent | Constructor | Main Method | Key Notes |
|-------|-------------|-------------|-----------|
| `RouterAgent` | `(llm_client: LLMClient)` | `async classify(input: RouterInput) -> RouterOutput` | Classifies input type, selects domains |
| `PlannerAgent` | `(llm_client: LLMClient)` | `async plan(input: PlannerInput) -> PlannerOutput` | Creates retrieval plan, handles clarify |
| `RetrieverAgent` | `(storage: StorageRepository)` | `async retrieve(input: RetrieverInput) -> RetrieverOutput` | **No LLM** - deterministic fetch |
| `AnalyzerAgent` | `(llm_client: LLMClient)` | `async analyze(input: AnalyzerInput) -> AnalyzerOutput` | Patterns, sufficiency verdict |
| `SynthesizerAgent` | `(llm_client: LLMClient)` | `async synthesize(input: SynthesizerInput) -> SynthesizerOutput` | Generates response |
| `EvaluatorAgent` | `(llm_client: LLMClient)` | `async evaluate(input: EvaluatorInput) -> EvaluatorOutput` | Quality check verdict |
| `ParserAgent` | `(llm_client: LLMClient)` | `async parse(input: ParserInput) -> ParserOutput` | Parses LOG input |
| `ObserverAgent` | `(llm_client: LLMClient)` | `async observe(input: ObserverInput) -> ObserverOutput` | Learns from interactions |

**Existing Correction Flow:** `process_correction()` from `quilto/flow.py` handles CORRECTION input type (already implemented)

### Session Class Modification Strategy

The Session class from Story 15.2 needs the `process()` method. Two approaches:

**Option A: Modify Session directly (RECOMMENDED)**
- Add `_quilto: "Quilto" | None` attribute
- Add `process()` async method
- SessionManager passes Quilto reference when creating Session

**Option B: Create ProcessableSession subclass**
- Inherit from Session
- Add process() method
- Quilto.create_session() returns ProcessableSession

Recommend Option A for simplicity. Use `TYPE_CHECKING` for circular import handling.

### Circular Import Handling

```python
# In session.py
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from quilto.quilto import Quilto

class Session:
    def __init__(
        self,
        data: SessionData,
        store: "SessionStore",
        config: SessionConfig,
        quilto: "Quilto | None" = None,  # Optional for backwards compat
    ) -> None:
        self._quilto = quilto
        ...
```

### Observer Trigger Integration

From `quilto/state/observer_triggers.py`:
```python
class ObserverTriggerConfig(BaseModel):
    post_query: bool = True
    user_correction: bool = True
    significant_log: bool = True
    periodic_hours: int | None = None
```

Observer should be invoked after successful query completion with:
- Query text
- Response text
- Retrieved entries context
- Current global context (if exists)

### Confidence Calculation (from query.py)

```python
_CONFIDENCE_SUFFICIENT = 0.8
_CONFIDENCE_PARTIAL = 0.6
_CONFIDENCE_INSUFFICIENT = 0.4
_CONFIDENCE_ADJUSTMENT = 0.1

def _calculate_confidence(analysis: AnalyzerOutput, evaluation: EvaluatorOutput) -> float:
    if analysis.verdict == Verdict.SUFFICIENT:
        base = _CONFIDENCE_SUFFICIENT
    elif analysis.verdict == Verdict.PARTIAL:
        base = _CONFIDENCE_PARTIAL
    else:
        base = _CONFIDENCE_INSUFFICIENT

    adjustment = _CONFIDENCE_ADJUSTMENT if evaluation.overall_verdict == Verdict.SUFFICIENT else -_CONFIDENCE_ADJUSTMENT
    return min(1.0, max(0.0, base + adjustment))
```

### LangGraph Integration Pattern

Use existing patterns from `quilto/state/` modules. Key integration points:

```python
from langgraph.graph import StateGraph, END

def create_orchestration_graph(quilto: "Quilto") -> StateGraph:
    """Create the agent orchestration graph.

    Note: domain_context is built dynamically after Router selects domains.
    storage_summary is fetched before plan_node runs.
    """
    graph = StateGraph(QuiltoState)

    # Add nodes - each node factory captures required dependencies
    graph.add_node("route", make_route_node(quilto.llm_client, quilto.domain_selector))
    graph.add_node("plan", make_plan_node(quilto.llm_client, quilto.storage))  # Gets storage_summary
    graph.add_node("retrieve", make_retrieve_node(quilto.storage))
    graph.add_node("analyze", make_analyze_node(quilto.llm_client))
    graph.add_node("synthesize", make_synthesize_node(quilto.llm_client))
    graph.add_node("evaluate", make_evaluate_node(quilto.llm_client))
    graph.add_node("parse", make_parse_node(quilto.llm_client))
    graph.add_node("correction", make_correction_node(quilto.llm_client, quilto.storage))
    graph.add_node("observe", make_observe_node(quilto.llm_client, quilto.observer_config))

    graph.set_entry_point("route")

    # Route based on input_type
    graph.add_conditional_edges("route", route_classifier, {
        "query": "plan",
        "log": "parse",
        "both": "plan",  # Query first
        "correction": "correction",
    })

    graph.add_conditional_edges("plan", plan_classifier, {
        "retrieve": "retrieve",
        "clarify": END,
    })

    graph.add_edge("retrieve", "analyze")
    graph.add_edge("analyze", "synthesize")
    graph.add_edge("synthesize", "evaluate")

    # After evaluate: check pass/retry, and handle BOTH flow
    graph.add_conditional_edges("evaluate", evaluate_classifier, {
        "pass": "check_both",  # New intermediate node
        "retry": "plan",
        "max_retries": "check_both",
    })

    # Handle BOTH: if input_type=="both", run parse after query completes
    graph.add_conditional_edges("check_both", both_classifier, {
        "parse": "parse",
        "observe": "observe",
    })

    graph.add_edge("parse", "observe")
    graph.add_edge("correction", "observe")
    graph.add_edge("observe", END)

    return graph.compile()
```

### Previous Story Patterns (Story 15.2)

Key learnings from Story 15.2:
- `Session.get_history()` returns a copy to prevent mutation
- All models use `ConfigDict(strict=True)`
- Use `Field(default_factory=list)` for mutable defaults
- Use `@runtime_checkable` on Protocol classes
- SQLiteSessionStore maintains persistent connection for `:memory:` DBs

### File Structure

```
quilto/
├── quilto.py          # NEW: Quilto class
├── orchestration.py   # NEW: LangGraph graph definition
├── models.py          # EXISTS: ProcessResult (from 15.1)
├── handlers.py        # EXISTS: ProgressHandler (from 15.1)
├── flow.py            # EXISTS: process_correction() - reuse for CORRECTION flow
├── domain_selector.py # EXISTS: DomainSelector - use for domain context
├── session/           # EXISTS (from 15.2) - needs modification
│   ├── session.py     # MODIFY: Add process() method, _quilto reference
│   └── manager.py     # MODIFY: Pass Quilto reference when creating Session
├── state/             # EXISTS: Routing functions, ObserverTriggerConfig
│   ├── models.py      # SessionState TypedDict - reference patterns
│   └── observer_triggers.py  # ObserverTriggerConfig, trigger_* functions
└── agents/            # EXISTS: All 8 agent implementations
```

### Files to Create/Modify

| File | Action | Purpose |
|------|--------|---------|
| `packages/quilto/quilto/quilto.py` | CREATE | Quilto class |
| `packages/quilto/quilto/orchestration.py` | CREATE | LangGraph graph definition |
| `packages/quilto/quilto/session/session.py` | UPDATE | Add process() method |
| `packages/quilto/quilto/session/manager.py` | UPDATE | Pass Quilto reference |
| `packages/quilto/quilto/__init__.py` | UPDATE | Export Quilto |
| `packages/quilto/tests/test_quilto.py` | CREATE | Unit tests |

### Test Strategy

Use mock LLM client that returns canned responses. Test:
1. Graph traversal (which nodes execute in which order)
2. State transformations at each node
3. Conditional edge routing
4. Retry loop behavior
5. ProgressHandler callback invocations
6. ProcessResult population

```python
@pytest.fixture
def mock_llm_client():
    """Mock LLM that returns predictable responses."""
    from unittest.mock import AsyncMock, MagicMock

    client = MagicMock()
    # Mock Router response
    client.complete = AsyncMock(return_value=...)
    return client
```

### Common Mistakes to Avoid

| Mistake | Correct Pattern | Source |
|---------|-----------------|--------|
| Not awaiting async methods | All agent calls are async | query.py |
| Missing error handling in nodes | Wrap agent calls in try/except, set `state["error"]` | New pattern |
| Not passing domain_context through | Thread `ActiveDomainContext` to all agents | query.py |
| Observer not actually invoked | Check trigger config, then invoke | Epic 15 rationale |
| Circular import Session ↔ Quilto | Use TYPE_CHECKING import | Common Python pattern |
| Hardcoding retry count | Use configurable `max_retries` | Architecture |
| Not updating conversation on error | Always add agent turn, even on failure | New requirement |
| Missing ProgressHandler null check | Check `if handler:` before calling | handlers.py |
| Forgetting storage_summary for Planner | **ALWAYS** call `storage.get_storage_summary()` before plan_node | Story 13.2 |
| Missing BOTH flow handling | After EVALUATE, check `input_type == "both"` → run PARSE | agent-system-design.md |
| Missing CORRECTION flow | Use `process_correction()` from `quilto/flow.py` | agent-system-design.md |
| Not building ActiveDomainContext | Call `DomainSelector.select_domains()` then `.build_context()` | quilto/domain_selector.py |

### Dependencies

- `langgraph>=0.2.0` - For StateGraph orchestration (already in pyproject.toml)
- All existing Quilto agent modules (8 agents, all production-ready)
- Story 15.1 models (ProcessResult, ClarificationQuestion, ProcessDebug, AgentTrace)
- Story 15.2 session management (Session, SessionManager, SQLiteSessionStore)
- Existing modules to reuse:
  - `quilto/flow.py` → `process_correction()` for CORRECTION flow
  - `quilto/domain_selector.py` → `DomainSelector` for domain context building
  - `quilto/state/observer_triggers.py` → `ObserverTriggerConfig`, trigger functions

### Validation Checklist (Run Before Marking Done)

**Code Quality:**
- [ ] All new classes have Google-style docstrings
- [ ] All async methods are properly awaited
- [ ] No circular imports at runtime
- [ ] Modern type hints: `list[str]` not `List[str]`, `X | None` not `Optional[X]`
- [ ] ProgressHandler methods handle None gracefully

**Exports:**
- [ ] `Quilto` exported from `quilto/__init__.py`
- [ ] `Quilto` in `__all__` list
- [ ] Import verification: `from quilto import Quilto`

**Tests:**
- [ ] `Quilto` initialization with required params
- [ ] `create_session()` returns Session with process method
- [ ] QUERY flow executes all agents in order
- [ ] LOG flow routes to parse node
- [ ] BOTH flow: query completes, then parse runs
- [ ] CORRECTION flow: uses process_correction with upsert
- [ ] Retry loop triggers on INSUFFICIENT verdict
- [ ] Retry stops after max_retries
- [ ] ProgressHandler callbacks invoked
- [ ] Observer invoked on query completion
- [ ] Conversation history passed to subsequent calls
- [ ] Debug mode populates ProcessResult.debug
- [ ] Clarification questions flow works
- [ ] Forced `mode="log"` bypasses Router
- [ ] Error handling returns partial result on agent failure

**Final Validation:**
- [ ] `make check` passes (lint + typecheck)
- [ ] `make validate` passes (lint + format + typecheck + test)

### References

| Source | Content |
|--------|---------|
| `_bmad-output/planning-artifacts/quilto-api-design-session.md` | Full API design decisions |
| `_bmad-output/planning-artifacts/architecture.md#Quilto Public API` | Architecture documentation |
| `_bmad-output/planning-artifacts/agent-system-design.md` | Agent orchestration design, state machine, CORRECTION handling |
| `packages/swealog/swealog/api/routes/query.py` | Existing pipeline to migrate (lines 93-296) |
| `packages/quilto/quilto/state/observer_triggers.py` | Observer trigger config |
| `packages/quilto/quilto/flow.py` | `process_correction()` for CORRECTION flow |
| `packages/quilto/quilto/domain_selector.py` | DomainSelector for domain context |
| `_bmad-output/project-context.md` | Validation rules and common mistakes |
| `_bmad-output/implementation-artifacts/epic-15/15-2-implement-session-management.md` | Previous story patterns |

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

### Completion Notes List

- Implementation complete with full LangGraph orchestration
- All 28 unit tests pass
- Code review fixes applied:
  - CRIT-2: Fixed `is_partial` flag now set in `check_both_node` when max_retries reached
  - CRIT-3: Removed unused `config` parameter from `create_session()`
  - MED-4: Added `total_elapsed_ms` calculation in `session.process()`

### File List

| File | Action |
|------|--------|
| `packages/quilto/quilto/quilto.py` | CREATE |
| `packages/quilto/quilto/orchestration.py` | CREATE |
| `packages/quilto/quilto/session/session.py` | UPDATE |
| `packages/quilto/quilto/__init__.py` | UPDATE |
| `packages/quilto/tests/test_quilto.py` | CREATE |

### Change Log

| Date | Change | Author |
|------|--------|--------|
| 2026-01-27 | Code review: Fixed is_partial flag, removed unused config param, added total_elapsed_ms | Claude Opus 4.5 |
