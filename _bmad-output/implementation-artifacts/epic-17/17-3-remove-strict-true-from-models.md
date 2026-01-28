# Story 17.3: Remove strict=True from State-Crossing Models

Status: done

## Story

As a **Quilto framework developer**,
I want Pydantic models to accept string coercion for enums,
so that LangGraph state serialization doesn't break validation.

## Acceptance Criteria

1. **Given** any of the 4 affected models (`AnalyzerInput`, `AnalyzerOutput`, `RouterOutput`, `SynthesizerInput`)
   **When** created with string enum values (e.g., `query_type="insight"`)
   **Then** Pydantic auto-coerces to the correct enum instance (no ValidationError)

2. **Given** all changes applied
   **When** `make validate` is run
   **Then** all tests pass (no behavior change for enum instances)

## Tasks

**Target File:** `packages/quilto/quilto/agents/models.py`

Remove `model_config = ConfigDict(strict=True)` from 4 models that cross LangGraph state boundaries.

- [x] Task 1: `RouterOutput` (line 138) - Change `ConfigDict(strict=True)` to `ConfigDict()` (AC: #1)
- [x] Task 2: `AnalyzerInput` (line 586) - Change `ConfigDict(strict=True)` to `ConfigDict()` (AC: #1)
- [x] Task 3: `AnalyzerOutput` (line 627) - Change `ConfigDict(strict=True)` to `ConfigDict()` (AC: #1)
- [x] Task 4: `SynthesizerInput` (line 664) - Change `ConfigDict(strict=True)` to `ConfigDict()` (AC: #1)
- [x] Task 5: Run validation (see Validation section for all steps) (AC: #2)

## Files Modified

| File | Changes |
|------|---------|
| `packages/quilto/quilto/agents/models.py` | Remove `strict=True` from 4 model configs |

## Code Changes (models.py)

| Line | Current | New |
|------|---------|-----|
| 138 | `model_config = ConfigDict(strict=True)` | `model_config = ConfigDict()` |
| 586 | `model_config = ConfigDict(strict=True)` | `model_config = ConfigDict()` |
| 627 | `model_config = ConfigDict(strict=True)` | `model_config = ConfigDict()` |
| 664 | `model_config = ConfigDict(strict=True)` | `model_config = ConfigDict()` |

**IMPORTANT:** Use `ConfigDict()` instead of removing the line entirely:
- Preserves consistent structure across all models
- Allows easy re-addition of config options (e.g., `frozen=True`, `extra="forbid"`) later
- Makes it clear this was an intentional design choice, not a forgotten config

## Models NOT Modified (Safe with strict=True)

**Summary:** Only the 4 models above cross LangGraph state boundaries. The 17 models below are internal and should KEEP `strict=True`.

These models don't cross LangGraph state boundaries:

| Model | Why Safe |
|-------|----------|
| `DomainInfo` | Created locally, never from state dict |
| `RouterInput` | Created locally before routing |
| `ParserInput` | Created locally, uses `arbitrary_types_allowed=True` |
| `ParserOutput` | Stored to state but never re-validated from state |
| `Gap`, `EvaluationFeedback`, `SubQuery` | Nested in other models, not top-level state |
| `ActiveDomainContext` | Created by DomainSelector, not from state dict |
| `PlannerInput`, `PlannerOutput` | Created locally or not re-validated |
| `RetrieverInput`, `RetrieverOutput` | Created locally or not re-validated |
| `Finding`, `SufficiencyEvaluation` | Nested models |
| `SynthesizerOutput` | Created by Synthesizer, not re-validated |
| `EvaluationDimension`, `EvaluatorInput`, `EvaluatorOutput` | Not re-validated from state |
| `ClarificationQuestion`, `ClarifierInput`, `ClarifierOutput` | Not re-validated from state |
| `ContextUpdate`, `ObserverInput`, `ObserverOutput` | Not re-validated from state |
| `RetrievalAttempt` | Nested model |

## Validation

```bash
# 1. Run full validation suite
make validate

# 2. Verify string coercion works
uv run python3 -c "
from quilto.agents.models import (
    AnalyzerInput, AnalyzerOutput, RouterOutput, SynthesizerInput,
    QueryType, Verdict, InputType, ActiveDomainContext, Finding,
    SufficiencyEvaluation, Gap, GapType, RetrievalAttempt
)

# Test 1: AnalyzerInput with string query_type
ai = AnalyzerInput(
    query='test query',
    query_type='insight',  # String, should coerce
    entries=[],
    retrieval_summary=[],
    domain_context=ActiveDomainContext(
        domains_loaded=['test'],
        vocabulary={},
        expertise='test'
    )
)
assert ai.query_type == QueryType.INSIGHT
print('AnalyzerInput: PASS')

# Test 2: AnalyzerOutput with string verdict
ao = AnalyzerOutput(
    query_intent='test intent',
    findings=[],
    patterns_identified=[],
    sufficiency_evaluation=SufficiencyEvaluation(
        critical_gaps=[],
        nice_to_have_gaps=[],
        evidence_check_passed=True,
        speculation_risk='none'
    ),
    verdict_reasoning='test reasoning',
    verdict='sufficient'  # String, should coerce
)
assert ao.verdict == Verdict.SUFFICIENT
print('AnalyzerOutput: PASS')

# Test 3: RouterOutput with string input_type
ro = RouterOutput(
    input_type='QUERY',  # String, should coerce
    confidence=0.9,
    selected_domains=['fitness'],
    domain_selection_reasoning='test',
    reasoning='test'
)
assert ro.input_type == InputType.QUERY
print('RouterOutput: PASS')

# Test 4: SynthesizerInput with string query_type
si = SynthesizerInput(
    query='test query',
    query_type='recommendation',  # String, should coerce
    analysis=ao,
    vocabulary={}
)
assert si.query_type == QueryType.RECOMMENDATION
print('SynthesizerInput: PASS')

print('All coercion tests passed!')
"

# 3. Verify original reproduction command works
uv run swealog run --config ./llm-config-openai.yaml --storage ./logs --debug --non-interactive "How was my workout this week?"
```

## Dev Notes

### Root Cause

LangGraph state serialization converts enums to strings. When models with `strict=True` re-validate from state, they reject strings where enums are expected.

**Full investigation:** See `17-1-query-flow-investigation.md` - Issue 2: Enum String Validation Failure

### Why Coercion is Safe

All Quilto enums inherit from `str` (e.g., `class QueryType(str, Enum)`). Without `strict=True`, Pydantic accepts both:
- `QueryType.INSIGHT` (enum instance) directly
- `"insight"` (string) coerced to `QueryType.INSIGHT`

Both are type-safe because enum values ARE strings.

### If Tests Fail

If `make validate` fails after changes:
1. Verify ONLY the 4 specified models were modified
2. Ensure `ConfigDict()` was used, not removal of the line
3. Check you didn't accidentally modify a model from the "Models NOT Modified" section
4. Rollback and investigate if a wrong model was modified

### Project Structure

- **Package:** Quilto (`packages/quilto/`)
- **File:** `quilto/agents/models.py`
- All changes are in the Quilto framework
- Swealog requires no changes (proper Quilto consumer)

### Related Type Ignore Comments

These `type: ignore` comments in `orchestration.py` exist because of the strict validation:
```python
query_type=query_type,  # type: ignore[arg-type]  # Line 509
query_type=query_type,  # type: ignore[arg-type]  # Line 607
```

These can remain as-is (they suppress pyright warnings about str vs enum) or be removed in a future cleanup story (17.9).

### References

- [Source: `17-1-query-flow-investigation.md` - Issue 2: Enum String Validation Failure]
- [Source: `epics.md#story-173-remove-stricttrue-from-state-crossing-models`]
- [Source: `project-context.md#pydantic-patterns`]

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

N/A - No debug logs needed for this straightforward config change.

### Completion Notes List

1. Changed `ConfigDict(strict=True)` to `ConfigDict()` in 4 models that cross LangGraph state boundaries
2. All 2024 tests pass (101 skipped are intentional - Ollama integration tests)
3. String coercion verification passed for all 4 models:
   - `AnalyzerInput`: `query_type='insight'` → `QueryType.INSIGHT`
   - `AnalyzerOutput`: `verdict='sufficient'` → `Verdict.SUFFICIENT`
   - `RouterOutput`: `input_type='QUERY'` → `InputType.QUERY`
   - `SynthesizerInput`: `query_type='recommendation'` → `QueryType.RECOMMENDATION`

### File List

| File | Changes |
|------|---------|
| `packages/quilto/quilto/agents/models.py` | Lines 138, 586, 627, 664: `ConfigDict(strict=True)` → `ConfigDict()` |
