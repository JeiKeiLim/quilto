"""Correction flow orchestration for handling user corrections.

This module provides the process_correction function that orchestrates
the correction flow: parsing correction input and saving with upsert
semantics to storage.
"""

from datetime import UTC, datetime

from pydantic import BaseModel

from quilto.agents import ParserAgent
from quilto.agents.models import InputType, ParserInput, RouterOutput
from quilto.flow.models import CorrectionResult
from quilto.storage import Entry, StorageRepository

__all__ = ["process_correction"]


async def process_correction(
    router_output: RouterOutput,
    parser_agent: ParserAgent,
    storage: StorageRepository,
    recent_entries: list[Entry],
    domain_schemas: dict[str, type[BaseModel]],
    vocabulary: dict[str, str],
    timestamp: datetime | None = None,
) -> CorrectionResult:
    """Process a correction request through Parser and Storage.

    Orchestrates the correction flow by:
    1. Validating the router output is a CORRECTION type
    2. Building ParserInput with correction mode enabled
    3. Calling Parser to identify target and extract delta
    4. Saving the correction with upsert semantics to storage

    Args:
        router_output: RouterOutput with input_type=CORRECTION and correction_target.
        parser_agent: ParserAgent instance for extraction.
        storage: StorageRepository for saving corrected entry.
        recent_entries: Recent entries for target identification.
        domain_schemas: Domain schemas for parsing.
        vocabulary: Vocabulary for term normalization.
        timestamp: Override timestamp (defaults to now).

    Returns:
        CorrectionResult indicating success/failure with details.

    Raises:
        ValueError: If router_output.input_type is not CORRECTION.

    Example:
        >>> result = await process_correction(
        ...     router_output=router_output,
        ...     parser_agent=parser,
        ...     storage=storage,
        ...     recent_entries=recent,
        ...     domain_schemas={"strength": StrengthSchema},
        ...     vocabulary={"bp": "bench press"},
        ... )
        >>> if result.success:
        ...     print(f"Corrected entry: {result.target_entry_id}")
    """
    # 1. Validate inputs
    if router_output.input_type != InputType.CORRECTION:
        raise ValueError("router_output must have input_type=CORRECTION")

    if not recent_entries:
        return CorrectionResult(
            success=False,
            error_message="No recent entries to correct",
        )

    # Default timestamp to now (UTC for consistency)
    ts = timestamp or datetime.now(UTC)

    # 2. Build ParserInput with correction mode
    parser_input = ParserInput(
        raw_input=router_output.log_portion or router_output.reasoning,
        timestamp=ts,
        domain_schemas=domain_schemas,
        vocabulary=vocabulary,
        recent_entries=recent_entries,
        correction_mode=True,
        correction_target=router_output.correction_target,
    )

    # 3. Call Parser
    parser_output = await parser_agent.parse(parser_input)

    # 4. Validate Parser identified the correction
    if not parser_output.is_correction:
        return CorrectionResult(
            success=False,
            error_message="Parser did not identify correction",
        )

    if not parser_output.target_entry_id:
        return CorrectionResult(
            success=False,
            error_message="Could not identify target entry",
        )

    # 5. Create Entry for storage
    entry_id = f"{parser_output.date.isoformat()}_{ts.strftime('%H-%M-%S')}"
    entry = Entry(
        id=entry_id,
        date=parser_output.date,
        timestamp=ts,
        raw_content=parser_output.raw_content,
        parsed_data=parser_output.domain_data,
    )

    # 6. Save with correction (triggers append + upsert)
    storage.save_entry(entry, correction=parser_output)

    # 7. Return success
    return CorrectionResult(
        success=True,
        target_entry_id=parser_output.target_entry_id,
        correction_delta=parser_output.correction_delta,
        original_entry_id=parser_output.target_entry_id,
    )
