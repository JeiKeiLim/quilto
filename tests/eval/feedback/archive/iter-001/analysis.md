# Iteration 1 Feedback Analysis

**Date Range:** 2026-01-20 to 2026-01-24
**Records Analyzed:** 9
**LLM Provider:** OpenRouter (llm-config-openai.yaml)
**Analyst:** Mary (Business Analyst) + Jongkuk Lim

---

## Executive Summary

Iteration 1 dogfooding revealed **6 distinct patterns** affecting user experience. The most critical issues are:
1. Clarification questions never trigger (over-corrected from previous fix)
2. Planner skips user logs for recommendation queries
3. Malformed JSON from OpenRouter causes application crashes

**Recommendation:** Prioritize Stories 12.1, 12.2, and 12.3 for Epic 12.

---

## Records Summary

| # | ID | Date | Query Summary | Entries Retrieved | Sentiment |
|---|-----|------|---------------|-------------------|-----------|
| 1 | `f89c6142` | 2026-01-20 17:35 | What workout did I log today? | 0 (malformed date) | **Negative** |
| 2 | `f89c6142_183624` | 2026-01-20 18:36 | Same as #1 | 1 | **Positive** |
| 3 | `fec3d15f` | 2026-01-20 18:40 | What workout tomorrow? | 6 | **Mixed** |
| 4 | `db9b34b5` | 2026-01-20 18:44 | Compare last week vs this week | 4 | **Mixed** |
| 5 | `8e8e6d87` | 2026-01-21 06:34 | Summarize all my workouts | 12 | **Mixed** |
| 6 | `14b9034b` | 2026-01-21 06:41 | Summarize + analyze comprehensively | 12 | **Mixed** |
| 7 | `e16dbc36` | 2026-01-22 09:37 | Can I finish marathon in 5 hours? | 0 | **Negative** |
| 8 | `e16dbc36_190829` | 2026-01-22 19:08 | Same as #7 | 0 | **Negative** |
| 9 | `3ec25871` | 2026-01-24 14:03 | Should I maintain current level? | 3 | **Mixed** |

### Sentiment Distribution

- **Positive:** 1 (11%)
- **Mixed:** 5 (56%)
- **Negative:** 3 (33%)

---

## Pattern Analysis

### Pattern 1: Clarification Never Triggers
**Severity:** High | **Evidence:** All 9 records

**Description:** The Clarifier agent was designed to ask about non-retrievable gaps (SUBJECTIVE, CLARIFICATION types). However, after a previous fix to reduce over-prompting, clarification questions no longer trigger even when critical.

**Root Cause:**
- Original issue: Clarification triggered too often (even when data was retrieved)
- Fix applied: Reduced clarification triggers
- Result: Now clarification never triggers (went too far)

**Evidence:**
- Records 7 & 8 (`e16dbc36`): Analyzer identified critical SUBJECTIVE gaps ("user's current running fitness") but flow went to Synthesize with generic response instead of Clarify.

**Impact:** Users receive generic advice when personalized guidance requires additional context.

---

### Pattern 2: Retrieval Strategy Misses User Logs
**Severity:** High | **Evidence:** `e16dbc36`, `e16dbc36_190829`

**Description:** Planner chooses `topical` or `keyword` strategy with narrow terms (e.g., "marathon") that don't match user's actual log content, resulting in 0 entries retrieved despite relevant data existing.

**Root Cause:**
- Planner reasoning: "No personal historical data is required" - INCORRECT
- Planner used `topical` strategy with "marathon" keyword
- User's running logs don't contain word "marathon" but are highly relevant

**Evidence:**
- Record 7: User asked about marathon training, has running logs (5km, 10km runs), retrieved 0 entries
- User feedback: "it did not refer to my logs even though there are related running logs"

**Impact:** Responses are generic instead of personalized, violating core project value proposition.

---

### Pattern 3: LLM Timeout Too Long
**Severity:** Medium | **Evidence:** Operational observation

**Description:** litellm's default timeout is 600 seconds (10 minutes). When OpenRouter hangs, users wait excessively before retry/fallback triggers.

**Root Cause:**
- No explicit timeout configuration in `LLMConfig`
- Uses litellm default (600 seconds)

**Decision:** Set uniform 45-second timeout as balance between quick response and allowing complex reasoning.

---

### Pattern 4: Malformed JSON Crashes Application
**Severity:** High | **Evidence:** `f89c6142`, `e16dbc36_190829`

**Description:** OpenRouter free-tier models produce intermittent malformed JSON that either:
1. Fails parsing (causes immediate fallback)
2. Passes parsing but contains garbage data (causes downstream crash)

**Root Cause:**
- `JSONDecodeError` treated as PERMANENT error (no retry, immediate fallback)
- If fallback also fails, application crashes
- Garbage data like `["The.", "I", "", "..."]` passes JSON validation but breaks logic

**Evidence:**
- Record 1 (`f89c6142`): Planner output contained `"2026-?..."` malformed date
- Record 8 (`e16dbc36_190829`): Router output contained `["The.", "I", "", "...", ".....", "...", "I"]`

**Impact:** Non-deterministic failures degrade user trust.

---

### Pattern 5: Response Lacks Detail
**Severity:** Medium | **Evidence:** `fec3d15f`, `8e8e6d87`, `14b9034b`, `3ec25871`

**Description:** Users consistently expect more detailed responses including:
- Reasoning (WHY this recommendation)
- Specific metrics (weights, distances, times from logs)
- Personalized analysis (not generic advice)

**User Feedback Quotes:**
- "it would be better to give why it recommended this"
- "I was expecting more of analytic response"
- "Wish it told me about how much weight I could lift"
- "response could have been a bit more detail"

**Root Cause:** Synthesizer prompt prioritizes brevity over comprehensiveness.

---

### Pattern 6: Response Language Mismatch
**Severity:** Low | **Evidence:** `8e8e6d87`

**Description:** User queries in Korean receive responses in English.

**User Feedback:** "The response language should have followed user's query language"

**Root Cause:** Synthesizer lacks language detection/matching instruction.

---

## Agent-Level Analysis

| Agent | Issues Found | Records Affected |
|-------|--------------|------------------|
| **Router** | Malformed domain selection | `e16dbc36_190829` |
| **Planner** | Wrong retrieval strategy, malformed dates, incorrect reasoning | `f89c6142`, `e16dbc36`, `e16dbc36_190829`, `db9b34b5` |
| **Retriever** | N/A (works correctly when given valid instructions) | - |
| **Analyzer** | Identifies gaps correctly but doesn't trigger Clarify | All records |
| **Synthesizer** | Insufficient detail, language mismatch | `fec3d15f`, `8e8e6d87`, `14b9034b`, `3ec25871` |
| **Evaluator** | Approved generic responses that should have been flagged | `e16dbc36`, `e16dbc36_190829` |
| **Clarifier** | Never triggered | All records |

---

## Recommendations

### Immediate (Epic 12)
1. **Fix clarification trigger logic** - Only when critical gaps AND no relevant logs
2. **Improve Planner retrieval strategy** - Always include DATE_RANGE for fitness queries
3. **Add timeout config + malformed JSON retry** - 45s timeout, 2 retries for schema errors
4. **Enhance Synthesizer prompts** - More comprehensive, cite specific metrics
5. **Add response language detection** - Match query language

### Future Considerations
- Add semantic retrieval to complement keyword matching
- Consider retrieval fallback: if topical returns 0, auto-try date_range
- Add Evaluator rule: "Flag generic responses when user logs exist"

---

## Appendix: User Feedback Verbatim

| Record | User Feedback |
|--------|---------------|
| `f89c6142` | "오늘 기록한 운동이 있는데도, 운동 데이터가 없다고 나옴. retriever range 에서 ? 글자가 있어서 제대로 retrieve 이 안된 것 같" |
| `f89c6142_183624` | "Correct response." |
| `fec3d15f` | "Not bad. It recommended based on my logs. But it would be better to give why it recommended this. And the workout plan could have been more detailed program." |
| `db9b34b5` | "I think we need give agent a tool for date awareness. 19th was monday and 20th which is today is tuesday. so it should have answered I have two records for this week." |
| `8e8e6d87` | "The response language should have followed user's query language but it responded in English which middle output would actually be better in English but at least the final response should match with the query language. The response quality is good overall. I was expecting more of analytic response but that was just my vague query." |
| `14b9034b` | "That is not bad response. I expected to suggest me what to do next but that was beyond my query scope I guess. Wish it told me about how much weight I could lift on upper body though. And it is vague that should pain is from injury or just muscle pain. But that is rather acceptible response." |
| `e16dbc36` | "although this response is generally but that is the problem. it did not refer to my logs even though there are related running logs." |
| `e16dbc36_190829` | "this could have referred to my current running training records even though the logs were not much. so this response is just general response whould could have been created without my records. this violates project rule. what could have been better was that 1) refer to my related training logs 2) based on that, estimate what my current status is and perhaps estimate my current full marathon time or even say its not possible yet based on my logs ... 3) guide detailed training program tailored by what can be estimated based in my training logs." |
| `3ec25871` | "This is good response overall. Although it would be nicer if it retrieved a bit longer period of logs so that it knows user's latest workout better. Also response could have been a bit more detail response such as why it's fine to keep current level and etc." |

---

*Analysis completed: 2026-01-24*
*Facilitator: Mary (Business Analyst)*
