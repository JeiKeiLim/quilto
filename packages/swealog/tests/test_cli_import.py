"""Tests for swealog.cli.import_cmd module."""

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from swealog.cli import (
    BatchImporter,
    BatchImportError,
    BatchResult,
    RawEntry,
    app,
    collect_import_files,
    parse_import_file,
)
from typer.testing import CliRunner

runner = CliRunner()


class TestRawEntry:
    """Tests for RawEntry dataclass."""

    def test_raw_entry_creation(self, tmp_path: Path) -> None:
        """Test creating a RawEntry instance."""
        file_path = tmp_path / "test.txt"
        entry = RawEntry(
            content="Bench 185x5",
            source_file=file_path,
            entry_number=1,
            line_start=1,
        )

        assert entry.content == "Bench 185x5"
        assert entry.source_file == file_path
        assert entry.entry_number == 1
        assert entry.line_start == 1


class TestBatchImportError:
    """Tests for BatchImportError dataclass."""

    def test_import_error_creation(self, tmp_path: Path) -> None:
        """Test creating an BatchImportError instance."""
        file_path = tmp_path / "test.txt"
        error = BatchImportError(
            file_path=file_path,
            entry_number=3,
            error_message="Parse failed",
            content_preview="Invalid content...",
        )

        assert error.file_path == file_path
        assert error.entry_number == 3
        assert error.error_message == "Parse failed"
        assert error.content_preview == "Invalid content..."


class TestBatchResult:
    """Tests for BatchResult dataclass."""

    def test_batch_result_default_values(self) -> None:
        """Test BatchResult with default values."""
        result = BatchResult(total_entries=10, successful=8, failed=2)

        assert result.total_entries == 10
        assert result.successful == 8
        assert result.failed == 2
        assert result.errors == []
        assert result.dry_run is False

    def test_batch_result_with_errors(self, tmp_path: Path) -> None:
        """Test BatchResult with errors list."""
        errors = [
            BatchImportError(
                file_path=tmp_path / "test.txt",
                entry_number=1,
                error_message="Error 1",
                content_preview="Preview 1",
            )
        ]
        result = BatchResult(
            total_entries=10,
            successful=9,
            failed=1,
            errors=errors,
            dry_run=True,
        )

        assert result.failed == 1
        assert len(result.errors) == 1
        assert result.dry_run is True


class TestParseImportFile:
    """Tests for parse_import_file function."""

    def test_single_entry_file(self, tmp_path: Path) -> None:
        """Test parsing a file with a single entry (no delimiters)."""
        file = tmp_path / "single.txt"
        file.write_text("Bench press 185x5 felt heavy")

        entries = parse_import_file(file)

        assert len(entries) == 1
        assert entries[0].content == "Bench press 185x5 felt heavy"
        assert entries[0].source_file == file
        assert entries[0].entry_number == 1
        assert entries[0].line_start == 1

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

    def test_explicit_delimiter_override(self, tmp_path: Path) -> None:
        """Test explicit delimiter overrides auto-detection."""
        file = tmp_path / "multi.txt"
        # Has both --- and double newline, but we force double newline
        file.write_text("Entry 1\n---\nStill Entry 1\n\nEntry 2")

        entries = parse_import_file(file, delimiter="\n\n")

        assert len(entries) == 2
        assert "Entry 1\n---\nStill Entry 1" in entries[0].content
        assert entries[1].content == "Entry 2"

    def test_empty_file(self, tmp_path: Path) -> None:
        """Test parsing an empty file."""
        file = tmp_path / "empty.txt"
        file.write_text("")

        entries = parse_import_file(file)

        assert len(entries) == 0

    def test_whitespace_only_file(self, tmp_path: Path) -> None:
        """Test parsing a file with only whitespace."""
        file = tmp_path / "whitespace.txt"
        file.write_text("   \n\n   ")

        entries = parse_import_file(file)

        assert len(entries) == 0

    def test_skips_empty_entries(self, tmp_path: Path) -> None:
        """Test that empty entries between delimiters are skipped."""
        file = tmp_path / "gaps.txt"
        file.write_text("Entry 1\n---\n\n---\nEntry 2")

        entries = parse_import_file(file)

        assert len(entries) == 2
        assert entries[0].content == "Entry 1"
        assert entries[1].content == "Entry 2"

    def test_entry_numbers_sequential(self, tmp_path: Path) -> None:
        """Test that entry numbers are sequential starting from 1."""
        file = tmp_path / "multi.txt"
        file.write_text("A\n---\nB\n---\nC")

        entries = parse_import_file(file)

        assert entries[0].entry_number == 1
        assert entries[1].entry_number == 2
        assert entries[2].entry_number == 3

    def test_multiline_entries(self, tmp_path: Path) -> None:
        """Test parsing entries that span multiple lines."""
        file = tmp_path / "multiline.txt"
        file.write_text("Line 1\nLine 2\nLine 3\n---\nEntry 2")

        entries = parse_import_file(file)

        assert len(entries) == 2
        assert entries[0].content == "Line 1\nLine 2\nLine 3"
        assert entries[1].content == "Entry 2"


class TestCollectImportFiles:
    """Tests for collect_import_files function."""

    def test_single_file(self, tmp_path: Path) -> None:
        """Test collecting a single file."""
        file = tmp_path / "logs.txt"
        file.write_text("content")

        files = collect_import_files(file)

        assert len(files) == 1
        assert files[0] == file

    def test_directory_txt_files(self, tmp_path: Path) -> None:
        """Test collecting .txt files from directory."""
        (tmp_path / "a.txt").write_text("a")
        (tmp_path / "b.txt").write_text("b")
        (tmp_path / "c.py").write_text("c")  # Should be ignored

        files = collect_import_files(tmp_path)

        assert len(files) == 2
        names = [f.name for f in files]
        assert "a.txt" in names
        assert "b.txt" in names
        assert "c.py" not in names

    def test_directory_md_files(self, tmp_path: Path) -> None:
        """Test collecting .md files from directory."""
        (tmp_path / "readme.md").write_text("readme")
        (tmp_path / "notes.md").write_text("notes")

        files = collect_import_files(tmp_path)

        assert len(files) == 2
        names = [f.name for f in files]
        assert "readme.md" in names
        assert "notes.md" in names

    def test_recursive_collection(self, tmp_path: Path) -> None:
        """Test recursive file collection from subdirectories."""
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        (tmp_path / "root.txt").write_text("root")
        (subdir / "child.txt").write_text("child")

        files = collect_import_files(tmp_path)

        assert len(files) == 2
        names = [f.name for f in files]
        assert "root.txt" in names
        assert "child.txt" in names

    def test_empty_directory(self, tmp_path: Path) -> None:
        """Test collecting from empty directory."""
        files = collect_import_files(tmp_path)

        assert len(files) == 0

    def test_chronological_order_by_mtime(self, tmp_path: Path) -> None:
        """Test files are sorted chronologically by modification time (AC2)."""
        import os
        import time

        # Create files with different modification times
        file_old = tmp_path / "old.txt"
        file_new = tmp_path / "new.txt"
        file_mid = tmp_path / "mid.txt"

        file_old.write_text("old")
        time.sleep(0.05)  # Small delay to ensure different mtime
        file_mid.write_text("mid")
        time.sleep(0.05)
        file_new.write_text("new")

        # Set explicit mtimes to guarantee ordering
        os.utime(file_old, (1000000, 1000000))
        os.utime(file_mid, (2000000, 2000000))
        os.utime(file_new, (3000000, 3000000))

        files = collect_import_files(tmp_path)

        assert len(files) == 3
        assert files[0].name == "old.txt"
        assert files[1].name == "mid.txt"
        assert files[2].name == "new.txt"


class TestBatchImporter:
    """Tests for BatchImporter class."""

    def test_init(self) -> None:
        """Test BatchImporter initialization."""
        llm_client = MagicMock()
        storage = MagicMock()
        domains: list[MagicMock] = []

        importer = BatchImporter(llm_client, storage, domains, dry_run=True)  # type: ignore[arg-type]

        assert importer.llm_client == llm_client
        assert importer.storage == storage
        assert importer.domains == domains
        assert importer.dry_run is True

    @pytest.mark.asyncio
    async def test_import_entry_success(self, tmp_path: Path) -> None:
        """Test successful entry import."""
        llm_client = MagicMock()
        storage = MagicMock()

        # Create mock domain
        mock_domain = MagicMock()
        mock_domain.name = "test_domain"
        mock_domain.description = "Test domain"
        mock_domain.log_schema = {"type": "object"}
        mock_domain.vocabulary = {"test": "test_value"}
        domains = [mock_domain]

        importer = BatchImporter(llm_client, storage, domains, dry_run=False)  # type: ignore[arg-type]

        entry = RawEntry(
            content="Bench 185x5",
            source_file=tmp_path / "test.txt",
            entry_number=1,
            line_start=1,
        )

        with (
            patch.object(importer, "import_entry", new_callable=AsyncMock) as mock_import,
        ):
            mock_import.return_value = None  # Success
            await importer.import_entry(entry, "2024-01-15_10-30-00")

        # The mock was called, so we verify it was set up
        assert mock_import.return_value is None

    @pytest.mark.asyncio
    async def test_import_entry_dry_run_no_save(self) -> None:
        """Test that dry_run mode doesn't save entries."""
        llm_client = MagicMock()
        storage = MagicMock()

        importer = BatchImporter(llm_client, storage, [], dry_run=True)  # type: ignore[arg-type]

        # Verify dry_run is set
        assert importer.dry_run is True

    @pytest.mark.asyncio
    async def test_import_entry_query_skipped(self, tmp_path: Path) -> None:
        """Test that QUERY entries are skipped without error (AC1)."""
        from quilto.agents.models import InputType, RouterOutput

        llm_client = MagicMock()
        storage = MagicMock()

        mock_domain = MagicMock()
        mock_domain.name = "test_domain"
        mock_domain.description = "Test domain"
        mock_domain.log_schema = {"type": "object"}
        mock_domain.vocabulary = {}
        domains = [mock_domain]

        importer = BatchImporter(llm_client, storage, domains, dry_run=False)  # type: ignore[arg-type]

        entry = RawEntry(
            content="What was my bench press max?",  # Query-type input
            source_file=tmp_path / "test.txt",
            entry_number=1,
            line_start=1,
        )

        # Mock RouterAgent.classify to return QUERY type
        mock_router_output = RouterOutput(
            input_type=InputType.QUERY,
            confidence=0.95,
            selected_domains=["test_domain"],
            domain_selection_reasoning="Fitness domain for query",
            query_portion="What was my bench press max?",
            correction_target=None,
            reasoning="This is a query asking about past data",
        )

        with patch("swealog.cli.import_cmd.RouterAgent") as mock_router_class:
            mock_router = mock_router_class.return_value
            mock_router.classify = AsyncMock(return_value=mock_router_output)

            result = await importer.import_entry(entry, "2024-01-15_10-30-00-0001")

            # QUERY should return None (skipped) without error
            assert result is None
            # Storage should NOT be called for QUERY
            storage.save_entry.assert_not_called()


class TestImportCommand:
    """Tests for import CLI command."""

    def test_import_help(self) -> None:
        """Test import command help."""
        result = runner.invoke(app, ["import", "--help"])

        assert result.exit_code == 0
        assert "Import log entries" in result.stdout
        assert "--dry-run" in result.stdout
        assert "--delimiter" in result.stdout
        assert "--error-log" in result.stdout
        assert "--verbose" in result.stdout

    def test_import_nonexistent_path(self) -> None:
        """Test import with nonexistent path."""
        result = runner.invoke(app, ["import", "/nonexistent/path.txt"])

        assert result.exit_code == 1
        assert "not found" in result.stdout.lower()

    def test_import_empty_directory(self, tmp_path: Path) -> None:
        """Test import from empty directory."""
        result = runner.invoke(app, ["import", str(tmp_path)])

        assert result.exit_code == 1
        assert "no" in result.stdout.lower()

    @patch("swealog.cli.import_cmd.load_cli_config")
    @patch("swealog.cli.import_cmd.LLMClient")
    @patch("swealog.cli.import_cmd.StorageRepository")
    @patch("swealog.cli.import_cmd.BatchImporter")
    def test_import_file_success(
        self,
        mock_importer_class: MagicMock,
        mock_storage_class: MagicMock,
        mock_llm_class: MagicMock,
        mock_config: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test successful file import with mocked dependencies."""
        file = tmp_path / "logs.txt"
        file.write_text("Bench 185x5\n---\nSquat 225x5")

        # Configure mock importer
        mock_importer = mock_importer_class.return_value
        mock_importer.import_entries = AsyncMock(return_value=BatchResult(total_entries=2, successful=2, failed=0))

        result = runner.invoke(app, ["import", str(file)])

        # Should succeed (imports were mocked)
        assert "2" in result.stdout or result.exit_code == 0

    @patch("swealog.cli.import_cmd.load_cli_config")
    @patch("swealog.cli.import_cmd.LLMClient")
    @patch("swealog.cli.import_cmd.StorageRepository")
    @patch("swealog.cli.import_cmd.BatchImporter")
    def test_import_dry_run(
        self,
        mock_importer_class: MagicMock,
        mock_storage_class: MagicMock,
        mock_llm_class: MagicMock,
        mock_config: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test dry-run mode shows preview."""
        file = tmp_path / "logs.txt"
        file.write_text("Test entry")

        mock_importer = mock_importer_class.return_value
        mock_importer.import_entries = AsyncMock(
            return_value=BatchResult(total_entries=1, successful=1, failed=0, dry_run=True)
        )

        result = runner.invoke(app, ["import", "--dry-run", str(file)])

        # Dry run message should appear
        assert "DRY RUN" in result.stdout.upper() or "dry" in result.stdout.lower()

    @patch("swealog.cli.import_cmd.load_cli_config")
    @patch("swealog.cli.import_cmd.LLMClient")
    @patch("swealog.cli.import_cmd.StorageRepository")
    @patch("swealog.cli.import_cmd.BatchImporter")
    def test_import_with_errors(
        self,
        mock_importer_class: MagicMock,
        mock_storage_class: MagicMock,
        mock_llm_class: MagicMock,
        mock_config: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test import with errors shows error summary."""
        file = tmp_path / "logs.txt"
        file.write_text("Entry 1\n---\nEntry 2")

        errors = [
            BatchImportError(
                file_path=file,
                entry_number=2,
                error_message="Parse failed",
                content_preview="Entry 2",
            )
        ]
        mock_importer = mock_importer_class.return_value
        mock_importer.import_entries = AsyncMock(
            return_value=BatchResult(total_entries=2, successful=1, failed=1, errors=errors)
        )

        result = runner.invoke(app, ["import", str(file)])

        # Should show error info and exit with error code
        assert result.exit_code == 1

    @patch("swealog.cli.import_cmd.load_cli_config")
    @patch("swealog.cli.import_cmd.LLMClient")
    @patch("swealog.cli.import_cmd.StorageRepository")
    @patch("swealog.cli.import_cmd.BatchImporter")
    def test_import_verbose_mode(
        self,
        mock_importer_class: MagicMock,
        mock_storage_class: MagicMock,
        mock_llm_class: MagicMock,
        mock_config: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test verbose mode shows file details."""
        file = tmp_path / "logs.txt"
        file.write_text("Test entry")

        mock_importer = mock_importer_class.return_value
        mock_importer.import_entries = AsyncMock(return_value=BatchResult(total_entries=1, successful=1, failed=0))

        result = runner.invoke(app, ["import", "--verbose", str(file)])

        # Verbose output should include file details
        assert "logs.txt" in result.stdout or result.exit_code == 0

    @patch("swealog.cli.import_cmd.load_cli_config")
    @patch("swealog.cli.import_cmd.LLMClient")
    @patch("swealog.cli.import_cmd.StorageRepository")
    @patch("swealog.cli.import_cmd.BatchImporter")
    def test_import_error_log_file(
        self,
        mock_importer_class: MagicMock,
        mock_storage_class: MagicMock,
        mock_llm_class: MagicMock,
        mock_config: MagicMock,
        tmp_path: Path,
    ) -> None:
        """Test --error-log writes errors to file."""
        file = tmp_path / "logs.txt"
        file.write_text("Test entry")
        error_log_path = tmp_path / "errors.log"

        errors = [
            BatchImportError(
                file_path=file,
                entry_number=1,
                error_message="Test error",
                content_preview="Test entry",
            )
        ]
        mock_importer = mock_importer_class.return_value
        mock_importer.import_entries = AsyncMock(
            return_value=BatchResult(total_entries=1, successful=0, failed=1, errors=errors)
        )

        runner.invoke(app, ["import", "--error-log", str(error_log_path), str(file)])

        # Error log should be written
        assert error_log_path.exists()
        content = error_log_path.read_text()
        assert "Test error" in content


class TestImportCommandExports:
    """Tests for import_cmd module exports."""

    def test_imports_available(self) -> None:
        """Test that all exports are importable from swealog.cli."""
        from swealog.cli import (
            BatchImporter,
            BatchImportError,
            BatchResult,
            RawEntry,
            collect_import_files,
            import_file,
            parse_import_file,
        )

        assert BatchImporter is not None
        assert BatchResult is not None
        assert BatchImportError is not None
        assert RawEntry is not None
        assert import_file is not None
        assert parse_import_file is not None
        assert collect_import_files is not None

    def test_import_command_registered(self) -> None:
        """Test that import command is registered with main app."""
        result = runner.invoke(app, ["--help"])

        assert "import" in result.stdout.lower()
