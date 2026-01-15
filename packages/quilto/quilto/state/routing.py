"""Routing logic for state machine transitions.

This module provides routing functions that determine the next state
based on current session state. Used as conditional edges in LangGraph.
"""

from quilto.state.session import SessionState


def route_after_clarify(state: SessionState) -> str:
    """Determine next state after CLARIFY node.

    After the Clarifier agent generates questions, the flow always
    transitions to WAIT_USER to pause for user input.

    Args:
        state: Current session state (not used, but required for LangGraph edge).

    Returns:
        Always returns "wait_user" as clarification always requires user input.

    Example:
        >>> state: SessionState = {"current_state": "CLARIFY"}
        >>> route_after_clarify(state)
        'wait_user'

    Note:
        This is a simple routing function since CLARIFY always leads to WAIT_USER.
        The state parameter is required by LangGraph conditional edge API.
    """
    return "wait_user"


def route_after_wait_user(state: SessionState) -> str:
    """Determine next state after WAIT_USER resumes.

    After user provides input (or declines), routes to either:
    - "analyze": User provided responses, re-analyze with new information
    - "synthesize": User declined, proceed with fallback action

    Args:
        state: Current session state with user_responses and next_state set.

    Returns:
        "analyze" if user provided responses, "synthesize" if user declined.

    Example:
        >>> state: SessionState = {
        ...     "current_state": "WAIT_USER",
        ...     "user_responses": {"energy_level": "tired"},
        ...     "next_state": "analyze"
        ... }
        >>> route_after_wait_user(state)
        'analyze'

        >>> declined_state: SessionState = {
        ...     "current_state": "WAIT_USER",
        ...     "user_responses": {},
        ...     "next_state": "synthesize"
        ... }
        >>> route_after_wait_user(declined_state)
        'synthesize'

    Note:
        The next_state is set by process_user_response() in wait_user.py.
        This function reads that decision for LangGraph conditional edge.
    """
    next_state = state.get("next_state")

    # Default to synthesize if next_state not set (defensive)
    if next_state is None:
        return "synthesize"

    return next_state


def route_after_planner(state: SessionState) -> str:
    """Determine next state after PLAN node.

    Routes based on Planner's next_action field:
    - "expand_domain": Planner detected domain gap, request expansion
    - "retrieve": Normal flow, proceed to retrieval
    - "clarify": Planner requests clarification
    - "synthesize": Planner has enough to synthesize

    Args:
        state: Current session state with planner_output.

    Returns:
        Route string: "expand_domain", "retrieve", "clarify", or "synthesize".

    Example:
        >>> state: SessionState = {
        ...     "planner_output": {
        ...         "next_action": "expand_domain",
        ...         "domain_expansion_request": ["nutrition"],
        ...     }
        ... }
        >>> route_after_planner(state)
        'expand_domain'

    Note:
        The domain_expansion_request must be set by the Planner node (not this
        routing function) because LangGraph routing functions should not mutate state.
    """
    planner_output = state.get("planner_output")
    if not planner_output:
        return "retrieve"  # Default

    next_action = planner_output.get("next_action", "retrieve")

    # Map next_action to route strings (lowercase for LangGraph convention)
    return {
        "expand_domain": "expand_domain",
        "retrieve": "retrieve",
        "clarify": "clarify",
        "synthesize": "synthesize",
    }.get(next_action, "retrieve")


def route_after_analyzer(state: SessionState) -> str:
    """Determine next state after ANALYZE node.

    Priority:
    1. outside_current_expertise gaps (not yet expanded) → expand_domain
    2. verdict == sufficient → synthesize
    3. verdict == insufficient/partial → plan (re-plan with gaps)

    Args:
        state: Current session state with analysis and gaps.

    Returns:
        Route string: "expand_domain", "synthesize", or "plan".

    Example:
        >>> state: SessionState = {
        ...     "analysis": {"verdict": "insufficient"},
        ...     "gaps": [
        ...         {
        ...             "outside_current_expertise": True,
        ...             "suspected_domain": "nutrition",
        ...         }
        ...     ],
        ...     "domain_expansion_history": [],
        ... }
        >>> route_after_analyzer(state)
        'expand_domain'

    Note:
        The domain_expansion_request must be set by the Analyzer node (not this
        routing function) when outside_current_expertise gaps are detected.
    """
    analysis = state.get("analysis")
    if not analysis:
        return "synthesize"  # Defensive default

    gaps = state.get("gaps") or []
    history = state.get("domain_expansion_history") or []

    # Check for outside_current_expertise gaps not yet expanded
    domains_to_expand = [
        gap.get("suspected_domain")
        for gap in gaps
        if gap.get("outside_current_expertise") and gap.get("suspected_domain")
    ]
    new_domains_to_expand = [d for d in domains_to_expand if d not in history]

    if new_domains_to_expand:
        return "expand_domain"

    verdict = analysis.get("verdict", "sufficient")
    if verdict == "sufficient":
        return "synthesize"

    # insufficient or partial → re-plan
    return "plan"


def route_after_expand_domain(state: SessionState) -> str:
    """Determine next state after EXPAND_DOMAIN node.

    Routes based on next_state set by expand_domain_node:
    - "plan": Successful expansion, continue planning with new context
    - "clarify": No new domains, has non-retrievable gaps
    - "synthesize": No new domains, synthesize partial answer

    Args:
        state: Current session state with next_state set by expand_domain_node.

    Returns:
        Route string: "plan", "clarify", or "synthesize".

    Example:
        >>> state: SessionState = {"next_state": "plan"}
        >>> route_after_expand_domain(state)
        'plan'
    """
    next_state = state.get("next_state")
    if next_state in ("plan", "clarify", "synthesize"):
        return next_state
    return "plan"  # Default to plan
