# Story 20.6: Parameterize Context Building with First+Recent Strategy

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **Swealog user with multi-turn sessions**,
I want **context building to preserve my first query even after many turns**,
So that **agents can reference my original intent throughout a long conversation**.

## Acceptance Criteria

1. **Given** `SessionConfig.context_turns = 6` (new default)
   **When** context is built from session history
   **Then** first turn + last (context_turns - 1) turns are included

2. **Given** a session with 8 turns [T1, T2, T3, T4, T5, T6, T7, T8]
   **When** `_build_conversation_context()` is called with `context_turns=6`
   **Then** context includes [T1, T4, T5, T6, T7, T8] (first + last 5)

3. **Given** `context_turns` is not set explicitly
   **When** context is built
   **Then** default value of 6 is used

4. **Given** session has fewer turns than `context_turns`
   **When** context is built
   **Then** all turns are included (no pruning needed)

5. **Given** a user asks "What did I ask for the first time?" after 5+ turns
   **When** Synthesizer generates response
   **Then** response correctly references the first turn content

6. **Given** `context_turns=6` and `max_conversation_turns=20`
   **When** both are configured
   **Then** storage pruning (20 turns) and context building (6 turns) operate independently

## Tasks / Subtasks

- [x] Task 1: Add `context_turns` to SessionConfig (AC: #1, #3)
  - [x] 1.1: Add `context_turns: int = Field(default=6, ge=2)` to SessionConfig in `session/models.py`
  - [x] 1.2: Add docstring explaining this controls context building (separate from storage pruning)
  - [x] 1.3: Ensure ge=2 to guarantee at least first + 1 recent turn

- [x] Task 2: Update `_build_conversation_context()` to use first+recent strategy (AC: #1, #2, #4)
  - [x] 2.1: Replace hardcoded `history[-4:]` with parameterized `context_turns` logic
  - [x] 2.2: Implement: if len(history) > context_turns, use [first] + last (N-1)
  - [x] 2.3: If len(history) <= context_turns, use all turns
  - [x] 2.4: Access config via `self._config.context_turns`

- [x] Task 3: Unit Tests (AC: #1-4)
  - [x] 3.1: Test `_build_conversation_context()` with history > context_turns (verify first+recent)
  - [x] 3.2: Test `_build_conversation_context()` with history < context_turns (all included)
  - [x] 3.3: Test `_build_conversation_context()` with history == context_turns (all included)
  - [x] 3.4: Test default `context_turns=6` when not explicitly set
  - [x] 3.5: Test context_turns and max_conversation_turns are independent (AC: #6)

- [x] Task 4: Update Existing Tests (if needed)
  - [x] 4.1: Review tests in `test_session.py` that may rely on hardcoded 4-turn behavior
  - [x] 4.2: Update any affected tests to use new parameterized behavior

- [x] Task 5: Dogfooding Verification (manual - requires LLM) (AC: #5)
  - [x] 5.1: Start new session with >6 turns, ask "What did I ask first?"
  - [x] 5.2: Verify response references the actual first query, not a middle turn
  - [x] 5.3: Record feedback JSON with session_id for evidence

## Dev Notes

### Problem Statement

**Evidence:** Epic 20 Retrospective (`epic-20-retro-2026-01-29.md` lines 57-85)
- Query: "What did I ask for the first time?"
- Expected: Original upperbody strength question (first turn)
- Got: "Can you give me workout plan in detail?" (recent turn)
- User feedback: "it does have session context but only the last one"

**Root Cause:**
- Storage pruning: Uses `first + last (N-1)` strategy, parameterized via `max_conversation_turns=20`
- Context building: Uses `last 4 turns` only, hardcoded at line 145 in `session.py`
- Mismatch: Storage is smart (preserves first turn), context building is dumb (loses first turn)

### CRITICAL: Avoid Existing Pattern Duplication

The first+recent pruning logic already exists for storage in `session.py:109-114`. Reuse that pattern - do NOT reinvent it:

```python
# Existing storage pruning (lines 109-114) - REFERENCE THIS PATTERN:
max_turns = self._config.max_conversation_turns
if len(self._data.conversation) > max_turns:
    first_turn = self._data.conversation[0]
    recent_turns = self._data.conversation[-(max_turns - 1) :]
    self._data.conversation = [first_turn] + recent_turns
```

### Code Locations

**session/models.py (`packages/quilto/quilto/session/models.py`):**
- `SessionConfig` class at line 54-64
- Current field: `max_conversation_turns: int = Field(default=20, ge=2)` at line 64
- Add `context_turns` field AFTER `max_conversation_turns`
- Update docstring to describe both fields

**session/session.py (`packages/quilto/quilto/session/session.py`):**
- `_build_conversation_context()` method at lines 131-147
- Current hardcoded logic at line 145: `recent = history[-4:]`
- Replace with parameterized first+recent strategy using `self._config.context_turns`

**Existing storage pruning (REFERENCE - DO NOT DUPLICATE):**
- `add_turn()` method at lines 78-118
- First+recent pruning at lines 109-114 (use same pattern)

### Implementation Pattern

**Current (session.py lines 131-147):**
```python
def _build_conversation_context(self) -> str | None:
    """Build conversation context string from history.

    Uses the last 4 turns formatted as "{role}: {content}".
    This respects the 20-turn overall limit via pruning.

    Returns:
        Formatted context string, or None if no history.
    """
    history = self.get_history()
    if not history:
        return None

    # Take last 4 turns for context
    recent = history[-4:]  # <-- HARDCODED - THIS LOSES FIRST TURN
    lines = [f"{turn.role}: {turn.content}" for turn in recent]
    return "\n".join(lines)
```

**Target:**
```python
def _build_conversation_context(self) -> str | None:
    """Build conversation context string from history.

    Uses first turn + last (context_turns - 1) turns to preserve
    original intent while including recent context.

    Returns:
        Formatted context string, or None if no history.
    """
    history = self.get_history()
    if not history:
        return None

    context_turns = self._config.context_turns

    if len(history) <= context_turns:
        selected = history
    else:
        # First turn + last (N-1) turns - same strategy as storage pruning
        first_turn = history[0]
        recent_turns = history[-(context_turns - 1) :]
        selected = [first_turn] + recent_turns

    lines = [f"{turn.role}: {turn.content}" for turn in selected]
    return "\n".join(lines)
```

**CRITICAL:** The ` :]` spacing follows project ruff formatting convention (see line 113 in session.py).

### SessionConfig Update

**Current (lines 54-64):**
```python
class SessionConfig(BaseModel):
    """Configuration for session behavior.

    Attributes:
        max_conversation_turns: Maximum turns to keep (default 20).
            When exceeded, keeps first turn + last (N-1) turns.
    """

    model_config = ConfigDict(strict=True)

    max_conversation_turns: int = Field(default=20, ge=2)
```

**Target:**
```python
class SessionConfig(BaseModel):
    """Configuration for session behavior.

    Attributes:
        max_conversation_turns: Maximum turns to keep in storage (default 20).
            When exceeded, keeps first turn + last (N-1) turns.
        context_turns: Maximum turns to include in conversation context (default 6).
            When building context for agents, uses first turn + last (N-1) turns.
            Separate from storage pruning to allow fine-grained control.
    """

    model_config = ConfigDict(strict=True)

    max_conversation_turns: int = Field(default=20, ge=2)
    context_turns: int = Field(default=6, ge=2)
```

### Previous Story Intelligence

**Story 20.5 Learnings (RELEVANT TO THIS STORY):**
- Context propagation now passes `conversation_context` to all agents (Router, Planner, Analyzer, Synthesizer, Evaluator, Observer)
- All agents have updated prompts to use context effectively
- Integration tests verify context is passed correctly
- The `_build_conversation_context()` method is called from `session.process()` at line 197

**Story 20.5 File Changes (Reference for consistency):**
| File | Purpose |
|------|---------|
| `packages/quilto/quilto/agents/models.py` | Agent input models with `conversation_context` |
| `packages/quilto/quilto/orchestration.py` | Context propagation to all nodes |
| `packages/quilto/tests/test_context_propagation.py` | Integration tests for context |

**Epic 20 Retrospective Key Finding:**
- Pattern 4: Context building limited to last 4 turns (MEDIUM) - **THIS STORY FIXES IT**
- Multi-clarification rounds cause original query to drop out of context
- User verified: "it does have session context but only the last one"
- Context loss happens after 4 turns (turn 5 loses original query)

### Architecture Compliance

| Requirement | Status |
|-------------|--------|
| Quilto framework changes | All changes in `packages/quilto/quilto/session/` |
| Swealog app changes | None required |
| Backward compatibility | Default `context_turns=6` is larger than current 4 |
| Type hints | Using `int` with `Field(default=6, ge=2)` |
| Consistency | Uses same first+recent strategy as storage pruning |

### Test Coverage Requirements

**Existing tests to verify DO NOT BREAK (test_session.py):**
- `TestSessionConfig` class (lines 188-210) - test new field
- `test_turn_pruning_keeps_first_and_recent` (lines 453-480) - storage pruning tests remain unchanged

**New unit tests required:**
| Test | Purpose | Expected |
|------|---------|----------|
| `test_build_context_fewer_turns_than_limit` | <6 turns | All turns in context |
| `test_build_context_equal_turns_to_limit` | =6 turns | All turns in context |
| `test_build_context_more_turns_than_limit` | >6 turns | First + last 5 turns |
| `test_context_turns_default_value` | No explicit setting | context_turns=6 |
| `test_context_turns_custom_value` | Explicit setting | Respects custom value |
| `test_context_and_storage_independent` | Both set differently | Each works independently |

### Design Decisions

1. **Default 6 turns (not 4):** Larger than current to improve coverage without being too large
2. **Independent from max_conversation_turns:** Context building and storage pruning are separate concerns
3. **Same strategy (first+recent):** Consistent with storage pruning for conceptual alignment
4. **ge=2 constraint:** Ensures at least first + 1 recent turn (minimum useful context)

### Anti-Pattern Prevention

| Anti-Pattern | Prevention |
|--------------|------------|
| Creating new pruning logic | Reuse pattern from lines 109-114 (storage pruning) |
| Forgetting `ge=2` constraint | Field(ge=2) ensures valid minimum |
| Hardcoding turn count again | Use `self._config.context_turns` |
| Breaking existing tests | Run `test_turn_pruning_keeps_first_and_recent` |
| Inconsistent slice syntax | Use ` :]` with space (ruff convention) |

### Validation Commands

```bash
# Quick validation (run frequently)
make check

# Full validation (before commit)
make validate

# Run specific test file
uv run pytest packages/quilto/tests/test_session.py -v

# Run only new context_turns tests (after implementation)
uv run pytest packages/quilto/tests/test_session.py -v -k "context_turns or build_context"
```

### Dogfooding Verification Script

**Multi-turn session test (7+ turns required to trigger the fix):**
```bash
# Turn 1: Initial query
uv run swealog run --config ./llm-config-openai.yaml --storage ./logs --debug --non-interactive "I want upper body strength training"
# Note the session ID from output

# Turns 2-7: Add more turns (clarifications, follow-ups)
uv run swealog run --config ./llm-config-openai.yaml --storage ./logs --debug --non-interactive --session <id> "What exercises do you recommend?"
uv run swealog run --config ./llm-config-openai.yaml --storage ./logs --debug --non-interactive --session <id> "Can you give me more detail?"
uv run swealog run --config ./llm-config-openai.yaml --storage ./logs --debug --non-interactive --session <id> "What about for chest?"
uv run swealog run --config ./llm-config-openai.yaml --storage ./logs --debug --non-interactive --session <id> "And back exercises?"
uv run swealog run --config ./llm-config-openai.yaml --storage ./logs --debug --non-interactive --session <id> "How many sets?"

# Turn 8: Test first turn recall (THIS IS THE TEST)
uv run swealog run --config ./llm-config-openai.yaml --storage ./logs --debug --non-interactive --session <id> "What did I ask for first?"
# Expected: References "upper body strength training" (turn 1)
# Not: A middle turn like "What exercises do you recommend?"
```

### References

- [Evidence: Epic 20 Retrospective `_bmad-output/implementation-artifacts/epic-20/epic-20-retro-2026-01-29.md` lines 57-85]
- [Session models: `packages/quilto/quilto/session/models.py` lines 54-64]
- [Context building: `packages/quilto/quilto/session/session.py` lines 131-147]
- [Storage pruning: `packages/quilto/quilto/session/session.py` lines 109-114]
- [Session tests: `packages/quilto/tests/test_session.py` lines 188-210, 453-480]
- [Story 20.5 (prior): `_bmad-output/implementation-artifacts/epic-20/20-5-fix-session-context-propagation.md`]
- [Project conventions: `_bmad-output/project-context.md`]

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

- Dogfooding session: `f4e82e2e-49c1-42aa-96a9-8f203d61e249`

### Completion Notes List

1. Added `context_turns` field to `SessionConfig` with default=6 and ge=2 constraint
2. Updated docstring to explain both storage pruning (`max_conversation_turns`) and context building (`context_turns`) as separate concerns
3. Replaced hardcoded `history[-4:]` in `_build_conversation_context()` with parameterized first+recent strategy
4. Reused the same pattern as storage pruning (lines 109-114) for consistency
5. Added 8 new tests in `TestBuildConversationContext` class plus 5 tests in `TestSessionConfig` for `context_turns`
6. All 62 tests in `test_session.py` pass, total 2143 tests pass with `make validate`
7. Dogfooding verified: After 8 turns, system correctly recalled "I want upper body strength training" when asked "What did I ask for first?"

### File List

| File | Change |
|------|--------|
| `packages/quilto/quilto/session/models.py` | Added `context_turns` field to `SessionConfig` |
| `packages/quilto/quilto/session/session.py` | Updated `_build_conversation_context()` with first+recent strategy, improved docstring |
| `packages/quilto/tests/test_session.py` | Added 14 new tests: 9 in `TestBuildConversationContext` + 5 in `TestSessionConfig` for `context_turns` |

### Senior Developer Review (AI)

**Reviewer:** Amelia (Dev Agent) | **Date:** 2026-01-29 | **Outcome:** APPROVED

**Review Summary:**
- All 6 Acceptance Criteria verified as implemented with test coverage
- All 5 Tasks marked [x] confirmed complete with evidence
- `make validate` passes: 2144 tests pass (1 new test added during review)
- Dogfooding evidence provided with session ID

**Issues Found & Fixed:**
1. **[MEDIUM]** Added missing `context_turns=2` boundary test (`test_context_turns_minimum_boundary`)
2. **[MEDIUM]** Improved `_build_conversation_context()` docstring to document both behaviors
3. **[LOW]** Added explicit turn count assertion in `test_build_context_more_turns_than_limit`
4. **[LOW]** Clarified File List test count (14 tests: 9 + 5 distribution)

**Code Quality:** Implementation correctly reuses first+recent pattern from storage pruning (line 109-114) for consistency. Type hints, field validation, and slice syntax follow project conventions.
