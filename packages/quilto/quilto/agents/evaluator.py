"""Evaluator agent for quality-checking responses.

This module provides the EvaluatorAgent class which quality-checks synthesized
responses on four dimensions: accuracy, relevance, safety, and completeness.
Returns PASS/FAIL verdict with specific feedback for retry.
"""

from quilto.agents.models import (
    AnalyzerOutput,
    EvaluationDimension,
    EvaluationFeedback,
    EvaluatorInput,
    EvaluatorOutput,
    Verdict,
)
from quilto.llm import LLMClient


class EvaluatorAgent:
    """Evaluator agent for quality-checking synthesized responses.

    Quality-checks responses on four dimensions: accuracy, relevance,
    safety, and completeness. Uses strict AND logic where ANY dimension
    failure results in overall FAIL. Provides specific, actionable feedback
    for retry when evaluation fails.

    Attributes:
        llm_client: The LLM client for making inference calls.

    Example:
        >>> from quilto import LLMClient, load_llm_config
        >>> from quilto.agents import (
        ...     EvaluatorAgent, EvaluatorInput, AnalyzerOutput
        ... )
        >>> config = load_llm_config(Path("llm-config.yaml"))
        >>> client = LLMClient(config)
        >>> evaluator = EvaluatorAgent(client)
        >>> input = EvaluatorInput(
        ...     query="How has my bench press progressed?",
        ...     response="Your bench press increased by 10 lbs",
        ...     analysis=analyzer_output,
        ...     entries_summary="5 entries: Jan 3 175x5, Jan 10 185x5",
        ...     evaluation_rules=["Do not speculate beyond data"],
        ...     attempt_number=1
        ... )
        >>> output = await evaluator.evaluate(input)
        >>> print(evaluator.is_passed(output))
    """

    AGENT_NAME = "evaluator"

    def __init__(self, llm_client: LLMClient) -> None:
        """Initialize the Evaluator agent.

        Args:
            llm_client: LLM client configured with tier settings.
        """
        self.llm_client = llm_client

    def _format_analysis(self, analysis: AnalyzerOutput) -> str:
        """Format analyzer output for the evaluation prompt.

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

        return "\n".join(lines)

    def _format_evaluation_rules(self, rules: list[str]) -> str:
        """Format evaluation rules for the prompt.

        Args:
            rules: List of domain-specific evaluation rules.

        Returns:
            Formatted string with numbered rules.
        """
        if not rules:
            return "(No domain-specific evaluation rules)"

        lines: list[str] = []
        for i, rule in enumerate(rules, 1):
            lines.append(f"  {i}. {rule}")

        return "\n".join(lines)

    def _format_previous_feedback(self, feedback: list[EvaluationFeedback]) -> str:
        """Format previous evaluation feedback for retry context.

        Args:
            feedback: List of EvaluationFeedback from previous attempts.

        Returns:
            Formatted string with previous feedback.
        """
        if not feedback:
            return "(First attempt - no previous feedback)"

        lines: list[str] = []
        for i, fb in enumerate(feedback, 1):
            lines.append(f"  [{i}] Issue: {fb.issue}")
            lines.append(f"      Suggestion: {fb.suggestion}")
            if fb.affected_claim:
                lines.append(f"      Affected claim: {fb.affected_claim}")

        return "\n".join(lines)

    def _format_entries_summary(self, entries_summary: str) -> str:
        """Format entries summary for the prompt.

        Args:
            entries_summary: Summary of retrieved entries.

        Returns:
            Formatted string with entries summary.
        """
        return entries_summary

    def _format_user_responses(self, user_responses: dict[str, str]) -> str:
        """Format user responses for the prompt.

        Args:
            user_responses: Map of gap_addressed to user's answer.

        Returns:
            Formatted string showing what the user provided.
        """
        if not user_responses:
            return ""

        lines: list[str] = []
        for gap, answer in user_responses.items():
            lines.append(f"- {gap}: {answer}")
        return "\n".join(lines)

    def build_prompt(self, evaluator_input: EvaluatorInput) -> str:
        """Build the system prompt for response evaluation.

        Args:
            evaluator_input: The EvaluatorInput containing query, response, and context.

        Returns:
            The formatted system prompt string.
        """
        # Format components
        analysis_text = self._format_analysis(evaluator_input.analysis)
        rules_text = self._format_evaluation_rules(evaluator_input.evaluation_rules)
        feedback_text = self._format_previous_feedback(evaluator_input.previous_feedback)
        entries_text = self._format_entries_summary(evaluator_input.entries_summary)

        # Build user responses section if present
        user_responses_section = ""
        if evaluator_input.user_responses:
            formatted_responses = self._format_user_responses(evaluator_input.user_responses)
            user_responses_section = f"""
=== USER CLARIFICATION CONTEXT ===

The following information was gathered directly from the user via clarification questions.
This information is AUTHORITATIVE and should NOT be flagged as speculation.

{formatted_responses}

IMPORTANT EVALUATION RULES FOR CLARIFICATION CONTEXT:
1. Information derived from user answers is NOT speculation - it is user-provided data
2. Do NOT suggest "ask the user" for information already provided above
3. Treat user answers as valid evidence, equivalent to stored log entries
4. The response correctly uses this context if it references or builds upon these answers
"""

        # Retry context
        retry_instruction = ""
        if evaluator_input.attempt_number > 1:
            retry_instruction = f"""
=== RETRY CONTEXT ===

This is attempt #{evaluator_input.attempt_number}. Previous evaluation(s) failed.
Review the previous feedback carefully - the response should have addressed these issues.

PREVIOUS FEEDBACK:
{feedback_text}

CHECK: Has the response improved based on the previous feedback?"""

        return f"""ROLE: You are a quality assurance agent. \
Your job is to critically assess responses before they reach the user.

TASK: Evaluate the response on multiple dimensions. Be strict but fair.

=== EVALUATION DIMENSIONS ===

1. ACCURACY
   - Every claim must be supported by evidence from the analysis
   - Speculation without data = INSUFFICIENT
   - Check claims against the analysis findings

2. RELEVANCE
   - Response must address what the user actually asked
   - Tangential information without answering the question = INSUFFICIENT

3. SAFETY
   - Apply domain-specific safety rules below
   - Harmful or dangerous recommendations = INSUFFICIENT

4. COMPLETENESS
   - All parts of the query should be addressed
   - Missing major aspects = INSUFFICIENT

=== DOMAIN SAFETY RULES ===
{rules_text}

=== VERDICT LOGIC ===

CRITICAL: Strict AND logic applies:
- If ANY dimension is INSUFFICIENT → overall_verdict = INSUFFICIENT
- If ALL dimensions are SUFFICIENT → overall_verdict = SUFFICIENT

=== ANALYSIS RESULTS ===
{analysis_text}

=== AVAILABLE EVIDENCE ===
{entries_text}
{user_responses_section}
=== INPUT ===

Original query: {evaluator_input.query}
Response to evaluate: {evaluator_input.response}
Attempt number: {evaluator_input.attempt_number}
{retry_instruction}

=== RECOMMENDATION LOGIC ===

Based on verdict and context:
- ALL dimensions SUFFICIENT → "accept"
- FAIL + attempt < 3 + issues fixable → "retry_with_feedback"
- FAIL + accuracy issues suggest missing data → "retry_with_more_context"
- FAIL + attempt >= 3 → "give_partial"

=== OUTPUT (JSON) ===

Respond with a JSON object containing:
- dimensions: list of objects with dimension, verdict, reasoning, issues
  - dimension: "accuracy" | "relevance" | "safety" | "completeness"
  - verdict: "sufficient" (PASS) or "insufficient" (FAIL)
  - reasoning: explanation for verdict (required, non-empty)
  - issues: list of specific issues found (empty if passed)
- overall_verdict: "sufficient" or "insufficient" (based on strict AND logic)
- feedback: list of objects with issue, suggestion, affected_claim (empty if all passed)
- recommendation: "accept" | "retry_with_feedback" | "retry_with_more_context" | "give_partial"

For any INSUFFICIENT verdict, provide specific, actionable feedback that can guide a retry."""

    async def evaluate(self, evaluator_input: EvaluatorInput) -> EvaluatorOutput:
        """Evaluate a synthesized response for quality.

        Checks the response on four dimensions: accuracy, relevance,
        safety, and completeness. Uses strict AND logic where any
        dimension failure results in overall FAIL.

        Args:
            evaluator_input: EvaluatorInput with query, response, and context.

        Returns:
            EvaluatorOutput with dimension evaluations, verdict, and recommendation.

        Raises:
            ValueError: If query or response is empty or whitespace-only.
        """
        if not evaluator_input.query or not evaluator_input.query.strip():
            raise ValueError("query cannot be empty or whitespace-only")

        if not evaluator_input.response or not evaluator_input.response.strip():
            raise ValueError("response cannot be empty or whitespace-only")

        system_prompt = self.build_prompt(evaluator_input)
        messages = [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": f"Query: {evaluator_input.query}\n\nResponse to evaluate: {evaluator_input.response}",
            },
        ]

        result = await self.llm_client.complete_structured(
            agent=self.AGENT_NAME,
            messages=messages,
            response_model=EvaluatorOutput,
        )
        assert isinstance(result, EvaluatorOutput), f"Expected EvaluatorOutput, got {type(result)}"
        return result

    def is_passed(self, output: EvaluatorOutput) -> bool:
        """Check if evaluation passed.

        Args:
            output: EvaluatorOutput from evaluation.

        Returns:
            True if overall_verdict is SUFFICIENT.
        """
        return output.overall_verdict == Verdict.SUFFICIENT

    def get_failed_dimensions(self, output: EvaluatorOutput) -> list[EvaluationDimension]:
        """Get all dimensions that failed.

        Args:
            output: EvaluatorOutput from evaluation.

        Returns:
            List of EvaluationDimension with INSUFFICIENT verdict.
        """
        return [d for d in output.dimensions if d.verdict == Verdict.INSUFFICIENT]

    def get_all_issues(self, output: EvaluatorOutput) -> list[str]:
        """Aggregate all issues from failed dimensions.

        Args:
            output: EvaluatorOutput from evaluation.

        Returns:
            Flat list of all issue strings from failed dimensions.
        """
        failed = self.get_failed_dimensions(output)
        issues: list[str] = []
        for dim in failed:
            issues.extend(dim.issues)
        return issues

    def should_retry(
        self,
        output: EvaluatorOutput,
        attempt_number: int,
        max_retries: int = 2,
    ) -> bool:
        """Determine if evaluation should trigger a retry.

        Args:
            output: EvaluatorOutput from evaluation.
            attempt_number: Current attempt number (1-based).
            max_retries: Maximum number of retries allowed.

        Returns:
            True if evaluation failed AND attempt_number < max_retries.
        """
        return not self.is_passed(output) and attempt_number < max_retries
