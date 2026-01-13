"""Shared agent types for Quilto framework.

This module defines common data models used across all Quilto agents,
including input types, domain information, router, and parser models.
"""

from datetime import date, datetime
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class InputType(str, Enum):
    """Classification of user input type.

    Attributes:
        LOG: Declarative statements recording activities, events, or observations.
        QUERY: Questions seeking information, insights, or recommendations.
        BOTH: Input that logs something AND asks a question.
        CORRECTION: User fixing previously recorded information.
    """

    LOG = "LOG"
    QUERY = "QUERY"
    BOTH = "BOTH"
    CORRECTION = "CORRECTION"


class QueryType(str, Enum):
    """Classification of query intent.

    Attributes:
        SIMPLE: Direct retrieval ("show me X").
        INSIGHT: Why/pattern questions.
        RECOMMENDATION: What should I do.
        COMPARISON: Compare X vs Y.
        CORRECTION: Fix previous data.
    """

    SIMPLE = "simple"
    INSIGHT = "insight"
    RECOMMENDATION = "recommendation"
    COMPARISON = "comparison"
    CORRECTION = "correction"


class DependencyType(str, Enum):
    """Multi-question dependency classification.

    Attributes:
        INDEPENDENT: Can run in parallel.
        DEPENDENT: Sequential, later needs earlier.
        COUPLED: Really one question.
    """

    INDEPENDENT = "independent"
    DEPENDENT = "dependent"
    COUPLED = "coupled"


class GapType(str, Enum):
    """Classification of missing information.

    Attributes:
        TEMPORAL: Need different time range.
        TOPICAL: Need different subject matter.
        CONTEXTUAL: Need related context.
        SUBJECTIVE: Only user knows (current state).
        CLARIFICATION: Query itself is ambiguous.
    """

    TEMPORAL = "temporal"
    TOPICAL = "topical"
    CONTEXTUAL = "contextual"
    SUBJECTIVE = "subjective"
    CLARIFICATION = "clarification"


class RetrievalStrategy(str, Enum):
    """Retrieval strategy for sub-queries.

    Attributes:
        DATE_RANGE: When query mentions time periods.
        KEYWORD: When query mentions specific activities/items.
        TOPICAL: When query is about patterns/progress.
    """

    DATE_RANGE = "date_range"
    KEYWORD = "keyword"
    TOPICAL = "topical"


class DomainInfo(BaseModel):
    """Domain information for Router domain selection.

    Attributes:
        name: The unique identifier for the domain.
        description: Human-readable description of what the domain handles.
    """

    model_config = ConfigDict(strict=True)

    name: str
    description: str


class RouterInput(BaseModel):
    """Input to Router agent.

    Attributes:
        raw_input: The raw user input text to classify.
        session_context: Optional recent conversation for context.
        available_domains: List of domains available for selection.
    """

    model_config = ConfigDict(strict=True)

    raw_input: str
    session_context: str | None = None
    available_domains: list[DomainInfo]


class RouterOutput(BaseModel):
    """Output from Router agent.

    Attributes:
        input_type: The classified input type (LOG, QUERY, BOTH, CORRECTION).
        confidence: Confidence score for the classification (0.0 to 1.0).
        selected_domains: List of domain names to activate for this input.
        domain_selection_reasoning: Explanation of why domains were selected.
        log_portion: The logging portion of input (required if input_type is BOTH).
        query_portion: The query portion of input (required if input_type is BOTH).
        correction_target: What is being corrected (required if input_type is CORRECTION).
        reasoning: Brief explanation of the classification decision.
    """

    model_config = ConfigDict(strict=True)

    input_type: InputType
    confidence: float = Field(ge=0.0, le=1.0)

    selected_domains: list[str]
    domain_selection_reasoning: str

    log_portion: str | None = None
    query_portion: str | None = None

    correction_target: str | None = None

    reasoning: str

    @model_validator(mode="after")
    def validate_type_specific_fields(self) -> "RouterOutput":
        """Validate that BOTH has portions and CORRECTION has target.

        Returns:
            The validated RouterOutput instance.

        Raises:
            ValueError: If BOTH is missing portions or CORRECTION is missing target.
        """
        if self.input_type == InputType.BOTH and (not self.log_portion or not self.query_portion):
            raise ValueError("BOTH input_type requires both log_portion and query_portion")
        if self.input_type == InputType.CORRECTION and not self.correction_target:
            raise ValueError("CORRECTION input_type requires correction_target")
        return self


class ParserInput(BaseModel):
    """Input to Parser agent.

    Attributes:
        raw_input: The raw user input text to parse.
        timestamp: Timestamp when the entry was created.
        domain_schemas: Map of domain names to their Pydantic schema classes.
        vocabulary: Term normalization mapping for extraction.
        global_context: Optional global context for inference.
        recent_entries: Recent entries for correction mode target identification.
        correction_mode: Whether this is a correction to existing entry.
        correction_target: Natural language hint about what's being corrected.
    """

    model_config = ConfigDict(strict=True, arbitrary_types_allowed=True)

    raw_input: str
    timestamp: datetime

    domain_schemas: dict[str, type[BaseModel]]
    vocabulary: dict[str, str]

    global_context: str | None = None
    recent_entries: list[Any] = []

    correction_mode: bool = False
    correction_target: str | None = None


class ParserOutput(BaseModel):
    """Output from Parser agent.

    Attributes:
        date: Date of the entry.
        timestamp: Full timestamp of the entry.
        tags: Extracted tags from content.
        domain_data: Domain-specific parsed data, one entry per domain.
        raw_content: Original raw input (preserved exactly).
        confidence: Overall extraction confidence (0.0 to 1.0).
        extraction_notes: Notes about ambiguities or assumptions made.
        uncertain_fields: List of field names with uncertain extraction.
        is_correction: Whether this is a correction output.
        target_entry_id: ID of entry being corrected (if correction).
        correction_delta: Fields that changed (if correction).
    """

    model_config = ConfigDict(strict=True)

    date: date
    timestamp: datetime
    tags: list[str] = []

    domain_data: dict[str, Any]

    raw_content: str

    confidence: float = Field(ge=0.0, le=1.0)
    extraction_notes: list[str] = []
    uncertain_fields: list[str] = []

    is_correction: bool = False
    target_entry_id: str | None = None
    correction_delta: dict[str, Any] | None = None

    @model_validator(mode="after")
    def validate_required_fields(self) -> "ParserOutput":
        """Validate that raw_content is not empty.

        Returns:
            The validated ParserOutput instance.

        Raises:
            ValueError: If raw_content is empty or whitespace-only.
        """
        if not self.raw_content or not self.raw_content.strip():
            raise ValueError("raw_content cannot be empty")
        return self


# =============================================================================
# Planner Models
# =============================================================================


class Gap(BaseModel):
    """An identified gap in available information.

    Attributes:
        description: Description of the missing information.
        gap_type: Classification of the gap type.
        severity: How critical the gap is (critical or nice_to_have).
        searched: Whether this gap has been searched for.
        found: Whether the information was found.
        outside_current_expertise: Whether the gap is outside current domains.
        suspected_domain: Domain that might contain this information.
    """

    model_config = ConfigDict(strict=True)

    description: str
    gap_type: GapType
    severity: Literal["critical", "nice_to_have"]
    searched: bool = False
    found: bool = False
    outside_current_expertise: bool = False
    suspected_domain: str | None = None


class EvaluationFeedback(BaseModel):
    """Specific feedback from evaluation failure.

    Attributes:
        issue: Description of the issue found.
        suggestion: Suggested fix or improvement.
        affected_claim: The specific claim that was affected.
    """

    model_config = ConfigDict(strict=True)

    issue: str
    suggestion: str
    affected_claim: str | None = None


class SubQuery(BaseModel):
    """A decomposed sub-query.

    Attributes:
        id: Unique identifier for the sub-query.
        question: The extracted question text.
        retrieval_strategy: Strategy to use for retrieval (date_range, keyword, topical).
        retrieval_params: Strategy-specific parameters.
    """

    model_config = ConfigDict(strict=True)

    id: int
    question: str = Field(min_length=1)
    retrieval_strategy: str
    retrieval_params: dict[str, Any]


class ActiveDomainContext(BaseModel):
    """Combined context from base + selected domains.

    NOTE: This is a stub for Planner story. Full implementation
    will come with domain combination feature.

    Attributes:
        domains_loaded: List of domain names currently loaded.
        vocabulary: Term normalization mapping.
        expertise: Description of combined expertise.
        evaluation_rules: List of domain-specific evaluation rules.
        context_guidance: Guidance for context usage.
        available_domains: List of all available domains.
    """

    model_config = ConfigDict(strict=True)

    domains_loaded: list[str]
    vocabulary: dict[str, str]
    expertise: str
    evaluation_rules: list[str] = []
    context_guidance: str = ""
    available_domains: list[DomainInfo] = []


class PlannerInput(BaseModel):
    """Input to Planner agent.

    Attributes:
        query: The query to plan for.
        query_type: Optional pre-classified query type.
        domain_context: Combined domain context for planning.
        retrieval_history: History of previous retrieval attempts.
        gaps_from_analyzer: Gaps identified by Analyzer agent.
        evaluation_feedback: Feedback from evaluation failure.
        global_context_summary: Summary of global context.
    """

    model_config = ConfigDict(strict=True)

    query: str = Field(min_length=1)
    query_type: QueryType | None = None

    domain_context: ActiveDomainContext

    retrieval_history: list[dict[str, Any]] = []
    gaps_from_analyzer: list[Gap] = []
    evaluation_feedback: EvaluationFeedback | None = None

    global_context_summary: str | None = None


class PlannerOutput(BaseModel):
    """Output from Planner agent.

    Attributes:
        original_query: The original query being planned.
        query_type: Classified query type.
        sub_queries: Decomposed sub-queries.
        dependencies: Dependencies between sub-queries.
        execution_strategy: How to execute sub-queries.
        execution_order: Order of sub-query IDs for execution.
        retrieval_instructions: Instructions for Retriever agent.
        gaps_status: Status of known gaps.
        domain_expansion_request: Suggested domains to expand to.
        expansion_reasoning: Why expansion is needed.
        clarify_questions: Questions to ask user for clarification.
        next_action: What action should be taken next.
        reasoning: Explanation of planning decisions.
    """

    model_config = ConfigDict(strict=True)

    original_query: str
    query_type: QueryType

    sub_queries: list[SubQuery]
    dependencies: list[dict[str, Any]]
    execution_strategy: DependencyType
    execution_order: list[int]

    retrieval_instructions: list[dict[str, Any]]

    gaps_status: dict[str, dict[str, Any]]

    domain_expansion_request: list[str] | None = None
    expansion_reasoning: str | None = None

    clarify_questions: list[str] | None = None

    next_action: Literal["retrieve", "expand_domain", "clarify", "synthesize"]

    reasoning: str


# =============================================================================
# Retriever Models
# =============================================================================


class RetrievalAttempt(BaseModel):
    """Record of a single retrieval attempt.

    Attributes:
        attempt_number: Sequential number of this attempt (1-based).
        strategy: The strategy used ("date_range", "keyword", "topical").
        params: Strategy-specific parameters used.
        entries_found: Number of entries returned.
        summary: Brief human-readable description of the attempt.
        expanded_terms: Terms after vocabulary expansion (for keyword/topical).
    """

    model_config = ConfigDict(strict=True)

    attempt_number: int = Field(ge=1)
    strategy: str = Field(min_length=1)
    params: dict[str, Any]
    entries_found: int = Field(ge=0)
    summary: str = Field(min_length=1)
    expanded_terms: list[str] = Field(default_factory=list)


class RetrieverInput(BaseModel):
    """Input to Retriever agent.

    Attributes:
        instructions: Retrieval instructions from Planner's retrieval_instructions.
            Structure: [{"strategy": str, "params": dict, "sub_query_id": int}, ...]
        vocabulary: Term normalization mapping for vocabulary expansion.
        max_entries: Maximum entries to return (safety limit).
    """

    model_config = ConfigDict(strict=True)

    instructions: list[dict[str, Any]]
    vocabulary: dict[str, str] = Field(default_factory=dict)
    max_entries: int = Field(default=100, ge=1)


class RetrieverOutput(BaseModel):
    """Output from Retriever agent.

    Attributes:
        entries: Retrieved entries (deduplicated, up to max_entries).
        retrieval_summary: Record of each retrieval attempt.
        total_entries_found: Total entries before deduplication and truncation.
        date_range_covered: Actual date range of returned entries.
        warnings: List of warning messages (empty results, truncation, errors).
        truncated: True if results were limited by max_entries.
    """

    model_config = ConfigDict(strict=True)

    # Note: Using Any to avoid circular import (storage.repository imports agents.models)
    # At runtime, entries contains list[Entry] and date_range_covered is DateRange | None
    entries: list[Any]
    retrieval_summary: list[RetrievalAttempt]
    total_entries_found: int = Field(ge=0)
    date_range_covered: Any | None = None
    warnings: list[str] = Field(default_factory=list)
    truncated: bool = False


# =============================================================================
# Analyzer Models
# =============================================================================


class Verdict(str, Enum):
    """Sufficiency verdict from Analyzer agent.

    Attributes:
        SUFFICIENT: Enough evidence to answer confidently (no critical gaps).
        INSUFFICIENT: Critical gaps prevent meaningful answer.
        PARTIAL: Can answer with noted limitations (only nice_to_have gaps).
    """

    SUFFICIENT = "sufficient"
    INSUFFICIENT = "insufficient"
    PARTIAL = "partial"


class Finding(BaseModel):
    """A pattern or insight discovered by the Analyzer.

    Attributes:
        claim: The insight or finding text.
        evidence: References to specific entries/dates supporting the claim.
        confidence: Confidence level in this finding (high, medium, low).

    Example:
        >>> finding = Finding(
        ...     claim="Progressive overload on bench press",
        ...     evidence=["2026-01-10: bench 185x5", "2026-01-03: bench 180x5"],
        ...     confidence="high"
        ... )
    """

    model_config = ConfigDict(strict=True)

    claim: str = Field(min_length=1)
    evidence: list[str]
    confidence: Literal["high", "medium", "low"]


class SufficiencyEvaluation(BaseModel):
    """Structured assessment of information sufficiency.

    Attributes:
        critical_gaps: Gaps that block answering (severity="critical").
        nice_to_have_gaps: Gaps that would improve answer (severity="nice_to_have").
        evidence_check_passed: True if every claim has supporting data.
        speculation_risk: Level of claims beyond available data.

    Example:
        >>> evaluation = SufficiencyEvaluation(
        ...     critical_gaps=[],
        ...     nice_to_have_gaps=[Gap(
        ...         description="Historical comparison data",
        ...         gap_type=GapType.TEMPORAL,
        ...         severity="nice_to_have"
        ...     )],
        ...     evidence_check_passed=True,
        ...     speculation_risk="low"
        ... )
    """

    model_config = ConfigDict(strict=True)

    critical_gaps: list[Gap]
    nice_to_have_gaps: list[Gap]
    evidence_check_passed: bool
    speculation_risk: Literal["none", "low", "high"]


class AnalyzerInput(BaseModel):
    """Input to Analyzer agent.

    Attributes:
        query: The query being analyzed.
        query_type: Classification from Planner.
        sub_query_id: Optional sub-query ID for multi-part queries.
        entries: Retrieved entries for analysis (Any to avoid circular import).
        retrieval_summary: Record of retrieval attempts.
        domain_context: Combined domain context with expertise.
        global_context_summary: Optional user patterns from Observer.

    Example:
        >>> analyzer_input = AnalyzerInput(
        ...     query="How has my bench press progressed?",
        ...     query_type=QueryType.INSIGHT,
        ...     entries=[entry1, entry2],
        ...     retrieval_summary=[attempt],
        ...     domain_context=domain_ctx
        ... )
    """

    model_config = ConfigDict(strict=True)

    query: str = Field(min_length=1)
    query_type: QueryType
    sub_query_id: int | None = None

    # Using Any to avoid circular import with storage.repository
    entries: list[Any]
    retrieval_summary: list[RetrievalAttempt]

    domain_context: ActiveDomainContext
    global_context_summary: str | None = None


class AnalyzerOutput(BaseModel):
    """Output from Analyzer agent.

    Attributes:
        query_intent: Interpreted meaning of the query.
        findings: Patterns and insights discovered.
        patterns_identified: High-level patterns observed.
        sufficiency_evaluation: Structured gap and evidence assessment.
        verdict_reasoning: Explanation of assessment BEFORE verdict.
        verdict: Final sufficiency verdict (generated LAST by prompt instruction).

    Example:
        >>> output = AnalyzerOutput(
        ...     query_intent="User wants to know bench press progression",
        ...     findings=[finding1, finding2],
        ...     patterns_identified=["progressive overload"],
        ...     sufficiency_evaluation=evaluation,
        ...     verdict_reasoning="Found 5 entries showing clear progression...",
        ...     verdict=Verdict.SUFFICIENT
        ... )

    Note:
        The LLM prompt instructs verdict to be generated LAST to prevent
        premature commitment bias. Field order in Pydantic doesn't affect
        LLM output order - the prompt enforces this.
    """

    model_config = ConfigDict(strict=True)

    query_intent: str = Field(min_length=1)
    findings: list[Finding]
    patterns_identified: list[str]
    sufficiency_evaluation: SufficiencyEvaluation
    verdict_reasoning: str = Field(min_length=1)
    verdict: Verdict
