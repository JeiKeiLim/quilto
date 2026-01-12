# Story 3.2: Implement Planner Agent

Status: done

## Story

As a **Quilto developer**,
I want a **Planner agent that decomposes queries and creates retrieval strategies**,
So that **complex queries are handled systematically with proper execution plans**.

## Acceptance Criteria

1. **Given** a simple query with domain context
   **When** Planner processes it
   **Then** it returns a `PlannerOutput` with `execution_strategy: COUPLED`
   **And** creates a single sub-query matching the original query
   **And** defines a retrieval strategy (date_range, keyword, or topical)

2. **Given** a complex multi-part query
   **When** Planner classifies the dependency
   **Then** it returns `INDEPENDENT` if sub-queries don't need each other's results
   **And** returns `DEPENDENT` if one sub-query needs another's output
   **And** returns `COUPLED` if sub-queries share context tightly (really one question)

3. **Given** a query with domain context
   **When** Planner creates sub-queries
   **Then** each sub-query has an `id` field with unique identifier
   **And** each sub-query has a `question` field with the extracted question
   **And** each sub-query has a `retrieval_strategy` (date_range, keyword, topical)
   **And** each sub-query has `retrieval_params` with strategy-specific parameters
   **And** `execution_order` specifies the order for DEPENDENT queries

4. **Given** a query that may need additional domains
   **When** Planner detects the current domains are insufficient
   **Then** it sets `domain_expansion_request` with suggested domain names
   **And** provides `expansion_reasoning` explaining why expansion is needed
   **And** sets `next_action: "expand_domain"`

5. **Given** feedback from a failed evaluation
   **When** Planner receives `evaluation_feedback`
   **Then** it uses the feedback to adjust the retrieval strategy
   **And** creates an updated plan targeting the gaps identified
   **And** reasoning explains what changed from the previous plan

6. **Given** Analyzer gap feedback
   **When** Planner receives `gaps_from_analyzer`
   **Then** it creates retrieval instructions targeting each gap
   **And** gaps with `outside_current_expertise=True` trigger domain expansion request
   **And** gaps with `gap_type=SUBJECTIVE` or `gap_type=CLARIFICATION` trigger `next_action: "clarify"`
   **And** `clarify_questions` lists questions for non-retrievable gaps

7. **Given** the existing agent patterns from Router and Parser
   **When** implementing Planner
   **Then** it follows the same patterns: AGENT_NAME, build_prompt(), async method
   **And** uses `LLMClient.complete_structured()` with Pydantic output schema
   **And** is exported from `quilto.agents` module

8. **Given** integration tests with real Ollama
   **When** run with `--use-real-ollama` flag
   **Then** Planner correctly classifies simple queries as COUPLED
   **And** Planner correctly classifies multi-part queries by dependency type
   **And** Planner generates valid retrieval strategies with parameters

## Tasks / Subtasks

- [x] Task 1: Define Planner-related enums and shared types in models.py (AC: #1, #2, #3)
  - [x] Create `QueryType` enum: SIMPLE, INSIGHT, RECOMMENDATION, COMPARISON, CORRECTION
  - [x] Create `DependencyType` enum: INDEPENDENT, DEPENDENT, COUPLED
  - [x] Create `GapType` enum: TEMPORAL, TOPICAL, CONTEXTUAL, SUBJECTIVE, CLARIFICATION
  - [x] Create `RetrievalStrategy` enum: DATE_RANGE, KEYWORD, TOPICAL

- [x] Task 2: Define Planner input/output models in models.py (AC: #1, #3, #4, #5, #6)
  - [x] Create `Gap` model with description, gap_type, severity, searched, found, outside_current_expertise, suspected_domain
  - [x] Create `EvaluationFeedback` model with issue, suggestion, affected_claim fields
  - [x] Create `ActiveDomainContext` stub model (domains_loaded, vocabulary, expertise, evaluation_rules, context_guidance, available_domains)
  - [x] Create `SubQuery` model with id, question, retrieval_strategy, retrieval_params
  - [x] Create `PlannerInput` model with query, query_type, domain_context, gaps_from_analyzer, evaluation_feedback, retrieval_history, global_context_summary
  - [x] Create `PlannerOutput` model with all fields from agent-system-design.md Section 11.3
  - [x] Use `Field(min_length=1)` for required string fields (query, question)

- [x] Task 3: Implement PlannerAgent class (AC: #1, #2, #7)
  - [x] Create `planner.py` with PlannerAgent class
  - [x] Implement `build_prompt()` with classification rules and examples
  - [x] Implement `plan()` async method using `complete_structured()`
  - [x] Add Google-style docstrings for all methods
  - [x] Follow existing Router/Parser patterns

- [x] Task 4: Implement retrieval strategy generation (AC: #3)
  - [x] Add DATE_RANGE strategy with start_date, end_date params in prompt
  - [x] Add KEYWORD strategy with keywords, semantic_expansion params in prompt
  - [x] Add TOPICAL strategy with topics, related_terms params in prompt
  - [x] Add strategy selection logic to prompt

- [x] Task 5: Implement domain expansion detection (AC: #4)
  - [x] Add domain gap detection logic to prompt instructions
  - [x] Handle `outside_current_expertise` flag from gaps
  - [x] Generate domain_expansion_request based on gap analysis
  - [x] Set next_action appropriately

- [x] Task 6: Implement re-planning on feedback (AC: #5, #6)
  - [x] Handle evaluation_feedback in prompt
  - [x] Handle gaps_from_analyzer in prompt
  - [x] Set next_action to "clarify" for SUBJECTIVE/CLARIFICATION gaps
  - [x] Generate clarify_questions for non-retrievable gaps

- [x] Task 7: Export from agents module (AC: #7)
  - [x] Add PlannerAgent, PlannerInput, PlannerOutput to `__init__.py`
  - [x] Add all new enums and model types to exports
  - [x] Update `__all__` list with all new public symbols
  - [x] Ensure py.typed marker is present (should exist from Story 2-2)

- [x] Task 8: Add unit tests for Planner models (AC: #1, #2, #3)
  - [x] Test QueryType, DependencyType, GapType, RetrievalStrategy enum values
  - [x] Test SubQuery validation (id required, question min_length=1)
  - [x] Test PlannerInput validation (query min_length=1)
  - [x] Test PlannerOutput validation
  - [x] Test Gap model with all fields including outside_current_expertise
  - [x] Test EvaluationFeedback model

- [x] Task 9: Add unit tests for PlannerAgent (AC: #1, #2, #3, #4, #5, #6)
  - [x] Test simple query -> COUPLED classification
  - [x] Test multi-part independent -> INDEPENDENT classification
  - [x] Test sequential dependent -> DEPENDENT classification
  - [x] Test retrieval strategy generation (DATE_RANGE, KEYWORD, TOPICAL)
  - [x] Test domain expansion detection (outside_current_expertise gaps)
  - [x] Test re-planning with evaluation feedback
  - [x] Test re-planning with analyzer gaps
  - [x] Test clarify_questions generation for SUBJECTIVE/CLARIFICATION gaps
  - [x] Test empty query validation (raises ValueError)

- [x] Task 10: Add integration tests with real Ollama (AC: #8)
  - [x] Test real simple query planning
  - [x] Test real multi-part query classification
  - [x] Test real retrieval strategy generation
  - [x] Use `pytest.mark.asyncio` and `--use-real-ollama` fixture

- [x] Task 11: Verify no regression (AC: #7)
  - [x] Run full test suite: `make validate`
  - [x] Run integration tests: `make test-ollama`
  - [x] Verify all existing Router, Parser tests still pass

## Dev Notes

### Files to Create/Modify

| File | Action | Description |
|------|--------|-------------|
| `packages/quilto/quilto/agents/planner.py` | Create | PlannerAgent class |
| `packages/quilto/quilto/agents/models.py` | Modify | Add Planner enums and models |
| `packages/quilto/quilto/agents/__init__.py` | Modify | Export new types |
| `packages/quilto/tests/test_planner.py` | Create | Planner unit tests |
| `packages/quilto/tests/test_planner_integration.py` | Create | Integration tests (optional, can be in same file) |

### What This Story Does

This story implements the Planner agent which is the strategic brain of the query flow. It:
1. Analyzes queries to determine their structure (simple vs complex)
2. Classifies multi-question dependencies (INDEPENDENT/DEPENDENT/COUPLED)
3. Creates retrieval strategies for the Retriever agent
4. Detects when domain expansion is needed
5. Re-plans based on feedback from Evaluator or gaps from Analyzer
6. Determines next_action: retrieve, expand_domain, clarify, or synthesize

### What This Story Does NOT Include

- Retriever agent implementation (that's Story 3-3)
- State machine orchestration (that's framework-level, later stories)
- Actual retrieval execution (Planner creates the plan, Retriever executes)
- Domain expansion execution (Planner suggests, orchestrator decides)
- Full ActiveDomainContext implementation (stub is sufficient for now)

### Architecture Position

From agent-system-design.md:

```
Router -> BUILD_CONTEXT -> Planner -> Retriever -> Analyzer
                             ^                        |
                             +------------------------+
                               (re-plan if gaps)
```

**State Machine Transitions (from Section 5.4):**
```
PLAN -> RETRIEVE (normal, next_action="retrieve")
PLAN -> EXPAND_DOMAIN (next_action="expand_domain")
PLAN -> CLARIFY (next_action="clarify")
PLAN -> SYNTHESIZE (next_action="synthesize", already sufficient)
```

### Complete Model Definitions

**From agent-system-design.md Section 11.1 - Enums:**

```python
class QueryType(str, Enum):
    """Classification of query intent."""
    SIMPLE = "simple"           # Direct retrieval ("show me X")
    INSIGHT = "insight"         # Why/pattern questions
    RECOMMENDATION = "recommendation"  # What should I do
    COMPARISON = "comparison"   # Compare X vs Y
    CORRECTION = "correction"   # Fix previous data


class DependencyType(str, Enum):
    """Multi-question dependency classification."""
    INDEPENDENT = "independent"  # Can run in parallel
    DEPENDENT = "dependent"      # Sequential, later needs earlier
    COUPLED = "coupled"          # Really one question


class GapType(str, Enum):
    """Classification of missing information."""
    TEMPORAL = "temporal"        # Need different time range
    TOPICAL = "topical"          # Need different subject matter
    CONTEXTUAL = "contextual"    # Need related context
    SUBJECTIVE = "subjective"    # Only user knows (current state)
    CLARIFICATION = "clarification"  # Query itself is ambiguous
```

**From agent-system-design.md Section 11.3 - Planner Models:**

```python
class Gap(BaseModel):
    """An identified gap in available information."""
    description: str
    gap_type: GapType
    severity: Literal["critical", "nice_to_have"]
    searched: bool = False
    found: bool = False
    outside_current_expertise: bool = False
    suspected_domain: str | None = None


class EvaluationFeedback(BaseModel):
    """Specific feedback from evaluation failure."""
    issue: str
    suggestion: str
    affected_claim: str | None = None


class SubQuery(BaseModel):
    """A decomposed sub-query."""
    id: int
    question: str = Field(min_length=1)
    retrieval_strategy: str  # "date_range", "keyword", "topical"
    retrieval_params: dict   # Strategy-specific parameters


class ActiveDomainContext(BaseModel):
    """Combined context from base + selected domains.

    NOTE: This is a stub for Planner story. Full implementation
    will come with domain combination feature.
    """
    domains_loaded: list[str]
    vocabulary: dict[str, str]
    expertise: str
    evaluation_rules: list[str] = []
    context_guidance: str = ""
    available_domains: list[DomainInfo] = []


class PlannerInput(BaseModel):
    """Input to Planner agent."""
    query: str = Field(min_length=1)
    query_type: QueryType | None = None

    # Domain context
    domain_context: ActiveDomainContext

    # Context from previous attempts (for re-planning)
    retrieval_history: list[dict] = []
    gaps_from_analyzer: list[Gap] = []
    evaluation_feedback: EvaluationFeedback | None = None

    # Global context summary
    global_context_summary: str | None = None


class PlannerOutput(BaseModel):
    """Output from Planner agent."""
    # Query analysis
    original_query: str
    query_type: QueryType

    # Decomposition (if complex query)
    sub_queries: list[SubQuery]
    dependencies: list[dict]  # {"from": 1, "to": 2, "reason": "..."}
    execution_strategy: DependencyType
    execution_order: list[int]  # Order of sub_query IDs

    # Retrieval instructions for Retriever
    retrieval_instructions: list[dict]
    # Structure: {"strategy": str, "params": dict, "sub_query_id": int}

    # State tracking
    gaps_status: dict[str, dict]  # {"topic_x": {"searched": true, "found": false}}

    # Domain expansion (proactive)
    domain_expansion_request: list[str] | None = None
    expansion_reasoning: str | None = None

    # Clarification (for non-retrievable gaps)
    clarify_questions: list[str] | None = None

    # Action decision
    next_action: Literal["retrieve", "expand_domain", "clarify", "synthesize"]

    reasoning: str
```

### Retrieval Strategy Parameters

| Strategy | Parameters | Use Case |
|----------|------------|----------|
| DATE_RANGE | `{"start_date": "YYYY-MM-DD", "end_date": "YYYY-MM-DD"}` | "What did I do last week?" |
| KEYWORD | `{"keywords": ["bench", "press"], "semantic_expansion": true}` | "Show me bench press workouts" |
| TOPICAL | `{"topics": ["progress", "trend"], "related_terms": ["improvement"]}` | "How's my progress?" |

### Dependency Classification Examples (from agent-system-design.md Section 7.4)

| Query | Classification | Execution |
|-------|----------------|-----------|
| "How much did I bench and squat yesterday?" | INDEPENDENT | Parallel |
| "Why was bench heavy and how to fix it?" | DEPENDENT | Sequential |
| "What did I eat Tuesday and how much protein?" | COUPLED | Single pass |
| "Compare my running and strength this month" | INDEPENDENT | Parallel |
| "Why am I plateauing and what program should I try?" | DEPENDENT | Sequential |

### EXPAND vs CLARIFY Decision Logic (from Section 7.3)

```
For each gap from Analyzer:
    Is it retrievable (could exist in notes)?
        YES: Have we searched for it?
            NO  -> next_action="retrieve" (search for it)
            YES, not found -> check if domain gap:
                outside_current_expertise=True -> next_action="expand_domain"
                else -> next_action="clarify" (ask user)
        NO (gap_type=SUBJECTIVE or CLARIFICATION) -> next_action="clarify"
```

**Gap types that DON'T trigger expansion (always clarify):**
- SUBJECTIVE: Only user knows the answer now
- CLARIFICATION: Query itself is ambiguous

### Prompt Template Structure

```
ROLE: You are a query strategist for a context-aware AI system.

TASK: Analyze the query and create an execution plan.

=== QUERY DECOMPOSITION ===
INDEPENDENT: Different subjects/topics, no causal relationship
DEPENDENT: One answer informs another, causal chain
COUPLED: Same subject/timeframe, really one question

=== RETRIEVAL STRATEGIES ===
DATE_RANGE: When query mentions time periods (start_date, end_date)
KEYWORD: When query mentions specific activities/items (keywords, semantic_expansion)
TOPICAL: When query is about patterns/progress (topics, related_terms)

=== DOMAIN EXPANSION ===
Consider expansion when:
- Gaps require expertise outside current domains
- Cross-domain correlations needed

=== NEXT ACTION DECISION ===
- "retrieve": Normal case, have retrieval instructions
- "expand_domain": Need domains not currently loaded
- "clarify": Gaps are SUBJECTIVE or CLARIFICATION type
- "synthesize": Already have sufficient context (rare, on retry success)

=== INPUT ===
Query: {query}
Domain expertise: {domain_context.expertise}
Vocabulary: {domain_context.vocabulary}
Available domains: {domain_context.available_domains}
Gaps from Analyzer: {gaps_from_analyzer}
Evaluation feedback (if retry): {evaluation_feedback}
Retrieval history: {retrieval_history}
Global context: {global_context_summary}

=== OUTPUT (JSON) ===
{PlannerOutput schema}
```

### Code Patterns to Follow

**From RouterAgent (router.py):**
```python
AGENT_NAME = "router"

def __init__(self, llm_client: LLMClient) -> None:
    """Initialize the Router agent."""
    self.llm_client = llm_client

async def classify(self, router_input: RouterInput) -> RouterOutput:
    """Classify input and select domains."""
    if not router_input.raw_input or not router_input.raw_input.strip():
        raise ValueError("raw_input cannot be empty or whitespace-only")

    system_prompt = self.build_prompt(router_input)
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": router_input.raw_input},
    ]

    result = await self.llm_client.complete_structured(
        agent=self.AGENT_NAME,
        messages=messages,
        response_model=RouterOutput,
    )
    return result
```

**Apply to PlannerAgent:**
```python
AGENT_NAME = "planner"

async def plan(self, planner_input: PlannerInput) -> PlannerOutput:
    """Create retrieval plan for query."""
    if not planner_input.query or not planner_input.query.strip():
        raise ValueError("query cannot be empty or whitespace-only")
    # ... similar pattern
```

### Test Organization

```python
class TestPlannerEnums:
    """Tests for Planner-related enums."""
    def test_query_type_values(self): ...
    def test_dependency_type_values(self): ...
    def test_gap_type_values(self): ...


class TestPlannerModels:
    """Tests for Planner Pydantic models."""
    def test_sub_query_requires_id(self): ...
    def test_sub_query_question_min_length(self): ...
    def test_planner_input_query_min_length(self): ...
    def test_gap_model_all_fields(self): ...
    def test_evaluation_feedback_model(self): ...


class TestPlannerClassification:
    """Tests for dependency classification."""
    async def test_simple_query_coupled(self, mock_llm): ...
    async def test_multi_part_independent(self, mock_llm): ...
    async def test_multi_part_dependent(self, mock_llm): ...


class TestPlannerStrategies:
    """Tests for retrieval strategy generation."""
    async def test_date_range_strategy(self, mock_llm): ...
    async def test_keyword_strategy(self, mock_llm): ...
    async def test_topical_strategy(self, mock_llm): ...


class TestPlannerDomainExpansion:
    """Tests for domain expansion detection."""
    async def test_outside_expertise_triggers_expansion(self, mock_llm): ...
    async def test_subjective_gap_triggers_clarify(self, mock_llm): ...


class TestPlannerReplanning:
    """Tests for re-planning on feedback."""
    async def test_replanning_with_evaluation_feedback(self, mock_llm): ...
    async def test_replanning_with_analyzer_gaps(self, mock_llm): ...


class TestPlannerIntegration:
    """Integration tests with real Ollama."""
    @pytest.mark.asyncio
    async def test_real_simple_query(self, use_real_ollama: bool): ...
    @pytest.mark.asyncio
    async def test_real_multi_part_query(self, use_real_ollama: bool): ...
```

### Common Mistakes to Avoid (from project-context.md + Epic 2-3 learnings)

| Mistake | Correct Pattern | Story Source |
|---------|-----------------|--------------|
| Required string without length check | `Field(min_length=1)` | 2-4 |
| Redundant `@field_validator` for range | Use `Field(ge=0, le=10)` instead | 2-4 |
| Missing boundary value tests | Test exact boundaries (0.0, 1.0) | 2-1, 2-2 |
| Missing `py.typed` marker | Add marker file (already exists from 2-2) | 2-2 |
| Empty string not tested separately | Test both `None` and `""` cases | 2-2 |
| Missing `__all__` in `__init__.py` | Export all public classes | 1.5-8 |
| Both `Field()` AND `@field_validator` | Use only `Field(ge=, le=)` for range | 2-4 |
| Not running `make test-ollama` | Run before marking done | Epic 2 retro |

### Pre-Review Checklist (from Epic 2 Retrospective)

Before requesting code review, verify:

- [ ] `make check` passes (lint + typecheck)
- [ ] `make test-ollama` passes (integration tests)
- [ ] All new functions have Google-style docstrings
- [ ] All new classes exported in `__init__.py` with `__all__`
- [ ] Required string fields use `Field(min_length=1)`
- [ ] Empty string/None cases tested where applicable
- [ ] No regression in existing tests (run full suite)

### Validation Commands

```bash
# During development
make check                    # lint + typecheck

# Before marking complete (REQUIRED)
make validate                 # lint + format + typecheck + unit tests
make test-ollama              # Integration tests with real Ollama
```

### Error Handling

| Error Case | Expected Behavior | Test Example |
|------------|-------------------|--------------|
| Empty query | Raise ValueError | `PlannerInput(query="", domain_context=...)` |
| Whitespace-only query | Raise ValueError | `PlannerInput(query="   ", domain_context=...)` |
| No domain context | Use minimal context | Should still work with empty expertise |
| Unknown gap_type | Validate via enum | Pydantic rejects invalid values |

### Dependencies

| Dependency | Status | Notes |
|------------|--------|-------|
| LLMClient | Done (1-3) | Use existing interface |
| RouterOutput | Done (2-2) | Provides input_type context |
| InputType enum | Done (2-2) | Reuse for context |
| DomainInfo | Done (2-2) | Used in ActiveDomainContext |
| pytest fixtures | Done (2-2) | Use existing mock_llm, use_real_ollama |

### Architecture Compliance

**From architecture.md:**
- Planner is medium-high tier agent (tier: "medium_high")
- Uses LiteLLM via LLMClient abstraction
- Returns structured Pydantic output (PlannerOutput)

### Epic 3 Context

This is the second story of Epic 3: Query & Retrieval. It enables query planning by decomposing complex queries and creating retrieval strategies.

**Epic 3 Dependencies:**
- Story 3-1 (Router QUERY/BOTH) - **Done** - Provides classification
- Story 3-2 (Planner) - **This story** - Creates retrieval plans
- Story 3-3 (Retriever) - Depends on PlannerOutput
- Story 3-4 (Running domain) - Independent

### References

- [Source: epics.md#Story-3.2] Story definition
- [Source: agent-system-design.md#7.3] EXPAND vs CLARIFY decision logic
- [Source: agent-system-design.md#7.4] Multi-question handling
- [Source: agent-system-design.md#11.1] Shared enums (QueryType, DependencyType, GapType)
- [Source: agent-system-design.md#11.3] PlannerAgent interface
- [Source: state-machine-diagram.md] PLAN state position
- [Source: project-context.md] Quilto vs Swealog separation
- [Source: 3-1-extend-router-for-query-both-classification.md] Previous story patterns

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

N/A

### Completion Notes List

1. Implemented all 4 Planner-related enums: QueryType, DependencyType, GapType, RetrievalStrategy
2. Implemented 6 Pydantic models: Gap, EvaluationFeedback, SubQuery, ActiveDomainContext, PlannerInput, PlannerOutput
3. PlannerAgent follows existing Router/Parser patterns with AGENT_NAME, build_prompt(), and async plan() method
4. Comprehensive prompt includes query decomposition, dependency classification, retrieval strategy selection, domain expansion, and re-planning instructions
5. Helper methods (should_expand_domain, should_clarify, determine_next_action) provide programmatic decision support
6. All 16 new types exported from quilto.agents module with __all__ list
7. 49 unit tests covering enums, models, classification, strategies, domain expansion, re-planning, and input validation
8. 3 integration tests with real Ollama (test flexibility allows for LLM interpretation variance)
9. `make validate` passes: 581 passed, 14 skipped
10. `make test-ollama` passes: 591 passed, 4 skipped

### File List

| File | Action | Description |
|------|--------|-------------|
| `packages/quilto/quilto/agents/models.py` | Modified | Added QueryType, DependencyType, GapType, RetrievalStrategy enums and Gap, EvaluationFeedback, SubQuery, ActiveDomainContext, PlannerInput, PlannerOutput models |
| `packages/quilto/quilto/agents/planner.py` | Created | PlannerAgent class with build_prompt(), plan(), and helper methods |
| `packages/quilto/quilto/agents/__init__.py` | Modified | Exported PlannerAgent and all new types |
| `packages/quilto/tests/test_planner.py` | Created | Unit tests and 3 integration tests |
| `_bmad-output/implementation-artifacts/sprint-status.yaml` | Modified | Updated story status |
| `llm-config.yaml` | Created | LLM configuration for testing (project-level) |

---

## Senior Developer Review (AI)

**Reviewer:** Amelia (Dev Agent)
**Date:** 2026-01-12
**Model:** Claude Opus 4.5

### Review Outcome: ✅ APPROVED

### Verification Results

| Check | Result |
|-------|--------|
| `make validate` | ✅ 584 passed, 14 skipped |
| `make test-ollama` | ✅ 591 passed, 4 skipped |
| All ACs implemented | ✅ Verified |
| All `[x]` tasks complete | ✅ Verified |
| Exports in `__all__` | ✅ 16 types exported |
| Google-style docstrings | ✅ Present |

### Issues Found & Fixed

| ID | Severity | Issue | Resolution |
|----|----------|-------|------------|
| M1 | MEDIUM | `llm-config.yaml` not in File List | ✅ Added to File List |
| M2 | MEDIUM | `sprint-status.yaml` not in File List | ✅ Added to File List |
| M3 | MEDIUM | `RetrievalStrategy` enum not used in `SubQuery` | ⚠️ By design - matches LLM output format |
| M4 | MEDIUM | Missing edge case test for mixed gaps | ✅ Added 2 tests |
| L1 | LOW | `type: ignore` in planner.py | ⚠️ Acceptable - LiteLLM typing workaround |
| L2 | LOW | Missing `AGENT_NAME` test | ✅ Added test |
| L3 | LOW | Test count ambiguity | ✅ Fixed wording |

### Tests Added During Review

1. `test_agent_name_constant` - Verifies `PlannerAgent.AGENT_NAME == "planner"`
2. `test_determine_next_action_expansion_beats_clarify` - Edge case: gap with both flags
3. `test_determine_next_action_multiple_gaps_expansion_wins` - Priority when multiple gaps

### Notes

- **M3 (RetrievalStrategy enum):** The enum exists for documentation/reference but `SubQuery.retrieval_strategy` uses `str` to match LLM JSON output. This is intentional per agent-system-design.md spec.
- **L1 (type: ignore):** Standard workaround for LiteLLM's `complete_structured` return type variance.
- All HIGH and MEDIUM issues addressed. Story ready for merge.
