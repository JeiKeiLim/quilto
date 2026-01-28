# Story 18.4: Dogfooding Iteration 6

Status: backlog

**Story Type:** Validation (minimal code changes)

## Story

As a **Swealog user and developer**,
I want to test the system after Epic 18 fixes,
so that I can discover any remaining issues.

## Acceptance Criteria

1. **Given** Stories 18.1-18.3 are complete
   **When** reproduction queries are run
   **Then** all previously failing queries now work

2. **Given** `--debug` flag
   **When** query is processed
   **Then** intermediate agent outputs are visible

3. **Given** goal-related query
   **When** clarification is needed
   **Then** no AttributeError (Story 18.3 fix verified)

4. **Given** query with retrievable data
   **When** processed
   **Then** response reflects data (not "no data") (Story 18.1 fix verified)

5. **Given** dogfooding session
   **When** 10+ queries tested
   **Then** feedback recorded for next iteration analysis

## Tasks

- [ ] Task 1: Prerequisites
  - [ ] Verify Stories 18.1, 18.2, 18.3 are done
  - [ ] Verify `make validate` passes
  - [ ] Clean up any stale feedback files

- [ ] Task 2: Verify Previous Fixes
  - [ ] Re-run Korean comprehensive analysis query (Story 18.1 verification)
  - [ ] Re-run "Am I on track for my fitness goals?" (Story 18.3 verification)
  - [ ] Verify `--debug` shows intermediate outputs (Story 18.2 verification)

- [ ] Task 3: Dogfooding Session
  - [ ] Test 10+ different query types
  - [ ] Record feedback for each query
  - [ ] Note any new issues discovered

- [ ] Task 4: Document Findings
  - [ ] Archive feedback files to `tests/eval/feedback/archive/iter-006/`
  - [ ] Create `analysis.md` if new patterns emerge
  - [ ] Generate Epic 19 stories if needed

## Query Types to Test

| Category | Example Query |
|----------|---------------|
| Factual | "How many workouts this week?" |
| Insight | "What's my training consistency?" |
| Temporal | "What did I do yesterday?" |
| Comparative | "Monday vs Wednesday workout?" |
| Goal-related | "Am I on track for goals?" |
| Korean | "이번 주 운동 요약해줘" |
| Comprehensive | "Analyze all my workout data" |
| Recommendation | "What should I focus on?" |
| Historical | "How has my strength improved?" |
| Specific | "What's my bench press PR?" |

## Dev Notes

### Feedback Recording

With `--debug` flag, feedback is automatically prompted after each response. Files go to:
```
tests/eval/feedback/active/YYYY-MM-DD_query-id.json
```

### Archive Process

After session:
```bash
mkdir -p tests/eval/feedback/archive/iter-006
mv tests/eval/feedback/active/*.json tests/eval/feedback/archive/iter-006/
```

### Previous Iteration Results

| Iteration | Queries | Success | Bugs Found |
|-----------|---------|---------|------------|
| iter-005 (Epic 17) | 6 | 4 (67%) | 3 |

### Target for This Iteration

- 10+ queries
- 80%+ success rate
- Document any new patterns

### References

- [Source: Story 17.11 - Verify Fixes with Dogfooding]
- [Source: `tests/eval/feedback/archive/iter-005/analysis.md`]
