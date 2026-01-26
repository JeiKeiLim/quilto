# Human Review of Iteration 3 Feedback Records

**Reviewer:** Jongkuk Lim
**Date:** 2026-01-26
**Purpose:** Review auto-generated feedback from Claude Code dogfooding session
**Status:** REVIEW COMPLETE - Ready to discuss Epic 14

---

## How to Resume: Epic 14 Discussion

To discuss Epic 14 implications from fresh context:
```
Read these files in order:
1. tests/eval/feedback/archive/iter-003/analysis.md - Auto-generated analysis (patterns 13-16)
2. tests/eval/feedback/archive/iter-003/stories-generated.md - Auto-generated Epic 14 stories
3. tests/eval/feedback/active/human-review-iter-003.md - Human review results (this file)

Key discrepancies between auto-analysis and human review:
- Auto-analysis: 81% positive, 19% mixed, 0% negative
- Human review: 50% correct, 25% partial, 25% WRONG (false positives)
- NEW Pattern 17 (CRITICAL) discovered: Planner skips retrieval entirely (Records 13, 16)
- Pattern 16 confirmed but auto-analysis underestimated severity
- Records 2, 3, 13, 16 were marked positive by auto but are actually negative/mixed

Task: Reconcile auto-generated Epic 14 stories with human review findings:
- Add new story for Pattern 17 (Planner retrieval bypass) - CRITICAL priority
- Adjust priority of existing stories based on human findings
- Consider if any auto-generated stories should be deprioritized
```

---

## Previous: Record Review Resumption (COMPLETED)

~~To continue record review from fresh context~~ (DONE - all 16 records reviewed)

**Record Order (16 total):**
1. 08595fc6 - Skipped
2. 09c6ee60 - NEGATIVE (retriever missed pull-up data)
3. 39b8e450 - MIXED (temporal blindness persists)
4. 473182db - Skipped
5. 47d6c735 - Skipped
6. 67f387e4 - POSITIVE with suggestion
7. 719d91a8 - Skipped
8. 81ed9bd3 - Skipped
9. 939f011c - POSITIVE with suggestion
10. 9ea6d8dc - POSITIVE with note (temporal issue but good fallback)
11. 9ec3f2c3 - POSITIVE with suggestion (clarification question could help)
12. 9edecb7c - Skipped (auto-feedback already Mixed)
13. bca56fc1 - NEGATIVE (Planner skipped retrieval, gave generic response)
14. d417d4d4 - Skipped
15. f07a55ff - POSITIVE with note (clarification question opportunity missed)
16. ff8c098d - NEGATIVE (Planner skipped retrieval + goal context ignored)

---

## Record 1: `2026-01-26_08595fc6`
**Query:** "벤치프레스 1RM 추정해줘"
**Auto Sentiment:** Positive
**Human Review:** Skipped

---

## Record 2: `2026-01-26_09c6ee60`
**Query:** "어제 기록 확인해줘"
**Auto Sentiment:** Positive
**Human Review:** **NEGATIVE**

**Issues Identified:**
1. **Log storage issue**: Entry "Yesterday I did 3 sets of pull-ups, 어제 기록 확인해줘" stored on 2026-01-25 with relative time reference "Yesterday" - becomes misleading when queried later
2. **Retriever partial failure**: Actual pull-up data existed on 2026-01-12: "풀업 10개, 7개, 7개 진행" (10, 7, 7 reps with superset) - NOT retrieved
3. **Auto-feedback flaw**: Claude Code marked "positive" without verifying against real logs - feedback process needs access to ground truth

**Action Items:**
- Parser should convert relative time references to absolute dates when storing
- Retriever should search for related exercise history
- Auto-feedback system needs ground truth validation

---

## Record 3: `2026-01-26_39b8e450`
**Query:** "I think I might be overtraining my shoulders, can you check my workout frequency for that muscle group?"
**Auto Sentiment:** Positive (with language mismatch noted)
**Human Review:** **MIXED/NEGATIVE**

**Issues Identified:**
1. **Temporal context blindness PERSISTS**: Last shoulder workout was 2026-01-15, query on 2026-01-26 = 11 days gap. Response should have said "you haven't worked shoulders in 11 days, overtraining is unlikely right now" but instead focused only on historical frequency without current context
2. **Pattern 7 (Iteration 2) not fully resolved**: Story 13.1 was supposed to fix temporal recency awareness but this case shows it still misses the "time since last workout" context
3. **Language mismatch**: English query got Korean response
4. **Auto-feedback failure**: Claude Code didn't catch the temporal blindness issue - same pattern from Iteration 2

**Action Items:**
- Analyzer needs to always calculate and report "days since last [activity]" for frequency questions
- Synthesizer should lead with recency context before historical patterns

---

## Record 4: `2026-01-26_473182db`
**Query:** "최근에 등운동 했었나? 얼마나 됐지"
**Auto Sentiment:** Positive
**Human Review:** Skipped (note: relies on problematic "Yesterday I did 3 sets of pull-ups" entry)

---

## Record 5: `2026-01-26_47d6c735`
**Query:** "show me everything from january"
**Auto Sentiment:** Positive
**Human Review:** Skipped

---

## Record 6: `2026-01-26_67f387e4`
**Query:** "현재 러닝 실력으로 가능할까?"
**Auto Sentiment:** Positive
**Human Review:** **POSITIVE with suggestion**

**Issues Identified:**
1. **Query field inconsistency**: Full input was "마라톤 준비하고 싶은데 현재 러닝 실력으로 가능할까?" but query field only shows partial. Unclear if this is conversation context (Story 13.3) or recording bug.

**Positive Aspects:**
- Response correctly assesses marathon feasibility based on running data
- Cites specific evidence (7km @ 6:10, 5km with HR 172)
- Notes injury concerns appropriately
- Language matches query (Korean)

**Suggestion for Improvement:**
- Response mentions "12-20주 프로그램이 필요합니다" but doesn't provide actual guidance on what that program looks like. Would be better to include brief outline (e.g., weekly long run progression, recovery days, etc.)

---

## Record 7: `2026-01-26_719d91a8`
**Query:** "How long has it been since my last upper body workout?"
**Auto Sentiment:** Positive
**Human Review:** Skipped

---

## Record 8: `2026-01-26_81ed9bd3`
**Query:** "지난주에 운동 얼마나 했어?"
**Auto Sentiment:** Positive
**Human Review:** Skipped

---

## Record 9: `2026-01-26_939f011c`
**Query:** "지난 달 대비 이번 달 운동 빈도가 어떻게 변했어?"
**Auto Sentiment:** Positive
**Human Review:** **POSITIVE with suggestion**

**Positive Aspects:**
- Correctly created two sub-queries for Dec and Jan comparison
- Accurate count (1 Dec, 11 Jan)
- Properly disclosed uncertainty about missing Dec logs
- Language matched (Korean)

**Suggestion for Improvement:**
- Would be nice to show which workout TYPE frequency changed (strength vs cardio vs flexibility), but this cannot be measured since December only has a single record. Consider noting this limitation explicitly.

---

## Record 10: `2026-01-26_9ea6d8dc`
**Query:** "오늘 하체 운동 추천해줘, 저번에 스쿼트 했으니까"
**Auto Sentiment:** Positive
**Human Review:** **POSITIVE with note**

**Observations:**
1. **Same temporal issue**: User said "저번에 스쿼트 했으니까" (since I did squats last time) but no squat records found in logs
2. **Good fallback handling**: System correctly noted this as "nice-to-have gap" and provided useful recommendation anyway
3. **Response quality**: Despite missing squat data, the recommendation was evidence-based using available cardio fatigue patterns

---

## Record 11: `2026-01-26_9ec3f2c3`
**Query:** "Show me my squat progress compared to deadlift over the past month"
**Auto Sentiment:** Positive
**Human Review:** **POSITIVE with suggestion**

**Observations:**
1. **Response was reasonable**: Correctly identified no squat/deadlift data and explained the gap
2. **Clarification question opportunity missed**: Could have asked "Did you log these under different names?" or "Would you like to see other strength progress instead?"
3. **Pattern 11 still relevant**: Clarification questions could improve UX in data-gap scenarios

---

## Record 12: `2026-01-26_9edecb7c`
**Query:** "what was my last leg day like"
**Auto Sentiment:** Mixed
**Human Review:** Skipped (auto-feedback already caught the semantic ambiguity issue)

---

## Record 13: `2026-01-26_bca56fc1`
**Query:** "요즘 운동 좀 쉬었는데 다시 시작하려면 어떤 강도로 해야할까"
**Auto Sentiment:** Positive
**Human Review:** **NEGATIVE** - Auto-feedback was WRONG

**Issues Identified:**
1. **Planner skipped retrieval**: Decided to synthesize directly without checking storage, despite workout logs being available
2. **Generic response instead of personalized**: Should have said "Your last workout was on 01-20 (6 days ago), your recent trend was mostly cardio, so here's my suggestion..."
3. **storage_path null issue**: The test may have been run without storage connection, but this is a configuration issue, not a valid excuse for generic response
4. **Auto-feedback false positive**: Claude Code marked this as "positive" when it should have been negative - system failed to use available data

**Action Items:**
- Planner should always attempt retrieval for personalization questions
- Response should include "days since last workout" and "recent training trend" context
- Auto-feedback needs better validation against what data COULD have been retrieved

---

## Record 14: `2026-01-26_d417d4d4`
**Query:** "What's my estimated 1RM for bench press based on recent workouts?"
**Auto Sentiment:** Positive
**Human Review:** Skipped

---

## Record 15: `2026-01-26_f07a55ff`
**Query:** "How can I achieve a 200kg deadlift by summer?"
**Auto Sentiment:** Positive
**Human Review:** **POSITIVE with note**

**Observations:**
1. **Clarification question opportunity missed**: System identified needing more info (current 1RM, injuries, weekly availability) but didn't ask interactively - Pattern 11 still relevant
2. **Indirect estimation not possible**: Checked logs - no leg strength data (squats, leg press, etc.) exists, only cardio - so indirect estimation wasn't feasible here
3. **Good fallback handling**: Response appropriately disclosed limitations and listed what info is needed

---

## Record 16: `2026-01-26_ff8c098d`
**Query:** "What should I focus on?" (with context: "I want to lose 5kg by summer")
**Auto Sentiment:** Mixed
**Human Review:** **NEGATIVE** - Auto-feedback was incomplete

**Issues Identified:**
1. **Planner skipped retrieval entirely**: Set `next_action: clarify` without attempting to retrieve workout logs. Same critical issue as Record 13.
2. **Training logs exist but weren't accessed**: System has 19-22 entries (seen in other records) but Retriever shows 0 entries, 0 strategies used
3. **No date range expansion**: Should have tried retrieval first, then expanded if insufficient
4. **Goal context ignored (Pattern 16)**: Router correctly extracted "lose 5kg by summer" but Synthesizer gave generic "balanced fitness" advice instead of weight-loss focused guidance
5. **Auto-feedback incomplete**: Only caught goal context loss, missed the retrieval bypass issue

**What response SHOULD have been:**
> "Based on your recent training (mostly upper body and cardio over the past month), here's what you should focus on for your goal of losing 5kg by summer:
> 1. Calorie deficit is primary for weight loss
> 2. Maintain current cardio frequency
> 3. Continue strength training to preserve muscle mass
> 4. Your last workout was X days ago..."

**Action Items:**
- Planner should ALWAYS attempt retrieval for personalization questions before falling back to clarify
- Goal context from Router.log_portion must be passed to Synthesizer
- This is a CRITICAL bug affecting multiple queries (Records 13, 16)
- Record 11: `2026-01-26_9ec3f2c3`
- Record 12: `2026-01-26_9edecb7c`
- Record 13: `2026-01-26_bca56fc1`
- Record 14: `2026-01-26_d417d4d4`
- Record 15: `2026-01-26_f07a55ff`
- Record 16: `2026-01-26_ff8c098d`

---

## Summary Statistics (COMPLETE)

| Metric | Count |
|--------|-------|
| Total Records | 16 |
| **Confirmed OK (Skipped = auto-feedback correct)** | 6 |
| **Positive with suggestions/notes** | 4 |
| **Revised to NEGATIVE** | 3 |
| **Revised to MIXED** | 1 |
| Auto-feedback already Mixed (confirmed) | 2 |

### Accuracy of Auto-Feedback
- **Correct:** 8/16 (50%) - 6 skipped + 2 already mixed
- **Partially correct (missed details):** 4/16 (25%) - positive with notes
- **Wrong (false positives):** 4/16 (25%) - Records 2, 3, 13, 16

### Breakdown by Human Review
| # | Record | Auto Sentiment | Human Review |
|---|--------|----------------|--------------|
| 1 | 08595fc6 | Positive | Skipped |
| 2 | 09c6ee60 | Positive | **NEGATIVE** - retriever missed pull-up data |
| 3 | 39b8e450 | Positive | **MIXED** - temporal blindness persists |
| 4 | 473182db | Positive | Skipped |
| 5 | 47d6c735 | Positive | Skipped |
| 6 | 67f387e4 | Positive | POSITIVE with suggestion |
| 7 | 719d91a8 | Positive | Skipped |
| 8 | 81ed9bd3 | Positive | Skipped |
| 9 | 939f011c | Positive | POSITIVE with suggestion |
| 10 | 9ea6d8dc | Positive | POSITIVE with note |
| 11 | 9ec3f2c3 | Positive | POSITIVE with suggestion |
| 12 | 9edecb7c | Mixed | Skipped (auto already Mixed) |
| 13 | bca56fc1 | Positive | **NEGATIVE** - Planner skipped retrieval |
| 14 | d417d4d4 | Positive | Skipped |
| 15 | f07a55ff | Positive | POSITIVE with note |
| 16 | ff8c098d | Mixed | **NEGATIVE** - Planner skipped retrieval + goal ignored |

---

## Critical Patterns Identified (Human Review)

### NEW: Pattern 17 - Planner Skips Retrieval for Personalization Queries
**Severity:** CRITICAL | **Records:** 13, 16
**Description:** Planner sets `next_action: clarify` or `synthesize` without attempting retrieval, even when workout logs exist. Results in generic responses instead of personalized advice.
**Root Cause:** Planner logic doesn't enforce "always try retrieval first" for recommendation/personalization queries.
**Impact:** User gets generic advice when the system HAS their data.

### Pattern 16 - Goal Context Loss (Confirmed)
**Severity:** HIGH | **Records:** 16
**Description:** Router correctly extracts goal from log_portion (e.g., "lose 5kg by summer") but Synthesizer ignores it, giving generic advice.
**Root Cause:** Goal context not passed through agent pipeline.

### Pattern 11 - Clarification Questions Not Blocking (Still Relevant)
**Severity:** MEDIUM | **Records:** 11, 15, 16
**Description:** Clarification questions are generated but system doesn't wait for answers before providing response.

### Existing Patterns (Minor)
1. **Pattern 7 (Temporal Context Blindness)** - Partially persists (Record 3)
2. **Auto-feedback false positives** - Doesn't validate against real logs (Records 2, 13, 16)
3. **Relative time references in logs cause confusion** (Record 2)
