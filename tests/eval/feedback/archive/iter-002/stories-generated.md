# Epic 13 Stories Generated from Iteration 2 Analysis

**Source:** Iteration 2 Feedback Analysis (2026-01-26)
**Records Analyzed:** 7
**Patterns Identified:** 6 new patterns (all Iteration 1 patterns resolved)

> **REVISION NOTE (2026-01-26):** Story 13.2 was revised after Party Mode discussion. Original story addressed Korean keyword spacing edge cases. Revised story: "Simplify Retrieval with Storage Awareness" - adds storage summary for Planner visibility + removes keyword/topical strategies entirely. Effort bumped to Medium-Large (4-6h). See `epics.md` for current version.

---

## Recommended Stories

### Story 13.1: Add Temporal Recency Awareness to Analyzer

**Priority:** High | **Effort:** Medium (2-4h)

**As a** Quilto user,
**I want** the system to consider how long ago my workout logs were recorded,
**So that** recommendations account for recovery time and current fitness state.

**Acceptance Criteria:**

1. **Given** retrieved log entries with timestamps
   **When** Analyzer processes the data
   **Then** it calculates "days since most recent entry" and includes this in findings

2. **Given** a recommendation query with logs older than 5 days
   **When** generating recommendations
   **Then** the response acknowledges the time gap (e.g., "Your last recorded workout was 6 days ago")

3. **Given** fatigue/soreness evidence from logs older than 7 days
   **When** synthesizing response
   **Then** the system does NOT reference that soreness as "current" or "lingering"

4. **Given** a user who hasn't logged in 7+ days
   **When** asked for a workout recommendation
   **Then** the response suggests a moderate return-to-training approach rather than recovery

**Evidence:** Records `14b9034b`, `4d876936`, `7e6d1d9a` - Users received recovery recommendations despite 6-7 day workout gaps

---

### Story 13.2: Fix Keyword Retrieval for Korean Spacing Variations

**Priority:** High | **Effort:** Small (1-2h)

**As a** Quilto user logging in Korean,
**I want** keyword search to find my logs regardless of spacing variations,
**So that** queries like "bench press" find logs containing "벤치 프레스" or "벤치프레스".

**Acceptance Criteria:**

1. **Given** a search for "벤치프레스" (no space)
   **When** logs contain "벤치 프레스" (with space)
   **Then** the Retriever finds those entries

2. **Given** semantic expansion includes both "벤치프레스" and "벤치 프레스"
   **When** keyword search runs
   **Then** both variations are searched

3. **Given** a user query for bench press 1RM
   **When** logs contain "벤치 프레스 60kg" on 2026-01-12
   **Then** that entry is retrieved

**Evidence:** Record `151de3d9` - Bench press record from 2026-01-12 not found despite containing "벤치 프레스"

---

### Story 13.3: Implement Conversation Context for Multi-Turn Queries

**Priority:** Medium | **Effort:** Medium (2-4h)

**As a** Quilto user,
**I want** the system to remember context from my previous message,
**So that** I don't have to repeat information in follow-up questions.

**Acceptance Criteria:**

1. **Given** user states "I'd like to run a full marathon"
   **When** user immediately follows with "How do I do?"
   **Then** the system understands "do" refers to running a marathon

2. **Given** a LOG-type input that could be a goal statement
   **When** user's next message is a vague question
   **Then** Planner incorporates the previous message context

3. **Given** multi-turn conversation context
   **When** generating retrieval instructions
   **Then** keywords from previous turns are included

**Evidence:** Record `8628f945` - Marathon context lost between "I'd like to run a full marathon" and "How do I do?"

---

### Story 13.4: Fix Clarification Flow Routing

**Priority:** Medium | **Effort:** Small (1-2h)

**As a** Quilto user,
**I want** the system to actually ask clarification questions when needed,
**So that** I can provide missing information for better responses.

**Acceptance Criteria:**

1. **Given** Planner sets `next_action: "clarify"` with `clarify_questions` populated
   **When** the flow processes this output
   **Then** the Clarifier agent is invoked to ask the user

2. **Given** Planner generates clarification questions
   **When** the flow does not route to Clarifier
   **Then** an error is logged indicating routing failure

3. **Given** a vague query like "How do I do?"
   **When** Planner identifies critical subjective gaps
   **Then** the user receives the clarification questions before a response is generated

**Evidence:** Record `8628f945` - Planner generated clarify_questions but they were never asked to user

---

### Story 13.5: Improve Intent Classification for Goal Statements

**Priority:** Medium | **Effort:** Small (1-2h)

**As a** Quilto user,
**I want** goal statements like "I want to run a marathon" to be treated as implicit queries,
**So that** I receive guidance without needing to explicitly ask a question.

**Acceptance Criteria:**

1. **Given** input "I'd like to run a full marathon"
   **When** Router classifies input_type
   **Then** it is classified as BOTH (log of goal + implicit query for guidance)

2. **Given** input starting with "I want to..." or "I'd like to..."
   **When** no explicit question is present
   **Then** Router includes query_portion with the implied question "How should I achieve this?"

3. **Given** a goal-statement LOG without follow-up
   **When** processing completes
   **Then** the response offers guidance related to the goal

**Evidence:** Record `8628f945` - "I'd like to run a full marathon" was treated as LOG only

---

### Story 13.6: Add Indirect Estimation Fallback in Analyzer

**Priority:** Low | **Effort:** Medium (2-4h)

**As a** Quilto user,
**I want** the system to provide indirect estimates when direct data is missing,
**So that** I get useful answers with appropriate disclaimers.

**Acceptance Criteria:**

1. **Given** query for bench press 1RM with only incline press data available
   **When** Analyzer finds no direct bench press records
   **Then** it attempts indirect estimation using related exercises

2. **Given** indirect estimation is performed
   **When** Synthesizer generates response
   **Then** the response clearly states "This is an indirect estimate based on..."

3. **Given** multiple related exercises in logs
   **When** calculating indirect 1RM
   **Then** the system combines information (e.g., both incline press and bench variations)

4. **Given** insufficient data for even indirect estimation
   **When** verdict is "insufficient"
   **Then** the response explains what data would be needed

**Evidence:** Record `151de3d9` - System said "I don't have enough information" instead of attempting indirect estimation

---

## Stories Summary

| Story | Title | Priority | Effort | Pattern |
|-------|-------|----------|--------|---------|
| 13.1 | Add Temporal Recency Awareness | High | Medium | Pattern 7 |
| 13.2 | ~~Fix Keyword Retrieval for Korean~~ → **Simplify Retrieval with Storage Awareness** | High | Medium-Large | Pattern 8 |
| 13.3 | Implement Conversation Context | Medium | Medium | Pattern 9 |
| 13.4 | Fix Clarification Flow Routing | Medium | Small | Pattern 11 |
| 13.5 | Improve Intent Classification | Medium | Small | Pattern 10 |
| 13.6 | Add Indirect Estimation Fallback | Low | Medium | Pattern 12 |

---

## Scope Recommendation for Epic 13

**Minimum Viable Scope (3 stories):**
- Story 13.1: Temporal Recency Awareness (High impact, addresses most frequent complaint)
- Story 13.2: ~~Korean Keyword Retrieval~~ → **Simplify Retrieval with Storage Awareness** (High impact, architectural simplification)
- Story 13.4: Clarification Flow Routing (Medium impact, quick fix)

**Full Scope (6 stories):**
- All stories above address distinct user-reported issues
- Stories 13.3, 13.5, 13.6 provide enhanced conversational experience

**Estimated Total Effort:** 13-23 hours (2 Small + 3 Medium + 1 Medium-Large) - revised after Story 13.2 scope expansion

---

*Generated: 2026-01-26*
*Facilitator: Mary (Dev Agent)*
