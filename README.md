# Swealog

A fitness logging application powered by the Quilto agent framework.

## Overview

This workspace contains two packages:

- **quilto** - Domain-agnostic agent framework for note processing
- **swealog** - Fitness logging application using Quilto

## Requirements

- Python 3.13+
- [uv](https://docs.astral.sh/uv/) package manager

## Quick Start

```bash
# Install dependencies
uv sync

# Verify installation
uv run python -c "from quilto import __version__; print(f'quilto: {__version__}')"
uv run python -c "from swealog import __version__; print(f'swealog: {__version__}')"
```

## Development

```bash
# Run linter
uv run ruff check .

# Run type checker
uv run pyright

# Run tests
uv run pytest
```

## Project Structure

```
swealog/
├── packages/
│   ├── quilto/          # Agent framework
│   │   ├── quilto/      # Source code
│   │   └── tests/       # Package tests
│   └── swealog/         # Fitness app
│       ├── swealog/     # Source code
│       └── tests/       # Package tests
├── tests/               # Integration tests & corpus
├── pyproject.toml       # Workspace configuration
└── pyrightconfig.json   # Type checking config
```

## License

TBD
