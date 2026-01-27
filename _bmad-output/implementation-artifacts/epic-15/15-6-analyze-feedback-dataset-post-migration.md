# Story 15.6: Analyze Feedback Dataset Post-Migration

Status: backlog

## Story

As a **Quilto framework developer**,
I want **to analyze user feedback after migrating to the new Quilto API**,
So that **we identify any new issues or regressions introduced by the architecture change**.

## Background

**Origin:** Epic 15 completion checkpoint
**Source:** Fresh dogfooding on new Quilto public API architecture
**Priority:** Medium | **Effort:** Medium (2-3 hours)
**Type:** Analysis - generates next iteration stories

This is the first dogfooding iteration on the new architecture:
- Epic 14 was skipped (would have fixed issues in OLD manual wiring)
- Epic 15 restructured orchestration (Quilto class + LangGraph + Sessions)
- This story validates the new architecture works correctly

Key questions to answer:
1. Did existing issues (Pattern 7, 17 from Epic 14) resolve naturally?
2. Are there new issues introduced by the architecture change?
3. Is Observer working? (logs/logs/context/ should now be populated)
4. Does session-based conversation work correctly?

## Acceptance Criteria

1. **Given** Epic 15 stories 15-1 through 15-5 are complete
   **When** this story begins
   **Then** the new Quilto API is fully functional

2. **Given** at least 10 new feedback records collected
   **When** analyzed
   **Then** patterns are identified and categorized

3. **Given** the analysis is complete
   **When** issues are found
   **Then** stories for Epic 16 are generated

4. **Given** Observer should now be working
   **When** checking logs/logs/context/
   **Then** global-context.md contains accumulated knowledge

5. **Given** skipped Epic 14 issues
   **When** reviewing feedback
   **Then** determine if those issues persist, resolved, or changed

## Tasks / Subtasks

- [ ] Task 1: Collect fresh feedback (minimum 10 records)
  - [ ] 1.1: Use Swealog with new Quilto API for real queries
  - [ ] 1.2: Record feedback using existing infrastructure
  - [ ] 1.3: Include variety: LOG, QUERY, follow-ups, clarifications

- [ ] Task 2: Verify Observer is working
  - [ ] 2.1: Check logs/logs/context/global-context.md exists
  - [ ] 2.2: Verify it contains preferences/patterns/facts
  - [ ] 2.3: Note any issues with Observer behavior

- [ ] Task 3: Verify session conversation works
  - [ ] 3.1: Test multi-turn conversation
  - [ ] 3.2: Test clarification flow
  - [ ] 3.3: Test follow-up questions with context

- [ ] Task 4: Analyze feedback patterns
  - [ ] 4.1: Categorize by: Retrieval, Synthesis, Clarification, Observer, Session
  - [ ] 4.2: Compare to Epic 14 skipped issues
  - [ ] 4.3: Identify new issues specific to new architecture

- [ ] Task 5: Generate Epic 16 stories
  - [ ] 5.1: Create stories for identified issues
  - [ ] 5.2: Prioritize by frequency and severity
  - [ ] 5.3: Update sprint-status.yaml with Epic 16

- [ ] Task 6: Document findings
  - [ ] 6.1: Create analysis.md in tests/eval/feedback/archive/iter-004/
  - [ ] 6.2: Include comparison to pre-migration behavior
  - [ ] 6.3: Note any architecture-related learnings

## Dev Notes

### Feedback Collection Location

```
tests/eval/feedback/
├── archive/
│   ├── iter-001/  # Epic 11 feedback
│   ├── iter-002/  # Epic 12 feedback
│   ├── iter-003/  # Epic 13 feedback
│   └── iter-004/  # NEW - Post-migration feedback
```

### Epic 14 Issues to Re-evaluate

| Pattern | Description | Check If... |
|---------|-------------|-------------|
| 17 | Planner skips retrieval for personalization | Still occurs in LangGraph flow |
| 7 | Temporal blindness | Addressed by previous fixes |
| - | Response language mismatch | Still occurs |
| - | Evaluator false flags empty dates | Still occurs |

### Key Architecture Differences to Validate

| Before (Epic 13) | After (Epic 15) |
|------------------|-----------------|
| Manual agent wiring | LangGraph orchestration |
| No Observer invocation | Observer auto-triggers |
| No sessions | SQLite-backed sessions |
| No conversation context | Full history in session |

### Analysis Output Format

```markdown
# Feedback Analysis: Iteration 4 (Post-Migration)

## Summary
- Records analyzed: N
- Positive: X%
- Issues found: Y

## Observer Status
- Working: Yes/No
- Context entries: N

## Session Status
- Multi-turn works: Yes/No
- Clarification works: Yes/No

## Pattern Analysis
[Categorized findings]

## Epic 16 Stories
[Generated story list]
```

## Test Strategy

This is an analysis story - no automated tests. Output is:
1. Archived feedback in iter-004/
2. analysis.md document
3. Epic 16 stories in sprint-status.yaml
