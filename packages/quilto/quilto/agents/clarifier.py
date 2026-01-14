"""Clarifier agent for requesting missing information from users.

This module provides the ClarifierAgent class which generates clear,
specific questions to fill information gaps that cannot be retrieved
from stored data (subjective or clarification gaps only).
"""

from quilto.agents.models import (
    ClarifierInput,
    ClarifierOutput,
    Gap,
    GapType,
    RetrievalAttempt,
)
from quilto.llm import LLMClient


class ClarifierAgent:
    """Clarifier agent for requesting missing information from users.

    Generates clear, specific questions to fill information gaps when
    the system cannot proceed without user input. Only asks about
    non-retrievable gaps (SUBJECTIVE, CLARIFICATION) and avoids
    re-asking questions the user has already answered.

    Attributes:
        llm_client: The LLM client for making inference calls.

    Example:
        >>> from quilto import LLMClient, load_llm_config
        >>> from quilto.agents import (
        ...     ClarifierAgent, ClarifierInput, Gap, GapType
        ... )
        >>> config = load_llm_config(Path("llm-config.yaml"))
        >>> client = LLMClient(config)
        >>> clarifier = ClarifierAgent(client)
        >>> input = ClarifierInput(
        ...     original_query="How should I adjust my workout?",
        ...     gaps=[Gap(
        ...         description="Current energy level unknown",
        ...         gap_type=GapType.SUBJECTIVE,
        ...         severity="critical"
        ...     )],
        ...     vocabulary={"rpe": "rate of perceived exertion"},
        ...     retrieval_history=[],
        ...     previous_clarifications=[]
        ... )
        >>> output = await clarifier.clarify(input)
        >>> print(output.questions[0].question)
    """

    AGENT_NAME = "clarifier"
    MAX_QUESTIONS = 3

    def __init__(self, llm_client: LLMClient) -> None:
        """Initialize the Clarifier agent.

        Args:
            llm_client: LLM client configured with tier settings.
        """
        self.llm_client = llm_client

    def filter_non_retrievable_gaps(self, gaps: list[Gap]) -> list[Gap]:
        """Filter gaps to only non-retrievable types.

        Non-retrievable gaps are those that only the user can answer:
        - SUBJECTIVE: Current feelings, preferences, goals
        - CLARIFICATION: Ambiguous parts of the query

        Args:
            gaps: List of Gap objects from Analyzer.

        Returns:
            List of gaps with gap_type SUBJECTIVE or CLARIFICATION.
        """
        non_retrievable_types = {GapType.SUBJECTIVE, GapType.CLARIFICATION}
        return [g for g in gaps if g.gap_type in non_retrievable_types]

    def _format_gaps(self, gaps: list[Gap]) -> str:
        """Format gaps for the clarifier prompt.

        Args:
            gaps: List of Gap objects to format.

        Returns:
            Formatted string with gap details.
        """
        if not gaps:
            return "(No gaps to address)"

        lines: list[str] = []
        for i, gap in enumerate(gaps, 1):
            line = f"[{i}] {gap.description}"
            line += f"\n    Type: {gap.gap_type.value}"
            line += f"\n    Severity: {gap.severity}"
            lines.append(line)

        return "\n\n".join(lines)

    def _format_retrieval_history(self, history: list[RetrievalAttempt]) -> str:
        """Format retrieval history for context.

        Args:
            history: List of RetrievalAttempt records.

        Returns:
            Formatted string describing what was already searched.
        """
        if not history:
            return "(No retrieval attempts recorded)"

        lines: list[str] = []
        for attempt in history:
            line = f"- {attempt.strategy}: {attempt.summary}"
            line += f" ({attempt.entries_found} entries found)"
            lines.append(line)

        return "\n".join(lines)

    def _format_previous_clarifications(self, previous: list[str]) -> str:
        """Format previously asked questions to avoid re-asking.

        Args:
            previous: List of questions already asked.

        Returns:
            Formatted string with previous questions.
        """
        if not previous:
            return "(No previous clarifications - this is the first attempt)"

        lines: list[str] = []
        for i, question in enumerate(previous, 1):
            lines.append(f"  {i}. {question}")

        return "\n".join(lines)

    def _format_vocabulary(self, vocabulary: dict[str, str]) -> str:
        """Format vocabulary for the clarifier prompt.

        Args:
            vocabulary: Term normalization mapping.

        Returns:
            Formatted string with vocabulary terms.
        """
        if not vocabulary:
            return "(No domain vocabulary provided)"

        lines: list[str] = []
        for term, definition in vocabulary.items():
            lines.append(f"- {term}: {definition}")

        return "\n".join(lines)

    def _format_clarification_patterns(self, patterns: dict[str, list[str]]) -> str:
        """Format clarification patterns for the prompt.

        Args:
            patterns: Gap type to example questions mapping. Keys should be
                uppercase strings like "SUBJECTIVE", "CLARIFICATION".

        Returns:
            Formatted string with domain-specific example questions.
        """
        if not patterns:
            return "(No domain-specific patterns provided)"

        lines: list[str] = []
        for gap_type, examples in patterns.items():
            lines.append(f"For {gap_type} gaps, consider questions like:")
            for example in examples:
                lines.append(f"  - {example}")
            lines.append("")

        return "\n".join(lines).strip()

    def has_questions(self, output: ClarifierOutput) -> bool:
        """Check if output contains any questions.

        Args:
            output: ClarifierOutput from clarify method.

        Returns:
            True if there is at least one question.
        """
        return len(output.questions) > 0

    def build_prompt(self, clarifier_input: ClarifierInput) -> str:
        """Build the system prompt for question generation.

        Args:
            clarifier_input: The ClarifierInput containing query and gaps.

        Returns:
            The formatted system prompt string.
        """
        # Filter to non-retrievable gaps only
        non_retrievable_gaps = self.filter_non_retrievable_gaps(clarifier_input.gaps)

        # Format components
        vocabulary_text = self._format_vocabulary(clarifier_input.vocabulary)
        gaps_text = self._format_gaps(non_retrievable_gaps)
        retrieval_text = self._format_retrieval_history(clarifier_input.retrieval_history)
        previous_text = self._format_previous_clarifications(clarifier_input.previous_clarifications)
        patterns_text = self._format_clarification_patterns(clarifier_input.clarification_patterns)

        return f"""ROLE: You are a clarification agent that requests missing information from users.

TASK: Generate clear, concise questions to fill information gaps.

=== VOCABULARY ===
{vocabulary_text}

=== INPUT ===
Original query: {clarifier_input.original_query}

Gaps to address:
{gaps_text}

What we've already searched:
{retrieval_text}

Previous clarifications asked:
{previous_text}

=== RULES ===

1. Only ask about gaps that cannot be retrieved from stored data
2. Don't re-ask questions the user has already answered
3. Use domain-appropriate terminology from vocabulary
4. Keep questions concise and specific
5. Offer multiple-choice options when applicable
6. Explain WHY you're asking (context_explanation)
7. Maximum 3 questions per interaction

=== QUESTION GUIDELINES ===

Good: "What time did this happen?" (specific, actionable)
Bad: "Can you tell me more?" (vague, unhelpful)

Good: "Were you feeling tired or energized?" (options provided)
Bad: "How were you feeling?" (too open-ended)

=== DOMAIN-SPECIFIC PATTERNS ===
{patterns_text}

Use these patterns as inspiration. Adapt them to the specific context.

=== GAP TYPES YOU SHOULD ASK ABOUT ===

- SUBJECTIVE: Current feelings, preferences, goals that only the user knows
- CLARIFICATION: Ambiguous parts of the query that need clarification

=== GAP TYPES YOU SHOULD NOT ASK ABOUT ===

- TEMPORAL, TOPICAL, CONTEXTUAL: These can be retrieved from stored data

=== FALLBACK ACTION ===

Provide a fallback_action describing what can still be done if the user
declines to answer the questions. Example: "Provide a general answer based
on available data" or "Explain common patterns without personalization"

=== OUTPUT (JSON) ===

Respond with a JSON object containing:
- questions: list of objects with question, gap_addressed, options, required
  - question: string (the question to ask, required, non-empty)
  - gap_addressed: string (which gap this fills, required, non-empty)
  - options: list of strings or null (multiple choice if applicable)
  - required: boolean (whether the question must be answered)
- context_explanation: string (why we're asking, required, non-empty)
- fallback_action: string (what to do if user declines, required, non-empty)

IMPORTANT: Generate at most 3 questions. Prioritize critical gaps."""

    async def clarify(self, clarifier_input: ClarifierInput) -> ClarifierOutput:
        """Generate clarification questions for the user.

        Analyzes the gaps and generates clear, specific questions to fill
        information that cannot be retrieved from stored data.

        Args:
            clarifier_input: ClarifierInput with query, gaps, and context.

        Returns:
            ClarifierOutput with questions, context, and fallback action.

        Raises:
            ValueError: If original_query is empty or whitespace-only.
        """
        if not clarifier_input.original_query or not clarifier_input.original_query.strip():
            raise ValueError("original_query cannot be empty or whitespace-only")

        # Filter to non-retrievable gaps
        non_retrievable_gaps = self.filter_non_retrievable_gaps(clarifier_input.gaps)

        # Early return if no non-retrievable gaps
        if not non_retrievable_gaps:
            return ClarifierOutput(
                questions=[],
                context_explanation="No clarification needed",
                fallback_action="Proceed with available data",
            )

        system_prompt = self.build_prompt(clarifier_input)
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": clarifier_input.original_query},
        ]

        result = await self.llm_client.complete_structured(
            agent=self.AGENT_NAME,
            messages=messages,
            response_model=ClarifierOutput,
        )
        assert isinstance(result, ClarifierOutput), f"Expected ClarifierOutput, got {type(result)}"

        # Post-process: limit to max questions
        if len(result.questions) > self.MAX_QUESTIONS:
            result = ClarifierOutput(
                questions=result.questions[: self.MAX_QUESTIONS],
                context_explanation=result.context_explanation,
                fallback_action=result.fallback_action,
            )

        return result
