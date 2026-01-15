# Story 5.5: Pass Clarification Context to Evaluator

Status: done

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

- [x] Task 1: Update EvaluatorInput model (AC: #2, #6)
  - [x] 1.1: Add `user_responses: dict[str, str] = {}` field to `EvaluatorInput` in `packages/quilto/quilto/agents/models.py`
  - [x] 1.2: Add docstring explaining this maps `gap_addressed` to user's answer
  - [x] 1.3: Ensure default empty dict for backward compatibility

- [x] Task 2: Update Evaluator.build_prompt() (AC: #3, #4, #5)
  - [x] 2.1: Add `_format_user_responses()` helper method
  - [x] 2.2: Add "USER CLARIFICATION CONTEXT" section when user_responses is non-empty
  - [x] 2.3: Include instruction: "Treat user-provided answers as authoritative evidence"
  - [x] 2.4: Include instruction: "Do NOT suggest asking for information the user already provided"
  - [x] 2.5: Include instruction: "Information derived from user answers is NOT speculation"

- [x] Task 3: Update Evaluator.evaluate() method (AC: #1)
  - [x] 3.1: Ensure user_responses is passed to build_prompt()
  - [x] 3.2: No changes needed to evaluate() logic itself (prompt handles it)

- [x] Task 4: Update manual_test.py to pass user_responses to Evaluator (AC: #7)
  - [x] 4.1: After collecting clarification answers, store in a dict
  - [x] 4.2: Pass `user_responses` to `EvaluatorInput` construction
  - [x] 4.3: Verify the same query no longer incorrectly fails evaluation

- [x] Task 5: Create unit tests
  - [x] 5.1: Test `EvaluatorInput` accepts `user_responses` field
  - [x] 5.2: Test `EvaluatorInput` works with empty `user_responses` (backward compat)
  - [x] 5.3: Test `build_prompt()` includes clarification section when provided
  - [x] 5.4: Test `build_prompt()` omits clarification section when empty
  - [x] 5.5: Test `_format_user_responses()` helper formats correctly
  - [x] 5.6: Test evaluator with mock LLM doesn't flag user-provided info as speculative

  **Note:** Check if `packages/quilto/tests/test_evaluator.py` exists. If not, create it following the pattern from `test_clarification_patterns.py` (Story 5-4). Add user_responses tests to the evaluator test file.

- [x] Task 6: Run validation
  - [x] 6.1: Run `make check` (lint + typecheck)
  - [x] 6.2: Run `make validate` (full validation)
  - [x] 6.3: Run `make test-ollama` (integration tests with real Ollama)
  - [x] 6.4: Run manual_test.py with the problematic query to verify fix

## Dev Notes

### Architecture Patterns

- **Location:** `packages/quilto/quilto/agents/models.py` and `packages/quilto/quilto/agents/evaluator.py`
- **Pattern:** Follow existing helper method patterns (`_format_context_entries()`, `_format_evaluation_rules()`)
- **Framework:** This is Quilto framework code, not Swealog-specific

### Pattern Reference from Story 5-4 (CRITICAL)

This story follows the **EXACT same pattern** as Story 5-4 (add-fitness-clarification-patterns):

| Story 5-4 | Story 5-5 |
|-----------|-----------|
| Add `clarification_patterns` to `ClarifierInput` | Add `user_responses` to `EvaluatorInput` |
| Add `_format_clarification_patterns()` helper | Add `_format_user_responses()` helper |
| Add `=== DOMAIN-SPECIFIC PATTERNS ===` section | Add `=== USER CLARIFICATION CONTEXT ===` section |

**Reference:** `_bmad-output/implementation-artifacts/epic-5/5-4-add-fitness-clarification-patterns.md`

### Prompt Insertion Point

Add the `=== USER CLARIFICATION CONTEXT ===` section in `build_prompt()`:
- **AFTER:** `=== ANALYSIS RESULTS ===` section (around line 206-207)
- **BEFORE:** `=== INPUT ===` section (around line 209)

This ensures the Evaluator sees clarification context alongside analysis results before evaluating the response.

### EvaluatorInput Model Change

**ADD this field** to `EvaluatorInput` in `models.py` (after `previous_feedback` field, around line 772):

```python
user_responses: dict[str, str] = Field(default_factory=dict)
"""User's answers to clarification questions.

Maps gap_addressed (question topic) to the user's answer.
Example: {"Current 1RM": "60kg for 10 reps", "Training days": "4 days"}

When non-empty, Evaluator should treat this as authoritative information
and NOT flag responses using this data as speculative.
"""
```

**Note:** Use `Field(default_factory=dict)` to match existing patterns like `previous_feedback: list[EvaluationFeedback] = Field(default_factory=list)`

### Prompt Enhancement (EXACT TEXT TO USE)

Add this section to `build_prompt()` when `user_responses` is non-empty.
**Copy this text verbatim** (only `{formatted_user_responses}` is a variable):

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

**IMPORTANT:** The existing `collect_clarification_answers()` function (line 531-606) returns `dict[str, str]` mapping **question text** to **answer**. We need to convert this to `gap_addressed` → `answer` format for the Evaluator.

```python
# After collecting clarification answers (line ~1036-1040)
# collect_clarification_answers returns: {question_text: answer}
raw_answers = collect_clarification_answers(clarifier_output)

# Convert to format needed by Evaluator: {gap_addressed: answer}
user_responses = {
    q.gap_addressed: raw_answers.get(q.question, "")
    for q in clarifier_output.questions
    if q.question in raw_answers
}

# Pass to Evaluator (in run_evaluator call around line 1063)
evaluator_input = EvaluatorInput(
    query=query,
    response=synthesizer_output.response,
    analysis=analyzer_output,
    entries_summary=entries_summary,
    evaluation_rules=evaluation_rules,
    attempt_number=attempt_number,
    previous_feedback=previous_feedback or [],
    user_responses=user_responses,  # NEW - pass clarification context
)
```

**Note:** The conversion from `{question: answer}` to `{gap_addressed: answer}` is necessary because:
1. `collect_clarification_answers()` uses question text as keys
2. `EvaluatorInput.user_responses` expects `gap_addressed` as keys for semantic meaning

### References

- [Source: manual_test.log] - Bug discovery
- [Source: packages/quilto/quilto/agents/models.py] - EvaluatorInput model
- [Source: packages/quilto/quilto/agents/evaluator.py] - Evaluator implementation
- [Source: scripts/manual_test.py] - Manual testing script
- [Source: _bmad-output/implementation-artifacts/epic-5/5-1-implement-clarifier-agent.md] - Clarifier outputs user_responses format
- [Source: _bmad-output/implementation-artifacts/epic-5/5-2-implement-wait-user-state.md] - SessionState stores user_responses

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Completion Notes List

1. **EvaluatorInput Model Updated**: Added `user_responses: dict[str, str] = Field(default_factory=dict)` field with comprehensive docstring explaining usage. Default empty dict ensures backward compatibility (AC #2, #6).

2. **_format_user_responses() Helper Added**: New method in EvaluatorAgent that formats user responses as a bullet list for the prompt. Returns empty string when no responses present.

3. **USER CLARIFICATION CONTEXT Section**: Added dynamic section in build_prompt() that appears only when user_responses is non-empty. Includes four key evaluation rules:
   - Information derived from user answers is NOT speculation
   - Do NOT suggest "ask the user" for information already provided
   - Treat user answers as valid evidence
   - The response correctly uses this context if it references these answers

4. **manual_test.py Updated**: Added `build_user_responses_for_evaluator()` helper to convert raw answers (question -> answer) to the format needed by Evaluator (gap_addressed -> answer). Updated both QUERY and BOTH input type handlers to pass user_responses to run_evaluator.

5. **Comprehensive Unit Tests**: Added 16 new tests covering:
   - TestEvaluatorInputUserResponses: 4 tests for model field behavior
   - TestFormatUserResponsesHelper: 3 tests for helper method
   - TestBuildPromptUserResponses: 6 tests for prompt building
   - TestEvaluatorWithUserResponses: 3 tests including integration test with Ollama

6. **All Validation Passed**:
   - `ruff check` on changed files: All checks passed
   - `pyright` on changed files: 0 errors
   - `pytest packages/quilto/tests/test_evaluator.py`: 90 passed, 4 skipped
   - `make test-ollama`: 1143 passed, 4 skipped (full integration suite)

### Code Review (2026-01-15)

**Reviewer:** Amelia (Dev Agent - Claude Opus 4.5)

**Issues Found:** 1 High, 2 Medium, 2 Low

**Fixes Applied:**

1. **[HIGH] Fixed malformed prompt section header** (evaluator.py:245)
   - Changed `=== {entries_text}` to `=== AVAILABLE EVIDENCE ===\n{entries_text}`
   - Updated `_format_entries_summary()` to return raw summary (header now in template)
   - Ensures consistent `=== SECTION NAME ===` formatting across all prompt sections

2. **[MEDIUM] Added debug print for user_responses** (manual_test.py:823-824)
   - Now prints `User responses: N clarification answer(s)` when user_responses is provided
   - Improves debugging visibility when clarification context is passed to Evaluator

3. **[TEST] Updated test_format_entries_summary test** (test_evaluator.py:869-883)
   - Updated to reflect new behavior where header is in template, not helper method

**Not Fixed (Low priority):**
- Variable naming inconsistency `user_responses` vs `user_responses_both` (functional, cosmetic only)
- pyright ignore comment on `user_responses` field (matches existing pattern for `previous_feedback`)

**Post-Review Validation:**
- `ruff check`: All checks passed
- `pyright`: 0 errors
- Unit tests: 90 passed, 4 skipped
- Integration tests: 1143 passed, 4 skipped

### File List

**Files modified:**
- `packages/quilto/quilto/agents/models.py:773-780` - Added user_responses field to EvaluatorInput
- `packages/quilto/quilto/agents/evaluator.py:142` - Updated _format_entries_summary() to return raw summary (code review fix)
- `packages/quilto/quilto/agents/evaluator.py:144-159` - Added _format_user_responses() helper
- `packages/quilto/quilto/agents/evaluator.py:177-193` - Added user_responses_section building logic in build_prompt()
- `packages/quilto/quilto/agents/evaluator.py:245-247` - Fixed prompt template section header formatting (code review fix)
- `scripts/manual_test.py:631-648` - Added build_user_responses_for_evaluator() helper
- `scripts/manual_test.py:787-788` - Updated run_evaluator signature to accept user_responses
- `scripts/manual_test.py:815-816` - Updated EvaluatorInput construction with user_responses
- `scripts/manual_test.py:823-824` - Added debug print for user_responses count (code review fix)
- `scripts/manual_test.py:1030-1039,1066-1068` - Updated QUERY handler to track and pass user_responses
- `scripts/manual_test.py:1157-1166,1197-1199` - Updated BOTH handler to track and pass user_responses
- `packages/quilto/tests/test_evaluator.py:869-883` - Updated test_format_entries_summary test (code review fix)
- `packages/quilto/tests/test_evaluator.py:1552-1838` - Added TestEvaluatorInputUserResponses, TestFormatUserResponsesHelper, TestBuildPromptUserResponses, TestEvaluatorWithUserResponses test classes
