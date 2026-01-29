# Story 21.7: Fix Synthesizer Entry References

Status: done

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

- [x] Task 1: Fix Analyzer entry formatting - ROOT CAUSE (AC: #3)
  - [x] 1.1: Update `_format_entries()` in `packages/quilto/quilto/agents/analyzer.py` (line ~77-101)
    - Current: `[{i}] Date: {date_str}` uses index-based numbering
    - Change to: `[{date_str}] Content: {raw_content}` or use date as primary reference
  - [x] 1.2: Update Analyzer prompt to instruct LLM to cite entries by DATE, not by index number
  - [x] 1.3: Add explicit instruction: "When citing evidence, reference entries by their DATE (e.g., '2026-01-23 entry' or 'January 23rd entry'), NEVER by index number (e.g., 'Entry 1')."

- [x] Task 2: Fix Synthesizer analysis formatting (AC: #1, #3)
  - [x] 2.1: Update `_format_analysis()` in `packages/quilto/quilto/agents/synthesizer.py` (line ~69-94)
    - Current: `[{i}] {finding.claim}` uses numbered indices
    - Change to: Use dates from evidence citations instead of indices
  - [x] 2.2: Add prompt instruction: "When referencing findings or evidence, ALWAYS use dates (YYYY-MM-DD or natural language like 'January 23rd'), NEVER use index numbers like 'Entry 1' or '[1]'."

- [x] Task 3: Update Synthesizer prompt for date-based citations (AC: #1, #2)
  - [x] 3.1: Add explicit instruction for date usage: "When citing evidence, ALWAYS use the entry date (YYYY-MM-DD format or natural language like 'January 23rd'), NEVER use internal entry numbers or indexes like 'Entry 23'."
  - [x] 3.2: Add instruction for same-day disambiguation: "If multiple entries exist on the same day, include the time (e.g., 'January 23rd at 09:00') or descriptive context (e.g., 'the morning run on Jan 23')."
  - [x] 3.3: Add example in prompt:
    ```
    BAD: "Entry 23 shows you ran 5km, Entry 24 corrected the duration"
    GOOD: "On January 23rd you ran 5km. You later corrected the duration on January 28th."
    ```

- [x] Task 4: Update evidence_cited output format (AC: #4)
  - [x] 4.1: Check `SynthesizerOutput` model in `packages/quilto/quilto/agents/models.py`
  - [x] 4.2: Update prompt to specify evidence_cited format: "YYYY-MM-DD: <content>" or "Month Day: <content>"
  - [x] 4.3: Add example: `evidence_cited: ["2026-01-23: ran 5km in 30min", "2026-01-28: corrected to 35min"]`

- [x] Task 5: Add tests (AC: #1, #2, #3, #4)
  - [x] 5.1: Add `test_analyzer_formats_entries_with_dates()` - verify `_format_entries()` uses dates not indices
  - [x] 5.2: Add `test_synthesizer_format_analysis_uses_dates()` - verify `_format_analysis()` uses dates not indices
  - [x] 5.3: Add `test_synthesizer_prompt_contains_date_instructions()` - verify prompt has date citation instructions
  - [x] 5.4: Verify evidence_cited format via prompt instructions (AC #4 is prompt-driven, not model-enforced; actual LLM output format tested via integration tests)

- [x] Task 6: Run validation (AC: #1-#4)
  - [x] 6.1: `make check` - 0 lint/type errors
  - [x] 6.2: `make validate` - all tests pass
  - [x] 6.3: Manual test with query that spans multiple entries

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

### Root Cause Analysis (VERIFIED)

The "Entry X" format originates from **TWO locations** (code verified):

1. **Analyzer `_format_entries()` (PRIMARY SOURCE)** - Line 77-101 in `analyzer.py`:
   ```python
   line = f"[{i}] Date: {date_str}\n    Content: {raw_content}"
   ```
   This uses `[1]`, `[2]`, etc. indices. The LLM then naturally refers to these as "Entry 1", "Entry 2".

2. **Synthesizer `_format_analysis()` (SECONDARY)** - Line 69-94 in `synthesizer.py`:
   ```python
   for i, finding in enumerate(analysis.findings, 1):
       lines.append(f"  [{i}] {finding.claim}...")
   ```
   This propagates indexed references from Analyzer findings.

**Fix Strategy:**
- Task 1: Fix Analyzer's `_format_entries()` to use date as primary reference
- Task 2: Fix Synthesizer's `_format_analysis()` to not use numbered indices
- Task 3: Add explicit prompt instructions for date-based citations

### Entry Date Access

Entries have a `date` attribute directly accessible - NO need to parse entry IDs:
```python
# Entry objects have:
entry.date  # → date object (e.g., 2026-01-23)
entry.raw_content  # → string content

# Analyzer already extracts date_str:
date_str = str(getattr(entry, "date", "unknown"))  # Already in _format_entries()
```

**Key insight:** The date is already available; the fix is about how it's PRESENTED to the LLM (use date as reference, not index number).

### Key Files

| File | Purpose | Lines to Modify |
|------|---------|-----------------|
| `packages/quilto/quilto/agents/analyzer.py` | **PRIMARY** - `_format_entries()` uses indexed refs | Lines 77-101 |
| `packages/quilto/quilto/agents/synthesizer.py` | **SECONDARY** - `_format_analysis()` + prompt | Lines 69-94, 234-338 |
| `packages/quilto/quilto/agents/models.py` | `SynthesizerOutput.evidence_cited` model | Check format constraints |
| `packages/quilto/tests/test_analyzer.py` | Analyzer unit tests | Add date formatting tests |
| `packages/quilto/tests/test_synthesizer.py` | Synthesizer unit tests | Add date citation tests |

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

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

N/A - No debug logs needed

### Completion Notes List

1. **Task 1**: Fixed Analyzer `_format_entries()` to use `[{date_str}]` instead of `[{i}]`. Also added `DATE-BASED CITATION (CRITICAL)` section to Analyzer prompt with examples.

2. **Task 2**: Fixed Synthesizer `_format_analysis()` to use bullet points (`•`) instead of numbered indices (`[{i}]`).

3. **Task 3**: Added `DATE-BASED CITATION (CRITICAL)` section to Synthesizer prompt with good/bad examples and same-day disambiguation instructions.

4. **Task 4**: Covered by prompt instructions (`evidence_cited: ["2026-01-10: bench 185x5"]`). AC #4 is enforced via prompt engineering; the `SynthesizerOutput.evidence_cited` field is `list[str]` without format validation (by design, as format enforcement would be too restrictive for natural language).

5. **Task 5**: Added test classes:
   - `TestAnalyzerFormatsEntriesWithDates` (3 tests)
   - `TestSynthesizerFormatAnalysisUsesDates` (2 tests)
   - Additional prompt tests in both test files for date-based citation instructions

6. **Task 6**: `make validate` passes (2203 tests, 112 skipped)

### File List

| File | Change |
|------|--------|
| `packages/quilto/quilto/agents/analyzer.py` | Fixed `_format_entries()` to use dates, added DATE-BASED CITATION prompt section |
| `packages/quilto/quilto/agents/synthesizer.py` | Fixed `_format_analysis()` to use bullets, added DATE-BASED CITATION prompt section |
| `packages/quilto/tests/test_analyzer.py` | Added `TestAnalyzerFormatsEntriesWithDates` class and prompt tests |
| `packages/quilto/tests/test_synthesizer.py` | Added `TestSynthesizerFormatAnalysisUsesDates` class and prompt tests |

### Senior Developer Review (AI)

**Reviewer:** Claude Opus 4.5 (claude-opus-4-5-20251101)
**Date:** 2026-01-29

**Review Outcome:** ✅ APPROVED

**Findings Summary:**
- 0 HIGH issues
- 4 MEDIUM issues (all documentation clarifications, fixed)
- 1 LOW issue (cosmetic naming, not fixed)

**Issues Fixed:**
1. Updated Task 5.4 description to accurately reflect implementation (prompt-driven, not model-enforced)
2. Updated Completion Note #4 to clarify AC #4 enforcement approach
3. Story task descriptions now match actual implementation

**Verification:**
- `make validate` passes (2203 tests, 112 skipped)
- All acceptance criteria verified against implementation
- All tasks marked [x] confirmed implemented in code

**Notes:**
- AC #4 (evidence_cited format) is enforced via prompt engineering, which is appropriate for natural language outputs
- No code changes required - only story documentation corrections
