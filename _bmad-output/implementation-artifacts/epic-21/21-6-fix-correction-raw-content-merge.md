# Story 21.6: Fix CORRECTION Raw Content Merge

Status: ready-for-dev

## Story

As a **Swealog user**,
I want **corrections to merge with original entry content**,
so that **my corrected log entries retain meaningful context**.

## Acceptance Criteria

1. **Given** correction "actually it was 20 minutes at 7.5kph"
   **When** targeting entry with raw_content "Ran treadmill for 35 minutes at 8kph"
   **Then** corrected raw_content becomes "Ran treadmill for 20 minutes at 7.5kph" (merged, not literal replacement)

2. **Given** correction that changes a single value (e.g., duration)
   **When** applied to original entry
   **Then** all original context is preserved (activity type, location, notes, etc.)

3. **Given** correction that adds new information (e.g., "I also did stretching after")
   **When** applied to original entry
   **Then** new information is appended to existing content

4. **Given** Parser in correction mode
   **When** generating raw_content
   **Then** output is a complete standalone description, NOT the literal correction text

## Tasks / Subtasks

- [ ] Task 1: Analyze current Parser correction prompt (AC: #1, #4)
  - [ ] 1.1: Read `packages/quilto/quilto/agents/parser.py` correction mode section (~line 144-200)
  - [ ] 1.2: Identify where `raw_content` generation instruction exists
  - [ ] 1.3: Document current prompt behavior in Dev Notes below

- [ ] Task 2: Update Parser correction prompt to merge content (AC: #1, #2, #3, #4)
  - [ ] 2.1: Add explicit instruction: "Generate a complete, standalone raw_content that MERGES the correction INTO the original entry content. Do NOT simply echo the correction text."
  - [ ] 2.2: Add instruction to preserve original context: "Preserve the activity type, location, equipment, and any other details from the original entry that are NOT being corrected."
  - [ ] 2.3: Add few-shot examples:
    ```
    === CORRECTION MERGE EXAMPLES ===
    Example 1 - Value correction:
      original_raw_content: "Ran treadmill for 35 minutes at 8kph"
      correction_target: "actually it was 20 minutes at 7.5kph"
      → raw_content: "Ran treadmill for 20 minutes at 7.5kph"
      (NOT: "actually it was 20 minutes at 7.5kph")

    Example 2 - Partial correction:
      original_raw_content: "Did 5 sets of bench press at 80kg, felt strong"
      correction_target: "it was 4 sets not 5"
      → raw_content: "Did 4 sets of bench press at 80kg, felt strong"
      (preserves weight and notes)

    Example 3 - Addition:
      original_raw_content: "Morning run 5km"
      correction_target: "I also did stretching after"
      → raw_content: "Morning run 5km, followed by stretching"
    ```
  - [ ] 2.4: Ensure Parser receives original entry's raw_content in context (verify `format_recent_entries()` includes full raw_content for target entry)

- [ ] Task 3: Verify original content is available to Parser (AC: #1, #2)
  - [ ] 3.1: Check `format_recent_entries()` output - does it include full `raw_content`?
  - [ ] 3.2: If truncated (currently 80 chars), consider passing full `raw_content` for the target entry specifically
  - [ ] 3.3: Alternative: Add `original_raw_content` field to correction context in `process_correction()`

- [ ] Task 4: Add unit tests for merge behavior (AC: #1, #2, #3, #4)
  - [ ] 4.1: Add `test_correction_merges_with_original_content()` in `test_parser_correction_matching.py`
  - [ ] 4.2: Add `test_correction_preserves_unmodified_context()` - verify activity type preserved
  - [ ] 4.3: Add `test_correction_does_not_literal_replace()` - verify output != input correction text
  - [ ] 4.4: Add `test_correction_addition_appends_to_original()` - verify addition case

- [ ] Task 5: Integration test with full flow (AC: #1-#4)
  - [ ] 5.1: Add `test_correction_flow_produces_merged_raw_content()` in `test_correction_flow.py`
  - [ ] 5.2: Create entry with "Ran treadmill for 35 minutes at 8kph"
  - [ ] 5.3: Apply correction "actually 20 minutes at 7.5kph"
  - [ ] 5.4: Verify raw file contains merged content (includes "treadmill" and "20 minutes")
  - [ ] 5.5: Verify raw file does NOT contain literal "actually"

- [ ] Task 6: Run validation (AC: #1-#4)
  - [ ] 6.1: `make check` - 0 lint/type errors
  - [ ] 6.2: `make validate` - all tests pass
  - [ ] 6.3: Manual test with real query to verify merge behavior

## Dev Notes

### Problem Statement

**Current Behavior (BUG):**
```
Original entry: "Actually my treadmill was 35 minutes not 30"
User correction: "actually it was 20 minutes at about 7.5kph"
Result raw_content: "actually it was 20 minutes at about 7.5kph"  ← LITERAL REPLACEMENT
```

The corrected raw file loses ALL context about what activity it was (treadmill, running, etc.).

**Expected Behavior:**
```
Original entry: "Actually my treadmill was 35 minutes not 30"
User correction: "actually it was 20 minutes at about 7.5kph"
Result raw_content: "Ran treadmill for 20 minutes at 7.5kph"  ← MERGED
```

### Root Cause

In Story 21.1, the Parser was instructed to output `raw_content` as the "complete corrected section content". However, the prompt doesn't explicitly tell the Parser to **merge** the correction with original content. The Parser is interpreting this as "output what the user said" rather than "apply the user's correction to the original and output the result".

### Discovery Source

User feedback from `tests/eval/feedback/active/2026-01-29_380d908c.json`:
> "I can see it got replaced in original record at right place. however, this is terrible. original raw markdown had running log information but now it just have 'actually it was 20 minutes at about 7.5kph' only. it has no information on what it was."

### Current Parser Prompt Analysis (Fill during Task 1)

Location: `packages/quilto/quilto/agents/parser.py`

Current correction prompt section (to be analyzed):
- [ ] Does it mention merging?
- [ ] Does it have examples of correct merge behavior?
- [ ] Does it receive original raw_content?

### Key Files

| File | Purpose |
|------|---------|
| `packages/quilto/quilto/agents/parser.py` | Parser prompt - ADD merge instructions |
| `packages/quilto/quilto/flow/correction.py` | Correction flow - may need to pass original content |
| `packages/quilto/tests/test_parser_correction_matching.py` | Parser tests - ADD merge tests |
| `packages/quilto/tests/test_correction_flow.py` | Integration tests - ADD flow test |

### Architecture Compliance

| Requirement | Status |
|-------------|--------|
| Changes in Quilto (not Swealog) | Yes - all changes are framework-level |
| Domain-agnostic | Yes - merge behavior applies to any domain |
| Existing patterns followed | Yes - extends existing Parser prompt |
| Google-style docstrings | Required for any new functions |

### Anti-Patterns to Avoid

| Anti-Pattern | Correct Approach |
|--------------|------------------|
| Just add "merge" to prompt | Add explicit examples showing correct behavior |
| Assume raw_content is available | Verify and ensure Parser receives original content |
| Test only happy path | Test literal replacement is NOT happening |

### References

- [Source: `tests/eval/feedback/active/2026-01-29_380d908c.json`] - User feedback
- [Source: `_bmad-output/implementation-artifacts/epic-21/21-1-redesign-correction-edit-raw-markdown.md`] - Original correction design
- [Source: `_bmad-output/implementation-artifacts/epic-21/21-4-improve-parser-correction-entry-matching.md`] - Parser prompt structure
- [Source: `packages/quilto/quilto/agents/parser.py`] - Parser implementation

## Dev Agent Record

### Agent Model Used

(To be filled by Dev agent)

### Debug Log References

(To be filled by Dev agent)

### Completion Notes List

(To be filled by Dev agent)

### File List

(To be filled by Dev agent)
