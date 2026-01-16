# Story 8.1: Implement Typer CLI Framework

Status: done

## Story

As a **Quilto developer**,
I want a **Typer-based CLI framework in Quilto**,
So that **applications built on Quilto can expose command-line interfaces with rich output formatting and extensibility**.

## Acceptance Criteria

1. **AC1: Base CLI Application**
   - Given the quilto.cli module
   - When imported and used
   - Then a Typer application instance is available with version callback
   - And the app displays version with `--version` flag

2. **AC2: Rich Output Integration**
   - Given CLI output functionality
   - When using quilto.cli output helpers
   - Then console output uses rich formatting (colors, panels, tables)
   - And error messages display with appropriate styling (red for errors)
   - And success messages display with appropriate styling (green for success)

3. **AC3: Application Extensibility**
   - Given the quilto CLI base
   - When an application (like Swealog) extends it
   - Then custom commands can be registered using `add_command()`
   - And command groups can be created for organized subcommands
   - And base framework commands remain available

4. **AC4: Common Utilities**
   - Given the quilto.cli module
   - When using CLI utilities
   - Then async command helpers handle event loop properly
   - And configuration loading helpers are available (llm-config.yaml, storage path)
   - And error handling wrappers provide consistent exit codes

5. **AC5: Help and Documentation**
   - Given any CLI command
   - When `--help` is passed
   - Then rich-formatted help text is displayed
   - And command descriptions use Google-style docstrings

## Tasks / Subtasks

- [x] Task 1: Add dependencies to quilto pyproject.toml (AC: 1, 2)
  - [x] Add `typer>=0.15.0` to quilto dependencies
  - [x] Add `rich>=13.9.0` to quilto dependencies
  - [x] Run `uv sync` to update lockfile

- [x] Task 2: Create quilto.cli module structure (AC: 1)
  - [x] Create `packages/quilto/quilto/cli/` directory
  - [x] Create `__init__.py` with exports
  - [x] Create `app.py` with base Typer application
  - [x] Add `--version` callback using hardcoded version (avoid circular import)

- [x] Task 3: Implement rich output helpers (AC: 2)
  - [x] Create `output.py` with Console singleton
  - [x] Add `print_success()` - green success messages with ✓ prefix
  - [x] Add `print_error()` - red error messages with ✗ prefix
  - [x] Add `print_warning()` - yellow warning messages
  - [x] Add `print_info()` - blue info messages
  - [x] Add `print_panel()` - rich Panel wrapper
  - [x] Add `print_table()` - rich Table wrapper

- [x] Task 4: Implement extensibility framework (AC: 3)
  - [x] Export `app` instance from `quilto.cli`
  - [x] Verify `app.add_typer()` works for subcommand groups
  - [x] Verify `@app.command()` decorator works for command registration

- [x] Task 5: Implement common utilities (AC: 4)
  - [x] Create `utils.py` with async helpers
  - [x] Add `run_async()` decorator for async commands
  - [x] Add `load_cli_config()` wrapper around existing `quilto.llm.load_llm_config()`
  - [x] Add `resolve_storage_path()` for storage directory (default: `./logs`)
  - [x] Add exit code constants: `EXIT_SUCCESS=0`, `EXIT_ERROR=1`, `EXIT_USAGE_ERROR=2`

- [x] Task 6: Update quilto exports (AC: 1, 3)
  - [x] Add cli imports to `quilto/__init__.py`: `from quilto.cli import app as cli_app`
  - [x] Add `cli_app` to `__all__` list
  - [x] Note: quilto already has `py.typed` marker - no new marker needed for cli/

- [x] Task 7: Write unit tests (AC: 1-5)
  - [x] Create `packages/quilto/tests/test_cli_app.py` - app creation, version callback
  - [x] Create `packages/quilto/tests/test_cli_output.py` - output helpers with captured console
  - [x] Create `packages/quilto/tests/test_cli_utils.py` - async helpers, config loading
  - [x] Use `typer.testing.CliRunner` for command invocation tests
  - [x] Use `rich.console.Console(file=StringIO(), force_terminal=True)` for output capture

## Dev Notes

### Project Identity (CRITICAL)

This story adds CLI to **Quilto** (the framework), not Swealog. The CLI module provides:
- Base infrastructure that any application can extend
- Framework commands (none in this story, prepared for future)
- Rich output helpers for consistent formatting

Swealog-specific CLI commands (log, ask, import) will be implemented in Story 8.5.

### Architecture Compliance

**File Location:** `packages/quilto/quilto/cli/`

**Module Structure:**
```
quilto/cli/
├── __init__.py     # Exports: app, all output helpers, all utilities
├── app.py          # Base Typer app with version callback
├── output.py       # Rich output helpers (Console singleton)
└── utils.py        # Async helpers, config loading, exit codes
```

**Note:** No `py.typed` needed in cli/ - quilto already has `quilto/py.typed` at package root.

### Dependencies (MUST ADD)

**Add to `packages/quilto/pyproject.toml`:**
```toml
dependencies = [
    "litellm>=1.50.0",
    "pydantic>=2.10.0",
    "langgraph>=0.2.0",
    "typer>=0.15.0",      # ADD THIS
    "rich>=13.9.0",        # ADD THIS
]
```

Swealog already has these dependencies, but quilto.cli needs them declared in quilto for proper dependency resolution.

### Code Patterns

**Typer App (app.py):**
```python
import typer
from quilto import __version__

app = typer.Typer(
    name="quilto",
    help="Domain-agnostic agent framework for note processing",
    no_args_is_help=True,
)

def version_callback(value: bool) -> None:
    if value:
        print(f"quilto version {__version__}")
        raise typer.Exit()

@app.callback()
def main(
    version: bool = typer.Option(
        False, "--version", "-v",
        callback=version_callback,
        is_eager=True,
        help="Show version and exit",
    ),
) -> None:
    """Quilto - Domain-agnostic agent framework."""
```

**Rich Output (output.py):**
```python
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()  # Singleton for all output

def print_success(message: str) -> None:
    """Print success message in green."""
    console.print(f"[green]✓[/green] {message}")

def print_error(message: str) -> None:
    """Print error message in red."""
    console.print(f"[red]✗[/red] {message}", style="red")

def print_warning(message: str) -> None:
    """Print warning message in yellow."""
    console.print(f"[yellow]![/yellow] {message}", style="yellow")

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
from collections.abc import Awaitable, Callable
from functools import wraps
from pathlib import Path
from typing import Any, ParamSpec, TypeVar

from quilto.llm import LLMConfig, load_llm_config

P = ParamSpec("P")
T = TypeVar("T")

# Exit codes
EXIT_SUCCESS = 0
EXIT_ERROR = 1
EXIT_USAGE_ERROR = 2

def run_async(func: Callable[P, Awaitable[T]]) -> Callable[P, T]:
    """Decorator to run async function in sync context for Typer commands."""
    @wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
        return asyncio.run(func(*args, **kwargs))
    return wrapper

def load_cli_config(config_path: Path | None = None) -> LLMConfig:
    """Load LLM configuration from file.

    Args:
        config_path: Path to config file. Defaults to ./llm-config.yaml

    Returns:
        Loaded LLMConfig instance.
    """
    if config_path is None:
        config_path = Path("llm-config.yaml")
    return load_llm_config(config_path)

def resolve_storage_path(storage_path: Path | None = None) -> Path:
    """Resolve storage directory path.

    Args:
        storage_path: Explicit path. Defaults to ./logs

    Returns:
        Resolved Path, created if needed.
    """
    if storage_path is None:
        storage_path = Path("logs")
    storage_path.mkdir(parents=True, exist_ok=True)
    return storage_path
```

### Export Pattern

**quilto/cli/__init__.py:**
```python
"""CLI framework for Quilto applications."""

from quilto.cli.app import app
from quilto.cli.output import (
    console,
    print_error,
    print_info,
    print_panel,
    print_success,
    print_table,
    print_warning,
)
from quilto.cli.utils import (
    EXIT_ERROR,
    EXIT_SUCCESS,
    EXIT_USAGE_ERROR,
    load_cli_config,
    resolve_storage_path,
    run_async,
)

__all__ = [
    "EXIT_ERROR",
    "EXIT_SUCCESS",
    "EXIT_USAGE_ERROR",
    "app",
    "console",
    "load_cli_config",
    "print_error",
    "print_info",
    "print_panel",
    "print_success",
    "print_table",
    "print_warning",
    "resolve_storage_path",
    "run_async",
]
```

**quilto/__init__.py update (add to existing imports):**
```python
from quilto.cli import app as cli_app
# Add "cli_app" to __all__
```

### Testing Strategy

**Test Files (follow existing flat structure):**
- `packages/quilto/tests/test_cli_app.py` - App creation, version callback
- `packages/quilto/tests/test_cli_output.py` - All output helpers with captured console
- `packages/quilto/tests/test_cli_utils.py` - Async helpers, config loading

**Typer CliRunner Pattern:**
```python
from typer.testing import CliRunner
from quilto.cli import app

runner = CliRunner()

def test_version_flag() -> None:
    """Test --version displays version."""
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert "quilto version" in result.stdout

def test_help_flag() -> None:
    """Test --help displays help."""
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "Quilto" in result.stdout
```

**Rich Console Capture Pattern:**
```python
from io import StringIO
from rich.console import Console
from quilto.cli.output import print_success

def test_print_success_format() -> None:
    """Test success message formatting."""
    output = StringIO()
    test_console = Console(file=output, force_terminal=True)
    # Note: For testing, you may need to patch console or
    # create output functions that accept console as parameter
```

### Previous Epic Learnings (Epic 7)

From Epic 7 Retrospective:
- Integration tests with real Ollama catch bugs mocks miss
- Code review process catches real bugs (word boundary issues, data loss)
- Clean agent patterns enable smooth implementation
- Follow existing flat test structure in `packages/quilto/tests/`

### Anti-Patterns to Avoid

1. **Don't create Swealog-specific commands** - Those belong in Story 8.5
2. **Don't add entry point to quilto pyproject.toml** - Framework doesn't have CLI entry
3. **Don't import swealog from quilto** - Framework must be app-agnostic (see project-context.md)
4. **Don't use click directly** - Use typer (which wraps click)
5. **Don't print without rich** - All output should use rich formatting

### Dependencies

**Story 8.1 enables:**
- Story 8.5: Create Swealog CLI Commands (uses quilto.cli as base)
- Story 8.2: Implement FastAPI Endpoints (similar patterns for error handling)

**No blocking dependencies** - This is the first story of Epic 8.

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

### Debug Log References

N/A

### Completion Notes List

1. Added `typer>=0.15.0` and `rich>=13.9.0` dependencies to quilto pyproject.toml
2. Created `quilto/cli/` module with:
   - `app.py`: Base Typer app with version callback (hardcoded version to avoid circular import)
   - `output.py`: Rich output helpers (console singleton, print_success/error/warning/info/panel/table)
   - `utils.py`: Async helpers (run_async decorator with PEP 695 type parameters), config loading, exit codes
   - `__init__.py`: Exports all public APIs
3. Updated `quilto/__init__.py` to export `cli_app`
4. Created comprehensive unit tests (31 tests total):
   - `test_cli_app.py`: App creation, version callback, help flag, extensibility tests
   - `test_cli_output.py`: All output helper formatting tests with console capture
   - `test_cli_utils.py`: Exit codes, run_async decorator, config loading, storage path resolution
5. All 1578 tests pass (31 new CLI tests + existing tests)
6. Used PEP 695 type parameter syntax for `run_async` to satisfy ruff UP047 rule

### File List

**New Files:**
- packages/quilto/quilto/cli/__init__.py
- packages/quilto/quilto/cli/app.py
- packages/quilto/quilto/cli/output.py
- packages/quilto/quilto/cli/utils.py
- packages/quilto/tests/test_cli_app.py
- packages/quilto/tests/test_cli_output.py
- packages/quilto/tests/test_cli_utils.py

**Modified Files:**
- packages/quilto/pyproject.toml (added typer, rich dependencies)
- packages/quilto/quilto/__init__.py (added cli_app export)

## Senior Developer Review (AI)

**Reviewer:** Jongkuk Lim
**Date:** 2026-01-16
**Outcome:** Approved with fixes applied

### Issues Found and Fixed

1. **[HIGH] Pyright type error in `run_async` decorator** - Fixed by changing `Awaitable[T]` to `Coroutine[Any, Any, T]` in `utils.py:17`

2. **[MEDIUM] Version hardcoded in two places** - Fixed by using `importlib.metadata.version("quilto")` in `app.py` instead of hardcoded version

3. **[MEDIUM] Test pollution from shared app state** - Fixed extensibility test to use isolated Typer app instance

4. **[MEDIUM] Inconsistent output styling** - Standardized `print_error` and `print_warning` to use consistent rich markup pattern (full message in color tags)

5. **[LOW] Pyright unused function warnings** - Added `# pyright: ignore[reportUnusedFunction]` comments to test decorator functions

### Verification

- `make validate` passes (1578 tests, lint, typecheck)
- `make test-ollama` passes (1616 tests including real Ollama integration)
- All ACs verified implemented
- All tasks marked [x] verified complete

### Change Log

| Date | Change | Author |
|------|--------|--------|
| 2026-01-16 | Code review completed, 4 issues fixed | Claude Opus 4.5 |

