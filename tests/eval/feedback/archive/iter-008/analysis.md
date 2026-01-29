# Iteration 008 Analysis - Epic 19 Verification

## Executive Summary

### Automated Dogfooding (iter-008)

- **Total queries:** 16 (including Task 1/2 verification queries + Task 3 dogfooding)
- **Success rate (rating >= 3):** 81% (13/16)
- **Average rating:** 3.94/5
- **Target success rate (>= 90%):** NOT MET (81%)

### User Manual Testing (iter-008-pre)

- **Total queries:** 7 (manual testing by Jongkuk Lim during/after Story 19.1 and 19.2 development)
- **With user feedback:** 7/7 (all have detailed `user_feedback` field)
- **Results:** 1 cascade fail, 1 Planner skip, 1 CORRECTION success (but wrong semantics), 4 good responses
- **New patterns identified:** 6 (Patterns 4-9, all from user feedback)

### Combined

- **Total queries (both datasets):** 23
- **Total patterns identified:** 9
- **CRITICAL:** 1 (CORRECTION entry matching), **HIGH:** 4, **MEDIUM:** 2, **LOW:** 2

### Rating Distribution (iter-008 automated)

| Rating | Count | Queries |
|--------|-------|---------|
| 5/5 | 8 | 3.0, 3.2, 3.3, 3.4, 3.5, 3.10, 1.1, 2.1 |
| 4/5 | 3 | 3.6, 3.9, 2.5 |
| 3/5 | 2 | 3.7, 2.3 |
| 1/5 | 3 | 1.2 (CORRECTION), 3.1 (CORRECTION), 3.8 (Router empty) |

### iter-008-pre User Feedback Summary

| File | Query | User Verdict | Key Issue |
|------|-------|-------------|-----------|
| `0443fda2` | "I haven't gone to gym..." | FAIL | 2 timeouts + 3 schema validation errors |
| `0443fda2_082701` | Same (retry) | FAIL | Planner skipped retrieval, generic advice |
| `3bcee676` | CORRECTION (treadmill 40min) | Partial | Succeeded but wrong semantics (new entry, bad global context) |
| `3c73a11e` | "Should I force myself to go?" | Good | Observer fabricated preference from synthesizer |
| `8943ace6` | "Summarize this month + plan" | Good | Timeouts but recovered |
| `90c94c13` | "Look at my previous logs" | Good | Session continuity broken (pre-19.2) |
| `dd9b77f4` | "Tell me about my last workout" | Good | Observer hallucinated facts |

## Epic 19 Fix Verification

### Story 19.1 -- CORRECTION Flow Fix: FAIL

**Status:** The code fix is correct, but the Parser LLM does not comply.

**Evidence:**
- Task 1.2: "I logged 5 sets of pull-ups but it should be 4 sets" -> `is_correction: false`, `error_message: "Parser did not identify correction"`
- Task 1.2 retry: Same result on second attempt (not intermittent)
- Task 3.1: "Actually I ran 3km not 5km yesterday" -> Same failure

**Root Cause Analysis:**

The Story 19.1 fix (commit `f0d59f0`) correctly addressed 3 bugs:
1. Bug 1: Parser now receives `user_input` (not Router reasoning) -- **VERIFIED in code** (orchestration.py:1028)
2. Bug 2: `correction_node()` now sets `StateKeys.RESPONSE` -- **VERIFIED** (response generated, even for failures)
3. Bug 3: `ProcessResult.correction_result` field added -- **VERIFIED** (field present in debug output)

However, the Parser LLM (via OpenRouter) returns `is_correction: false` despite:
- Being explicitly told `correction_mode = True` in the prompt
- The prompt containing "IMPORTANT: Set is_correction = true"
- Receiving the actual user text with correction language

The prompt at `parser.py:131-163` tells the LLM to set `is_correction = false` if "no entry matches" (line 161). The LLM appears to fail at entry matching -- it cannot identify which recent entry to correct from the formatted entry list, so it defaults to `is_correction: false`.

**Likely underlying issue:** The recent entries format (`{entry_id}, {date}, {content_summary}`) may not give the LLM enough information to match against the correction target. The entry IDs are timestamp-based (e.g., `2026-01-29_00-06-53`) and content summaries are truncated, making it hard for the LLM to correlate "5 sets of pull-ups" with the right entry.

**Important update from iter-008-pre:** CORRECTION **did succeed once** (file `3bcee676`, query "Actually my last treadmill run was for 40 minutes with 8kph speed" -> `success: true`, `target_entry_id: "2026-01-26_18-33-00"`). This means the issue is **intermittent/LLM-dependent**, not a hard code bug. The Parser sometimes sets `is_correction: true` and sometimes doesn't, depending on LLM output variance.

However, even when CORRECTION succeeds, the **semantics are wrong** (user feedback from `3bcee676`):
- CORRECTION creates a new raw entry instead of modifying the existing one
- Global context gets polluted with per-session facts
- User expects: modify `raw/2026-01-26.md` at the relevant section, re-parse, update parsed file

### Story 19.2 -- Session Persistence Fix: PASS

**Status:** All checks passed.

| Check | Result |
|-------|--------|
| Session ID printed (not `:memory:`) | PASS |
| Session resumes with `--session <id>` | PASS |
| Conversation context preserved | PASS (Planner interpreted "What about last week?" correctly) |
| `--no-persist` flag works | PASS |
| No "Session not found" warning | PASS |

## Regression Check

### QUERY Flow: PASS

All QUERY types work correctly (factual, insight, temporal, recommendation, Korean, goal). This matches iter-006 (100%) and iter-007 performance.

### LOG Flow: PASS

Both English and Korean LOG entries were correctly parsed and stored:
- English: "I ran 5km yesterday" -> Running domain, date correctly resolved
- Korean: "오늘 스쿼트 3세트 10개씩 60kg" -> Strength domain, 3x10@60kg extracted

### BOTH Flow: PASS

"I ran 5km today. How does that compare to my recent runs?" -> Entry logged AND comparison response generated.

### Multilingual: PASS

Korean query "이번 달 운동 요약해줘" returned Korean response (language matching works).

## New Patterns Identified

### From iter-008 (automated dogfooding)

### Pattern 1 (CRITICAL): Parser Correction Entry Matching Failure

- **Impact:** CORRECTION flow is non-functional in automated run (0/3)
- **Root cause:** Parser LLM cannot match correction target to recent entries
- **Frequency:** 100% (3/3 automated CORRECTION attempts failed)
- **Note:** iter-008-pre shows CORRECTION **did succeed once** (file `3bcee676`) -- the issue is intermittent/LLM-dependent, not 100% broken
- **Recommendation:** Improve entry matching in correction prompt -- include more entry detail (full raw_content, not truncated), or implement a non-LLM matching heuristic (fuzzy text matching on raw_content + date)

### Pattern 2 (MEDIUM): Router Empty Output on Transient LLM Failure

- **Impact:** Complete cascade failure (empty response)
- **Root cause:** Rate limit or transient error causes Router to return `{}`, which then fails domain_context validation
- **Frequency:** 1/16 queries (6%)
- **Recommendation:** Add retry logic for Router failures, or validate Router output before proceeding

### Pattern 3 (LOW): Timeout on Complex Queries with Many Entries

- **Impact:** Degraded response quality and confidence
- **Root cause:** Large entry count (23+) with complex Korean prompt causes LLM timeout
- **Frequency:** 1/16 queries (6%)
- **Recommendation:** Existing retry/timeout config (from Story 12.3) handles this; no action needed unless frequency increases

### From iter-008-pre (user manual testing, 7 queries)

### Pattern 4 (HIGH): Planner Skips Retrieval for Recommendation Queries

- **Impact:** Generic advice instead of personalized response based on user data
- **Source:** `0443fda2_082701` -- "I haven't gone to gym. What do I do today?"
- **Root cause:** Planner set `next_action: "synthesize"` and `sub_queries: []`, skipping retrieval entirely
- **User feedback:** *"So it didn't even try to retrieve my recent logs? This is complete failure. The goal is always try to give tailored answer."*
- **Recommendation:** Planner must ALWAYS retrieve recent logs for recommendation queries. Personalization requires data.

### Pattern 5 (HIGH): Observer Fabricates User Preferences from Agent Output

- **Impact:** Global context polluted with false user preferences
- **Source:** `3c73a11e` -- Observer recorded "User prefers light or mobility-focused workout" but user never said this; it was the Synthesizer's suggestion
- **User feedback:** *"Observer should only note something from me not from agents. `User seeks guidance on whether to force a gym visit despite low motivation` this part was okay but later part is just fabrication."*
- **Recommendation:** Observer must distinguish between user-stated facts/preferences and agent-generated recommendations. Only persist what the USER actually said.

### Pattern 6 (HIGH): Correction Creates New Entry Instead of Modifying Existing

- **Impact:** Correction semantics fundamentally wrong -- creates duplicate instead of editing
- **Source:** `3bcee676` -- Correction succeeded but created a new raw log entry and a new parsed entry
- **User feedback:** *"Ideal is that fix previous records in raw file... modify raw/2026-01-26.md at ## 18:33 part and run parser agent then give it to application so that it handles whether to update parsed file or not. And no global context update."*
- **Recommendation:** CORRECTION should modify the existing raw entry in-place, not create a new one. Re-parse after edit. No new log entry creation.

### Pattern 7 (HIGH): Global Context Stores Facts When It Should Store Preferences/Goals/Insights

- **Impact:** Global context becomes a noisy fact dump instead of a user memory system
- **Source:** `3bcee676` -- Observer stored "run_2026-01-26: duration_minutes: 40, distance_km: 5.33" as a "fact" in global context
- **User feedback:** *"Global context is supposed to be user's preference, goal, insights something like that... Think of how Claude or ChatGPT manages user memory."*
- **Mental model:** Global context = user preferences, goals, behavioral patterns (e.g., "when user says 'run', they mean outdoor running"). NOT individual workout facts.
- **Recommendation:** Restrict Observer to only persist: (a) user preferences, (b) stated goals, (c) behavioral insights. Filter out per-session facts.

### Pattern 8 (MEDIUM): Multiple Schema Validation Errors in Single Query (Cascading)

- **Impact:** Complete query failure with no recovery
- **Source:** `0443fda2` -- Analyzer, Synthesizer, and Observer all failed with JSON schema validation errors
- **User feedback:** *"2 timeout and 3 schema validation error. That's odd for too many error in single query."*
- **Recommendation:** Add independent error handling per agent; one agent's failure shouldn't cascade to others

### Pattern 9 (LOW): Observer Hallucinates Facts Not in Any Log Entry

- **Impact:** False information stored in global context
- **Source:** `dd9b77f4` -- Observer stored "3 km run on 2026-01-28; user reported feeling sluggish, possibly due to cold weather" -- none of this was in any entry
- **Recommendation:** Observer should only extract facts directly stated by user. Add validation against actual entries.

## Recommendations

### Epic 20 Story Recommendations

1. **Story 20.1 (CRITICAL): Fix Parser Correction Entry Matching + Correction Semantics**
   - Root cause: Parser LLM fails to match correction target to recent entries (intermittent -- succeeded once in iter-008-pre)
   - Additional: Correction should modify existing raw entry in-place, not create new entry (user feedback from `3bcee676`)
   - Options:
     a. Improve prompt: Include full raw_content in recent entries (not truncated at 50 chars)
     b. Add pre-matching heuristic: Use fuzzy text matching to narrow candidates before LLM call
     c. Simplify matching: Instead of asking LLM to match, always use the most recent entry matching the correction domain
   - AC: CORRECTION queries return `is_correction: true` and modify existing raw files (not create new entries)

2. **Story 20.2 (HIGH): Fix Observer to Only Persist User-Stated Information**
   - Observer currently fabricates preferences from agent output (Pattern 5) and hallucinates facts (Pattern 9)
   - Observer stores per-session facts in global context when it should only store preferences/goals/insights (Pattern 7)
   - AC: Observer only persists (a) user preferences, (b) stated goals, (c) behavioral patterns derived from user statements. Never persists agent recommendations or per-session facts.

3. **Story 20.3 (HIGH): Planner Must Always Retrieve for Personalization Queries**
   - Planner sometimes skips retrieval for recommendation queries (Pattern 4)
   - AC: For QUERY and BOTH types, Planner always includes at least one retrieval instruction. Never `sub_queries: []`.

4. **Story 20.4 (MEDIUM): Add Router Output Validation and Retry**
   - Router returning `{}` causes complete cascade failure (Pattern 2)
   - Add: (a) Validate Router output fields before proceeding, (b) Retry once on empty output
   - AC: Transient Router failures don't produce empty responses

5. **Story 20.5 (MEDIUM): Dogfooding Iteration 9** (post-fixes)
   - Verify CORRECTION flow, Observer behavior, Planner retrieval after fixes
   - Target: >= 90% success rate

### Feedback Infrastructure Improvements (from user)

6. **Story 20.6 (LOW): Add Session ID to Feedback JSON**
   - Currently feedback JSON has no session ID for tracking which session generated it
   - Add `session_id` field to feedback JSON structure

7. **Story 20.7 (LOW): Structured User Feedback in JSON**
   - Current: `"user_feedback": "free text"`, `"feedback_sentiment": null`
   - Proposed: `"feedback": {"content": "feedback text", "by": "user" | "claude", "sentiment": "positive" | "negative" | null}`
   - Enables prioritization: user feedback with negative sentiment = high priority for review

## Previous Iteration Comparison

| Iteration | Epic | Success Rate | Avg Rating | Key Finding |
|-----------|------|--------------|------------|-------------|
| iter-003 | 13 | 81% | N/A | 4 patterns identified |
| iter-005 | 17 | 80% (4/5) | N/A | 3 bugs -> Epic 18 |
| iter-006 | 18 | 100% (13/13) | 4.64/5 | All fixes verified |
| iter-007 | 18 | 90% (9/10) | N/A | CORRECTION broken + session DB |
| **iter-008** | **19** | **81% (13/16)** | **3.94/5** | **CORRECTION still broken, session fixed** |

The success rate drop from iter-007 (90%) to iter-008 (81%) is primarily due to the CORRECTION flow remaining broken (3 failures) plus one transient Router error. Excluding CORRECTION-type queries, the success rate is 92% (12/13).

## Conclusion

**Epic 19 is PARTIALLY validated:**
- Story 19.2 (Session Persistence): FULLY VERIFIED
- Story 19.1 (CORRECTION Flow): CODE FIX VERIFIED but LLM behavior not fixed -- Parser prompt needs improvement

The CORRECTION flow failure is a **prompt engineering issue**, not a code bug. The three code bugs from Story 19.1 were correctly fixed, but the Parser LLM still cannot match correction targets to recent entries. This requires a new story (recommended: Story 20.1) to improve the correction entry matching logic.
