# Epic 12: Dogfooding Iteration 2 - Improvement Stories

**Generated From:** Iteration 1 Feedback Analysis
**Date:** 2026-01-24
**Total Stories:** 5
**Estimated Effort:** 8-14 hours

---

## Story 12.1: Fix Clarification Trigger Logic

**Priority:** High | **Effort:** Medium (2-4 hours)

### Story

**As a** Quilto user,
**I want** the system to ask clarification questions only when truly necessary,
**So that** I'm not over-prompted but critical gaps are addressed.

### Background

The Clarifier agent was over-corrected from "too many questions" to "never asking". The flow needs to trigger clarification when:
- Analyzer identifies SUBJECTIVE/CLARIFICATION gaps with severity=critical
- AND Retriever found 0 relevant entries for the query

### Acceptance Criteria

1. **Given** Analyzer identifies SUBJECTIVE/CLARIFICATION gaps with severity=critical
   **When** Retriever found 0 relevant entries for the query
   **Then** flow transitions to CLARIFY state

2. **Given** Analyzer identifies critical gaps
   **When** Retriever found relevant entries (count > 0)
   **Then** flow skips CLARIFY and proceeds to Synthesize with available data

3. **Given** no critical non-retrievable gaps
   **When** processing completes
   **Then** no clarification questions are asked

4. **Given** the clarification flow
   **When** a clarification question is generated
   **Then** it addresses the specific gap identified by Analyzer

### Dev Notes

- Check the gate logic between ANALYZE → CLARIFY transition in LangGraph flow
- The condition should be: `has_critical_subjective_gaps AND retrieved_entries_count == 0`
- Review Story 5.1 and 5.2 for original Clarifier implementation
- Review Epic 5 retrospective for context on the over-correction

### Evidence

- All 9 iteration 1 records had no clarification questions
- Records `e16dbc36` (marathon query): Analyzer found critical SUBJECTIVE gaps but flow went to Synthesize

---

## Story 12.2: Improve Planner Retrieval Strategy Selection

**Priority:** High | **Effort:** Medium (2-4 hours)

### Story

**As a** Quilto user,
**I want** queries about my fitness to always check my logs first,
**So that** responses are personalized rather than generic.

### Background

The Planner chose `topical` strategy with "marathon" keyword for a marathon training query, which didn't match the user's running logs. The user had relevant running data (5km, 10km runs) but received a generic response because 0 entries were retrieved.

### Acceptance Criteria

1. **Given** a recommendation or insight query (e.g., marathon training, workout advice)
   **When** Planner creates retrieval strategy
   **Then** DATE_RANGE is always included as priority 1 strategy

2. **Given** Planner choosing `topical` or `keyword` only
   **When** user has relevant logs in storage
   **Then** those logs are retrieved (not skipped)

3. **Given** query about user's fitness capabilities
   **When** Planner determines retrieval strategy
   **Then** reasoning must NOT say "no historical data required"

4. **Given** topical/keyword strategy returns 0 entries
   **When** DATE_RANGE fallback is available
   **Then** automatically try DATE_RANGE before concluding "no data"

### Dev Notes

- Update Planner prompt with rule: "For fitness queries, ALWAYS include DATE_RANGE as priority 1"
- Add retrieval fallback logic: if topical returns 0, auto-fallback to date_range
- Evidence: Records `e16dbc36` retrieved 0 entries despite running logs existing
- User feedback: "it did not refer to my logs even though there are related running logs"

### Evidence

- Records `e16dbc36`, `e16dbc36_190829`: Marathon query retrieved 0 entries
- Planner reasoning: "No personal historical data is required" - INCORRECT

---

## Story 12.3: Add LLM Timeout and Retry Configuration

**Priority:** Medium | **Effort:** Small (1-2 hours)

### Story

**As a** Quilto developer,
**I want** configurable LLM timeout with smart retry behavior,
**So that** the system doesn't hang and handles intermittent failures gracefully.

### Background

- litellm's default timeout is 600 seconds (too long)
- Malformed JSON is treated as PERMANENT error (no retry)
- OpenRouter free-tier is non-deterministic - same input might work on retry

### Acceptance Criteria

1. **Given** `LLMConfig`
   **When** timeout is not specified
   **Then** default is 45 seconds (not litellm's 600s default)

2. **Given** LLM request exceeds timeout
   **When** retry count < max_retries
   **Then** retry with exponential backoff (existing behavior, now with shorter timeout)

3. **Given** LLM returns malformed JSON (JSONDecodeError, ValidationError)
   **When** schema_retry_count < max_schema_retries (default: 2)
   **Then** retry same provider (treat as TRANSIENT, not PERMANENT)

4. **Given** malformed JSON after max_schema_retries exhausted
   **When** fallback provider is configured
   **Then** try fallback provider before degradation

5. **Given** all providers fail with malformed JSON
   **When** graceful degradation is enabled
   **Then** return PartialResult (not crash)

### Dev Notes

Add to `LLMConfig`:
```python
timeout: int = 45  # seconds
max_schema_retries: int = 2  # retries for JSON/validation errors
```

Implementation:
- Pass timeout to litellm: `completion_kwargs["timeout"] = self.config.timeout`
- Modify `classify_error()` or `_retry_structured_with_backoff()` to track schema retry count
- Schema errors: TRANSIENT for first N retries, then PERMANENT

### Evidence

- Record `f89c6142`: Planner output contained `"2026-?..."` malformed date
- Record `e16dbc36_190829`: Router output contained garbage array

---

## Story 12.4: Enhance Synthesizer for Detailed Responses

**Priority:** Medium | **Effort:** Small (1-2 hours)

### Story

**As a** Quilto user,
**I want** responses to include reasoning, specific metrics, and log references,
**So that** I understand why recommendations are made based on my data.

### Background

Users consistently requested more detailed responses. Current Synthesizer prioritizes brevity over comprehensiveness.

### Acceptance Criteria

1. **Given** a recommendation response
   **When** Synthesizer generates output
   **Then** response includes WHY (reasoning based on log patterns)

2. **Given** logs with numeric data (weights, distances, times, heart rates)
   **When** Synthesizer generates output
   **Then** specific metrics are cited (e.g., "Your bench press increased from 50kg to 60kg")

3. **Given** retrieved log entries
   **When** Synthesizer generates output
   **Then** relevant entries are explicitly cited with dates

4. **Given** a query asking for advice
   **When** Synthesizer generates output
   **Then** response explains the reasoning behind the advice

### Dev Notes

Update Synthesizer prompt with:
- "Always explain WHY you're making this recommendation"
- "Cite specific numbers from user's logs (weights, distances, heart rates, times)"
- "Reference log dates as evidence for your claims"
- "If recommending something, explain what pattern in the user's data led to this recommendation"

### Evidence

- `fec3d15f`: "it would be better to give why it recommended this"
- `8e8e6d87`: "I was expecting more of analytic response"
- `14b9034b`: "Wish it told me about how much weight I could lift on upper body"
- `3ec25871`: "response could have been a bit more detail"

---

## Story 12.5: Add Response Language Detection

**Priority:** Low | **Effort:** Small (1-2 hours)

### Story

**As a** Quilto user querying in Korean,
**I want** the final response in Korean,
**So that** the experience feels natural.

### Background

User queried in Korean but received response in English. Intermediate outputs can remain in English for debugging, but final response should match query language.

### Acceptance Criteria

1. **Given** user query in Korean
   **When** Synthesizer generates response
   **Then** response is in Korean

2. **Given** user query in English
   **When** Synthesizer generates response
   **Then** response is in English

3. **Given** mixed language query
   **When** Synthesizer generates response
   **Then** response uses the dominant language of the query

### Dev Notes

Two implementation options:
- **Option A:** Add language detection in Router, pass to Synthesizer
- **Option B:** Add instruction to Synthesizer: "Match response language to query language"

Recommendation: Option B is simpler and likely sufficient.

Add to Synthesizer prompt:
- "IMPORTANT: Your response MUST be in the same language as the user's query"
- "If query is in Korean, respond in Korean. If query is in English, respond in English."

### Evidence

- Record `8e8e6d87`: Korean query got English response
- User feedback: "The response language should have followed user's query language"

---

---

## Story 12.6: Analyze Feedback Dataset (Iteration 2)

**Priority:** Medium | **Effort:** Medium (2-4 hours)

### Story

**As a** Quilto developer,
**I want** to analyze feedback collected during Epic 12 implementation,
**So that** patterns are identified and improvement stories are generated for Epic 13.

### Background

This is the **continuation of the dogfooding loop**. After implementing Stories 12.1-12.5, collect new feedback and analyze whether the fixes resolved the identified issues.

### Acceptance Criteria

1. **Given** feedback records in `tests/eval/feedback/active/`
   **When** analysis is completed
   **Then** all records are reviewed with sentiment categorization

2. **Given** analyzed feedback records
   **When** patterns are identified
   **Then** analysis documents which issues persist vs resolved from Iteration 1

3. **Given** identified patterns
   **When** improvement stories are generated
   **Then** each story has user story format, acceptance criteria, effort, and priority

4. **Given** iteration complete
   **When** archiving
   **Then** records move to `archive/iter-002/` with analysis.md and stories-generated.md

5. **Given** generated stories
   **When** Epic 13 is scoped
   **Then** priority stories are added to epics.md and sprint-status.yaml

### Dev Notes

- Follow same methodology as Story 11.4
- Compare against Iteration 1 findings to measure improvement
- Key questions to answer:
  - Did Story 12.1 fix clarification trigger issues?
  - Did Story 12.2 fix retrieval strategy issues?
  - Did Story 12.3 reduce timeout/crash issues?
  - Did Story 12.4 improve response detail?
  - Did Story 12.5 fix language mismatch?
- Archive to `tests/eval/feedback/archive/iter-002/`

---

## Summary

| Story | Title | Priority | Effort | Key Change |
|-------|-------|----------|--------|------------|
| 12.1 | Fix Clarification Trigger Logic | High | Medium | Gate: critical gaps + 0 entries → CLARIFY |
| 12.2 | Improve Planner Retrieval Strategy | High | Medium | Always include DATE_RANGE for fitness queries |
| 12.3 | Add LLM Timeout and Retry Config | Medium | Small | 45s timeout, retry malformed JSON |
| 12.4 | Enhance Synthesizer Detail | Medium | Small | Add reasoning, metrics, citations |
| 12.5 | Add Response Language Detection | Low | Small | Match response language to query |
| 12.6 | Analyze Feedback Dataset (Iter 2) | Medium | Medium | Analyze, archive, generate Epic 13 |

**Total Estimated Effort:** 10-18 hours

---

*Generated: 2026-01-24*
*Source: Iteration 1 Feedback Analysis*
