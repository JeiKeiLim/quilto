"""CLI command for unified auto-routing of input.

Routes input to appropriate flow based on Router classification:
- LOG: Execute log flow
- QUERY: Execute query flow via Quilto
- BOTH: Execute log flow, then query flow with query_portion via Quilto
- CORRECTION: Execute correction flow (log with correction mode)
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Annotated, Any, Literal

import typer
from quilto import (
    DomainModule,
    DomainSelector,
    LLMClient,
    ObserverTriggerConfig,
    ProcessResult,
    Quilto,
    RouterAgent,
    RouterInput,
    StorageRepository,
)

from swealog.cli.debug import DebugLogger
from swealog.cli.feedback import (
    FeedbackRecorder,
    SessionMetadata,
    SimplifiedFeedbackRecord,
    generate_feedback_id,
)
from swealog.cli.flows import execute_log_flow
from swealog.cli.output import print_error, print_info, print_panel, print_success, print_warning
from swealog.cli.utils import EXIT_ERROR, get_dependencies, run_async

logger = logging.getLogger(__name__)


def _create_quilto(
    llm_client: LLMClient,
    storage: StorageRepository,
    domains: list[DomainModule],
    debug: bool = False,
) -> Quilto:
    """Create Quilto instance for CLI query processing.

    Args:
        llm_client: LLM client for agents.
        storage: Storage repository for entries.
        domains: Available domain modules.
        debug: Enable debug mode with traces.

    Returns:
        Configured Quilto instance with in-memory session storage.
    """
    return Quilto(
        llm_client=llm_client,
        storage=storage,
        domains=domains,
        observer_config=ObserverTriggerConfig(enable_post_query=True),
        session_db_path=":memory:",
        debug=debug,
    )


def _display_query_result_from_process_result(result: ProcessResult) -> None:
    """Display query result from ProcessResult with consistent formatting.

    Args:
        result: ProcessResult from Quilto session.process().
    """
    # Determine is_partial from retry_count
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


def _handle_clarification_from_process_result(result: ProcessResult) -> bool:
    """Handle clarification request from ProcessResult.

    Args:
        result: ProcessResult from Quilto session.process().

    Returns:
        True if clarification was needed and displayed, False otherwise.
    """
    if not result.clarification_questions:
        return False

    print_warning("Clarification needed:")
    for i, question in enumerate(result.clarification_questions, 1):
        print_info(f"  {i}. {question.question}")
    print_info("Please re-query with more specific details.")
    return True


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
        # Non-interactive mode: record feedback as empty (to be filled by auto-review)
        return ""

    print()  # Blank line before prompt
    return typer.prompt(
        "How was this response? (press Enter to skip)",
        default="",
        show_default=False,
    )


def _record_simplified_feedback(
    query: str,
    input_type: Literal["LOG", "QUERY", "BOTH", "CORRECTION"],
    router_output: dict[str, Any],
    result: ProcessResult,
    user_feedback: str,
    config_path: Path | None,
    storage_path: Path | None,
    non_interactive: bool = False,
    router_elapsed_ms: float = 0.0,
) -> Path | None:
    """Record simplified feedback using ProcessResult traces.

    Args:
        query: The original query text.
        input_type: The classified input type.
        router_output: Router agent output dict.
        result: ProcessResult from Quilto.
        user_feedback: User's feedback string (may be empty).
        config_path: Path to LLM config (optional).
        storage_path: Path to storage directory (optional).
        non_interactive: Whether running in non-interactive mode.
        router_elapsed_ms: Router agent elapsed time in milliseconds.

    Returns:
        Path to recorded feedback file, or None if no debug info.
    """
    if result.debug is None:
        return None

    # Build traces list from ProcessResult.debug.traces
    traces = [
        {
            "agent_name": trace.agent_name,
            "input_summary": trace.input_summary,
            "output_summary": trace.output_summary,
            "elapsed_ms": trace.elapsed_ms,
            "timestamp": trace.timestamp.isoformat(),
        }
        for trace in result.debug.traces
    ]

    # Include router output as first trace with actual timing
    input_summary = query[:50] + "..." if len(query) > 50 else query
    router_trace = {
        "agent_name": "router",
        "input_summary": input_summary,
        "output_summary": f"input_type={router_output.get('input_type', 'unknown')}",
        "elapsed_ms": router_elapsed_ms,
        "timestamp": datetime.now().isoformat(),
    }
    all_traces = [router_trace] + traces

    feedback_id = generate_feedback_id(query)
    feedback_record = SimplifiedFeedbackRecord(
        id=feedback_id,
        query=query,
        traces=all_traces,
        final_response=result.response or "",
        user_feedback=user_feedback,
        session=SessionMetadata(
            timestamp=datetime.now(),
            input_type=input_type,
            config_path=str(config_path) if config_path else None,
            storage_path=str(storage_path) if storage_path else None,
            debug_enabled=True,
            non_interactive=non_interactive,
        ),
    )

    recorder = FeedbackRecorder()
    file_path = recorder.record_simplified(feedback_record)
    logger.info("Recorded feedback to %s", file_path)
    return file_path


@run_async
async def auto(
    text: Annotated[str, typer.Argument(help="Input text (log entry, query, or both)")],
    config: Annotated[Path | None, typer.Option("--config", "-c", help="Path to llm-config.yaml")] = None,
    storage_path: Annotated[Path | None, typer.Option("--storage", "-s", help="Path to storage directory")] = None,
    debug: Annotated[bool, typer.Option("--debug", "-d", help="Show debug output with agent timing")] = False,
    non_interactive: Annotated[
        bool, typer.Option("--non-interactive", "-n", help="Skip prompts (for automated testing)")
    ] = False,
) -> None:
    """Automatically route input to the appropriate flow.

    The Router agent classifies input and routes to:
    - LOG: Log the entry (same as `swealog log`)
    - QUERY: Execute query via Quilto (same as `swealog ask`)
    - BOTH: Log first, then query with the query portion via Quilto
    - CORRECTION: Correct a previous entry

    Examples:
        swealog auto "bench 185x5"                    # Routes to LOG
        swealog auto "how's my progress?"             # Routes to QUERY
        swealog auto "ran 5k, how does that compare?" # Routes to BOTH
        swealog auto --debug "bench 185x5"            # With debug timing
        swealog auto --debug --non-interactive "..."  # For auto-dogfood script
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
            # Execute log flow (Swealog-specific, NOT via Quilto)
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
            # Execute query flow via Quilto
            quilto = _create_quilto(llm_client, storage, domains, debug)
            session = quilto.create_session()
            result = await session.process(text, mode="query")

            # Handle clarification request
            if _handle_clarification_from_process_result(result):
                return

            _display_query_result_from_process_result(result)

            # Prompt for feedback and record if debug enabled
            user_feedback = _prompt_for_feedback(debug, non_interactive)
            if user_feedback is not None:
                _record_simplified_feedback(
                    query=text,
                    input_type="QUERY",
                    router_output=router_output.model_dump(),
                    result=result,
                    user_feedback=user_feedback,
                    config_path=config,
                    storage_path=storage_path,
                    non_interactive=non_interactive,
                    router_elapsed_ms=timing["elapsed"] * 1000,  # Convert seconds to ms
                )

        elif input_type == "BOTH":
            # Execute log flow first (Swealog-specific)
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

            # Then execute query flow via Quilto with query_portion
            query_text = router_output.query_portion or text
            quilto = _create_quilto(llm_client, storage, domains, debug)
            session = quilto.create_session()
            result = await session.process(query_text, mode="query")

            # Handle clarification request
            if _handle_clarification_from_process_result(result):
                return

            _display_query_result_from_process_result(result)

            # Prompt for feedback and record if debug enabled
            user_feedback = _prompt_for_feedback(debug, non_interactive)
            if user_feedback is not None:
                _record_simplified_feedback(
                    query=query_text,  # Use query_portion, not original text
                    input_type="BOTH",
                    router_output=router_output.model_dump(),
                    result=result,
                    user_feedback=user_feedback,
                    config_path=config,
                    storage_path=storage_path,
                    non_interactive=non_interactive,
                    router_elapsed_ms=timing["elapsed"] * 1000,  # Convert seconds to ms
                )

        elif input_type == "CORRECTION":
            # Execute correction flow (Swealog-specific, NOT via Quilto)
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
