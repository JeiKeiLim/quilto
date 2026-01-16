"""CLI import command for batch log operations."""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Annotated

import typer
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
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TaskID,
    TaskProgressColumn,
    TextColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
)
from rich.table import Table

from swealog.cli.output import console, print_error, print_info, print_panel, print_success
from swealog.cli.utils import load_cli_config, resolve_storage_path, run_async
from swealog.domains import general_fitness, nutrition, running, strength, swimming

logger = logging.getLogger(__name__)


@dataclass
class RawEntry:
    """A raw entry parsed from import file."""

    content: str
    source_file: Path
    entry_number: int
    line_start: int


@dataclass
class BatchImportError:
    """Error during batch import."""

    file_path: Path
    entry_number: int
    error_message: str
    content_preview: str


@dataclass
class BatchResult:
    """Result of batch import operation."""

    total_entries: int
    successful: int
    failed: int
    errors: list["BatchImportError"] = field(default_factory=lambda: [])
    dry_run: bool = False


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
            delimiter = "\n\n"
        else:
            # Single entry file (no delimiters found)
            stripped = content.strip()
            if stripped:
                return [RawEntry(content=stripped, source_file=file_path, entry_number=1, line_start=1)]
            return []

    # Split by delimiter
    entries: list[RawEntry] = []
    parts = content.split("\n---\n") if delimiter == "---" else content.split(delimiter)

    line_num = 1
    for i, part in enumerate(parts, 1):
        stripped = part.strip()
        if stripped:
            entries.append(
                RawEntry(
                    content=stripped,
                    source_file=file_path,
                    entry_number=i,
                    line_start=line_num,
                )
            )
        # Track line numbers for next entry
        if delimiter == "---":
            line_num += part.count("\n") + 2  # +2 for \n---\n
        else:
            line_num += part.count("\n") + delimiter.count("\n")

    return entries


def collect_import_files(path: Path) -> list[Path]:
    """Collect files to import from a path.

    Args:
        path: File or directory path.

    Returns:
        List of file paths sorted chronologically.
    """
    if path.is_file():
        return [path]

    # Collect .txt and .md files recursively
    txt_files = list(path.rglob("*.txt"))
    md_files = list(path.rglob("*.md"))
    all_files = txt_files + md_files

    # Sort by modification time for chronological order
    return sorted(all_files, key=lambda f: f.stat().st_mtime)


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

    async def import_entry(self, entry: RawEntry, entry_id: str) -> BatchImportError | None:
        """Import a single entry.

        Args:
            entry: Raw entry to import.
            entry_id: Unique ID for this entry.

        Returns:
            BatchImportError if failed, None if successful.
        """
        try:
            # Route the entry
            router = RouterAgent(self.llm_client)
            domain_infos = [DomainInfo(name=d.name, description=d.description) for d in self.domains]
            router_input = RouterInput(raw_input=entry.content, available_domains=domain_infos)
            router_output = await router.classify(router_input)

            # Skip QUERY-only entries (not loggable)
            # Handle LOG, BOTH, and CORRECTION types (same as /input API)
            if router_output.input_type.value == "QUERY":
                return None  # Skip silently - queries don't create log entries, not an error

            # Filter domains to those selected by Router
            selected_domains = [d for d in self.domains if d.name in router_output.selected_domains]
            if not selected_domains:
                selected_domains = self.domains

            # Build domain schemas and vocabulary
            domain_schemas = {d.name: d.log_schema for d in selected_domains}
            vocabulary: dict[str, str] = {}
            for d in selected_domains:
                vocabulary.update(d.vocabulary)

            # Parse using entry_id timestamp (strip counter suffix if present)
            base_timestamp = entry_id.split("-", 3)[:3]  # Get YYYY-MM-DD part
            time_part = entry_id.split("_")[1].split("-")[0:3]  # Get HH-MM-SS part
            timestamp_str = "-".join(base_timestamp) + "_" + "-".join(time_part)
            timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d_%H-%M-%S")

            # Handle CORRECTION type (same as /input API)
            is_correction = router_output.input_type.value == "CORRECTION"
            recent_entries: list[Entry] = []
            if is_correction:
                recent_entries = self.storage.get_entries_by_pattern("**/*.md")[-10:]

            parser = ParserAgent(self.llm_client)
            parser_input = ParserInput(
                raw_input=entry.content,
                timestamp=timestamp,
                domain_schemas=domain_schemas,
                vocabulary=vocabulary,
                correction_mode=is_correction,
                correction_target=router_output.correction_target,
                recent_entries=recent_entries,
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
                # Handle correction save (same as /input API)
                if is_correction and parser_output.is_correction:
                    self.storage.save_entry(storage_entry, correction=parser_output)
                else:
                    self.storage.save_entry(storage_entry)

            return None

        except Exception as e:
            content_preview = entry.content[:100] + "..." if len(entry.content) > 100 else entry.content
            return BatchImportError(
                file_path=entry.source_file,
                entry_number=entry.entry_number,
                error_message=str(e),
                content_preview=content_preview,
            )

    async def import_entries(
        self,
        entries: list[RawEntry],
        progress: Progress,
        task_id: TaskID,
    ) -> BatchResult:
        """Import a list of raw entries.

        Args:
            entries: List of RawEntry objects to import.
            progress: Rich Progress instance for updates.
            task_id: Task ID for progress updates.

        Returns:
            BatchResult with statistics and errors.
        """
        result = BatchResult(total_entries=len(entries), successful=0, failed=0, dry_run=self.dry_run)

        for i, entry in enumerate(entries):
            progress.update(task_id, completed=i, description=f"[cyan]{entry.source_file.name}[/cyan]")

            # Generate unique entry_id with counter suffix to avoid collisions in batch
            base_id = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            entry_id = f"{base_id}-{i:04d}"

            error = await self.import_entry(entry, entry_id)
            if error:
                result.failed += 1
                result.errors.append(error)
            else:
                result.successful += 1

        progress.update(task_id, completed=len(entries))
        return result


def display_errors(errors: list[BatchImportError], error_log: Path | None) -> None:
    """Display import errors in table format.

    Args:
        errors: List of BatchImportError objects.
        error_log: Optional path to write errors to file.
    """
    if not errors:
        return

    table = Table(title="Import Errors")
    table.add_column("File", style="cyan")
    table.add_column("Entry #", style="yellow")
    table.add_column("Error", style="red")
    table.add_column("Preview", style="dim")

    for err in errors:
        table.add_row(
            err.file_path.name,
            str(err.entry_number),
            err.error_message[:50] + "..." if len(err.error_message) > 50 else err.error_message,
            err.content_preview[:30] + "..." if len(err.content_preview) > 30 else err.content_preview,
        )

    console.print(table)

    # Write to error log if specified
    if error_log:
        with error_log.open("w", encoding="utf-8") as f:
            for err in errors:
                f.write(f"=== {err.file_path}:{err.entry_number} ===\n")
                f.write(f"Error: {err.error_message}\n")
                f.write(f"Content:\n{err.content_preview}\n\n")
        print_info(f"Error details written to {error_log}")


@run_async
async def import_file(
    path: Annotated[Path, typer.Argument(help="File or directory to import")],
    dry_run: Annotated[bool, typer.Option("--dry-run", "-n", help="Preview import without saving")] = False,
    delimiter: Annotated[
        str | None, typer.Option("--delimiter", "-d", help="Entry delimiter (default: auto-detect)")
    ] = None,
    error_log: Annotated[Path | None, typer.Option("--error-log", help="Path to write error details")] = None,
    verbose: Annotated[bool, typer.Option("--verbose", "-v", help="Show detailed progress per entry")] = False,
) -> None:
    """Import log entries from file or directory.

    Processes fitness log entries through the Router → Parser pipeline and
    saves them to storage. Supports batch import from multiple files.

    Examples:
        swealog import logs.txt
        swealog import ./historical/ --dry-run
        swealog import workout.md --delimiter "---"
    """
    # Validate path exists
    if not path.exists():
        print_error(f"Path not found: {path}")
        raise typer.Exit(1)

    # Collect files to process
    files = collect_import_files(path)
    if not files:
        print_error("No .txt or .md files found to import")
        raise typer.Exit(1)

    if verbose:
        print_info(f"Found {len(files)} file(s) to process")

    # Parse all entries from all files
    entries: list[RawEntry] = []
    for file_path in files:
        file_entries = parse_import_file(file_path, delimiter)
        entries.extend(file_entries)
        if verbose:
            print_info(f"  {file_path.name}: {len(file_entries)} entries")

    if not entries:
        print_error("No entries found to import")
        raise typer.Exit(1)

    print_info(f"Found {len(entries)} entries to import from {len(files)} file(s)")

    if dry_run:
        print_info("[yellow]DRY RUN MODE - no entries will be saved[/yellow]")

    # Initialize importer
    config = load_cli_config()
    llm_client = LLMClient(config)
    storage = StorageRepository(resolve_storage_path())
    domains: list[DomainModule] = [general_fitness, strength, nutrition, running, swimming]

    importer = BatchImporter(llm_client, storage, domains, dry_run)

    # Run import with progress bar
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        TimeElapsedColumn(),
        TimeRemainingColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("Starting...", total=len(entries))
        result = await importer.import_entries(entries, progress, task)

    # Display results
    if result.dry_run:
        print_panel(
            f"[bold]Dry Run Complete[/bold]\n\n"
            f"Would import: [green]{result.successful}[/green] entries\n"
            f"Would fail: [red]{result.failed}[/red] entries",
            title="Import Preview",
        )
    else:
        if result.failed == 0:
            print_success(f"Imported {result.successful} entries successfully")
        else:
            print_panel(
                f"[bold]Import Complete[/bold]\n\n"
                f"Successful: [green]{result.successful}[/green]\n"
                f"Failed: [red]{result.failed}[/red]",
                title="Import Results",
            )

    # Display errors if any
    display_errors(result.errors, error_log)

    if result.failed > 0 and not dry_run:
        raise typer.Exit(1)
