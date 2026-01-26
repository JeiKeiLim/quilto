# Story 13.5: Improve Intent Classification for Goal Statements

Status: done

## Story

As a **Quilto user**,
I want **goal statements like "I want to run a marathon" to be treated as implicit queries**,
So that **I receive guidance without needing to explicitly ask a question**.

## Background

**Origin:** Dogfooding Iteration 3 (Epic 13)
**Source:** `tests/eval/feedback/archive/iter-002/analysis.md` - Pattern 11: Goal Statements Treated as LOG Only
**Priority:** Medium | **Effort:** Small (1-2 hours)
**Type:** Enhancement - Router classification logic

**Key Evidence (Record `8628f945`):**
- User input: "I'd like to run a full marathon"
- Router output: Treated as LOG only (no guidance provided)
- User feedback: "I queried `I'd like to go run a full marathon` and it assumed it was log and processed parsing only. Which is a bit gray area since this could also be interpreted as a query for suggestion."

**Current Behavior:**
The Router classifies "I'd like to run a marathon" as LOG (declarative statement recording a goal), missing the implicit query intent ("how do I achieve this?").

**Desired Behavior:**
Goal statements should be classified as BOTH:
- `log_portion`: "I'd like to run a full marathon" (the goal is logged)
- `query_portion`: "How do I prepare to run a full marathon?" (implicit question inferred)

## Acceptance Criteria

1. **Given** input "I'd like to run a full marathon"
   **When** Router classifies input_type
   **Then** it is classified as BOTH (log of goal + implicit query for guidance)

2. **Given** input starting with "I want to..." or "I'd like to..."
   **When** no explicit question is present
   **Then** Router includes query_portion with the implied question (e.g., "How do I achieve [goal]?")

3. **Given** a pure declarative LOG without goal intent (e.g., "Ran 5k today")
   **When** Router classifies
   **Then** it remains classified as LOG (no false positives)

4. **Given** goal statements in Korean (e.g., "마라톤을 완주하고 싶어")
   **When** Router classifies input_type
   **Then** it is classified as BOTH with appropriate query_portion in the same language

5. **Given** explicit question with goal context (e.g., "I want to run a marathon, how do I start?")
   **When** Router classifies
   **Then** it is classified as BOTH with both portions correctly extracted (no regression)

## Tasks / Subtasks

- [x] Task 1: Update Router prompt to recognize goal statement patterns (AC: #1, #2, #4)
  - [x] 1.1: Add GOAL_STATEMENT pattern recognition to classification rules
  - [x] 1.2: Add guidance: Goal statements ("I want to...", "I'd like to...", "My goal is to...") imply seeking guidance
  - [x] 1.3: Add instruction to generate implicit query_portion for goal statements
  - [x] 1.4: Ensure prompt handles both English and Korean goal patterns

- [x] Task 2: Add unit tests for goal statement classification (AC: #1, #2, #3, #5)
  - [x] 2.1: Create new `TestGoalStatementClassification` class (follow `TestBothClassification` pattern at lines 983-1139)
  - [x] 2.2: Test "I'd like to run a marathon" → BOTH with query_portion
  - [x] 2.3: Test "I want to lose 10kg" → BOTH with query_portion
  - [x] 2.4: Test "Ran 5k today" → LOG (no false positive)
  - [x] 2.5: Test "I just ran 5k" → LOG (edge case: past tense with recent time marker)
  - [x] 2.6: Test "I want to run a marathon, how do I start?" → BOTH (no regression)
  - [x] 2.7: Test Korean goal statement "마라톤을 완주하고 싶어" → BOTH with query_portion in Korean

- [x] Task 3: Add integration test with real Ollama (optional) (AC: #1)
  - [x] 3.1: Mark test with `@pytest.mark.ollama_integration`
  - [x] 3.2: Verify actual LLM behavior matches expected BOTH classification

- [x] Task 4: Run validation
  - [x] 4.1: Run `make check` (lint + typecheck)
  - [x] 4.2: Run `make validate` (full validation)

## Dev Notes

### Implementation Approach

**File: `packages/quilto/quilto/agents/router.py`**

Update the `build_prompt()` method to add goal statement recognition. The key change is in the classification rules section.

**Current prompt snippet (lines 66-78 in router.py):**
```python
=== CLASSIFICATION RULES ===

INPUT TYPES:
- LOG: Declarative statements recording activities, events, or observations
- QUERY: Questions seeking information, insights, or recommendations
- BOTH: Input that logs something AND asks a question
- CORRECTION: User fixing previously recorded information ("actually", "I meant", "that was wrong")

SIGNALS:
- Question words (why, how, what, when, which) → QUERY
- Question mark → QUERY
- Past tense declarative → LOG
- Correction language → CORRECTION
```

**Updated prompt section to add:**
```python
=== CLASSIFICATION RULES ===

INPUT TYPES:
- LOG: Declarative statements recording activities, events, or observations
- QUERY: Questions seeking information, insights, or recommendations
- BOTH: Input that logs something AND asks a question
- CORRECTION: User fixing previously recorded information ("actually", "I meant", "that was wrong")

SIGNALS:
- Question words (why, how, what, when, which) → QUERY
- Question mark → QUERY
- Past tense declarative → LOG
- Correction language → CORRECTION

GOAL STATEMENTS (classify as BOTH):
- Patterns: "I want to...", "I'd like to...", "My goal is...", "I'm trying to...", "I hope to..."
- Korean patterns: "~하고 싶어", "~하고 싶다", "~목표는", "~하려고 해"
- These imply implicit query seeking guidance on achieving the goal
- For BOTH: log_portion = the goal statement, query_portion = inferred question about achieving it
- Example: "I want to run a marathon" → log_portion="I want to run a marathon", query_portion="How do I prepare to run a marathon?"
```

### Pattern Recognition Examples

| Input | Classification | log_portion | query_portion |
|-------|---------------|-------------|---------------|
| "I'd like to run a full marathon" | BOTH | "I'd like to run a full marathon" | "How do I prepare to run a full marathon?" |
| "I want to lose 10kg" | BOTH | "I want to lose 10kg" | "How can I lose 10kg?" |
| "My goal is to bench 100kg" | BOTH | "My goal is to bench 100kg" | "How do I reach a 100kg bench press?" |
| "Ran 5k today" | LOG | N/A | N/A |
| "How do I run faster?" | QUERY | N/A | N/A |

### Distinguishing Goals from Pure Logs

**Goal indicators (→ BOTH):**
- Future-oriented desire: "want to", "would like to", "hope to", "trying to"
- Target achievement: "goal is to", "aiming for", "working toward"
- Aspiration: "dream of", "plan to", "intend to"

**Pure log indicators (→ LOG):**
- Past tense completed action: "ran", "lifted", "ate"
- Present tense status: "feeling good", "energy is high"
- No aspirational language

### Edge Cases

| Case | Handling |
|------|----------|
| "I ran a marathon" (past) | LOG - completed action, not a goal |
| "I want to run a marathon" (future goal) | BOTH - goal seeking guidance |
| "I'm running tomorrow" (planned action) | LOG - concrete plan, not seeking advice |
| "I'd like to improve my running" (vague goal) | BOTH - seeking improvement guidance |
| "I just ran 5k" (recent past) | LOG - past action with time marker, not a goal |
| Empty goal (just "I want to") | LOG - too vague for meaningful query inference |

### File Changes Summary

| File | Change Type | Lines Impact |
|------|-------------|--------------|
| `packages/quilto/quilto/agents/router.py` | MODIFY | ~15 lines (add GOAL STATEMENTS section after line 78) |
| `packages/quilto/tests/test_router.py` | MODIFY | ~80 lines (new TestGoalStatementClassification class) |

### Validation Checklist

Before marking complete:
- [x] `make check` passes (lint + typecheck)
- [x] `make validate` passes (all unit tests)
- [x] Goal statement "I'd like to run a marathon" → BOTH
- [x] Pure log "Ran 5k today" → LOG (no regression)
- [x] Explicit question "How do I...?" → QUERY (no regression)
- [x] BOTH with explicit question still works (no regression)
- [x] Korean goal patterns handled correctly

### What This Does NOT Do

- **No Planner changes:** Planner receives BOTH with query_portion, handles normally
- **No Analyzer changes:** Query flow proceeds with inferred query_portion
- **No new fields:** Uses existing RouterOutput structure (log_portion, query_portion)
- **No sentiment analysis:** Pure pattern matching in prompt, not emotional analysis

### Previous Story Learnings (Story 13.4)

From Story 13.4 (Fix Clarification Flow Routing):
- Router already handles BOTH classification correctly when explicit portions exist
- Pipeline properly processes BOTH inputs through both log and query flows
- Mocking approach: Use `create_mock_llm_client(response_json)` pattern for unit tests

### References

| Source | Content |
|--------|---------|
| `tests/eval/feedback/archive/iter-002/records/2026-01-26_8628f945.json` | Evidence of goal statement misclassification |
| `packages/quilto/quilto/agents/router.py:45-124` | Current Router prompt (build_prompt method) |
| `packages/quilto/quilto/agents/router.py:66-78` | Classification rules section to modify |
| `packages/quilto/quilto/agents/models.py:108-168` | RouterInput/RouterOutput models |
| `packages/quilto/tests/test_router.py:983-1139` | TestBothClassification class (pattern to follow for new tests) |
| `packages/quilto/tests/test_router.py:41-63` | create_mock_llm_client helper function |
| `_bmad-output/implementation-artifacts/epic-13/13-4-fix-clarification-flow-routing.md` | Previous story for context |

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

N/A - All tests passing on first run.

### Completion Notes List

1. Added GOAL STATEMENTS section to Router prompt (router.py:80-86)
   - English patterns: "I want to...", "I'd like to...", "My goal is...", "I'm trying to...", "I hope to..."
   - Korean patterns: "~하고 싶어", "~하고 싶다", "~목표는", "~하려고 해"
   - Instructions for generating implicit query_portion
   - Explicit note that past completed actions are NOT goal statements

2. Added TestGoalStatementClassification class (test_router.py:1387-1576)
   - 8 unit tests covering all AC requirements
   - Tests for English goal patterns (marathon, weight loss, bench 100kg, improve cardio)
   - Tests for Korean goal pattern (마라톤을 완주하고 싶어)
   - Tests for no false positives (pure log "Ran 5k today", past tense "I just ran 5k")
   - Test for regression (explicit question with goal context)

3. Added TestGoalStatementIntegration class (test_router.py:1579-1620)
   - Integration test with real Ollama for marathon goal statement

4. Validation: `make validate` passed - 1905 tests passed, 101 skipped

### File List

Files modified:
- `packages/quilto/quilto/agents/router.py` - Added GOAL STATEMENTS section to prompt (lines 80-86, 7 lines added)
- `packages/quilto/tests/test_router.py` - Added TestGoalStatementClassification (lines 1386-1594) and TestGoalStatementIntegration (lines 1596-1623) classes (237 lines added)

### Known Issues / Future Improvements

**[TECH-DEBT] Language-specific prompt patterns don't scale**
- Location: `router.py:82` - Korean patterns `~하고 싶어`, `~하고 싶다`, `~목표는`, `~하려고 해`
- Problem: Adding explicit patterns for each language (Korean, Japanese, Chinese, Spanish, etc.) is not maintainable
- Recommendation: Remove Korean-specific patterns and rely on LLM generalization from English examples
- The LLM should understand the *concept* of goal statements and apply it across languages it knows
- English patterns serve as conceptual examples, not exhaustive rules
- Action: Consider removing Korean patterns from prompt; keep Korean test case to verify multilingual handling works via LLM generalization

