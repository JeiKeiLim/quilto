"""CLI command for logging fitness entries."""

import logging
from pathlib import Path
from typing import Annotated

import typer
from quilto import (
    DomainSelector,
    RouterAgent,
    RouterInput,
)

from swealog.cli.debug import DebugLogger
from swealog.cli.flows import execute_log_flow
from swealog.cli.output import print_error, print_info, print_success
from swealog.cli.utils import EXIT_ERROR, EXIT_SUCCESS, get_dependencies, run_async

logger = logging.getLogger(__name__)


@run_async
async def log(
    text: Annotated[str, typer.Argument(help="Fitness log entry text")],
    config: Annotated[Path | None, typer.Option("--config", "-c", help="Path to llm-config.yaml")] = None,
    storage_path: Annotated[Path | None, typer.Option("--storage", "-s", help="Path to storage directory")] = None,
    debug: Annotated[bool, typer.Option("--debug", "-d", help="Show debug output with agent timing")] = False,
) -> None:
    """Log a fitness entry via CLI.

    Example:
        swealog log "bench 185x5"
        swealog log --debug "ran 5k in 25min"
    """
    dbg = DebugLogger(enabled=debug)
    try:
        # Initialize via shared helper
        llm_client, storage, domains = get_dependencies(config, storage_path)
        selector = DomainSelector(domains)

        # Route input
        router = RouterAgent(llm_client)
        router_input = RouterInput(raw_input=text, available_domains=selector.get_domain_infos())
        with dbg.agent("Router", f'"{text[:50]}..."' if len(text) > 50 else f'"{text}"') as timing:
            router_output = await router.classify(router_input)
        dbg.log_output("Router", router_output.model_dump(), timing["elapsed"])

        # Handle QUERY-only
        if router_output.input_type.value == "QUERY":
            print_info("This looks like a query. Use 'swealog ask' instead.")
            print_info(f'Try: swealog ask "{text}"')
            raise typer.Exit(EXIT_SUCCESS)

        # Handle correction mode
        is_correction = router_output.input_type.value == "CORRECTION"

        # Execute log flow using shared function
        entry_id = await execute_log_flow(
            text=text,
            llm_client=llm_client,
            storage=storage,
            domains=domains,
            dbg=dbg,
            selected_domains=router_output.selected_domains,
            is_correction=is_correction,
            correction_target=router_output.correction_target,
        )

        # Output
        print_success(f"Logged entry: {entry_id}")
        if router_output.input_type.value == "BOTH":
            print_info(f"Query detected: {router_output.query_portion}")
            print_info(f"Use 'swealog ask \"{router_output.query_portion}\"' to process the query")

    except typer.Exit:
        raise
    except Exception as e:
        logger.exception("Log command failed: %s", e)
        print_error(f"Failed to log entry: {e}")
        raise typer.Exit(EXIT_ERROR) from e
