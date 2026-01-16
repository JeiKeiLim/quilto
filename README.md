# Swealog

A fitness logging application powered by the Quilto agent framework. Log workouts in natural language and query your fitness data with AI-powered analysis.

## Overview

This workspace contains two packages:

| Package | Description |
|---------|-------------|
| **quilto** | Domain-agnostic agent framework for note processing |
| **swealog** | Fitness logging application built on Quilto |

**Quilto** provides the core agent pipeline (Router, Parser, Planner, Retriever, Analyzer, Synthesizer, Evaluator) while **Swealog** adds fitness-specific domains, vocabulary, and interfaces.

## Features

- Natural language fitness logging ("bench 185x5 felt heavy")
- AI-powered query analysis ("how has my bench progressed?")
- Multi-domain support: Strength, Running, Swimming, Nutrition, General Fitness
- Batch import from text/markdown files
- Local-first with Ollama (privacy-focused) or cloud LLM support
- CLI and REST API interfaces
- Automatic error cascade with graceful degradation

## Requirements

- Python 3.13+
- [uv](https://docs.astral.sh/uv/) package manager
- [Ollama](https://ollama.ai/) with `qwen2.5:7b` model (or cloud API key)

## Quick Start

```bash
# Install dependencies
uv sync

# Pull required Ollama model (if using local LLM)
ollama pull qwen2.5:7b

# Verify installation
uv run swealog --version
```

## CLI Usage

### Log a Fitness Entry

```bash
# Simple log
uv run swealog log "bench press 185x5 felt heavy"

# With custom config
uv run swealog log "ran 5k in 25:30" --config ./my-config.yaml

# With custom storage directory
uv run swealog log "swam 2000m freestyle" --storage ./my-logs
```

### Query Your Data

```bash
# Ask questions about your fitness data
uv run swealog ask "how has my bench press progressed?"

# Get running statistics
uv run swealog ask "what was my average pace last week?"

# Nutrition queries
uv run swealog ask "how many calories did I consume yesterday?"
```

### Batch Import

```bash
# Import from a single file
uv run swealog import ./workout-journal.txt

# Import from a directory (recursively finds .txt and .md files)
uv run swealog import ./logs/

# Dry run (preview without saving)
uv run swealog import ./logs/ --dry-run

# Verbose output
uv run swealog import ./logs/ --verbose
```

**Import file format:**
```
2024-01-15: Bench press 185x5, 185x5, 185x4. Felt strong today.
---
2024-01-16: Morning run 5k in 26:30. Easy pace, good weather.
---
2024-01-17: Swimming 2000m freestyle, 45 minutes.
```

Entries are separated by `---` or double newlines.

### Start API Server

```bash
# Start on default port (8000)
uv run swealog serve

# Custom host and port
uv run swealog serve --host 0.0.0.0 --port 3000

# With auto-reload for development
uv run swealog serve --reload
```

### CLI Options

| Option | Short | Description |
|--------|-------|-------------|
| `--config` | `-c` | Path to llm-config.yaml |
| `--storage` | `-s` | Path to storage directory (default: ./logs) |
| `--version` | `-v` | Show version |
| `--help` | | Show help |

## API Usage

### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| POST | `/input` | Process input (log or query) |
| POST | `/query` | Query fitness data |

### Examples

```bash
# Health check
curl http://localhost:8000/health

# Log an entry
curl -X POST http://localhost:8000/input \
  -H "Content-Type: application/json" \
  -d '{"text": "bench press 185x5 felt heavy"}'

# Query data
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"text": "how has my bench progressed?"}'
```

### Response Models

**Input Response:**
```json
{
  "status": "accepted",
  "input_type": "LOG",
  "entry_id": "2024-01-15_10-30-00",
  "message": null
}
```

**Query Response:**
```json
{
  "response": "Your bench press has improved from 175 lbs to 185 lbs over the past month.",
  "sources": ["2024-01-01_09-00-00", "2024-01-15_10-30-00"],
  "confidence": 0.85,
  "partial": false
}
```

## Configuration

Create `llm-config.yaml` in your project root:

```yaml
default_provider: "ollama"
# fallback_provider: "anthropic"  # Uncomment for cloud fallback

providers:
  ollama:
    api_base: "http://localhost:11434"
  # anthropic:
  #   api_key: "${ANTHROPIC_API_KEY}"

tiers:
  low:
    ollama: "qwen2.5:7b"
  medium:
    ollama: "qwen2.5:7b"
  high:
    ollama: "qwen2.5:7b"

agents:
  router:
    tier: low
  parser:
    tier: medium
  planner:
    tier: medium
  analyzer:
    tier: high
  synthesizer:
    tier: high
  evaluator:
    tier: medium
```

### Dual LLM Support

Quilto supports both local and cloud providers:

| Mode | Provider | Trade-offs |
|------|----------|------------|
| **Local** | Ollama | Privacy, no API costs, offline, lower quality |
| **Cloud** | OpenAI, Anthropic | Higher quality, larger context, requires API key |

## Architecture

```
User Input
    │
    ▼
┌─────────┐     ┌─────────┐     ┌───────────┐
│ Router  │────▶│ Parser  │────▶│  Storage  │
└─────────┘     └─────────┘     └───────────┘
    │                                 │
    │ (Query)                         │
    ▼                                 ▼
┌─────────┐     ┌───────────┐   ┌───────────┐
│ Planner │────▶│ Retriever │──▶│ Analyzer  │
└─────────┘     └───────────┘   └───────────┘
                                      │
                                      ▼
                              ┌─────────────┐
                              │ Synthesizer │
                              └─────────────┘
                                      │
                                      ▼
                              ┌───────────┐
                              │ Evaluator │──▶ Response
                              └───────────┘
```

**Agents:**
- **Router** - Classifies input as LOG, QUERY, BOTH, or CORRECTION
- **Parser** - Extracts structured data from natural language
- **Planner** - Creates retrieval strategy for queries
- **Retriever** - Fetches relevant entries from storage
- **Analyzer** - Analyzes retrieved data for patterns
- **Synthesizer** - Generates natural language response
- **Evaluator** - Validates response quality with retry loop

## Supported Domains

| Domain | Examples |
|--------|----------|
| **Strength** | Bench press, squat, deadlift with sets/reps/weight |
| **Running** | Distance, pace, splits, heart rate, terrain |
| **Swimming** | Laps, strokes, intervals, pool length |
| **Nutrition** | Meals, calories, macros, food items |
| **General Fitness** | Any workout activity, perceived effort |

## Development

```bash
# Quick validation (run often)
make check          # lint + typecheck

# Full validation (before commits)
make validate       # lint + format + typecheck + test

# Integration tests with real Ollama
make test-ollama

# Individual commands
uv run ruff check .        # Lint
uv run ruff format .       # Format
uv run pyright             # Type check
uv run pytest              # Unit tests
```

## Project Structure

```
swealog/
├── packages/
│   ├── quilto/              # Agent framework
│   │   ├── quilto/
│   │   │   ├── agents/      # All agent implementations
│   │   │   ├── llm/         # LLM client abstraction
│   │   │   ├── storage/     # Storage interface
│   │   │   └── domain.py    # DomainModule base class
│   │   └── tests/
│   │
│   └── swealog/             # Fitness application
│       ├── swealog/
│       │   ├── cli/         # CLI commands (log, ask, import, serve)
│       │   ├── api/         # FastAPI endpoints
│       │   └── domains/     # Fitness domain modules
│       └── tests/
│
├── tests/                   # Integration tests & corpus
├── llm-config.yaml          # LLM configuration
├── pyproject.toml           # Workspace configuration
└── Makefile                 # Development commands
```

## License

TBD
