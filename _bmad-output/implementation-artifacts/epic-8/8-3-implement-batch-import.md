# Story 8.3: Implement Batch Import

Status: done

## Story

As a **Swealog user**,
I want a **CLI import command for batch operations**,
So that **I can import historical fitness logs efficiently**.

## Acceptance Criteria

1. **AC1: Import Command Basic Functionality**
   - Given a text file with multiple log entries
   - When `swealog import <file>` is run
   - Then each entry is processed through the Router → Parser pipeline (same as `/input` API)
   - And progress is displayed with entry count/total
   - And final summary shows successful/failed entries

2. **AC2: Directory Import Support**
   - Given a directory containing log files
   - When `swealog import <directory>` is run
   - Then all `.txt` and `.md` files are processed recursively
   - And files are processed in chronological order (by filename or modification time)
   - And a summary shows total files processed

3. **AC3: Entry Delimiter Support**
   - Given a file with multiple entries
   - When entries are separated by `---` or double newlines
   - Then each delimited section is treated as a separate entry
   - And single-entry files (no delimiters) are processed as one entry

4. **AC4: Error Collection and Reporting**
   - Given errors during batch import
   - When processing completes
   - Then errors are collected (not raised immediately)
   - And all errors are reported at the end with entry context
   - And successful entries continue processing despite errors

5. **AC5: Dry-Run Mode**
   - Given the `--dry-run` flag
   - When `swealog import --dry-run <path>` is run
   - Then entries are parsed and validated but not saved
   - And output shows what would be imported
   - And no changes are made to storage

6. **AC6: Progress Display**
   - Given batch import in progress
   - When processing entries
   - Then rich progress bar shows current progress
   - And current file/entry being processed is displayed
   - And ETA is shown for large imports

## Tasks / Subtasks

- [x] Task 1: Create import command structure (AC: 1, 2)
  - [x] Add `import_cmd.py` module in `packages/swealog/swealog/cli/`
  - [x] Create `import` command accepting file or directory path
  - [x] Register import command with main app in `app.py`
  - [x] Export import command in `cli/__init__.py`

- [x] Task 2: Implement file/directory detection (AC: 1, 2)
  - [x] Detect if path is file or directory
  - [x] For files: validate file exists and is readable
  - [x] For directories: recursively find all `.txt` and `.md` files
  - [x] Sort files chronologically (parse date from filename or use mtime)
  - [x] Create `ImportSource` model with file path and detected entry count

- [x] Task 3: Implement entry parsing from files (AC: 3)
  - [x] Create `parse_import_file()` function
  - [x] Support `---` delimiter between entries
  - [x] Support double newline (`\n\n`) delimiter as fallback
  - [x] Handle single-entry files (no delimiters)
  - [x] Return list of `RawEntry` objects with content and source info

- [x] Task 4: Implement batch processor (AC: 1, 4)
  - [x] Create `BatchImporter` class with async processing
  - [x] Process entries through existing `/input` pipeline (reuse API logic)
  - [x] Use `RouterAgent` and `ParserAgent` from quilto
  - [x] Collect errors without stopping processing
  - [x] Track successful/failed entry counts
  - [x] Return `BatchResult` with stats and error list

- [x] Task 5: Implement progress display (AC: 6)
  - [x] Use `rich.progress.Progress` for progress bar
  - [x] Show: completed/total entries, current file, elapsed time, ETA
  - [x] Use `print_info()`, `print_success()`, `print_error()` from output.py
  - [x] Display final summary panel with statistics

- [x] Task 6: Implement dry-run mode (AC: 5)
  - [x] Add `--dry-run` flag to import command
  - [x] Skip `storage.save_entry()` calls in dry-run mode
  - [x] Still run Router and Parser for validation
  - [x] Show preview of what would be imported

- [x] Task 7: Implement error reporting (AC: 4)
  - [x] Create `BatchImportError` dataclass with entry context
  - [x] Store file path, entry number, error message, raw content preview
  - [x] Display errors in table format at end of import
  - [x] Optionally write errors to log file with `--error-log` flag

- [x] Task 8: Add CLI options and help (AC: 1-6)
  - [x] `--dry-run`: Preview import without saving
  - [x] `--delimiter`: Override entry delimiter (default: auto-detect)
  - [x] `--error-log`: Path to write error details
  - [x] `--verbose`: Show detailed progress per entry
  - [x] Update help text with examples and usage

- [x] Task 9: Write unit tests (AC: 1-6)
  - [x] Create `packages/swealog/tests/test_cli_import.py`
  - [x] Test single file import with mocked agents
  - [x] Test directory import with multiple files
  - [x] Test delimiter parsing (---, double newlines, none)
  - [x] Test error collection and reporting
  - [x] Test dry-run mode (verify no storage calls)
  - [x] Test progress display with captured output
  - [x] Use `typer.testing.CliRunner` for command invocation
  - [x] Comprehensive coverage of all 6 acceptance criteria

## Dev Notes

### Project Identity (CRITICAL)

This story adds import functionality to **Swealog** (the application), NOT Quilto. Following the pattern established in Stories 8.1 and 8.2.

**Quilto provides:** Agents (RouterAgent, ParserAgent), LLM client abstraction, storage interface, DomainModule
**Swealog provides:** CLI commands (import, serve), API endpoints, fitness domains, user-facing features

### Architecture Compliance

**File Location:** `packages/swealog/swealog/cli/import_cmd.py`

**Module Structure (matches existing Story 8.1 structure):**
```
swealog/cli/
├── __init__.py       # Exports: app, output helpers, utilities, import_file
├── app.py            # Main Typer app + serve command + import command registration
├── output.py         # Rich output helpers
├── utils.py          # Async helpers, config loading
└── import_cmd.py     # Import command implementation (NEW)
```

### Dependencies (already available)

From swealog pyproject.toml (Story 8.1):
- `typer>=0.15.0` - CLI framework
- `rich>=13.9.0` - Progress bar, tables, panels
- `quilto` - Agents, storage, domain modules

No new dependencies required.

### Code Patterns

**Import Command (import_cmd.py):**
```python
"""CLI import command for batch log operations."""

import logging
from pathlib import Path
from typing import Annotated

import typer
from rich.progress import (
    Progress,
    SpinnerColumn,
    TextColumn,
    BarColumn,
    TaskProgressColumn,
    TimeElapsedColumn,
)

from swealog.cli.output import console, print_error, print_info, print_success, print_panel
from swealog.cli.utils import run_async, load_cli_config, resolve_storage_path

logger = logging.getLogger(__name__)


@run_async
async def import_command(
    path: Annotated[Path, typer.Argument(help="File or directory to import")],
    dry_run: bool = typer.Option(False, "--dry-run", "-n", help="Preview without saving"),
    delimiter: str | None = typer.Option(None, "--delimiter", "-d", help="Entry delimiter"),
    error_log: Path | None = typer.Option(None, "--error-log", help="Write errors to file"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output"),
) -> None:
    """Import log entries from file or directory.

    Examples:
        swealog import logs.txt
        swealog import ./historical/ --dry-run
        swealog import workout.md --delimiter "---"
    """
    # Implementation here
```

**Registering in app.py:**
```python
from swealog.cli.import_cmd import import_command

# Register import command directly (not as subcommand group)
app.command(name="import")(import_command)
```

**Entry Parsing:**
```python
from dataclasses import dataclass


@dataclass
class RawEntry:
    """A raw entry parsed from import file."""
    content: str
    source_file: Path
    entry_number: int
    line_start: int


def parse_import_file(file_path: Path, delimiter: str | None = None) -> list[RawEntry]:
    """Parse a file into individual entries.

    Args:
        file_path: Path to the file to parse.
        delimiter: Entry delimiter (None for auto-detect).

    Returns:
        List of RawEntry objects.
    """
    content = file_path.read_text(encoding="utf-8")

    # Auto-detect delimiter if not specified
    if delimiter is None:
        if "\n---\n" in content:
            delimiter = "---"
        elif "\n\n" in content:
            # Double newline delimiter
            delimiter = "\n\n"
        else:
            # Single entry file (no delimiters found)
            return [RawEntry(content=content.strip(), source_file=file_path, entry_number=1, line_start=1)]

    # Split by delimiter
    entries = []
    if delimiter == "---":
        parts = content.split("\n---\n")
    else:
        parts = content.split(delimiter)

    line_num = 1
    for i, part in enumerate(parts, 1):
        stripped = part.strip()
        if stripped:
            entries.append(RawEntry(
                content=stripped,
                source_file=file_path,
                entry_number=i,
                line_start=line_num,
            ))
        line_num += part.count("\n") + len(delimiter.split("\n"))  # Account for delimiter lines

    return entries
```

**Batch Processor:**
```python
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime

from quilto import (
    DomainModule,
    Entry,
    LLMClient,
    ParserAgent,
    ParserInput,
    RouterAgent,
    RouterInput,
    StorageRepository,
)
from quilto.agents import DomainInfo


@dataclass
class ImportError:
    """Error during batch import."""
    file_path: Path
    entry_number: int
    error_message: str
    content_preview: str  # First 100 chars


@dataclass
class BatchResult:
    """Result of batch import operation."""
    total_entries: int
    successful: int
    failed: int
    errors: list[ImportError] = field(default_factory=list)
    dry_run: bool = False


class BatchImporter:
    """Batch importer for log entries."""

    def __init__(
        self,
        llm_client: LLMClient,
        storage: StorageRepository,
        domains: list[DomainModule],
        dry_run: bool = False,
    ) -> None:
        """Initialize batch importer.

        Args:
            llm_client: LLM client for Router and Parser agents.
            storage: Storage repository for saving entries.
            domains: Available domain modules for parsing.
            dry_run: If True, validate but don't save entries.
        """
        self.llm_client = llm_client
        self.storage = storage
        self.domains = domains
        self.dry_run = dry_run

    async def import_entries(
        self,
        entries: list[RawEntry],
        progress_callback: Callable[[int, int, str], None] | None = None,
    ) -> BatchResult:
        """Import a list of raw entries.

        Args:
            entries: List of RawEntry objects to import.
            progress_callback: Optional callback(current, total, status).

        Returns:
            BatchResult with statistics and errors.
        """
        result = BatchResult(total_entries=len(entries), successful=0, failed=0, dry_run=self.dry_run)

        router = RouterAgent(self.llm_client)
        parser = ParserAgent(self.llm_client)
        domain_infos = [DomainInfo(name=d.name, description=d.description) for d in self.domains]

        for i, entry in enumerate(entries):
            if progress_callback:
                progress_callback(i + 1, len(entries), f"Processing {entry.source_file.name}")

            try:
                # Route the entry
                router_input = RouterInput(raw_input=entry.content, available_domains=domain_infos)
                router_output = await router.classify(router_input)

                # Parse if LOG or BOTH (skip QUERY-only entries)
                if router_output.input_type.value in ("LOG", "BOTH"):
                    # Filter domains to those selected by Router
                    selected_domains = [d for d in self.domains if d.name in router_output.selected_domains]
                    if not selected_domains:
                        selected_domains = self.domains

                    # Build domain schemas and vocabulary
                    domain_schemas = {d.name: d.log_schema for d in selected_domains}
                    vocabulary: dict[str, str] = {}
                    for d in selected_domains:
                        vocabulary.update(d.vocabulary)

                    # Generate entry_id from timestamp
                    entry_id = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                    timestamp = datetime.now()

                    parser_input = ParserInput(
                        raw_input=entry.content,
                        timestamp=timestamp,
                        domain_schemas=domain_schemas,
                        vocabulary=vocabulary,
                        correction_mode=False,
                        correction_target=None,
                        recent_entries=[],
                    )

                    parser_output = await parser.parse(parser_input)

                    if not self.dry_run:
                        # Create and save entry
                        storage_entry = Entry(
                            id=entry_id,
                            date=parser_output.date,
                            timestamp=parser_output.timestamp,
                            raw_content=entry.content,
                            parsed_data=parser_output.domain_data,
                        )
                        self.storage.save_entry(storage_entry)

                result.successful += 1

            except Exception as e:
                result.failed += 1
                result.errors.append(ImportError(
                    file_path=entry.source_file,
                    entry_number=entry.entry_number,
                    error_message=str(e),
                    content_preview=entry.content[:100] + "..." if len(entry.content) > 100 else entry.content,
                ))

        return result
```

**Progress Display:**
```python
from quilto import LLMClient, StorageRepository
from swealog.domains import general_fitness, strength, nutrition, running, swimming


async def run_import(path: Path, dry_run: bool, delimiter: str | None) -> None:
    """Run the import with progress display.

    Args:
        path: File or directory path to import from.
        dry_run: If True, validate but don't save entries.
        delimiter: Optional entry delimiter (None for auto-detect).
    """
    # Gather all entries
    entries: list[RawEntry] = []
    if path.is_file():
        entries = parse_import_file(path, delimiter)
    else:
        # Process files recursively, sorted for chronological order
        files = sorted(path.rglob("*.txt")) + sorted(path.rglob("*.md"))
        for file_path in files:
            entries.extend(parse_import_file(file_path, delimiter))

    if not entries:
        print_error("No entries found to import")
        raise typer.Exit(1)

    print_info(f"Found {len(entries)} entries to import")

    # Initialize importer using existing CLI utilities
    config = load_cli_config()
    llm_client = LLMClient(config)
    storage = StorageRepository(resolve_storage_path())
    domains = [general_fitness, strength, nutrition, running, swimming]

    importer = BatchImporter(llm_client, storage, domains, dry_run)

    # Run with progress bar
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        TimeElapsedColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("Importing...", total=len(entries))

        def update_progress(current: int, total: int, status: str) -> None:
            progress.update(task, completed=current, description=status)

        result = await importer.import_entries(entries, update_progress)

    # Display results
    if result.dry_run:
        print_panel(
            f"[bold]Dry Run Complete[/bold]\n\n"
            f"Would import: {result.successful} entries\n"
            f"Would fail: {result.failed} entries",
            title="Import Preview"
        )
    else:
        print_panel(
            f"[bold]Import Complete[/bold]\n\n"
            f"Successful: [green]{result.successful}[/green]\n"
            f"Failed: [red]{result.failed}[/red]",
            title="Import Results"
        )

    # Display errors
    if result.errors:
        print_error(f"\n{len(result.errors)} errors occurred:")
        for err in result.errors:
            print_error(f"  {err.file_path}:{err.entry_number} - {err.error_message}")
```

### Testing Patterns

**Test Import Command (test_cli_import.py):**
```python
import pytest
from pathlib import Path
from typer.testing import CliRunner
from unittest.mock import AsyncMock, MagicMock, patch

from swealog.cli import app
from swealog.cli.import_cmd import parse_import_file, RawEntry, BatchResult


runner = CliRunner()


class TestParseImportFile:
    """Tests for entry parsing from files."""

    def test_single_entry_file(self, tmp_path: Path) -> None:
        """Test parsing a file with a single entry."""
        file = tmp_path / "single.txt"
        file.write_text("Bench 185x5 felt heavy")

        entries = parse_import_file(file)

        assert len(entries) == 1
        assert entries[0].content == "Bench 185x5 felt heavy"
        assert entries[0].entry_number == 1

    def test_delimiter_dash(self, tmp_path: Path) -> None:
        """Test parsing entries separated by ---."""
        file = tmp_path / "multi.txt"
        file.write_text("Entry 1\n---\nEntry 2\n---\nEntry 3")

        entries = parse_import_file(file)

        assert len(entries) == 3
        assert entries[0].content == "Entry 1"
        assert entries[1].content == "Entry 2"
        assert entries[2].content == "Entry 3"

    def test_delimiter_double_newline(self, tmp_path: Path) -> None:
        """Test parsing entries separated by double newlines."""
        file = tmp_path / "multi.txt"
        file.write_text("Entry 1\n\nEntry 2\n\nEntry 3")

        entries = parse_import_file(file)

        assert len(entries) == 3
        assert entries[0].content == "Entry 1"
        assert entries[1].content == "Entry 2"
        assert entries[2].content == "Entry 3"


class TestImportCommand:
    """Tests for import CLI command."""

    @patch("swealog.cli.import_cmd.BatchImporter")
    @patch("swealog.cli.import_cmd.load_cli_config")
    def test_import_file_success(self, mock_config: MagicMock, mock_importer: MagicMock, tmp_path: Path) -> None:
        """Test successful file import."""
        file = tmp_path / "logs.txt"
        file.write_text("Bench 185x5\n---\nSquat 225x5")

        # Configure mock
        mock_instance = mock_importer.return_value
        mock_instance.import_entries = AsyncMock(return_value=BatchResult(
            total_entries=2, successful=2, failed=0
        ))

        result = runner.invoke(app, ["import", str(file)])

        assert result.exit_code == 0
        assert "2" in result.output  # 2 entries

    def test_import_dry_run(self, tmp_path: Path) -> None:
        """Test dry-run mode doesn't save entries."""
        file = tmp_path / "logs.txt"
        file.write_text("Test entry")

        # ... mock and verify storage.save_entry not called
```

### Previous Story Intelligence (Stories 8.1 & 8.2)

From Story 8.1 implementation:
- CLI module at `swealog/cli/` with modular structure
- `run_async` decorator for async commands in sync Typer context
- `load_cli_config()` for LLM configuration
- `resolve_storage_path()` for storage directory
- Output helpers: `print_success()`, `print_error()`, `print_info()`, `print_panel()`, `print_table()`
- Entry point in pyproject.toml: `swealog = "swealog.cli:app"`

From Story 8.2 implementation:
- `/input` endpoint logic in `routes/input.py` - reuse the `parse_log_background` pattern
- `RouterAgent` and `ParserAgent` initialization with domain infos
- Entry ID format: `YYYY-MM-DD_HH-MM-SS`
- Storage entry creation via `Entry` model and `storage.save_entry()`
- Error handling pattern with `try/except` collecting errors

### Key Quilto Components to Use

From quilto package (already implemented):
- `RouterAgent`: Input classification (LOG/QUERY/BOTH/CORRECTION)
- `ParserAgent`: Structured data extraction
- `RouterInput`, `ParserInput`: Agent input models
- `DomainInfo`: Domain information for Router
- `Entry`: Storage entry model
- `StorageRepository`: File-based storage

### Reuse from API Routes

The batch import should reuse logic from `routes/input.py:parse_log_background`:
- Router classification
- Domain selection
- Parser invocation
- Entry creation and storage

Consider extracting shared logic into a `process_input()` function that both API and CLI can use.

### File Format Examples

**Single entry file (logs.txt):**
```
Bench press 185x5, felt heavy today. Did 3 sets.
```

**Multi-entry file with --- delimiter:**
```
Bench press 185x5, felt heavy today
---
Squat 225x5, good depth
---
Deadlift 315x3, grip gave out
```

**Multi-entry file with double newline (entries separated by blank line):**
```
Morning workout: bench 185x5

Afternoon run: 5k in 25 minutes

Evening stretching
```

Note: Auto-detection prefers `---` delimiter when present, falls back to double newline.

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

- [Source: _bmad-output/planning-artifacts/epics.md#Story-8.3] - Story requirements
- [Source: _bmad-output/planning-artifacts/architecture.md#CLI-Future-Web] - CLI decision
- [Source: packages/swealog/swealog/cli/app.py] - Existing CLI structure
- [Source: packages/swealog/swealog/api/routes/input.py] - Input processing pattern
- [Source: packages/quilto/quilto/storage/repository.py] - StorageRepository methods
- [Source: _bmad-output/implementation-artifacts/epic-8/8-1-implement-typer-cli-framework.md] - CLI patterns
- [Source: _bmad-output/implementation-artifacts/epic-8/8-2-implement-fastapi-endpoints.md] - Input processing

## Dev Agent Record

### Agent Model Used

Claude Opus 4.5 (claude-opus-4-5-20251101)

### Debug Log References

N/A

### Completion Notes List

- Implemented full batch import functionality for Swealog CLI
- Created `import_cmd.py` with `BatchImporter`, `RawEntry`, `BatchImportError`, `BatchResult` classes
- Entry parsing supports `---` delimiter, double newlines, and single-entry files (auto-detect)
- Directory import recursively collects `.txt` and `.md` files sorted by modification time
- Progress bar shows current file, progress, elapsed time, and ETA using rich.progress
- Dry-run mode validates entries through Router/Parser without saving
- Error collection continues processing despite failures, reports all errors at end
- Errors displayed in table format and optionally written to file via `--error-log`
- All 31 unit tests pass covering: parsing, file collection, command invocation, error handling
- Renamed `ImportError` to `BatchImportError` to avoid shadowing Python builtin

#### Code Review Fixes Applied (2026-01-16)

- **[HIGH] Entry ID Collision Fix**: Added counter suffix (`-NNNN`) to entry_id to prevent collisions in batch processing
- **[HIGH] CORRECTION Type Handling**: Added full CORRECTION input type support matching `/input` API (recent entries lookup, correction_target, save with correction)
- **[HIGH] collect_import_files Export**: Added `collect_import_files` to `__init__.py` exports
- **[MEDIUM] Test: QUERY Skip Behavior**: Added `test_import_entry_query_skipped` verifying QUERY entries are correctly skipped
- **[MEDIUM] Test: Chronological Sort Order**: Added `test_chronological_order_by_mtime` verifying AC2 file ordering

### File List

- `packages/swealog/swealog/cli/import_cmd.py` (NEW) - Import command implementation
- `packages/swealog/swealog/cli/app.py` (MODIFIED) - Register import command
- `packages/swealog/swealog/cli/__init__.py` (MODIFIED) - Export import_cmd classes and collect_import_files
- `packages/swealog/tests/test_cli_import.py` (NEW) - 33 unit tests for import functionality
