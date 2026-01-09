# Test Corpus

Test data for Quilto/Swealog parser accuracy and query validation.

## Structure

```
corpus/
├── schemas/                     # Test validation schemas (Python)
│   ├── __init__.py              # Package exports
│   └── expected_output.py       # ExpectedParserOutput, is_synthetic()
│
├── fitness/                     # Fitness domain test set
│   ├── ground_truth/
│   │   └── strong_workouts.csv  # Original structured data (gold standard)
│   ├── entries/
│   │   ├── from_csv/            # Synthesized from CSV (93 files) - verifiable
│   │   ├── human/               # Real human-written notes (future)
│   │   └── synthetic/           # Pure LLM-generated, human-validated
│   └── expected/
│       ├── parser/              # Expected ParserOutput JSON
│       ├── query/               # Expected query responses
│       └── retrieval/           # Expected retrieval results
│
├── multi_domain/                # Cross-domain test cases
│   ├── entries/
│   └── expected/parser/
│
├── generic/                     # Domain-agnostic tests
│   ├── edge_cases/              # Empty, unicode, length, markdown, injection
│   │   ├── expected/            # EdgeCaseExpectedOutput JSON files
│   │   └── edge-*.md            # 20+ edge case entries
│   └── multilingual/            # Korean, English, mixed
│
└── variation_rules/             # Human-provided synthesis instructions
    ├── SYNTHESIS_RULES.md       # Original synthesis documentation
    ├── writing_styles.yaml      # Rushed, detailed, mixed patterns
    ├── typos.yaml               # Common typos, abbreviations
    └── edge_patterns.yaml       # Edge cases to generate
```

## Data Sources

| Source | Location | Purpose |
|--------|----------|---------|
| Strong CSV | `fitness/ground_truth/` | Gold standard structured data |
| From CSV | `*/entries/from_csv/` | Synthesized from CSV - **verifiable expected output** |
| Human entries | `*/entries/human/` | Real user writing patterns (future) |
| Synthetic | `*/entries/synthetic/` | Pure LLM-generated, human-validated |

## Accuracy Metrics

**Primary accuracy source:** `from_csv/` entries (93 files)
- Expected output derived from `strong_workouts.csv` ground truth
- No LLM circular validation - real structured data as reference

**Secondary (when available):** `human/` entries
- Real user writing patterns expose LLM blind spots

**Robustness testing (NOT for accuracy):** `synthetic/` entries (50+ files)
- Human-created entries with controlled variations
- Tests parser robustness with edge cases, typos, multilingual input
- **Excluded from primary accuracy metrics** via `is_synthetic()` function

| Metric | Calculation |
|--------|-------------|
| Field-level F1 | Per-field (exercise, weight, reps, sets) |
| Exact match | Full ParserOutput matches expected |
| Domain detection | Correct domains identified |

## Synthetic Entries

Synthetic entries are human-created test cases designed to test parser robustness with edge cases. They are stored in `fitness/entries/synthetic/` and have corresponding expected outputs in `fitness/expected/parser/synthetic/`.

### Categories

| Category | Count | Purpose |
|----------|-------|---------|
| typo | 10 | Korean/English typos, spacing issues, spelled-out numbers |
| minimal | 10 | Ultra-short entries (single exercise, one set) |
| verbose | 10 | Long narratives with feelings, supersets, multiple exercises |
| multilingual | 10 | Pure English, mixed Korean/English |
| multi_domain | 10 | Multiple exercises, strength + cardio references |

### Entry Format

Each synthetic entry has YAML frontmatter:

```yaml
---
category: typo | minimal | verbose | multilingual | multi_domain
difficulty: easy | medium | hard
exercises: ["Exercise Name 1", "Exercise Name 2"]
notes: "What edge case this tests"
validated_by: human  # REQUIRED
---
Entry content here...
```

### Expected Output Format

Expected outputs use `ExpectedParserOutput` schema with `date: "synthetic"`:

```json
{
  "activity_type": "workout",
  "exercises": [...],
  "date": "synthetic"
}
```

### Validation Script

Validate synthetic entries:

```bash
# Validate all entries
uv run scripts/generate_synthetic_entries.py validate

# Show statistics
uv run scripts/generate_synthetic_entries.py stats

# List unvalidated entries
uv run scripts/generate_synthetic_entries.py list-unvalidated
```

### Important Notes

1. **Synthetic entries are human-created**, not LLM-generated - prevents circular validation
2. **Expected outputs are human-validated** - derived from entry content by human review
3. **date field is "synthetic"** - distinguishes from real entries with actual dates
4. **Use `is_synthetic()` function** (from `tests/corpus/schemas/expected_output.py`) to exclude synthetic entries from Story 1.7 primary accuracy metrics

## Edge Case Test Entries

Domain-agnostic edge case entries for validating Quilto Parser robustness. Located in `generic/edge_cases/`.

### Categories

| Category | Pattern | Count | Purpose |
|----------|---------|-------|---------|
| empty | `edge-empty-*.md` | 5 | Empty, whitespace, non-breaking spaces |
| unicode | `edge-unicode-*.md` | 5 | Emoji, RTL, special chars, zero-width |
| length | `edge-length-*.md` | 4 | Single char to 10,000+ chars |
| markdown | `edge-markdown-*.md` | 4 | Unclosed blocks, deep nesting, broken links |
| injection | `edge-injection-*.md` | 4 | SQL-like, prompt injection, HTML, path traversal |

### Schema

Edge case expected outputs use `EdgeCaseExpectedOutput` from `tests/corpus/schemas/edge_case_schema.py`:

```json
{
  "parseable": false,
  "reason": "empty_or_whitespace",
  "extracted_text": null,
  "warnings": [],
  "category": "empty"
}
```

### Running Edge Case Tests

```bash
uv run pytest tests/corpus/test_edge_cases.py -v
```

## Adding New Domains

1. Create `corpus/{domain}/` directory
2. Add `schemas/{domain}.yaml` with field definitions
3. Add entries to `{domain}/entries/human/`
4. Generate expected outputs in `{domain}/expected/parser/`
