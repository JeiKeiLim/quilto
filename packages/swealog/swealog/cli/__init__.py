"""CLI framework for Swealog application."""

from swealog.cli.app import app
from swealog.cli.ask_cmd import ask
from swealog.cli.auto_cmd import auto
from swealog.cli.debug import DebugLogger, create_debug_callback
from swealog.cli.feedback import (
    FeedbackRecord,
    FeedbackRecorder,
    IntermediateOutputs,
    SessionMetadata,
    generate_feedback_id,
    get_unique_feedback_path,
)
from swealog.cli.flows import execute_log_flow
from swealog.cli.import_cmd import (
    BatchImporter,
    BatchImportError,
    BatchResult,
    RawEntry,
    collect_import_files,
    import_file,
    parse_import_file,
)
from swealog.cli.log_cmd import log
from swealog.cli.output import (
    console,
    print_error,
    print_info,
    print_panel,
    print_success,
    print_table,
    print_warning,
)
from swealog.cli.utils import (
    EXIT_ERROR,
    EXIT_SUCCESS,
    EXIT_USAGE_ERROR,
    get_dependencies,
    load_cli_config,
    resolve_storage_path,
    run_async,
)

__all__ = [
    "BatchImporter",
    "BatchImportError",
    "BatchResult",
    "DebugLogger",
    "FeedbackRecord",
    "FeedbackRecorder",
    "IntermediateOutputs",
    "SessionMetadata",
    "create_debug_callback",
    "EXIT_ERROR",
    "EXIT_SUCCESS",
    "EXIT_USAGE_ERROR",
    "RawEntry",
    "app",
    "ask",
    "auto",
    "collect_import_files",
    "console",
    "execute_log_flow",
    "generate_feedback_id",
    "get_dependencies",
    "get_unique_feedback_path",
    "import_file",
    "load_cli_config",
    "log",
    "parse_import_file",
    "print_error",
    "print_info",
    "print_panel",
    "print_success",
    "print_table",
    "print_warning",
    "resolve_storage_path",
    "run_async",
]
