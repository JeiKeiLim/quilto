# Story 8.1: Implement Typer CLI Framework

Status: ready-for-review

## Story

As a **Swealog user**,
I want a **Typer-based CLI for Swealog**,
So that **I can interact with my fitness logs via command-line with rich output formatting**.

## Acceptance Criteria

1. **AC1: Base CLI Application**
   - Given the swealog.cli module
   - When imported and used
   - Then a Typer application instance is available with version callback
   - And the app displays version with `--version` flag

2. **AC2: Rich Output Integration**
   - Given CLI output functionality
   - When using swealog.cli output helpers
   - Then console output uses rich formatting (colors, panels, tables)
   - And error messages display with appropriate styling (red for errors)
   - And success messages display with appropriate styling (green for success)

3. **AC3: Common Utilities**
   - Given the swealog.cli module
   - When using CLI utilities
   - Then async command helpers handle event loop properly
   - And configuration loading helpers are available (llm-config.yaml, storage path)
   - And error handling wrappers provide consistent exit codes

4. **AC4: Help and Documentation**
   - Given any CLI command
   - When `--help` is passed
   - Then rich-formatted help text is displayed
   - And command descriptions use Google-style docstrings

## Tasks / Subtasks

- [x] Task 1: Verify dependencies in swealog pyproject.toml (AC: 1, 2)
  - [x] Confirm `typer>=0.15.0` exists in swealog dependencies
  - [x] Confirm `rich>=13.9.0` exists in swealog dependencies
  - [x] Run `uv sync` to update lockfile

- [x] Task 2: Create swealog.cli module structure (AC: 1)
  - [x] Create `packages/swealog/swealog/cli/` directory
  - [x] Create `__init__.py` with exports
  - [x] Create `app.py` with base Typer application
  - [x] Add `--version` callback using importlib.metadata

- [x] Task 3: Implement rich output helpers (AC: 2)
  - [x] Create `output.py` with Console singleton
  - [x] Add `print_success()` - green success messages with checkmark prefix
  - [x] Add `print_error()` - red error messages with X prefix
  - [x] Add `print_warning()` - yellow warning messages
  - [x] Add `print_info()` - blue info messages
  - [x] Add `print_panel()` - rich Panel wrapper
  - [x] Add `print_table()` - rich Table wrapper

- [x] Task 4: Implement common utilities (AC: 3)
  - [x] Create `utils.py` with async helpers
  - [x] Add `run_async()` decorator for async commands
  - [x] Add `load_cli_config()` wrapper around `quilto.llm.load_llm_config()`
  - [x] Add `resolve_storage_path()` for storage directory (default: `./logs`)
  - [x] Add exit code constants: `EXIT_SUCCESS=0`, `EXIT_ERROR=1`, `EXIT_USAGE_ERROR=2`

- [x] Task 5: Add CLI entry point (AC: 1)
  - [x] Add `[project.scripts]` entry to swealog pyproject.toml
  - [x] Entry point: `swealog = "swealog.cli:app"`

- [x] Task 6: Write unit tests (AC: 1-4)
  - [x] Create `packages/swealog/tests/test_cli_app.py` - app creation, version callback
  - [x] Create `packages/swealog/tests/test_cli_output.py` - output helpers with captured console
  - [x] Create `packages/swealog/tests/test_cli_utils.py` - async helpers, config loading
  - [x] Use `typer.testing.CliRunner` for command invocation tests

## Dev Notes

### Project Identity (CRITICAL)

This story adds CLI to **Swealog** (the application), NOT Quilto. Quilto is a domain-agnostic framework that should not have user interfaces.

**Quilto provides:** Agents, LLM client, storage interface, DomainModule base class
**Swealog provides:** CLI, API, fitness domains, user-facing features

### Architecture Compliance

**File Location:** `packages/swealog/swealog/cli/`

**Module Structure:**
```
swealog/cli/
├── __init__.py     # Exports: app, all output helpers, all utilities
├── app.py          # Base Typer app with version callback
├── output.py       # Rich output helpers (Console singleton)
└── utils.py        # Async helpers, config loading, exit codes
```

### Dependencies

Swealog already has typer and rich in pyproject.toml:
```toml
dependencies = [
    "quilto",
    "typer>=0.15.0",
    "rich>=13.9.0",
]
```

### Code Patterns

**Typer App (app.py):**
```python
from importlib.metadata import version

import typer


def _get_version() -> str:
    try:
        return version("swealog")
    except Exception:
        return "unknown"


def version_callback(value: bool) -> None:
    if value:
        print(f"swealog version {_get_version()}")
        raise typer.Exit()


app = typer.Typer(
    name="swealog",
    help="Fitness logging application powered by Quilto",
    no_args_is_help=True,
)


@app.callback()
def main(
    version: bool = typer.Option(
        False, "--version", "-v",
        callback=version_callback,
        is_eager=True,
        help="Show version and exit",
    ),
) -> None:
    """Swealog - AI-powered fitness logging."""
```

**Rich Output (output.py):**
```python
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()  # Singleton for all output


def print_success(message: str) -> None:
    """Print success message in green."""
    console.print(f"[green]✓ {message}[/green]")


def print_error(message: str) -> None:
    """Print error message in red."""
    console.print(f"[red]✗ {message}[/red]")


def print_warning(message: str) -> None:
    """Print warning message in yellow."""
    console.print(f"[yellow]! {message}[/yellow]")


def print_info(message: str) -> None:
    """Print info message in blue."""
    console.print(f"[blue]ℹ[/blue] {message}")


def print_panel(content: str, title: str = "") -> None:
    """Print content in a rich panel."""
    console.print(Panel(content, title=title))


def print_table(headers: list[str], rows: list[list[str]], title: str = "") -> None:
    """Print data in a rich table."""
    table = Table(title=title)
    for header in headers:
        table.add_column(header)
    for row in rows:
        table.add_row(*row)
    console.print(table)
```

**Async Helper (utils.py):**
```python
import asyncio
from collections.abc import Callable, Coroutine
from functools import wraps
from pathlib import Path
from typing import Any

from quilto.llm import LLMConfig, load_llm_config

# Exit codes
EXIT_SUCCESS = 0
EXIT_ERROR = 1
EXIT_USAGE_ERROR = 2


def run_async[T, **P](func: Callable[P, Coroutine[Any, Any, T]]) -> Callable[P, T]:
    """Decorator to run async function in sync context for Typer commands."""
    @wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
        return asyncio.run(func(*args, **kwargs))
    return wrapper


def load_cli_config(config_path: Path | None = None) -> LLMConfig:
    """Load LLM configuration from file."""
    if config_path is None:
        config_path = Path("llm-config.yaml")
    return load_llm_config(config_path)


def resolve_storage_path(storage_path: Path | None = None) -> Path:
    """Resolve storage directory path."""
    if storage_path is None:
        storage_path = Path("logs")
    storage_path.mkdir(parents=True, exist_ok=True)
    return storage_path
```

### Entry Point

**Add to swealog pyproject.toml:**
```toml
[project.scripts]
swealog = "swealog.cli:app"
```

### Validation Commands

```bash
# During development
make check        # lint + typecheck

# Before completion
make validate     # lint + format + typecheck + test
```

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Completion Notes List

1. **REVISED**: Moved CLI from Quilto (framework) to Swealog (application) - frameworks should not have user interfaces
2. Created `swealog/cli/` module with:
   - `app.py`: Base Typer app with version callback using importlib.metadata
   - `output.py`: Rich output helpers (console singleton, print_success/error/warning/info/panel/table)
   - `utils.py`: Async helpers (run_async decorator with PEP 695 type parameters), config loading, exit codes
   - `__init__.py`: Exports all public APIs
3. Added `[project.scripts]` entry point: `swealog = "swealog.cli:app"`
4. Removed typer/rich dependencies from quilto/pyproject.toml (already in swealog)
5. Removed quilto/cli/ module and cli_app export from quilto/__init__.py
6. Created comprehensive unit tests (31 tests total):
   - `test_cli_app.py`: App creation, version callback, help flag, extensibility tests
   - `test_cli_output.py`: All output helper formatting tests with console capture
   - `test_cli_utils.py`: Exit codes, run_async decorator, config loading, storage path resolution
7. All 1578 tests pass

### File List

**New Files:**
- packages/swealog/swealog/cli/__init__.py
- packages/swealog/swealog/cli/app.py
- packages/swealog/swealog/cli/output.py
- packages/swealog/swealog/cli/utils.py
- packages/swealog/tests/test_cli_app.py
- packages/swealog/tests/test_cli_output.py
- packages/swealog/tests/test_cli_utils.py

**Modified Files:**
- packages/swealog/pyproject.toml (add entry point)
