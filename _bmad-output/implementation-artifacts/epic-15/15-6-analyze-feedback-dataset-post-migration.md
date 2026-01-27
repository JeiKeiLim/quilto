# Story 15.6: Analyze Feedback Dataset Post-Migration

Status: ready-for-dev

## Story

As a **Quilto framework developer**,
I want **to analyze user feedback after migrating to the new Quilto API**,
So that **we identify any new issues or regressions introduced by the architecture change**.

## Background

**Origin:** Epic 15 completion checkpoint
**Source:** Fresh dogfooding on new Quilto public API architecture
**Priority:** Medium | **Effort:** Medium (2-3 hours)
**Type:** Analysis - generates next iteration stories (iter-004)

This is the first dogfooding iteration on the new architecture:
- Epic 14 was skipped (would have fixed issues in OLD manual wiring)
- Epic 15 restructured orchestration (Quilto class + LangGraph + Sessions)
- Story 15.5 fixed the `retrieval_history` bug that was preventing Observer from running
- This story validates the new architecture works correctly

Key questions to answer:
1. Did skipped Epic 14 issues (Pattern 17, 16, 7, 11, 13) resolve naturally with new architecture?
2. Are there new issues introduced by the LangGraph orchestration?
3. Is Observer working? (`logs/context/global.md` should contain preferences/patterns/facts)
4. Does session-based conversation work correctly for multi-turn queries?

## Acceptance Criteria

1. **Given** Epic 15 stories 15-1 through 15-5 are complete
   **When** this story begins
   **Then** the new Quilto API is fully functional

2. **Given** at least 10 new feedback records collected (minimum threshold)
   **When** analyzed
   **Then** patterns are identified and categorized by agent (Router, Planner, Retriever, Analyzer, Synthesizer, Observer)

3. **Given** the analysis is complete
   **When** issues are found
   **Then** stories for Epic 16 are generated in `sprint-status.yaml`

4. **Given** Observer should now be working (fixed in Story 15.5)
   **When** checking `logs/context/global.md`
   **Then** file exists with preferences/patterns/facts sections populated

5. **Given** skipped Epic 14 issues (6 patterns from human-review-iter-003.md)
   **When** reviewing feedback
   **Then** determine status for each: RESOLVED / PERSISTS / CHANGED

## Tasks / Subtasks

- [ ] Task 1: Collect fresh feedback (minimum 10 records)
  - [ ] 1.1: Check existing records in `tests/eval/feedback/active/` (2 records exist as of story creation)
  - [ ] 1.2: Run `swealog auto "..." --debug` for variety of queries until 10+ records collected
  - [ ] 1.3: Include variety: LOG only, QUERY only, BOTH, follow-ups, clarifications, preference statements

- [ ] Task 2: Verify Observer is working (AC: #4)
  - [ ] 2.1: Check `logs/context/global.md` exists (correct path, not `logs/logs/context/`)
  - [ ] 2.2: Verify file contains preferences/patterns/facts sections with actual content
  - [ ] 2.3: Test with explicit preference: `swealog auto "I always prefer kg over lbs" --debug`
  - [ ] 2.4: Document what triggers `should_update=True` vs `should_update=False`

- [ ] Task 3: Verify session conversation works
  - [ ] 3.1: Test multi-turn conversation (follow-up question referencing previous response)
  - [ ] 3.2: Test clarification flow (ambiguous query → clarification question → user response)
  - [ ] 3.3: Test context preservation ("What about last month?" after asking about this month)

- [ ] Task 4: Analyze feedback patterns (AC: #2, #5)
  - [ ] 4.1: Categorize each record by agent: Router, Planner, Retriever, Analyzer, Synthesizer, Evaluator, Observer
  - [ ] 4.2: Compare against Epic 14 skipped issues (6 patterns from human-review-iter-003.md)
  - [ ] 4.3: Identify NEW issues specific to LangGraph orchestration
  - [ ] 4.4: Human review records marked "positive" by auto-feedback (auto-feedback has 25% false positive rate)

- [ ] Task 5: Generate Epic 16 stories (AC: #3)
  - [ ] 5.1: Create stories for issues with severity CRITICAL or HIGH
  - [ ] 5.2: Prioritize: 1=Data loss/wrong answers, 2=UX issues, 3=Minor polish
  - [ ] 5.3: Add Epic 16 section to `_bmad-output/implementation-artifacts/sprint-status.yaml`
  - [ ] 5.4: Create `tests/eval/feedback/archive/iter-004/stories-generated.md`

- [ ] Task 6: Archive iteration (AC: #2)
  - [ ] 6.1: Create `tests/eval/feedback/archive/iter-004/` directory
  - [ ] 6.2: Move all files from `active/` to `archive/iter-004/records/`
  - [ ] 6.3: Create `analysis.md` following format from `iter-003/analysis.md`
  - [ ] 6.4: Include human review summary (don't trust auto-feedback blindly)

## Dev Notes

### Existing Feedback Records

As of story creation, 2 records exist in `tests/eval/feedback/active/`:
- `2026-01-27_14b9034b.json`
- `2026-01-27_14b9034b_130808.json`

**Minimum target: 10 records** before analysis begins.

### Feedback Collection Commands

```bash
# Collect feedback with debug mode (required for feedback prompt)
swealog auto "What should I focus on today?" --debug
swealog auto "How was my workout this week?" --debug
swealog auto "I prefer tracking weight in kg" --debug
swealog auto "러닝 페이스 확인해줘" --debug

# Check Observer context
cat logs/context/global.md

# Check feedback files
ls -la tests/eval/feedback/active/
```

### Feedback Collection Location

```
tests/eval/feedback/
├── active/                    # Current collection (2 records exist)
├── archive/
│   ├── iter-001/              # Epic 11 feedback (9 records)
│   ├── iter-002/              # Epic 12 feedback (7 records)
│   ├── iter-003/              # Epic 13 feedback (16 records)
│   └── iter-004/              # NEW - Post-migration feedback (this story)
└── README.md                  # Process documentation
```

### Epic 14 Skipped Issues (MUST Re-evaluate)

From `tests/eval/feedback/archive/iter-003/human-review-iter-003.md`:

| # | Pattern | Severity | Description | Check If... |
|---|---------|----------|-------------|-------------|
| 17 | Planner skips retrieval | **CRITICAL** | Sets `next_action: clarify/synthesize` without trying retrieval | Still occurs with LangGraph `plan_node` |
| 16 | Goal context loss | HIGH | Router extracts goal but Synthesizer ignores it | Goal passed through state to `synthesize_node` |
| 7 | Temporal blindness | MEDIUM | "Days since last workout" not calculated | Analyzer considers recency in new flow |
| 11 | Clarification not blocking | MEDIUM | Questions generated but response continues | `check_clarify` conditional edge works |
| 13 | Response language mismatch | MINOR | English query → Korean response | Synthesizer matches query language |
| 14 | Evaluator false negative | MINOR | Flags missing data for dates with no logs | Evaluator checks actual storage |

### Key Architecture Changes to Validate

| Aspect | Before (Epic 13) | After (Epic 15) | Validation Check |
|--------|------------------|-----------------|------------------|
| Orchestration | Manual wiring in `query.py` (~400 lines) | LangGraph in `orchestration.py` | Same behavior, less code |
| Observer | Never invoked (bug) | Auto-triggers via `observe_node` | `logs/context/global.md` populated |
| Sessions | None | SQLite-backed `Session` class | Multi-turn conversation works |
| Conversation | No history | Full history in `session.messages` | Follow-up questions preserve context |
| Planner bug | `retrieval_history=None` caused ValidationError | Fixed to default `[]` (Story 15.5) | Planner runs without exception |

### Analysis Output Format

Use `tests/eval/feedback/archive/iter-003/analysis.md` as template. Required sections:

```markdown
# Feedback Analysis: Iteration 4 (Post-Migration)

**Analysis Date:** YYYY-MM-DD
**Records Analyzed:** N
**Analyst:** [Agent name]

## Executive Summary
- Positive: X% (N/Total)
- Mixed: Y% (N/Total)
- Negative: Z% (N/Total)
- Key finding: [One sentence summary]

## Observer Status (NEW for iter-004)
- Working: Yes/No
- Context file exists: Yes/No at `logs/context/global.md`
- Sections populated: preferences/patterns/facts/insights
- Example preference captured: [quote from global.md]

## Session Status (NEW for iter-004)
- Multi-turn conversation: Works/Broken
- Clarification blocking: Works/Broken
- Context preservation: Works/Broken

## Epic 14 Pattern Resolution
| # | Pattern | Epic 14 Status | Post-Migration Status | Evidence |
|---|---------|----------------|----------------------|----------|
| 17 | Planner skips retrieval | SKIPPED | RESOLVED/PERSISTS | Record IDs |
| ... | ... | ... | ... | ... |

## New Patterns Identified
| # | Pattern | Severity | Evidence | Suggested Fix |
|---|---------|----------|----------|---------------|

## Stories Generated for Epic 16
1. **16.X: [Title]** - [One sentence description]

## Appendix: Record Files
[List all records with sentiment]
```

## Test Strategy

This is an analysis story - **no automated tests**. Output artifacts:
1. `tests/eval/feedback/archive/iter-004/records/` - moved from active/
2. `tests/eval/feedback/archive/iter-004/analysis.md` - findings document
3. `tests/eval/feedback/archive/iter-004/stories-generated.md` - Epic 16 stories
4. `_bmad-output/implementation-artifacts/sprint-status.yaml` - Epic 16 section added

**Critical:** Auto-feedback has ~25% false positive rate. Manually verify any record marked "positive" that involves personalization, temporal context, or language matching.

## Previous Story Intelligence (15.5)

**Root Cause Fixed in 15.5:**
- `PlannerInput` was failing validation because `retrieval_history` was passed as `None` instead of `[]`
- This caused `plan_node` to fail silently (exception caught at lines 805-807)
- Result: entire query flow never reached `observe_node`

**Fix Applied:** Changed `orchestration.py:317-320` to default `retrieval_history` to `[]` instead of `None`

**Observer Now Working:**
- Context file created at `logs/context/global.md`
- Preferences/patterns/facts sections populate after queries with explicit preferences
- Example: "I always prefer kilograms over pounds" → `unit_preference: kilograms`

**Integration Tests Added:** 10 tests in `packages/quilto/tests/test_observer_integration.py`

### Observer Verification Commands

```bash
# 1. Run a query with explicit preference
swealog auto "I always prefer kilograms over pounds for body weight" --debug

# 2. Verify context file was created
ls -la logs/context/global.md

# 3. Check content
cat logs/context/global.md
# Expected: YAML frontmatter + sections with preference entry
```

**Expected `global.md` format after successful Observer run:**
```markdown
---
last_updated: 2026-01-27
version: 1
token_estimate: 50
---

# Global Context

## Preferences (certain)
- [2026-01-27|certain|post_query: user explicit preference] unit_preference: kilograms

## Patterns (likely)

## Facts (certain)

## Insights (tentative)
```

### Sample Queries for Feedback Collection

Include a mix of these categories to get comprehensive coverage:

| Category | Example Query | What to Check |
|----------|---------------|---------------|
| Temporal | "How long since my last upper body workout?" | Recency awareness (Pattern 7) |
| Personalization | "What should I focus on today?" | Planner retrieves data (Pattern 17) |
| Goal-oriented | "I want to lose 5kg by summer, what should I do?" | Goal context passed (Pattern 16) |
| Follow-up | "What about last month?" (after asking about this month) | Session context preserved |
| Preference | "I prefer kg over lbs" | Observer captures preference |
| Multilingual | "벤치프레스 1RM 추정해줘" | Response language matches (Pattern 13) |
| Clarification | "Recommend a workout" (ambiguous) | Clarification question blocks (Pattern 11) |
| Data gap | "Show my squat progress" (no squat data) | Graceful handling |

### References

| Source | Content |
|--------|---------|
| `_bmad-output/implementation-artifacts/epic-15/15-5-verify-observer-integration.md` | Observer fix details, root cause analysis |
| `tests/eval/feedback/archive/iter-003/human-review-iter-003.md` | **Critical:** Skipped Epic 14 patterns (6 patterns) |
| `tests/eval/feedback/archive/iter-003/analysis.md` | Template for analysis.md format |
| `tests/eval/feedback/README.md` | Feedback collection process |
| `packages/quilto/quilto/orchestration.py` | LangGraph orchestration with all nodes |
| `packages/swealog/swealog/api/dependencies.py` | `create_quilto()` with ObserverTriggerConfig |
| `_bmad-output/implementation-artifacts/sprint-status.yaml` | Where to add Epic 16 |

### Auto-Feedback Quality Warning

From human-review-iter-003.md analysis:
- **Auto-feedback false positive rate: 25%** (4/16 records)
- Records 2, 3, 13, 16 were marked "positive" but were actually negative/mixed on human review
- **Must manually verify** any record involving: personalization, temporal context, language matching, goal extraction

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

- `tests/eval/feedback/active/2026-01-27_14b9034b.json`
- `tests/eval/feedback/active/2026-01-27_14b9034b_130808.json`
- `logs/logs/context/global.md` (note: path doubling bug)

### Completion Notes List

#### Analysis Date: 2026-01-27

**Critical Finding: Incomplete Migration (Story 15-4)**

The migration in Story 15-4 was incomplete. Two critical issues identified:

1. **Lost Observability in Feedback Records**
   - OLD (iter-003): Full `intermediate_outputs` with complete agent data (reasoning, findings, evidence)
   - NEW (post-migration): Only `traces` with summaries (`agent_name`, `output_summary`)
   - Result: Cannot debug agent behavior from feedback records

2. **Swealog Bypasses Quilto Design**
   - `auto_cmd.py` calls `RouterAgent` directly BEFORE calling Quilto
   - Router runs TWICE (once in Swealog, once in Quilto orchestration)
   - Violates single-entry-point design

3. **Response Generation Broken**
   - Both feedback records show: `"final_response": "I encountered an error generating a response."`
   - Analyzer/Synthesizer failing silently (exception handlers don't add traces)
   - Retrieval works (23 entries), but downstream agents fail

4. **Path Doubling Bug (Minor)**
   - Observer writes to `logs/logs/context/global.md` instead of `logs/context/global.md`
   - Cause: `StorageRepository` adds `/logs/` but `base_path` already set to `logs/`

**Root Cause Analysis**

The `ProgressHandler.on_agent_complete()` callback only receives:
```python
async def on_agent_complete(self, agent: str, elapsed: float) -> None
```

Missing the actual agent OUTPUT. This is why feedback recording lost all intermediate data.

**Recommended Fix for Epic 16**

Extend `on_agent_complete` to pass full output:
```python
async def on_agent_complete(
    self, agent: str, elapsed: float, output: dict[str, Any]
) -> None
```

This lets developers decide how to use the output (logging, UI, ignore).

---

## Epic 16 Stories (Generated from Analysis)

### 16.1: Add Agent Output to ProgressHandler Callback (HIGH)
**Problem:** `on_agent_complete` doesn't pass agent output, losing observability
**Fix:** Add `output: dict[str, Any]` parameter to `on_agent_complete`
**Files:** `packages/quilto/quilto/handlers.py`, `packages/quilto/quilto/orchestration.py`

### 16.2: Fix Response Generation Failure (CRITICAL)
**Problem:** Synthesizer fails with "I encountered an error generating a response"
**Root Cause:** Likely cascading failure from Analyzer (need to investigate)
**Files:** `packages/quilto/quilto/orchestration.py` (analyze_node, synthesize_node)

### 16.3: Fix Path Doubling in Observer Context (LOW)
**Problem:** `logs/logs/context/global.md` instead of `logs/context/global.md`
**Fix:** Remove `/logs/` from `StorageRepository` context path OR change Swealog's base_path
**Files:** `packages/quilto/quilto/storage/repository.py` OR `packages/swealog/swealog/api/dependencies.py`

### 16.4: Remove Redundant Router Call in Swealog CLI (MEDIUM)
**Problem:** `auto_cmd.py` calls Router directly, then Quilto calls Router again
**Fix:** Use `session.process(mode="auto")` and get input_type from ProcessResult
**Files:** `packages/swealog/swealog/cli/auto_cmd.py`

### 16.5: Update Feedback Recording to Use Callback (MEDIUM)
**Problem:** `SimplifiedFeedbackRecord` only stores trace summaries
**Fix:** After 16.1, use callback to capture full intermediate outputs
**Depends On:** 16.1
**Files:** `packages/swealog/swealog/cli/auto_cmd.py`, `packages/swealog/swealog/cli/feedback.py`

### 16.6: Migrate LOG/CORRECTION Flows to Quilto API (HIGH)
**Problem:** LOG and CORRECTION flows call `execute_log_flow()` directly, bypassing Quilto
- Observer never triggers for LOG inputs (`enable_post_log=True` is useless)
- Inconsistent architecture (QUERY uses Quilto, LOG doesn't)
- Swealog imports internal Quilto agents (RouterAgent, ParserAgent)
**Fix:**
- Use `session.process(text, mode="log")` for LOG
- Use `session.process(text, mode="auto")` for BOTH (let Quilto handle both portions)
- Remove or deprecate `execute_log_flow()` (keep only for batch import if needed)
**Files:** `packages/swealog/swealog/cli/auto_cmd.py`, `packages/swealog/swealog/cli/flows.py`

### 16.7: Consolidate CLI to Single Auto Command (MEDIUM)
**Problem:** Swealog has 3 commands: `auto`, `ask`, `log` - fragmented, works around Router
- If Router classification is unreliable, fix Router, don't bypass it
- Swealog should be reference implementation demonstrating ideal Quilto usage
- Single entry point: `swealog auto "..."` → let Quilto handle everything
**Fix:**
- Remove `ask_cmd.py` and `log_cmd.py`
- Keep only `auto` command as single entry point
- All input goes through `session.process(text, mode="auto")`
**Files:**
- DELETE: `packages/swealog/swealog/cli/ask_cmd.py`
- DELETE: `packages/swealog/swealog/cli/log_cmd.py`
- MODIFY: `packages/swealog/swealog/cli/app.py` (remove command registrations)

---

### File List

| File | Action |
|------|--------|
| `_bmad-output/implementation-artifacts/epic-15/15-6-analyze-feedback-dataset-post-migration.md` | MODIFIED - Added analysis findings |
| `_bmad-output/implementation-artifacts/sprint-status.yaml` | MODIFIED - Added Epic 16 stories |
