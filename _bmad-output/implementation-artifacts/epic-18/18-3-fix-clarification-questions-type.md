# Story 18.3: Fix Clarification Questions Type Mismatch

Status: backlog

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

**Location:** `packages/quilto/quilto/session/session.py:267`

**Root Cause:** `clarify_questions_raw` from LangGraph state sometimes contains strings instead of dicts. The code assumes dict structure: `q.get("question")`.

## Acceptance Criteria

1. **Given** `clarify_questions_raw` contains dict items
   **When** `_build_process_result` processes them
   **Then** questions are extracted correctly

2. **Given** `clarify_questions_raw` contains string items (serialized by LangGraph)
   **When** `_build_process_result` processes them
   **Then** no AttributeError, strings handled gracefully

3. **Given** `clarify_questions_raw` is None or empty
   **When** `_build_process_result` processes it
   **Then** empty questions list returned

4. **Given** mixed types in `clarify_questions_raw`
   **When** processed
   **Then** valid questions extracted, invalid items skipped with warning

## Tasks

- [ ] Task 1: Add type check in `_build_process_result`
  - Location: `packages/quilto/quilto/session/session.py:267`
  - Pattern: `isinstance(q, dict) and q.get("question")`

- [ ] Task 2: Handle string items gracefully
  - If item is string, try to parse as question text directly
  - Or skip with warning log

- [ ] Task 3: Add unit tests for type handling
  - Test with dict items (normal case)
  - Test with string items (LangGraph serialization case)
  - Test with None
  - Test with empty list
  - Test with mixed types

- [ ] Task 4: Run validation - `make check` during dev, `make validate` before commit

## Dev Notes

### Current Code (Problematic)

```python
# session.py:267 (approximate)
clarify_questions = [
    ClarificationQuestion(question=q.get("question"), options=q.get("options"))
    for q in clarify_questions_raw
    if q.get("question")  # AttributeError if q is string
]
```

### Fixed Code

```python
clarify_questions = []
for q in clarify_questions_raw or []:
    if isinstance(q, dict) and q.get("question"):
        clarify_questions.append(
            ClarificationQuestion(
                question=q.get("question"),
                options=q.get("options")
            )
        )
    elif isinstance(q, str) and q.strip():
        # LangGraph may serialize as string - treat as question text
        logger.debug("Clarification question received as string: %s", q[:50])
        clarify_questions.append(
            ClarificationQuestion(question=q, options=None)
        )
```

### Similar Pattern: Story 17.4

Story 17.4 fixed `eval_feedback` type vulnerability with same pattern:
```python
if isinstance(eval_feedback, list) and eval_feedback:
    result = eval_feedback[0]
else:
    result = "insufficient"
```

### Files to Modify

- `packages/quilto/quilto/session/session.py` - `_build_process_result` method

### Test File

- `packages/quilto/tests/test_session_clarification.py` (new)

### References

- [Source: `tests/eval/feedback/archive/iter-005/analysis.md` - Issue 2]
- [Pattern: Story 17.4 - eval_feedback type safety]
