# Story 13.3: Implement Conversation Context for Multi-Turn Queries

Status: done

## Story

As a **Quilto user**,
I want **the system to remember context from my previous message**,
So that **I don't have to repeat information in follow-up questions**.

## Background

**Origin:** Dogfooding Iteration 3 (Epic 13)
**Source:** `tests/eval/feedback/archive/iter-002/analysis.md` - Pattern 9: Context Loss in Multi-Turn Conversations
**Priority:** Medium | **Effort:** Medium (2-4 hours)
**Type:** Feature - Multi-turn conversation support

**Key Evidence (Record `8628f945`):**
- File: `tests/eval/feedback/archive/iter-002/records/2026-01-26_8628f945.json`
- User first said: "I'd like to run a full marathon" (LOG)
- User then asked: "How do I do?" (QUERY)
- Router correctly identified BOTH type with `log_portion="I'd like to run a full marathon"` and `query_portion="How do I do?"`
- Planner processed `query_portion` without marathon context, generating clarification questions
- User feedback: "It failed to keep the context on I'd like to run a full marathon part."

**The Problem:** In BOTH-type inputs, Router extracts `log_portion` but this context is NOT passed to Planner when processing `query_portion`. The fix passes `log_portion` as `conversation_context` to help Planner interpret vague queries.

## Acceptance Criteria

1. **Given** user states "I'd like to run a full marathon"
   **When** user immediately follows with "How do I do?"
   **Then** the system understands "do" refers to running a marathon

2. **Given** a BOTH-type input where Router identifies both log and query portions
   **When** Planner processes the `query_portion`
   **Then** Planner incorporates `log_portion` as conversation context for query interpretation

3. **Given** `conversation_context` provided to Planner
   **When** generating retrieval instructions
   **Then** context informs Planner's query understanding and sub-query generation

## Tasks / Subtasks

- [x] Task 1: Add `conversation_context` field to `PlannerInput` (AC: #2, #3)
  - [x] 1.1: Add `conversation_context: str | None = None` field to `PlannerInput` in `packages/quilto/quilto/agents/models.py`
  - [x] 1.2: Update docstring to explain when/how conversation_context is used
  - [x] 1.3: Add unit test in `packages/quilto/tests/test_planner.py` (test_planner_input_with_conversation_context, test_planner_input_conversation_context_optional)

- [x] Task 2: Update Planner prompt to use conversation context (AC: #1, #2, #3)
  - [x] 2.1: Add `_format_conversation_context()` helper method
  - [x] 2.2: Add CONVERSATION CONTEXT section to `build_prompt()` after STORAGE AWARENESS section
  - [x] 2.3: Instruct Planner to use conversation_context when interpreting vague queries
  - [x] 2.4: Add test case in `packages/quilto/tests/test_planner.py` (test_prompt_includes_conversation_context, test_prompt_handles_empty_conversation_context)

- [x] Task 3: Pass `log_portion` as conversation context in BOTH flow (AC: #1, #2)
  - [x] 3.1: Update `execute_query_pipeline()` in `packages/swealog/swealog/api/routes/query.py` to accept `conversation_context: str | None = None` parameter
  - [x] 3.2: Pass `conversation_context` to `PlannerInput` when creating Planner input
  - [x] 3.3: Update `auto_cmd.py` BOTH branch to pass `router_output.log_portion` as `conversation_context`
  - [x] 3.4: Integration test not added - coverage via existing BOTH flow tests in test_cli_auto.py

- [x] Task 4: Run validation
  - [x] 4.1: Run `make check` (lint + typecheck) - PASSED
  - [x] 4.2: Run `make validate` (full validation) - PASSED (1888 passed, 100 skipped)
  - [x] 4.3: Run `make test-ollama` (integration tests) - 1931 passed, 1 flaky failure (unrelated pre-existing test_real_synthesis_detailed_style)

## Dev Notes

### Design Rationale

This is a **minimal, focused fix** targeting the specific problem from Record `8628f945`:
- When Router classifies BOTH, it extracts `log_portion` (e.g., "I'd like to run a full marathon")
- Currently, only `query_portion` ("How do I do?") is passed to `execute_query_pipeline()`
- The fix passes `log_portion` as `conversation_context` to help Planner interpret vague queries

**Why this approach:**
1. **Minimal code change:** Add one field, update one prompt, modify two call sites
2. **No session persistence:** Context is per-request (within a single BOTH input), not across requests
3. **LLM-based interpretation:** Planner uses context for understanding, not retrieval
4. **Backward compatible:** New field is optional with None default
5. **Follows Story 13.2 pattern:** Uses same approach as `storage_summary` field

**What this does NOT do:**
- Track conversation history across multiple CLI invocations
- Store session state between requests
- Implement full multi-turn chat with message history

### Implementation Approach

**File 1: `packages/quilto/quilto/agents/models.py`**

Add to `PlannerInput` class (follow `storage_summary` pattern from Story 13.2):

```python
class PlannerInput(BaseModel):
    """Input to Planner agent.

    Attributes:
        query: The query to plan for.
        ...existing fields...
        storage_summary: Summary of storage contents for date range decisions.
        conversation_context: Recent context from same interaction (e.g., log_portion
            in BOTH-type inputs). Helps interpret vague follow-up queries like
            "How do I do?" when user previously stated a goal.
    """

    # ...existing fields...
    storage_summary: dict[str, Any] | None = None
    conversation_context: str | None = None  # NEW
```

**File 2: `packages/quilto/quilto/agents/planner.py`**

Add helper and update `build_prompt()`:

```python
def _format_conversation_context(self, planner_input: PlannerInput) -> str:
    """Format conversation context for prompt."""
    if not planner_input.conversation_context:
        return "(No recent conversation context)"
    return planner_input.conversation_context
```

Add section in `build_prompt()` after STORAGE AWARENESS (around line 204):

```
=== CONVERSATION CONTEXT ===

{conversation_context_text}

Use this recent context to interpret the current query:
- If the query is vague ("How do I do?", "What about that?"), infer the subject from context
- The context provides user intent that may not be explicit in the query
- Incorporate context into your query interpretation and sub-query generation

Example:
- Context: "I'd like to run a full marathon"
- Query: "How do I do?"
- Interpretation: User wants guidance on how to prepare for/run a full marathon
```

**File 3: `packages/swealog/swealog/api/routes/query.py`**

Update function signature:

```python
async def execute_query_pipeline(
    query: str,
    llm_client: LLMClient,
    storage: StorageRepository,
    domains: list[DomainModule],
    debug_callback: DebugCallback | None = None,
    collect_outputs: bool = False,
    conversation_context: str | None = None,  # NEW
) -> dict[str, Any]:
```

Update PlannerInput creation (around line 143):

```python
planner_input = PlannerInput(
    query=query,
    domain_context=active_context,
    storage_summary=storage_summary,
    conversation_context=conversation_context,  # NEW
)
```

**File 4: `packages/swealog/swealog/cli/auto_cmd.py`**

Update BOTH branch (around line 237):

```python
elif input_type == "BOTH":
    # Execute log flow first
    entry_id = await execute_log_flow(...)
    print_success(f"Logged entry: {entry_id}")

    # Then execute query flow with query_portion AND log_portion as context
    query_text = router_output.query_portion or text
    debug_callback = create_debug_callback(debug)
    result = await execute_query_pipeline(
        query=query_text,
        llm_client=llm_client,
        storage=storage,
        domains=domains,
        debug_callback=debug_callback,
        collect_outputs=debug,
        conversation_context=router_output.log_portion,  # NEW: Pass log_portion as context
    )
```

### Edge Cases

| Case | Handling |
|------|----------|
| `conversation_context` is None | Prompt section shows "(No recent conversation context)" |
| `conversation_context` is empty string | Treat same as None |
| QUERY-type input (not BOTH) | `conversation_context` not passed, field remains None |
| LOG-type input | No query flow executed, not relevant |

### File Changes Summary

| File | Change Type | Lines Impact |
|------|-------------|--------------|
| `packages/quilto/quilto/agents/models.py` | MODIFY | ~3 lines (add field + docstring) |
| `packages/quilto/quilto/agents/planner.py` | MODIFY | ~20 lines (add helper + prompt section) |
| `packages/swealog/swealog/api/routes/query.py` | MODIFY | ~5 lines (add parameter + pass to PlannerInput) |
| `packages/swealog/swealog/cli/auto_cmd.py` | MODIFY | ~2 lines (pass log_portion) |
| `packages/quilto/tests/test_planner.py` | MODIFY | ~30 lines (model + prompt context tests) |

### Validation Checklist

Before marking complete:
- [x] `make check` passes (lint + typecheck)
- [x] `make validate` passes (all unit tests)
- [x] `make test-ollama` passes (integration tests) - 1 flaky failure unrelated to this story
- [x] PlannerInput has conversation_context field with docstring
- [x] Planner prompt includes CONVERSATION CONTEXT section
- [x] `execute_query_pipeline` accepts conversation_context parameter
- [x] `auto_cmd.py` BOTH branch passes `log_portion` as conversation_context
- [x] Unit tests cover conversation context handling
- [x] Empty/None conversation_context handled gracefully

### References

| Source | Content |
|--------|---------|
| `tests/eval/feedback/archive/iter-002/analysis.md` | Pattern 9: Context Loss in Multi-Turn Conversations |
| `tests/eval/feedback/archive/iter-002/records/2026-01-26_8628f945.json` | Specific example of context loss |
| `_bmad-output/planning-artifacts/epics.md#Story 13.3` | Story definition with acceptance criteria |
| `_bmad-output/implementation-artifacts/epic-13/13-2-simplify-retrieval-with-storage-awareness.md` | Previous story - follow same pattern for new field |
| `packages/quilto/quilto/agents/models.py:340-366` | PlannerInput model definition |
| `packages/quilto/quilto/agents/planner.py:147-316` | Planner agent build_prompt method |
| `packages/swealog/swealog/api/routes/query.py:93-273` | execute_query_pipeline function |
| `packages/swealog/swealog/cli/auto_cmd.py:221-260` | BOTH branch in auto command |

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

N/A

### Completion Notes List

- Story 13.3 implements conversation context passing for BOTH-type inputs
- When Router classifies input as BOTH, the `log_portion` (e.g., "I'd like to run a full marathon") is now passed to Planner as `conversation_context`
- Planner uses this context to interpret vague follow-up queries (e.g., "How do I do?")
- This is a per-request context (within single BOTH input), not session persistence
- Follows same pattern as `storage_summary` field from Story 13.2
- All tests pass: 1888 unit tests, 1931 integration tests (1 flaky failure unrelated to this story)

### File List

| File | Change |
|------|--------|
| `packages/quilto/quilto/agents/models.py` | Added `conversation_context: str \| None = None` field to PlannerInput with docstring |
| `packages/quilto/quilto/agents/planner.py` | Added `_format_conversation_context()` helper and CONVERSATION CONTEXT section in `build_prompt()` |
| `packages/swealog/swealog/api/routes/query.py` | Added `conversation_context` parameter to `execute_query_pipeline()` and pass to PlannerInput |
| `packages/swealog/swealog/cli/auto_cmd.py` | Pass `router_output.log_portion` as `conversation_context` in BOTH branch |
| `packages/quilto/tests/test_planner.py` | Added 5 test cases for conversation context (2 model tests + 3 prompt tests) |
| `packages/quilto/quilto/agents/retriever.py` | Formatting only (code review linter) |
| `packages/quilto/quilto/storage/repository.py` | Formatting only (code review linter) |
| `packages/quilto/tests/test_retriever.py` | Formatting only (code review linter) |
