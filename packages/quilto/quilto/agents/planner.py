"""Planner agent for query decomposition and retrieval strategy.

This module provides the PlannerAgent class which decomposes queries,
classifies dependencies, creates retrieval strategies, and handles
domain expansion and clarification requests.
"""

from quilto.agents.models import (
    Gap,
    GapType,
    PlannerInput,
    PlannerOutput,
)
from quilto.llm import LLMClient


class PlannerAgent:
    """Planner agent for query decomposition and retrieval strategy.

    Analyzes queries to determine their structure (simple vs complex),
    classifies multi-question dependencies, creates retrieval strategies,
    detects when domain expansion is needed, and re-plans based on feedback.

    Attributes:
        llm_client: The LLM client for making inference calls.

    Example:
        >>> from quilto import LLMClient, load_llm_config
        >>> from quilto.agents import PlannerAgent, PlannerInput, ActiveDomainContext
        >>> config = load_llm_config(Path("llm-config.yaml"))
        >>> client = LLMClient(config)
        >>> planner = PlannerAgent(client)
        >>> input = PlannerInput(
        ...     query="What did I eat yesterday?",
        ...     domain_context=ActiveDomainContext(
        ...         domains_loaded=["nutrition"],
        ...         vocabulary={},
        ...         expertise="Nutrition tracking"
        ...     )
        ... )
        >>> output = await planner.plan(input)
    """

    AGENT_NAME = "planner"

    def __init__(self, llm_client: LLMClient) -> None:
        """Initialize the Planner agent.

        Args:
            llm_client: LLM client configured with tier settings.
        """
        self.llm_client = llm_client

    def _format_gaps(self, gaps: list[Gap]) -> str:
        """Format gaps from analyzer for prompt.

        Args:
            gaps: List of Gap objects from Analyzer agent.

        Returns:
            Formatted string describing gaps.
        """
        if not gaps:
            return "(No gaps identified)"

        lines: list[str] = []
        for gap in gaps:
            line = f"- {gap.description} (type: {gap.gap_type.value}, severity: {gap.severity})"
            if gap.searched:
                line += f", searched: {gap.searched}, found: {gap.found}"
            if gap.outside_current_expertise:
                line += f", outside_expertise: True, suspected_domain: {gap.suspected_domain}"
            lines.append(line)
        return "\n".join(lines)

    def _format_evaluation_feedback(self, planner_input: PlannerInput) -> str:
        """Format evaluation feedback for prompt.

        Args:
            planner_input: The PlannerInput containing optional feedback.

        Returns:
            Formatted string describing feedback.
        """
        if planner_input.evaluation_feedback is None:
            return "(No evaluation feedback)"

        feedback = planner_input.evaluation_feedback
        result = f"Issue: {feedback.issue}\nSuggestion: {feedback.suggestion}"
        if feedback.affected_claim:
            result += f"\nAffected claim: {feedback.affected_claim}"
        return result

    def _format_retrieval_history(self, planner_input: PlannerInput) -> str:
        """Format retrieval history for prompt.

        Args:
            planner_input: The PlannerInput containing retrieval history.

        Returns:
            Formatted string describing previous attempts.
        """
        if not planner_input.retrieval_history:
            return "(No previous retrieval attempts)"

        lines: list[str] = []
        for i, attempt in enumerate(planner_input.retrieval_history, 1):
            strategy = attempt.get("strategy", "unknown")
            params = attempt.get("params", {})
            result = attempt.get("result_summary", "no result")
            lines.append(f"{i}. Strategy: {strategy}, params: {params}, result: {result}")
        return "\n".join(lines)

    def build_prompt(self, planner_input: PlannerInput) -> str:
        """Build the system prompt with planning rules and examples.

        Args:
            planner_input: The PlannerInput containing query and context.

        Returns:
            The formatted system prompt string.
        """
        domain_context = planner_input.domain_context

        # Format available domains
        available_domains_text = "\n".join(f"- {d.name}: {d.description}" for d in domain_context.available_domains)
        if not available_domains_text:
            available_domains_text = "(No additional domains available)"

        # Format vocabulary
        vocabulary_text = "\n".join(f"- {k} → {v}" for k, v in domain_context.vocabulary.items())
        if not vocabulary_text:
            vocabulary_text = "(No vocabulary defined)"

        # Format gaps, feedback, and history
        gaps_text = self._format_gaps(planner_input.gaps_from_analyzer)
        feedback_text = self._format_evaluation_feedback(planner_input)
        history_text = self._format_retrieval_history(planner_input)
        global_context = planner_input.global_context_summary or "(No global context)"

        # Format query type if pre-classified
        query_type_hint = ""
        if planner_input.query_type:
            query_type_hint = f"\nPre-classified query type: {planner_input.query_type.value}"

        return f"""ROLE: You are a query strategist for a context-aware AI system.

TASK: Analyze the query and create an execution plan.

=== QUERY TYPE CLASSIFICATION ===

QUERY TYPES:
- simple: Direct retrieval ("show me X", "what did I X")
- insight: Why/pattern questions ("why is X", "what's the trend")
- recommendation: What should I do questions ("what should I X")
- comparison: Compare X vs Y questions
- correction: Fix previous data

=== QUERY DECOMPOSITION ===

Analyze if the query contains multiple questions. Classify dependencies:

DEPENDENCY TYPES:
- independent: Different subjects/topics, no causal relationship. Can run in parallel.
  Example: "How much did I bench and squat yesterday?" → Two separate queries about different exercises
- dependent: One answer informs another, causal chain. Must run sequentially.
  Example: "Why was bench heavy and how to fix it?" → Need to understand "why" before "how to fix"
- coupled: Same subject/timeframe, really one question. Single pass.
  Example: "What did I eat Tuesday and how much protein?" → Both about Tuesday's food

Single questions should always be classified as COUPLED.

=== RETRIEVAL STRATEGIES ===

Choose the appropriate strategy for each sub-query:

DATE_RANGE: When query mentions time periods
- Parameters: {{"start_date": "YYYY-MM-DD", "end_date": "YYYY-MM-DD"}}
- Use for: "last week", "yesterday", "on Tuesday", specific dates

KEYWORD: When query mentions specific activities/items
- Parameters: {{"keywords": ["term1", "term2"], "semantic_expansion": true/false}}
- Use for: specific exercises, foods, activities

TOPICAL: When query is about patterns/progress
- Parameters: {{"topics": ["topic1"], "related_terms": ["term1"]}}
- Use for: trends, progress, patterns, insights

=== DOMAIN EXPANSION ===

Consider requesting domain expansion when:
- Gaps have outside_current_expertise=True
- Cross-domain correlations are needed
- Query requires expertise not in currently loaded domains

Set domain_expansion_request with suggested domain names and provide expansion_reasoning.

=== CLARIFICATION ===

Request clarification (next_action="clarify") when:
- Gap type is SUBJECTIVE (only user knows the current state)
- Gap type is CLARIFICATION (query itself is ambiguous)
- Information cannot be retrieved from stored data

Add questions to clarify_questions list.

=== NEXT ACTION DECISION ===

Choose next_action based on this logic:
- "retrieve": Normal case, have retrieval instructions ready
- "expand_domain": Need domains not currently loaded (outside_current_expertise gaps)
- "clarify": Gaps are SUBJECTIVE or CLARIFICATION type, or query is ambiguous
- "synthesize": Already have sufficient context (rare, typically on successful retry)

=== RE-PLANNING ON FEEDBACK ===

If evaluation_feedback or gaps_from_analyzer are provided, this is a re-planning request:
- Analyze what went wrong in previous attempt
- Adjust retrieval strategy to address the feedback
- Target specific gaps that were identified
- Explain in reasoning what changed from previous plan

=== INPUT ===

Query: {planner_input.query}{query_type_hint}

Currently loaded domains: {", ".join(domain_context.domains_loaded) or "(none)"}
Domain expertise: {domain_context.expertise or "(not specified)"}

Vocabulary:
{vocabulary_text}

Available domains for expansion:
{available_domains_text}

Gaps from Analyzer:
{gaps_text}

Evaluation feedback (if retry):
{feedback_text}

Retrieval history:
{history_text}

Global context:
{global_context}

=== OUTPUT (JSON) ===

Respond with a JSON object matching this schema:
- original_query: string (the input query)
- query_type: "simple" | "insight" | "recommendation" | "comparison" | "correction"
- sub_queries: list of objects with:
  - id: integer (unique identifier)
  - question: string (the extracted question)
  - retrieval_strategy: "date_range" | "keyword" | "topical"
  - retrieval_params: object with strategy-specific parameters
- dependencies: list of objects {{"from": int, "to": int, "reason": string}}
- execution_strategy: "independent" | "dependent" | "coupled"
- execution_order: list of integers (sub_query IDs in execution order)
- retrieval_instructions: list of objects {{"strategy": string, "params": object, "sub_query_id": int}}
- gaps_status: object mapping gap descriptions to {{"searched": bool, "found": bool}}
- domain_expansion_request: list of strings or null
- expansion_reasoning: string or null
- clarify_questions: list of strings or null
- next_action: "retrieve" | "expand_domain" | "clarify" | "synthesize"
- reasoning: string explaining the planning decisions"""

    async def plan(self, planner_input: PlannerInput) -> PlannerOutput:
        """Create retrieval plan for query.

        Analyzes the query, decomposes it if complex, classifies dependencies,
        selects retrieval strategies, and determines the next action.

        Args:
            planner_input: PlannerInput with query, domain_context, and optional
                feedback from previous attempts.

        Returns:
            PlannerOutput with execution plan and retrieval instructions.

        Raises:
            ValueError: If query is empty or whitespace-only.
        """
        if not planner_input.query or not planner_input.query.strip():
            raise ValueError("query cannot be empty or whitespace-only")

        system_prompt = self.build_prompt(planner_input)
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": planner_input.query},
        ]

        result = await self.llm_client.complete_structured(
            agent=self.AGENT_NAME,
            messages=messages,
            response_model=PlannerOutput,
        )
        return result  # type: ignore[return-value]

    def should_expand_domain(self, gaps: list[Gap]) -> bool:
        """Check if any gaps indicate need for domain expansion.

        Args:
            gaps: List of gaps from Analyzer.

        Returns:
            True if any gap has outside_current_expertise=True.
        """
        return any(gap.outside_current_expertise for gap in gaps)

    def should_clarify(self, gaps: list[Gap]) -> bool:
        """Check if any gaps require user clarification.

        Args:
            gaps: List of gaps from Analyzer.

        Returns:
            True if any gap has type SUBJECTIVE or CLARIFICATION.
        """
        clarification_types = {GapType.SUBJECTIVE, GapType.CLARIFICATION}
        return any(gap.gap_type in clarification_types for gap in gaps)

    def determine_next_action(self, gaps: list[Gap], has_retrieval_instructions: bool) -> str:
        """Determine the next action based on gaps and state.

        This is a helper method for programmatic determination of next_action
        without LLM call. The LLM output should be preferred, but this can
        be used for validation or override.

        Args:
            gaps: List of gaps from Analyzer.
            has_retrieval_instructions: Whether retrieval instructions exist.

        Returns:
            One of: "retrieve", "expand_domain", "clarify", "synthesize"
        """
        # Check for expansion first (highest priority for solvable gaps)
        if self.should_expand_domain(gaps):
            return "expand_domain"

        # Check for clarification (gaps that can't be retrieved)
        if self.should_clarify(gaps):
            return "clarify"

        # Normal case: retrieve if we have instructions
        if has_retrieval_instructions:
            return "retrieve"

        # No gaps and no retrieval needed: synthesize
        return "synthesize"
