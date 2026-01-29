# Story 21.7: Fix Synthesizer Entry References

Status: ready-for-dev

## Story

As a **Swealog user**,
I want **response references to use dates and times instead of entry numbers**,
so that **I can understand which workout is being discussed**.

## Acceptance Criteria

1. **Given** Synthesizer generates a response citing evidence
   **When** referencing logged entries
   **Then** uses date format (e.g., "January 23rd" or "2026-01-23") NOT "Entry 23"

2. **Given** multiple entries from the same day
   **When** Synthesizer needs to distinguish them
   **Then** includes time (e.g., "January 23rd at 09:00" or "the morning entry on Jan 23")

3. **Given** Analyzer findings with entry references
   **When** passed to Synthesizer
   **Then** Synthesizer translates internal IDs to human-readable dates

4. **Given** evidence_cited list in Synthesizer output
   **When** formatting citations
   **Then** format is "YYYY-MM-DD: <content>" or "Month Day: <content>"

## Tasks / Subtasks

- [ ] Task 1: Analyze current Synthesizer output format (AC: #1, #3)
  - [ ] 1.1: Read `packages/quilto/quilto/agents/synthesizer.py` prompt section
  - [ ] 1.2: Identify where entry references are generated
  - [ ] 1.3: Check if Analyzer passes entry IDs or indexes to Synthesizer
  - [ ] 1.4: Document current behavior in Dev Notes below

- [ ] Task 2: Update Synthesizer prompt (AC: #1, #2, #3)
  - [ ] 2.1: Add instruction: "When citing evidence, ALWAYS use the entry date (YYYY-MM-DD format or natural language like 'January 23rd'), NEVER use internal entry numbers or indexes like 'Entry 23'."
  - [ ] 2.2: Add instruction for same-day disambiguation: "If multiple entries exist on the same day, include the time (e.g., 'January 23rd at 09:00') or descriptive context (e.g., 'the morning run on Jan 23')."
  - [ ] 2.3: Add example in prompt:
    ```
    BAD: "Entry 23 shows you ran 5km, Entry 24 corrected the duration"
    GOOD: "On January 23rd you ran 5km. You later corrected the duration on January 28th."
    ```

- [ ] Task 3: Update evidence_cited format (AC: #4)
  - [ ] 3.1: Check `SynthesizerOutput` model in `packages/quilto/quilto/agents/synthesizer.py`
  - [ ] 3.2: Ensure `evidence_cited` uses date format, not entry index
  - [ ] 3.3: If Analyzer passes indexes, update Synthesizer to extract date from entry data

- [ ] Task 4: Check Analyzer output format (AC: #3)
  - [ ] 4.1: Read `packages/quilto/quilto/agents/analyzer.py` to see how findings cite entries
  - [ ] 4.2: If Analyzer uses "Entry X" format, update Analyzer prompt too
  - [ ] 4.3: Ensure evidence array includes date information for Synthesizer to use

- [ ] Task 5: Add tests (AC: #1, #2, #3, #4)
  - [ ] 5.1: Add `test_synthesizer_uses_dates_not_entry_numbers()` in `test_synthesizer.py` or appropriate test file
  - [ ] 5.2: Add `test_synthesizer_disambiguates_same_day_entries()`
  - [ ] 5.3: Add `test_evidence_cited_format_uses_dates()`

- [ ] Task 6: Run validation (AC: #1-#4)
  - [ ] 6.1: `make check` - 0 lint/type errors
  - [ ] 6.2: `make validate` - all tests pass
  - [ ] 6.3: Manual test with query that spans multiple entries

## Dev Notes

### Problem Statement

**Current Behavior (CONFUSING):**
```
Query: "what was my last workout?"
Response: "Your most recent training session was a treadmill run on 2026-01-23.
You ran for 35 minutes at about 8 kph. This was logged originally as a 30‑minute
run (Entry 23) and later corrected to the 35‑minute duration (Entry 25) with
the speed confirmed in Entry 24."
```

User feedback: "what is entry 23, 24, and 25? it means nothing to user. needs actual reference on date and time."

**Expected Behavior:**
```
Query: "what was my last workout?"
Response: "Your most recent training session was a treadmill run on January 23rd.
You ran for 35 minutes at about 8 kph. This was originally logged as 30 minutes
and later corrected to 35 minutes on January 29th, with the speed (8 kph)
confirmed on January 28th."
```

### Discovery Source

User feedback from `tests/eval/feedback/active/2026-01-29_a5c95b2b.json`:
> "what is entry 23, 24, and 25? it means nothing to user. needs actual reference on date and time."

### Root Cause Analysis

The "Entry 23" format likely comes from:
1. **Analyzer** - when building findings, may reference entries by index in the retrieved list
2. **Synthesizer** - when citing evidence, may copy Analyzer's index-based references

Need to trace where this originates and fix at the source.

### Entry ID Format Reference

Entry IDs follow format: `{YYYY-MM-DD}_{HH-MM-SS}`
Example: `2026-01-23_09-00-00`

The date and time are extractable from the ID itself:
- Date: `entry_id.split("_")[0]` → "2026-01-23"
- Time: `entry_id.split("_")[1].replace("-", ":")` → "09:00:00"

### Key Files

| File | Purpose |
|------|---------|
| `packages/quilto/quilto/agents/synthesizer.py` | Synthesizer prompt - primary fix location |
| `packages/quilto/quilto/agents/analyzer.py` | Analyzer prompt - may also need update |
| `packages/quilto/tests/test_synthesizer.py` | Synthesizer tests (if exists) |
| `packages/quilto/tests/test_analyzer.py` | Analyzer tests (if exists) |

### Architecture Compliance

| Requirement | Status |
|-------------|--------|
| Changes in Quilto (not Swealog) | Yes - all changes are framework-level |
| Domain-agnostic | Yes - date formatting applies to any domain |
| Existing patterns followed | Yes - prompt engineering fix |

### Anti-Patterns to Avoid

| Anti-Pattern | Correct Approach |
|--------------|------------------|
| Just tell Synthesizer "don't use Entry X" | Provide clear alternative format with examples |
| Assume Analyzer format is correct | Check and fix Analyzer if it's the source |
| Hardcode date format | Use consistent format throughout (YYYY-MM-DD or natural language) |

### References

- [Source: `tests/eval/feedback/active/2026-01-29_a5c95b2b.json`] - User feedback
- [Source: `packages/quilto/quilto/agents/synthesizer.py`] - Synthesizer implementation
- [Source: `packages/quilto/quilto/agents/analyzer.py`] - Analyzer implementation

## Dev Agent Record

### Agent Model Used

(To be filled by Dev agent)

### Debug Log References

(To be filled by Dev agent)

### Completion Notes List

(To be filled by Dev agent)

### File List

(To be filled by Dev agent)
