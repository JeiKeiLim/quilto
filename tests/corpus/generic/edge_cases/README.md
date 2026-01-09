# Edge Case Test Entries

Domain-agnostic edge case test entries for validating Quilto Parser robustness.

## Purpose

These entries test how the Parser handles problematic inputs that could occur in ANY domain:
- Empty or whitespace-only content
- Unicode edge cases (emoji, RTL, special characters)
- Extremely long or short inputs
- Malformed markdown
- Injection attempt patterns

**Note:** These are NOT fitness-specific tests. They validate generic Parser behavior with invalid/edge inputs.

## Categories

| Category | Pattern | Description | Count |
|----------|---------|-------------|-------|
| empty | `edge-empty-*.md` | Empty, whitespace, non-breaking spaces | 5 |
| unicode | `edge-unicode-*.md` | Emoji, RTL, special chars, zero-width | 5 |
| length | `edge-length-*.md` | Single char to 10,000+ chars | 4 |
| markdown | `edge-markdown-*.md` | Unclosed blocks, deep nesting, broken links | 4 |
| injection | `edge-injection-*.md` | SQL-like, prompt injection, HTML, path traversal | 4 |

## File Structure

```
edge_cases/
├── README.md              # This file
├── expected/              # Expected output JSON files
│   └── edge-{category}-{nn}.json
├── edge-empty-01.md       # Empty file (0 bytes)
├── edge-empty-02.md       # Single space
├── edge-unicode-01.md     # Emoji only
├── edge-injection-01.md   # SQL-like patterns
└── ...
```

## Expected Output Schema

Each entry has a corresponding JSON in `expected/` using `EdgeCaseExpectedOutput`:

```json
{
  "parseable": false,
  "reason": "empty_or_whitespace",
  "extracted_text": null,
  "warnings": [],
  "category": "empty"
}
```

### Fields

| Field | Type | Description |
|-------|------|-------------|
| `parseable` | bool | Whether input could be parsed |
| `reason` | str \| null | Reason for parse failure |
| `extracted_text` | str \| null | Successfully extracted text |
| `warnings` | list[str] | Non-fatal warnings |
| `category` | str | One of: empty, unicode, length, markdown, injection |

## Expected Behavior

- **Empty/whitespace**: `parseable=false`, reason describes why
- **Unicode edge cases**: `parseable=true`, text extracted as-is with warnings
- **Length extremes**: `parseable=true`, may have truncation warnings
- **Malformed markdown**: `parseable=true`, best-effort extraction
- **Injection attempts**: `parseable=true`, treated as normal text (NOT executed)

## Running Tests

```bash
uv run pytest tests/corpus/test_edge_cases.py -v
```

## Schema Location

`tests/corpus/schemas/edge_case_schema.py`
