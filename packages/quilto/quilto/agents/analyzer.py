"""Analyzer agent for pattern finding and sufficiency assessment.

This module provides the AnalyzerAgent class which analyzes retrieved entries
to find patterns, assess information sufficiency, and determine if a query
can be answered with the available evidence.
"""

from datetime import date, datetime
from typing import Any, cast

from quilto.agents.models import (
    AnalyzerInput,
    AnalyzerOutput,
    Gap,
    RetrievalAttempt,
    SufficiencyEvaluation,
)
from quilto.llm import LLMClient


class AnalyzerAgent:
    """Analyzer agent for pattern finding and sufficiency assessment.

    Analyzes retrieved entries to find patterns and insights, assesses
    information sufficiency, identifies gaps, and generates a verdict
    on whether the query can be answered with available evidence.

    Attributes:
        llm_client: The LLM client for making inference calls.

    Example:
        >>> from quilto import LLMClient, load_llm_config
        >>> from quilto.agents import (
        ...     AnalyzerAgent, AnalyzerInput, ActiveDomainContext, QueryType
        ... )
        >>> config = load_llm_config(Path("llm-config.yaml"))
        >>> client = LLMClient(config)
        >>> analyzer = AnalyzerAgent(client)
        >>> input = AnalyzerInput(
        ...     query="How has my bench press progressed?",
        ...     query_type=QueryType.INSIGHT,
        ...     entries=[entry1, entry2],
        ...     retrieval_summary=[attempt],
        ...     domain_context=ActiveDomainContext(
        ...         domains_loaded=["strength"],
        ...         vocabulary={"pr": "personal record"},
        ...         expertise="Strength training analysis"
        ...     )
        ... )
        >>> output = await analyzer.analyze(input)
        >>> print(output.verdict)
    """

    AGENT_NAME = "analyzer"

    def __init__(self, llm_client: LLMClient) -> None:
        """Initialize the Analyzer agent.

        Args:
            llm_client: LLM client configured with tier settings.
        """
        self.llm_client = llm_client

    def _format_entries(self, entries: list[Any]) -> str:
        """Format entries for the analysis prompt.

        Args:
            entries: List of Entry objects to format.

        Returns:
            Formatted string with entry details (date, content, domain_data).
        """
        if not entries:
            return "(No entries retrieved)"

        lines: list[str] = []
        for i, entry in enumerate(entries, 1):
            # Handle Entry objects or dict-like structures
            entry_repr = repr(entry)  # Get string representation early
            date_str: str = "unknown"
            raw_content: str = entry_repr
            domain_data: Any = None

            if isinstance(entry, dict):
                entry_dict = cast(dict[str, Any], entry)
                date_val = entry_dict.get("date", "unknown")
                date_str = str(date_val) if date_val else "unknown"
                content_val = entry_dict.get("raw_content")
                raw_content = str(content_val) if content_val else entry_repr
                domain_data = entry_dict.get("domain_data")
            else:
                date_val = getattr(entry, "date", "unknown")
                date_str = str(date_val) if date_val else "unknown"
                content_val = getattr(entry, "raw_content", None)
                raw_content = str(content_val) if content_val else entry_repr
                domain_data = getattr(entry, "domain_data", None)

            line = f"[{i}] Date: {date_str}\n    Content: {raw_content}"
            if domain_data:
                line += f"\n    Domain data: {domain_data}"
            lines.append(line)

        return "\n\n".join(lines)

    def _format_retrieval_summary(self, summary: list[RetrievalAttempt]) -> str:
        """Format retrieval attempts for the prompt.

        Args:
            summary: List of RetrievalAttempt records.

        Returns:
            Formatted string describing retrieval attempts.
        """
        if not summary:
            return "(No retrieval attempts recorded)"

        lines: list[str] = []
        for attempt in summary:
            line = f"- Attempt {attempt.attempt_number}: {attempt.strategy}"
            line += f", found {attempt.entries_found} entries"
            line += f"\n  {attempt.summary}"
            lines.append(line)

        return "\n".join(lines)

    def _format_global_context(self, context: str | None) -> str:
        """Format global context for the prompt.

        Args:
            context: Optional global context summary string.

        Returns:
            Formatted context or placeholder if None.
        """
        if context is None or not context.strip():
            return "(No global context available)"
        return context

    def _calculate_temporal_context(self, entries: list[Any]) -> str:
        """Calculate temporal context from entries.

        Computes days since the most recent entry to help the LLM
        understand how current the data is for proper recommendations.

        Args:
            entries: List of Entry objects or dicts with date fields.

        Returns:
            Formatted string with today's date, most recent entry date,
            days since most recent, and oldest entry date.
        """
        if not entries:
            return "(No entries - cannot calculate temporal context)"

        today = date.today()
        dates: list[date] = []
        for entry in entries:
            raw_date: date | str | None = None
            if isinstance(entry, dict):
                entry_dict = cast(dict[str, Any], entry)
                raw_date = cast(date | str | None, entry_dict.get("date"))
            else:
                raw_date = cast(date | str | None, getattr(entry, "date", None))

            if raw_date:
                entry_date: date
                if isinstance(raw_date, str):
                    entry_date = datetime.fromisoformat(raw_date).date()
                elif isinstance(raw_date, datetime):
                    entry_date = raw_date.date()
                else:
                    entry_date = raw_date
                dates.append(entry_date)

        if not dates:
            return "(No valid dates in entries)"

        most_recent = max(dates)
        oldest = min(dates)
        days_since = (today - most_recent).days

        return f"""Today's date: {today}
Most recent entry: {most_recent} ({days_since} days ago)
Oldest entry: {oldest}"""

    def has_critical_gaps(self, evaluation: SufficiencyEvaluation) -> bool:
        """Check if evaluation has any critical gaps.

        Args:
            evaluation: SufficiencyEvaluation from analysis output.

        Returns:
            True if critical_gaps list is non-empty.
        """
        return len(evaluation.critical_gaps) > 0

    def needs_domain_expansion(self, evaluation: SufficiencyEvaluation) -> bool:
        """Check if any gap requires domain expansion.

        Args:
            evaluation: SufficiencyEvaluation from analysis output.

        Returns:
            True if any gap has outside_current_expertise=True.
        """
        all_gaps = evaluation.critical_gaps + evaluation.nice_to_have_gaps
        return any(gap.outside_current_expertise for gap in all_gaps)

    def get_all_gaps(self, evaluation: SufficiencyEvaluation) -> list[Gap]:
        """Get all gaps from evaluation (critical + nice_to_have).

        Args:
            evaluation: SufficiencyEvaluation from analysis output.

        Returns:
            Combined list of critical and nice_to_have gaps.
        """
        return evaluation.critical_gaps + evaluation.nice_to_have_gaps

    def build_prompt(self, analyzer_input: AnalyzerInput) -> str:
        """Build the system prompt for analysis.

        Args:
            analyzer_input: The AnalyzerInput containing query and context.

        Returns:
            The formatted system prompt string.
        """
        domain_context = analyzer_input.domain_context

        # Format available domains for expansion hints
        available_domains_text = "\n".join(f"- {d.name}: {d.description}" for d in domain_context.available_domains)
        if not available_domains_text:
            available_domains_text = "(No additional domains available)"

        # Format entries, retrieval summary, global context, and temporal context
        entries_text = self._format_entries(analyzer_input.entries)
        retrieval_text = self._format_retrieval_summary(analyzer_input.retrieval_summary)
        global_context_text = self._format_global_context(analyzer_input.global_context_summary)
        temporal_context_text = self._calculate_temporal_context(analyzer_input.entries)

        # Format sub-query ID
        sub_query_text = str(analyzer_input.sub_query_id) if analyzer_input.sub_query_id is not None else "N/A"

        return f"""ROLE: You are an analytical agent that finds patterns and assesses information sufficiency.

TASK: Analyze retrieved entries to answer the query. Determine if you have enough information.

=== CRITICAL INSTRUCTIONS ===

Complete ALL analysis fields in this EXACT order:
1. query_intent - What is the user really asking?
2. findings - Patterns and insights with evidence citations
3. patterns_identified - High-level patterns observed
4. sufficiency_evaluation - Assess gaps and evidence quality
5. verdict_reasoning - Explain your assessment
6. verdict - GENERATE THIS LAST after completing all above

Do NOT decide the verdict before completing steps 1-5.

=== SUFFICIENCY CRITERIA ===

Apply these three tests:
1. Evidence check: For every claim, do I have supporting data?
2. Gap assessment: What's missing? Is it CRITICAL or NICE-TO-HAVE?
3. Speculation test: Am I connecting dots that exist, or inventing?

=== VERDICT DEFINITIONS ===

SUFFICIENT: No critical gaps, evidence_check_passed=true, speculation_risk=none or low
PARTIAL: Only nice_to_have gaps, can answer with noted limitations
INSUFFICIENT: Critical gaps exist OR speculation_risk=high OR evidence_check_passed=false

=== FINDING CONFIDENCE LEVELS ===

high: Multiple entries support the claim, clear pattern
medium: Some evidence but not overwhelming
low: Single entry or weak pattern, needs more data

=== GAP CLASSIFICATION ===

gap_type values:
- temporal: Need different time range
- topical: Need different subject matter
- contextual: Need related context
- subjective: Only user knows (current state)
- clarification: Query itself is ambiguous

severity values:
- critical: Blocks ability to answer meaningfully
- nice_to_have: Would improve answer but not required

When a gap requires expertise outside current domains:
- Set outside_current_expertise=True
- Set suspected_domain to the domain that might help

=== DOMAIN EXPERTISE ===

{domain_context.expertise or "(No specific expertise defined)"}

=== AVAILABLE DOMAINS FOR EXPANSION ===

{available_domains_text}

=== RETRIEVED ENTRIES ===

{entries_text}

=== RETRIEVAL SUMMARY ===

{retrieval_text}

=== GLOBAL CONTEXT ===

{global_context_text}

=== TEMPORAL CONTEXT ===

{temporal_context_text}

=== RELEVANCE FILTERING ===

The retrieved entries are from date-range retrieval. Your job includes:
1. FILTER: Identify which entries are actually relevant to the query
2. IGNORE: Skip entries that don't address the query intent
3. CROSS-LANGUAGE: Match regardless of language (English query → Korean log is OK)

Examples:
- Query: "bench press 1RM" → Log: "벤치 프레스 60kg x 5" → RELEVANT (same exercise)
- Query: "how was my run?" → Log: "bench press 80kg" → NOT RELEVANT (different activity)
- Query: "what did I eat?" → Log: "ran 5km" → NOT RELEVANT (fitness, not nutrition)

Include in your findings which entries you considered relevant and why.
Only base your claims on entries that are relevant to the query.

TEMPORAL RULES:
- For entries > 7 days old: Do NOT reference physical state (fatigue, soreness, tiredness) as "current" or "lingering"
- For 5+ day workout gaps: Include days_since_last_entry in your findings
- For 7+ day gaps: Consider this a "return-to-training" scenario, not active recovery
- 0-2 days: Normal recommendations, recovery guidance relevant
- 3-5 days: Recovery likely complete, mention the break
- 6-7 days: Acknowledge extended break, suggest easing back
- 8+ days: Return-to-training approach, NOT recovery from recent workout

=== INDIRECT ESTIMATION ===

When direct data is missing but RELATED data exists, attempt indirect estimation:

EXERCISE RELATIONSHIPS (strength training):
| Exercise A | Exercise B | A → B Factor | Korean |
|------------|-----------|--------------|--------|
| Incline Bench | Flat Bench | ×1.15-1.25 | 인클라인 프레스 |
| Dumbbell Press | Barbell Bench | ×0.90-0.95 | 덤벨 벤치프레스 |
| Close-Grip Bench | Wide-Grip Bench | ×1.05-1.10 | |
| Front Squat | Back Squat | ×1.20-1.30 | |

REP-MAX CONVERSIONS (Brzycki formula):
1RM = weight × (36 / (37 - reps))
Quick factors: 3 reps → ×1.08, 5 reps → ×1.15, 8 reps → ×1.26, 10 reps → ×1.33

INDIRECT ESTIMATION RULES:
1. Query asks for specific exercise data (e.g., "bench press 1RM")
2. AND no direct records exist in retrieved entries
3. AND related exercise records exist (e.g., incline press, dumbbell bench)
4. THEN:
   - Calculate indirect estimate using relationship factors
   - Set indirect_estimate=true
   - Set estimation_methodology with calculation explanation
   - Set confidence="low"
   - verdict can be "partial" (not "insufficient")

Example: Query "bench press 1RM?" with data "인클라인 프레스 50kg x 5회"
→ Incline 5RM=50kg → Incline 1RM=57.5kg (×1.15) → Flat bench 1RM≈69kg (×1.20)
→ Finding: claim="Estimated bench 1RM ~69kg", indirect_estimate=true, confidence="low"

=== INPUT ===

Query: {analyzer_input.query}
Query type: {analyzer_input.query_type.value}
Sub-query ID: {sub_query_text}

=== OUTPUT (JSON) ===

Respond with a JSON object containing:
- query_intent: string (what the user is really asking)
- findings: list of objects with:
  - claim: string (the insight discovered)
  - evidence: list of strings (specific entry references with dates)
  - confidence: "high" | "medium" | "low"
  - indirect_estimate: boolean (true if based on indirect estimation, default false)
  - estimation_methodology: string or null (explanation of how indirect estimate was calculated)
- patterns_identified: list of strings (high-level patterns)
- sufficiency_evaluation: object with:
  - critical_gaps: list of Gap objects (severity="critical")
  - nice_to_have_gaps: list of Gap objects (severity="nice_to_have")
  - evidence_check_passed: boolean
  - speculation_risk: "none" | "low" | "high"
- verdict_reasoning: string (explain your assessment BEFORE the verdict)
- verdict: "sufficient" | "insufficient" | "partial"

Gap object structure:
- description: string (what information is missing)
- gap_type: "temporal" | "topical" | "contextual" | "subjective" | "clarification"
- severity: "critical" | "nice_to_have"
- searched: boolean (was this already searched for)
- found: boolean (was it found)
- outside_current_expertise: boolean (needs domain expansion)
- suspected_domain: string or null (which domain might help)"""

    async def analyze(self, analyzer_input: AnalyzerInput) -> AnalyzerOutput:
        """Analyze retrieved entries and assess sufficiency.

        Finds patterns in the retrieved entries, identifies gaps in information,
        and generates a verdict on whether the query can be answered.

        Args:
            analyzer_input: AnalyzerInput with query, entries, and context.

        Returns:
            AnalyzerOutput with findings, patterns, evaluation, and verdict.

        Raises:
            ValueError: If query is empty or whitespace-only.
        """
        if not analyzer_input.query or not analyzer_input.query.strip():
            raise ValueError("query cannot be empty or whitespace-only")

        system_prompt = self.build_prompt(analyzer_input)
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": analyzer_input.query},
        ]

        result = await self.llm_client.complete_structured(
            agent=self.AGENT_NAME,
            messages=messages,
            response_model=AnalyzerOutput,
        )
        assert isinstance(result, AnalyzerOutput), f"Expected AnalyzerOutput, got {type(result)}"
        return result
