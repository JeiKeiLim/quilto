# Story 11.4: Analyze Feedback Dataset

Status: done

## Story

As a **Quilto developer**,
I want **to analyze collected feedback with Mary (Analyst) and Jongkuk Lim**,
So that **patterns are identified and improvement stories are generated for the next dogfooding iteration (Epic 12)**.

## Background

This is an **analysis story**, not an implementation story. The goal is to:
1. Review all feedback records collected during dogfooding
2. Identify patterns in user feedback and system behavior
3. Generate actionable improvement stories for Epic 12
4. Archive Iteration 1 and prepare for the next cycle

**Current Feedback Dataset:**
- 9 feedback records in `tests/eval/feedback/active/`
- Date range: 2026-01-20 to 2026-01-24
- All using OpenRouter (`llm-config-openai.yaml`)

## Acceptance Criteria

1. **AC1: All Feedback Records Analyzed**
   - **Given** feedback records in `tests/eval/feedback/active/`
   - **When** Mary (Analyst) reviews each record
   - **Then** each record's intermediate outputs, final response, and user feedback are documented
   - **And** feedback sentiment is categorized (positive, negative, neutral, mixed)

2. **AC2: Patterns Identified**
   - **Given** the analyzed feedback records
   - **When** patterns are identified
   - **Then** analysis documents:
     - Which query types get poor feedback?
     - Which intermediate step correlates with quality issues?
     - Are there domain-specific patterns?
     - Are there LLM provider-specific patterns?
   - **And** each pattern has supporting evidence (record IDs)

3. **AC3: Improvement Stories Generated**
   - **Given** the identified patterns
   - **When** improvement stories are generated
   - **Then** each story has:
     - Clear user story format (As a..., I want..., So that...)
     - Acceptance criteria
     - Estimated effort (small/medium/large)
     - Priority (high/medium/low)
   - **And** stories are documented in `archive/iter-001/stories-generated.md`

4. **AC4: Iteration Archived**
   - **Given** analysis is complete
   - **When** archiving iteration
   - **Then** create `tests/eval/feedback/archive/iter-001/` directory
   - **And** create `archive/iter-001/records/` subdirectory
   - **And** move all files from `active/` to `archive/iter-001/records/`
   - **And** create `archive/iter-001/analysis.md` with findings
   - **And** create `archive/iter-001/stories-generated.md` with improvement stories
   - **And** leave `active/` with only `.gitkeep` for next iteration

5. **AC5: Epic 12 Scope Defined**
   - **Given** the generated stories
   - **When** Epic 12 is scoped
   - **Then** priority stories are selected for next iteration
   - **And** Epic 12 definition is added to `_bmad-output/planning-artifacts/epics.md`
   - **And** `sprint-status.yaml` is updated with Epic 12 and its stories

## Tasks / Subtasks

- [x] **Task 1:** Load and Review All Feedback Records (AC: 1)
  - [x] 1.1: Read `2026-01-20_f89c6142.json` - Korean query with malformed JSON (OpenRouter)
  - [x] 1.2: Read `2026-01-20_f89c6142_183624.json` - Same query, different time
  - [x] 1.3: Read `2026-01-20_fec3d15f.json` - Unknown query
  - [x] 1.4: Read `2026-01-20_db9b34b5.json` - Working comparison query
  - [x] 1.5: Read `2026-01-21_8e8e6d87.json` - All workout summary query
  - [x] 1.6: Read `2026-01-21_14b9034b.json` - Unknown query
  - [x] 1.7: Read `2026-01-22_e16dbc36.json` - Marathon training query
  - [x] 1.8: Read `2026-01-22_e16dbc36_190829.json` - Same query, different time
  - [x] 1.9: Read `2026-01-24_3ec25871.json` - Exercise level maintenance query
  - [x] 1.10: Document each record's query, response quality, and user feedback
  - [x] 1.11: Categorize feedback sentiment (positive/negative/neutral/mixed)

- [x] **Task 2:** Analyze Patterns in Feedback (AC: 2)
  - [x] 2.1: Group records by feedback sentiment
  - [x] 2.2: Identify which intermediate step correlates with quality issues:
    - Router: Domain selection issues?
    - Planner: Strategy selection issues?
    - Retriever: Retrieval failures?
    - Analyzer: Analysis quality issues?
    - Synthesizer: Response formatting issues?
    - Evaluator: Missed quality issues?
  - [x] 2.3: Identify query type patterns (simple vs complex, Korean vs English)
  - [x] 2.4: Identify domain-specific patterns (fitness subdomains)
  - [x] 2.5: Identify LLM provider patterns (OpenRouter model behavior)
  - [x] 2.6: Document each pattern with supporting evidence (record IDs)

- [x] **Task 3:** Generate Improvement Stories (AC: 3)
  - [x] 3.1: For each identified pattern, draft an improvement story
  - [x] 3.2: Write stories in user story format with acceptance criteria
  - [x] 3.3: Estimate effort (small: 1-2 hours, medium: 2-4 hours, large: 4+ hours)
  - [x] 3.4: Assign priority (high: blocks usage, medium: degrades experience, low: nice-to-have)
  - [x] 3.5: Group stories by theme (retrieval, response quality, UX, etc.)
  - [x] 3.6: Document in `archive/iter-001/stories-generated.md`

- [x] **Task 4:** Archive Iteration 1 (AC: 4)
  - [x] 4.1: Create `tests/eval/feedback/archive/iter-001/` directory
  - [x] 4.2: Create `tests/eval/feedback/archive/iter-001/records/` subdirectory
  - [x] 4.3: Move all `.json` files from `active/` to `archive/iter-001/records/`
  - [x] 4.4: Write `archive/iter-001/analysis.md` with:
    - Summary of records analyzed
    - Key patterns identified
    - Root causes
    - Recommendations
  - [x] 4.5: Write `archive/iter-001/stories-generated.md` with generated stories
  - [x] 4.6: Verify `active/` only contains `.gitkeep`

- [x] **Task 5:** Define Epic 12 Scope (AC: 5)
  - [x] 5.1: Select high-priority stories for Epic 12
  - [x] 5.2: Add Epic 12 definition to `_bmad-output/planning-artifacts/epics.md`
  - [x] 5.3: Update `sprint-status.yaml` with Epic 12 and its stories
  - [ ] 5.4: Commit all changes (pending user action)

## Dev Notes

### Current Feedback Records Summary

Based on preliminary analysis, the 9 feedback records show these preliminary patterns:

| Record ID | Query (abbreviated) | Feedback Summary | Sentiment |
|-----------|---------------------|------------------|-----------|
| `f89c6142` | "내가 오늘 기록한 운동이 뭐였지?" | Malformed JSON, no data | Negative |
| `f89c6142_183624` | Same query, later time | Unknown | TBD |
| `fec3d15f` | Unknown | Unknown | TBD |
| `db9b34b5` | "지난주 운동량에 비해 이번주..." | Working date_range | Mixed |
| `8e8e6d87` | "내가 지금까지 했던 모든 운동을 총 정리해서 알려줘" | Response in wrong language | Mixed |
| `14b9034b` | Unknown | Unknown | TBD |
| `e16dbc36` | "내가 풀 마라톤을 5시간에 완주 할수 있을까?" | No logs retrieved, generic response | Negative |
| `e16dbc36_190829` | Same query, later time | Unknown | TBD |
| `3ec25871` | "지금 정도 운동 수준을 유지하는게 맞을까?" | Good but could be more detailed | Mixed |

### Known Issues from Previous Stories

From Story 11.3 investigation:
- **OpenRouter free-tier models** produce intermittent malformed JSON
- **Ollama (qwen2.5:7b)** consistently produces valid JSON
- Existing defensive code handles malformed dates

### Key Patterns to Investigate

**Pattern 1: Response Language Mismatch**
- User query in Korean, response in English
- Evidence: `2026-01-21_8e8e6d87.json` - User feedback: "The response language should have followed user's query language"
- Potential fix: Add language detection and force Synthesizer to respond in same language

**Pattern 2: Retrieval Strategy Gaps**
- Marathon query retrieved 0 entries despite having running logs
- Evidence: `2026-01-22_e16dbc36.json` - User feedback: "it did not refer to my logs even though there are related running logs"
- Potential fix: Improve Retriever keyword expansion or add date-based fallback

**Pattern 3: Response Detail Level**
- Users expect more detailed, analytic responses
- Evidence: `2026-01-24_3ec25871.json` - User feedback: "response could have been a bit more detail"
- Potential fix: Adjust Synthesizer prompt for more comprehensive responses

**Pattern 4: Retrieval Date Range**
- Planner uses too narrow date range (7 days) for queries needing longer context
- Evidence: `2026-01-24_3ec25871.json` - User feedback: "it would be nicer if it retrieved a bit longer period of logs"
- Potential fix: Adjust Planner heuristics for date range selection

### Analysis Methodology

This story uses **qualitative feedback analysis**:

1. **Read each feedback record completely**
   - Query text
   - All intermediate outputs (Router → Evaluator)
   - Final response
   - User feedback verbatim

2. **Categorize feedback sentiment**
   - Positive: User explicitly approves
   - Negative: User reports issues or failures
   - Neutral: Skipped feedback (empty string)
   - Mixed: User has both praise and criticism

3. **Identify root causes**
   - Which agent produced the issue?
   - Was it a prompt issue or code issue?
   - Is it model-specific (OpenRouter vs Ollama)?

4. **Generate actionable stories**
   - One story per distinct issue
   - Clear acceptance criteria
   - Effort and priority estimates

### Archive Directory Structure

After completion:
```
tests/eval/feedback/
├── active/
│   └── .gitkeep              # Empty for next iteration
├── archive/
│   ├── .gitkeep
│   └── iter-001/
│       ├── records/          # All JSON files from active/
│       │   ├── 2026-01-20_f89c6142.json
│       │   ├── 2026-01-20_f89c6142_183624.json
│       │   ├── 2026-01-20_fec3d15f.json
│       │   ├── 2026-01-20_db9b34b5.json
│       │   ├── 2026-01-21_8e8e6d87.json
│       │   ├── 2026-01-21_14b9034b.json
│       │   ├── 2026-01-22_e16dbc36.json
│       │   ├── 2026-01-22_e16dbc36_190829.json
│       │   └── 2026-01-24_3ec25871.json
│       ├── analysis.md       # Findings and patterns
│       └── stories-generated.md  # Epic 12 stories
└── README.md
```

### Collaboration Notes

This story involves **Mary (Analyst)** and **Jongkuk Lim** working together:

- **Mary's Role:** Analyze patterns, identify root causes, draft improvement stories
- **Jongkuk's Role:** Provide domain expertise, prioritize stories, approve Epic 12 scope

The analysis session should produce:
1. A comprehensive understanding of current system weaknesses
2. Actionable improvement stories for Epic 12
3. Archived iteration for future reference

### Project Structure Notes

This story produces **documentation only** (no code changes):
- `tests/eval/feedback/archive/iter-001/analysis.md`
- `tests/eval/feedback/archive/iter-001/stories-generated.md`
- `_bmad-output/planning-artifacts/epics.md` (Epic 12 section)
- `_bmad-output/implementation-artifacts/sprint-status.yaml` (Epic 12 entries)

### Common Mistakes to Avoid

| Mistake | Prevention |
|---------|------------|
| Skipping feedback records | Must read ALL 9 records |
| Generating too many stories | Focus on high-impact issues (3-5 stories) |
| Vague acceptance criteria | Each story must have testable criteria |
| Not archiving properly | Follow exact directory structure |
| Forgetting to update sprint-status.yaml | Include Epic 12 with stories |

### References

- [Source: tests/eval/feedback/README.md] Feedback collection documentation
- [Source: epics.md#Story-11.4] Story definition
- [Source: project-context.md] Development workflow
- [Source: 11-2-implement-feedback-recording-infrastructure.md] Feedback schema
- [Source: 11-3-investigate-retrieval-priority-bug.md] OpenRouter JSON issues

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

N/A (analysis story, no code)

### Completion Notes List

1. **Analyzed all 9 feedback records** from `tests/eval/feedback/active/`
2. **Identified 6 patterns** affecting user experience:
   - P1: Clarification never triggers (over-corrected)
   - P2: Retrieval strategy misses logs (wrong Planner strategy)
   - P3: LLM timeout too long (600s default)
   - P4: Malformed JSON crashes app (no retry)
   - P5: Response lacks detail (Synthesizer brevity)
   - P6: Response language mismatch (no detection)
3. **Generated 5 improvement stories** for Epic 12
4. **Archived Iteration 1:**
   - Moved 9 JSON files to `archive/iter-001/records/`
   - Created `archive/iter-001/analysis.md`
   - Created `archive/iter-001/stories-generated.md`
5. **Updated Epic 12 definition** in `epics.md`
6. **Updated sprint-status.yaml** with Epic 12 stories

### Sentiment Summary

| Sentiment | Count | % |
|-----------|-------|---|
| Positive | 1 | 11% |
| Mixed | 5 | 56% |
| Negative | 3 | 33% |

### Decisions Made During Analysis

| Topic | Decision | Rationale |
|-------|----------|-----------|
| Clarification trigger | Fix: Only when critical gaps + 0 entries | Balance over-asking vs never-asking |
| LLM timeout | 45 seconds uniform | Simple implementation, meets expectation |
| Malformed JSON | Retry same provider 1-2x | OpenRouter is non-deterministic |
| Response detail | Adjust Synthesizer prompt | More comprehensive default |

### File List

- `tests/eval/feedback/archive/iter-001/records/*.json` - 9 archived feedback records
- `tests/eval/feedback/archive/iter-001/analysis.md` - Detailed analysis findings
- `tests/eval/feedback/archive/iter-001/stories-generated.md` - 5 Epic 12 stories
- `_bmad-output/planning-artifacts/epics.md` - Updated with Epic 12 definition
- `_bmad-output/implementation-artifacts/sprint-status.yaml` - Updated with Epic 12 status
- `_bmad-output/implementation-artifacts/epic-11/11-4-analyze-feedback-dataset.md` - This file (marked done)

### Change Log

| Date | Change | Author |
|------|--------|--------|
| 2026-01-24 | Completed analysis with Mary (Analyst) + Jongkuk Lim | Claude Opus 4.5 |
