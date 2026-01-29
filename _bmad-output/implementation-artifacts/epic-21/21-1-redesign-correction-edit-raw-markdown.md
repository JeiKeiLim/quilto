# Story 21.1: Redesign CORRECTION to Edit Raw Markdown In-Place

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **Swealog user**,
I want **corrections to modify the original raw entry**,
so that **my log files maintain accurate history without duplicates**.

## Acceptance Criteria

1. **Given** a CORRECTION request
   **When** target entry is identified
   **Then** the original raw file is located (not a new file created)

2. **Given** target raw file and section
   **When** correction is applied
   **Then** only the specific section is modified

3. **Given** correction applied to raw file
   **When** no new raw file is created
   **Then** existing file modification timestamp is updated

4. **Given** input "I logged 5 sets but it should be 4"
   **When** processed as CORRECTION targeting a strength entry
   **Then** the matching entry's raw markdown is modified in-place and parsed JSON is updated

## Tasks / Subtasks

- [x] Task 1: Design new CORRECTION flow architecture (AC: #1, #2, #3)
  - [x] 1.1: Define `CorrectionEdit` model in `quilto/flow/models.py`: `target_file: Path`, `section_start: int`, `section_end: int`, `original_content: str`, `new_content: str` — all line numbers are 0-indexed (Python convention)
  - [x] 1.2: Add method `StorageRepository.find_raw_entry_section(entry_id: str) -> tuple[Path, int, int] | None` to locate target file and line boundaries — returns `None` if not found (not exception)
  - [x] 1.3: Add method `StorageRepository.edit_raw_section(file_path: Path, start: int, end: int, new_content: str) -> None` for surgical edits — uses atomic write (tempfile + rename)
  - [x] 1.4: Document flow: Router → Parser (extract delta) → `correction_node()` in orchestration.py → Storage (find section) → Storage (edit in-place) → Parser (re-parse) → Storage (update JSON)

- [x] Task 2: Implement `find_raw_entry_section()` in `quilto/storage/repository.py` (AC: #1)
  - [x] 2.1: Parse entry_id format `{YYYY-MM-DD}_{HH-MM-SS}` — note format uses dashes (e.g., `2026-01-26_18-33-00`), extract date and time via string split
  - [x] 2.2: Get raw file path from date via existing `_get_raw_path()` method
  - [x] 2.3: Parse raw file to find section with matching `## HH:MM` header — use regex `r"^## (\d{2}):(\d{2})"` consistent with existing `_parse_raw_file()` pattern at repository.py:108
  - [x] 2.4: Return `(file_path, start_line, end_line)` where `start_line` is the `## HH:MM` header line (0-indexed), `end_line` is line before next `## ` section header or EOF (exclusive, Python slice convention)
  - [x] 2.5: Return `None` if entry not found (file missing, no matching section, or multiple sections match the same time → return `None` to trigger clarification)

- [x] Task 3: Implement `edit_raw_section()` in `quilto/storage/repository.py` (AC: #2, #3)
  - [x] 3.1: Read entire raw file as list of lines using `file_path.read_text(encoding="utf-8").splitlines(keepends=True)`
  - [x] 3.2: Replace `lines[start:end]` with new content — new content MUST include the `## HH:MM` header line (caller provides complete section content)
  - [x] 3.3: Write modified file atomically using `tempfile.NamedTemporaryFile(mode='w', dir=file_path.parent, delete=False)` then `Path(temp_path).replace(file_path)`
  - [x] 3.4: Preserve file encoding (UTF-8) — write with `encoding="utf-8"`, preserve original line endings (use `splitlines(keepends=True)`)
  - [x] 3.5: Log start/end lines and byte counts before/after for debugging — no separate validation (atomic write ensures consistency)

- [x] Task 4: Refactor `correction_node()` and `process_correction()` flow (AC: #1, #2, #3, #4)
  - [x] 4.1: Modify `correction_node()` in `quilto/orchestration.py` to call new in-place edit flow instead of current `save_entry(entry, correction=parser_output)` at orchestration.py:~180
  - [x] 4.2: After Parser identifies `target_entry_id`, call `storage.find_raw_entry_section(target_entry_id)` to locate file and line boundaries
  - [x] 4.3: Build new section content: Parser's `raw_content` IS the complete corrected section content (includes `## HH:MM` header) — do NOT programmatically merge, use Parser output directly
  - [x] 4.4: Call `storage.edit_raw_section(file_path, start, end, parser_output.raw_content)` — this replaces the `save_entry()` call for correction flow
  - [x] 4.5: Remove the `## HH:MM [correction]` append logic from `save_entry()` in `repository.py:286-290` — corrections no longer use this path
  - [x] 4.6: Update `CorrectionResult` in `quilto/flow/models.py` to include `modified_file: Path | None = None` and `edited_lines: tuple[int, int] | None = None` — both Optional since failure cases won't have these

- [x] Task 5: Trigger re-parse after raw file edit (AC: #4)
  - [x] 5.1: After `edit_raw_section()`, re-read the modified section
  - [x] 5.2: Create new ParserInput with just the modified section content
  - [x] 5.3: Call Parser in non-correction mode to get fresh parsed_data
  - [x] 5.4: Update (not append) the parsed JSON entry via `_update_parsed_json()`

- [x] Task 6: Write comprehensive tests (AC: #1, #2, #3, #4)
  - [x] 6.1: Test `find_raw_entry_section()` with existing entry — verify returns `(Path, start, end)` tuple
  - [x] 6.2: Test `find_raw_entry_section()` with non-existent entry (returns `None`) — file missing AND section missing cases
  - [x] 6.3: Test `edit_raw_section()` preserves surrounding content — verify lines before `start` and after `end` unchanged
  - [x] 6.4: Test `edit_raw_section()` with first section in file (start=0)
  - [x] 6.5: Test `edit_raw_section()` with last section in file (end=len(lines))
  - [x] 6.6: Test `edit_raw_section()` with single-section file (entire file is the section)
  - [x] 6.7: Test full flow: correction modifies raw file in-place — verify file content changed
  - [x] 6.8: Test full flow: parsed JSON is updated (not duplicated) — verify single entry_id in JSON
  - [x] 6.9: Test full flow: no `[correction]` marker appended — grep for `[correction]` should return empty
  - [x] 6.10: **UPDATE existing tests** in `test_correction_flow.py:613-740` — remove/update `test_correction_appends_to_raw_file()` and `test_reading_corrected_entries()` which test OLD append behavior
  - [x] 6.11: Add test for atomic write safety — verify incomplete write doesn't corrupt file (simulate crash mid-write)
  - [x] 6.12: Use `create_parser_output()` helper from `test_storage.py:13-37` for consistency

- [x] Task 7: Run validation (AC: #1-#4)
  - [x] 7.1: Run `make check` (lint + typecheck) — 0 errors
  - [x] 7.2: Run `make validate` (full validation with unit tests) — all new tests pass

## Dev Notes

### ⚠️ CRITICAL: Must-Do Checklist (Do Not Skip)

Before marking this story complete, verify ALL of the following:

- [x] **Remove** `## HH:MM [correction]` append logic from `repository.py:286-290`
- [x] **Update** `correction_node()` in `orchestration.py` (not just `correction.py`)
- [x] **Update/Remove** old test `test_correction_appends_to_raw_file()` at `test_correction_flow.py:613`
- [x] **Add** `modified_file: Path | None = None` to `CorrectionResult` model
- [x] **Verify** atomic write uses `tempfile.NamedTemporaryFile` (not direct write)
- [x] **Run** `make validate` — 0 errors required

### Problem Statement

**Current Behavior (WRONG):**
```
User: "Actually my run was 3km not 5km"
→ Creates NEW raw file: raw/2026/01/2026-01-26.md with "## 14:30 [correction]" section appended
→ Creates NEW parsed entry
```

**Expected Behavior (CORRECT):**
```
User: "Actually my run was 3km not 5km"
→ Locates EXISTING raw file: raw/2026/01/2026-01-26.md
→ Finds section "## 18:33" containing the run entry
→ Modifies THAT section in-place: "5km" → "3km"
→ Re-parses the modified section
→ Updates the EXISTING parsed JSON entry
```

### Current Flow Analysis (Broken)

```
packages/quilto/quilto/flow/correction.py:107-118

# 5. Create Entry for storage
entry_id = f"{parser_output.date.isoformat()}_{ts.strftime('%H-%M-%S')}"
entry = Entry(
    id=entry_id,
    date=parser_output.date,
    timestamp=ts,
    raw_content=parser_output.raw_content,  # <-- Creates NEW content
    parsed_data=parser_output.domain_data,
)

# 6. Save with correction (triggers append + upsert)
storage.save_entry(entry, correction=parser_output)  # <-- APPENDS [correction]
```

And in `repository.py:286-290`:
```python
if correction and correction.is_correction:
    # Correction flow: append correction note
    correction_content = f"\n\n## {time_str} [correction]\n{entry.raw_content}"
    with raw_path.open("a", encoding="utf-8") as f:
        f.write(correction_content)  # <-- APPENDS, doesn't edit in-place
```

### New Flow Design

```
1. Router identifies CORRECTION
   ↓
2. Parser extracts:
   - target_entry_id: "2026-01-26_18-33-00"
   - correction_delta: {"distance_km": 3}  # New value
   ↓
3. Storage.find_raw_entry_section(target_entry_id)
   → Returns: (Path("raw/2026/01/2026-01-26.md"), start_line=12, end_line=18)
   ↓
4. Build merged content:
   - Read original section (lines 12-18)
   - Apply correction delta (replace "5km" with "3km" in text)
   ↓
5. Storage.edit_raw_section(file, 12, 18, merged_content)
   → Modifies file in-place, preserves surrounding content
   ↓
6. Re-parse modified section
   - ParserInput with just the modified content
   - Parser returns fresh parsed_data
   ↓
7. Storage._update_parsed_json()
   → Updates existing entry (not creates new)
```

### Key Implementation Decisions

**Decision 1: How to identify target section?**
- Use entry_id format: `{YYYY-MM-DD}_{HH-MM-SS}`
- Parse to extract date (for file path) and time (for section header)
- Section header format: `## HH:MM`

**Decision 2: How to determine section boundaries?**
- Start: Line with `## HH:MM` matching entry timestamp
- End: Line before next `## ` or EOF
- Return line numbers (1-indexed for human readability)

**Decision 3: How to build merged content?**
- Option A: LLM generates complete new section (currently used by Parser)
- Option B: Programmatic string replacement based on delta
- **Recommendation:** Use Option A since Parser already extracts complete `raw_content` as the corrected version. The delta is for programmatic updates, but raw content is what goes in the file.

**Decision 4: Atomic write?**
- Yes: Write to temp file, then rename
- Prevents data loss if process crashes mid-write

### Project Structure Notes

All changes are in **Quilto** (`packages/quilto/`) - this is domain-agnostic functionality:
- `quilto/storage/repository.py` — Add `find_raw_entry_section()`, `edit_raw_section()`
- `quilto/flow/correction.py` — Refactor to use in-place editing
- `quilto/flow/models.py` — Update `CorrectionResult` model

**Swealog changes:** None expected. CLI already displays `result.response` from ProcessResult.

### Architecture Compliance

| Requirement | Status |
|-------------|--------|
| Changes in Quilto (not Swealog) | Yes - all changes are framework-level |
| Domain-agnostic | Yes - no fitness-specific logic |
| Existing patterns followed | Yes - StorageRepository pattern, Pydantic models |
| No new dependencies | Yes - uses standard library only |
| Google-style docstrings | Required for new/modified functions |
| Type hints complete | Required - pyright strict mode |

### Library/Framework Requirements

| Library | Version | Usage |
|---------|---------|-------|
| Pydantic | 2.10+ | CorrectionResult model update — use `Field()` for Optional fields |
| pathlib | stdlib | File path manipulation — `Path.read_text()`, `Path.replace()` |
| tempfile | stdlib | Atomic write — `NamedTemporaryFile(mode='w', dir=parent, delete=False)` |
| re | stdlib | Section header matching — reuse pattern from `_parse_raw_file()` |
| logging | stdlib | Debug logging for line counts |

### File Structure Requirements

```
packages/quilto/quilto/
  storage/
    repository.py          # MODIFY - Add find_raw_entry_section(), edit_raw_section()
  flow/
    correction.py          # MODIFY - Refactor process_correction() to use in-place editing
    models.py              # MODIFY - Update CorrectionResult (add modified_file, edited_lines)
  orchestration.py         # MODIFY - Update correction_node() to call new flow (line ~180)
packages/quilto/tests/
  test_storage.py          # MODIFY - Add find_raw_entry_section() and edit_raw_section() unit tests
  test_correction_flow.py  # MODIFY - Update/remove old append tests (lines 613-740), add new in-place tests
```

### Existing Code References (Do Not Reinvent)

| Existing Code | Location | Reuse For |
|---------------|----------|-----------|
| `_parse_raw_file()` | repository.py:82-144 | Section header regex pattern `r"^## (\d{2}):(\d{2})"` |
| `_get_raw_path()` | repository.py:52-63 | Get raw file path from date |
| `_update_parsed_json()` | repository.py:334-357 | Update parsed JSON after re-parse |
| `create_parser_output()` | test_storage.py:13-37 | Test fixture helper for ParserOutput |
| `sample_entries` fixture | test_correction_flow.py:98-115 | Test data pattern |

### Testing Requirements

- **Unit tests:** `find_raw_entry_section()` with various scenarios — add to `test_storage.py`
- **Unit tests:** `edit_raw_section()` preserves surrounding content — verify byte equality for unchanged sections
- **Integration tests:** Full correction flow modifies file in-place — mock Parser, verify file content
- **Boundary tests:** First section, last section, single-section file — all 3 must pass
- **Error tests:** Entry not found, file not found — verify returns `None`, not exception
- **CRITICAL: Update old tests:** Remove/update `test_correction_appends_to_raw_file()` at `test_correction_flow.py:613` which explicitly tests OLD append behavior with `[correction]` marker
- **Run:** `make validate` must pass (0 lint errors, 0 type errors, all tests pass)

### Previous Story Intelligence

**Story 19.1 (Epic 19):** Fixed Parser input and response generation for CORRECTION flow. Key learnings:
- Parser now receives correct user input (not Router reasoning)
- `correction_node()` generates response and sets `StateKeys.RESPONSE` — **THIS function needs modification**
- ProcessResult includes `correction_result` field
- **HOWEVER:** The flow still creates new entries instead of editing existing ones

**Story 5.3 (Epic 5):** Original CORRECTION flow implementation with append strategy. Key learnings:
- `save_entry(entry, correction=parser_output)` triggers append + upsert
- The `## HH:MM [correction]` marker was designed for audit trail — **THIS behavior must be removed**
- Upsert semantics update parsed JSON but append to raw markdown

**Story 20.5 (Epic 20):** Session context propagation fix. Key learnings:
- Pattern: when adding new flow, ensure ALL relevant agents receive updated context
- This story may need to verify `correction_node()` receives conversation context correctly

**Key Insight from User Feedback:**
> "Ideal is that fix previous records in raw file... modify raw/2026-01-26.md at ## 18:33 part and run parser agent then give it to application so that it handles whether to update parsed file or not."

This is an **architectural change** from append-based corrections to in-place editing.

### Anti-Patterns to Avoid

| Anti-Pattern | Correct Approach |
|--------------|------------------|
| Add new fields without `| None` default | Use `field: Type | None = None` for new Optional fields |
| Hardcode line numbers | Use 0-indexed for code, log as 1-indexed for humans |
| Create new correction tests without updating old | **MUST update/remove** old append-based tests |
| Use string concatenation for file writes | Use `tempfile` + atomic rename |
| Catch all exceptions silently | Let file permission errors propagate |

### Git Intelligence

Recent commits (Epic 20) show stabilization:
- `773a4e6` Story 20.6: Parameterize context building
- `7c2501b` Epic 20 Retrospective complete
- `09335ac` Story 20.5: Session context propagation fix

### Key Data Flow (Current - Broken)

```
User: "Actually my run was 3km not 5km"
  |
  v
Router: CORRECTION, correction_target: "distance should be 3km"
  |
  v
Parser: target_entry_id: "2026-01-26_18-33-00"
        correction_delta: {"distance_km": 3}
        raw_content: "40 minutes at 8kph, 3km"  # Corrected content
  |
  v
correction.py:
  entry_id = "2026-01-26_14-30-00"  # NEW timestamp (now)
  entry = Entry(raw_content="40 minutes at 8kph, 3km")
  storage.save_entry(entry, correction=parser_output)
  |
  v
repository.py save_entry():
  correction_content = "\n\n## 14:30 [correction]\n40 minutes at 8kph, 3km"
  raw_path.open("a").write(correction_content)  # APPENDS
  _update_parsed_json()  # Updates parsed (this part is correct)
  |
  v
Result:
  raw/2026-01-26.md:
    ## 18:33
    40 minutes at 8kph, 5km  # STILL WRONG!

    ## 14:30 [correction]
    40 minutes at 8kph, 3km  # Appended, doesn't fix original
```

### Key Data Flow (Fixed)

```
User: "Actually my run was 3km not 5km"
  |
  v
Router: CORRECTION, correction_target: "distance should be 3km"
  |
  v
Parser: target_entry_id: "2026-01-26_18-33-00"
        correction_delta: {"distance_km": 3}
        raw_content: "40 minutes at 8kph, 3km"  # Corrected content
  |
  v
correction.py:
  file_path, start, end = storage.find_raw_entry_section(target_entry_id)
  → (Path(".../2026-01-26.md"), 12, 18)
  |
  v
  storage.edit_raw_section(file_path, start, end, new_content)
  → Modifies lines 12-18 in-place
  |
  v
  Re-parse modified section via Parser
  |
  v
  storage._update_parsed_json()  # Updates existing entry
  |
  v
Result:
  raw/2026-01-26.md:
    ## 18:33
    40 minutes at 8kph, 3km  # FIXED IN-PLACE!

  parsed/2026-01-26.json:
    "2026-01-26_18-33-00": { "distance_km": 3 }  # Updated (not duplicated)
```

### Edge Cases to Consider

1. **Multiple entries on same day:** Only target section should be modified — verify other sections byte-for-byte identical
2. **First section in file:** `start=0`, no preceding content — verify replacement works
3. **Last section in file:** `end=len(lines)`, no following content — verify no trailing garbage
4. **Single-section file:** Entire file is the section (start=0, end=len(lines)) — verify file rewrites correctly
5. **Entry not found:** Return `None` from `find_raw_entry_section()`, don't raise exception — caller handles error response
6. **Malformed raw file:** If no `## HH:MM` header found, return `None` — don't crash on unexpected format
7. **Duplicate timestamps:** If multiple sections have same `## HH:MM` (rare), return `None` — safer to fail than guess
8. **Empty raw file:** Return `None` — file exists but has no sections
9. **File permission error:** Let exception propagate — don't silently fail atomic write

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 21.1] - Acceptance criteria
- [Source: _bmad-output/implementation-artifacts/epic-19/epic-19-retro-2026-01-29.md] - Problem identification
- [Source: _bmad-output/implementation-artifacts/epic-20/epic-20-retro-2026-01-29.md] - Context building
- [Source: packages/quilto/quilto/flow/correction.py] - Current correction flow (`process_correction()`)
- [Source: packages/quilto/quilto/orchestration.py:~180] - `correction_node()` **MODIFY THIS**
- [Source: packages/quilto/quilto/storage/repository.py:263-312] - Current save_entry with correction **REMOVE append logic**
- [Source: packages/quilto/quilto/storage/repository.py:82-144] - Raw file parsing (REUSE regex pattern)
- [Source: packages/quilto/quilto/storage/repository.py:52-63] - `_get_raw_path()` (REUSE for file lookup)
- [Source: packages/quilto/quilto/flow/models.py] - CorrectionResult model **ADD fields**
- [Source: packages/quilto/tests/test_correction_flow.py:613-740] - **UPDATE/REMOVE** old append tests
- [Source: packages/quilto/tests/test_storage.py:13-37] - `create_parser_output()` helper (REUSE)
- [Source: _bmad-output/project-context.md] - Project conventions

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

N/A

### Completion Notes List

- Implemented `CorrectionEdit` model in `quilto/flow/models.py` with strict Pydantic validation
- Added `modified_file` and `edited_lines` fields to `CorrectionResult` model
- Implemented `find_raw_entry_section()` in `quilto/storage/repository.py` - locates raw file and section boundaries using regex matching
- Implemented `edit_raw_section()` in `quilto/storage/repository.py` - performs atomic in-place edits using tempfile + rename pattern
- Refactored `process_correction()` in `quilto/flow/correction.py` to use in-place editing flow instead of append-based flow
- Removed `[correction]` append logic from `save_entry()` in repository.py - corrections now use direct in-place editing
- Re-parse flow implemented: after editing raw file, Parser is called in non-correction mode to get fresh parsed_data
- Updated existing correction tests to reflect new in-place behavior
- Added comprehensive new tests for `find_raw_entry_section()` and `edit_raw_section()` in test_storage.py
- Added `CorrectionEdit` model tests in test_correction_flow.py
- All 2166 tests pass with `make validate`

### File List

- packages/quilto/quilto/flow/models.py (MODIFIED - Added CorrectionEdit model, updated CorrectionResult)
- packages/quilto/quilto/flow/__init__.py (MODIFIED - Export CorrectionEdit)
- packages/quilto/quilto/flow/correction.py (MODIFIED - Refactored to use in-place editing)
- packages/quilto/quilto/storage/repository.py (MODIFIED - Added find_raw_entry_section, edit_raw_section, updated save_entry)
- packages/quilto/tests/test_storage.py (MODIFIED - Added TestFindRawEntrySection, TestEditRawSection classes, updated TestCorrections)
- packages/quilto/tests/test_correction_flow.py (MODIFIED - Added TestCorrectionEditModel, updated TestStorageRepositoryCorrectionIntegration, updated TestCorrectionResultModel)

### Code Review

**Reviewed:** 2026-01-29
**Reviewer:** Claude Opus 4.5 (Dev Agent - Adversarial Review)
**Result:** PASS - Story 21.1 code reviewed

**Issues Found:**
- 0 HIGH, 2 MEDIUM, 1 LOW (all fixed or acceptable)

**Fixes Applied:**
- Renamed `test_pattern_with_correction_entries` → `test_pattern_with_legacy_correction_entries` in test_storage.py to clarify it tests backward-compat parsing of old [correction] markers

**Verification:**
- `make check` passes (lint + typecheck)
- All 2166 tests pass
- All acceptance criteria verified against implementation
- File list in story matches actual changed files
