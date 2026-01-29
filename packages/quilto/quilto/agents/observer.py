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
        conversation_context = observer_input.conversation_context or "(none)"
        return f"""=== USER INPUT (extract insights from here ONLY) ===
User Query: {observer_input.query}

=== SYSTEM ANALYSIS (for context only, NOT for persistence) ===
{analysis_str}

=== AGENT RESPONSE (NEVER extract insights from here) ===
{observer_input.response}

=== SESSION CONVERSATION CONTEXT ===
{conversation_context}

NOTE ON USER INPUT VS AGENT OUTPUT:
- USER INPUT (query): The ONLY source for extracting preferences, patterns, facts
- AGENT RESPONSE: Contains recommendations and advice - NEVER persist as user preferences
- Analysis: System-generated context - use for understanding, not for persistence

NOTE ON SESSION VS GLOBAL CONTEXT:
- SESSION context: Temporary facts from current conversation (e.g., "user asked about leg workout")
- GLOBAL context: Persistent preferences/patterns (e.g., "user prefers metric units")
- DO NOT add session-specific facts to global context
- Only add persistent insights discovered during this session
- Insights MUST come from explicit user statements, not agent suggestions"""

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

=== USER VS AGENT CONTENT (CRITICAL) ===

ONLY extract insights from the "User Query" field (user input).
NEVER persist anything from the "Agent Response" field (agent output).

The user query is what the user actually said. The agent response contains recommendations,
suggestions, and advice - these are NOT user preferences or facts.

EXAMPLES:

USER QUERY: "I haven't gone to gym today. What should I do?"
AGENT RESPONSE: "You could try a light mobility workout."

BAD: {{"preference": "light or mobility-focused workout"}}  -- FABRICATED from agent
GOOD: {{"should_update": false}}  -- User asked question, stated no preference

USER QUERY: "I prefer morning workouts"
AGENT RESPONSE: "That's great!"

GOOD: {{"preference": "morning workouts", "confidence": "certain"}}  -- User explicitly stated

USER QUERY: "Should I force myself to go to gym despite low motivation?"
AGENT RESPONSE: "Consider a rest day or light session."

BAD: {{"pattern": "struggles with motivation"}}  -- Interpretation, not stated
GOOD: {{"should_update": false}}  -- User asked a question, stated nothing to persist

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

=== WHAT NOT TO PERSIST (CRITICAL) ===

NEVER persist any of the following:
- Agent recommendations (e.g., "light workout", "rest day advice")
- Agent interpretations of user intent
- Per-session facts (belong in parsed entries, not global context)
- Per-workout data (durations, distances, weights from a single workout)
- Inferences not explicitly stated by user
- Questions user asked (these are not preferences)

These should ONLY be in global context if explicitly stated by user:
- Preferences: User must say "I prefer X" or "I like X" or similar
- Patterns: User must describe their typical behavior explicitly
- Facts: User must state the fact directly

=== KEY CONSOLIDATION RULES ===

- Same key = supersede old value (don't create "unit_preference_2")
- Related insights = merge into one (don't list every workout time separately)
- Confidence transitions: tentative → likely → certain (never downgrade)

=== SOURCE FIELD REQUIREMENTS (CRITICAL) ===

The `source` field MUST quote the exact user text that justifies the update.
No quote = no update. Vague sources are not acceptable.

CORRECT: "source": "user said 'I prefer running outdoors'"
CORRECT: "source": "user stated 'I usually workout in the morning'"
WRONG: "source": "post_query: user asked about motivation"  -- No quote, vague
WRONG: "source": "inferred from context"  -- No user quote

If you cannot quote exact user text, set should_update: false.

=== OUTPUT (JSON) ===

Respond with a JSON object containing:
- should_update: boolean (true if any meaningful insights to add)
- updates: list of objects, each with:
  - category: "preference" | "pattern" | "fact" | "insight"
  - key: string (unique identifier, e.g., "unit_preference", "typical_schedule")
  - value: string (the value to store)
  - confidence: "certain" | "likely" | "tentative"
  - source: string (MUST quote exact user text, e.g., "user said 'I prefer metric units'")
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
