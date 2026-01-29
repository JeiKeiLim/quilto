"""Base Typer application for Swealog CLI.

Single unified command delegates to Quilto for all input processing:
- LOG: Creates fitness entries
- QUERY: Answers questions about fitness data
- BOTH: Logs entry then answers query
- CORRECTION: Corrects previous entries
"""

import logging
from datetime import datetime
from importlib.metadata import version
from pathlib import Path
from typing import Annotated, Literal

import typer
from dotenv import load_dotenv
from quilto import (
    DomainModule,
    LLMClient,
    ObserverTriggerConfig,
    ProcessResult,
    Quilto,
    StorageRepository,
)

from swealog.cli.feedback import (
    FeedbackProgressHandler,
    FeedbackRecord,
    FeedbackRecorder,
    SessionMetadata,
    generate_feedback_id,
)
from swealog.cli.import_cmd import import_file
from swealog.cli.output import (
    print_error,
    print_info,
    print_panel,
    print_success,
    print_warning,
)
from swealog.cli.utils import EXIT_ERROR, get_dependencies, run_async

logger = logging.getLogger(__name__)


def _get_version() -> str:
    """Get swealog version from installed package metadata.

    Returns:
        Version string, or 'unknown' if package not installed.
    """
    try:
        return version("swealog")
    except Exception:
        return "unknown"


def version_callback(value: bool) -> None:
    """Print version and exit if --version flag is provided.

    Args:
        value: Whether --version flag was passed.
    """
    if value:
        print(f"swealog version {_get_version()}")
        raise typer.Exit()


def _create_quilto(
    llm_client: LLMClient,
    storage: StorageRepository,
    domains: list[DomainModule],
    debug: bool = False,
    session_db_path: str = "quilto_sessions.db",
    progress_handler: FeedbackProgressHandler | None = None,
) -> Quilto:
    """Create Quilto instance for CLI processing.

    Args:
        llm_client: LLM client for agents.
        storage: Storage repository for entries.
        domains: Available domain modules.
        debug: Enable debug mode with traces.
        session_db_path: Path to session database. Defaults to 'quilto_sessions.db'.
        progress_handler: Optional handler for capturing agent outputs.

    Returns:
        Configured Quilto instance.
    """
    return Quilto(
        llm_client=llm_client,
        storage=storage,
        domains=domains,
        observer_config=ObserverTriggerConfig(enable_post_query=True),
        session_db_path=session_db_path,
        progress_handler=progress_handler,
        debug=debug,
    )


def _display_query_result_from_process_result(result: ProcessResult) -> None:
    """Display query result from ProcessResult with consistent formatting.

    Args:
        result: ProcessResult from Quilto session.process().
    """
    is_partial = result.debug is not None and result.debug.retry_count >= 2

    if is_partial:
        print_warning("Partial response (insufficient data or evaluation failed):")

    print_panel(result.response or "", title="Response")

    if result.source_entry_ids:
        sources_str = ", ".join(result.source_entry_ids[:5])
        if len(result.source_entry_ids) > 5:
            sources_str += f" (+{len(result.source_entry_ids) - 5} more)"
        print_info(f"Sources: {sources_str}")

    confidence = result.confidence or 0.0
    print_info(f"Confidence: {confidence:.0%}")


def _display_log_success(result: ProcessResult, prefix: str = "Logged") -> None:
    """Display LOG/CORRECTION success with entry info.

    Args:
        result: ProcessResult containing parsed_data.
        prefix: Prefix for success message ('Logged' or 'Corrected').
    """
    if result.parsed_data:
        entry_id = result.parsed_data.get("entry_id", "entry")
        print_success(f"{prefix} entry: {entry_id}")
    else:
        print_success(f"{prefix} entry successfully")


def _display_result(result: ProcessResult) -> None:
    """Display ProcessResult based on input_type.

    Args:
        result: ProcessResult from Quilto session.process().
    """
    # Handle clarification first (any input type)
    if result.clarification_questions:
        print_warning("Clarification needed:")
        for i, q in enumerate(result.clarification_questions, 1):
            print_info(f"  {i}. {q.question}")
            if q.options:
                for opt in q.options:
                    print_info(f"     - {opt}")
        print_info("Please re-query with more specific details.")
        return

    # Display based on input_type
    if result.input_type == "log":
        _display_log_success(result)

    elif result.input_type == "correction":
        if result.response:
            print_success(result.response)
        else:
            _display_log_success(result, prefix="Corrected")

    elif result.input_type == "both":
        _display_log_success(result)
        _display_query_result_from_process_result(result)

    else:  # query
        _display_query_result_from_process_result(result)


def _prompt_for_feedback(debug: bool, non_interactive: bool) -> str | None:
    """Prompt user for feedback if debug mode is active.

    Args:
        debug: Whether debug mode is enabled.
        non_interactive: If True, skip prompting and return empty string.

    Returns:
        User feedback string or None if debug disabled.
        Empty string if user skipped or non_interactive.
    """
    if not debug:
        return None

    if non_interactive:
        return ""

    print()
    return typer.prompt(
        "How was this response? (press Enter to skip)",
        default="",
        show_default=False,
    )


def _record_feedback_with_handler(
    query: str,
    input_type: Literal["LOG", "QUERY", "BOTH", "CORRECTION"],
    result: ProcessResult,
    progress_handler: FeedbackProgressHandler,
    user_feedback: str,
    config_path: Path | None,
    storage_path: Path | None,
    non_interactive: bool = False,
    session_id: str | None = None,
) -> Path:
    """Record feedback using FeedbackProgressHandler outputs.

    Uses full agent outputs captured via ProgressHandler callbacks instead
    of abbreviated traces from ProcessResult.

    Args:
        query: The original query text.
        input_type: The classified input type.
        result: ProcessResult from Quilto.
        progress_handler: Handler with captured agent outputs.
        user_feedback: User's feedback string (may be empty).
        config_path: Path to LLM config (optional).
        storage_path: Path to storage directory (optional).
        non_interactive: Whether running in non-interactive mode.
        session_id: Session ID for multi-turn conversation tracking.

    Returns:
        Path to recorded feedback file.
    """
    feedback_id = generate_feedback_id(query)
    feedback_record = FeedbackRecord(
        id=feedback_id,
        query=query,
        intermediate_outputs=progress_handler.get_intermediate_outputs(),
        final_response=result.response or "",
        user_feedback=user_feedback,
        session=SessionMetadata(
            timestamp=datetime.now(),
            input_type=input_type,
            session_id=session_id,
            config_path=str(config_path) if config_path else None,
            storage_path=str(storage_path) if storage_path else None,
            debug_enabled=True,
            non_interactive=non_interactive,
        ),
    )

    recorder = FeedbackRecorder()
    file_path = recorder.record(feedback_record)
    logger.info("Recorded feedback with full outputs to %s", file_path)
    return file_path


app = typer.Typer(
    name="swealog",
    help="Fitness logging application powered by Quilto",
    no_args_is_help=False,
)


@app.callback()
def main_callback(
    version: Annotated[
        bool,
        typer.Option(
            "--version",
            "-v",
            callback=version_callback,
            is_eager=True,
            help="Show version and exit",
        ),
    ] = False,
) -> None:
    """Swealog - AI-powered fitness logging."""
    # Load .env file if present
    load_dotenv()


@app.command(name="run")
@run_async
async def run_command(
    text: Annotated[str, typer.Argument(help="Input text (log entry, query, or both)")],
    session_id: Annotated[
        str | None,
        typer.Option("--session", "-s", help="Session ID for multi-turn conversation"),
    ] = None,
    debug: Annotated[
        bool,
        typer.Option("--debug", "-d", help="Show debug output with agent timing"),
    ] = False,
    config: Annotated[
        Path | None,
        typer.Option("--config", "-c", help="Path to llm-config.yaml"),
    ] = None,
    storage_path: Annotated[
        Path | None,
        typer.Option("--storage", help="Path to storage directory"),
    ] = None,
    no_persist: Annotated[
        bool,
        typer.Option("--no-persist", help="Use in-memory session (no persistence)"),
    ] = False,
    non_interactive: Annotated[
        bool,
        typer.Option("--non-interactive", "-n", help="Skip prompts (for automation)"),
    ] = False,
) -> None:
    """Process any input through Quilto (log entries, queries, corrections).

    Examples:
        swealog run "bench 185x5"                      # LOG - creates entry
        swealog run "how's my progress?"               # QUERY - returns response
        swealog run "ran 5k, how does that compare?"   # BOTH - log + response
        swealog run --session abc123 "follow-up"       # Multi-turn conversation
        swealog run --debug "text"                     # Show traces
    """
    # Validate text is not empty
    if not text.strip():
        print_error("Input text cannot be empty")
        raise typer.Exit(EXIT_ERROR)

    try:
        # Initialize dependencies
        llm_client, storage, domains = get_dependencies(config, storage_path)

        # Create progress handler for debug mode to capture full agent outputs
        progress_handler = FeedbackProgressHandler(debug=debug) if debug else None

        # Determine session persistence
        session_db_path = ":memory:" if no_persist else "quilto_sessions.db"
        quilto = _create_quilto(llm_client, storage, domains, debug, session_db_path, progress_handler)

        # Warn if --no-persist overrides --session
        if no_persist and session_id:
            print_warning("--no-persist overrides --session (session will not be loaded from disk)")

        # Get or create session
        if session_id and not no_persist:
            session = quilto.get_session(session_id)
            if session is None:
                print_warning(f"Session '{session_id}' not found, creating new session")
                session = quilto.create_session()
            print_info(f"Session: {session.session_id}")
        else:
            session = quilto.create_session()
            print_info(f"Session: {session.session_id}")

        # Process through Quilto orchestration (single entry point)
        result = await session.process(text, mode="auto")

        # Display debug traces if enabled
        if debug and result.debug:
            for trace in result.debug.traces:
                summary = trace.output_summary
                display = summary[:50] + "..." if len(summary) > 50 else summary
                print_info(f"[{trace.agent_name}] {trace.elapsed_ms:.0f}ms - {display}")

        # Display result
        _display_result(result)

        # Prompt for feedback if debug enabled
        if debug and not result.clarification_questions:
            user_feedback = _prompt_for_feedback(debug, non_interactive)
            if user_feedback is not None:
                # Map input_type to feedback type literal
                input_type_raw = (result.input_type or "query").upper()
                input_type_map: dict[str, Literal["LOG", "QUERY", "BOTH", "CORRECTION"]] = {
                    "LOG": "LOG",
                    "QUERY": "QUERY",
                    "BOTH": "BOTH",
                    "CORRECTION": "CORRECTION",
                }
                feedback_input_type = input_type_map.get(input_type_raw, "QUERY")

                # Record feedback with full agent outputs captured by handler
                # progress_handler is always truthy when debug=True
                assert progress_handler is not None  # Type narrowing
                _record_feedback_with_handler(
                    query=text,
                    input_type=feedback_input_type,
                    result=result,
                    progress_handler=progress_handler,
                    user_feedback=user_feedback,
                    config_path=config,
                    storage_path=storage_path,
                    non_interactive=non_interactive,
                    session_id=session.session_id,
                )

    except typer.Exit:
        raise
    except Exception as e:
        logger.exception("Command failed: %s", e)
        print_error(f"Failed to process input: {e}")
        raise typer.Exit(EXIT_ERROR) from e


@app.command()
def serve(
    host: str = typer.Option("127.0.0.1", help="Host to bind to"),
    port: int = typer.Option(8000, help="Port to bind to"),
    reload: bool = typer.Option(False, help="Enable auto-reload for development"),
) -> None:
    """Start the Swealog API server.

    Runs uvicorn with the FastAPI application.

    Args:
        host: Host address to bind the server to.
        port: Port number to bind the server to.
        reload: Whether to enable auto-reload for development.
    """
    import uvicorn

    uvicorn.run(
        "swealog.api:app",
        host=host,
        port=port,
        reload=reload,
    )


# Register import command (name="import" since "import" is reserved keyword)
app.command(name="import")(import_file)
