# Stories Generated from Iteration 3 Analysis

**Generated:** 2026-01-26
**Source:** iter-003/analysis.md
**Target Epic:** Epic 14

---

## Summary

Based on 16 feedback records analyzed in Iteration 3, the following stories are generated to address newly identified patterns.

| Story | Pattern | Priority | Effort |
|-------|---------|----------|--------|
| 14.1 | Goal Context Loss (#16) | High | Small |
| 14.2 | Response Language Mismatch (#13) | Medium | Small |
| 14.3 | Evaluator False Negative (#14) | Low | Small |

---

## Story 14.1: Pass Goal Context to Synthesizer

### Problem
When Router classifies an input as BOTH and extracts a goal statement in `log_portion`, this goal context is not passed through to the Synthesizer. As a result, the final response may give generic advice that ignores the user's explicitly stated goal.

### Evidence
**Record `ff8c098d`:**
- Router correctly identified: `log_portion: "I want to lose 5kg by summer"`
- Synthesizer response: Generic "balanced approach—strength training, cardio, flexibility" advice
- User feedback: "The response gives generic balanced fitness advice instead of weight-loss focused guidance, despite the user explicitly stating a weight-loss goal."

### Acceptance Criteria
- [ ] When Router identifies a goal in `log_portion`, include it in Synthesizer's input context
- [ ] Synthesizer prompt should instruct it to incorporate stated goals into recommendations
- [ ] Test case: "I want to lose 5kg by summer, what should I focus on?" → Response should mention calorie deficit, weight loss strategies
- [ ] All existing tests pass

### Technical Notes
- Modify agent orchestration to pass `log_portion` when input_type is BOTH
- Update Synthesizer prompt to be goal-aware
- Consider adding a `user_goal` field to the context passed between agents

---

## Story 14.2: Match Response Language to Query Language

### Problem
When the query is in a different language than the workout logs, the Synthesizer sometimes responds in the log language instead of the query language.

### Evidence
**Record `39b8e450`:**
- Query: "I think I might be overtraining my shoulders, can you check my workout frequency for that muscle group?" (English)
- Logs: Mostly in Korean
- Response: In Korean
- User feedback: "One minor issue: query was in English but response was in Korean"

### Acceptance Criteria
- [ ] Detect the language of the query (not the logs)
- [ ] Respond in the query language
- [ ] Test case: English query with Korean logs → English response
- [ ] Test case: Korean query with English logs → Korean response
- [ ] All existing tests pass

### Technical Notes
- Could use simple language detection (presence of Korean characters, etc.)
- Alternative: Explicitly instruct Synthesizer to match query language
- Consider storing detected query language in Router output

---

## Story 14.3: Fix Evaluator Completeness Check

### Problem
The Evaluator incorrectly flags responses as "incomplete" for time periods where no workout entries exist in storage.

### Evidence
**Record `47d6c735`:**
- Query: "show me everything from january"
- Response: Listed all 21 entries from January
- Evaluator complaint: "missing entries for 14, 16, 17, 18, 21"
- User feedback: "Those dates have no logged workouts. The response is actually comprehensive and accurate given the retrieved data."

### Acceptance Criteria
- [ ] Evaluator completeness check should consider only what data exists in storage
- [ ] Empty dates should not trigger "incomplete" verdicts
- [ ] Test case: Request all entries for a period → Response includes all stored entries → Evaluator marks complete
- [ ] All existing tests pass

### Technical Notes
- Pass the actual date coverage from Retriever to Evaluator
- Evaluator should validate completeness against what was retrieved, not hypothetical entries
- May need to adjust the completeness heuristic

---

## Optional: Story 14.4: Clarify Ambiguous Fitness Terms

### Problem (Low Priority)
Some fitness terms like "leg day" are semantically ambiguous. The user may mean dedicated leg strength training (squats, leg press) while the system interprets any leg-involving activity (stair climbing, running).

### Evidence
**Record `9edecb7c`:**
- Query: "what was my last leg day like"
- Response: Described stair climbing session
- User feedback: "stair climbing is cardio with leg involvement, not a dedicated leg strength training day"

### Acceptance Criteria
- [ ] Identify potentially ambiguous fitness terms ("leg day", "arm day", "cardio", etc.)
- [ ] Consider asking clarifying question when interpretation is uncertain
- [ ] Alternative: Include both interpretations in response

### Technical Notes
- This is lower priority as the response was technically correct
- May add complexity without significant user benefit
- Consider deferring to Epic 15 or later

---

## Not Addressing

### Pattern 11 (Clarification Questions)
Status: **PARTIALLY RESOLVED** - Questions are now generated but the system doesn't block response generation while waiting for answers. This is acceptable behavior for async/non-interactive mode and may not need further changes.

---

## Next Steps

1. Add these stories to `_bmad-output/planning-artifacts/epics.md` under Epic 14
2. Prioritize 14.1 (goal context) as highest impact
3. Stories 14.2 and 14.3 can be parallelized
4. Story 14.4 is optional for this sprint
