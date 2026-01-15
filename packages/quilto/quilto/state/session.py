"""Session state for Quilto query processing.

This module defines the SessionState TypedDict used for LangGraph state management.
All Pydantic models must be converted to dict using .model_dump() for JSON serialization.
"""

from operator import add
from typing import Annotated, Any, TypedDict


class SessionState(TypedDict, total=False):
    """Full state for a query/log processing session.

    All Pydantic model values must be stored as dicts (use .model_dump()).
    This ensures LangGraph can serialize/deserialize state correctly.

    Attributes:
        raw_input: Original user input text.
        input_type: InputType enum as string.
        query: Extracted query portion.
        query_type: QueryType enum as string.
        retrieval_history: Accumulating list of retrieval attempts.
        retrieved_entries: Accumulating list of retrieved entries.
        planner_output: PlannerOutput.model_dump() result.
            Contains next_action, retrieval_strategies, domain_expansion_request.
        analysis: AnalyzerOutput.model_dump() result.
        gaps: List of Gap.model_dump() results.
        draft_response: Current draft response from Synthesizer.
        evaluation: EvaluatorOutput.model_dump() result.
        retry_count: Current retry iteration.
        max_retries: Maximum retries allowed (default 2).
        clarification_questions: List of ClarificationQuestion.model_dump().
        clarifier_output: ClarifierOutput.model_dump() result.
        user_responses: Mapping of gap_addressed to user answer.
        waiting_for_user: True when waiting for user input.
        current_state: Current state machine position.
        next_state: Routing destination after processing.
        final_response: Final response to return to user.
        complete: True when processing is complete.
        active_domain_context: ActiveDomainContext.model_dump() result.
            Contains merged vocabulary, expertise, and rules from selected domains.
            Use active_domain_context["domains_loaded"] to get list of selected domains.
        domain_expansion_request: List of domain names requested for expansion.
            Set by Planner (next_action="expand_domain") or Analyzer (outside_current_expertise gap).
            Cleared after EXPAND_DOMAIN node processes it.
        domain_expansion_history: List of all domains added via expansion.
            Persists across retry cycles to prevent infinite loops.
            Checked before adding domains - skip any already in history.
        is_partial: True when domain expansion is exhausted.
            Signals Synthesizer to generate partial answer.
            Set when requested domains already in history or invalid.

    Example:
        >>> state: SessionState = {
        ...     "raw_input": "How's my bench press progress?",
        ...     "input_type": "QUERY",
        ...     "current_state": "ROUTE",
        ...     "waiting_for_user": False,
        ...     "complete": False,
        ... }
    """

    # Input
    raw_input: str
    input_type: str

    # Query flow
    query: str | None
    query_type: str | None

    # Retrieval (accumulating - use Annotated reducer)
    retrieval_history: Annotated[list[dict[str, Any]], add]
    retrieved_entries: Annotated[list[dict[str, Any]], add]

    # Planning (Story 6-3)
    # Serialized PlannerOutput from Planner agent.
    # Contains: next_action, retrieval_strategies, domain_expansion_request, etc.
    # Set by Planner node for downstream routing decisions.
    planner_output: dict[str, Any] | None

    # Analysis
    analysis: dict[str, Any] | None
    gaps: list[dict[str, Any]]

    # Response
    draft_response: str | None
    evaluation: dict[str, Any] | None
    retry_count: int
    max_retries: int

    # Clarification (Story 5-2 scope)
    clarification_questions: list[dict[str, Any]]
    clarifier_output: dict[str, Any] | None
    user_responses: dict[str, str]
    waiting_for_user: bool

    # Control
    current_state: str
    next_state: str | None

    # Output
    final_response: str | None
    complete: bool

    # Correction tracking (Story 5-3)
    is_correction_flow: bool
    correction_target: str | None
    correction_result: dict[str, Any] | None

    # Domain expansion (Story 6-3)
    active_domain_context: dict[str, Any] | None
    domain_expansion_request: list[str] | None
    domain_expansion_history: list[str]
    is_partial: bool
