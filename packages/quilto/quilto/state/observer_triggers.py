"""Observer trigger system for invoking Observer at appropriate times.

This module provides the trigger configuration, detection protocols, helper
functions, and LangGraph node for invoking the Observer agent at specific
events in the query/log processing flow.

Trigger types:
- post_query: After successful query completion (query + analysis + response)
- user_correction: After a user correction is processed
- significant_log: After parsing a potentially notable entry (PR, milestone, event)
- periodic: Scheduled batch updates (optional)
"""

import re
from datetime import datetime, timedelta
from typing import Any, Literal, Protocol

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from quilto.agents import ObserverAgent
from quilto.agents.models import (
    ActiveDomainContext,
    AnalyzerOutput,
    ObserverInput,
    ObserverOutput,
)
from quilto.state.session import SessionState
from quilto.storage import (
    DateRange,
    Entry,
    GlobalContext,
    GlobalContextManager,
    StorageRepository,
)

# =============================================================================
# Configuration Model
# =============================================================================


class ObserverTriggerConfig(BaseModel):
    """Configuration for Observer trigger behavior.

    Controls which triggers are enabled and periodic trigger settings.
    Applications can customize this to enable/disable specific triggers.

    Attributes:
        enable_post_query: Enable trigger after query completion (default True).
        enable_user_correction: Enable trigger after corrections (default True).
        enable_significant_log: Enable trigger for significant entries (default True).
        enable_periodic: Enable periodic batch updates (default False).
        periodic_interval_minutes: Interval for periodic triggers (required if enable_periodic=True).

    Example:
        >>> config = ObserverTriggerConfig(
        ...     enable_post_query=True,
        ...     enable_user_correction=True,
        ...     enable_significant_log=True,
        ...     enable_periodic=True,
        ...     periodic_interval_minutes=60,
        ... )
    """

    model_config = ConfigDict(strict=True)

    enable_post_query: bool = True
    enable_user_correction: bool = True
    enable_significant_log: bool = True
    enable_periodic: bool = False
    periodic_interval_minutes: int | None = None

    @field_validator("periodic_interval_minutes", mode="after")
    @classmethod
    def validate_periodic_interval(cls, v: int | None) -> int | None:
        """Validate periodic_interval_minutes is positive when set.

        Args:
            v: The interval value to validate.

        Returns:
            The validated interval value.

        Raises:
            ValueError: If interval is not positive when set.
        """
        if v is not None and v <= 0:
            raise ValueError("periodic_interval_minutes must be > 0 when set")
        return v

    @model_validator(mode="after")
    def validate_periodic_config(self) -> "ObserverTriggerConfig":
        """Validate periodic configuration is complete.

        Returns:
            The validated config instance.

        Raises:
            ValueError: If enable_periodic=True but periodic_interval_minutes is not set.
        """
        if self.enable_periodic and self.periodic_interval_minutes is None:
            raise ValueError("periodic_interval_minutes is required when enable_periodic=True")
        return self


# =============================================================================
# Significant Entry Detection Protocol
# =============================================================================


class SignificantEntryDetector(Protocol):
    """Protocol for determining if an entry is significant enough to trigger Observer.

    Applications can implement custom detectors to define what constitutes
    a "significant" entry in their domain.
    """

    def is_significant(self, entry: Entry, parsed_data: dict[str, Any]) -> bool:
        """Determine if entry warrants Observer attention.

        Args:
            entry: The log entry to evaluate.
            parsed_data: Parsed domain data from the entry.

        Returns:
            True if the entry is significant, False otherwise.
        """
        ...


class DefaultSignificantEntryDetector:
    """Default implementation checking for PRs, milestones, and events.

    Checks for:
    - Personal record (PR) indicators
    - Milestone keywords (first, 100th, etc.)
    - Event mentions (competition, race, etc.)
    """

    def is_significant(self, entry: Entry, parsed_data: dict[str, Any]) -> bool:
        """Determine if entry is significant based on content keywords.

        Args:
            entry: The log entry to evaluate.
            parsed_data: Parsed domain data (not currently used but available for extension).

        Returns:
            True if the entry contains significant indicators.
        """
        content_lower = entry.raw_content.lower()

        # Check for PR indicators using word boundary matching
        # Note: "pr" needs word boundary to avoid false positives like "press"
        phrase_indicators = ["personal record", "new record", "personal best"]
        if any(ind in content_lower for ind in phrase_indicators):
            return True

        # Word boundary check for "pr" and "pb" abbreviations
        if re.search(r"\bpr\b", content_lower) or re.search(r"\bpb\b", content_lower):
            return True

        # Check for milestones
        milestone_patterns = ["first", "100th", "1000th", "milestone"]
        if any(pat in content_lower for pat in milestone_patterns):
            return True

        # Check for events
        event_indicators = ["competition", "race", "meet", "match", "tournament"]
        return any(ind in content_lower for ind in event_indicators)


# =============================================================================
# Helper Functions
# =============================================================================


def serialize_global_context(context: GlobalContext) -> str:
    """Serialize GlobalContext to markdown string for ObserverInput.

    This is a standalone helper that replicates the serialization logic
    from GlobalContextManager._serialize_context() for use in trigger functions.

    Args:
        context: The GlobalContext to serialize.

    Returns:
        Markdown string suitable for ObserverInput.current_global_context.
    """
    lines: list[str] = []

    # YAML frontmatter
    lines.append("---")
    lines.append(f"last_updated: {context.frontmatter.last_updated}")
    lines.append(f"version: {context.frontmatter.version}")
    lines.append(f"token_estimate: {context.frontmatter.token_estimate}")
    lines.append("---")
    lines.append("")
    lines.append("# Global Context")
    lines.append("")

    # Preferences section
    lines.append("## Preferences (certain)")
    if context.preferences:
        for entry in context.preferences:
            lines.append(f"- [{entry.added_date}|{entry.confidence}|{entry.source}] {entry.key}: {entry.value}")
    lines.append("")

    # Patterns section
    lines.append("## Patterns (likely)")
    if context.patterns:
        for entry in context.patterns:
            lines.append(f"- [{entry.added_date}|{entry.confidence}|{entry.source}] {entry.key}: {entry.value}")
    lines.append("")

    # Facts section
    lines.append("## Facts (certain)")
    if context.facts:
        for entry in context.facts:
            lines.append(f"- [{entry.added_date}|{entry.confidence}|{entry.source}] {entry.key}: {entry.value}")
    lines.append("")

    # Insights section
    lines.append("## Insights (tentative)")
    if context.insights:
        for entry in context.insights:
            lines.append(f"- [{entry.added_date}|{entry.confidence}|{entry.source}] {entry.key}: {entry.value}")
    lines.append("")

    return "\n".join(lines)


def get_combined_context_guidance(active_domain_context: ActiveDomainContext) -> str:
    """Combine context_management_guidance from all loaded domains.

    Extracts and concatenates guidance from all domains in the active context,
    labeling each with the domain name.

    Args:
        active_domain_context: The active domain context with loaded domains.

    Returns:
        Combined guidance string with domain labels, or default message if none.
    """
    # The context_guidance field contains the combined guidance from domains
    if active_domain_context.context_guidance:
        return active_domain_context.context_guidance
    return "No domain-specific guidance available."


# =============================================================================
# Trigger Functions
# =============================================================================


async def trigger_post_query(
    observer: ObserverAgent,
    context_manager: GlobalContextManager,
    config: ObserverTriggerConfig,
    query: str,
    analysis: AnalyzerOutput,
    response: str,
    active_domain_context: ActiveDomainContext,
) -> ObserverOutput | None:
    """Trigger Observer after successful query completion.

    Builds ObserverInput with post_query trigger and invokes Observer.
    Applies updates to GlobalContext if should_update is True.

    Args:
        observer: The ObserverAgent instance.
        context_manager: GlobalContextManager for context operations.
        config: Trigger configuration.
        query: The user's query.
        analysis: AnalyzerOutput from query analysis.
        response: The generated response.
        active_domain_context: Active domain context with guidance.

    Returns:
        ObserverOutput if trigger is enabled and Observer ran, None otherwise.
    """
    if not config.enable_post_query:
        return None

    # Get combined guidance
    guidance = get_combined_context_guidance(active_domain_context)

    # Get and serialize current global context
    context = context_manager.read_context()
    serialized_context = serialize_global_context(context)

    # Build ObserverInput
    observer_input = ObserverInput(
        trigger="post_query",
        current_global_context=serialized_context,
        context_management_guidance=guidance,
        query=query,
        analysis=analysis.model_dump(),
        response=response,
    )

    # Call Observer
    output = await observer.observe(observer_input)

    # Apply updates if needed
    if output.should_update:
        context_manager.apply_updates(output.updates)

    return output


async def trigger_user_correction(
    observer: ObserverAgent,
    context_manager: GlobalContextManager,
    config: ObserverTriggerConfig,
    correction: str,
    what_was_corrected: str,
    active_domain_context: ActiveDomainContext,
) -> ObserverOutput | None:
    """Trigger Observer after a correction is processed.

    Builds ObserverInput with user_correction trigger and invokes Observer.
    User corrections should generate updates with "certain" confidence.

    Args:
        observer: The ObserverAgent instance.
        context_manager: GlobalContextManager for context operations.
        config: Trigger configuration.
        correction: The correction text.
        what_was_corrected: Description of what was corrected.
        active_domain_context: Active domain context with guidance.

    Returns:
        ObserverOutput if trigger is enabled and Observer ran, None otherwise.
    """
    if not config.enable_user_correction:
        return None

    # Get combined guidance
    guidance = get_combined_context_guidance(active_domain_context)

    # Get and serialize current global context
    context = context_manager.read_context()
    serialized_context = serialize_global_context(context)

    # Build ObserverInput
    observer_input = ObserverInput(
        trigger="user_correction",
        current_global_context=serialized_context,
        context_management_guidance=guidance,
        correction=correction,
        what_was_corrected=what_was_corrected,
    )

    # Call Observer
    output = await observer.observe(observer_input)

    # Apply updates if needed
    if output.should_update:
        context_manager.apply_updates(output.updates)

    return output


async def trigger_significant_log(
    observer: ObserverAgent,
    context_manager: GlobalContextManager,
    config: ObserverTriggerConfig,
    entry: Entry,
    parsed_data: dict[str, Any],
    active_domain_context: ActiveDomainContext,
    detector: SignificantEntryDetector | None = None,
) -> ObserverOutput | None:
    """Trigger Observer after parsing a potentially notable entry.

    First checks if the entry is "significant" using the detector.
    If significant, builds ObserverInput and invokes Observer.

    Args:
        observer: The ObserverAgent instance.
        context_manager: GlobalContextManager for context operations.
        config: Trigger configuration.
        entry: The log entry to evaluate.
        parsed_data: Parsed domain data from the entry.
        active_domain_context: Active domain context with guidance.
        detector: Optional custom detector (uses DefaultSignificantEntryDetector if None).

    Returns:
        ObserverOutput if trigger is enabled, entry is significant, and Observer ran.
        None otherwise.
    """
    if not config.enable_significant_log:
        return None

    # Use provided detector or default
    actual_detector = detector or DefaultSignificantEntryDetector()

    # Check if entry is significant
    if not actual_detector.is_significant(entry, parsed_data):
        return None

    # Get combined guidance
    guidance = get_combined_context_guidance(active_domain_context)

    # Get and serialize current global context
    context = context_manager.read_context()
    serialized_context = serialize_global_context(context)

    # Build ObserverInput
    observer_input = ObserverInput(
        trigger="significant_log",
        current_global_context=serialized_context,
        context_management_guidance=guidance,
        new_entry=entry.model_dump(),
    )

    # Call Observer
    output = await observer.observe(observer_input)

    # Apply updates if needed
    if output.should_update:
        context_manager.apply_updates(output.updates)

    return output


async def trigger_periodic(
    observer: ObserverAgent,
    context_manager: GlobalContextManager,
    storage: StorageRepository,
    config: ObserverTriggerConfig,
    active_domain_context: ActiveDomainContext,
    since_datetime: datetime | None = None,
) -> list[ObserverOutput]:
    """Trigger Observer for periodic batch processing of recent logs.

    Fetches entries since the specified datetime (or last 24 hours)
    and processes each through trigger_significant_log.

    Args:
        observer: The ObserverAgent instance.
        context_manager: GlobalContextManager for context operations.
        storage: StorageRepository for fetching entries.
        config: Trigger configuration.
        active_domain_context: Active domain context with guidance.
        since_datetime: Start datetime for fetching entries (default: 24 hours ago).

    Returns:
        List of ObserverOutput from processing significant entries.
    """
    if not config.enable_periodic:
        return []

    # Calculate date range
    if since_datetime is None:
        since_datetime = datetime.now() - timedelta(hours=24)

    # Build DateRange for query
    date_range = DateRange(start=since_datetime.date(), end=datetime.now().date())

    # Fetch entries
    entries = storage.get_entries_by_date_range(date_range.start, date_range.end)

    # Process each entry through significant_log trigger
    results: list[ObserverOutput] = []
    for entry in entries:
        # Use empty parsed_data as we're doing batch processing
        output = await trigger_significant_log(
            observer=observer,
            context_manager=context_manager,
            config=config,
            entry=entry,
            parsed_data={},
            active_domain_context=active_domain_context,
        )
        if output is not None:
            results.append(output)

    return results


# =============================================================================
# LangGraph Node
# =============================================================================


def _determine_trigger_type(state: SessionState) -> Literal["post_query", "user_correction", "significant_log"]:
    """Determine which trigger type to use based on state.

    Args:
        state: The current session state.

    Returns:
        The trigger type to use.
    """
    if state.get("correction_result"):
        return "user_correction"
    elif state.get("input_type") == "LOG":
        return "significant_log"
    else:
        return "post_query"


async def observe_node(state: SessionState) -> dict[str, Any]:
    """LangGraph node for Observer trigger execution.

    Determines the appropriate trigger type from state context,
    calls the corresponding trigger function, and updates state.

    Note: This node requires Observer components to be injected via
    state or a registry mechanism. If not configured, it returns
    gracefully without error.

    Args:
        state: The current session state.

    Returns:
        Dict with keys:
        - next_state: "COMPLETE" (always)
        - observer_output: ObserverOutput.model_dump() or None
    """
    # Check if Observer components are configured in state
    # These would typically be injected via a registry or state initialization
    observer = state.get("_observer")  # type: ignore[typeddict-item]
    context_manager = state.get("_context_manager")  # type: ignore[typeddict-item]
    config = state.get("_observer_trigger_config")  # type: ignore[typeddict-item]
    active_domain_context_dict = state.get("active_domain_context")

    # If Observer not configured, skip gracefully
    if observer is None or context_manager is None or config is None:
        return {"next_state": "COMPLETE", "observer_output": None}

    # Reconstruct ActiveDomainContext from dict
    if active_domain_context_dict is None:
        return {"next_state": "COMPLETE", "observer_output": None}

    active_domain_context = ActiveDomainContext.model_validate(active_domain_context_dict)

    # Determine trigger type
    trigger_type = _determine_trigger_type(state)

    output: ObserverOutput | None = None

    if trigger_type == "user_correction":
        # Extract correction info from state
        correction_result = state.get("correction_result")
        if correction_result:
            correction_target = state.get("correction_target") or "unknown"
            output = await trigger_user_correction(
                observer=observer,
                context_manager=context_manager,
                config=config,
                correction=state.get("raw_input", ""),
                what_was_corrected=correction_target,
                active_domain_context=active_domain_context,
            )

    elif trigger_type == "significant_log":
        # For significant_log, we would need the parsed entry from state
        # This is a simplified implementation - full integration would
        # extract the Entry from state after STORE node
        pass  # Significant log handling requires Entry from state

    else:  # post_query
        # Extract query info from state
        query = state.get("query") or state.get("raw_input", "")
        analysis_dict = state.get("analysis")
        response = state.get("final_response") or state.get("draft_response") or ""

        if analysis_dict:
            analysis = AnalyzerOutput.model_validate(analysis_dict)
            output = await trigger_post_query(
                observer=observer,
                context_manager=context_manager,
                config=config,
                query=query,
                analysis=analysis,
                response=response,
                active_domain_context=active_domain_context,
            )

    return {
        "next_state": "COMPLETE",
        "observer_output": output.model_dump() if output else None,
    }
