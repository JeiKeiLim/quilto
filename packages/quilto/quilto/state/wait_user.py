"""WAIT_USER state handler for human-in-the-loop interactions.

This module implements the WAIT_USER state using LangGraph's interrupt() mechanism
to pause execution and await user input for clarification questions.
"""

from typing import Any

from langgraph.types import interrupt

from quilto.state.session import SessionState


def enter_wait_user(
    state: SessionState,
    clarifier_output: dict[str, Any],
) -> SessionState:
    """Enter WAIT_USER state and pause for user input.

    This function stores clarification questions in state and uses LangGraph's
    interrupt() to pause execution until the user provides a response.

    Args:
        state: Current session state.
        clarifier_output: ClarifierOutput.model_dump() containing questions,
            context_explanation, and fallback_action.

    Returns:
        Updated SessionState with clarification questions stored and
        user response processed.

    Example:
        >>> state: SessionState = {
        ...     "raw_input": "How am I feeling?",
        ...     "current_state": "CLARIFY",
        ...     "waiting_for_user": False,
        ... }
        >>> clarifier_output = {
        ...     "questions": [
        ...         {"question": "What's your energy level?", "gap_addressed": "energy_level"}
        ...     ],
        ...     "context_explanation": "Need current state info",
        ...     "fallback_action": "Provide general response"
        ... }
        >>> # In real usage, interrupt() pauses here and resumes with user input
        >>> # result = enter_wait_user(state, clarifier_output)

    Note:
        When the graph is resumed with Command(resume=user_response), execution
        continues from the interrupt() call with user_input containing the
        UserClarificationResponse data.
    """
    # Store clarification context in state before interrupt
    questions = clarifier_output.get("questions", [])

    # Build interrupt payload with questions and context
    interrupt_payload = {
        "questions": questions,
        "context": clarifier_output.get("context_explanation", ""),
        "fallback": clarifier_output.get("fallback_action", ""),
    }

    # Update state with clarification info
    updated_state = dict(state)
    updated_state["clarification_questions"] = questions
    updated_state["clarifier_output"] = clarifier_output
    updated_state["waiting_for_user"] = True
    updated_state["current_state"] = "WAIT_USER"

    # Pause execution and await user response
    # When resumed with Command(resume=user_response), user_input contains the response
    user_input = interrupt(value=interrupt_payload)

    # Process the user response after resumption
    return process_user_response(
        SessionState(**updated_state),  # pyright: ignore[reportArgumentType]
        user_input,
    )


def process_user_response(
    state: SessionState,
    user_input: dict[str, Any],
) -> SessionState:
    """Process user response after WAIT_USER state resumes.

    This function is called after interrupt() returns with user input.
    It updates state based on whether user provided responses or declined.

    Args:
        state: Current session state (from before interrupt).
        user_input: User's response containing 'responses' dict and 'declined' bool.

    Returns:
        Updated SessionState with:
        - user_responses populated (if responses provided)
        - next_state set to "analyze" or "synthesize"
        - waiting_for_user cleared

    Example:
        >>> state: SessionState = {
        ...     "waiting_for_user": True,
        ...     "current_state": "WAIT_USER",
        ... }
        >>> user_input = {"responses": {"energy_level": "tired"}, "declined": False}
        >>> result = process_user_response(state, user_input)
        >>> result["next_state"]
        'analyze'
        >>> result["user_responses"]
        {'energy_level': 'tired'}

    Note:
        - If declined=True, next_state is "synthesize" (use fallback_action)
        - If declined=False with responses, next_state is "analyze"
    """
    updated_state = dict(state)

    declined = user_input.get("declined", False)
    responses = user_input.get("responses", {})

    if declined:
        # User declined - route to Synthesizer with fallback
        updated_state["user_responses"] = {}
        updated_state["next_state"] = "synthesize"
        updated_state["current_state"] = "WAIT_USER_DONE"
    else:
        # User provided responses - route back to Analyzer
        updated_state["user_responses"] = responses
        updated_state["next_state"] = "analyze"
        updated_state["current_state"] = "WAIT_USER_DONE"

    # Clear waiting flag
    updated_state["waiting_for_user"] = False

    return SessionState(**updated_state)  # pyright: ignore[reportArgumentType]
