"""CLI command for unified auto-routing of input.

Routes input to appropriate flow based on Router classification:
- LOG: Execute log flow
- QUERY: Execute query flow
- BOTH: Execute log flow, then query flow with query_portion
- CORRECTION: Execute correction flow (log with correction mode)
"""

import logging
from pathlib import Path
from typing import Annotated, Any

import typer
from quilto import (
    DomainSelector,
    RouterAgent,
    RouterInput,
)

from swealog.api.routes.query import execute_query_pipeline
from swealog.cli.debug import DebugLogger, create_debug_callback
from swealog.cli.flows import execute_log_flow
from swealog.cli.output import print_error, print_info, print_panel, print_success, print_warning
from swealog.cli.utils import EXIT_ERROR, get_dependencies, run_async

logger = logging.getLogger(__name__)


def _display_query_result(result: dict[str, Any]) -> None:
    """Display query pipeline result with consistent formatting.

    Args:
        result: Query pipeline result dict with response, sources, confidence, is_partial.
    """
    if result["is_partial"]:
        print_warning("Partial response (insufficient data or evaluation failed):")

    print_panel(result["response"], title="Response")

    if result["sources"]:
        sources_str = ", ".join(result["sources"][:5])
        if len(result["sources"]) > 5:
            sources_str += f" (+{len(result['sources']) - 5} more)"
        print_info(f"Sources: {sources_str}")

    print_info(f"Confidence: {result['confidence']:.0%}")


@run_async
async def auto(
    text: Annotated[str, typer.Argument(help="Input text (log entry, query, or both)")],
    config: Annotated[Path | None, typer.Option("--config", "-c", help="Path to llm-config.yaml")] = None,
    storage_path: Annotated[Path | None, typer.Option("--storage", "-s", help="Path to storage directory")] = None,
    debug: Annotated[bool, typer.Option("--debug", "-d", help="Show debug output with agent timing")] = False,
) -> None:
    """Automatically route input to the appropriate flow.

    The Router agent classifies input and routes to:
    - LOG: Log the entry (same as `swealog log`)
    - QUERY: Execute query (same as `swealog ask`)
    - BOTH: Log first, then query with the query portion
    - CORRECTION: Correct a previous entry

    Examples:
        swealog auto "bench 185x5"                    # Routes to LOG
        swealog auto "how's my progress?"             # Routes to QUERY
        swealog auto "ran 5k, how does that compare?" # Routes to BOTH
        swealog auto --debug "bench 185x5"            # With debug timing
    """
    dbg = DebugLogger(enabled=debug)
    try:
        # Initialize dependencies
        llm_client, storage, domains = get_dependencies(config, storage_path)
        selector = DomainSelector(domains)

        # Route input
        router = RouterAgent(llm_client)
        router_input = RouterInput(raw_input=text, available_domains=selector.get_domain_infos())
        with dbg.agent("Router", f'"{text[:50]}..."' if len(text) > 50 else f'"{text}"') as timing:
            router_output = await router.classify(router_input)
        dbg.log_output("Router", router_output.model_dump(), timing["elapsed"])

        input_type = router_output.input_type.value

        # Route based on classification
        if input_type == "LOG":
            # Execute log flow
            entry_id = await execute_log_flow(
                text=text,
                llm_client=llm_client,
                storage=storage,
                domains=domains,
                dbg=dbg,
                selected_domains=router_output.selected_domains,
                is_correction=False,
                correction_target=None,
            )
            print_success(f"Logged entry: {entry_id}")

        elif input_type == "QUERY":
            # Execute query flow
            debug_callback = create_debug_callback(debug)
            result = await execute_query_pipeline(
                query=text,
                llm_client=llm_client,
                storage=storage,
                domains=domains,
                debug_callback=debug_callback,
            )
            _display_query_result(result)

        elif input_type == "BOTH":
            # Execute log flow first
            entry_id = await execute_log_flow(
                text=text,
                llm_client=llm_client,
                storage=storage,
                domains=domains,
                dbg=dbg,
                selected_domains=router_output.selected_domains,
                is_correction=False,
                correction_target=None,
            )
            print_success(f"Logged entry: {entry_id}")

            # Then execute query flow with query_portion
            query_text = router_output.query_portion or text
            debug_callback = create_debug_callback(debug)
            result = await execute_query_pipeline(
                query=query_text,
                llm_client=llm_client,
                storage=storage,
                domains=domains,
                debug_callback=debug_callback,
            )
            _display_query_result(result)

        elif input_type == "CORRECTION":
            # Execute correction flow
            entry_id = await execute_log_flow(
                text=text,
                llm_client=llm_client,
                storage=storage,
                domains=domains,
                dbg=dbg,
                selected_domains=router_output.selected_domains,
                is_correction=True,
                correction_target=router_output.correction_target,
            )
            print_success(f"Logged entry: {entry_id}")

        else:
            # Unexpected input type - treat as LOG
            logger.warning("Unexpected input type %s, treating as LOG", input_type)
            entry_id = await execute_log_flow(
                text=text,
                llm_client=llm_client,
                storage=storage,
                domains=domains,
                dbg=dbg,
                selected_domains=router_output.selected_domains,
                is_correction=False,
                correction_target=None,
            )
            print_success(f"Logged entry: {entry_id}")

    except typer.Exit:
        raise
    except Exception as e:
        logger.exception("Auto command failed: %s", e)
        print_error(f"Failed to process input: {e}")
        raise typer.Exit(EXIT_ERROR) from e
