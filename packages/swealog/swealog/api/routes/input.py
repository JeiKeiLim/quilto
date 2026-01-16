"""POST /input endpoint for processing user input."""

import logging
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
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

from swealog.api.dependencies import get_domains, get_llm_client, get_storage
from swealog.api.models import InputRequest, InputResponse

logger = logging.getLogger(__name__)

router = APIRouter()


async def parse_log_background(
    raw_input: str,
    entry_id: str,
    llm_client: LLMClient,
    storage: StorageRepository,
    domains: list[DomainModule],
    selected_domain_names: list[str],
    is_correction: bool = False,
    correction_target: str | None = None,
) -> None:
    """Background task to parse and store log entry.

    Args:
        raw_input: The raw user input text.
        entry_id: The generated entry ID (timestamp-based).
        llm_client: LLM client for Parser agent.
        storage: Storage repository for saving entries.
        domains: Available domain modules.
        selected_domain_names: Domains selected by Router.
        is_correction: Whether this is a correction input.
        correction_target: What is being corrected (if correction).
    """
    try:
        # Filter domains to those selected by Router
        selected_domains = [d for d in domains if d.name in selected_domain_names]
        if not selected_domains:
            selected_domains = domains  # Fall back to all domains

        # Build domain schemas and vocabulary from selected domains
        domain_schemas = {d.name: d.log_schema for d in selected_domains}
        vocabulary: dict[str, str] = {}
        for d in selected_domains:
            vocabulary.update(d.vocabulary)

        # Get recent entries for correction context
        recent_entries: list[Entry] = []
        if is_correction:
            recent_entries = storage.get_entries_by_pattern("**/*.md")[-10:]

        # Parse the input - entry_id format is "YYYY-MM-DD_HH-MM-SS"
        timestamp = datetime.strptime(entry_id, "%Y-%m-%d_%H-%M-%S")
        parser = ParserAgent(llm_client)
        parser_input = ParserInput(
            raw_input=raw_input,
            timestamp=timestamp,
            domain_schemas=domain_schemas,
            vocabulary=vocabulary,
            correction_mode=is_correction,
            correction_target=correction_target,
            recent_entries=recent_entries,
        )

        parser_output = await parser.parse(parser_input)

        # Create entry for storage
        entry = Entry(
            id=entry_id,
            date=parser_output.date,
            timestamp=parser_output.timestamp,
            raw_content=raw_input,
            parsed_data=parser_output.domain_data,
        )

        # Save to storage
        if is_correction and parser_output.is_correction:
            storage.save_entry(entry, correction=parser_output)
        else:
            storage.save_entry(entry)

        logger.info("Parsed and saved entry %s", entry_id)

    except Exception as e:
        logger.exception("Background parsing failed for entry %s: %s", entry_id, e)


@router.post("/input", response_model=InputResponse)
async def process_input(
    request: InputRequest,
    background_tasks: BackgroundTasks,
    llm_client: Annotated[LLMClient, Depends(get_llm_client)],
    storage: Annotated[StorageRepository, Depends(get_storage)],
    domains: Annotated[list[DomainModule], Depends(get_domains)],
) -> InputResponse:
    """Process user input (log, query, both, or correction).

    Routes input through Router agent and schedules background parsing
    for LOG/BOTH/CORRECTION inputs.

    Args:
        request: The input request with text field.
        background_tasks: FastAPI background tasks manager.
        llm_client: LLM client for agents.
        storage: Storage repository for entries.
        domains: Available domain modules.

    Returns:
        InputResponse with status, input_type, and entry_id.

    Raises:
        HTTPException: If router classification fails.
    """
    try:
        # Route input through Router agent
        router_agent = RouterAgent(llm_client)
        domain_infos = [DomainInfo(name=d.name, description=d.description) for d in domains]
        router_input = RouterInput(raw_input=request.text, available_domains=domain_infos)

        router_output = await router_agent.classify(router_input)
        entry_id = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

        # Handle LOG, BOTH, CORRECTION - schedule background parsing
        if router_output.input_type.value in ("LOG", "BOTH", "CORRECTION"):
            is_correction = router_output.input_type.value == "CORRECTION"
            background_tasks.add_task(
                parse_log_background,
                request.text,
                entry_id,
                llm_client,
                storage,
                domains,
                router_output.selected_domains,
                is_correction,
                router_output.correction_target,
            )

        # Build response
        return InputResponse(
            status="accepted",
            input_type=router_output.input_type.value,
            entry_id=(entry_id if router_output.input_type.value in ("LOG", "BOTH", "CORRECTION") else None),
            message=(
                f"Query detected: {router_output.query_portion}" if router_output.input_type.value == "BOTH" else None
            ),
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        logger.exception("Input processing failed: %s", e)
        raise HTTPException(status_code=500, detail=f"Internal error: {type(e).__name__}") from e
