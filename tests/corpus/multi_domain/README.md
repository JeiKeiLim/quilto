# Multi-Domain Test Entries

Domain-agnostic test entries proving Quilto handles ANY domain, not just fitness.

## Purpose

These entries validate that Quilto's Parser agent works correctly with non-fitness domains:
- **Journal** - Personal diary/mood entries
- **Cooking** - Recipe and cooking logs
- **Study** - Learning notes and progress

## Directory Structure

```
multi_domain/
├── README.md                   # This file
├── entries/
│   ├── journal/               # Personal diary entries
│   │   ├── journal-01.md to journal-06.md       (standard)
│   │   ├── journal-minimal-01.md, -02.md        (brief)
│   │   ├── journal-verbose-01.md, -02.md        (detailed)
│   │   └── journal-mixed-01.md, -02.md          (KO-EN mixed)
│   │
│   ├── cooking/               # Recipe/cooking logs
│   │   ├── cooking-01.md to cooking-06.md       (standard)
│   │   ├── cooking-minimal-01.md, -02.md        (brief)
│   │   ├── cooking-verbose-01.md, -02.md        (detailed)
│   │   └── cooking-mixed-01.md, -02.md          (KO-EN mixed)
│   │
│   └── study/                 # Learning notes
│       ├── study-01.md to study-06.md           (standard)
│       ├── study-minimal-01.md, -02.md          (brief)
│       ├── study-verbose-01.md, -02.md          (detailed)
│       └── study-mixed-01.md, -02.md            (KO-EN mixed)
│
└── expected/                   # Expected Parser outputs (Story 1.5-4)
    └── parser/                # Parser output expectations (TBD)
```

## Entry Categories

| Category | Pattern | Per Domain | Description |
|----------|---------|------------|-------------|
| standard | `{domain}-NN.md` | 6 | Normal complexity entries |
| minimal | `{domain}-minimal-NN.md` | 2 | Very brief notes |
| verbose | `{domain}-verbose-NN.md` | 2 | Detailed/elaborate entries |
| mixed | `{domain}-mixed-NN.md` | 2 | Korean-English code-switching |

**Per domain:** 12 entries
**Total:** 36 entries across 3 domains

## Domain Content

### Journal Entries
- Emotional state/mood indicators
- Daily activities and reflections
- Time references (morning, afternoon, etc.)
- Personal observations

### Cooking Entries
- Dish name or description
- Ingredients with quantities
- Cooking time/duration
- Quality notes

### Study Entries
- Subject/topic studied
- Duration or time spent
- Comprehension notes
- Next steps or follow-up items

## Usage

These entries are INPUT data for Parser validation. Expected outputs (schemas, JSON expectations) will be added to `expected/parser/` in Story 1.5-4.

## Related

- `tests/corpus/generic/multilingual/` - Language variation tests
- `tests/corpus/generic/edge_cases/` - Edge case robustness tests
- Story 1.5-4 will add expected output schemas
