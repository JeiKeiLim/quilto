"""Correction flow orchestration for handling user corrections.

This module provides the process_correction function that orchestrates
the correction flow: parsing correction input, editing raw markdown
in-place, re-parsing, and updating the parsed JSON.
"""

import logging
from datetime import UTC, datetime

from pydantic import BaseModel

from quilto.agents import ParserAgent
from quilto.agents.models import InputType, ParserInput, RouterOutput
from quilto.flow.models import CorrectionResult
from quilto.storage import Entry, StorageRepository

__all__ = ["process_correction"]

logger = logging.getLogger(__name__)


async def process_correction(
    router_output: RouterOutput,
    parser_agent: ParserAgent,
    storage: StorageRepository,
    recent_entries: list[Entry],
    domain_schemas: dict[str, type[BaseModel]],
    vocabulary: dict[str, str],
    user_input: str,
    timestamp: datetime | None = None,
) -> CorrectionResult:
    """Process a correction request by editing raw markdown in-place.

    Orchestrates the correction flow by:
    1. Validating the router output is a CORRECTION type
    2. Building ParserInput with correction mode enabled
    3. Calling Parser to identify target and generate corrected content
    4. Locating the target section in the raw file
    5. Editing the raw file in-place (surgical edit)
    6. Re-parsing the modified section
    7. Updating the parsed JSON entry

    Args:
        router_output: RouterOutput with input_type=CORRECTION and correction_target.
        parser_agent: ParserAgent instance for extraction.
        storage: StorageRepository for editing raw files.
        recent_entries: Recent entries for target identification.
        domain_schemas: Domain schemas for parsing.
        vocabulary: Vocabulary for term normalization.
        user_input: Original user input text for Parser extraction.
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
        ...     user_input="I logged 5 sets but it should be 4",
        ... )
        >>> if result.success:
        ...     print(f"Corrected entry: {result.target_entry_id}")
        ...     print(f"Modified file: {result.modified_file}")
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
        raw_input=user_input,
        timestamp=ts,
        domain_schemas=domain_schemas,
        vocabulary=vocabulary,
        recent_entries=recent_entries,
        correction_mode=True,
        correction_target=router_output.correction_target,
    )

    # 3. Call Parser to identify target and generate corrected content
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

    # 5. Locate the target section in the raw file
    section_info = storage.find_raw_entry_section(parser_output.target_entry_id)
    if section_info is None:
        return CorrectionResult(
            success=False,
            error_message=f"Could not locate entry '{parser_output.target_entry_id}' in raw files",
        )

    file_path, start_line, end_line = section_info
    logger.debug(
        "process_correction: Found target section in %s lines %d-%d",
        file_path,
        start_line,
        end_line,
    )

    # 6. Build new section content
    # Parser's raw_content IS the complete corrected section content (includes ## HH:MM header)
    # Extract time from target_entry_id for the header
    try:
        _, time_part = parser_output.target_entry_id.split("_")
        time_components = time_part.split("-")
        hour = int(time_components[0])
        minute = int(time_components[1])
        time_header = f"## {hour:02d}:{minute:02d}"
    except (ValueError, IndexError) as e:
        logger.error("Failed to extract time from target_entry_id: %s", e)
        return CorrectionResult(
            success=False,
            error_message=f"Invalid target_entry_id format: {parser_output.target_entry_id}",
        )

    # Build complete section content with header
    new_content = f"{time_header}\n{parser_output.raw_content}\n"

    # 7. Edit the raw file in-place
    try:
        storage.edit_raw_section(file_path, start_line, end_line, new_content)
        logger.info(
            "process_correction: Edited %s lines %d-%d for entry %s",
            file_path,
            start_line,
            end_line,
            parser_output.target_entry_id,
        )
    except (FileNotFoundError, ValueError) as e:
        logger.error("Failed to edit raw section: %s", e)
        return CorrectionResult(
            success=False,
            error_message=f"Failed to edit raw file: {e}",
        )

    # 8. Re-parse the modified section to get fresh parsed_data
    reparse_input = ParserInput(
        raw_input=parser_output.raw_content,
        timestamp=ts,
        domain_schemas=domain_schemas,
        vocabulary=vocabulary,
        correction_mode=False,  # Not correction mode for re-parse
    )
    reparse_output = await parser_agent.parse(reparse_input)

    # 9. Replace the parsed JSON entry with fresh re-parse output (not merge)
    # Accessing private methods here is intentional - correction flow is internal to quilto
    parsed_path = storage._get_parsed_path(parser_output.date)  # noqa: SLF001  # pyright: ignore[reportPrivateUsage]
    storage._save_parsed_json(  # noqa: SLF001  # pyright: ignore[reportPrivateUsage]
        parsed_path,
        parser_output.target_entry_id,
        reparse_output.domain_data,
    )
    logger.debug(
        "process_correction: Updated parsed JSON for entry %s",
        parser_output.target_entry_id,
    )

    # 10. Return success with details
    return CorrectionResult(
        success=True,
        target_entry_id=parser_output.target_entry_id,
        correction_delta=parser_output.correction_delta,
        original_entry_id=parser_output.target_entry_id,
        modified_file=file_path,
        edited_lines=(start_line, end_line),
    )
