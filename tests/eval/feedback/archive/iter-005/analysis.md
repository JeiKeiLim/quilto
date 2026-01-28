# Dogfooding Iteration 5 Analysis

Date: 2026-01-28
Source: Story 17.11 - Verify Fixes with Dogfooding

## Summary

**Epic 17 fixes VERIFIED** - Query flow is working. 4 of 5 automated query types succeeded.

**3 new bugs discovered:**
1. CRITICAL: Analyzer silent failure - Synthesizer claims "no data" when Retriever found 23 entries
2. HIGH: `--debug` flag not printing intermediate agent outputs (regression)
3. HIGH: Clarification questions type mismatch causes AttributeError

## Epic 17 Fixes Verified

| Story | Fix | Status |
|-------|-----|--------|
| 17.2 | Remove `/logs/` prefix from StorageRepository | VERIFIED - Retriever finds 10-23 entries |
| 17.3 | Remove `strict=True` from state-crossing models | VERIFIED - No ValidationError |
| 17.4 | Add isinstance check for eval_feedback | VERIFIED - No type crash |
| 17.5 | Add Observer error propagation | VERIFIED - Observer timeout visible in logs |
| 17.6 | Protect state dict access with .get() | VERIFIED - No KeyError |
| 17.7 | Define state key constants | VERIFIED - No typo-related crashes |
| 17.8 | Add domain context validation fallback | VERIFIED - Domain context loads |
| 17.9 | Audit type:ignore comments | N/A - Type safety improvement |
| 17.10 | Add debug logging to exception handlers | VERIFIED - Error traces visible with --debug |

## Dogfooding Results

| Query Type | Query | Result | Entries | Confidence |
|------------|-------|--------|---------|------------|
| Factual | "How many times did I work out last week?" | SUCCESS | 11 | 90% |
| Insight | "How is my training consistency?" | SUCCESS | 23 | 90% |
| Temporal | "What exercises did I do yesterday?" | SUCCESS | 10 | 50% |
| Comparative | "Was my Monday workout harder than Wednesday?" | SUCCESS | 11 | 50% |
| Goal-related | "Am I on track for my fitness goals?" | BUG | - | - |

## New Issues for Epic 18

### Issue 0: Analyzer Silent Failure - Data Not Passed to Synthesizer (CRITICAL)

**Source:** `tests/eval/feedback/active/2026-01-28_14b9034b.json`

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

**User Feedback:**
> "I don't know if retrieval was succeeded because middle output wasn't printed in terminal. Turns out, retrieval was success but I don't know why final response says no records."

**Root Cause Hypothesis:**
1. Analyzer agent failed silently (returned empty `{}`)
2. Retriever entries not passed correctly to Analyzer
3. Or Synthesizer not receiving Analyzer output and not falling back to Retriever entries

**Impact:** Users get completely wrong responses claiming no data when data exists. Trust-destroying bug.

**Priority:** CRITICAL - Higher than all other issues

**Investigation Needed:**
- Check Analyzer node in orchestration.py - why empty output?
- Check state passing between Retriever → Analyzer → Synthesizer
- Add logging to Analyzer to catch silent failures

### Issue 1: Debug Flag Not Printing Intermediate Outputs (HIGH)

**Source:** User feedback in `2026-01-28_14b9034b.json`

**Symptom:**
- `--debug` flag only prints timing summaries
- Does NOT print intermediate agent outputs (Router, Planner, Retriever, Analyzer, Synthesizer)
- User cannot see what each agent returned

**User Feedback:**
> "I don't know if retrieval was succeeded because middle output wasn't printed in terminal."

**Expected Behavior:**
With `--debug`, the CLI should print each agent's output:
```
[Router] input_type=QUERY, domains=[GeneralFitness, Strength, Running]
[Planner] strategy=date_range, start=2025-12-31, end=2026-01-26
[Retriever] found 23 entries
[Analyzer] {...analysis output...}
[Synthesizer] {...response...}
```

**Current Behavior:**
```
ℹ  6042ms - type=query
ℹ  8245ms - action=retrieve
ℹ  4ms - 12 entries
```

**Root Cause:** The `on_agent_complete` callback in CLI is not printing the full `output` dict, only extracting specific fields for timing display.

**Priority:** HIGH - Essential for debugging and user trust (knowing what's happening)

### Issue 2: Clarification Questions Type Mismatch (HIGH)

**Location:** `packages/quilto/quilto/session/session.py:267`

**Symptom:**
```
AttributeError: 'str' object has no attribute 'get'
```

**Root Cause:** `clarify_questions_raw` from LangGraph state sometimes contains strings instead of dicts. The code assumes dict structure: `q.get("question")`.

**Fix:** Add type check before accessing dict methods:
```python
for q in clarify_questions_raw
if isinstance(q, dict) and q.get("question")
```

**Priority:** HIGH - Causes complete query failure

### Issue 3: Pydantic Serialization Warnings (LOW)

**Source:** litellm/Pydantic internal handling

**Symptom:**
```
PydanticSerializationUnexpectedValue: Expected `Message` - serialized value may not be as expected
PydanticSerializationUnexpectedValue: Expected `StreamingChoices` - serialized value may not be as expected
```

**Impact:** Harmless warnings, does not affect functionality. Caused by litellm using different Message/Choices types than Pydantic expects.

**Priority:** LOW - No functional impact, cosmetic only

### Issue 4: Observer Timeout (LOW)

**Symptom:** `observe_node failed: litellm.Timeout`

**Context:** Observer calls LLM to extract patterns from query. If it times out, the query still completes successfully (Observer is non-critical).

**Current Behavior:** Error is logged but doesn't block query flow - graceful degradation working as designed.

**Priority:** LOW - Working as designed, may want to reduce Observer LLM calls or add caching

## Recommendations for Epic 18

1. **Story 18.1:** Fix Analyzer silent failure / data pipeline gap (CRITICAL)
   - Investigate why Analyzer returns empty `{}` when Retriever finds entries
   - Ensure Retriever entries are passed to Analyzer correctly
   - Add fallback: if Analyzer empty, Synthesizer should use Retriever entries directly
   - Add logging to detect Analyzer failures

2. **Story 18.2:** Restore --debug intermediate output printing (HIGH)
   - Update `on_agent_complete` callback in CLI to print full agent outputs
   - Show Router, Planner, Retriever, Analyzer, Synthesizer outputs
   - Essential for debugging and user visibility

3. **Story 18.3:** Fix clarification questions type mismatch (HIGH)
   - Add isinstance check in `_build_process_result`
   - Add test case for string-serialized clarification questions

4. **Story 18.4 (Optional):** Suppress or fix Pydantic serialization warnings
   - Investigate litellm version compatibility
   - Or add warning filter

5. **Story 18.5 (Optional):** Optimize Observer performance
   - Consider caching patterns
   - Or reduce LLM calls for repeated queries

## Feedback Files

6 feedback JSON files created during this session:
- `tests/eval/feedback/active/2026-01-28_*.json`

## Conclusion

Epic 17 successfully fixed the critical query flow issues (storage path, enum validation, etc.). The system is now partially functional for dogfooding.

**However, 3 significant bugs discovered:**
1. **CRITICAL:** Analyzer silent failure causes Synthesizer to claim "no data" when 23 entries were retrieved
2. **HIGH:** `--debug` flag not printing intermediate outputs - users can't see what's happening
3. **HIGH:** Clarification questions type mismatch causes AttributeError

Epic 18 should prioritize:
1. Fix Analyzer data pipeline (CRITICAL - trust-destroying)
2. Restore debug output printing (HIGH - essential for debugging)
3. Fix clarification questions type handling (HIGH - causes failures)
