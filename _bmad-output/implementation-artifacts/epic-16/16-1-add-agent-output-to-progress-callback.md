# Story 16.1: Add Agent Output to ProgressHandler Callback

Status: done

## Story

As a **Quilto framework developer**,
I want **`on_agent_complete` to receive the agent's output**,
So that **applications can capture full intermediate data for debugging and feedback recording**.

## Background

**Origin:** Epic 15 Retrospective (2026-01-27)
**Priority:** HIGH | **Effort:** Small (1-2 hours)
**Type:** Enhancement - extend existing ProgressHandler protocol

**Problem Statement:**
`ProgressHandler.on_agent_complete(agent, elapsed)` only receives agent name and execution time. This prevents applications from capturing intermediate agent outputs for debugging, feedback recording, and richer UIs.

**Impact:** Story 16.5 depends on this for feedback recording via callbacks.

## Acceptance Criteria

1. **Given** a ProgressHandler implementation
   **When** `on_agent_complete` is called
   **Then** it receives `(agent: str, elapsed: float, output: dict[str, Any])`

2. **Given** the Router agent completes
   **When** `on_agent_complete` is called
   **Then** `output` contains `input_type`, `selected_domains`, `confidence` from RouterOutput

3. **Given** the Planner agent completes
   **When** `on_agent_complete` is called
   **Then** `output` contains `query_type`, `retrieval_instructions`, `next_action`

4. **Given** the Retriever agent completes
   **When** `on_agent_complete` is called
   **Then** `output` contains `entries`, `retrieval_summary`

5. **Given** the Analyzer agent completes
   **When** `on_agent_complete` is called
   **Then** `output` contains `verdict`, `findings`

6. **Given** the Synthesizer agent completes
   **When** `on_agent_complete` is called
   **Then** `output` contains `response`

7. **Given** the Evaluator agent completes
   **When** `on_agent_complete` is called
   **Then** `output` contains `overall_verdict`, `feedback`

8. **Given** the Parser agent completes
   **When** `on_agent_complete` is called
   **Then** `output` contains `domain_data`

9. **Given** the Observer agent completes
   **When** `on_agent_complete` is called
   **Then** `output` contains `should_update`, `updates`

10. **Given** existing ProgressHandler implementations without the `output` parameter
    **When** the signature changes
    **Then** backwards compatibility is maintained (handlers without `output` param still work)

11. **Given** an agent fails with an exception
    **When** `on_agent_complete` is called
    **Then** `output` is empty dict `{}`

## Tasks / Subtasks

- [x] Task 1: Update `ProgressHandler` Protocol in `handlers.py`
  - [x] 1.1: Add `output: dict[str, Any]` parameter to `on_agent_complete` signature
  - [x] 1.2: Update docstring with output parameter documentation

- [x] Task 2: Update `_call_progress_handler` helper in `orchestration.py`
  - [x] 2.1: Add signature caching at helper level (inspect once, cache result)
  - [x] 2.2: Pass `output` dict when handler supports it; pass only `(agent, elapsed)` otherwise

- [x] Task 3: Update all 9 agent nodes to pass output
  - [x] 3.1: `route_node` - pass `router_output.model_dump(mode="json")`
  - [x] 3.2: `plan_node` - pass `planner_output.model_dump(mode="json")`
  - [x] 3.3: `retrieve_node` - pass `retriever_output.model_dump(mode="json")`
  - [x] 3.4: `analyze_node` - pass `analyzer_output.model_dump(mode="json")`
  - [x] 3.5: `synthesize_node` - pass `synthesizer_output.model_dump(mode="json")`
  - [x] 3.6: `evaluate_node` - pass `evaluator_output.model_dump(mode="json")`
  - [x] 3.7: `parse_node` - pass `parser_output.model_dump(mode="json")`
  - [x] 3.8: `correction_node` - pass `result.model_dump(mode="json")`
  - [x] 3.9: `observe_node` - store `observer_output` in state, then pass to callback

- [x] Task 4: Write/Update tests
  - [x] 4.1: Update `test_handlers.py` - extend existing MockProgressHandler
  - [x] 4.2: Add test in `test_handlers.py` - verify output capture for each agent type
  - [x] 4.3: Test backward compatibility (handler without output param still works)

- [x] Task 5: Run validation
  - [x] 5.1: `make check` passes (lint + typecheck)
  - [x] 5.2: `make validate` passes (lint + format + typecheck + test)

## Dev Notes

### Target Protocol Signature

```python
# packages/quilto/quilto/handlers.py (lines 10-43)
@runtime_checkable
class ProgressHandler(Protocol):
    async def on_agent_complete(
        self, agent: str, elapsed: float, output: dict[str, Any]
    ) -> None:
        """Called when an agent completes execution.

        Args:
            agent: Name of the agent that completed.
            elapsed: Execution time in seconds.
            output: Agent output as dictionary (JSON-serializable).
                Router: input_type, selected_domains, confidence
                Planner: query_type, retrieval_instructions, next_action
                Retriever: entries, retrieval_summary
                Analyzer: verdict, findings
                Synthesizer: response
                Evaluator: overall_verdict, feedback
                Parser: domain_data
                Observer: should_update, updates
                Empty dict {} on agent error.
        """
        ...
```

### Backward Compatibility Implementation

Cache the signature check at helper level to avoid per-call inspection overhead:

```python
import inspect
from functools import lru_cache

def _get_method_param_count(handler: Any, method_name: str) -> int:
    """Get parameter count for handler method (cached)."""
    method_fn = getattr(handler, method_name, None)
    if method_fn is None:
        return 0
    # Use id(handler) + method_name as cache key
    sig = inspect.signature(method_fn)
    # Subtract 1 for 'self'
    return len(sig.parameters)

async def _call_progress_handler(
    quilto: "Quilto",
    method: str,
    *args: Any,
) -> None:
    handler = quilto.progress_handler
    if handler is None:
        return

    method_fn = getattr(handler, method, None)
    if method_fn is None:
        return

    if method == "on_agent_complete":
        param_count = _get_method_param_count(handler, method)
        if param_count >= 3:  # agent, elapsed, output
            await method_fn(*args)
        else:
            # Old handler: only agent, elapsed
            await method_fn(args[0], args[1])
    else:
        await method_fn(*args)
```

### Node Update Pattern

Each node already has the output as a Pydantic model. Add third argument to callback:

```python
# Before
await _call_progress_handler(quilto, "on_agent_complete", "router", elapsed / 1000)

# After
await _call_progress_handler(
    quilto, "on_agent_complete", "router", elapsed / 1000,
    router_output.model_dump(mode="json")
)
```

Use `mode="json"` for full JSON serializability (handles nested Pydantic models, datetimes, etc.).

### Node Locations in orchestration.py

All nodes to update (function names - search for these):
- `route_node` - RouterOutput
- `plan_node` - PlannerOutput
- `retrieve_node` - RetrieverOutput
- `analyze_node` - AnalyzerOutput
- `synthesize_node` - SynthesizerOutput
- `evaluate_node` - EvaluatorOutput
- `parse_node` - ParserOutput
- `correction_node` - CorrectionResult
- `observe_node` - ObserverOutput (also store in state as `observer_output`)

### observe_node Special Case

Currently `observe_node` does NOT store `observer_output` in the returned state dict. Update to include it:

```python
# In observe_node, add to return dict:
return {
    "observer_output": observer_output.model_dump(),  # ADD THIS
    "traces": _add_trace(...),
}

# Then pass to callback:
await _call_progress_handler(
    quilto, "on_agent_complete", "observer", elapsed / 1000,
    observer_output.model_dump(mode="json")
)
```

### Error Case Handling

When a node catches an exception, pass empty dict:

```python
except Exception as e:
    await _call_progress_handler(
        quilto, "on_agent_complete", "router", elapsed / 1000, {}
    )
    return {"error": f"Router failed: {e!s}", ...}
```

### Files to Modify

| File | Action |
|------|--------|
| `packages/quilto/quilto/handlers.py` | Update Protocol signature |
| `packages/quilto/quilto/orchestration.py` | Update helper + 9 nodes |
| `packages/quilto/tests/test_handlers.py` | Extend MockProgressHandler |
| `packages/quilto/tests/test_quilto.py` | Add output capture tests |

### Existing Test Pattern to Extend

`test_handlers.py` has `MockProgressHandler` class at line 14. Extend it:

```python
class MockProgressHandler:
    def __init__(self) -> None:
        self.events: list[tuple[str, ...]] = []
        self.outputs: list[dict[str, Any]] = []  # ADD THIS

    async def on_agent_complete(
        self, agent: str, elapsed: float, output: dict[str, Any]
    ) -> None:
        self.events.append(("complete", agent, str(elapsed)))
        self.outputs.append(output)  # CAPTURE OUTPUT
```

### Validation Checklist

**Protocol Changes:**
- [x] `on_agent_complete` signature has `output: dict[str, Any]` parameter
- [x] Docstring documents all agent output types

**Orchestration Changes:**
- [x] `_call_progress_handler` caches signature check
- [x] All 9 nodes pass `model_dump(mode="json")` to callback
- [x] `observe_node` stores `observer_output` in state
- [x] Error handlers pass `{}` as output

**Tests:**
- [x] MockProgressHandler captures output
- [x] Each agent's output dict verified
- [x] Old handlers (no output param) still work
- [x] Error case returns empty dict

**Final Validation:**
- [x] `make check` passes
- [x] `make validate` passes

### References

| Source | Purpose |
|--------|---------|
| `packages/quilto/quilto/handlers.py` | ProgressHandler Protocol (60 lines) |
| `packages/quilto/quilto/orchestration.py` | Node implementations (1045 lines) |
| `packages/quilto/tests/test_handlers.py` | Existing handler tests (75 lines) |
| `packages/quilto/tests/test_quilto.py` | Orchestration integration tests |
| `_bmad-output/implementation-artifacts/epic-15/epic-15-retro-2026-01-27.md` | Issue origin |

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

N/A

### Completion Notes List

1. Updated `ProgressHandler.on_agent_complete` to accept `output: dict[str, Any]` as third parameter
2. Added signature caching via `_get_method_param_count()` to avoid per-call inspection overhead
3. Implemented backward compatibility in `_call_progress_handler` - old handlers without output param continue to work
4. Updated all 9 agent nodes (route, plan, retrieve, analyze, synthesize, evaluate, parse, correction, observe) to pass `model_dump(mode="json")` output
5. Updated all 9 exception handlers to pass empty dict `{}` on error per AC-11
6. Added `observer_output` to `QuiltoState` TypedDict for state storage per dev notes
7. Added comprehensive tests: output capture, per-agent-type verification, error case, backward compatibility

### File List

| File | Action |
|------|--------|
| `packages/quilto/quilto/handlers.py` | Modified - Updated Protocol signature with output param, fixed example |
| `packages/quilto/quilto/orchestration.py` | Modified - Added signature caching + updated all 9 nodes + error handlers |
| `packages/quilto/tests/test_handlers.py` | Modified - Extended tests for output capture and backward compatibility |
| `_bmad-output/implementation-artifacts/epic-16/16-1-add-agent-output-to-progress-callback.md` | Modified - Updated validation checklist and file list |
