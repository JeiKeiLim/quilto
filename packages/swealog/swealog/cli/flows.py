"""Shared flow functions for CLI commands.

Provides reusable async functions for log and query flows that can be
used by log, ask, and auto commands.
"""

import logging
from datetime import datetime

from quilto import (
    DomainModule,
    Entry,
    LLMClient,
    ParserAgent,
    ParserInput,
    StorageRepository,
)

from swealog.cli.debug import DebugLogger

logger = logging.getLogger(__name__)


async def execute_log_flow(
    text: str,
    llm_client: LLMClient,
    storage: StorageRepository,
    domains: list[DomainModule],
    dbg: DebugLogger,
    selected_domains: list[str],
    is_correction: bool = False,
    correction_target: str | None = None,
) -> str:
    """Execute log flow to parse and store an entry.

    Args:
        text: Raw input text to parse and log.
        llm_client: LLM client for parsing.
        storage: Storage repository to save entry.
        domains: Available domain modules.
        dbg: Debug logger for timing output.
        selected_domains: Domain names selected by router.
        is_correction: Whether this is a correction entry.
        correction_target: Target of correction (e.g., "yesterday").

    Returns:
        Entry ID of the saved entry.
    """
    # Generate entry ID and timestamp from single datetime
    timestamp = datetime.now()
    entry_id = timestamp.strftime("%Y-%m-%d_%H-%M-%S")

    # Build parser context from selected domains
    active_domains = [d for d in domains if d.name in selected_domains] or domains
    domain_schemas = {d.name: d.log_schema for d in active_domains}
    vocabulary: dict[str, str] = {}
    for d in active_domains:
        vocabulary.update(d.vocabulary)

    # Handle correction mode - get recent entries
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
        correction_target=correction_target,
        recent_entries=recent_entries,
    )
    with dbg.agent("Parser", f"domains={list(domain_schemas.keys())}") as timing:
        parser_output = await parser.parse(parser_input)
    dbg.log_output("Parser", parser_output.model_dump(), timing["elapsed"])

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

    return entry_id
