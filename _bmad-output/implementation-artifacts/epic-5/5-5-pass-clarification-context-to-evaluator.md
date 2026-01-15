# Story 5.5: Pass Clarification Context to Evaluator

Status: ready-for-dev

<!-- Hotfix story created from Epic 5 Retrospective -->

## Story

As a **Quilto developer**,
I want the **Evaluator to receive user clarification context**,
so that **it can properly assess responses that incorporate user-provided information**.

## Background (From Retrospective)

**Discovery:** During Epic 5 retrospective, manual testing revealed that the Evaluator agent incorrectly flags valid responses as "insufficient" when clarification context was gathered.

**Example from manual_test.log:**
1. Clarifier asked: "What is your current flat-bench press 1RM?"
2. User answered: "Haven't measured yet. 60kg 10 reps so far."
3. Synthesizer correctly used this to estimate ~80kg 1RM
4. Evaluator flagged: "Speculative estimate of 1RM not grounded in user's recorded lifts"
5. Evaluator suggested: "Ask the user for their current flat-bench max" - **but we already asked!**

**Root Cause:** `EvaluatorInput` model doesn't include `user_responses` field, so Evaluator has no way to know that clarification happened.

## Acceptance Criteria

1. **Given** the Evaluator receives a response that uses clarification answers
   **When** it evaluates accuracy
   **Then** it considers user-provided answers as valid evidence (not speculation)

2. **Given** `EvaluatorInput` model
   **When** updated
   **Then** it includes `user_responses: dict[str, str] = {}` field

3. **Given** `Evaluator.build_prompt()` method
   **When** user_responses is non-empty
   **Then** prompt includes a "USER CLARIFICATION CONTEXT" section explaining what was asked and answered

4. **Given** evaluation rules that suggest "ask the user"
   **When** that information was already provided via clarification
   **Then** Evaluator does NOT flag as missing or suggest asking again

5. **Given** the Evaluator prompt
   **When** user_responses is provided
   **Then** prompt explicitly states: "The following information was gathered directly from the user and should be treated as authoritative"

6. **Given** backward compatibility
   **When** user_responses is empty or not provided
   **Then** Evaluator behaves exactly as before (no regression)

7. **Given** manual_test.py
   **When** running the same query that exposed this bug
   **Then** Evaluator no longer incorrectly flags responses using clarification data

## Tasks / Subtasks

- [ ] Task 1: Update EvaluatorInput model (AC: #2, #6)
  - [ ] 1.1: Add `user_responses: dict[str, str] = {}` field to `EvaluatorInput` in `packages/quilto/quilto/agents/models.py`
  - [ ] 1.2: Add docstring explaining this maps `gap_addressed` to user's answer
  - [ ] 1.3: Ensure default empty dict for backward compatibility

- [ ] Task 2: Update Evaluator.build_prompt() (AC: #3, #4, #5)
  - [ ] 2.1: Add `_format_user_responses()` helper method
  - [ ] 2.2: Add "USER CLARIFICATION CONTEXT" section when user_responses is non-empty
  - [ ] 2.3: Include instruction: "Treat user-provided answers as authoritative evidence"
  - [ ] 2.4: Include instruction: "Do NOT suggest asking for information the user already provided"
  - [ ] 2.5: Include instruction: "Information derived from user answers is NOT speculation"

- [ ] Task 3: Update Evaluator.evaluate() method (AC: #1)
  - [ ] 3.1: Ensure user_responses is passed to build_prompt()
  - [ ] 3.2: No changes needed to evaluate() logic itself (prompt handles it)

- [ ] Task 4: Update manual_test.py to pass user_responses to Evaluator (AC: #7)
  - [ ] 4.1: After collecting clarification answers, store in a dict
  - [ ] 4.2: Pass `user_responses` to `EvaluatorInput` construction
  - [ ] 4.3: Verify the same query no longer incorrectly fails evaluation

- [ ] Task 5: Create unit tests
  - [ ] 5.1: Test `EvaluatorInput` accepts `user_responses` field
  - [ ] 5.2: Test `EvaluatorInput` works with empty `user_responses` (backward compat)
  - [ ] 5.3: Test `build_prompt()` includes clarification section when provided
  - [ ] 5.4: Test `build_prompt()` omits clarification section when empty
  - [ ] 5.5: Test `_format_user_responses()` helper formats correctly
  - [ ] 5.6: Test evaluator with mock LLM doesn't flag user-provided info as speculative

- [ ] Task 6: Run validation
  - [ ] 6.1: Run `make check` (lint + typecheck)
  - [ ] 6.2: Run `make validate` (full validation)
  - [ ] 6.3: Run `make test-ollama` (integration tests with real Ollama)
  - [ ] 6.4: Run manual_test.py with the problematic query to verify fix

## Dev Notes

### Architecture Patterns

- **Location:** `packages/quilto/quilto/agents/models.py` and `packages/quilto/quilto/agents/evaluator.py`
- **Pattern:** Follow existing helper method patterns (`_format_context_entries()`, `_format_evaluation_rules()`)
- **Framework:** This is Quilto framework code, not Swealog-specific

### Current EvaluatorInput Model (Before Fix)

```python
class EvaluatorInput(BaseModel):
    """Input for EvaluatorAgent."""
    model_config = ConfigDict(strict=True)

    query: str = Field(min_length=1)
    response: str = Field(min_length=1)
    context_entries: list[Entry]
    evaluation_rules: list[str]
    expertise: str
    # MISSING: user_responses!
```

### Updated EvaluatorInput Model (After Fix)

```python
class EvaluatorInput(BaseModel):
    """Input for EvaluatorAgent."""
    model_config = ConfigDict(strict=True)

    query: str = Field(min_length=1)
    response: str = Field(min_length=1)
    context_entries: list[Entry]
    evaluation_rules: list[str]
    expertise: str
    user_responses: dict[str, str] = {}
    """User's answers to clarification questions.

    Maps gap_addressed (question topic) to the user's answer.
    Example: {"Current 1RM": "60kg for 10 reps", "Training days": "4 days"}

    When non-empty, Evaluator should treat this as authoritative information
    and NOT flag responses using this data as speculative.
    """
```

### Prompt Enhancement

Add this section to `build_prompt()` when `user_responses` is non-empty:

```
=== USER CLARIFICATION CONTEXT ===

The following information was gathered directly from the user via clarification questions.
This information is AUTHORITATIVE and should NOT be flagged as speculation.

{formatted_user_responses}

IMPORTANT EVALUATION RULES FOR CLARIFICATION CONTEXT:
1. Information derived from user answers is NOT speculation - it is user-provided data
2. Do NOT suggest "ask the user" for information already provided above
3. Treat user answers as valid evidence, equivalent to stored log entries
4. The response correctly uses this context if it references or builds upon these answers
```

### Helper Method Pattern

Follow existing patterns from `evaluator.py`:

```python
def _format_user_responses(self, user_responses: dict[str, str]) -> str:
    """Format user responses for the prompt.

    Args:
        user_responses: Map of gap_addressed to user's answer.

    Returns:
        Formatted string showing what the user provided.
    """
    if not user_responses:
        return ""

    lines: list[str] = []
    for gap, answer in user_responses.items():
        lines.append(f"- {gap}: {answer}")
    return "\n".join(lines)
```

### Testing Standards (from project-context.md)

- **ConfigDict:** Use `model_config = ConfigDict(strict=True)` for all models
- **Boundary tests:** Test empty dict, single response, multiple responses
- **Backward compatibility:** Test that empty user_responses works exactly as before
- **Integration:** Run manual_test.py to verify real-world fix

### Relationship to Other Stories

- **Story 5-1 (done):** ClarifierAgent - produces `user_responses` dict
- **Story 5-2 (done):** WAIT_USER state - captures `user_responses` in SessionState
- **Story 5-3 (done):** Correction flow - separate concern
- **Story 5-4 (done):** Fitness clarification patterns - produces better questions
- **Story 5-5 (this):** Evaluator context - consumes `user_responses` from clarification

### manual_test.py Update

The script already collects answers in a dict format. Need to pass this to EvaluatorInput:

```python
# After collecting clarification answers
user_responses = {
    q.gap_addressed: answer
    for q, answer in zip(clarifier_output.questions, collected_answers)
}

# Pass to Evaluator
evaluator_input = EvaluatorInput(
    query=query,
    response=synthesizer_output.response,
    context_entries=retrieved_entries,
    evaluation_rules=evaluation_rules,
    expertise=merged_expertise,
    user_responses=user_responses,  # NEW
)
```

### References

- [Source: manual_test.log] - Bug discovery
- [Source: packages/quilto/quilto/agents/models.py] - EvaluatorInput model
- [Source: packages/quilto/quilto/agents/evaluator.py] - Evaluator implementation
- [Source: scripts/manual_test.py] - Manual testing script
- [Source: _bmad-output/implementation-artifacts/epic-5/5-1-implement-clarifier-agent.md] - Clarifier outputs user_responses format
- [Source: _bmad-output/implementation-artifacts/epic-5/5-2-implement-wait-user-state.md] - SessionState stores user_responses

## Dev Agent Record

### Agent Model Used

(To be filled by dev agent)

### Completion Notes List

(To be filled after implementation)

### File List

**Expected files to modify:**
- `packages/quilto/quilto/agents/models.py` - Add user_responses to EvaluatorInput
- `packages/quilto/quilto/agents/evaluator.py` - Update build_prompt() with clarification context
- `scripts/manual_test.py` - Pass user_responses to Evaluator
- `packages/quilto/tests/test_evaluator.py` - Add tests for user_responses handling
