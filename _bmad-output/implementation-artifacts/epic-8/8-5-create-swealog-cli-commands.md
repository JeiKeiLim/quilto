# Story 8.5: Create Swealog CLI Commands

Status: done

## Story

As a **Swealog user**,
I want **`swealog log` and `swealog ask` CLI commands**,
So that **I can log fitness entries and query my data from the terminal without using the API**.

## Acceptance Criteria

1. **AC1: Log Command**
   - Given the user runs `swealog log "bench 185x5 felt heavy"`
   - When the command executes
   - Then the input is routed through Router agent
   - And LOG/BOTH inputs are parsed and stored
   - And QUERY-only inputs show a hint to use `ask` instead
   - And the entry ID is displayed on success

2. **AC2: Ask Command**
   - Given the user runs `swealog ask "how has my bench press progressed?"`
   - When the command executes
   - Then the full query pipeline runs (Router→Planner→Retriever→Analyzer→Synthesizer→Evaluator)
   - And the response is displayed in a rich panel
   - And source entry IDs are listed
   - And confidence score is shown

3. **AC3: Error Handling**
   - Given an error occurs (LLM failure, storage error)
   - When the command handles it
   - Then a user-friendly error message is displayed (red styling)
   - And appropriate exit code is returned (EXIT_ERROR=1)

4. **AC4: Configuration Options**
   - Given the CLI commands
   - When `--config` flag is provided
   - Then custom llm-config.yaml path is used
   - And `--storage` flag specifies custom storage path (default: ./logs)

5. **AC5: Rich Output Formatting**
   - Given command output
   - When displaying results
   - Then success messages use green styling with checkmark
   - And query responses use Panel with title
   - And metadata (sources, confidence) use info styling

## Tasks / Subtasks

- [x] Task 1: Create shared dependency helper (AC: 4) - **DO FIRST**
  - [x] Update `utils.py` with `get_dependencies()` function
  - [x] Signature: `def get_dependencies(config_path: Path | None, storage_path: Path | None) -> tuple[LLMClient, StorageRepository, list[DomainModule]]`
  - [x] Load config via `load_cli_config(config_path)`
  - [x] Create `LLMClient(config)`
  - [x] Create `StorageRepository(resolve_storage_path(storage_path))`
  - [x] Import and return all 5 domains as list
  - [x] This helper is used by BOTH log and ask commands for consistency

- [x] Task 2: Create log command module (AC: 1, 3, 4, 5)
  - [x] Create `packages/swealog/swealog/cli/log_cmd.py`
  - [x] Implement `log()` async function with `@run_async` decorator
  - [x] Use `get_dependencies()` helper for initialization
  - [x] Use `DomainSelector` to get domain infos (consistent with API)
  - [x] Route input through `RouterAgent.classify()`
  - [x] Handle QUERY-only: `print_info` + suggest `ask` + `Exit(EXIT_SUCCESS)`
  - [x] Handle LOG/BOTH/CORRECTION: parse + store + `print_success` with entry_id
  - [x] For BOTH: also `print_info` about query portion
  - [x] Wrap in try/except: `print_error` + `Exit(EXIT_ERROR)` on failure
  - [x] Register in app.py: `app.command()(log)`

- [x] Task 3: Create ask command module (AC: 2, 3, 4, 5)
  - [x] Create `packages/swealog/swealog/cli/ask_cmd.py`
  - [x] Implement `ask()` async function with `@run_async` decorator
  - [x] Use `get_dependencies()` helper for initialization
  - [x] Import and call `execute_query_pipeline()` from `swealog.api.routes.query`
  - [x] Display response in `print_panel(result["response"], title="Response")`
  - [x] Format sources: show first 5 + "(+N more)" if > 5
  - [x] Display confidence as percentage: `{result['confidence']:.0%}`
  - [x] If `result["is_partial"]`: `print_warning` before response
  - [x] Wrap in try/except: `print_error` + `Exit(EXIT_ERROR)` on failure
  - [x] Register in app.py: `app.command()(ask)`

- [x] Task 4: Export new commands from __init__.py (AC: all)
  - [x] Export `log` function from log_cmd
  - [x] Export `ask` function from ask_cmd
  - [x] Export `get_dependencies` helper
  - [x] Add all to `__all__` list

- [x] Task 5: Write unit tests (AC: 1-5)
  - [x] Create `packages/swealog/tests/test_cli_log.py` with CliRunner
  - [x] Create `packages/swealog/tests/test_cli_ask.py` with CliRunner
  - [x] Mock at module level (patch swealog.cli.log_cmd.RouterAgent, etc.)
  - [x] Use `AsyncMock` for async agent methods
  - [x] See Testing Patterns section below for structure

- [x] Task 6: Integration test with real Ollama (AC: 1, 2)
  - [x] Run `make test-ollama` - must pass before story is complete

## Dev Notes

### Project Identity (CRITICAL)

This story adds commands to **Swealog** (the application), NOT Quilto.

- **Location:** `packages/swealog/swealog/cli/`
- **Quilto provides:** Agents (Router, Parser, query agents), LLMClient, StorageRepository, DomainSelector
- **Swealog provides:** CLI commands, fitness domains, user-facing features

### File Structure
```
packages/swealog/swealog/cli/
├── __init__.py          # Export new commands (MODIFY)
├── app.py               # Register log/ask commands (MODIFY)
├── output.py            # Rich helpers (unchanged)
├── utils.py             # Add get_dependencies helper (MODIFY)
├── import_cmd.py        # Existing import command (unchanged)
├── log_cmd.py           # NEW: swealog log command
└── ask_cmd.py           # NEW: swealog ask command

packages/swealog/tests/
├── test_cli_log.py      # NEW: log command tests
└── test_cli_ask.py      # NEW: ask command tests
```

### Code Reuse - CRITICAL

**DO NOT DUPLICATE API LOGIC.** Reuse existing implementations:

1. **Ask command:** Import `execute_query_pipeline()` from `api/routes/query.py`
   - Returns: `dict[str, Any]` with keys: `response`, `sources`, `confidence`, `is_partial`
   - Handles full pipeline internally (Router→Planner→Retriever→Analyzer→Synthesizer→Evaluator)

2. **Log command:** Adapt logic from `parse_log_background()` in `api/routes/input.py`
   - Run synchronously (CLI waits for result, unlike API background task)
   - Use `DomainSelector` for consistent domain handling

### Imports Reference

**From Quilto (all available from top-level):**
```python
from quilto import (
    DomainInfo,          # For router domain context
    DomainModule,        # Type for domain list
    DomainSelector,      # Build domain context consistently
    Entry,               # Entry model for storage
    LLMClient,           # LLM client
    ParserAgent,         # Parse log entries
    ParserInput,         # Parser input model
    RouterAgent,         # Route input type
    RouterInput,         # Router input model
    StorageRepository,   # Storage (takes Path as base_path)
)
```

**From Swealog domains:**
```python
from swealog.domains import general_fitness, nutrition, running, strength, swimming
```

**From CLI utilities (existing):**
```python
from swealog.cli.output import print_error, print_info, print_panel, print_success, print_warning
from swealog.cli.utils import EXIT_ERROR, EXIT_SUCCESS, run_async
```

**From API (reuse for ask):**
```python
from swealog.api.routes.query import execute_query_pipeline
```

### Code Patterns

**Shared Dependencies Helper (utils.py addition):**
```python
# Add to utils.py

from quilto import DomainModule, LLMClient, StorageRepository
from swealog.domains import general_fitness, nutrition, running, strength, swimming


def get_dependencies(
    config_path: Path | None = None,
    storage_path: Path | None = None,
) -> tuple[LLMClient, StorageRepository, list[DomainModule]]:
    """Initialize shared CLI dependencies.

    Args:
        config_path: Optional path to llm-config.yaml.
        storage_path: Optional path to storage directory.

    Returns:
        Tuple of (LLMClient, StorageRepository, list of domains).
    """
    config = load_cli_config(config_path)
    llm_client = LLMClient(config)
    storage = StorageRepository(resolve_storage_path(storage_path))
    domains: list[DomainModule] = [general_fitness, strength, nutrition, running, swimming]
    return llm_client, storage, domains
```

**Log Command (log_cmd.py):**
```python
"""CLI command for logging fitness entries."""

import logging
from datetime import datetime
from pathlib import Path
from typing import Annotated

import typer
from quilto import (
    DomainSelector,
    Entry,
    ParserAgent,
    ParserInput,
    RouterAgent,
    RouterInput,
)

from swealog.cli.output import print_error, print_info, print_success
from swealog.cli.utils import EXIT_ERROR, EXIT_SUCCESS, get_dependencies, run_async

logger = logging.getLogger(__name__)


@run_async
async def log(
    text: Annotated[str, typer.Argument(help="Fitness log entry text")],
    config: Annotated[Path | None, typer.Option("--config", "-c", help="Path to llm-config.yaml")] = None,
    storage_path: Annotated[Path | None, typer.Option("--storage", "-s", help="Path to storage directory")] = None,
) -> None:
    """Log a fitness entry via CLI."""
    try:
        # Initialize via shared helper
        llm_client, storage, domains = get_dependencies(config, storage_path)
        selector = DomainSelector(domains)

        # Route input
        router = RouterAgent(llm_client)
        router_input = RouterInput(raw_input=text, available_domains=selector.get_domain_infos())
        router_output = await router.classify(router_input)

        # Handle QUERY-only
        if router_output.input_type.value == "QUERY":
            print_info("This looks like a query. Use 'swealog ask' instead.")
            print_info(f'Try: swealog ask "{text}"')
            raise typer.Exit(EXIT_SUCCESS)

        # Parse and store
        entry_id = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        timestamp = datetime.now()

        # Build parser context from selected domains
        selected_domains = [d for d in domains if d.name in router_output.selected_domains] or domains
        domain_schemas = {d.name: d.log_schema for d in selected_domains}
        vocabulary: dict[str, str] = {}
        for d in selected_domains:
            vocabulary.update(d.vocabulary)

        # Handle correction mode
        is_correction = router_output.input_type.value == "CORRECTION"
        recent_entries: list[Entry] = []
        if is_correction:
            recent_entries = storage.get_entries_by_pattern("**/*.md")[-10:]

        # Parse
        parser = ParserAgent(llm_client)
        parser_input = ParserInput(
            raw_input=text,
            timestamp=timestamp,
            domain_schemas=domain_schemas,
            vocabulary=vocabulary,
            correction_mode=is_correction,
            correction_target=router_output.correction_target,
            recent_entries=recent_entries,
        )
        parser_output = await parser.parse(parser_input)

        # Create and save entry
        entry = Entry(
            id=entry_id,
            date=parser_output.date,
            timestamp=parser_output.timestamp,
            raw_content=text,
            parsed_data=parser_output.domain_data,
        )
        if is_correction and parser_output.is_correction:
            storage.save_entry(entry, correction=parser_output)
        else:
            storage.save_entry(entry)

        # Output
        print_success(f"Logged entry: {entry_id}")
        if router_output.input_type.value == "BOTH":
            print_info(f"Query detected: {router_output.query_portion}")
            print_info(f'Use \'swealog ask "{router_output.query_portion}"\' to process the query')

    except typer.Exit:
        raise
    except Exception as e:
        logger.exception("Log command failed: %s", e)
        print_error(f"Failed to log entry: {e}")
        raise typer.Exit(EXIT_ERROR) from e
```

**Ask Command (ask_cmd.py):**
```python
"""CLI command for querying fitness data."""

import logging
from pathlib import Path
from typing import Annotated

import typer

from swealog.api.routes.query import execute_query_pipeline
from swealog.cli.output import print_error, print_info, print_panel, print_warning
from swealog.cli.utils import EXIT_ERROR, get_dependencies, run_async

logger = logging.getLogger(__name__)


@run_async
async def ask(
    query: Annotated[str, typer.Argument(help="Question about your fitness data")],
    config: Annotated[Path | None, typer.Option("--config", "-c", help="Path to llm-config.yaml")] = None,
    storage_path: Annotated[Path | None, typer.Option("--storage", "-s", help="Path to storage directory")] = None,
) -> None:
    """Query your fitness data via CLI."""
    try:
        llm_client, storage, domains = get_dependencies(config, storage_path)

        # Reuse API pipeline logic
        result = await execute_query_pipeline(
            query=query,
            llm_client=llm_client,
            storage=storage,
            domains=domains,
        )

        # Warn if partial
        if result["is_partial"]:
            print_warning("Partial response (insufficient data or evaluation failed):")

        print_panel(result["response"], title="Response")

        # Sources
        if result["sources"]:
            sources_str = ", ".join(result["sources"][:5])
            if len(result["sources"]) > 5:
                sources_str += f" (+{len(result['sources']) - 5} more)"
            print_info(f"Sources: {sources_str}")

        print_info(f"Confidence: {result['confidence']:.0%}")

    except Exception as e:
        logger.exception("Ask command failed: %s", e)
        print_error(f"Query failed: {e}")
        raise typer.Exit(EXIT_ERROR) from e
```

**Register Commands (app.py):**
```python
# Add at end of app.py after existing imports
from swealog.cli.ask_cmd import ask
from swealog.cli.log_cmd import log

app.command()(log)
app.command()(ask)
```

### Testing Patterns

**Key Testing Approach:**
- Use `CliRunner` from `typer.testing`
- Mock at the module level where functions are imported (e.g., `swealog.cli.log_cmd.get_dependencies`)
- Use `AsyncMock` for async methods like `router.classify()` and `parser.parse()`
- Check `result.exit_code` and `result.output` for assertions

**Test Log Command (test_cli_log.py):**
```python
"""Tests for swealog log CLI command."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from typer.testing import CliRunner

from swealog.cli import app


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


@pytest.fixture
def mock_dependencies() -> MagicMock:
    """Create mock dependencies tuple."""
    mock_client = MagicMock()
    mock_storage = MagicMock()
    mock_domains = [MagicMock(name="GeneralFitness", log_schema={}, vocabulary={})]
    return (mock_client, mock_storage, mock_domains)


class TestLogCommand:
    def test_log_success(self, runner: CliRunner, mock_dependencies: tuple) -> None:
        """Log with LOG input saves entry and shows success."""
        with (
            patch("swealog.cli.log_cmd.get_dependencies", return_value=mock_dependencies),
            patch("swealog.cli.log_cmd.DomainSelector") as mock_selector,
            patch("swealog.cli.log_cmd.RouterAgent") as mock_router_cls,
            patch("swealog.cli.log_cmd.ParserAgent") as mock_parser_cls,
        ):
            mock_selector.return_value.get_domain_infos.return_value = []
            mock_router_cls.return_value.classify = AsyncMock(return_value=MagicMock(
                input_type=MagicMock(value="LOG"),
                selected_domains=["GeneralFitness"],
                query_portion=None,
                correction_target=None,
            ))
            mock_parser_cls.return_value.parse = AsyncMock(return_value=MagicMock(
                date="2026-01-16",
                timestamp="2026-01-16T12:00:00",
                domain_data={},
                is_correction=False,
            ))

            result = runner.invoke(app, ["log", "bench 185x5"])

            assert result.exit_code == 0
            assert "Logged entry:" in result.output

    def test_log_query_suggests_ask(self, runner: CliRunner, mock_dependencies: tuple) -> None:
        """Log with QUERY input suggests using ask command."""
        with (
            patch("swealog.cli.log_cmd.get_dependencies", return_value=mock_dependencies),
            patch("swealog.cli.log_cmd.DomainSelector"),
            patch("swealog.cli.log_cmd.RouterAgent") as mock_router_cls,
        ):
            mock_router_cls.return_value.classify = AsyncMock(return_value=MagicMock(
                input_type=MagicMock(value="QUERY"),
            ))

            result = runner.invoke(app, ["log", "how much did I bench?"])

            assert result.exit_code == 0
            assert "swealog ask" in result.output

    def test_log_error_shows_message(self, runner: CliRunner) -> None:
        """Log error shows user-friendly message and exits with error code."""
        with patch("swealog.cli.log_cmd.get_dependencies", side_effect=Exception("Config error")):
            result = runner.invoke(app, ["log", "test"])

            assert result.exit_code == 1
            assert "Failed to log entry" in result.output
```

**Test Ask Command (test_cli_ask.py):**
```python
"""Tests for swealog ask CLI command."""

from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from swealog.cli import app


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


@pytest.fixture
def mock_dependencies() -> tuple:
    return (MagicMock(), MagicMock(), [])


class TestAskCommand:
    def test_ask_success(self, runner: CliRunner, mock_dependencies: tuple) -> None:
        """Ask displays response, sources, and confidence."""
        with (
            patch("swealog.cli.ask_cmd.get_dependencies", return_value=mock_dependencies),
            patch("swealog.cli.ask_cmd.execute_query_pipeline") as mock_pipeline,
        ):
            mock_pipeline.return_value = {
                "response": "Your bench improved from 175 to 185 lbs.",
                "sources": ["2026-01-10", "2026-01-15"],
                "confidence": 0.85,
                "is_partial": False,
            }

            result = runner.invoke(app, ["ask", "how has my bench progressed?"])

            assert result.exit_code == 0
            assert "bench improved" in result.output
            assert "85%" in result.output

    def test_ask_partial_shows_warning(self, runner: CliRunner, mock_dependencies: tuple) -> None:
        """Partial response shows warning message."""
        with (
            patch("swealog.cli.ask_cmd.get_dependencies", return_value=mock_dependencies),
            patch("swealog.cli.ask_cmd.execute_query_pipeline") as mock_pipeline,
        ):
            mock_pipeline.return_value = {
                "response": "Limited data.",
                "sources": [],
                "confidence": 0.4,
                "is_partial": True,
            }

            result = runner.invoke(app, ["ask", "how fast?"])

            assert result.exit_code == 0
            assert "Partial response" in result.output

    def test_ask_error_shows_message(self, runner: CliRunner) -> None:
        """Ask error shows user-friendly message."""
        with patch("swealog.cli.ask_cmd.get_dependencies", side_effect=Exception("LLM error")):
            result = runner.invoke(app, ["ask", "test"])

            assert result.exit_code == 1
            assert "Query failed" in result.output
```

### Previous Story Intelligence

**From Story 8.4 (Error Cascade):**
- Error cascade is handled INSIDE agents via `LLMClient.complete_with_cascade()`
- CLI commands don't need to call cascade directly - agents already handle it
- If an agent returns `PartialResult`, check with `isinstance(result, PartialResult)`

**From Story 8.3 (Batch Import):**
- CLI pattern: `@run_async` decorator wraps async functions for Typer
- Rich output: `print_success`, `print_error`, `print_info`, `print_warning`, `print_panel`
- Exit codes: `EXIT_SUCCESS=0`, `EXIT_ERROR=1`, `EXIT_USAGE_ERROR=2`

**From Story 8.1 (CLI Framework):**
- Entry point: `swealog = "swealog.cli:app"` in pyproject.toml
- Register commands: `app.command()(function_name)`
- Arguments: `Annotated[str, typer.Argument(help="...")]`
- Options: `Annotated[Path | None, typer.Option("--config", "-c", help="...")]`

**From Story 8.2 (FastAPI Endpoints):**
- **CRITICAL:** `execute_query_pipeline()` returns `dict[str, Any]`:
  - `response: str` - The generated response
  - `sources: list[str]` - Entry IDs used
  - `confidence: float` - 0.0 to 1.0
  - `is_partial: bool` - True if data insufficient or eval failed
- `parse_log_background()` shows the parsing pattern - adapt for synchronous CLI use

### Validation Commands

```bash
# During development
make check        # lint + typecheck

# Before completion
make validate     # lint + format + typecheck + test

# Integration testing (requires Ollama)
make test-ollama
```

### References

- `packages/swealog/swealog/cli/app.py` - Base CLI application, add imports and commands here
- `packages/swealog/swealog/cli/utils.py` - Add `get_dependencies()` helper here
- `packages/swealog/swealog/cli/output.py` - Rich output helpers (use as-is)
- `packages/swealog/swealog/api/routes/query.py:47` - `execute_query_pipeline()` to reuse
- `packages/swealog/swealog/api/routes/input.py:28` - `parse_log_background()` pattern reference
- `packages/quilto/quilto/__init__.py` - All Quilto exports (verify imports)

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

N/A

### Completion Notes List

- Implemented `get_dependencies()` helper in `utils.py` to share initialization logic between `log` and `ask` commands
- Created `log_cmd.py` with full routing, parsing, and storage logic for LOG/BOTH/CORRECTION inputs
- Created `ask_cmd.py` reusing `execute_query_pipeline()` from the API routes for consistent behavior
- Both commands support `--config` and `--storage` options for custom paths
- Error handling wraps all operations with user-friendly messages and appropriate exit codes
- Rich output formatting: success messages (green checkmark), panels for responses, info styling for metadata
- 15 unit tests pass (7 for log, 8 for ask) using CliRunner with mocked dependencies
- `make validate` passes (1709 tests passed)
- `make test-ollama` passes (1747 tests passed) - integration tests with real Ollama

### File List

**Created:**
- `packages/swealog/swealog/cli/log_cmd.py`
- `packages/swealog/swealog/cli/ask_cmd.py`
- `packages/swealog/tests/test_cli_log.py`
- `packages/swealog/tests/test_cli_ask.py`

**Modified:**
- `packages/swealog/swealog/cli/utils.py` - Added `get_dependencies()` helper
- `packages/swealog/swealog/cli/app.py` - Imported and registered `log` and `ask` commands
- `packages/swealog/swealog/cli/__init__.py` - Exported `log`, `ask`, and `get_dependencies`

