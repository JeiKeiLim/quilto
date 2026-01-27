# Story 15.4: Migrate Swealog to Use Quilto Public API

Status: done

## Story

As a **Swealog application developer**,
I want **to use Quilto's public API instead of manual agent wiring**,
So that **Swealog benefits from new Quilto features automatically**.

## Background

**Origin:** Quilto Public API Design Session (2026-01-26)
**Source:** `_bmad-output/planning-artifacts/quilto-api-design-session.md`
**Priority:** High | **Effort:** Medium (3-4 hours)
**Type:** Refactor - replace manual wiring with framework API
**Depends On:** Story 15.3 (Quilto class with LangGraph orchestration)

**Problem Statement:**
- Swealog manually wires 6 agents (~400 lines in `swealog/api/routes/query.py`)
- `execute_query_pipeline()` duplicates orchestration logic now in Quilto
- CLI commands (`auto`, `ask`) also use `execute_query_pipeline()` directly
- Observer infrastructure exists but is NEVER invoked (fixed in Quilto 15.3)

**Solution:**
- Replace `execute_query_pipeline()` calls with `Quilto.create_session().process()`
- Remove ~400 lines of manual orchestration code from Swealog
- Leverage new Quilto API for automatic Observer integration
- Existing behavior remains functionally equivalent

**Key Design Decision:** The migration must preserve existing behavior while enabling Observer triggers. The `session.process()` auto-detects input type via Router (same as before), but now runs through LangGraph with built-in Observer invocation.

## Acceptance Criteria

1. **Given** the Swealog FastAPI `/query` endpoint
   **When** a query is submitted
   **Then** it uses `Quilto.create_session().process()` internally

2. **Given** the Swealog CLI `auto` command
   **When** user input is processed (QUERY or BOTH type)
   **Then** it uses the same Quilto API for query processing

3. **Given** the Swealog CLI `ask` command
   **When** a query is submitted
   **Then** it uses `Quilto.create_session().process(mode="query")`

4. **Given** the migration is complete
   **When** `execute_query_pipeline()` is searched for
   **Then** it no longer exists in Swealog (moved to Quilto)

5. **Given** identical inputs before and after migration
   **When** processed through the system
   **Then** outputs are functionally equivalent (same response structure)

6. **Given** a QUERY type input via CLI or API
   **When** processed through Quilto
   **Then** Observer is invoked (verified in Story 15.5)

7. **Given** a BOTH type input via CLI
   **When** processed through the system
   **Then** query flow runs through Quilto, LOG flow uses existing `execute_log_flow()` (LOG flow is Swealog-specific)

## Tasks / Subtasks

- [x] Task 1: Update FastAPI `/query` endpoint (AC: #1, #4, #5)
  - [x] 1.1: Add `Quilto` import to `swealog/api/routes/query.py`
  - [x] 1.2: Create shared Quilto instance via dependency injection (or create per-request)
  - [x] 1.3: Replace `execute_query_pipeline()` call with `session.process(mode="query")`
  - [x] 1.4: Map `ProcessResult` to existing `QueryResponse` model for backwards compatibility
  - [x] 1.5: Handle clarification questions (return special response or HTTP status)
  - [x] 1.6: Remove `execute_query_pipeline()` function and related imports
  - [x] 1.7: Remove `_DebugTimer`, `_calculate_confidence`, `_format_entries_summary` helpers

- [x] Task 2: Update CLI `ask` command (AC: #3, #5)
  - [x] 2.1: Add `Quilto` import to `swealog/cli/ask_cmd.py`
  - [x] 2.2: Replace `execute_query_pipeline()` call with `session.process(mode="query")`
  - [x] 2.3: Map `ProcessResult` fields to existing display logic
  - [x] 2.4: Update import statements (remove `execute_query_pipeline` import)

- [x] Task 3: Update CLI `auto` command for QUERY/BOTH flows (AC: #2, #7)
  - [x] 3.1: Add `Quilto` import to `swealog/cli/auto_cmd.py`
  - [x] 3.2: Replace QUERY flow `execute_query_pipeline()` with Quilto `session.process(mode="query")`
  - [x] 3.3: Replace BOTH flow query portion with Quilto `session.process(mode="query")`
  - [x] 3.4: Keep existing Router call for input_type classification (Router runs BEFORE Quilto to determine CLI display)
  - [x] 3.5: Keep existing LOG/CORRECTION flow using `execute_log_flow()` (LOG flow is Swealog-specific, NOT in Quilto scope)
  - [x] 3.6: Simplify feedback recording to work with ProcessResult traces (see Dev Notes)

- [x] Task 4: Create Quilto dependency provider (AC: #1, #2, #3)
  - [x] 4.1: Add `from quilto import Quilto` import to `swealog/api/dependencies.py`
  - [x] 4.2: Create `get_quilto()` dependency that builds Quilto with correct domains
  - [x] 4.3: Use `session_db_path=":memory:"` for stateless per-request (matches current behavior)
  - [x] 4.4: Configure ObserverTriggerConfig with enable_post_query=True

- [x] Task 5: Handle clarification questions (AC: #1, #5)
  - [x] 5.1: In `/query` endpoint, check `result.clarification_questions`
  - [x] 5.2: If present, return modified response (empty response + questions in message field)
  - [x] 5.3: Consider adding `clarification_questions` field to `QueryResponse` model (optional)

- [x] Task 6: Update feedback recording in CLI (AC: #2)
  - [x] 6.1: Adapt `_record_feedback()` to work with `ProcessResult` instead of full intermediate outputs
  - [x] 6.2: Create simplified `SimplifiedFeedbackRecord` schema that stores ProcessResult.debug.traces
  - [x] 6.3: Keep existing `FeedbackRecord` schema but make `intermediate_outputs` optional or create alternative

- [x] Task 7: Clean up removed code (AC: #4)
  - [x] 7.1: Remove `execute_query_pipeline()` from `query.py`
  - [x] 7.2: Remove helper functions: `_DebugTimer`, `_calculate_confidence`, `_format_entries_summary`
  - [x] 7.3: Remove unused imports from all modified files
  - [x] 7.4: Verify no other code references `execute_query_pipeline` using grep

- [x] Task 8: Write tests (AC: all)
  - [x] 8.1: Test `/query` endpoint returns same response structure (QueryResponse unchanged)
  - [x] 8.2: Test CLI `ask` command output format unchanged
  - [x] 8.3: Test CLI `auto` command for QUERY type
  - [x] 8.4: Test CLI `auto` command for BOTH type (log + query)
  - [x] 8.5: Test clarification question handling
  - [x] 8.6: Test backwards compatibility - API consumers receive identical JSON structure

- [x] Task 9: Run validation
  - [x] 9.1: `make check` passes (lint + typecheck)
  - [x] 9.2: `make validate` passes (lint + format + typecheck + test)

## Dev Notes

### ProcessResult → QueryResponse Mapping

| ProcessResult Field | QueryResponse Field | Notes |
|---------------------|---------------------|-------|
| `response` | `response` | Use `result.response or ""` (response is Optional) |
| `source_entry_ids` | `sources` | Direct mapping |
| `confidence` | `confidence` | Use `result.confidence or 0.0` (confidence is Optional) |
| `state["is_partial"]` | `partial` | **NOT in ProcessResult** - extract from orchestration state |
| `clarification_questions` | (new field or special handling) | See Task 5 |

### Determining `partial` Flag

The `is_partial` flag is set in Quilto orchestration state (Story 15.3, `check_both_node`) when max_retries reached. However, **ProcessResult does NOT have an is_partial field**.

**Solution:** Modify `Session._build_process_result()` in Story 15.3 to include `is_partial` from state, OR add logic in Swealog to infer it:
```python
# In /query endpoint after getting ProcessResult:
is_partial = (result.confidence or 0) < 0.5  # Heuristic
# OR better: Check if Quilto debug has retry_count >= max_retries
is_partial = result.debug and result.debug.retry_count >= 2
```

**Recommended:** Add `is_partial: bool = False` to ProcessResult in a follow-up or modify Session._build_process_result() to read from state.

### BOTH Flow Strategy - IMPORTANT

**Current CLI behavior (auto_cmd.py):** LOG flow first, then QUERY flow
**Quilto BOTH flow (Story 15.3):** Query flow first, then parse

**These are DIFFERENT.** For this migration:
- Keep CLI BOTH behavior unchanged: LOG → QUERY
- Use `execute_log_flow()` for LOG portion (Swealog-specific)
- Use `session.process(mode="query")` for QUERY portion (via Quilto)

Do NOT use `session.process(mode="auto")` for BOTH inputs - it would run Quilto's BOTH flow which is query-first.

### LOG and CORRECTION Flows - Keep Existing

The LOG flow uses `execute_log_flow()` from `flows.py` which:
1. Calls ParserAgent directly
2. Creates Swealog-specific Entry model
3. Saves to StorageRepository with Swealog directory structure

This is **NOT migrating to Quilto** because:
- Quilto's `process(mode="log")` runs Parser but returns `parsed_data` only
- Swealog's LOG flow creates/saves entries in a Swealog-specific way
- Entry creation is application-specific, not framework-specific

**CORRECTION flow:** Also keep using `execute_log_flow(is_correction=True)`. Quilto's CORRECTION flow uses `process_correction()` which has different semantics.

### Feedback Recording Adaptation

Current `IntermediateOutputs` requires full agent output dicts:
```python
class IntermediateOutputs(BaseModel):
    router: dict[str, Any]
    planner: dict[str, Any]
    retriever: dict[str, Any]
    analyzer: dict[str, Any]
    synthesizer: dict[str, Any]
    evaluator: dict[str, Any]
```

ProcessResult only provides `debug.traces` with summaries:
```python
result.debug.traces  # List[AgentTrace] with input_summary, output_summary strings
```

**Options:**
1. **Simplify feedback schema** - Create `TraceFeedbackRecord` that stores traces instead of full outputs
2. **Make intermediate_outputs optional** - Allow feedback without full outputs
3. **Enhance ProcessResult** - Add raw outputs to debug (would require Quilto changes)

**Recommended:** Option 1 - Create simplified schema:
```python
class SimplifiedFeedbackRecord(BaseModel):
    id: str
    query: str
    traces: list[dict[str, Any]]  # From ProcessResult.debug.traces
    final_response: str
    user_feedback: str
    session: SessionMetadata
```

### Target Code Structure

**API Query Endpoint** (~50 lines):
```python
from quilto import Quilto
from quilto.state import ObserverTriggerConfig
from swealog.api.dependencies import get_domains, get_llm_client, get_storage

def get_quilto(
    llm_client: Annotated[LLMClient, Depends(get_llm_client)],
    storage: Annotated[StorageRepository, Depends(get_storage)],
    domains: Annotated[list[DomainModule], Depends(get_domains)],
) -> Quilto:
    return Quilto(
        llm_client=llm_client,
        storage=storage,
        domains=domains,
        observer_config=ObserverTriggerConfig(post_query=True),
        session_db_path=":memory:",  # Stateless per-request
    )

@router.post("/query", response_model=QueryResponse)
async def process_query(
    request: QueryRequest,
    quilto: Annotated[Quilto, Depends(get_quilto)],
) -> QueryResponse:
    session = quilto.create_session()
    result = await session.process(request.text, mode="query")

    # Handle clarification
    if result.clarification_questions:
        return QueryResponse(
            response="",
            sources=[],
            confidence=0.0,
            partial=False,
            # Future: add clarification_questions field
        )

    # Map ProcessResult to QueryResponse
    is_partial = result.debug and result.debug.retry_count >= 2 if result.debug else False
    return QueryResponse(
        response=result.response or "",
        sources=result.source_entry_ids,
        confidence=result.confidence or 0.0,
        partial=is_partial,
    )
```

**CLI Ask Command**:
```python
from quilto import Quilto

async def ask(...) -> None:
    llm_client, storage, domains = get_dependencies(config, storage_path)
    quilto = Quilto(
        llm_client=llm_client,
        storage=storage,
        domains=domains,
        debug=debug,
        session_db_path=":memory:",
    )
    session = quilto.create_session()
    result = await session.process(query, mode="query")

    # Map to existing display
    is_partial = result.debug and result.debug.retry_count >= 2 if result.debug else False
    if is_partial:
        print_warning("Partial response...")
    if result.response:
        print_panel(result.response, title="Response")
    # ...
```

**CLI Auto Command** (QUERY portion only - LOG stays as-is):
```python
elif input_type == "QUERY":
    quilto = Quilto(
        llm_client=llm_client,
        storage=storage,
        domains=domains,
        debug=debug,
        session_db_path=":memory:",
    )
    session = quilto.create_session()
    result = await session.process(text, mode="query")

    # Handle clarification
    if result.clarification_questions:
        _handle_clarification_from_process_result(result)
        return

    _display_query_result_from_process_result(result)

elif input_type == "BOTH":
    # LOG portion - keep existing (Swealog-specific)
    entry_id = await execute_log_flow(...)
    print_success(f"Logged entry: {entry_id}")

    # QUERY portion - use Quilto
    quilto = Quilto(...)
    session = quilto.create_session()
    result = await session.process(router_output.query_portion or text, mode="query")
    _display_query_result_from_process_result(result)
```

### Files to Modify

| File | Action | Purpose |
|------|--------|---------|
| `packages/swealog/swealog/api/routes/query.py` | MAJOR UPDATE | Use Quilto, remove execute_query_pipeline |
| `packages/swealog/swealog/api/dependencies.py` | UPDATE | Add get_quilto dependency, add Quilto import |
| `packages/swealog/swealog/cli/ask_cmd.py` | UPDATE | Use Quilto instead of execute_query_pipeline |
| `packages/swealog/swealog/cli/auto_cmd.py` | UPDATE | Use Quilto for QUERY/BOTH query flow only |
| `packages/swealog/swealog/cli/feedback.py` | UPDATE | Adapt to work with ProcessResult traces |
| `packages/swealog/swealog/api/models.py` | OPTIONAL | Add clarification_questions to QueryResponse |

### Files to Keep Unchanged

| File | Reason |
|------|--------|
| `packages/swealog/swealog/cli/flows.py` | LOG flow is Swealog-specific, not migrating |
| `packages/swealog/swealog/cli/log_cmd.py` | Uses flows.py, not execute_query_pipeline |
| `packages/swealog/swealog/cli/debug.py` | CLI debug utilities still useful for Router timing |

### Common Mistakes to Avoid

| Mistake | Correct Pattern | Source |
|---------|-----------------|--------|
| Migrating LOG flow to Quilto | Keep existing `execute_log_flow()` - Swealog-specific entry creation | flows.py |
| Migrating CORRECTION flow to Quilto | Keep `execute_log_flow(is_correction=True)` - different semantics | flows.py |
| Using `mode="auto"` for BOTH inputs | Use `mode="query"` for query portion only - LOG handled separately | BOTH flow design |
| Not handling clarification questions | Check `result.clarification_questions` and handle appropriately | ProcessResult |
| Forgetting `mode="query"` | Use `mode="query"` for ask command and API to skip Router overhead | session.process() |
| Using persistent DB for CLI | Use `session_db_path=":memory:"` for stateless CLI commands | Session pattern |
| Breaking feedback recording | Create simplified schema or make intermediate_outputs optional | feedback.py |
| Not removing old imports | Clean up unused imports after removing execute_query_pipeline | Code hygiene |
| Returning None for response | Use `result.response or ""` to handle None case | ProcessResult.response is Optional |
| Expecting intermediate_outputs | ProcessResult.debug.traces has summaries, not full outputs | ProcessResult |
| Missing Quilto import in dependencies | Add `from quilto import Quilto` to dependencies.py | Task 4.1 |
| Assuming is_partial in ProcessResult | ProcessResult lacks is_partial - infer from retry_count or confidence | Story 15.3 |

### Error Handling

Quilto orchestration may raise:
- `RuntimeError`: Session not connected to Quilto
- Agent-specific exceptions wrapped in state["error"]

In `/query` endpoint:
```python
try:
    result = await session.process(...)
except RuntimeError as e:
    raise HTTPException(status_code=500, detail=f"Session error: {e}") from e
except Exception as e:
    logger.exception("Query processing failed: %s", e)
    raise HTTPException(status_code=500, detail=f"Internal error: {type(e).__name__}") from e
```

### Dependencies

- `quilto` package (already installed, workspace dependency)
- Story 15.3 complete (Quilto class available with session.process())
- Verify exports: `from quilto import Quilto, LLMClient, StorageRepository, DomainModule`

### Validation Checklist (Run Before Marking Done)

**Functionality:**
- [ ] `/query` endpoint returns same response structure (QueryResponse)
- [ ] CLI `ask` command works with same output format
- [ ] CLI `auto` command QUERY flow works
- [ ] CLI `auto` command BOTH flow works (LOG + QUERY)
- [ ] Clarification questions handled (if encountered)
- [ ] Feedback recording still works in debug mode (adapted schema)

**Code Quality:**
- [ ] `execute_query_pipeline()` removed from Swealog
- [ ] No unused imports remain
- [ ] All public functions have docstrings
- [ ] Type hints complete

**Backwards Compatibility:**
- [ ] QueryResponse JSON structure unchanged
- [ ] API consumers receive identical response format

**Final Validation:**
- [ ] `make check` passes (lint + typecheck)
- [ ] `make validate` passes (lint + format + typecheck + test)

### References

| Source | Content |
|--------|---------|
| `_bmad-output/planning-artifacts/quilto-api-design-session.md` | Full API design decisions |
| `_bmad-output/planning-artifacts/architecture.md#Quilto Public API` | Architecture documentation |
| `packages/quilto/quilto/quilto.py` | Quilto class implementation (from 15.3) |
| `packages/quilto/quilto/session/session.py` | Session.process() method |
| `packages/quilto/quilto/models.py` | ProcessResult, ClarificationQuestion models |
| `packages/swealog/swealog/api/routes/query.py` | Current ~400 line implementation to replace |
| `packages/swealog/swealog/cli/auto_cmd.py` | CLI auto command using execute_query_pipeline |
| `packages/swealog/swealog/cli/ask_cmd.py` | CLI ask command using execute_query_pipeline |
| `packages/swealog/swealog/cli/feedback.py` | Feedback recording schema to adapt |
| `_bmad-output/project-context.md` | Validation rules and common mistakes |
| `_bmad-output/implementation-artifacts/epic-15/15-3-implement-quilto-class.md` | Previous story learnings |

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

N/A

### Completion Notes List

1. **Task 4**: Created `get_quilto()` dependency in `dependencies.py` that builds a Quilto instance with correct domains, in-memory session storage, and `ObserverTriggerConfig(enable_post_query=True)`.

2. **Task 1**: Completely rewrote `/query` endpoint to use Quilto instead of `execute_query_pipeline()`. The endpoint now:
   - Builds Quilto via `get_quilto()` dependency
   - Calls `session.process(request.text, mode="query")`
   - Maps ProcessResult to QueryResponse with backwards-compatible structure
   - Handles clarification questions by returning them in the response field
   - Determines `partial` flag from `result.debug.retry_count >= 2`

3. **Task 2**: Updated CLI `ask` command to use Quilto directly instead of `execute_query_pipeline()`. Added clarification question handling and display of debug traces when `--debug` enabled.

4. **Task 3**: Updated CLI `auto` command QUERY and BOTH flows to use Quilto for query processing. LOG and CORRECTION flows remain unchanged (use `execute_log_flow()` which is Swealog-specific).

5. **Task 5**: Clarification handling implemented in both `/query` endpoint (returns message with questions) and CLI commands (displays questions with prompt to re-query).

6. **Task 6**: Created `SimplifiedFeedbackRecord` model and `record_simplified()` method in `FeedbackRecorder` to work with ProcessResult traces instead of full intermediate outputs.

7. **Task 7**: Removed `execute_query_pipeline()` and all helper functions (`_DebugTimer`, `_calculate_confidence`, `_format_entries_summary`). Updated all tests that referenced the removed function.

8. **Task 8**: Updated tests in `test_api_routes.py`, `test_cli_ask.py`, `test_cli_auto.py`, and `test_cli_debug.py` to mock Quilto instead of `execute_query_pipeline()`.

9. **Task 9**: All 2010 tests pass. `make validate` passes (lint + format + typecheck + test).

### File List

| File | Action |
|------|--------|
| `packages/swealog/swealog/api/dependencies.py` | MODIFIED - Added Quilto imports, created `get_quilto()` dependency |
| `packages/swealog/swealog/api/routes/query.py` | MAJOR REWRITE - Replaced ~400 lines with ~50 lines using Quilto |
| `packages/swealog/swealog/cli/ask_cmd.py` | MODIFIED - Use Quilto instead of `execute_query_pipeline()` |
| `packages/swealog/swealog/cli/auto_cmd.py` | MODIFIED - Use Quilto for QUERY/BOTH flows, added `_record_simplified_feedback()` |
| `packages/swealog/swealog/cli/feedback.py` | MODIFIED - Added `SimplifiedFeedbackRecord` and `record_simplified()` |
| `packages/swealog/tests/test_api_routes.py` | MODIFIED - Updated tests to mock Quilto |
| `packages/swealog/tests/test_cli_ask.py` | MODIFIED - Updated tests to mock Quilto |
| `packages/swealog/tests/test_cli_auto.py` | MODIFIED - Updated tests to mock Quilto |
| `packages/swealog/tests/test_cli_debug.py` | MODIFIED - Updated tests to mock Quilto, removed `_DebugTimer` tests |

