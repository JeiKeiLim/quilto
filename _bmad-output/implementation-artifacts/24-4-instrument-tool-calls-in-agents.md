# Story 24.4: Instrument Tool Calls in Agents

Status: done

## Story

As a **Quilto developer**,
I want **storage operations traced**,
so that **I can see full execution flow including tool calls in Langfuse**.

## Acceptance Criteria

1. **Given** Retriever agent storage reads
   **When** `storage.get_entries_by_date_range()` called
   **Then** operation is wrapped in span with metadata (date_range, domain, entries_found)

2. **Given** Parser agent storage writes (in parse_node)
   **When** `storage.save_entry()` called
   **Then** operation is wrapped in span with file paths and entry_id

3. **Given** Observer agent context operations
   **When** `context_manager.read_context()` and `context_manager.apply_updates()` called
   **Then** operations are wrapped in spans with context metadata

4. **Given** trace in Langfuse
   **When** viewed
   **Then** shows nested structure:
   ```
   Trace: "user query"
   ├── Span: Router
   ├── Span: Retriever
   │   └── Tool: storage.get_entries_by_date_range
   ├── Span: Analyzer
   └── Span: Synthesizer
   ```

5. **Given** NoOpProvider used (observability disabled)
   **When** agents execute storage operations
   **Then** no errors occur and agents function normally

## Tasks / Subtasks

- [x] Task 1: Add ObservabilityProvider to orchestration state (AC: #1, #2, #3, #5)
  - [x] Add `observability_provider` field to QuiltoState TypedDict
  - [x] Add StateKeys.OBSERVABILITY constant
  - [x] Pass provider from Quilto instance to state in `create_orchestration_graph`

- [x] Task 2: Instrument retrieve_node storage reads (AC: #1, #4, #5)
  - [x] Get ObservabilityProvider from state in `retrieve_node`
  - [x] Wrap `storage.get_entries_by_date_range()` call in `provider.span()` context manager
  - [x] Include metadata: `start_date`, `end_date`, `entries_found`
  - [x] Handle NoOpProvider gracefully (no-op spans work correctly)

- [x] Task 3: Instrument parse_node storage writes (AC: #2, #4, #5)
  - [x] Get ObservabilityProvider from state in `parse_node`
  - [x] Wrap `storage.save_entry()` call in `provider.span()` context manager
  - [x] Include metadata: `entry_id`, `file_path`, `domains`

- [x] Task 4: Instrument observe_node context operations (AC: #3, #4, #5)
  - [x] Get ObservabilityProvider from state in `observe_node`
  - [x] Wrap `context_manager.read_context()` in `provider.span()` with metadata
  - [x] Wrap `context_manager.apply_updates()` in `provider.span()` with `updates_count` metadata

- [x] Task 5: Instrument correction_node storage operations (AC: #2, #4, #5)
  - [x] Get ObservabilityProvider from state in `correction_node`
  - [x] Wrap `storage.get_entries_by_date_range()` call in span (recent entries fetch)
  - [x] Note: Correction's storage writes happen in `process_correction` flow - instrument there too

- [x] Task 6: Write unit tests (AC: #5)
  - [x] Test: retrieve_node works normally with NoOpProvider
  - [x] Test: parse_node works normally with NoOpProvider
  - [x] Test: observe_node works normally with NoOpProvider
  - [x] Test: correction_node works normally with NoOpProvider

- [x] Task 7: Write Langfuse integration test (AC: #1, #2, #3, #4) **REQUIRED**
  - [x] Create test with real LangfuseProvider using credentials from .env
  - [x] Run a QUERY flow that triggers Retriever
  - [x] Run a LOG flow that triggers Parser
  - [x] Call `provider.flush()` to ensure delivery
  - [x] Retrieve trace via Langfuse API: `langfuse.get_trace(trace_id)`
  - [x] Assert: Tool spans exist nested under agent spans
  - [x] Assert: Metadata includes operation details (date_range, file paths)

## Dev Notes

### Architecture Compliance

**Location:** Changes primarily in `packages/quilto/quilto/orchestration.py`

**Integration Pattern (from Architecture):**
> **Dual Integration:**
> - **LangGraph:** Native Langfuse callback → Agent nodes, state transitions, LLM calls
> - **Tool calls:** Manual span instrumentation → Storage reads/writes, external operations

This story implements the **manual span instrumentation** part for tool calls.

### Story 24.1, 24.2, 24.3 Established Patterns

**ObservabilityProvider Protocol (from Story 24.1):**
```python
# quilto/observability/provider.py
@runtime_checkable
class ObservabilityProvider(Protocol):
    def span(
        self,
        name: str,
        metadata: dict[str, Any] | None = None,
        input: Any | None = None,
    ) -> AbstractContextManager[SpanContext]:
        """Create a span for tracing an operation."""
        ...
```

**LangfuseProvider span usage (from Story 24.2):**
```python
with provider.span("operation_name", metadata={"key": "value"}, input=data):
    # Code to trace
    result = do_operation()
```

**Config and provider creation (from Story 24.3):**
```python
from quilto.config import load_config, create_observability_provider

config = load_config(Path("config.yaml"))
provider = create_observability_provider(config.observability)
```

### Current Orchestration Architecture

The orchestration graph is in `packages/quilto/quilto/orchestration.py`:

**Key Node Functions:**
- `route_node()` - Classifies input (LOG/QUERY/BOTH/CORRECTION)
- `retrieve_node()` - Calls `RetrieverAgent.retrieve()` which uses `storage.get_entries_by_date_range()`
- `parse_node()` - Calls `ParserAgent.parse()` then `storage.save_entry()` for LOG persistence
- `observe_node()` - Calls `ObserverAgent.observe()` with `GlobalContextManager.read_context()` and `apply_updates()`
- `correction_node()` - Calls `process_correction()` with storage operations

**State Access Pattern (Story 17.6 established):**
```python
quilto = _get_quilto(state, "node_name")  # Get Quilto instance from state
```

### Implementation Strategy

**Step 1: Get provider from Quilto instance**

Currently `Quilto` class doesn't have `observability_provider`. This will be added in Story 24.5. For now, make provider access optional:

```python
# In orchestration.py node functions
def _get_observability_provider(state: QuiltoState) -> ObservabilityProvider:
    """Get observability provider from state, falling back to NoOp."""
    quilto = state.get(StateKeys.QUILTO)
    if quilto is None:
        from quilto.observability.noop import NoOpProvider
        return NoOpProvider()

    # Story 24.5 will add this attribute to Quilto
    provider = getattr(quilto, 'observability_provider', None)
    if provider is None:
        from quilto.observability.noop import NoOpProvider
        return NoOpProvider()

    return provider
```

**Step 2: Wrap storage calls in spans**

Example for `retrieve_node`:
```python
async def retrieve_node(state: QuiltoState) -> dict[str, Any]:
    quilto = _get_quilto(state, "retrieve_node")
    provider = _get_observability_provider(state)

    # ... existing code ...

    # Wrap storage call in span
    with provider.span(
        "storage.get_entries_by_date_range",
        metadata={
            "start_date": str(start_date),
            "end_date": str(end_date),
        },
    ):
        entries = quilto.storage.get_entries_by_date_range(start_date, end_date)

    # ... rest of code ...
```

**Step 3: Ensure NoOpProvider works**

NoOpProvider's `span()` is already a no-op context manager that yields `SpanContext(span_id="", trace_id="")`. No special handling needed - just call `provider.span()` and it will work whether enabled or disabled.

### Storage Operations to Instrument

| Node | Method | Metadata |
|------|--------|----------|
| `retrieve_node` | `RetrieverAgent._execute_date_range()` (calls `storage.get_entries_by_date_range`) | `start_date`, `end_date`, `entries_found` |
| `parse_node` | `storage.save_entry()` | `entry_id`, `date`, `domains` |
| `observe_node` | `GlobalContextManager.read_context()` | `context_file_path` |
| `observe_node` | `GlobalContextManager.apply_updates()` | `updates_count` |
| `correction_node` | `storage.get_entries_by_date_range()` | `start_date`, `end_date` |
| `correction_node` | `process_correction()` (internal storage) | `target_entry_id` |

### Where to Instrument

**Option A: Instrument in orchestration.py nodes (RECOMMENDED)**
- Pros: Single place, easy to maintain, access to all context
- Cons: Storage calls are inside agent methods

**Option B: Instrument inside agent classes**
- Pros: Closer to actual storage calls
- Cons: Agents need provider injected, breaks current design

**Decision: Option A** - Instrument at the node level in `orchestration.py`. The storage calls visible in nodes are:
- `retrieve_node`: `retriever.retrieve()` internally calls storage
- `parse_node`: `quilto.storage.save_entry()` is called directly in node
- `observe_node`: `context_manager.read_context()` and `apply_updates()` called directly
- `correction_node`: `quilto.storage.get_entries_by_date_range()` called directly

For `RetrieverAgent._execute_date_range()`, we have two options:
1. Instrument the entire `retriever.retrieve()` call (captures all storage ops)
2. Instrument inside `RetrieverAgent` (requires injecting provider)

**Decision:** Instrument around the `retriever.retrieve()` call at the node level for now. The Retriever is deterministic (no LLM) so the entire retrieve operation is effectively a "tool call".

### Project Structure Notes

**Files to Modify:**
```
packages/quilto/quilto/orchestration.py  # Add spans around storage calls
```

**Files NOT to Modify (agents remain unchanged):**
```
packages/quilto/quilto/agents/retriever.py   # No changes needed
packages/quilto/quilto/agents/parser.py      # No changes needed
packages/quilto/quilto/agents/observer.py    # No changes needed
```

**Tests to Create:**
```
packages/quilto/tests/test_orchestration_observability.py  # Unit tests
packages/quilto/tests/observability/test_langfuse_integration.py  # Integration test (extend existing)
```

### Testing Requirements

**Unit Tests (NoOpProvider):**
```python
@pytest.mark.asyncio
async def test_retrieve_node_with_noop_provider():
    """Retrieve node works normally when observability disabled."""
    # Create state with NoOpProvider
    # Run retrieve_node
    # Assert entries returned correctly
    pass

@pytest.mark.asyncio
async def test_parse_node_with_noop_provider():
    """Parse node saves entry when observability disabled."""
    # Create state with NoOpProvider
    # Run parse_node
    # Assert entry saved to storage
    pass
```

**Langfuse Integration Test (REQUIRED):**
```python
@pytest.mark.integration
@pytest.mark.asyncio
async def test_tool_spans_in_langfuse(langfuse_provider, quilto_instance):
    """Tool calls create nested spans in Langfuse trace."""
    # 1. Process a QUERY via Quilto
    session = quilto_instance.create_session()
    result = await session.process("What did I eat yesterday?")

    # 2. Flush traces
    langfuse_provider.flush()

    # 3. Retrieve trace via API
    trace = langfuse.get_trace(trace_id)

    # 4. Assert tool span exists under Retriever span
    retriever_span = find_span(trace, "retriever")
    tool_span = find_child_span(retriever_span, "storage.get_entries_by_date_range")
    assert tool_span is not None
    assert "start_date" in tool_span.metadata
    assert "entries_found" in tool_span.metadata
```

### References

- [Source: _bmad-output/planning-artifacts/architecture.md#LLM Observability - Dual Integration Pattern]
- [Source: _bmad-output/planning-artifacts/epics.md#Story 24.4]
- [Source: packages/quilto/quilto/orchestration.py - Node functions]
- [Source: packages/quilto/quilto/observability/provider.py - ObservabilityProvider protocol]
- [Source: packages/quilto/quilto/observability/langfuse.py - LangfuseProvider.span() implementation]
- [Source: packages/quilto/quilto/observability/noop.py - NoOpProvider.span() no-op implementation]
- [Source: Story 24.1 - ObservabilityProvider protocol definition]
- [Source: Story 24.2 - LangfuseProvider implementation]
- [Source: Story 24.3 - Unified config loading and create_observability_provider]

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

None

### Completion Notes List

- Implemented `_get_observability_provider()` helper function with fallback to NoOpProvider
- Added `StateKeys.OBSERVABILITY` constant for state key management
- Instrumented `retrieve_node` with `storage.retrieve` span (wraps entire retriever.retrieve() call)
- Instrumented `parse_node` with `storage.save_entry` span (entry_id, date, domains metadata)
- Instrumented `observe_node` with `context_manager.read_context` and `context_manager.apply_updates` spans
- Instrumented `correction_node` with `storage.get_entries_by_date_range` and `process_correction` spans
- Created 14 unit tests in `test_orchestration_observability.py` - all pass
- Extended `test_langfuse_integration.py` with 4 new tests for tool span verification - all pass
- All 1477 tests pass with no regressions

### Code Review Fixes Applied (2026-01-30)

- **Issue #1**: Added missing `_observability_provider: Any` field to QuiltoState TypedDict
- **Issue #2**: Added `domains` metadata to retrieve_node span; added `log_event("retrieval_complete")` to capture `entries_found` after retrieval
- **Issue #3**: Added `raw_file_path` and `parsed_file_path` to parse_node span metadata (calculated inline to avoid protected method access)
- **Issue #4**: Fixed unit tests to avoid importing private `_get_observability_provider` - now uses test helper that mirrors the same logic
- **Issue #5**: Updated test metadata to match new implementation structure

### File List

- packages/quilto/quilto/orchestration.py (modified)
- packages/quilto/tests/test_orchestration_observability.py (created)
- packages/quilto/tests/observability/test_langfuse_integration.py (modified)

### Change Log

- 2026-01-30: Story 24.4 implementation complete - tool call instrumentation for Langfuse observability
- 2026-01-30: Code review fixes applied - AC#1/AC#2 metadata requirements, TypedDict field, test improvements

