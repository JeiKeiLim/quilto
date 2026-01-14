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
