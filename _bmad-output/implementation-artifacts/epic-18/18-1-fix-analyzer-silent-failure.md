# Story 18.1: Fix Analyzer Silent Failure

Status: backlog

## Story

As a **Swealog user**,
I want the Synthesizer to use retrieved data correctly,
so that I don't see "no data" responses when data exists.

## Problem Statement

**Source:** Story 17.11 Dogfooding - `tests/eval/feedback/archive/iter-005/2026-01-28_14b9034b.json`

**Query:** "내가 지금까지 했던 모든 운동을 총 정리해서 알려주는데 나의 운동 상태가 어떤지 종합적으로 분석하여 알려줘"

**Symptom:**
- Retriever found 23 detailed workout entries
- Synthesizer claims "운동 기록이 없기 때문에" (no workout records)
- User sees incorrect "no data" response when data clearly exists

**Evidence from feedback JSON:**
```json
"retriever": { "total_entries_found": 23, "entries": [...23 rich entries...] }
"analyzer": {}  // EMPTY - Silent failure
"synthesizer": { "response": "현재 제공된 운동 기록이 없기 때문에..." }
```

**Impact:** Trust-destroying bug - users get completely wrong responses.

## Acceptance Criteria

1. **Given** Retriever finds N > 0 entries
   **When** Analyzer processes them
   **Then** Analyzer output is NOT empty `{}`

2. **Given** Analyzer returns empty output
   **When** Synthesizer receives state
   **Then** Synthesizer falls back to Retriever entries directly

3. **Given** Analyzer fails silently
   **When** state is checked
   **Then** `analyzer_error` field indicates the issue (similar to Observer error propagation in Story 17.5)

4. **Given** full query flow
   **When** data exists in storage
   **Then** response reflects that data (not "no data")

## Investigation Tasks

- [ ] Task 1: Add debug logging to `analyze_node` in orchestration.py
  - Log entries received from state
  - Log AnalyzerInput construction
  - Log Analyzer LLM response
  - Log AnalyzerOutput validation

- [ ] Task 2: Check state passing: Retriever → Analyzer
  - Verify `entries` key is populated after retrieve_node
  - Verify analyze_node reads `entries` correctly
  - Check if entries format matches AnalyzerInput expectations

- [ ] Task 3: Check Analyzer prompt/response
  - Review Analyzer system prompt for edge cases
  - Check if Korean queries cause issues
  - Check if large entry counts (23) cause truncation

## Fix Tasks (after investigation)

- [ ] Task 4: Implement fix based on root cause
- [ ] Task 5: Add Synthesizer fallback to Retriever entries when Analyzer empty
- [ ] Task 6: Add `analyzer_error` field for error propagation (per Story 17.5 pattern)
- [ ] Task 7: Add unit tests for the fix
- [ ] Task 8: Run validation - `make check` during dev, `make validate` before commit

## Dev Notes

### Root Cause Hypotheses

1. **Analyzer LLM timeout** - Large Korean query + 23 entries may exceed timeout
2. **AnalyzerInput construction failure** - Silent exception in model construction
3. **State key mismatch** - Retriever stores under different key than Analyzer reads
4. **Entry format mismatch** - Retriever entries don't match AnalyzerInput.entries type

### Story 17.5 Pattern Reference

Observer error propagation pattern from Story 17.5:
```python
except Exception as e:
    error_info = {"error": str(e), "error_type": type(e).__name__}
    await _call_progress_handler(quilto, "on_agent_complete", "analyzer", elapsed / 1000, error_info)
    logger.warning("analyze_node failed: %s", e)
    return {"analyzer_error": str(e)}
```

### Files to Investigate

- `packages/quilto/quilto/orchestration.py` - analyze_node function
- `packages/quilto/quilto/agents/analyzer.py` - Analyzer agent
- `packages/quilto/quilto/agents/models.py` - AnalyzerInput, AnalyzerOutput

### References

- [Source: `tests/eval/feedback/archive/iter-005/analysis.md` - Issue 0]
- [Source: `tests/eval/feedback/archive/iter-005/2026-01-28_14b9034b.json`]
- [Pattern: Story 17.5 - Observer error propagation]
