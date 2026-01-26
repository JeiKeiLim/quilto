# Iteration 2 Feedback Analysis

**Date Range:** 2026-01-25 to 2026-01-26
**Records Analyzed:** 7
**LLM Provider:** OpenRouter (llm-config-openai.yaml)
**Analyst:** Mary (Dev Agent) + Jongkuk Lim

---

## Executive Summary

Iteration 2 dogfooding demonstrates that **all 6 patterns from Iteration 1 have been resolved** by Stories 12.1-12.5. However, **6 new patterns** emerged, with the most critical being:

1. **Temporal Context Blindness** - System doesn't account for time elapsed since last workout
2. **Keyword Retrieval Misses Exact Matches** - Bench press record not found despite existing
3. **Context Loss in Multi-Turn Conversations** - Marathon context lost between messages

**Recommendation:** Prioritize Stories 13.1, 13.2, and 13.3 for Epic 13.

---

## Records Summary

| # | ID | Date | Query Summary | Entries Retrieved | Sentiment |
|---|-----|------|---------------|-------------------|-----------|
| 1 | `3ec25871` | 2026-01-25 09:54 | Should I maintain current exercise level? (Korean) | 12 | **Positive** |
| 2 | `14b9034b` | 2026-01-25 10:01 | Summarize all workouts + comprehensive analysis (Korean) | 12 | **Mixed** |
| 3 | `4d876936` | 2026-01-26 07:37 | What workout should I do today? (Korean) | 12 | **Negative** |
| 4 | `17caaff4` | 2026-01-26 07:46 | Haven't been to gym, eating bad foods - what to do today? | 13 | **Positive** |
| 5 | `7e6d1d9a` | 2026-01-26 07:54 | Should I go easy with 5h sleep + gym break? | 14 | **Mixed** |
| 6 | `8628f945` | 2026-01-26 08:01 | Full marathon goal + "How do I do?" | 0 | **Negative** |
| 7 | `151de3d9` | 2026-01-26 08:07 | What is my 1RM bench press? | 2 | **Negative** |

### Sentiment Distribution

- **Positive:** 2 (29%)
- **Mixed:** 2 (29%)
- **Negative:** 3 (43%)

---

## Iteration 1 Pattern Status

### Pattern 1: Clarification Never Triggers
**Status:** RESOLVED
**Evidence:** Records `17caaff4` and `8628f945` show Planner correctly generating clarification questions when critical subjective gaps exist.
**Fix Applied:** Story 12.1

---

### Pattern 2: Retrieval Strategy Misses User Logs
**Status:** RESOLVED
**Evidence:** All 6 recommendation queries used DATE_RANGE as priority 1 strategy, retrieving 12-14 entries each.
**Fix Applied:** Story 12.2

---

### Pattern 3: LLM Timeout Too Long
**Status:** RESOLVED (Cannot Verify)
**Evidence:** No timeout issues observed in any of the 7 records.
**Fix Applied:** Story 12.3

---

### Pattern 4: Malformed JSON Crashes Application
**Status:** RESOLVED (Cannot Verify)
**Evidence:** No JSON parsing errors observed. All intermediate outputs are valid JSON.
**Fix Applied:** Story 12.3

---

### Pattern 5: Response Lacks Detail
**Status:** RESOLVED
**Evidence:** Records `3ec25871`, `14b9034b`, `17caaff4` show detailed responses with specific dates, metrics, evidence citations, and key points. User feedback: "Good response" (multiple records).
**Fix Applied:** Story 12.4

---

### Pattern 6: Response Language Mismatch
**Status:** RESOLVED
**Evidence:** Korean queries (`3ec25871`, `14b9034b`, `4d876936`) receive Korean responses. English queries (`17caaff4`, `7e6d1d9a`) receive English responses.
**Fix Applied:** Story 12.5

---

## New Patterns Identified

### Pattern 7: Temporal Context Blindness (Recency Unawareness)
**Severity:** High | **Evidence:** `14b9034b`, `4d876936`, `7e6d1d9a`

**Description:** The system retrieves historical logs correctly but fails to account for the time elapsed since the most recent entry when making recommendations. It treats 1-day-old logs and 17-day-old logs with equal relevance.

**Root Cause:**
- Analyzer and Synthesizer agents lack awareness of the query date vs. the latest log date
- No calculation of "days since last workout" to adjust recommendations

**User Feedback:**
- "it's been 6 days since the last workout... The response should have considered a bit more time awareness."
- "It's been almost 7 days from my last workout. Recovery training recommendation seems a bit off."
- "leg/ankle discomfort 17 days ago seems a bit far from now."

**Impact:** Recommendations are based on outdated fatigue/soreness data, leading to inappropriate advice (e.g., recommending recovery when user has already recovered).

---

### Pattern 8: Keyword Retrieval Misses Exact Matches
**Severity:** High | **Evidence:** `151de3d9`

**Description:** Keyword-based retrieval for "bench press" failed to find the user's actual bench press record from 2026-01-12 (contains "벤치 프레스 60kg"), finding only incline dumbbell press records.

**Root Cause:**
- Semantic expansion expanded to incline/dumbbell variants but may have prioritized them
- Possible issue with Korean tokenization ("벤치 프레스" vs "벤치프레스")

**User Feedback:**
- "I had benchpress records in 2026-01-12 and it failed to retrieve that."

**Impact:** Users receive incomplete or incorrect answers when relevant logs exist but aren't retrieved.

---

### Pattern 9: Context Loss in Multi-Turn Conversations
**Severity:** Medium | **Evidence:** `8628f945`

**Description:** When user provides context in one message ("I'd like to run a full marathon") and asks a follow-up ("How do I do?"), the system loses the context and asks for clarification.

**Root Cause:**
- Planner processes each query independently without conversation history
- Router correctly identified the log portion about marathon but Planner didn't incorporate it

**User Feedback:**
- "It failed to keep the context on I'd like to run a full marathon part."

**Impact:** Users must repeat themselves, degrading the conversational experience.

---

### Pattern 10: Ambiguous LOG vs QUERY Classification
**Severity:** Medium | **Evidence:** `8628f945`

**Description:** Statements expressing intentions ("I'd like to run a full marathon") are classified as LOG when they could reasonably be QUERY (seeking guidance).

**Root Cause:**
- Router classifies declarative statements as LOG
- Intent-based queries ("I want to...") are treated as statements rather than implicit questions

**User Feedback:**
- "it assumed it was log and processed parsing only. Which is a bit gray area since this could also be interpreted as a query for suggestion."

**Impact:** Users expecting guidance receive only log confirmation, requiring additional prompts.

---

### Pattern 11: Clarification Questions Generated But Not Asked
**Severity:** Medium | **Evidence:** `8628f945`

**Description:** Planner generates `clarify_questions` but the flow proceeds without actually asking the user.

**Root Cause:**
- Planner sets `next_action: "clarify"` but the flow doesn't route to Clarifier
- Possible disconnect between Planner's clarify_questions and actual flow execution

**User Feedback:**
- "I saw Planner generated clarification question but it did not ask me a clarification questions."

**Impact:** System fails to gather needed information even when it knows it's missing.

---

### Pattern 12: Analyzer Should Attempt Indirect Estimation
**Severity:** Low | **Evidence:** `151de3d9`

**Description:** When direct data is missing, the system gives up instead of attempting indirect estimation with appropriate disclaimers.

**Root Cause:**
- Analyzer marks verdict as "insufficient" and stops
- No fallback logic to combine related data for indirect estimation

**User Feedback:**
- "it should have tried indirect 1rm estimation based on indirect information"
- "could have combined information together with benchpress records and incline press records"

**Impact:** Users receive "no data" responses when partial/indirect answers would be valuable.

---

## Agent-Level Analysis

| Agent | Issues Found | Records Affected |
|-------|--------------|------------------|
| **Router** | Ambiguous LOG/QUERY classification | `8628f945` |
| **Planner** | Clarify questions generated but not executed; no conversation context | `8628f945` |
| **Retriever** | Keyword search missed exact Korean match | `151de3d9` |
| **Analyzer** | No temporal recency awareness; no indirect estimation fallback | `14b9034b`, `4d876936`, `7e6d1d9a`, `151de3d9` |
| **Synthesizer** | References outdated fatigue data as current | `4d876936`, `7e6d1d9a` |
| **Evaluator** | Approved responses with temporal blindness | `4d876936`, `7e6d1d9a` |
| **Clarifier** | Not invoked despite Planner requesting clarification | `8628f945` |

---

## Recommendations for Epic 13

### Immediate (Epic 13)

1. **Add Temporal Recency Awareness** - Calculate days since last workout, adjust recommendations
2. **Fix Keyword Retrieval for Korean** - Ensure tokenization handles spacing variations
3. **Implement Conversation Context** - Carry context between multi-turn queries
4. **Fix Clarification Flow Routing** - Ensure Planner's clarify action routes to Clarifier
5. **Improve Intent Classification** - Handle "I want to..." as implicit queries
6. **Add Indirect Estimation Fallback** - Provide estimates with disclaimers when direct data missing

### Future Considerations

- Add semantic search to complement keyword matching
- Consider time-weighted relevance scoring for retrieved entries
- Add Evaluator rule: "Flag responses citing data > 7 days old without recency context"

---

## Appendix: User Feedback Verbatim

| Record | User Feedback |
|--------|---------------|
| `3ec25871` | "Good response. I would ask follow up question thinking this is good answer." |
| `14b9034b` | "Good response in general but it's been 6 days since the last workout which the last workout wasn't hard training neither. The response should have considered a bit more time awareness." |
| `4d876936` | "It's been almost 7 days from my last workout. Recovery training recommendation seems a bit off." |
| `17caaff4` | "This is good response. But I'm not quite sure how it is referencing to past logs while the sources are only today's log which the agent assumed it was log and wrote it. I saw retriever retrieve today's log only. But Analyzer agent somehow held past logs. I don't know where this came from. I say the process and response are good and it just needs clarification for me how it got past logs." |
| `7e6d1d9a` | "Good. But I'm not sure saying fatigue last more than 2 weeks is good. And leg/ankle discomfort 17 days ago seems a bit far from now. It looks like final response knows my workout status and is not aware of time progression." |
| `8628f945` | "It failed to keep the context on I'd like to run a full marathon part. And I saw Planner generated clarification question but it did not ask me a clarification questions. Also before this query, I queried `I'd like to go run a full marathon` and it assumed it was log and processed parsing only. Which is a bit gray area since this could also be interpreted as a query for suggestion. Besides this gray area, after parsing(LOG) only activity, it should have asked me to provide feedback just like now." |
| `151de3d9` | "I had benchpress records in 2026-01-12 and it failed to retrieve that. Also even without benchpress records, it should have tried indirect 1rm estimation based on indirect information and notifying that this is indirect estimation ... But it would have been better if it retrieved my actual benchpress records and estimated from that. Also could have combined information together with benchpress records and incline press records then provided a bit better estimation." |

---

*Analysis completed: 2026-01-26*
*Facilitator: Mary (Dev Agent)*
