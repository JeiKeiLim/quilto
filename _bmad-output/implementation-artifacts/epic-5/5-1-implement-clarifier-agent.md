# Story 5.1: Implement Clarifier Agent

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **Quilto developer**,
I want a **Clarifier agent that requests missing information from users**,
so that **the system asks rather than guesses when stuck**.

## Acceptance Criteria

1. **Given** gaps identified by Analyzer as non-retrievable (gap_type=SUBJECTIVE or CLARIFICATION)
   **When** Clarifier processes them
   **Then** it generates clear, specific questions for the user

2. **Given** the Clarifier agent
   **When** it generates questions
   **Then** questions reference the original query context

3. **Given** the Clarifier agent output
   **When** questions are generated
   **Then** the system should be ready to transition to WAIT_USER state (state machine integration is Story 5-2)

4. **Given** previous clarifications that were already asked
   **When** Clarifier generates new questions
   **Then** it does NOT re-ask questions the user has already answered

5. **Given** the Clarifier agent
   **When** instantiated and used
   **Then** it follows the same LLMClient pattern as Router, Parser, Planner, Retriever, Analyzer, Synthesizer, and Evaluator

6. **Given** gaps that could be retrieved from storage
   **When** Clarifier processes them
   **Then** it does NOT ask about those gaps (only ask about non-retrievable gaps)

7. **Given** multiple non-retrievable gaps
   **When** Clarifier generates questions
   **Then** it prioritizes and groups related questions (max 3 questions per interaction)

## Tasks / Subtasks

- [x] Task 1: Create Clarifier Pydantic models (AC: #1, #2, #3, #4, #7)
  - [x] 1.1: Define `ClarificationQuestion` model with: question, gap_addressed, options, required (per architecture Section 11.8)
  - [x] 1.2: Define `ClarifierInput` model with: original_query, gaps, vocabulary, retrieval_history, previous_clarifications
  - [x] 1.3: Define `ClarifierOutput` model with: questions, context_explanation, fallback_action (per architecture Section 11.8)

- [x] Task 2: Create ClarifierAgent class (AC: #5)
  - [x] 2.1: Create `packages/quilto/quilto/agents/clarifier.py`
  - [x] 2.2: Define `ClarifierAgent` class with `AGENT_NAME = "clarifier"`
  - [x] 2.3: Implement `__init__(self, llm_client: LLMClient)`
  - [x] 2.4: Add Google-style docstrings with examples

- [x] Task 3: Build Clarifier prompt (AC: #1, #2, #4, #6)
  - [x] 3.1: Implement `build_prompt(self, clarifier_input: ClarifierInput) -> str`
  - [x] 3.2: Include rule: "Only ask about gaps that cannot be retrieved from stored data"
  - [x] 3.3: Include rule: "Don't re-ask questions the user has already answered"
  - [x] 3.4: Include rule: "Use domain-appropriate terminology from vocabulary"
  - [x] 3.5: Include rule: "Offer multiple-choice options when applicable"
  - [x] 3.6: Include question guidelines (good/bad examples per architecture)
  - [x] 3.7: Include fallback_action instruction section
  - [x] 3.8: Inject vocabulary using `_format_vocabulary()` helper
  - [x] 3.9: Include retrieval_history for context on what was searched

- [x] Task 4: Implement clarify method (AC: #1, #7)
  - [x] 4.1: Implement `async def clarify(self, clarifier_input: ClarifierInput) -> ClarifierOutput`
  - [x] 4.2: Validate original_query is not empty/whitespace (per Evaluator pattern)
  - [x] 4.3: Filter gaps to only non-retrievable (SUBJECTIVE, CLARIFICATION gap_types)
  - [x] 4.4: If no non-retrievable gaps, return empty ClarifierOutput (no LLM call needed)
  - [x] 4.5: Call LLM with structured output to `ClarifierOutput`
  - [x] 4.6: Limit questions to max 3 per interaction (post-process or in prompt)

- [x] Task 5: Add helper methods
  - [x] 5.1: `filter_non_retrievable_gaps(self, gaps: list[Gap]) -> list[Gap]`
  - [x] 5.2: `_format_gaps(self, gaps: list[Gap]) -> str`
  - [x] 5.3: `_format_retrieval_history(self, history: list[RetrievalAttempt]) -> str`
  - [x] 5.4: `_format_previous_clarifications(self, previous: list[str]) -> str`
  - [x] 5.5: `_format_vocabulary(self, vocabulary: dict[str, str]) -> str` (follow Synthesizer pattern)
  - [x] 5.6: `has_questions(self, output: ClarifierOutput) -> bool`

- [x] Task 6: Export from agents __init__.py
  - [x] 6.1: Add ClarifierAgent to imports
  - [x] 6.2: Add ClarificationQuestion, ClarifierInput, ClarifierOutput to imports
  - [x] 6.3: Update `__all__` list with all new exports (4 new items)

- [x] Task 7: Create comprehensive unit tests in `packages/quilto/tests/test_clarifier.py`
  - [x] 7.1: Test model validation for all new types (ClarificationQuestion, ClarifierInput, ClarifierOutput)
  - [x] 7.2: Test ClarificationQuestion with options=None (valid) and options=[] (valid)
  - [x] 7.3: Test ClarifierAgent instantiation
  - [x] 7.4: Test prompt building with various gap combinations
  - [x] 7.5: Test filter_non_retrievable_gaps helper
  - [x] 7.6: Test clarify method with mock LLM (happy path)
  - [x] 7.7: Test that retrievable gaps are excluded
  - [x] 7.8: Test that previous clarifications are not re-asked (instruction verified in prompt)
  - [x] 7.9: Test max 3 questions limit
  - [x] 7.10: Test empty previous_clarifications list handling
  - [x] 7.11: Test empty gaps list returns early (no LLM call)
  - [x] 7.12: Test all exports importable from quilto.agents

- [x] Task 8: Check if manual_test.py update needed
  - [x] 8.1: Review `scripts/manual_test.py` for Clarifier support
  - [x] 8.2: Add ClarifierAgent to manual testing (runs after Analyzer when INSUFFICIENT with non-retrievable gaps)

- [x] Task 9: Run validation
  - [x] 9.1: Run `make check` (lint + typecheck)
  - [x] 9.2: Run `make validate` (full validation)
  - [x] 9.3: Run `make test-ollama` (integration tests with real Ollama)

## Dev Notes

### Architecture Patterns

- **Location:** `packages/quilto/quilto/agents/clarifier.py` (Quilto framework, NOT Swealog)
- **Pattern:** Follow existing agent patterns from `analyzer.py`, `synthesizer.py`, `evaluator.py`
- **Model Requirement:** MEDIUM tier - natural question generation but not complex reasoning
- **LLM Tier:** Configure as "medium" in llm-config.yaml (similar to Synthesizer)

### Critical Design: Non-Retrievable Gaps Only

The Clarifier MUST only ask about gaps that **cannot** be retrieved from stored data. Per architecture (Section 7.3):

| Gap Type | Category | Action |
|----------|----------|--------|
| Temporal | Retrievable | DO NOT ask - Retriever handles |
| Topical | Retrievable | DO NOT ask - Retriever handles |
| Contextual | Retrievable | DO NOT ask - Retriever handles |
| Subjective-past | Retrievable | DO NOT ask - might be logged |
| **Subjective-present** | **Non-retrievable** | **ASK user** |
| **Query clarification** | **Non-retrievable** | **ASK user** |

The `filter_non_retrievable_gaps` helper should filter to only:
- `gap_type == GapType.SUBJECTIVE` (current state, feelings, preferences)
- `gap_type == GapType.CLARIFICATION` (ambiguous query)

### Gap Classification Reference (from agents.models)

Reuse existing `Gap` model:
```python
class GapType(str, Enum):
    TEMPORAL = "temporal"      # Need different time range
    TOPICAL = "topical"        # Need different subject matter
    CONTEXTUAL = "contextual"  # Need related context
    SUBJECTIVE = "subjective"  # Only user knows (current state)
    CLARIFICATION = "clarification"  # Query itself is ambiguous
```

### ClarificationQuestion Model

Per agent-system-design.md Section 11.8 (CORRECTED to match architecture):

```python
class ClarificationQuestion(BaseModel):
    """A question to ask the user."""
    model_config = ConfigDict(strict=True)

    question: str = Field(min_length=1)  # The actual question to ask
    gap_addressed: str = Field(min_length=1)  # Which gap this would fill (from Gap.description)
    options: list[str] | None = None  # Multiple choice if applicable
    required: bool = True  # Whether the question must be answered
```

**Note on gap_addressed**: Since `Gap` model doesn't have an `id` field, use `gap.description` as the identifier for linking questions to gaps.

### ClarifierInput Model

Per agent-system-design.md Section 11.8:

```python
class ClarifierInput(BaseModel):
    """Input to Clarifier agent."""
    model_config = ConfigDict(strict=True)

    original_query: str = Field(min_length=1)
    gaps: list[Gap]  # From Analyzer, will be filtered to non-retrievable
    vocabulary: dict[str, str]  # For proper terminology

    # Context to avoid asking about things we could look up
    retrieval_history: list[RetrievalAttempt] = []

    # User interaction history (avoid re-asking)
    previous_clarifications: list[str] = []
```

### ClarifierOutput Model

Per agent-system-design.md Section 11.8 (CORRECTED to match architecture):

```python
class ClarifierOutput(BaseModel):
    """Output from Clarifier agent."""
    model_config = ConfigDict(strict=True)

    questions: list[ClarificationQuestion]  # Max 3 per interaction

    # Framing for user
    context_explanation: str = Field(min_length=1)  # Why we're asking

    # If user declines, what we can still do
    fallback_action: str = Field(min_length=1)  # Per architecture spec
```

**Note**: The architecture uses `fallback_action` (what to do if user declines) instead of `ready_for_user`. This is more actionable for the state machine in Story 5-2.

**Edge Case - Empty Output**: When no non-retrievable gaps exist, return:
```python
ClarifierOutput(
    questions=[],
    context_explanation="No clarification needed",
    fallback_action="Proceed with available data"
)
```
This avoids an LLM call when clarification isn't needed.

### Prompt Template

From agent-system-design.md Section 12.8 (aligned with architecture):

```
ROLE: You are a clarification agent that requests missing information from users.

TASK: Generate clear, concise questions to fill information gaps.

=== VOCABULARY ===
{vocabulary}

=== INPUT ===
Original query: {original_query}
Gaps to address: {formatted_gaps}
What we've already searched: {retrieval_history}
Previous clarifications asked: {previous_clarifications}

=== RULES ===

1. Only ask about gaps that cannot be retrieved from stored data
2. Don't re-ask questions the user has already answered
3. Use domain-appropriate terminology from vocabulary
4. Keep questions concise and specific
5. Offer multiple-choice options when applicable
6. Explain WHY you're asking (context_explanation)
7. Maximum 3 questions per interaction

=== QUESTION GUIDELINES ===

Good: "What time did this happen?" (specific, actionable)
Bad: "Can you tell me more?" (vague, unhelpful)

Good: "Were you feeling tired or energized?" (options provided)
Bad: "How were you feeling?" (too open-ended)

=== GAP TYPES YOU SHOULD ASK ABOUT ===

- SUBJECTIVE: Current feelings, preferences, goals that only the user knows
- CLARIFICATION: Ambiguous parts of the query that need clarification

=== GAP TYPES YOU SHOULD NOT ASK ABOUT ===

- TEMPORAL, TOPICAL, CONTEXTUAL: These can be retrieved from stored data

=== FALLBACK ACTION ===

Provide a fallback_action describing what can still be done if the user
declines to answer the questions. Example: "Provide a general answer based
on available data" or "Explain common patterns without personalization"

=== OUTPUT (JSON) ===
{ClarifierOutput.model_json_schema()}
```

### Project Structure Notes

- File: `packages/quilto/quilto/agents/clarifier.py`
- Tests: `packages/quilto/tests/test_clarifier.py` (follows existing pattern: test_analyzer.py, test_synthesizer.py, etc.)
- This is **Quilto framework** code (domain-agnostic)
- Uses same patterns as all other agents

### Testing Standards (from project-context.md)

- **Boundary tests:** Test empty gaps list, min_length=1 constraints
- **Empty vs None:** Test both `None` and `""` for optional string fields
- **options field:** Test `options=None` and `options=[]` both valid (per architecture)
- **ConfigDict:** Use `model_config = ConfigDict(strict=True)` for all models
- **All exports:** Verify importable from `quilto.agents`
- **Mock LLM:** Use mock_llm fixture for unit tests
- **Integration:** Run `make test-ollama` to verify with real LLM
- **Required string fields:** Use `Field(min_length=1)` for required strings (question, original_query, gap_addressed, context_explanation, fallback_action)

### Implementation Checklist (Validation-Triggered)

Before implementation, verify these patterns from existing agents:

| Pattern | Example From | Apply To Clarifier |
|---------|--------------|-------------------|
| Agent class docstring with example | `analyzer.py:20-51` | Copy structure |
| `_format_*` helper methods | `synthesizer.py:57-129` | Create similar |
| Empty input validation | `evaluator.py:256-259` | Add to `clarify()` |
| Mock LLM test fixture | `test_analyzer.py` | Use same fixture |
| Structured output via `complete_structured` | `analyzer.py:326-330` | Same pattern |

### Previous Story Learnings (Epic 4)

From Epic 4 Retrospective:
1. **Verdict-last pattern prevents premature commitment** - Prompt ordering matters
2. **Real usage reveals gaps** - manual_test.py caught retrieval strategy issue
3. **Domain expertise integration works** - Analyzer and Evaluator use domain knowledge

From Story 4-3 (Evaluator):
1. **Four-dimension evaluation provides robust quality gates**
2. **Pyright/Pydantic `default_factory` needs `# pyright: ignore` comments**

From Story 3-5 (completed as prerequisite):
1. **Date-range retrieval is now default** - This helps Clarifier by ensuring proper retrieval before asking

### Epic 4 Retrospective Action Items

- **Story 3.5 completed** - Retrieval strategy ordering fixed before Epic 5
- **Dependencies verified** - Analyzer gap detection ready for Clarifier

### Relationship to Other Stories

- **Story 5-1 (this):** Clarifier agent implementation (standalone)
- **Story 5-2:** WAIT_USER state (integrates with Clarifier)
- **Story 5-3:** Correction flow (separate flow, uses Parser)
- **Story 5-4:** Fitness clarification patterns (domain-specific, builds on 5-1)

The Clarifier agent is implemented first as a standalone agent. The state machine integration (CLARIFY → WAIT_USER transition) is handled in Story 5-2.

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 5.1]
- [Source: _bmad-output/planning-artifacts/agent-system-design.md#Section 11.8 Clarifier Agent Interface]
- [Source: _bmad-output/planning-artifacts/agent-system-design.md#Section 7.3 Question 3: EXPAND vs CLARIFY]
- [Source: _bmad-output/planning-artifacts/agent-system-design.md#Section 12.8 Clarifier Prompt]
- [Source: packages/quilto/quilto/agents/analyzer.py] - Pattern reference
- [Source: packages/quilto/quilto/agents/synthesizer.py] - Pattern reference
- [Source: packages/quilto/quilto/agents/models.py] - Gap, GapType models to reuse
- [Source: _bmad-output/project-context.md#Common Mistakes to Avoid]
- [Source: _bmad-output/implementation-artifacts/epic-4/retro-2026-01-14.md] - Epic 4 learnings

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

N/A

### Completion Notes List

1. Implemented ClarifierAgent with full LLMClient pattern matching other agents (Router, Parser, Planner, Retriever, Analyzer, Synthesizer, Evaluator)
2. Created 3 Pydantic models: ClarificationQuestion, ClarifierInput, ClarifierOutput
3. `filter_non_retrievable_gaps` correctly filters to SUBJECTIVE and CLARIFICATION gap types only
4. Max 3 questions per interaction enforced via post-processing
5. Empty/whitespace query validation raises ValueError
6. No LLM call when no non-retrievable gaps exist (early return)
7. All 55 unit tests pass (53 executed + 2 integration skipped without --use-real-ollama)
8. Integration tests with real Ollama pass (via make test-ollama)
9. Added Clarifier to manual_test.py - runs after Analyzer when non-retrievable gaps exist

### File List

- `packages/quilto/quilto/agents/models.py` - Added ClarificationQuestion, ClarifierInput, ClarifierOutput models
- `packages/quilto/quilto/agents/clarifier.py` - New ClarifierAgent implementation
- `packages/quilto/quilto/agents/__init__.py` - Export ClarifierAgent and models
- `packages/quilto/tests/test_clarifier.py` - Comprehensive unit tests (55 tests)
- `scripts/manual_test.py` - Added ClarifierAgent integration

### Change Log

| Date | Change | Author |
|------|--------|--------|
| 2026-01-14 | Initial implementation: ClarifierAgent, models, tests, exports | Dev Agent |
| 2026-01-14 | Code review fixes: Fixed pyright errors in manual_test.py (redundant None checks), added MAX_QUESTIONS constant | Code Review |
