# Story 17.1: Query Flow Investigation

**Date:** 2026-01-28
**Status:** Complete

---

## Reproduction Command

```bash
uv run swealog run --config ./llm-config-openai.yaml --storage ./logs --debug --non-interactive "How was my workout this week?"
```

**Result:** `"I encountered an error: Synthesizer failed..."` with 0 entries retrieved.

---

## Root Causes Identified

### Issue 1: Storage Path Doubling

**Symptom:** Retriever returns 0 entries despite data existing.

**Root Cause:**
- `StorageRepository` internally adds `/logs/` to `base_path`
- When user passes `--storage ./logs`, result is `./logs/logs/raw/...`
- Data exists in `./logs/raw/` but storage looks in `./logs/logs/raw/`

**Evidence:**
```python
# Test with uv run python3
from quilto.storage import StorageRepository
from pathlib import Path
from datetime import date, timedelta

# Path(".") → logs/parsed/... → 12 entries found
# Path("logs") → logs/logs/parsed/... → 0 entries found
```

**Location:** `packages/quilto/quilto/storage/repository.py:46-50, 61-68, 79-86`

**Fix Options:**
- Option A: Remove `/logs/` prefix from StorageRepository (breaking change)
- Option B: Document `--storage` should point to parent directory
- Option C: Rename CLI flag to `--storage-base` with clear documentation

---

### Issue 2: Enum String Validation Failure

**Symptom:** ValidationError cascade across Analyzer, Synthesizer, Evaluator nodes.

**Error Pattern:**
```
ValidationError: 1 validation error for AnalyzerInput
query_type
  Input should be an instance of QueryType [type=is_instance_of, input_value='insight', input_type=str]
```

**Root Cause Chain:**

1. `plan_node` converts enum to string for LangGraph state:
   ```python
   # orchestration.py:391-392, 408
   query_type_str = query_type_val.value  # "insight"
   return {"query_type": query_type_str}
   ```

2. `analyze_node` reads string from state, passes to model with `strict=True`:
   ```python
   # orchestration.py:503, 507-509
   query_type = state.get("query_type", "factual")  # Gets string "insight"
   AnalyzerInput(query_type=query_type, ...)  # FAILS - string, not enum
   ```

3. Fallback uses string instead of enum:
   ```python
   # orchestration.py:545
   "verdict": "insufficient",  # Should be Verdict.INSUFFICIENT
   ```

4. Cascade continues to `synthesize_node` and `evaluate_node`.

**Why It Worked at Epic 13:**
- Epic 13 used direct agent calls (no LangGraph)
- LangGraph orchestration introduced in Story 15.3
- Direct calls pass enum instances; LangGraph state serializes to strings

**Location:**
- `packages/quilto/quilto/orchestration.py:391-392, 408, 503, 509, 545, 601, 607`
- `packages/quilto/quilto/agents/models.py` - `strict=True` on Input models

**Fix Options:**
- Option A: Remove `strict=True` from Input models crossing LangGraph state
  - Pros: Simple, Pydantic auto-coerces strings to enums
  - Cons: Slightly reduced type safety
- Option B: Add string→enum conversion in orchestration nodes
  - Pros: Preserves strict validation
  - Cons: More boilerplate, easy to miss conversion points

---

## Affected Models

### Models Requiring Fix (Cross LangGraph State)

| Model | Enum Field | How It Crosses State | Line |
|-------|------------|---------------------|------|
| `AnalyzerInput` | `query_type: QueryType` | Created with `state.get("query_type")` | 503, 509 |
| `SynthesizerInput` | `query_type: QueryType` | Created with `state.get("query_type")` | 601, 607 |
| `AnalyzerOutput` | `verdict: Verdict` | Validated via `model_validate(state["analyzer_output"])` | 583, 666 |
| `RouterOutput` | `input_type: InputType` | Validated via `model_validate(state["router_output"])` | 821 |

### Models NOT Requiring Fix (Don't Cross State)

| Model | Enum Field | Why Safe |
|-------|------------|----------|
| `PlannerInput` | `query_type: QueryType \| None` | Optional, not read from state |
| `PlannerOutput` | `query_type: QueryType` | Created from LLM response, not re-validated |
| `EvaluatorOutput` | `overall_verdict: Verdict` | Created from LLM response, not re-validated |
| `EvaluationDimension` | `verdict: Verdict` | Inside EvaluatorOutput, not separately validated |

---

## Type Ignore Comments (Technical Debt)

These comments in `orchestration.py` suppressed warnings about the type mismatch:

```python
query_type=query_type,  # type: ignore[arg-type]  # Line 509
retrieval_summary=retrieval_summary,  # type: ignore[arg-type]  # Line 511
query_type=query_type,  # type: ignore[arg-type]  # Line 607
```

---

## Deep Dive Findings

### Issue 3: Router Parsing Failures

**Symptom:** `"Failed to parse structured response for agent 'router'"`

**Location:** `packages/quilto/quilto/llm/client.py:316`

**Analysis:** This occurs when LLM returns malformed JSON or missing required fields. The error is logged but may cause downstream failures. This is an LLM reliability issue, not a code bug.

**Severity:** Medium - intermittent, depends on LLM response quality

---

### Issue 4: Pydantic Serialization Warnings

**Symptom:** `"Expected 10 fields but got 6: Expected Message"`

**Analysis:** These warnings come from litellm's internal Pydantic models when serializing LLM response objects. This is a litellm library issue, not our code.

**Severity:** Low - cosmetic warning, doesn't affect functionality

---

### Issue 5: Hardcoded String Verdicts in Fallbacks

**Location:** `orchestration.py`

| Line | Code | Issue |
|------|------|-------|
| 545 | `"verdict": "insufficient"` | Should use enum if `strict=True` kept |
| 550 | `"analysis_verdict": "insufficient"` | String in state (OK, used for routing) |
| 712 | `"eval_verdict": "insufficient"` | String in state (OK, used for routing) |

**Note:** Lines 550 and 712 are state fields used for string comparison in routing functions, not for model validation. Only line 545 is problematic because it's inside a dict that gets validated as `AnalyzerOutput`.

---

### Issue 6: Stale `logs/logs/` Directory

**Symptom:** Empty `logs/logs/` directory exists from before Story 16.3 fix.

**Resolution:** Manual cleanup: `rm -rf ./logs/logs/`

**Severity:** Low - doesn't affect functionality, just confusing

---

## State Flow Analysis

### Data Stored to State (via `.model_dump()`)

| Output | Stored Key | Later Validated As | Has Enum? |
|--------|------------|-------------------|-----------|
| `router_output.model_dump()` | `router_output` | `RouterOutput` (line 821) | Yes - `input_type` |
| `domain_context.model_dump()` | `domain_context` | `ActiveDomainContext` | No |
| `planner_output.model_dump()` | `planner_output` | Not re-validated | - |
| `analyzer_output.model_dump()` | `analyzer_output` | `AnalyzerOutput` (lines 583, 666) | Yes - `verdict` |
| `synthesizer_output.model_dump()` | `synthesizer_output` | Not re-validated | - |
| `evaluator_output.model_dump()` | `evaluator_output` | Not re-validated | - |

---

## Items NOT Requiring Fix

- [ ] ~~Router parsing failures~~ - LLM reliability issue, not code bug
- [ ] ~~Pydantic serialization warnings~~ - litellm library issue
- [x] ~~Other enum fields~~ - Fully mapped above
- [ ] Empty `logs/logs/` cleanup - Manual task, not code fix
- [ ] Test coverage for state serialization - Future improvement

---

## Decision Log

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Fix 1 (Storage) | Option A: Remove `/logs/` prefix | User expectation: `--storage ./logs` stores in `./logs/` |
| Fix 2 (Enum) | Option A: Remove `strict=True` | LangGraph naturally serializes to strings; enums are `str` subclasses so coercion is safe |

---

## Summary of Required Changes

### Fix 1: Storage Path (Quilto)

**File:** `packages/quilto/quilto/storage/repository.py`

Remove `/logs/` from all internal paths:
- Line 48-50: `_ensure_directories()`
- Line 61-68: `_get_raw_path()`
- Line 79-86: `_get_parsed_path()`
- Line 369, 380: `get_global_context()`, `update_global_context()`

### Fix 2: Enum Validation (Quilto)

**File:** `packages/quilto/quilto/agents/models.py`

Remove `strict=True` from these models (or change to `strict=False`):
- `AnalyzerInput` (line 586)
- `SynthesizerInput` (line 664)
- `AnalyzerOutput` (line 627)
- `RouterOutput` (line 138)

---

---

## Broader Code Quality Issues (Deep Dive)

### Category: High Priority Issues

#### Issue 7: `eval_feedback` Type Vulnerability

**Symptom:** Potential crash when accessing `eval_feedback[0]` if it's a string instead of list.

**Location:** `orchestration.py:365-367, 974-975`

```python
# Line 365-367 (plan_node)
eval_feedback = state.get("eval_feedback")
evaluation_feedback = eval_feedback[0] if eval_feedback else None
# Problem: If eval_feedback is a string, returns first character, not first element

# Line 974-975 (retry_node)
reason = eval_feedback[0] if eval_feedback else "insufficient"
# Same problem
```

**Severity:** HIGH - can cause confusing runtime behavior

---

#### Issue 8: Silent Observer Failures

**Symptom:** Observer node catches all exceptions and returns `{}` silently.

**Location:** `orchestration.py:875, 887, 931-936`

```python
# Line 875: Returns {} if Observer disabled
# Line 887: Returns {} if domain_context_dict empty
# Line 931-936:
except Exception as e:
    logger.warning("Observer failed: %s", e)
    return {}
```

**Problem:** No feedback to progress handler. Global context never updated. Subsequent queries use stale context.

**Severity:** HIGH - context learning silently disabled

---

#### Issue 9: Unprotected State Dict Access

**Symptom:** Direct `state["key"]` access without defaults can raise KeyError.

**Location:** `orchestration.py`

| Line | Access | Risk |
|------|--------|------|
| 750 | `state["user_input"]` | KeyError if missing |
| 807 | `state["_quilto"]` | KeyError if missing |
| 871 | `state["_quilto"]` | KeyError if missing |
| 902 | `state["user_input"]` | Mixed pattern - some `.get()`, some direct |

**Severity:** HIGH - causes crashes instead of graceful degradation

---

#### Issue 10: Broad Exception Handling

**Symptom:** `except Exception:` catches ALL errors including system errors.

**Location:**
- `llm/client.py:312` - silently passes in fallback chain
- `llm/client.py:386-410` - `_retry_with_backoff` masks unknown errors
- `cli/app.py:55` - version check silently returns "unknown"

**Problem:** OOM, signal handling, and other critical errors are masked as transient LLM failures.

**Severity:** HIGH - difficult to diagnose production issues

---

### Category: Medium Priority Issues

#### Issue 11: Hardcoded State Keys

**Symptom:** No centralized definition for state keys like `"_quilto"`, `"user_input"`, etc.

**Location:** `orchestration.py` throughout

**Problem:** Typos cause silent failures. Changes require grepping entire codebase.

**Severity:** MEDIUM - maintenance burden, error-prone

---

#### Issue 12: Domain Context Validation Missing

**Symptom:** `ActiveDomainContext.model_validate()` can fail without being caught.

**Location:** `orchestration.py:361, 501, 661, 761, 889`

**Problem:** If domain_context dict is corrupted in state, ValidationError raised with unhelpful message instead of graceful fallback.

**Severity:** MEDIUM - unexpected crashes

---

#### Issue 13: Global Context Silent Fallback

**Symptom:** Context parsing returns defaults without indicating corruption.

**Location:** `storage/context.py:232-239, 270-271`

**Problem:** Corrupted global context files are silently replaced with empty context. Data loss without user knowledge.

**Severity:** MEDIUM - silent data loss

---

#### Issue 14: Hardcoded Magic Numbers

**Symptom:** `max_entries=100` hardcoded without configuration option.

**Location:** `orchestration.py:447`

**Problem:** Can't configure for different domains/use cases.

**Severity:** MEDIUM - inflexible

---

#### Issue 15: Session Pruning Strategy

**Symptom:** Session conversation pruning discards middle turns.

**Location:** `session/session.py:88-92`

**Problem:** "Keeps first turn + last (max_turns-1)" may discard context-critical turns (e.g., user preferences established in turn 3 of 20).

**Severity:** MEDIUM - potential context loss

---

### Category: Low Priority Issues

#### Issue 16: Type Ignore Comments

**Symptom:** 140+ `# type: ignore` comments throughout codebase.

**Key Locations:**
- `orchestration.py:270-271, 355, 378, 380, 397, 403, 405, 509, 511`

**Problem:** Hide legitimate type problems that may become runtime errors.

**Severity:** LOW - technical debt

---

#### Issue 17: Handler Signature Caching

**Symptom:** `_HANDLER_SIGNATURE_CACHE` is global mutable dict with no synchronization.

**Location:** `orchestration.py:160-187`

**Problem:** In multi-session async scenarios, cache may have stale entries.

**Severity:** LOW - edge case

---

#### Issue 18: Missing Feedback Validation

**Symptom:** `IntermediateOutputs` defaults all fields to empty dicts.

**Location:** `cli/feedback.py:31-49`

**Problem:** Can't distinguish between "agent didn't run" and "agent ran but output is truly empty".

**Severity:** LOW - debugging inconvenience

---

## Issue Summary by Severity

| Severity | Count | Issues |
|----------|-------|--------|
| **Critical** | 2 | Storage path doubling, Enum validation |
| **High** | 4 | eval_feedback type, Observer failures, State access, Exception handling |
| **Medium** | 5 | State keys, Domain context validation, Context fallback, Magic numbers, Session pruning |
| **Low** | 3 | Type ignores, Handler cache, Feedback validation |
| **Total** | **14** | |

---

## Recommended Fix Order

### Phase 1: Critical (Block Query Flow)
1. Fix 1: Remove `/logs/` prefix from StorageRepository
2. Fix 2: Remove `strict=True` from 4 models

### Phase 2: High (Stability)
3. Add type checking for `eval_feedback` before indexing
4. Add proper error propagation for Observer failures
5. Replace direct `state["key"]` with `.get("key")` + defaults
6. Narrow exception handling to specific exception types

### Phase 3: Medium (Robustness)
7. Define state key constants
8. Add try/except around domain context validation
9. Add logging for context parsing corruption
10. Make `max_entries` configurable

### Phase 4: Low (Tech Debt)
11. Audit and remove type: ignore comments
12. Add thread safety to handler cache
13. Improve feedback validation structure

---

## Next Steps

1. ~~Deep dive into other potential issues~~ - Complete
2. Review findings with user
3. Get approval to implement fixes
4. Implement Phase 1 fixes (Critical)
5. Implement Phase 2 fixes (High)
6. Update affected tests
7. Verify with reproduction command
8. Clean up stale `logs/logs/` directory
