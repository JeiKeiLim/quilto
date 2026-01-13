"""Synthesizer agent for generating user-facing responses.

This module provides the SynthesizerAgent class which generates natural language
responses based on analysis results, grounded in evidence and using domain-appropriate
terminology.
"""

from quilto.agents.models import (
    AnalyzerOutput,
    Gap,
    SynthesizerInput,
    SynthesizerOutput,
    Verdict,
)
from quilto.llm import LLMClient


class SynthesizerAgent:
    """Synthesizer agent for generating user-facing responses.

    Generates natural language responses based on analysis findings,
    using domain vocabulary for proper terminology and citing evidence
    to support claims. Handles both complete and partial answers.

    Attributes:
        llm_client: The LLM client for making inference calls.

    Example:
        >>> from quilto import LLMClient, load_llm_config
        >>> from quilto.agents import (
        ...     SynthesizerAgent, SynthesizerInput, AnalyzerOutput, QueryType
        ... )
        >>> config = load_llm_config(Path("llm-config.yaml"))
        >>> client = LLMClient(config)
        >>> synthesizer = SynthesizerAgent(client)
        >>> input = SynthesizerInput(
        ...     query="How has my bench press progressed?",
        ...     query_type=QueryType.INSIGHT,
        ...     analysis=analyzer_output,
        ...     vocabulary={"pr": "personal record"},
        ...     response_style="concise"
        ... )
        >>> output = await synthesizer.synthesize(input)
        >>> print(output.response)
    """

    AGENT_NAME = "synthesizer"

    def __init__(self, llm_client: LLMClient) -> None:
        """Initialize the Synthesizer agent.

        Args:
            llm_client: LLM client configured with tier settings.
        """
        self.llm_client = llm_client

    def _format_analysis(self, analysis: AnalyzerOutput) -> str:
        """Format analyzer output for the synthesis prompt.

        Args:
            analysis: AnalyzerOutput with findings and patterns.

        Returns:
            Formatted string with findings and patterns.
        """
        lines: list[str] = []

        # Format findings
        lines.append("FINDINGS:")
        if not analysis.findings:
            lines.append("  (No findings)")
        else:
            for i, finding in enumerate(analysis.findings, 1):
                lines.append(f"  [{i}] {finding.claim} (confidence: {finding.confidence})")
                if finding.evidence:
                    lines.append(f"      Evidence: {', '.join(finding.evidence)}")

        # Format patterns
        lines.append("\nPATTERNS IDENTIFIED:")
        if not analysis.patterns_identified:
            lines.append("  (No patterns identified)")
        else:
            for pattern in analysis.patterns_identified:
                lines.append(f"  - {pattern}")

        # Add verdict context
        lines.append(f"\nANALYSIS VERDICT: {analysis.verdict.value}")
        lines.append(f"VERDICT REASONING: {analysis.verdict_reasoning}")

        return "\n".join(lines)

    def _format_vocabulary(self, vocabulary: dict[str, str]) -> str:
        """Format vocabulary for the synthesis prompt.

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

    def _format_gaps(self, gaps: list[Gap]) -> str:
        """Format unanswered gaps for partial answer context.

        Args:
            gaps: List of Gap objects representing unanswered information.

        Returns:
            Formatted string describing gaps.
        """
        if not gaps:
            return "(No gaps)"

        lines: list[str] = []
        for gap in gaps:
            line = f"- {gap.description} ({gap.gap_type.value})"
            if gap.suspected_domain:
                line += f" [may need: {gap.suspected_domain}]"
            lines.append(line)

        return "\n".join(lines)

    def _get_confidence_from_verdict(self, verdict: Verdict) -> str:
        """Map analyzer verdict to synthesizer confidence.

        Args:
            verdict: Analyzer verdict (SUFFICIENT, PARTIAL, INSUFFICIENT).

        Returns:
            Confidence level string ("high", "medium", "low").
        """
        if verdict == Verdict.SUFFICIENT:
            return "high"
        elif verdict == Verdict.PARTIAL:
            return "medium"
        else:  # INSUFFICIENT
            return "low"

    def build_prompt(self, synthesizer_input: SynthesizerInput) -> str:
        """Build the system prompt for response generation.

        Args:
            synthesizer_input: The SynthesizerInput containing query and analysis.

        Returns:
            The formatted system prompt string.
        """
        # Format components
        vocabulary_text = self._format_vocabulary(synthesizer_input.vocabulary)
        analysis_text = self._format_analysis(synthesizer_input.analysis)
        gaps_text = self._format_gaps(synthesizer_input.unanswered_gaps)

        # Response style guidance
        if synthesizer_input.response_style == "concise":
            style_guidance = """CONCISE STYLE (target: 50-100 words):
- 2-4 sentences for simple queries
- Bullet points for multiple findings
- Direct answer without elaboration
- Focus on key insight, skip background"""
        else:  # detailed
            style_guidance = """DETAILED STYLE (target: 200-400 words):
- Full context and explanation
- All supporting evidence listed with dates
- Nuanced interpretation of patterns
- Include relevant trends and comparisons"""

        # Partial answer handling
        partial_instruction = ""
        if synthesizer_input.is_partial:
            partial_instruction = f"""
=== PARTIAL ANSWER REQUIRED ===

This is a PARTIAL answer (retry limit exceeded). Structure your response as:

"Here's what I can tell you: [answer based on available data]

To provide a more complete answer, I would need: [list gaps]"

UNANSWERED GAPS:
{gaps_text}

IMPORTANT: Be transparent about what you cannot answer. The gaps_disclosed field
must list what information is missing in user-friendly language."""

        # Get expected confidence
        expected_confidence = self._get_confidence_from_verdict(synthesizer_input.analysis.verdict)

        return f"""ROLE: You are a response generation agent that creates user-facing answers.

TASK: Generate a clear, helpful response based on the analysis.

=== VOCABULARY ===
Use proper terminology from the domain:
{vocabulary_text}

=== ANALYSIS RESULTS ===
{analysis_text}

=== INPUT ===
Query: {synthesizer_input.query}
Query type: {synthesizer_input.query_type.value}
Response style: {synthesizer_input.response_style}
Is partial answer: {synthesizer_input.is_partial}
{partial_instruction}

=== RESPONSE STYLE GUIDANCE ===
{style_guidance}

=== RESPONSE GUIDELINES ===

1. Address what the user asked directly
2. Support claims with evidence (cite dates/entries from findings)
3. Use domain-appropriate terminology from vocabulary
4. Match requested response style (concise vs detailed)
5. If partial: clearly state what you can answer and what remains unknown

=== CONFIDENCE MAPPING ===

Based on analysis verdict ({synthesizer_input.analysis.verdict.value}),
set confidence to: {expected_confidence}

=== OUTPUT (JSON) ===

Respond with a JSON object containing:
- response: string (the user-facing answer, required, non-empty)
- key_points: list of strings (main takeaways, 2-5 points)
- evidence_cited: list of strings (dates/entries referenced, e.g., "2026-01-10: bench 185x5")
- gaps_disclosed: list of strings (empty if not partial, otherwise gaps in user-friendly language)
- confidence: "{expected_confidence}" (based on analysis verdict)"""

    async def synthesize(self, synthesizer_input: SynthesizerInput) -> SynthesizerOutput:
        """Generate a user-facing response from analysis results.

        Creates a natural language response based on analyzer findings,
        using domain vocabulary and citing evidence to support claims.

        Args:
            synthesizer_input: SynthesizerInput with query, analysis, and context.

        Returns:
            SynthesizerOutput with response, key points, evidence, and confidence.

        Raises:
            ValueError: If query is empty or whitespace-only.
        """
        if not synthesizer_input.query or not synthesizer_input.query.strip():
            raise ValueError("query cannot be empty or whitespace-only")

        system_prompt = self.build_prompt(synthesizer_input)
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": synthesizer_input.query},
        ]

        result = await self.llm_client.complete_structured(
            agent=self.AGENT_NAME,
            messages=messages,
            response_model=SynthesizerOutput,
        )
        assert isinstance(result, SynthesizerOutput), f"Expected SynthesizerOutput, got {type(result)}"
        return result
