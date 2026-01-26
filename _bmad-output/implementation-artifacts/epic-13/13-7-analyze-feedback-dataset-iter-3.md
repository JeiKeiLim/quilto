# Story 13.7: Analyze Feedback Dataset (Iteration 3)

Status: ready-for-dev

## Story

As a **Quilto developer**,
I want **to analyze feedback collected during Epic 13 implementation**,
So that **patterns are identified and improvement stories are generated for Epic 14**.

## Background

**Origin:** Dogfooding Iteration Cycle (Epic 11-12-13)
**Source:** Story 12.6 established the iteration pattern; this story continues the cycle
**Priority:** Medium | **Effort:** Medium (2-4 hours)
**Type:** Analysis task (not code implementation)

This is the final story of Epic 13, which closes the Dogfooding Iteration 3 cycle. Stories 13.1-13.6 implemented fixes for the 6 patterns identified in Iteration 2 analysis. This story:

1. Analyzes new feedback collected after those fixes
2. Determines if the fixes resolved the identified issues
3. Generates improvement stories for Epic 14 (Dogfooding Iteration 4)
4. Archives Iteration 3 data for future reference

**Iteration Pattern Reference:**
```
1. User runs: swealog auto "..."
2. Quilto generates response
3. User provides natural language feedback
4. System records to tests/eval/feedback/active/
5. [Stories 13.1-13.6 DONE] Implement fixes
6. [THIS STORY] Analyze dataset, generate Epic 14 stories
7. Archive iteration, start next cycle
```

## Acceptance Criteria

1. **Given** feedback records in `tests/eval/feedback/active/`
   **When** analysis is completed
   **Then** all records are reviewed with sentiment categorization (positive/mixed/negative)

2. **Given** analyzed feedback records
   **When** patterns are identified
   **Then** analysis documents which issues persist vs resolved (comparing to Iteration 2 patterns)

3. **Given** identified patterns
   **When** improvement stories are generated
   **Then** each story has: user story format, acceptance criteria, effort estimate, and priority

4. **Given** iteration complete
   **When** archiving
   **Then** records move to `archive/iter-003/` with `analysis.md` and `stories-generated.md`

5. **Given** generated stories
   **When** Epic 14 is scoped
   **Then** priority stories are added to `epics.md` and `sprint-status.yaml`

## Tasks / Subtasks

- [ ] Task 1: Load and catalog all feedback records (AC: #1)
  - [ ] 1.1: Read all JSON files from `tests/eval/feedback/active/`
  - [ ] 1.2: Parse each record extracting: query, intermediate outputs, final response, user feedback
  - [ ] 1.3: Categorize sentiment for each record (positive/mixed/negative)
  - [ ] 1.4: Create summary table like Iteration 1/2 format

- [ ] Task 2: Compare against Iteration 2 patterns (AC: #2)
  - [ ] 2.1: Load `tests/eval/feedback/archive/iter-002/analysis.md` for reference
  - [ ] 2.2: For each of the 6 Iteration 2 patterns, determine if resolved:
    - Pattern 7: Temporal Context Blindness -> Fixed by Story 13.1?
    - Pattern 8: Keyword Retrieval Misses Exact Matches -> Fixed by Story 13.2?
    - Pattern 9: Context Loss in Multi-Turn Conversations -> Fixed by Story 13.3?
    - Pattern 10: Ambiguous LOG vs QUERY Classification -> Fixed by Story 13.5?
    - Pattern 11: Clarification Questions Generated But Not Asked -> Fixed by Story 13.4?
    - Pattern 12: Analyzer Should Attempt Indirect Estimation -> Fixed by Story 13.6?
  - [ ] 2.3: Document evidence for each pattern status (RESOLVED/PERSISTS/NEW)

- [ ] Task 3: Identify new patterns (AC: #2)
  - [ ] 3.1: Analyze intermediate outputs for systematic issues not in Iteration 2
  - [ ] 3.2: Group negative/mixed feedback by root cause
  - [ ] 3.3: Assign severity (High/Medium/Low) based on frequency and impact
  - [ ] 3.4: Document each new pattern with evidence and root cause

- [ ] Task 4: Generate improvement stories for Epic 14 (AC: #3)
  - [ ] 4.1: For each NEW pattern or PERSISTING pattern, draft a story:
    - User story format (As a, I want, So that)
    - Acceptance criteria (Given/When/Then format)
    - Priority (High/Medium/Low)
    - Effort estimate (Small 1-2h / Medium 2-4h / Large 4-8h)
  - [ ] 4.2: Prioritize stories by severity and effort ratio
  - [ ] 4.3: Write `stories-generated.md` in archive

- [ ] Task 5: Archive Iteration 3 (AC: #4)
  - [ ] 5.1: Create directory `tests/eval/feedback/archive/iter-003/`
  - [ ] 5.2: Move all files from `active/` to `archive/iter-003/records/`
  - [ ] 5.3: Write `analysis.md` following Iteration 1/2 format
  - [ ] 5.4: Write `stories-generated.md` with Epic 14 scope

- [ ] Task 6: Update planning artifacts (AC: #5)
  - [ ] 6.1: Add Epic 14 section to `_bmad-output/planning-artifacts/epics.md`
  - [ ] 6.2: Add Epic 14 stories to `_bmad-output/implementation-artifacts/sprint-status.yaml`
  - [ ] 6.3: Update epic-13 status to "done" in sprint-status.yaml

## Dev Notes

### This is an ANALYSIS Story, Not a Code Implementation Story

Unlike Stories 13.1-13.6 which modified code, this story is purely analytical:
- **Read feedback JSON files** (from `active/` directory)
- **Analyze patterns** using human judgment
- **Write markdown documentation**
- **Update YAML status files**

No unit tests, no code changes to `packages/quilto/` or `packages/swealog/`.

### Pre-Requisite: Collect Feedback First

**IMPORTANT:** Before running this analysis, feedback needs to be collected from dogfooding the system with Stories 13.1-13.6 fixes applied.

To collect feedback:
```bash
# Run swealog with feedback enabled
swealog auto "your query here"

# After receiving response, provide feedback when prompted
# This records to tests/eval/feedback/active/
```

### Iteration 2 Patterns to Compare Against

From `tests/eval/feedback/archive/iter-002/analysis.md`:

| # | Pattern | Severity | Fix Applied |
|---|---------|----------|-------------|
| 7 | Temporal Context Blindness (Recency Unawareness) | High | Story 13.1 |
| 8 | Keyword Retrieval Misses Exact Matches | High | Story 13.2 |
| 9 | Context Loss in Multi-Turn Conversations | Medium | Story 13.3 |
| 10 | Ambiguous LOG vs QUERY Classification | Medium | Story 13.5 |
| 11 | Clarification Questions Generated But Not Asked | Medium | Story 13.4 |
| 12 | Analyzer Should Attempt Indirect Estimation | Low | Story 13.6 |

### Analysis Template (Follow This Structure)

```markdown
# Iteration 3 Feedback Analysis

**Date Range:** [Start] to [End]
**Records Analyzed:** N
**LLM Provider:** [Determine from config or records]
**Analyst:** [Agent] + Jongkuk Lim

---

## Executive Summary

[Summary of findings - what's resolved, what persists, what's new]

---

## Records Summary

| # | ID | Date | Query Summary | Entries Retrieved | Sentiment |
|---|-----|------|---------------|-------------------|-----------|
| 1 | `xxx` | YYYY-MM-DD HH:MM | [Query] | N | **Positive/Mixed/Negative** |
...

### Sentiment Distribution
- **Positive:** N (X%)
- **Mixed:** N (X%)
- **Negative:** N (X%)

---

## Iteration 2 Pattern Status

### Pattern 7: Temporal Context Blindness
**Status:** RESOLVED / PERSISTS / MODIFIED
**Evidence:** [Specific records demonstrating status]

[Repeat for all 6 patterns]

---

## New Patterns Identified

### Pattern N: [Name]
**Severity:** High/Medium/Low | **Evidence:** [Record IDs]
**Description:** [What's happening]
**Root Cause:** [Why it's happening]
**Impact:** [How it affects users]

---

## Recommendations for Epic 14

[List of prioritized improvement stories]

---

## Appendix: User Feedback Verbatim

[Table of all user feedback quotes]
```

### stories-generated.md Template

```markdown
# Epic 14 Stories Generated from Iteration 3 Analysis

**Source:** Iteration 3 Feedback Analysis (YYYY-MM-DD)
**Records Analyzed:** N

---

## Recommended Stories

### Story 14.1: [Title]

**Priority:** High | **Effort:** [Size]

**As a** Quilto user,
**I want** [capability],
**So that** [benefit].

**Acceptance Criteria:**
1. **Given** [context]
   **When** [action]
   **Then** [expected result]

**Evidence:** [Record IDs and quotes supporting this story]

---

[Repeat for each recommended story]
```

### File Structure After Completion

```
tests/eval/feedback/
├── active/                    # Empty after archiving
├── archive/
│   ├── iter-001/             # Already exists (Epic 11)
│   │   ├── records/
│   │   ├── analysis.md
│   │   └── stories-generated.md
│   ├── iter-002/             # Already exists (Epic 12)
│   │   ├── records/
│   │   ├── analysis.md
│   │   └── stories-generated.md
│   └── iter-003/             # Created by this story
│       ├── records/          # JSON files moved here
│       ├── analysis.md       # New analysis document
│       └── stories-generated.md  # Epic 14 stories
└── README.md
```

### Previous Story Learnings (from 13.1-13.6)

1. **Story 13.1** - Added temporal recency awareness to Analyzer (calculates days since last workout)
2. **Story 13.2** - Simplified retrieval to date-range only with storage awareness (removed keyword/topical)
3. **Story 13.3** - Implemented conversation context for multi-turn queries
4. **Story 13.4** - Fixed clarification flow routing (now actually asks clarify questions)
5. **Story 13.5** - Improved intent classification for goal statements (treats as BOTH)
6. **Story 13.6** - Added indirect estimation fallback in Analyzer

### Anti-Patterns to Avoid

| Mistake | Correct |
|---------|---------|
| Creating code changes | This is analysis only - modify docs, not code |
| Interpreting feedback | Quote feedback verbatim, analyze patterns objectively |
| Skipping pattern comparison | Must compare against all 6 Iteration 2 patterns |
| Forgetting to archive | Move active/ files to archive/iter-003/records/ |
| Not updating sprint-status.yaml | Must add Epic 14 and mark Epic 13 done |

### Validation Checklist (Copy-Paste for Dev Agent)

```
- [ ] All feedback records read and cataloged
- [ ] Sentiment categorization complete for all records
- [ ] All 6 Iteration 2 patterns evaluated (RESOLVED/PERSISTS/NEW)
- [ ] New patterns documented with evidence
- [ ] Epic 14 stories drafted with proper format
- [ ] `archive/iter-003/` directory created
- [ ] All files moved from `active/` to `archive/iter-003/records/`
- [ ] `archive/iter-003/analysis.md` written
- [ ] `archive/iter-003/stories-generated.md` written
- [ ] `_bmad-output/planning-artifacts/epics.md` updated with Epic 14
- [ ] `_bmad-output/implementation-artifacts/sprint-status.yaml` updated
- [ ] Epic 13 status changed to "done" in sprint-status.yaml
```

### Key Files to Read

| File | Purpose |
|------|---------|
| `tests/eval/feedback/active/*.json` | Feedback records to analyze |
| `tests/eval/feedback/archive/iter-002/analysis.md` | Reference format and patterns |
| `_bmad-output/planning-artifacts/epics.md` | Add Epic 14 section |
| `_bmad-output/implementation-artifacts/sprint-status.yaml` | Update statuses |

### Key Files to Write

| File | Purpose |
|------|---------|
| `tests/eval/feedback/archive/iter-003/analysis.md` | Main analysis output |
| `tests/eval/feedback/archive/iter-003/stories-generated.md` | Epic 14 story drafts |
| `_bmad-output/planning-artifacts/epics.md` | Add Epic 14 section |
| `_bmad-output/implementation-artifacts/sprint-status.yaml` | Add Epic 14, mark Epic 13 done |

### Project Structure Notes

- Aligns with established iteration pattern from Epic 11, 12
- Follows directory conventions in `project-context.md`
- No conflicts with other Epic 13 stories (13.1-13.6 are all complete)
- Stories 11.4 and 12.6 provide precedent for analysis methodology

### References

| Source | Content |
|--------|---------|
| `tests/eval/feedback/archive/iter-002/analysis.md` | Iteration 2 analysis (template) |
| `_bmad-output/planning-artifacts/epics.md#Story 12.6` | Previous analysis story definition |
| `_bmad-output/planning-artifacts/epics.md#Story 13.7` | This story definition |
| `_bmad-output/implementation-artifacts/epic-12/12-6-analyze-feedback-dataset-iter-2.md` | Previous analysis story file |

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

N/A - Analysis task

### Completion Notes List

### File List
