# Story 6.3: Implement Mid-Flow Domain Expansion

Status: done

## Story

As a **Quilto developer**,
I want **Planner and Analyzer to request domain expansion**,
so that **queries can access additional domains when needed**.

## Background

Stories 6.1 and 6.2 established the domain selection and combination infrastructure:
- **Story 6.1**: Router auto-selects domains, `DomainSelector.build_active_context()` merges selected domains
- **Story 6.2**: Added `base_domain` parameter for combining a base domain with selected domains

However, the **mid-flow domain expansion** capability is NOT yet implemented:
- Planner can output `domain_expansion_request` and `expansion_reasoning`, but no state handles it
- Analyzer can mark gaps with `outside_current_expertise=True` and `suspected_domain`, but nothing acts on it
- SessionState has no fields for tracking domain expansion history
- No `EXPAND_DOMAIN` state exists in the state machine

**What This Story Delivers:**
- `EXPAND_DOMAIN` state that loads additional domains mid-flow
- State transition handling for Planner's `next_action="expand_domain"`
- State transition handling for Analyzer gaps with `outside_current_expertise=True`
- SessionState fields for tracking domain expansion (`domain_expansion_history`, `domain_expansion_request`)
- Rebuild of `ActiveDomainContext` with expanded domains

**Architecture Reference (agent-system-design.md Section 5.2):**
```
PLAN → EXPAND_DOMAIN (proactive domain gap)
ANALYZE → EXPAND_DOMAIN (gap.outside_current_expertise)
EXPAND_DOMAIN → BUILD_CONTEXT (rebuild with new domains)
BUILD_CONTEXT → PLAN (continue query flow with expanded context)
```

**Implementation Note:** While architecture specifies EXPAND_DOMAIN → BUILD_CONTEXT → PLAN, this story implements EXPAND_DOMAIN → PLAN directly by rebuilding context inline. This simplifies implementation while achieving the same result. The `active_domain_context` is rebuilt within the EXPAND_DOMAIN node, making a separate BUILD_CONTEXT step unnecessary.

## Acceptance Criteria

1. **Given** Planner outputs `next_action="expand_domain"` with `domain_expansion_request=["nutrition"]`
   **When** the state machine processes the Planner output
   **Then** system transitions to EXPAND_DOMAIN state
   **And** `domain_expansion_request` is stored in SessionState
   **And** the expansion is logged for debugging

2. **Given** Analyzer identifies a gap with `outside_current_expertise=True` and `suspected_domain="nutrition"`
   **When** the state machine processes the Analyzer output
   **Then** system transitions to EXPAND_DOMAIN state (not back to PLAN)
   **And** `domain_expansion_request` is set from the gap's `suspected_domain`
   **And** gap severity does not block expansion (both critical and nice_to_have can trigger)

3. **Given** system is in EXPAND_DOMAIN state with `domain_expansion_request=["nutrition"]`
   **When** EXPAND_DOMAIN node executes
   **Then** `DomainSelector.build_active_context()` is called with current domains + requested domains
   **And** new `ActiveDomainContext` replaces the previous one in SessionState (serialized via `.model_dump()`)
   **And** `domain_expansion_history` is appended with the newly added domains
   **And** system transitions to PLAN (context is rebuilt in-place within EXPAND_DOMAIN node)

4. **Given** domain expansion has been attempted with the same domain previously
   **When** Planner or Analyzer requests expansion to an already-expanded domain
   **Then** domain is NOT added again (no infinite loop)
   **And** `is_partial=True` is set in SessionState
   **And** system proceeds to CLARIFY (if non-retrievable gaps exist) or SYNTHESIZE (otherwise)
   **And** `domain_expansion_history` is checked before adding domains

5. **Given** the expanded `ActiveDomainContext`
   **When** downstream agents (Planner, Analyzer, Synthesizer) receive it
   **Then** they have access to the merged vocabulary, expertise, and rules from the new domain
   **And** no code changes are required in agent implementations (verified by integration test)

6. **Given** `domain_expansion_request` contains a domain NOT in available domains
   **When** EXPAND_DOMAIN attempts to load it
   **Then** invalid domain names are logged as warnings (`logger.warning`) and skipped
   **And** valid domain names in the request are still loaded
   **And** if all names are invalid, system sets `is_partial=True` and proceeds to CLARIFY or SYNTHESIZE

7. **Given** `active_domain_context` is None in SessionState (edge case)
   **When** EXPAND_DOMAIN node executes
   **Then** current domains are treated as empty list
   **And** expansion proceeds normally with the requested domains

## Tasks / Subtasks

- [x] Task 1: Add domain expansion fields to SessionState (AC: #1, #4, #7)
  - [x] 1.1: Add `domain_expansion_request: list[str] | None` field
  - [x] 1.2: Add `domain_expansion_history: list[str]` field (tracks all expanded domains across retries)
  - [x] 1.3: Add `active_domain_context: dict[str, Any] | None` field (serialized ActiveDomainContext)
  - [x] 1.4: Add `is_partial: bool` field (True when expansion exhausted, signals Synthesizer)
  - [x] 1.5: Update docstring to document new fields
  - [x] 1.6: Add `planner_output: dict[str, Any] | None` field (for routing after Planner)

  **Note:** `selected_domains` is NOT needed as a separate field - `active_domain_context["domains_loaded"]` already tracks this. Avoid redundant state.

- [x] Task 2: Create EXPAND_DOMAIN node function (AC: #3, #4, #6)
  - [x] 2.1: Create `expand_domain_node()` in `packages/quilto/quilto/state/expand_domain.py`
  - [x] 2.2: Function signature: `expand_domain_node(state: SessionState, domain_selector: DomainSelector) -> dict[str, Any]`
  - [x] 2.3: Read `domain_expansion_request` from state (handle None → empty list)
  - [x] 2.4: Read current domains from `active_domain_context["domains_loaded"]`
  - [x] 2.5: Filter out domains already in `domain_expansion_history` (prevent infinite loop)
  - [x] 2.6: Filter out domains not in `domain_selector.domains` (skip invalid, log warning via `logger.warning`)
  - [x] 2.7: If no new domains to add:
    - Set `is_partial=True` in state (for Synthesizer)
    - Set `next_state="clarify"` if there are non-retrievable gaps, else `"synthesize"`
    - Return state update with `domain_expansion_request=None`
  - [x] 2.8: Merge current domains with new domains (deduplicated)
  - [x] 2.9: Call `domain_selector.build_active_context(merged_domains)`
  - [x] 2.10: Update state with new `active_domain_context` (serialized via `.model_dump()`)
  - [x] 2.11: Append new domains to `domain_expansion_history`
  - [x] 2.12: Log expansion for debugging: `logger.info("Domain expansion: added %s", new_domains)`
  - [x] 2.13: Set `next_state="plan"` (return to planning with expanded context)
  - [x] 2.14: Clear `domain_expansion_request=None`

- [x] Task 3: Add routing from Planner to EXPAND_DOMAIN (AC: #1)
  - [x] 3.1: Create `route_after_planner()` in `packages/quilto/quilto/state/routing.py`
  - [x] 3.2: Read `planner_output` dict from state (PlannerOutput was already `.model_dump()`'d)
  - [x] 3.3: If `planner_output["next_action"] == "expand_domain"`:
    - Return state update with `domain_expansion_request=planner_output["domain_expansion_request"]`
    - Return route string `"expand_domain"`
  - [x] 3.4: If `planner_output["next_action"] == "clarify"`: return `"clarify"`
  - [x] 3.5: If `planner_output["next_action"] == "synthesize"`: return `"synthesize"`
  - [x] 3.6: Default: return `"retrieve"`

  **Note:** LangGraph conditional edges can't mutate state. The node BEFORE the edge must set `domain_expansion_request`. Implement this via a wrapper pattern: Planner node sets `domain_expansion_request` when `next_action=="expand_domain"`.

- [x] Task 4: Add routing from Analyzer to EXPAND_DOMAIN (AC: #2)
  - [x] 4.1: Create `route_after_analyzer()` in `packages/quilto/quilto/state/routing.py`
  - [x] 4.2: Read `gaps` list from state (list of Gap.model_dump() dicts)
  - [x] 4.3: Collect `suspected_domain` from gaps where `outside_current_expertise=True`
  - [x] 4.4: If domains_to_expand is non-empty AND not all in `domain_expansion_history`:
    - Return route string `"expand_domain"`
  - [x] 4.5: Priority check order:
    1. `outside_current_expertise` gaps → `"expand_domain"`
    2. `verdict == "sufficient"` → `"synthesize"`
    3. `verdict == "insufficient"` → `"plan"` (re-plan with gaps)
  - [x] 4.6: Implement state update for `domain_expansion_request` in Analyzer node (not routing function)

- [x] Task 5: Update state machine graph (all ACs)
  - [x] 5.1: Export functions in `packages/quilto/quilto/state/__init__.py`
  - [x] 5.2: Export functions in `packages/quilto/quilto/__init__.py`
  - [x] 5.3: Add `route_after_expand_domain()` routing function for conditional edges
  - [x] 5.4: Node and routing functions provided as building blocks for LangGraph integration

  **Implementation Note:** The actual LangGraph graph construction is out of scope for this story. This story provides the node function (`expand_domain_node`) and routing functions (`route_after_planner`, `route_after_analyzer`, `route_after_expand_domain`) that will be used when the graph is built.

- [x] Task 6: Create unit tests (AC: #1, #2, #3, #4, #6, #7)
  - [x] 6.1: Test `expand_domain_node` with valid expansion request
  - [x] 6.2: Test `expand_domain_node` filters out domains already in history
  - [x] 6.3: Test `expand_domain_node` logs warning for invalid domains (use `caplog` fixture)
  - [x] 6.4: Test `expand_domain_node` routes to clarify when no new domains and non-retrievable gaps
  - [x] 6.5: Test `expand_domain_node` routes to synthesize when no new domains and no non-retrievable gaps
  - [x] 6.6: Test `expand_domain_node` sets `is_partial=True` when expansion fails
  - [x] 6.7: Test `expand_domain_node` handles `active_domain_context=None` (AC #7)
  - [x] 6.8: Test `route_after_planner` returns `"expand_domain"` for correct next_action
  - [x] 6.9: Test `route_after_analyzer` detects `outside_current_expertise` gaps
  - [x] 6.10: Test `route_after_analyzer` respects `domain_expansion_history`
  - [x] 6.11: Test `domain_expansion_history` accumulates across multiple expansions

- [x] Task 7: Create integration tests (AC: #5)
  - [x] 7.1: Test Planner → EXPAND_DOMAIN → PLAN flow (mock Planner output)
  - [x] 7.2: Test Analyzer → EXPAND_DOMAIN → PLAN flow (mock Analyzer output with outside_current_expertise gap)
  - [x] 7.3: Test downstream agents receive merged context after expansion (verify vocabulary, expertise merged)
  - [x] 7.4: Test with Swealog domains: start with strength, expand to nutrition
  - [x] 7.5: Test no infinite loop: request same domain twice, verify single expansion
  - [x] 7.6: Add one `@pytest.mark.ollama` test: real Planner requests expansion for nutrition-related query

- [x] Task 8: Run validation
  - [x] 8.1: Run `make check` (lint + typecheck) - All changed files pass
  - [x] 8.2: Run unit tests - 61 passed, 1 skipped (ollama test)
  - [x] 8.3: Run full test suite - 805 passed, 28 skipped

## Dev Notes

### Key Architecture Decisions

**State Machine Location:** State machine logic is in `packages/quilto/quilto/state/` directory. Routing logic is in `routing.py`, session state in `session.py`. The EXPAND_DOMAIN node will be in a new `expand_domain.py` file.

**Why EXPAND_DOMAIN → PLAN (not → BUILD_CONTEXT):**
The architecture diagram shows `EXPAND_DOMAIN → BUILD_CONTEXT → PLAN`. However, we implement `EXPAND_DOMAIN → PLAN` directly because:
1. `expand_domain_node` rebuilds `ActiveDomainContext` inline via `domain_selector.build_active_context()`
2. No separate BUILD_CONTEXT state is needed - context is rebuilt within EXPAND_DOMAIN
3. This matches the existing pattern where context is built once and stored in state

**Node Function Pattern:**
```python
"""Domain expansion node for mid-flow domain loading."""

import logging
from typing import Any

from quilto.domain_selector import DomainSelector
from quilto.state.session import SessionState

logger = logging.getLogger(__name__)


def expand_domain_node(
    state: SessionState,
    domain_selector: DomainSelector,
) -> dict[str, Any]:
    """Expand domain context with requested domains.

    Args:
        state: Current session state with domain_expansion_request.
        domain_selector: DomainSelector instance with all available domains.

    Returns:
        State updates including new active_domain_context and next_state.
    """
    request = state.get("domain_expansion_request") or []
    history = state.get("domain_expansion_history", [])

    # Get current domains from active context
    active_ctx = state.get("active_domain_context")
    current_domains = active_ctx.get("domains_loaded", []) if active_ctx else []

    # Filter: new domains only (not in history), valid domains only (in selector)
    invalid_domains = [d for d in request if d not in domain_selector.domains]
    for invalid in invalid_domains:
        logger.warning("Domain expansion: '%s' not in available domains, skipping", invalid)

    new_domains = [
        d for d in request
        if d not in history and d in domain_selector.domains
    ]

    if not new_domains:
        # No expansion possible - proceed to clarify or synthesize partial
        logger.info("Domain expansion: no new domains to add (requested=%s, history=%s)", request, history)

        # Check if there are non-retrievable gaps for clarification
        gaps = state.get("gaps", [])
        has_non_retrievable_gaps = any(
            gap.get("gap_type") in ("subjective", "clarification")
            for gap in gaps
        )

        return {
            "next_state": "clarify" if has_non_retrievable_gaps else "synthesize",
            "domain_expansion_request": None,
            "is_partial": True,  # Signal to Synthesizer
        }

    # Build merged domain list (current + new, deduplicated)
    merged = current_domains + [d for d in new_domains if d not in current_domains]

    logger.info("Domain expansion: adding %s (merged=%s)", new_domains, merged)

    # Rebuild context with expanded domains
    new_context = domain_selector.build_active_context(merged)

    return {
        "active_domain_context": new_context.model_dump(),
        "domain_expansion_history": history + new_domains,
        "domain_expansion_request": None,  # Clear request
        "next_state": "plan",  # Return to planning with new context
    }
```

### Routing Logic Integration

**From Planner (in `routing.py`):**
```python
def route_after_planner(state: SessionState) -> str:
    """Determine next state after PLAN node.

    Routes based on Planner's next_action field.

    Args:
        state: Current session state with planner_output.

    Returns:
        Route string: "expand_domain", "retrieve", "clarify", or "synthesize".
    """
    planner_output = state.get("planner_output")
    if not planner_output:
        return "retrieve"  # Default

    next_action = planner_output.get("next_action", "retrieve")

    # Map next_action to route strings (lowercase for LangGraph convention)
    return {
        "expand_domain": "expand_domain",
        "retrieve": "retrieve",
        "clarify": "clarify",
        "synthesize": "synthesize",
    }.get(next_action, "retrieve")
```

**From Analyzer (in `routing.py`):**
```python
def route_after_analyzer(state: SessionState) -> str:
    """Determine next state after ANALYZE node.

    Priority:
    1. outside_current_expertise gaps → expand_domain
    2. verdict == sufficient → synthesize
    3. verdict == insufficient → plan (re-plan with gaps)

    Args:
        state: Current session state with analysis and gaps.

    Returns:
        Route string: "expand_domain", "synthesize", or "plan".
    """
    analysis = state.get("analysis")
    if not analysis:
        return "synthesize"  # Defensive default

    gaps = state.get("gaps", [])
    history = state.get("domain_expansion_history", [])

    # Check for outside_current_expertise gaps not yet expanded
    domains_to_expand = [
        gap.get("suspected_domain")
        for gap in gaps
        if gap.get("outside_current_expertise") and gap.get("suspected_domain")
    ]
    new_domains_to_expand = [d for d in domains_to_expand if d not in history]

    if new_domains_to_expand:
        return "expand_domain"

    verdict = analysis.get("verdict", "sufficient")
    if verdict == "sufficient":
        return "synthesize"

    # insufficient or partial → re-plan
    return "plan"
```

**Important: State mutation for domain_expansion_request**

LangGraph routing functions should NOT mutate state. The `domain_expansion_request` must be set by the node that triggers expansion:

1. **Planner node**: When `next_action == "expand_domain"`, the Planner node must copy `domain_expansion_request` from PlannerOutput to SessionState.
2. **Analyzer node**: When detecting `outside_current_expertise` gaps, the Analyzer node must populate `domain_expansion_request` from the gaps' `suspected_domain` values.

### SessionState Extensions

Add to `packages/quilto/quilto/state/session.py`:
```python
class SessionState(TypedDict, total=False):
    # ... existing fields ...

    # Domain expansion (Story 6-3)
    active_domain_context: dict[str, Any] | None
    domain_expansion_request: list[str] | None
    domain_expansion_history: list[str]
    is_partial: bool  # True when expansion exhausted, synthesize partial answer
```

**Note:** `selected_domains` is NOT added - use `active_domain_context["domains_loaded"]` instead to avoid redundant state.

### Infinite Loop Prevention

The `domain_expansion_history` field is critical:
1. Tracks ALL domains added via expansion (not just current selection)
2. Checked BEFORE adding domains - skip any already in history
3. Persists across retry cycles (Analyzer → EXPAND_DOMAIN → PLAN → ... → Analyzer → EXPAND_DOMAIN)
4. If request contains ONLY domains already in history, route to CLARIFY/SYNTHESIZE

### Edge Cases

| Case | Behavior |
|------|----------|
| Empty `domain_expansion_request` | Skip expansion, route to next appropriate state |
| All requested domains invalid | Log warning for each, route to CLARIFY or SYNTHESIZE |
| All requested domains already expanded | Skip expansion, set `is_partial=True`, route to CLARIFY/SYNTHESIZE |
| Mix of valid/invalid domains | Expand valid ones, log warning for invalid |
| Domain in request also in `domains_loaded` | Skip (already loaded), no duplication |
| `active_domain_context` is None | Treat `domains_loaded` as empty list |

### Test Strategy

**Unit Tests (Task 6):**
- Create test fixtures with mock DomainSelector and SessionState
- Test `expand_domain_node` in isolation with various state combinations
- Test routing logic functions in isolation
- Use `caplog` fixture to verify warning logs for invalid domains
- Test `is_partial` flag is set correctly

**Integration Tests (Task 7):**
- Use actual Swealog domains (strength, nutrition, running, general_fitness)
- Start with single domain, trigger expansion via mock Planner/Analyzer output
- Verify downstream agents receive expanded context (check vocabulary merge)
- NO `@pytest.mark.ollama` needed for most tests (mock LLM responses)
- One `@pytest.mark.ollama` test to verify real Planner behavior

### File References

| File | Purpose | Action |
|------|---------|--------|
| `packages/quilto/quilto/state/session.py` | SessionState TypedDict | Add 4 new fields |
| `packages/quilto/quilto/state/expand_domain.py` | New file | Create `expand_domain_node()` |
| `packages/quilto/quilto/state/routing.py` | Routing functions | Add `route_after_planner()`, `route_after_analyzer()` |
| `packages/quilto/quilto/state/__init__.py` | Package exports | Export new functions |
| `packages/quilto/quilto/domain_selector.py` | DomainSelector | NO CHANGES - use existing API |
| `packages/quilto/tests/test_expand_domain.py` | New file | Unit tests for expand_domain_node |
| `packages/quilto/tests/test_routing.py` | New file | Unit tests for routing functions |
| `tests/integration/test_domain_expansion_integration.py` | New file | Integration tests |

### Story Dependencies

| Story | Dependency Type | Notes |
|-------|-----------------|-------|
| 6-1 (done) | Upstream | Router domain selection, DomainSelector class |
| 6-2 (done) | Upstream | Base domain support, `build_active_context()` API |
| 6-4 (next) | Downstream | Swimming domain will benefit from mid-flow expansion |

### Common Mistakes to Avoid

| Mistake | Correct Pattern |
|---------|-----------------|
| Modifying DomainSelector | No changes needed - use existing `build_active_context()` |
| Storing ActiveDomainContext directly in state | Use `.model_dump()` for LangGraph serialization |
| Not checking domain_expansion_history | Always check before adding to prevent infinite loops |
| Adding separate `selected_domains` field | Use `active_domain_context["domains_loaded"]` instead |
| Mutating state in routing functions | Set `domain_expansion_request` in nodes, not routing |
| Ignoring invalid domain names silently | Log warning and skip, don't crash |
| Resetting domain_expansion_history on retry | Persist across all retries |
| Only triggering expansion on critical gaps | Both critical and nice_to_have can trigger if outside_current_expertise |
| Forgetting to set `is_partial=True` | Set when expansion fails, so Synthesizer knows |

### References

- [Source: _bmad-output/planning-artifacts/agent-system-design.md:314-361] State machine design with EXPAND_DOMAIN
- [Source: _bmad-output/planning-artifacts/agent-system-design.md:1549-1553] Gap model with `outside_current_expertise`
- [Source: _bmad-output/planning-artifacts/agent-system-design.md:1658-1662] PlannerOutput with `domain_expansion_request`
- [Source: _bmad-output/planning-artifacts/epics.md:970-983] Story 6.3 requirements
- [Source: packages/quilto/quilto/agents/models.py:254-276] Gap model implementation
- [Source: packages/quilto/quilto/agents/models.py:367-408] PlannerOutput implementation
- [Source: packages/quilto/quilto/domain_selector.py:60-102] `build_active_context()` implementation
- [Source: packages/quilto/quilto/state/session.py:11-89] Current SessionState TypedDict

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

N/A - Clean implementation with all tests passing.

### Completion Notes List

1. Added `planner_output` field to SessionState to support routing after Planner node.
2. Implementation follows the simplified EXPAND_DOMAIN → PLAN pattern (rebuilding context inline) rather than EXPAND_DOMAIN → BUILD_CONTEXT → PLAN from architecture doc.
3. Routing functions are pure - they don't mutate state, only return route strings. State updates are done by nodes.
4. The `@pytest.mark.ollama` test is skipped by default and requires `--use-real-ollama` flag.
5. Pre-existing lint errors in `scripts/convert_obsidian.py` are unrelated to this story.

### File List

| File | Action | Description |
|------|--------|-------------|
| `packages/quilto/quilto/state/session.py` | Modified | Added 5 new fields: `planner_output`, `active_domain_context`, `domain_expansion_request`, `domain_expansion_history`, `is_partial` |
| `packages/quilto/quilto/state/expand_domain.py` | Created | `expand_domain_node()` function for mid-flow domain expansion |
| `packages/quilto/quilto/state/routing.py` | Modified | Added `route_after_planner()`, `route_after_analyzer()`, `route_after_expand_domain()` |
| `packages/quilto/quilto/state/__init__.py` | Modified | Exported new functions |
| `packages/quilto/quilto/__init__.py` | Modified | Exported new functions at package level |
| `packages/quilto/tests/test_expand_domain.py` | Created | 21 unit tests for expand_domain_node |
| `packages/quilto/tests/test_routing.py` | Created | 27 unit tests for routing functions |
| `tests/integration/test_domain_expansion_integration.py` | Created | 13 integration tests including 1 ollama test |

