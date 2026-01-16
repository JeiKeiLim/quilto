"""Observer agent for learning patterns and updating global context.

This module provides the ObserverAgent class which learns patterns
from user data and updates the global context for personalization.
"""

from quilto.agents.models import (
    ObserverInput,
    ObserverOutput,
)
from quilto.llm import LLMClient


class ObserverAgent:
    r"""Observer agent for learning patterns and updating global context.

    Runs asynchronously to update the global context based on patterns
    discovered in user data. Triggered by post_query, user_correction,
    or significant_log events.

    Attributes:
        llm_client: The LLM client for making inference calls.

    Example:
        >>> from quilto import LLMClient, load_llm_config
        >>> from quilto.agents import ObserverAgent, ObserverInput
        >>> config = load_llm_config(Path("llm-config.yaml"))
        >>> client = LLMClient(config)
        >>> observer = ObserverAgent(client)
        >>> input = ObserverInput(
        ...     trigger="post_query",
        ...     query="How has my bench press progressed?",
        ...     analysis=analyzer_output,
        ...     response="Your bench press improved by 10 lbs...",
        ...     current_global_context="# Global Context\n...",
        ...     context_management_guidance="Track PRs, workout patterns..."
        ... )
        >>> output = await observer.observe(input)
        >>> if output.should_update:
        ...     print(f"Captured: {output.insights_captured}")
    """

    AGENT_NAME = "observer"

    def __init__(self, llm_client: LLMClient) -> None:
        """Initialize the Observer agent.

        Args:
            llm_client: LLM client configured with tier settings.
        """
        self.llm_client = llm_client

    def _format_post_query_context(self, observer_input: ObserverInput) -> str:
        """Format context for post_query trigger.

        Args:
            observer_input: The ObserverInput containing query context.

        Returns:
            Formatted string with query, analysis, and response.
        """
        analysis_str = str(observer_input.analysis) if observer_input.analysis else "(none)"
        return f"""=== QUERY CONTEXT ===
User Query: {observer_input.query}

Analysis Summary:
{analysis_str}

Response Given:
{observer_input.response}"""

    def _format_correction_context(self, observer_input: ObserverInput) -> str:
        """Format context for user_correction trigger.

        Args:
            observer_input: The ObserverInput containing correction context.

        Returns:
            Formatted string with correction details.
        """
        return f"""=== CORRECTION CONTEXT ===
User Correction: {observer_input.correction}

What Was Corrected: {observer_input.what_was_corrected}

NOTE: User corrections represent explicit preferences and should be treated
with "certain" confidence. The user is directly telling us what they want."""

    def _format_significant_log_context(self, observer_input: ObserverInput) -> str:
        """Format context for significant_log trigger.

        Args:
            observer_input: The ObserverInput containing the new entry.

        Returns:
            Formatted string with entry details.
        """
        entry_str = str(observer_input.new_entry) if observer_input.new_entry else "(none)"
        return f"""=== SIGNIFICANT LOG CONTEXT ===
New Entry:
{entry_str}

Look for:
- Personal records (PRs)
- Milestones (100th workout, first marathon, etc.)
- Major events (competition, race, etc.)
- New activities being started"""

    def _format_trigger_context(self, observer_input: ObserverInput) -> str:
        """Format trigger-specific context.

        Args:
            observer_input: The ObserverInput to format.

        Returns:
            Formatted string based on trigger type.
        """
        if observer_input.trigger == "post_query":
            return self._format_post_query_context(observer_input)
        elif observer_input.trigger == "user_correction":
            return self._format_correction_context(observer_input)
        else:  # significant_log
            return self._format_significant_log_context(observer_input)

    def build_prompt(self, observer_input: ObserverInput) -> str:
        """Build the system prompt for context observation.

        Args:
            observer_input: The ObserverInput containing trigger and context.

        Returns:
            The formatted system prompt string.
        """
        trigger_context = self._format_trigger_context(observer_input)
        current_context = observer_input.current_global_context or "(empty - new user)"

        return f"""ROLE: You are an Observer agent that learns patterns from user data to build a personalized profile.

TASK: Analyze the given context and determine if any new insights should be added to the global context.

=== CURRENT GLOBAL CONTEXT ===
{current_context}

{trigger_context}

=== DOMAIN GUIDANCE ===
{observer_input.context_management_guidance}

=== RULES FOR UPDATES ===

1. BE CONSERVATIVE: Only add updates when you have strong evidence
2. PREFER HIGH CONFIDENCE: Start with "tentative" for new patterns, upgrade to
   "likely" or "certain" only with clear evidence
3. NO SPECULATION: Don't infer preferences without evidence
4. CONSOLIDATE: If updating an existing key, supersede the old value rather than creating duplicates
5. SIZE MANAGEMENT: Aim to keep context concise - consolidate related insights

=== CONFIDENCE LEVELS ===

- "certain": User explicitly stated (corrections, direct preferences)
- "likely": Strong pattern from multiple data points
- "tentative": Initial observation, needs reinforcement

=== CATEGORIES ===

- "preference": User preferences (unit_preference, response_style)
- "pattern": Behavioral patterns (typical_active_days, usual_time_of_day)
- "fact": Objective facts (records, current_routine)
- "insight": Correlations and observations (sleep_performance_correlation)

=== TRIGGER-SPECIFIC GUIDANCE ===

For "post_query": Look for patterns revealed during analysis, inferred preferences
For "user_correction": Treat as explicit preference with "certain" confidence
For "significant_log": Look for milestones, records, major events

=== KEY CONSOLIDATION RULES ===

- Same key = supersede old value (don't create "unit_preference_2")
- Related insights = merge into one (don't list every workout time separately)
- Confidence transitions: tentative → likely → certain (never downgrade)

=== OUTPUT (JSON) ===

Respond with a JSON object containing:
- should_update: boolean (true if any meaningful insights to add)
- updates: list of objects, each with:
  - category: "preference" | "pattern" | "fact" | "insight"
  - key: string (unique identifier, e.g., "unit_preference", "typical_schedule")
  - value: string (the value to store)
  - confidence: "certain" | "likely" | "tentative"
  - source: string (what triggered this update, e.g., "post_query: bench press analysis")
- insights_captured: list of strings (human-readable descriptions of what was learned)

If nothing meaningful to update, return should_update=false with empty updates list.

IMPORTANT: Be conservative. It's better to miss an insight than to pollute the context with noise."""

    async def observe(self, observer_input: ObserverInput) -> ObserverOutput:
        """Observe user data and generate context updates.

        Analyzes the input based on trigger type and generates updates
        for the global context.

        Args:
            observer_input: ObserverInput with trigger and context.

        Returns:
            ObserverOutput with updates and insights.

        Raises:
            ValueError: If context_management_guidance is empty or whitespace-only.
        """
        if not observer_input.context_management_guidance.strip():
            raise ValueError("context_management_guidance cannot be empty or whitespace-only")

        system_prompt = self.build_prompt(observer_input)
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Trigger: {observer_input.trigger}"},
        ]

        result = await self.llm_client.complete_structured(
            agent=self.AGENT_NAME,
            messages=messages,
            response_model=ObserverOutput,
        )
        assert isinstance(result, ObserverOutput), f"Expected ObserverOutput, got {type(result)}"

        return result
