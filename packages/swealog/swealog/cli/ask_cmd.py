"""CLI command for querying fitness data."""

import logging
from pathlib import Path
from typing import Annotated

import typer
from quilto import ObserverTriggerConfig, Quilto

from swealog.cli.output import print_error, print_info, print_panel, print_warning
from swealog.cli.utils import EXIT_ERROR, get_dependencies, run_async

logger = logging.getLogger(__name__)


@run_async
async def ask(
    query: Annotated[str, typer.Argument(help="Question about your fitness data")],
    config: Annotated[Path | None, typer.Option("--config", "-c", help="Path to llm-config.yaml")] = None,
    storage_path: Annotated[Path | None, typer.Option("--storage", "-s", help="Path to storage directory")] = None,
    debug: Annotated[bool, typer.Option("--debug", "-d", help="Show debug output with agent timing")] = False,
) -> None:
    """Query your fitness data via CLI.

    Example:
        swealog ask "how's my bench progress?"
        swealog ask --debug "what did I do last week?"
    """
    try:
        llm_client, storage, domains = get_dependencies(config, storage_path)

        # Build Quilto instance
        quilto = Quilto(
            llm_client=llm_client,
            storage=storage,
            domains=domains,
            observer_config=ObserverTriggerConfig(enable_post_query=True),
            session_db_path=":memory:",  # Stateless per-request
            debug=debug,
        )

        # Create session and process query
        session = quilto.create_session()
        result = await session.process(query, mode="query")

        # Handle clarification questions
        if result.clarification_questions:
            print_warning("Clarification needed:")
            for i, question in enumerate(result.clarification_questions, 1):
                print_info(f"  {i}. {question.question}")
            print_info("Please re-query with more specific details.")
            return

        # Display debug traces if enabled
        if debug and result.debug:
            for trace in result.debug.traces:
                summary = trace.output_summary
                display = summary[:50] + "..." if len(summary) > 50 else summary
                print_info(f"[{trace.agent_name}] {trace.elapsed_ms:.0f}ms - {display}")

        # Determine is_partial from retry_count
        is_partial = result.debug is not None and result.debug.retry_count >= 2

        # Warn if partial
        if is_partial:
            print_warning("Partial response (insufficient data or evaluation failed):")

        print_panel(result.response or "", title="Response")

        # Sources
        if result.source_entry_ids:
            sources_str = ", ".join(result.source_entry_ids[:5])
            if len(result.source_entry_ids) > 5:
                sources_str += f" (+{len(result.source_entry_ids) - 5} more)"
            print_info(f"Sources: {sources_str}")

        confidence = result.confidence or 0.0
        print_info(f"Confidence: {confidence:.0%}")

    except Exception as e:
        logger.exception("Ask command failed: %s", e)
        print_error(f"Query failed: {e}")
        raise typer.Exit(EXIT_ERROR) from e
