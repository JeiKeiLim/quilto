# Feedback Collection for Dogfooding Iterations

This directory contains user feedback collected during dogfooding sessions of the Swealog CLI.

## Dogfooding Iteration Cycle

```
┌─────────────────────────────────────────────────────────────┐
│                  Dogfooding Iteration                       │
├─────────────────────────────────────────────────────────────┤
│  1. User runs: swealog auto "..."                           │
│  2. Quilto generates response                               │
│  3. Swealog prompts: "How was this response?"               │
│  4. User provides natural language feedback                 │
│  5. System records: query + intermediate outputs + feedback │
│  6. Collect until sufficient dataset                        │
│  7. Analyze dataset → Generate improvement stories          │
│  8. Implement fixes                                         │
│  9. Archive iteration, start next cycle                     │
└─────────────────────────────────────────────────────────────┘
```

## Directory Structure

```
tests/eval/feedback/
├── active/                    # Current collection (commit these)
│   ├── .gitkeep
│   └── 2026-01-20_abc12345.json
├── archive/                   # Completed iterations (commit these)
│   ├── .gitkeep
│   ├── iter-001/
│   │   ├── records/           # Moved from active/
│   │   ├── analysis.md        # Findings and patterns
│   │   └── stories-generated.md
│   └── iter-002/
└── README.md                  # This file
```

## Feedback JSON Schema

Each feedback file contains:

```json
{
  "id": "2026-01-20_a1b2c3d4",
  "query": "What was my running pace last week?",
  "intermediate_outputs": {
    "router": { ... },
    "planner": { ... },
    "retriever": { ... },
    "analyzer": { ... },
    "synthesizer": { ... },
    "evaluator": { ... }
  },
  "final_response": "Based on your logs...",
  "user_feedback": "Retrieved wrong dates, showed this week instead of last week",
  "session": {
    "timestamp": "2026-01-20T15:30:45.123456",
    "input_type": "QUERY",
    "config_path": "llm-config.yaml",
    "storage_path": "logs/",
    "debug_enabled": true
  },
  "feedback_sentiment": null
}
```

### Field Descriptions

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique ID: `{YYYY-MM-DD}_{hash}` where hash is first 8 chars of SHA256(query) |
| `query` | string | Original user query text |
| `intermediate_outputs` | object | Agent outputs from each pipeline stage |
| `final_response` | string | The response shown to the user |
| `user_feedback` | string | User's feedback (empty string if skipped) |
| `session` | object | Session metadata (timestamp, input type, paths, debug flag) |
| `feedback_sentiment` | string\|null | Future: auto-classified sentiment |

### Input Types

- `LOG` - User logging data (no query, no feedback prompt)
- `QUERY` - User asking a question (triggers feedback prompt)
- `BOTH` - User logging data AND asking a question (triggers feedback prompt)
- `CORRECTION` - User correcting previous entry (no feedback prompt)

## Archive Process

When an iteration is complete:

1. Create new directory: `archive/iter-NNN/`
2. Create `records/` subdirectory
3. Move all files from `active/` to `archive/iter-NNN/records/`
4. Document findings in `archive/iter-NNN/analysis.md`
5. List generated stories in `archive/iter-NNN/stories-generated.md`
6. Commit the archive

## Analyzing Collected Feedback

### Manual Analysis

1. Read through feedback files in `active/`
2. Look for patterns:
   - Which query types get negative feedback?
   - Which intermediate step correlates with quality issues?
   - Are there domain-specific patterns?
3. Document findings in analysis.md

### Automated Analysis (Future)

- Sentiment classification via LLM
- Clustering similar issues
- Correlation with intermediate outputs

## Triggering Feedback Collection

Feedback is only collected when:
- `swealog auto` command is used
- `--debug` flag is active
- Flow is QUERY or BOTH (not LOG or CORRECTION)

Example:
```bash
swealog auto "What was my running pace last week?" --debug
```

After the response, you'll see:
```
How was this response? (press Enter to skip):
```

## Git Policy

- Feedback files in `active/` and `archive/` **should be committed**
- They are test artifacts that track dogfooding progress
- They help reproduce issues and validate fixes
