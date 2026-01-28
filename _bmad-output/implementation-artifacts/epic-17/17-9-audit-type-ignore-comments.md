# Story 17.9: Audit Type Ignore Comments

Status: done

## Story

As a **Quilto framework developer**,
I want to reduce `# type: ignore` comments,
so that real type issues aren't hidden.

## Acceptance Criteria

1. **Given** orchestration.py type ignores
   **When** reviewed
   **Then** each is either fixed or documented with rationale

2. **Given** unnecessary type ignores
   **When** removed
   **Then** pyright passes without them

3. **Given** necessary type ignores
   **When** kept
   **Then** specific error code is used (e.g., `# type: ignore[arg-type]`)

## Tasks / Subtasks

- [x] Task 1: Fix return-value ignores via TypeVar pattern (AC: #2)
  - [x] Subtask 1.1: Add `T = TypeVar("T", bound=BaseModel)` to `llm/client.py`
  - [x] Subtask 1.2: Change `complete_structured` signature to `response_model: type[T]) -> T`
  - [x] Subtask 1.3: Remove type ignores from router.py:160, planner.py:376, client.py:353

- [x] Task 2: Fix query_type string-to-enum issues (AC: #2)
  - [x] Subtask 2.1: Lines 647, 748 - Convert `query_type` string to `QueryType` enum before passing
  - [x] Subtask 2.2: Apply pattern: `QueryType(query_type) if isinstance(query_type, str) else query_type`

- [x] Task 3: Fix orchestration.py remaining ignores (AC: #2, #3)
  - [x] Subtask 3.1: Line 490 - Add public `get_storage_summary()` accessor to `quilto.py`
  - [x] Subtask 3.2: Lines 511, 513 - Type guard for `storage_summary` and `evaluation_feedback`
  - [x] Subtask 3.3: Lines 530, 536, 538 - Replace `hasattr` with `isinstance(i, BaseModel)` pattern

- [x] Task 4: Fix remaining file ignores (AC: #2, #3)
  - [x] Subtask 4.1: `storage/context.py:366,368` - Ensure enum values passed directly
  - [x] Subtask 4.2: `llm/errors.py:112` - Add `isinstance` check for `status_code` access
  - [x] Subtask 4.3: `state/observer_triggers.py:525-527` - Add internal keys to QuiltoState TypedDict
  - [x] Subtask 4.4: `agents/models.py:874` - Fix validator return type annotation

- [x] Task 5: Document necessary ignores with rationale (AC: #3)
  - [x] Subtask 5.1: Keep litellm ignores (lines 259-260) with rationale comment
  - [x] Subtask 5.2: Ensure all remaining ignores have specific error codes

- [x] Task 6: Run validation - `make check` during dev, `make validate` before commit (AC: All)

## Dev Notes

### Current State (21 Type Ignores)

**Total:** 21 `# type: ignore` comments across 8 files in `packages/quilto/quilto/`

| File | Count | Description |
|------|-------|-------------|
| `orchestration.py` | 9 | State typing, model validation |
| `llm/client.py` | 3 | litellm return types |
| `state/observer_triggers.py` | 3 | TypedDict state access |
| `storage/context.py` | 2 | Pydantic field types |
| `agents/router.py` | 1 | Return type |
| `agents/planner.py` | 1 | Return type |
| `agents/models.py` | 1 | Return type |
| `llm/errors.py` | 1 | Union attribute access |

### Root Cause Analysis

**Category 1: complete_structured return type (4 ignores)**

Files: `router.py:160`, `planner.py:376`, `client.py:353`

Root cause: `complete_structured` returns `BaseModel` but callers expect specific types.

Fix: Add TypeVar to `llm/client.py`:
```python
from typing import TypeVar

T = TypeVar("T", bound=BaseModel)

async def complete_structured(
    self,
    agent: str,
    messages: list[dict[str, Any]],
    response_model: type[T],  # Changed from type[BaseModel]
    **kwargs: Any,
) -> T:  # Changed from BaseModel
```

**Category 2: String-to-Enum Coercion (3 ignores)**

Lines: `orchestration.py:647`, `orchestration.py:748`, `orchestration.py:649`

Root cause: `state.get()` returns `str` but `AnalyzerInput`/`SynthesizerInput` expect `QueryType` enum.

Fix pattern:
```python
# Before
query_type = state.get(StateKeys.QUERY_TYPE, "factual")
analyzer_input = AnalyzerInput(query_type=query_type, ...)  # type: ignore[arg-type]

# After
query_type_str = state.get(StateKeys.QUERY_TYPE, "factual")
query_type = QueryType(query_type_str) if isinstance(query_type_str, str) else query_type_str
analyzer_input = AnalyzerInput(query_type=query_type, ...)  # No ignore needed
```

Apply to:
- Line 647: `AnalyzerInput(query_type=...)`
- Line 748: `SynthesizerInput(query_type=...)`
- Line 649: `retrieval_summary` (similar pattern - verify actual type mismatch)

**Category 3: Private Method Access (1 ignore)**

Line: `orchestration.py:490`

Root cause: Accessing `quilto._get_storage_summary()` from orchestration module.

Fix: Add public accessor to `quilto.py`:
```python
def get_storage_summary(self) -> dict[str, Any]:
    """Get storage summary for agent planning.

    Returns:
        Summary of storage contents for date range decisions.
    """
    return self._get_storage_summary()
```

Then update orchestration.py:490:
```python
storage_summary: dict[str, Any] = quilto.get_storage_summary()
```

**Category 4: evaluation_feedback arg-type (1 ignore)**

Line: `orchestration.py:513`

Root cause: `state.get(StateKeys.EVAL_FEEDBACK)` returns `list[EvaluationFeedback] | None`, but we extract element at index 0 which could be `EvaluationFeedback` or remain as `None`. `PlannerInput.evaluation_feedback` expects `EvaluationFeedback | None`.

Current code (lines 496-500):
```python
eval_feedback = state.get(StateKeys.EVAL_FEEDBACK)
if state.get(StateKeys.RETRY_COUNT, 0) > 0:
    evaluation_feedback = eval_feedback[0] if isinstance(eval_feedback, list) and eval_feedback else None
else:
    evaluation_feedback = None
```

Fix: Already correct logic, but pyright can't infer type. Add explicit annotation:
```python
evaluation_feedback: EvaluationFeedback | None = (
    eval_feedback[0] if isinstance(eval_feedback, list) and eval_feedback else None
)
```

**Category 5: storage_summary arg-type (1 ignore)**

Line: `orchestration.py:511`

Root cause: `storage_summary` is `dict[str, Any]` but `PlannerInput.storage_summary` expects `dict[str, Any] | None`.

Fix: This is actually compatible - remove the ignore. If pyright still complains, the issue is elsewhere.

**Category 6: union-attr with hasattr (2 ignores)**

Lines: `orchestration.py:536`, `orchestration.py:538`

Root cause: `retrieval_instructions` can be `list[RetrievalInstruction | dict]`. `hasattr` check isn't understood by pyright.

Fix: Replace `hasattr` with `isinstance`:
```python
from pydantic import BaseModel

for i in planner_output.retrieval_instructions:
    if isinstance(i, BaseModel):
        retrieval_instr.append(i.model_dump())
    else:
        # i is already a dict
        retrieval_instr.append(i)
```

**Category 7: clarify_questions union-attr (1 ignore)**

Line: `orchestration.py:530`

Root cause: `planner_output.clarify_questions` is `list[ClarifyQuestion] | None`. Code checks `if planner_output.clarify_questions:` but pyright doesn't narrow type inside comprehension.

Fix: Add explicit None check:
```python
clarify_q: list[dict[str, Any]] | None = None
clarify_questions = planner_output.clarify_questions
if clarify_questions is not None:
    clarify_q = [q.model_dump() for q in clarify_questions]
```

**Category 8: litellm type stubs (2 ignores) - KEEP**

Lines: `llm/client.py:259-260`

Root cause: litellm library lacks complete type stubs.

Action: **KEEP with rationale comment**:
```python
# litellm lacks complete type stubs - ignore is necessary
response = await litellm.acompletion(**completion_kwargs)  # type: ignore[reportUnknownMemberType]
return response.choices[0].message.content or ""  # type: ignore[reportUnknownMemberType,reportAttributeAccessIssue]
```

**Category 9: TypedDict internal keys (3 ignores)**

Lines: `state/observer_triggers.py:525-527`

Root cause: `QuiltoState` TypedDict doesn't include `_observer`, `_context_manager`, `_observer_trigger_config`.

Fix option A - Extend QuiltoState (in `state/models.py`):
```python
class QuiltoState(TypedDict, total=False):
    # ... existing keys ...
    # Internal keys (not part of public API)
    _observer: Any
    _context_manager: Any
    _observer_trigger_config: Any
```

Fix option B - Use cast (less invasive):
```python
observer = cast(Optional[Observer], state.get("_observer"))
context_manager = cast(Optional[ContextManager], state.get("_context_manager"))
config = cast(Optional[ObserverTriggerConfig], state.get("_observer_trigger_config"))
```

**Category 10: storage/context.py enum arg-type (2 ignores)**

Lines: `storage/context.py:366, 368`

Root cause: Likely passing string instead of enum for `confidence`/`category` fields.

Action: Grep for `ContextConfidence` and `ContextCategory` definitions. Ensure enum values are passed directly:
```python
# If parsing from string:
confidence = ContextConfidence(parsed_confidence_str)
category = ContextCategory(category_str)
```

**Category 11: llm/errors.py union-attr (1 ignore)**

Line: `llm/errors.py:112`

Root cause: `exception` could be multiple types, not all have `status_code`.

Fix: Add isinstance check or getattr:
```python
# Option A: isinstance
if hasattr(exception, "status_code"):
    status = exception.status_code
else:
    status = None

# Option B: getattr (cleaner)
status = getattr(exception, "status_code", None)
```

**Category 12: agents/models.py validator return (1 ignore)**

Line: `agents/models.py:874`

Root cause: `@field_validator` return type inference issue.

Fix: Add explicit return type annotation:
```python
@field_validator("some_field", mode="after")
@classmethod
def validate_field(cls, v: list[SomeType] | None) -> list[SomeType] | None:
    # ... validation logic ...
    return filtered  # or return v
```

### Expected Outcomes

**Target: Reduce from 21 to ~2-4 type ignores**

Fixable ignores:
- 4 return-value ignores → Fixed by TypeVar pattern
- 3 query_type arg-type → Fixed by enum conversion
- 1 private method → Fixed by public accessor
- 2 hasattr union-attr → Fixed by isinstance pattern
- 1 clarify_questions → Fixed by explicit None check
- 3 TypedDict internal keys → Fixed by extending TypedDict or cast
- 2 storage/context enum → Fixed by direct enum usage
- 1 llm/errors union-attr → Fixed by getattr
- 1 models.py validator → Fixed by explicit annotation
- 2 evaluation/storage arg-type → Fixed by type guards

Must keep (with rationale):
- 2 litellm ignores (lines 259-260) - External library lacks stubs

### Test Strategy

No new tests required - type hygiene story. Verification:

```bash
# After each fix, run:
uv run pyright

# Track progress:
grep -r "# type: ignore" packages/quilto/quilto/ | wc -l

# Before commit:
make validate
```

### Project Structure

- **Package:** Quilto (`packages/quilto/`)
- **Files to Modify:**
  - `quilto/llm/client.py` - TypeVar + keep litellm ignores
  - `quilto/orchestration.py` - Most fixes here (9 ignores)
  - `quilto/quilto.py` - Add public `get_storage_summary()`
  - `quilto/agents/router.py` - Remove return-value ignore
  - `quilto/agents/planner.py` - Remove return-value ignore
  - `quilto/agents/models.py` - Fix validator annotation
  - `quilto/storage/context.py` - Enum usage fix
  - `quilto/llm/errors.py` - getattr pattern
  - `quilto/state/observer_triggers.py` - TypedDict or cast fix
  - `quilto/state/models.py` - Extend QuiltoState (if option A)

### Previous Story Intelligence

Stories 17.4-17.8 established patterns:
- `isinstance` checks for type safety (Story 17.4) → Use for Categories 6, 7
- `.get()` with defaults for dict access (Story 17.6) → Already applied
- `StateKeys` constants for state key access (Story 17.7) → Already applied
- Defensive validation with fallback (Story 17.8) → Pattern for Category 4

### Architecture Compliance

- **No new dependencies** - Only using built-in `typing` module
- **Non-breaking** - Type improvements don't change runtime behavior
- **Backward compatible** - Public accessor wraps existing private method

### References

- Story 17.1: Investigation - Issue 6: Type Ignores Hide Issues
- `_bmad-output/project-context.md`: Pyright strict mode requirement
- `architecture.md`: Testing standards (pyright strict mode)

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

N/A

### Completion Notes List

1. **Reduced type ignores from 21 to 3** - Target was 2-4, achieved 3
2. **TypeVar pattern in llm/client.py** - Added `T = TypeVar("T", bound=BaseModel)` for complete_structured methods
3. **QueryType enum conversion** - Fixed string-to-enum issues in orchestration.py for AnalyzerInput and SynthesizerInput
4. **Public accessor added** - `quilto.get_storage_summary()` replaces private method access
5. **Type aliases introduced** - `ConfidenceLevel` and `CategoryType` in storage/context.py for Literal type clarity
6. **Unnecessary cast removed** - parser.py cast became unnecessary after TypeVar pattern
7. **All tests pass** - 2064 passed, 101 skipped

**Remaining Type Ignores (3):**
- `llm/client.py:262-263` - litellm lacks complete type stubs (external library)
- `storage/context.py:355` - Literal type narrowing from set membership check (pyright limitation)

### File List

- `packages/quilto/quilto/llm/client.py` - TypeVar pattern, litellm ignores with rationale
- `packages/quilto/quilto/orchestration.py` - QueryType enum conversion, EvaluationFeedback type guards, simplified planner output handling
- `packages/quilto/quilto/quilto.py` - Added public `get_storage_summary()` accessor
- `packages/quilto/quilto/agents/router.py` - Removed return-value type ignore
- `packages/quilto/quilto/agents/planner.py` - Removed return-value type ignore
- `packages/quilto/quilto/agents/parser.py` - Removed unnecessary cast
- `packages/quilto/quilto/agents/models.py` - Fixed validator return type
- `packages/quilto/quilto/storage/context.py` - Added type aliases, fixed Literal type handling
- `packages/quilto/quilto/llm/errors.py` - Used getattr for status_code access
- `packages/quilto/quilto/state/observer_triggers.py` - Used cast for internal state keys

## Senior Developer Review (AI)

**Date:** 2026-01-28
**Reviewer:** Amelia (Dev Agent)
**Outcome:** ✅ APPROVED

### Verification Summary

| Claim | Verified |
|-------|----------|
| Reduced type ignores from 21 to 3 | ✅ Confirmed |
| TypeVar pattern added | ✅ llm/client.py:26 |
| QueryType enum conversion | ✅ orchestration.py:640, 743 |
| Public accessor added | ✅ quilto.py:128 |
| All tests pass | ✅ 2064 passed |
| pyright clean | ✅ 0 errors |

### Remaining Type Ignores Audit

All 3 remaining `# type: ignore` comments have documented rationale:
1. `llm/client.py:262` - litellm external library lacks stubs
2. `llm/client.py:263` - litellm response attribute access
3. `storage/context.py:355` - pyright cannot narrow Literal through set membership

### Notes

- 20 `# pyright: ignore` comments exist but are out of scope for this story (focused on `# type: ignore`)
- All acceptance criteria met
- No blocking issues found

**Status:** Ready for merge
