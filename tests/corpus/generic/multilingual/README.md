# Multilingual Test Corpus

Domain-agnostic multilingual test entries for validating Quilto Parser's handling of language variations, number formats, and date formats.

## Purpose

Tests Parser robustness with **valid** multilingual content (NOT malformed input like edge cases). Covers:

- Pure English and pure Korean entries
- Korean-English code-switching patterns
- Number format variations (US, European, Korean)
- Date format variations (ISO, US, European, Korean)

## Categories

| Category | Pattern | Count | Purpose |
|----------|---------|-------|---------|
| lang | `multi-lang-*.md` | 4 | Pure single-language entries |
| mixed | `multi-mixed-*.md` | 4 | Korean-English code-switching |
| number | `multi-number-*.md` | 4 | Number format variations |
| date | `multi-date-*.md` | 5 | Date format variations |

**Total: 17 entries**

## Entry Content

All entries are **domain-agnostic** (NOT fitness-specific):

- Journal/diary entries
- Cooking/recipe notes
- Study/learning logs
- Meeting notes
- Shopping/expense notes

## Expected Output Schema

Uses `MultilingualExpectedOutput` from `tests/corpus/schemas/multilingual_schema.py`:

```json
{
  "language_detected": ["ko", "en"],
  "extracted_text": "Normalized text content",
  "numbers_detected": [{"original": "1,000", "normalized": "1000"}],
  "dates_detected": [{"original": "2026년 1월 9일", "normalized": "2026-01-09"}],
  "category": "mixed"
}
```

## Language Detection

- `"en"` - English content
- `"ko"` - Korean content
- For mixed content, list both: `["ko", "en"]`

## Running Tests

```bash
uv run pytest tests/corpus/test_multilingual.py -v
```

## File Structure

```
multilingual/
├── README.md
├── expected/                    # Expected output JSONs
│   ├── multi-lang-01.json
│   ├── multi-lang-02.json
│   └── ...
├── multi-lang-01.md            # Pure English
├── multi-lang-02.md            # Pure Korean
├── multi-mixed-01.md           # Code-switching
├── multi-number-01.md          # Number formats
├── multi-date-01.md            # Date formats
└── ...
```
