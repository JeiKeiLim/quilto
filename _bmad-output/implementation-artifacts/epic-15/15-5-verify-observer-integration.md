# Story 15.5: Verify Observer Integration and Context Population

Status: backlog

## Story

As a **Quilto framework developer**,
I want **to verify Observer triggers work and context is populated**,
So that **users get personalized responses based on accumulated knowledge**.

## Background

**Origin:** Epic 13 Retrospective - Observer never invoked
**Source:** `_bmad-output/planning-artifacts/CRITICAL-quilto-orchestration-design.md`
**Priority:** High | **Effort:** Small (1-2 hours)
**Type:** Verification + bug fixes

The core problem that triggered Epic 15:
- Observer infrastructure exists in Quilto (`state/observer_triggers.py`)
- Observer agent exists (`agents/observer.py`)
- But `logs/logs/context/` is EMPTY - Observer is never called

After Epic 15 implementation, Observer should run automatically via Quilto orchestration.

## Acceptance Criteria

1. **Given** a query processed through Quilto
   **When** the query completes successfully
   **Then** `trigger_post_query()` is invoked

2. **Given** Observer determines context should update
   **When** `should_update=True` in ObserverOutput
   **Then** `logs/logs/context/global-context.md` is updated

3. **Given** a LOG input with personal record mention
   **When** processed through Quilto
   **Then** `trigger_significant_log()` is invoked

4. **Given** multiple queries over time
   **When** context accumulates
   **Then** preferences/patterns/facts sections grow

5. **Given** a fresh Swealog installation
   **When** first query is processed
   **Then** `logs/logs/context/global-context.md` is created if not exists

## Tasks / Subtasks

- [ ] Task 1: Manual verification of Observer invocation
  - [ ] 1.1: Clear `logs/logs/context/` directory
  - [ ] 1.2: Run a query through Swealog CLI
  - [ ] 1.3: Verify `global-context.md` is created/updated
  - [ ] 1.4: Check log output shows Observer was invoked

- [ ] Task 2: Add Observer invocation logging
  - [ ] 2.1: Add debug log in `trigger_post_query()` when called
  - [ ] 2.2: Add debug log when context is updated
  - [ ] 2.3: Verify logs appear during query processing

- [ ] Task 3: Write integration test for Observer
  - [ ] 3.1: Create test that processes a query
  - [ ] 3.2: Assert `global-context.md` exists after processing
  - [ ] 3.3: Assert context file was modified (check mtime)

- [ ] Task 4: Fix any issues discovered
  - [ ] 4.1: If Observer not invoked, trace LangGraph to find where it should be called
  - [ ] 4.2: If context not written, check GlobalContextManager integration
  - [ ] 4.3: If significant_log not triggered, verify SignificantEntryDetector

- [ ] Task 5: Document Observer behavior
  - [ ] 5.1: Update architecture.md with Observer invocation points
  - [ ] 5.2: Add example of context file format
  - [ ] 5.3: Document trigger conditions

- [ ] Task 6: Run validation
  - [ ] 6.1: Run `make check` (lint + typecheck)
  - [ ] 6.2: Run `make validate` (full validation)
  - [ ] 6.3: Run `make test-ollama` (integration tests)

## Dev Notes

### Observer Triggers (from observer_triggers.py)

| Trigger | When | Effect |
|---------|------|--------|
| `post_query` | After successful query | Learn from Q&A exchange |
| `user_correction` | After correction processed | Learn from user feedback |
| `significant_log` | After notable log entry | Learn from PRs, milestones |
| `periodic` | Scheduled batch (optional) | Batch context review |

### Context File Location

```
logs/
├── logs/
│   └── context/
│       └── global-context.md  # ← Should be populated
```

### Expected Context Format

```markdown
---
last_updated: 2026-01-27T10:30:00
version: 1
token_estimate: 450
---

# Global Context

## Preferences (certain)
- [2026-01-27|certain|post_query] workout_time: prefers morning workouts

## Patterns (likely)
- [2026-01-27|likely|post_query] rest_days: typically rests on weekends

## Facts (certain)
- [2026-01-27|certain|user_correction] bench_1rm: 225 lbs

## Insights (tentative)
- [2026-01-27|tentative|post_query] fatigue_pattern: tends to overtrain when stressed
```

### Debugging Tips

If Observer not invoked:
1. Check LangGraph has OBSERVE node after EVALUATE
2. Check conditional routing calls OBSERVE
3. Add `print()` in `observe_node()` to trace

If context not updated:
1. Check `GlobalContextManager.apply_updates()` is called
2. Check file permissions on `logs/logs/context/`
3. Check ObserverOutput.should_update value

## Test Strategy

- Integration test with real Ollama
- Check file system for context file creation
- Use debug=True to verify Observer appears in traces
