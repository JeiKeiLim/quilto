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
            print_info(f"Use 'swealog ask \"{router_output.query_portion}\"' to process the query")

    except typer.Exit:
        raise
    except Exception as e:
        logger.exception("Log command failed: %s", e)
        print_error(f"Failed to log entry: {e}")
        raise typer.Exit(EXIT_ERROR) from e
