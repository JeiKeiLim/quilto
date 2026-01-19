"""CLI command for querying fitness data."""

import logging
from pathlib import Path
from typing import Annotated

import typer

from swealog.api.routes.query import execute_query_pipeline
from swealog.cli.debug import create_debug_callback
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
        debug_callback = create_debug_callback(debug)

        # Reuse API pipeline logic
        result = await execute_query_pipeline(
            query=query,
            llm_client=llm_client,
            storage=storage,
            domains=domains,
            debug_callback=debug_callback,
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
