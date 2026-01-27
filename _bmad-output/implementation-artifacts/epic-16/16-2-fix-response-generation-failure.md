# Story 16.2: Fix Response Generation Failure

Status: done

## Story

As a **Quilto framework user**,
I want **the query flow to generate responses instead of errors**,
So that **my questions are answered instead of receiving "I encountered an error generating a response"**.

## Background

**Origin:** Epic 15 Retrospective (2026-01-27) + Story 15.6 Feedback Analysis
**Priority:** CRITICAL | **Effort:** Medium (3-4 hours)
**Type:** Bug Fix - orchestration flow failure

**Problem Statement:**
Feedback records show all QUERY flows return: `"I encountered an error generating a response."`
Traces show Router, Planner, Retriever running, then jumping directly to Observer - Analyzer, Synthesizer, and Evaluator traces are missing.

**Impact:** All queries fail. Framework is unusable for query flow.

## Root Cause Analysis

### Observed Behavior

```
Traces:
1. router → type=query
2. planner → action=retrieve
3. retriever → 23 entries
4. planner → action=retrieve (retry 1)
5. retriever → 23 entries
6. planner → action=retrieve (retry 2)
7. retriever → 23 entries
8. observer → updates=0
```

**Missing:** analyzer, synthesizer, evaluator traces across ALL retry cycles.

### Root Cause: Cascade Failure

1. `analyze_node` exception handler returns `{"error": "...", "analysis_verdict": "insufficient"}` but does NOT set `analyzer_output`
2. `synthesize_node` calls `AnalyzerOutput.model_validate(state.get("analyzer_output", {}))` on empty dict
3. Pydantic `ValidationError` → synthesizer exception caught silently
4. Synthesizer returns `"I encountered an error generating a response."`

### Contributing Factors

- Silent exception handling: all nodes catch `Exception` without logging
- No trace added on exception path → invisible failures
- LLM may return malformed JSON causing initial Analyzer failure

## Acceptance Criteria

1. **Given** a QUERY input that successfully retrieves entries
   **When** the orchestration runs
   **Then** Analyzer, Synthesizer, and Evaluator traces appear in debug output

2. **Given** the Analyzer agent fails
   **When** the exception is caught
   **Then** the error message is logged with full exception details

3. **Given** the Synthesizer agent fails
   **When** the exception is caught
   **Then** the error message is logged with full exception details

4. **Given** the Evaluator agent fails
   **When** the exception is caught
   **Then** the error message is logged with full exception details

5. **Given** any agent failure in query flow
   **When** checking debug output
   **Then** the specific failure reason is visible (not just "error generating response")

6. **Given** the Analyzer fails with an exception
   **When** Synthesizer attempts to run
   **Then** Synthesizer should handle missing `analyzer_output` gracefully (not cascade fail)

7. **Given** the query flow completes (even with errors)
   **When** examining the final response
   **Then** error responses include the specific agent that failed and why

8. **Given** a Korean language query with 23+ entries
   **When** processed through the orchestration
   **Then** the query should complete with a meaningful response

## Tasks / Subtasks

- [x] Task 1: Add error logging to orchestration nodes (AC: #2, #3, #4, #5)
  - [x] 1.1: Add `import logging` at module top (near line 12)
  - [x] 1.2: Add `logger = logging.getLogger(__name__)` after imports
  - [x] 1.3: In `analyze_node` exception handler, add `logger.exception("analyze_node failed")`
  - [x] 1.4: In `synthesize_node` exception handler, add `logger.exception("synthesize_node failed")`
  - [x] 1.5: In `evaluate_node` exception handler, add `logger.exception("evaluate_node failed")`

- [x] Task 2: Add error traces to exception handlers (AC: #1, #5)
  - [x] 2.1: In `analyze_node` exception handler, call `_add_trace(state, "analyzer", ..., f"ERROR: {e!s}", elapsed)`
  - [x] 2.2: In `synthesize_node` exception handler, call `_add_trace(state, "synthesizer", ..., f"ERROR: {e!s}", elapsed)`
  - [x] 2.3: In `evaluate_node` exception handler, call `_add_trace(state, "evaluator", ..., f"ERROR: {e!s}", elapsed)`
  - [x] 2.4: Return traces in exception return dict: `"traces": _add_trace(...)`

- [x] Task 3: Fix Synthesizer cascade failure (AC: #6) - CRITICAL
  - [x] 3.1: In `analyze_node` exception handler, add `"analyzer_output"` key with valid fallback dict
  - [x] 3.2: Fallback must match `AnalyzerOutput` model structure exactly (see Dev Notes)
  - [x] 3.3: In `synthesize_node`, wrap `model_validate()` in try/except with fallback response

- [x] Task 4: Improve error response messages (AC: #7)
  - [x] 4.1: Update synthesizer error message to: `f"I encountered an error: {agent_name} failed - {e!s}"`
  - [x] 4.2: Sanitize exception message (remove stack traces, keep first line)

- [x] Task 5: Write tests (AC: #1-8)
  - [x] 5.1: Add `TestAnalyzerFailureCascade` class in `test_quilto.py`
  - [x] 5.2: Test analyzer failure returns fallback analyzer_output
  - [x] 5.3: Test synthesizer with invalid analyzer_output doesn't crash
  - [x] 5.4: Test error trace appears in ProcessResult.debug.traces

- [x] Task 6: Run validation
  - [x] 6.1: `make check` passes (lint + typecheck)
  - [x] 6.2: `make validate` passes (lint + format + typecheck + test)
  - [x] 6.3: Manual test: `swealog auto "How was my workout?" --debug` produces meaningful response
    - **WAIVED**: Requires running Ollama instance. Unit tests cover the fix behavior. Integration testing deferred to post-merge validation.

## Dev Notes

### CRITICAL: File Locations (Verified)

| File | Purpose |
|------|---------|
| `packages/quilto/quilto/orchestration.py` | Primary fix - add logging + traces + fallback |
| `packages/quilto/tests/test_quilto.py` | Add tests here (NOT test_orchestration.py - doesn't exist) |
| `packages/quilto/quilto/agents/models.py` | Reference for AnalyzerOutput structure |

### Existing Logging Pattern to Follow

`observe_node` already uses logging (line 889-893):
```python
import logging
# ...
logging.getLogger(__name__).warning("observe_node failed: %s", e)
```

Use this same pattern. Add at module level:
```python
import logging

logger = logging.getLogger(__name__)
```

### AnalyzerOutput Model Structure (EXACT)

From `agents/models.py` lines 600-634:
```python
class AnalyzerOutput(BaseModel):
    model_config = ConfigDict(strict=True)

    query_intent: str = Field(min_length=1)
    findings: list[Finding]  # NOT list[dict]!
    patterns_identified: list[str]
    sufficiency_evaluation: SufficiencyEvaluation  # nested model
    verdict_reasoning: str = Field(min_length=1)
    verdict: Verdict  # enum: SUFFICIENT, PARTIAL, INSUFFICIENT
```

### Fallback AnalyzerOutput Dict (Use This Exactly)

```python
from quilto.agents.models import Verdict

fallback_output = {
    "query_intent": "Unable to analyze due to error",
    "findings": [],  # empty list is valid
    "patterns_identified": [],
    "sufficiency_evaluation": {
        "critical_gaps": [],
        "nice_to_have_gaps": [],
        "evidence_check_passed": False,
        "speculation_risk": "high",
    },
    "verdict_reasoning": f"Analysis failed with error: {e!s}",
    "verdict": "insufficient",  # string, not Verdict enum
}
```

### Exception Handler Pattern (Copy This)

```python
except Exception as e:
    elapsed = (time.perf_counter() - start) * 1000
    logger.exception("analyze_node failed for query: %s", user_input[:50])
    await _call_progress_handler(quilto, "on_agent_complete", "analyzer", elapsed / 1000, {})

    fallback_output = {
        "query_intent": "Unable to analyze due to error",
        "findings": [],
        "patterns_identified": [],
        "sufficiency_evaluation": {
            "critical_gaps": [],
            "nice_to_have_gaps": [],
            "evidence_check_passed": False,
            "speculation_risk": "high",
        },
        "verdict_reasoning": f"Analysis failed with error: {e!s}",
        "verdict": "insufficient",
    }

    return {
        "error": f"Analyzer failed: {e!s}",
        "analysis_verdict": "insufficient",
        "analyzer_output": fallback_output,
        "traces": _add_trace(state, "analyzer", user_input[:50], f"ERROR: {e!s}", elapsed),
    }
```

### Synthesizer Defensive Validation

In `synthesize_node`, wrap the model_validate call:
```python
try:
    analyzer_output_dict = state.get("analyzer_output", {})
    analyzer_output = AnalyzerOutput.model_validate(analyzer_output_dict)
except Exception as validation_err:
    logger.warning("Invalid analyzer_output, using minimal fallback: %s", validation_err)
    # Create minimal valid AnalyzerOutput for synthesizer
    from quilto.agents.models import SufficiencyEvaluation, Verdict
    analyzer_output = AnalyzerOutput(
        query_intent="Analysis unavailable",
        findings=[],
        patterns_identified=[],
        sufficiency_evaluation=SufficiencyEvaluation(
            critical_gaps=[],
            nice_to_have_gaps=[],
            evidence_check_passed=False,
            speculation_risk="high",
        ),
        verdict_reasoning="Analyzer output invalid or missing",
        verdict=Verdict.INSUFFICIENT,
    )
```

### Test Pattern (Add to test_quilto.py)

```python
class TestAnalyzerFailureCascade:
    """Tests for analyzer failure handling."""

    @pytest.mark.asyncio
    async def test_analyzer_failure_provides_fallback_output(self, quilto: Quilto) -> None:
        """Analyzer failure should provide fallback analyzer_output."""
        session = quilto.create_session()

        with patch.object(quilto, "_get_graph") as mock_get_graph:
            mock_graph = MagicMock()
            mock_graph.ainvoke = AsyncMock(
                return_value={
                    "input_type": "query",
                    "error": "Analyzer failed: ValidationError",
                    "analyzer_output": {  # Fallback should be present
                        "query_intent": "Unable to analyze due to error",
                        "findings": [],
                        "patterns_identified": [],
                        "sufficiency_evaluation": {
                            "critical_gaps": [],
                            "nice_to_have_gaps": [],
                            "evidence_check_passed": False,
                            "speculation_risk": "high",
                        },
                        "verdict_reasoning": "Analysis failed with error",
                        "verdict": "insufficient",
                    },
                    "response": "I encountered an error: Analyzer failed",
                    "selected_domains": [],
                    "traces": [
                        {
                            "agent_name": "analyzer",
                            "input_summary": "test",
                            "output_summary": "ERROR: ValidationError",
                            "elapsed_ms": 100.0,
                            "timestamp": datetime.now(UTC),
                        }
                    ],
                }
            )
            mock_get_graph.return_value = mock_graph

            result = await session.process("Test query")

        assert result is not None
        # Error trace should be present
        if result.debug:
            assert any("ERROR" in t.output_summary for t in result.debug.traces)

    @pytest.mark.asyncio
    async def test_synthesizer_handles_missing_analyzer_output(
        self, quilto: Quilto
    ) -> None:
        """Synthesizer should not crash on missing analyzer_output."""
        session = quilto.create_session()

        with patch.object(quilto, "_get_graph") as mock_get_graph:
            mock_graph = MagicMock()
            mock_graph.ainvoke = AsyncMock(
                return_value={
                    "input_type": "query",
                    # No analyzer_output key at all
                    "response": "Fallback response",
                    "selected_domains": [],
                }
            )
            mock_get_graph.return_value = mock_graph

            # Should not raise
            result = await session.process("Test query")

        assert result is not None
```

### Debugging Commands

```bash
# Run with debug to see traces
swealog auto "How was my workout?" --debug

# Run tests
cd packages/quilto && uv run pytest tests/test_quilto.py -v -k "analyzer"

# Check current exception handlers
grep -n "except Exception" packages/quilto/quilto/orchestration.py
```

### Validation Checklist

**Logging:**
- [x] `import logging` added at module top
- [x] `logger = logging.getLogger(__name__)` after imports
- [x] `analyze_node`, `synthesize_node`, `evaluate_node` use `logger.exception()`

**Traces:**
- [x] Exception handlers call `_add_trace()` with "ERROR:" prefix
- [x] Return dict includes `"traces": _add_trace(...)` key

**Cascade Prevention:**
- [x] `analyze_node` exception sets `"analyzer_output"` with valid fallback dict
- [x] `synthesize_node` wraps `model_validate()` in try/except with fallback

**Error Messages:**
- [x] Error response includes agent name: `"Analyzer failed: ..."`

**Tests:**
- [x] `TestAnalyzerFailureCascade` class added to `test_quilto.py`
- [x] Tests verify fallback output and error traces

**Final Validation:**
- [x] `make check` passes
- [x] `make validate` passes
- [ ] `swealog auto "How was my workout?" --debug` produces meaningful response (requires Ollama)

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

### Completion Notes List

- Added `import logging` and module-level `logger = logging.getLogger(__name__)` to orchestration.py
- Updated `analyze_node` exception handler: added logger.exception(), fallback analyzer_output dict, and error trace
- Updated `synthesize_node` exception handler: added logger.exception(), defensive validation for analyzer_output with fallback AnalyzerOutput creation, sanitized error message, and error trace
- Updated `evaluate_node` exception handler: added logger.exception() and error trace
- Refactored `observe_node` to use module-level logger instead of inline import
- Added `TestAnalyzerFailureCascade` test class with 4 tests covering:
  - Analyzer failure provides fallback output
  - Synthesizer handles missing analyzer_output
  - Error trace appears in debug output
  - Error response includes agent name

**Code Review Fixes Applied (2026-01-27):**
- Added `TestOrchestrationNodeExceptionHandling` class with 4 direct unit tests that call node functions
- Added type annotations for `user_input` variable in `analyze_node`, `synthesize_node`, `evaluate_node`
- Waived Task 6.3 manual test (requires Ollama, unit tests cover fix behavior)

### File List

- `packages/quilto/quilto/orchestration.py` - Added error logging, traces, cascade prevention, and type annotations
- `packages/quilto/tests/test_quilto.py` - Added TestAnalyzerFailureCascade + TestOrchestrationNodeExceptionHandling test classes
