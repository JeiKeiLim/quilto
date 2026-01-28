# Story 18.3: Fix Clarification Questions Type Mismatch

Status: done

## Story

As a **Swealog user**,
I want clarification questions to work correctly,
so that the system can ask for missing information.

## Problem Statement

**Source:** Story 17.11 Dogfooding - Goal-related query failure

**Query:** "Am I on track for my fitness goals?"

**Symptom:**
```
AttributeError: 'str' object has no attribute 'get'
```

**Location:** `packages/quilto/quilto/session/session.py:261-268`

**Root Cause Analysis:**

Type mismatch in the clarification questions data flow:

1. **PlannerOutput.clarify_questions** is `list[str] | None` (`quilto/agents/models.py:409`)
2. **QuiltoState.clarify_questions** is typed as `list[dict[str, Any]] | None` (`orchestration.py:199`) - **TYPE ANNOTATION IS WRONG**
3. **plan_node** stores Planner output directly (`orchestration.py:540-549`)
4. **session.py:261-268** assumes dict format and calls `q.get("question")` - **CRASHES on strings**

When Planner outputs `["What time did you exercise?"]` (strings), the state receives strings, but session.py tries `q.get("question")` which fails.

## Acceptance Criteria

1. **Given** `clarify_questions_raw` contains dict items (with `question` key)
   **When** `_build_process_result` processes them
   **Then** questions are extracted correctly as `ClarificationQuestion` objects

2. **Given** `clarify_questions_raw` contains string items (from Planner output)
   **When** `_build_process_result` processes them
   **Then** no AttributeError, strings converted to `ClarificationQuestion(question=str, options=None)`

3. **Given** `clarify_questions_raw` is None or empty list
   **When** `_build_process_result` processes it
   **Then** `clarification_questions` is None (not empty list)

4. **Given** mixed types in `clarify_questions_raw` (dicts and strings)
   **When** processed
   **Then** all valid items converted to `ClarificationQuestion` objects

## Tasks / Subtasks

- [x] Task 1: Fix `_build_process_result` type handling (AC: #1, #2, #3, #4)
  - [x] Subtask 1.1: Add `isinstance(q, dict)` check before calling `q.get()`
  - [x] Subtask 1.2: Handle string items by creating `ClarificationQuestion(question=q, options=None)`
  - [x] Subtask 1.3: Handle None or empty list -> return None (not empty list)

- [x] Task 2: Add unit tests to existing test file (AC: #1, #2, #3, #4)
  - [x] Subtask 2.1: Add `TestBuildProcessResultClarification` class to `packages/quilto/tests/test_session.py`
  - [x] Subtask 2.2: Test dict items with `question` key (normal case)
  - [x] Subtask 2.3: Test string items (Planner output case)
  - [x] Subtask 2.4: Test None and empty list
  - [x] Subtask 2.5: Test mixed types (dicts and strings)
  - [x] Subtask 2.6: Test empty/whitespace strings are skipped
  - [x] Subtask 2.7: Test dict without `question` key is skipped

- [x] Task 3: Validation (All ACs)
  - [x] Subtask 3.1: `make check` during development
  - [x] Subtask 3.2: `make validate` before commit

## Dev Notes

### Two ClarificationQuestion Classes (Important Context)

The codebase has TWO different `ClarificationQuestion` classes:

| Location | Purpose | Fields |
|----------|---------|--------|
| `quilto/models.py:14-30` | **Public API** (used by session.py) | `question`, `options` |
| `quilto/agents/models.py:826-875` | Internal agent model | `question`, `gap_addressed`, `options`, `required` |

This story fixes `session.py` which uses the **Public API version** (`quilto.models.ClarificationQuestion`).

### Current Code (Problematic)

```python
# session.py:257-268
clarify_questions_raw = state.get("clarify_questions")
clarification_questions: list[ClarificationQuestion] | None = None
if clarify_questions_raw:
    clarification_questions = [
        ClarificationQuestion(
            question=q.get("question", ""),  # AttributeError if q is string!
            options=q.get("options"),
        )
        for q in clarify_questions_raw
        if q.get("question")  # AttributeError if q is string!
    ]
```

### Fixed Code

```python
# session.py:257-268 - Apply isinstance pattern from Story 17.4
clarify_questions_raw = state.get("clarify_questions")
clarification_questions: list[ClarificationQuestion] | None = None
if clarify_questions_raw:
    result_questions: list[ClarificationQuestion] = []
    for q in clarify_questions_raw:
        if isinstance(q, dict) and q.get("question"):
            result_questions.append(
                ClarificationQuestion(
                    question=q.get("question", ""),
                    options=q.get("options"),
                )
            )
        elif isinstance(q, str) and q.strip():
            result_questions.append(
                ClarificationQuestion(question=q, options=None)
            )
    clarification_questions = result_questions if result_questions else None
```

### Data Flow (Root Cause Detail)

```
Planner.plan()
  -> PlannerOutput.clarify_questions: list[str] | None  (models.py:409)
  -> plan_node stores directly in state (orchestration.py:540-549)
  -> QuiltoState.clarify_questions: list[dict[str, Any]] | None  (WRONG TYPE at orchestration.py:199)
  -> session._build_process_result() assumes dict format -> CRASH
```

The state type annotation at `orchestration.py:199` is wrong but fixing it is deferred to avoid scope creep. The session.py fix handles both formats defensively.

### Related Pattern: Story 17.4

Story 17.4 fixed similar isinstance issue with `eval_feedback` in `orchestration.py`:
```python
# Before (unsafe):
reason = eval_feedback[0] if eval_feedback else "insufficient"

# After (safe):
if isinstance(eval_feedback, list) and eval_feedback:
    reason = eval_feedback[0]
else:
    reason = "insufficient"
```

Apply the same defensive isinstance pattern here.

### Test Implementation

Add to existing `packages/quilto/tests/test_session.py`:

```python
# Import at top of file (already available):
# from quilto import ClarificationQuestion, Session, SessionConfig, SessionData, SQLiteSessionStore

class TestBuildProcessResultClarification:
    """Test _build_process_result handles clarify_questions types correctly."""

    @pytest.fixture
    def session(self) -> Session:
        """Create session for testing _build_process_result."""
        store = SQLiteSessionStore(":memory:")
        config = SessionConfig()
        now = datetime.now(UTC)
        data = SessionData(session_id="test", created_at=now, updated_at=now)
        store.save(data)
        return Session(data, store, config)

    def _build_state(self, clarify_questions: Any) -> dict[str, Any]:
        """Build minimal state dict for _build_process_result."""
        return {
            "input_type": "query",
            "response": "Test response",
            "confidence": 0.9,
            "source_entry_ids": [],
            "parsed_data": None,
            "selected_domains": [],
            "clarify_questions": clarify_questions,
        }

    def test_dict_items_with_question_key(self, session: Session) -> None:
        """Dict items with question key should be converted correctly."""
        state = self._build_state([
            {"question": "What time?", "options": ["Morning", "Evening"]},
            {"question": "How intense?", "options": None},
        ])
        result = session._build_process_result(state)

        assert result.clarification_questions is not None
        assert len(result.clarification_questions) == 2
        assert result.clarification_questions[0].question == "What time?"
        assert result.clarification_questions[0].options == ["Morning", "Evening"]
        assert result.clarification_questions[1].question == "How intense?"
        assert result.clarification_questions[1].options is None

    def test_string_items_converted_to_questions(self, session: Session) -> None:
        """String items should be converted to ClarificationQuestion."""
        state = self._build_state([
            "What time did you exercise?",
            "How did you feel afterward?",
        ])
        result = session._build_process_result(state)

        assert result.clarification_questions is not None
        assert len(result.clarification_questions) == 2
        assert result.clarification_questions[0].question == "What time did you exercise?"
        assert result.clarification_questions[0].options is None
        assert result.clarification_questions[1].question == "How did you feel afterward?"

    def test_none_returns_none(self, session: Session) -> None:
        """None clarify_questions should return None."""
        state = self._build_state(None)
        result = session._build_process_result(state)
        assert result.clarification_questions is None

    def test_empty_list_returns_none(self, session: Session) -> None:
        """Empty list should return None (not empty list)."""
        state = self._build_state([])
        result = session._build_process_result(state)
        assert result.clarification_questions is None

    def test_mixed_types_all_converted(self, session: Session) -> None:
        """Mixed dict and string items should all be converted."""
        state = self._build_state([
            {"question": "From dict", "options": ["A", "B"]},
            "From string",
        ])
        result = session._build_process_result(state)

        assert result.clarification_questions is not None
        assert len(result.clarification_questions) == 2
        assert result.clarification_questions[0].question == "From dict"
        assert result.clarification_questions[1].question == "From string"

    def test_empty_string_skipped(self, session: Session) -> None:
        """Empty or whitespace-only strings should be skipped."""
        state = self._build_state(["Valid question", "", "   "])
        result = session._build_process_result(state)

        assert result.clarification_questions is not None
        assert len(result.clarification_questions) == 1
        assert result.clarification_questions[0].question == "Valid question"

    def test_dict_without_question_key_skipped(self, session: Session) -> None:
        """Dict without question key should be skipped."""
        state = self._build_state([
            {"question": "Valid"},
            {"options": ["A", "B"]},
            {"text": "Not a question"},
        ])
        result = session._build_process_result(state)

        assert result.clarification_questions is not None
        assert len(result.clarification_questions) == 1
```

### Minimal State Dict Structure

The `_build_process_result` method expects these state keys (with defaults):
- `input_type`: str (default from state, required for ProcessResult)
- `response`: str | None
- `confidence`: float | None
- `source_entry_ids`: list[str] (default [])
- `parsed_data`: dict | None
- `selected_domains`: list[str] (default [])
- `clarify_questions`: list[str | dict] | None (the key we're fixing)

### Files to Modify

| File | Changes |
|------|---------|
| `packages/quilto/quilto/session/session.py` | Fix `_build_process_result` lines 257-268 - add isinstance checks |
| `packages/quilto/tests/test_session.py` | Add `TestBuildProcessResultClarification` class with 7 unit tests |

### Validation Commands

```bash
# During development
make check

# Before commit
make validate
```

### Project Structure Notes

- **Package:** Quilto (`packages/quilto/`)
- **File:** `quilto/session/session.py`
- **Tests:** Add to existing `packages/quilto/tests/test_session.py`
- Follows isinstance pattern from Story 17.4

### References

- [Source: `tests/eval/feedback/archive/iter-005/analysis.md` - Issue 2]
- [Source: `epics.md#story-183-fix-clarification-questions-type-mismatch`]
- [Pattern: Story 17.4 - eval_feedback type safety in orchestration.py]
- [Reference: PlannerOutput.clarify_questions definition at agents/models.py:409]

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

None - implementation straightforward.

### Completion Notes List

1. Fixed `_build_process_result` to handle both dict and string formats for clarify_questions
2. Applied isinstance pattern from Story 17.4 (eval_feedback type safety)
3. All 7 new unit tests pass covering:
   - Dict items with question key (AC #1)
   - String items from Planner output (AC #2)
   - None/empty list returns None (AC #3)
   - Mixed types (AC #4)
   - Edge cases: empty strings skipped, dicts without question key skipped
4. `make validate` passes (2094 passed, 101 skipped)
5. Code review fixes applied:
   - M1: Added test for empty options list edge case
   - M2: Removed redundant None check on line 302
   - M3: Added type hint comment for loop variable
   - L1: Fixed comment precision (list[str] → list[str] | None)
   - L3: Corrected line numbers in File List (258 → 257)

### File List

| File | Changes |
|------|---------|
| `packages/quilto/quilto/session/session.py` | Fixed `_build_process_result` lines 257-273 - added isinstance checks for dict vs string handling |
| `packages/quilto/tests/test_session.py` | Added `TestBuildProcessResultClarification` class with 8 unit tests (lines 738-868) - includes code review edge case |
