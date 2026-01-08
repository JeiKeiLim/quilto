# Test Corpus

Test data for Quilto/Swealog parser accuracy and query validation.

## Structure

```
corpus/
├── schemas/                     # Domain schema definitions (YAML)
│   ├── fitness.yaml
│   ├── wellness.yaml
│   └── tasks.yaml
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
│   ├── edge_cases/              # Typos, minimal, verbose, malformed
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

**Tertiary (volume only):** `synthetic/` entries
- For stress testing, NOT for accuracy metrics

| Metric | Calculation |
|--------|-------------|
| Field-level F1 | Per-field (exercise, weight, reps, sets) |
| Exact match | Full ParserOutput matches expected |
| Domain detection | Correct domains identified |

## Adding New Domains

1. Create `corpus/{domain}/` directory
2. Add `schemas/{domain}.yaml` with field definitions
3. Add entries to `{domain}/entries/human/`
4. Generate expected outputs in `{domain}/expected/parser/`
