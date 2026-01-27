# Story 15.4: Migrate Swealog to Use Quilto Public API

Status: backlog

## Story

As a **Swealog application developer**,
I want **to use Quilto's public API instead of manual agent wiring**,
So that **Swealog benefits from new Quilto features automatically**.

## Background

**Origin:** Quilto Public API Design Session (2026-01-27)
**Source:** `_bmad-output/planning-artifacts/quilto-api-design-session.md`
**Priority:** High | **Effort:** Medium (3-4 hours)
**Type:** Refactor - replace manual wiring with Quilto API

Current state:
- `swealog/api/routes/query.py` has ~400 lines manually orchestrating 6 agents
- Observer is never invoked (logs/logs/context/ is empty)
- New Quilto agents don't propagate to Swealog

After migration:
- Swealog uses `q = Quilto(...); session.process(...)`
- ~400 lines reduced to ~50 lines
- Observer runs automatically
- Future Quilto improvements flow to Swealog

## Acceptance Criteria

1. **Given** the Swealog FastAPI `/query` endpoint
   **When** a query is submitted
   **Then** it uses `Quilto.create_session().process()` internally

2. **Given** the Swealog CLI `auto` command
   **When** user input is processed
   **Then** it uses the same Quilto API

3. **Given** the migration is complete
   **When** `execute_query_pipeline()` is searched for
   **Then** it no longer exists in Swealog (moved to Quilto)

4. **Given** identical inputs before and after migration
   **When** processed through the system
   **Then** outputs are functionally equivalent (may differ in Observer effects)

5. **Given** a query processed after migration
   **When** Observer triggers are enabled
   **Then** `logs/logs/context/` receives updates

## Tasks / Subtasks

- [ ] Task 1: Create Quilto instance in Swealog
  - [ ] 1.1: Add `get_quilto()` dependency in `swealog/api/dependencies.py`
  - [ ] 1.2: Initialize Quilto with existing llm_client, storage, domains
  - [ ] 1.3: Configure ObserverTriggerConfig with sensible defaults

- [ ] Task 2: Update `/query` endpoint
  - [ ] 2.1: Replace `execute_query_pipeline()` call with `session.process()`
  - [ ] 2.2: Map `ProcessResult` to existing `QueryResponse` model
  - [ ] 2.3: Handle clarification_questions in response

- [ ] Task 3: Update CLI `auto` command
  - [ ] 3.1: Use Quilto session for processing
  - [ ] 3.2: Maintain session across interactive loop
  - [ ] 3.3: Update debug output to use ProcessResult.debug

- [ ] Task 4: Remove deprecated code from Swealog
  - [ ] 4.1: Delete `execute_query_pipeline()` function
  - [ ] 4.2: Delete `_DebugTimer` class
  - [ ] 4.3: Delete `_format_entries_summary()` function
  - [ ] 4.4: Delete `_calculate_confidence()` function
  - [ ] 4.5: Clean up unused imports

- [ ] Task 5: Update tests
  - [ ] 5.1: Update `/query` endpoint tests to expect same behavior
  - [ ] 5.2: Update CLI tests if any
  - [ ] 5.3: Verify existing eval tests still pass

- [ ] Task 6: Run validation
  - [ ] 6.1: Run `make check` (lint + typecheck)
  - [ ] 6.2: Run `make validate` (full validation)
  - [ ] 6.3: Run `make test-ollama` (integration tests)

## Dev Notes

### Before Migration (query.py ~400 lines)

```python
async def execute_query_pipeline(
    query: str,
    llm_client: LLMClient,
    storage: StorageRepository,
    domains: list[DomainModule],
    ...
) -> dict[str, Any]:
    # 300+ lines of manual agent wiring
    router_agent = RouterAgent(llm_client)
    planner = PlannerAgent(llm_client)
    # ... etc
```

### After Migration (query.py ~50 lines)

```python
from quilto import Quilto

@router.post("/query", response_model=QueryResponse)
async def process_query(
    request: QueryRequest,
    quilto: Annotated[Quilto, Depends(get_quilto)],
) -> QueryResponse:
    session = quilto.create_session()
    result = await session.process(request.text)

    return QueryResponse(
        response=result.response or "",
        sources=result.source_entry_ids,
        confidence=result.confidence or 0.0,
        partial=result.response is None,
    )
```

### File Locations

| File | Action |
|------|--------|
| `packages/swealog/swealog/api/dependencies.py` | UPDATE - add get_quilto() |
| `packages/swealog/swealog/api/routes/query.py` | MAJOR REFACTOR - remove ~350 lines |
| `packages/swealog/swealog/cli/auto_cmd.py` | UPDATE - use Quilto session |
| `packages/swealog/tests/test_query.py` | UPDATE - verify behavior unchanged |

### Dependency Injection

```python
# swealog/api/dependencies.py

_quilto: Quilto | None = None

def get_quilto(
    llm_client: Annotated[LLMClient, Depends(get_llm_client)],
    storage: Annotated[StorageRepository, Depends(get_storage)],
    domains: Annotated[list[DomainModule], Depends(get_domains)],
) -> Quilto:
    global _quilto
    if _quilto is None:
        _quilto = Quilto(
            llm_client=llm_client,
            storage=storage,
            domains=domains,
            observer=ObserverTriggerConfig(
                enable_post_query=True,
                enable_user_correction=True,
                enable_significant_log=True,
            ),
        )
    return _quilto
```

## Test Strategy

- Run existing eval suite to verify no regression
- Manual test: Check logs/logs/context/ gets populated after queries
- Compare response quality before/after (should be identical except Observer effects)
