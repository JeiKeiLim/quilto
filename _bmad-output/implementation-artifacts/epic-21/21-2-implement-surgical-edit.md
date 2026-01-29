# Story 21.2: Implement Surgical Edit (Preserve Surrounding Content)

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **Swealog user**,
I want **corrections to only modify the relevant section**,
so that **other log entries in the same file are preserved**.

## Acceptance Criteria

1. **Given** raw file with multiple sections
   **When** correction targets one section
   **Then** only that section is modified

2. **Given** correction edit
   **When** applied
   **Then** surrounding markdown structure is preserved (headers, formatting)

3. **Given** section boundaries
   **When** edit is applied
   **Then** content before and after target section is unchanged

4. **Given** a surgical edit operation
   **When** completed successfully
   **Then** the byte content of lines[:start] and lines[end:] is identical to original

## Tasks / Subtasks

- [x] Task 1: Verify Story 21.1 surgical edit implementation (AC: #1, #2, #3)
  - [x] 1.1: Read `packages/quilto/quilto/storage/repository.py:476-575` and confirm `lines[:start] + new_lines + lines[end:]` pattern at line 540
  - [x] 1.2: Run `uv run pytest packages/quilto/tests/test_storage.py::TestEditRawSection -v` — all 10 tests must pass
  - [x] 1.3: Add inline comment to story Dev Notes confirming surgical edit is complete (no production code changes needed)

- [x] Task 2: Add byte-level verification tests in `TestEditRawSection` class (AC: #4)
  - [x] 2.1: Add `test_edit_preserves_surrounding_bytes_exact(self, tmp_path: Path)` — capture `"".join(lines[:start])` before edit, compare byte-for-byte after
  - [x] 2.2: Add `test_edit_preserves_trailing_bytes_exact(self, tmp_path: Path)` — capture `"".join(lines[end:])` before edit, compare byte-for-byte after
  - [x] 2.3: Add `test_edit_preserves_multibyte_utf8_exact(self, tmp_path: Path)` — use Korean (한글), Chinese (中文), emoji (🏃) in surrounding content

- [x] Task 3: Add markdown structure preservation tests in `TestEditRawSection` (AC: #2)
  - [x] 3.1: Add `test_edit_preserves_other_section_headers(self, tmp_path: Path)` — assert exact header strings `## 08:00` and `## 18:00` remain after editing middle section
  - [x] 3.2: Add `test_edit_preserves_blank_lines_between_sections(self, tmp_path: Path)` — count `\n\n` patterns before/after, must be equal

- [x] Task 4: Add integration test in `TestStorageRepositoryCorrectionIntegration` class (AC: #1-#4)
  - [x] 4.1: Add `test_surgical_edit_preserves_surrounding_content_integration` in `packages/quilto/tests/test_correction_flow.py`
    - Create raw file with 3 sections: `## 08:00`, `## 12:00`, `## 18:00`
    - Call `storage.edit_raw_section()` on middle section (12:00)
    - Assert `content_before_edit[:section1_end] == content_after_edit[:section1_end]` (byte-identical)
    - Assert `content_before_edit[section3_start:] == content_after_edit[section3_start:]` (byte-identical)

- [x] Task 5: Run validation (AC: #1-#4)
  - [x] 5.1: `uv run ruff check . && uv run pyright` — 0 errors
  - [x] 5.2: `uv run pytest packages/quilto/tests/test_storage.py::TestEditRawSection -v` — all tests pass
  - [x] 5.3: `uv run pytest packages/quilto/tests/test_correction_flow.py::TestStorageRepositoryCorrectionIntegration -v` — integration test passes

## Dev Notes

### Story Scope: TEST-ONLY (No Production Code Changes)

Story 21.1 implemented surgical edit in `edit_raw_section()` at `repository.py:540`:
```python
modified_lines = lines[:start] + new_lines + lines[end:]  # Surgical edit
```

This story adds **explicit byte-level verification tests** to prove surrounding content is byte-identical (not just "present").

### Existing Tests (10 tests in `TestEditRawSection`)

| Test | What It Verifies | Gap |
|------|------------------|-----|
| `test_edit_preserves_surrounding_content` | Substring assertions | Not byte-exact |
| `test_edit_first_section` | start=0 works | OK |
| `test_edit_last_section` | end=len(lines) works | OK |
| `test_edit_single_section_file` | Full file replace | OK |
| `test_edit_preserves_utf8_encoding` | Korean preserved | Not multi-byte exact |
| `test_atomic_write_safety` | No corruption | OK |

**Gap to Fill:** Tests use `in` operator, not `==` byte comparison.

### Test Implementation Guide

**Location:** `packages/quilto/tests/test_storage.py` in `TestEditRawSection` class (line ~628)

**Test 1: Byte-exact leading content**
```python
def test_edit_preserves_surrounding_bytes_exact(self, tmp_path: Path) -> None:
    """Verify lines[:start] is byte-identical after edit."""
    repo = StorageRepository(tmp_path)
    raw_dir = tmp_path / "raw" / "2026" / "01"
    raw_dir.mkdir(parents=True)
    content = "## 08:00\nMorning run 5km\n\n## 12:00\nLunch gym\n\n## 18:00\nEvening yoga\n"
    file_path = raw_dir / "2026-01-26.md"
    file_path.write_text(content, encoding="utf-8")

    lines_before = content.splitlines(keepends=True)
    leading_bytes_before = "".join(lines_before[:4]).encode("utf-8")  # Lines 0-3

    repo.edit_raw_section(file_path, start=4, end=7, new_content="## 12:00\nCorrected lunch\n")

    modified = file_path.read_text(encoding="utf-8")
    lines_after = modified.splitlines(keepends=True)
    leading_bytes_after = "".join(lines_after[:4]).encode("utf-8")

    assert leading_bytes_before == leading_bytes_after
```

**Test 2: Byte-exact trailing content**
```python
def test_edit_preserves_trailing_bytes_exact(self, tmp_path: Path) -> None:
    """Verify lines[end:] is byte-identical after edit."""
    # Same setup, assert trailing bytes match
```

**Test 3: Multi-byte UTF-8**
```python
def test_edit_preserves_multibyte_utf8_exact(self, tmp_path: Path) -> None:
    """Verify Korean/Chinese/emoji in surrounding content preserved."""
    content = "## 08:00\n한글 운동 🏃\n\n## 12:00\nTarget\n\n## 18:00\n中文晚餐\n"
    # Edit middle, verify 한글 and 中文 byte-identical
```

**Integration Test Location:** `packages/quilto/tests/test_correction_flow.py` in `TestStorageRepositoryCorrectionIntegration` class

### Anti-Patterns to Avoid

| Anti-Pattern | Correct Approach |
|--------------|------------------|
| `"Morning workout" in modified` | `leading_before == leading_after` (byte-exact) |
| `assert modified.count("\n\n")` | `assert blank_before == blank_after` (count match) |
| Add production code | **TEST-ONLY STORY** |
| New test file | Add to existing `TestEditRawSection` class |

### File Changes Summary

| File | Action | Class/Location |
|------|--------|----------------|
| `packages/quilto/tests/test_storage.py` | ADD 4 tests | `TestEditRawSection` (line ~628) |
| `packages/quilto/tests/test_correction_flow.py` | ADD 1 test | `TestStorageRepositoryCorrectionIntegration` |

**Total: 5 new tests, 0 production files changed.**

### References

| Document | Line/Section | Purpose |
|----------|--------------|---------|
| `epics.md` | Story 21.2 (line ~3579) | Acceptance criteria source |
| `21-1-*.md` | Dev Agent Record | Previous story learnings |
| `repository.py` | Line 540 | Surgical edit: `lines[:start] + new_lines + lines[end:]` |
| `test_storage.py` | Line 628-787 | `TestEditRawSection` class (ADD tests here) |
| `test_correction_flow.py` | `TestStorageRepositoryCorrectionIntegration` | ADD integration test |

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

### Completion Notes List

- **Task 1 Verified:** Surgical edit at `repository.py:540` confirmed: `lines[:start] + new_lines + lines[end:]` pattern. 9 existing tests pass in `TestEditRawSection`.
- **Task 2 Complete:** Added 3 byte-level verification tests: `test_edit_preserves_surrounding_bytes_exact`, `test_edit_preserves_trailing_bytes_exact`, `test_edit_preserves_multibyte_utf8_exact`.
- **Task 3 Complete:** Added 2 markdown structure tests: `test_edit_preserves_other_section_headers`, `test_edit_preserves_blank_lines_between_sections`.
- **Task 4 Complete:** Added integration test `test_surgical_edit_preserves_surrounding_content_integration` in `test_correction_flow.py`.
- **Task 5 Complete:** Validation passed - 0 lint/type errors, 14 `TestEditRawSection` tests pass (9 existing + 5 new), 5 integration tests pass.

### Senior Developer Review (AI)

**Reviewer:** Claude Opus 4.5 | **Date:** 2026-01-29

**Issues Found & Fixed:**

| ID | Severity | Issue | Resolution |
|----|----------|-------|------------|
| H2 | HIGH | `test_edit_preserves_trailing_bytes_exact` used hardcoded indices brittle to line count changes | Refactored to use content-based marker matching (`"## 18:00"` marker) |
| H3 | HIGH | `test_edit_preserves_blank_lines_between_sections` didn't verify surrounding blank lines - counted total including replaced content | Refactored to verify surrounding sections explicitly preserve blank line structure |
| M1 | MEDIUM | Integration test had same brittleness as H2 | Refactored to use content-based marker matching |
| M2 | MEDIUM | sprint-status.yaml modified but not in File List | Added to File List |

**Outcome:** APPROVED - All HIGH/MEDIUM issues fixed. Tests now robust to replacement line count variations.

### File List

- `packages/quilto/tests/test_storage.py` - Added 5 tests to `TestEditRawSection` class (total 14 tests now)
- `packages/quilto/tests/test_correction_flow.py` - Added 1 integration test to `TestStorageRepositoryCorrectionIntegration` class
- `_bmad-output/implementation-artifacts/sprint-status.yaml` - Story status updated

