# Investigation Report: LOG Persistence Failure

**Story:** 23.1 - Investigate LOG Persistence Failure
**Date:** 2026-01-30
**Investigator:** Dev Agent (Claude Opus 4.5)

---

## Executive Summary

LOG entries are parsed correctly but never saved to storage. The root cause is a **missing storage call** in `parse_node()` function. CORRECTION flow works because it calls `storage.edit_raw_section()`, but LOG flow has no equivalent.

---

## Root Cause Analysis

### Primary Finding

**Location:** `packages/quilto/quilto/orchestration.py`

The `parse_node()` function (lines 942-998) parses input correctly but returns immediately without calling `storage.save_entry()`.

```
ACTUAL FLOW (BROKEN):
Router → parse_node() → observe_node() → END
              ↓
         Returns parsed_data
         (never calls save_entry)

EXPECTED FLOW:
Router → parse_node() → [SAVE TO STORAGE] → observe_node() → END
                              ↑
                         MISSING STEP
```

### Graph Definition

**Line 1374:**
```python
graph.add_edge("parse", "observe")
```

The graph goes directly from `parse` to `observe` with no save step in between.

### Evidence

1. **Grep search for `save_entry` in orchestration.py:** No matches found
2. **Test execution:**
   - Files before: 18 entries
   - Files after: 18 entries (unchanged)
   - No `2026-01-30.md` created despite "Logged entry successfully" message
3. **Parser output:** `{}` (empty dict - but this is a separate issue)

### Contrast with CORRECTION Flow

**CORRECTION works because:**
- `correction_node()` calls `process_correction()` (line 1042)
- `process_correction()` calls `storage.edit_raw_section()` (correction.py:151)
- `process_correction()` calls `storage._update_parsed_json()` (correction.py:177)

**LOG fails because:**
- `parse_node()` never calls any storage method
- No intermediate save step exists in the graph

---

## Affected Code Paths

| File | Lines | Issue |
|------|-------|-------|
| `packages/quilto/quilto/orchestration.py` | 942-998 | `parse_node()` never calls `save_entry()` |
| `packages/quilto/quilto/orchestration.py` | 1374 | Graph edge `parse → observe` with no save |

---

## Proposed Fix Location

**Option A (RECOMMENDED): Add save logic directly to `parse_node()`**

Location: `orchestration.py` line ~990 (after progress handler, before return)

```python
# After line 983 (after progress handler call)
# Add storage save logic:

from quilto.storage import Entry
from datetime import datetime, UTC
import uuid

entry = Entry(
    id=str(uuid.uuid4())[:8],
    date=datetime.now(UTC).date(),
    timestamp=datetime.now(UTC),
    raw_content=user_input,
    parsed_data=parser_output.domain_data,
)
quilto.storage.save_entry(entry)
```

**Rationale:**
- Matches pattern of `correction_node()` which handles storage directly
- Single location for LOG persistence
- No graph modification required
- Minimal code change

---

## Test Verification Strategy

### Unit Test
```python
# test_parse_node_saves_entry.py
async def test_parse_node_saves_entry():
    """Verify parse_node calls storage.save_entry()."""
    mock_storage = Mock()
    # ... setup
    await parse_node(state)
    mock_storage.save_entry.assert_called_once()
```

### Integration Test
```python
# test_log_creates_files.py
async def test_log_creates_raw_file():
    """Verify LOG input creates raw markdown file."""
    before = list(storage_path.glob("raw/**/*.md"))
    await session.process("I did 10 pushups", mode="log")
    after = list(storage_path.glob("raw/**/*.md"))
    assert len(after) > len(before)
```

### File Verification (Manual)
```bash
date_dir="logs/raw/$(date +%Y)/$(date +%m)"
before_count=$(ls -1 "$date_dir" 2>/dev/null | wc -l)
uv run swealog run --config ./llm-config-openai.yaml --storage ./logs --debug "I did 10 pushups"
after_count=$(ls -1 "$date_dir" 2>/dev/null | wc -l)
# after_count should be > before_count
```

---

## Architecture Compliance Impact

| Requirement | Status | Impact |
|-------------|--------|--------|
| FR-F2: Store raw notes | **BROKEN** | Raw markdown not saved for LOG |
| FR-F3: Parse structured data | **BROKEN** | Parsed JSON not saved for LOG |
| AR-1: Separate raw/parsed | N/A | Implementation exists, not called |
| AR-2: Directory structure | N/A | Path generation works correctly |

---

## Additional Finding: Parser Output Empty

During testing, Parser returned `{}` (empty dict). This may be a separate issue:

```
ℹ [Parser]
ℹ {}
```

The parser ran but produced no domain data. This could be:
1. Domain schema mismatch
2. LLM response parsing issue
3. Input format not recognized

**Recommendation:** Create follow-up story to investigate Parser empty output.

---

## Story 23.2 Fix Specification

### Required Changes

1. **File:** `packages/quilto/quilto/orchestration.py`
2. **Function:** `parse_node()` (lines 942-998)
3. **Location:** After line 983 (after progress handler), before return statement

### Code Change

```python
# Add import at top of file (if not present)
import uuid

# In parse_node(), after line 983, add:
from quilto.storage import Entry

entry = Entry(
    id=str(uuid.uuid4())[:8],
    date=datetime.now(UTC).date(),
    timestamp=datetime.now(UTC),
    raw_content=user_input,
    parsed_data=parser_output.domain_data,
)
quilto.storage.save_entry(entry)
```

### Tests to Add

1. `test_parse_node_calls_save_entry()` - Unit test with mocked storage
2. `test_log_input_creates_raw_file()` - Integration test
3. `test_log_input_creates_parsed_json()` - Integration test

### Acceptance Criteria

- [ ] LOG input creates `logs/raw/YYYY/MM/YYYY-MM-DD.md`
- [ ] LOG input creates/updates `logs/parsed/YYYY/MM/YYYY-MM-DD.json`
- [ ] Existing CORRECTION flow continues to work
- [ ] All tests pass including new persistence tests

---

## References

- [Source: `orchestration.py:942-998`, parse_node()]
- [Source: `orchestration.py:1374`, parse→observe edge]
- [Source: `correction.py:151`, storage.edit_raw_section()]
- [Source: `repository.py:264-307`, save_entry() implementation]
- [Source: `epic-22-retro-2026-01-30.md`, lines 57-75]
