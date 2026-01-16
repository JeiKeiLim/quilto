"""Domain expansion node for mid-flow domain loading.

This module provides the EXPAND_DOMAIN node function that handles
mid-flow domain expansion when Planner or Analyzer detects gaps
that require additional domain expertise.
"""

import logging
from typing import Any

from quilto.domain_selector import DomainSelector
from quilto.state.session import SessionState

logger = logging.getLogger(__name__)


def expand_domain_node(
    state: SessionState,
    domain_selector: DomainSelector,
) -> dict[str, Any]:
    """Expand domain context with requested domains.

    Handles domain expansion by:
    1. Reading domain_expansion_request from state
    2. Filtering out already-expanded domains (from history)
    3. Filtering out invalid domain names (log warning)
    4. Rebuilding ActiveDomainContext with merged domains
    5. Updating history and routing to next state

    Args:
        state: Current session state with domain_expansion_request.
        domain_selector: DomainSelector instance with all available domains.

    Returns:
        State updates including:
        - active_domain_context: Rebuilt context (if expansion successful)
        - domain_expansion_history: Updated history with new domains
        - domain_expansion_request: Cleared (set to None)
        - next_state: "plan" (success), "clarify" (has gaps), or "synthesize" (partial)
        - is_partial: True if no new domains could be added

    Example:
        >>> state = {
        ...     "domain_expansion_request": ["nutrition"],
        ...     "domain_expansion_history": [],
        ...     "active_domain_context": {"domains_loaded": ["strength"]},
        ... }
        >>> result = expand_domain_node(state, domain_selector)
        >>> result["next_state"]
        'plan'
        >>> "nutrition" in result["domain_expansion_history"]
        True
    """
    request: list[str] = state.get("domain_expansion_request") or []
    history: list[str] = state.get("domain_expansion_history") or []

    # Get current domains from active context (AC #7: handle None)
    active_ctx = state.get("active_domain_context")
    current_domains: list[str] = active_ctx.get("domains_loaded", []) if active_ctx else []

    # Filter: invalid domains (not in selector) - log warning (AC #6)
    invalid_domains = [d for d in request if d not in domain_selector.domains]
    for invalid in invalid_domains:
        logger.warning("Domain expansion: '%s' not in available domains, skipping", invalid)

    # Filter: new domains only (not in history, valid in selector) (AC #4)
    new_domains = [d for d in request if d not in history and d in domain_selector.domains]

    if not new_domains:
        # No expansion possible - proceed to clarify or synthesize partial (AC #4)
        logger.info(
            "Domain expansion: no new domains to add (requested=%s, history=%s)",
            request,
            history,
        )

        # Check if there are non-retrievable gaps for clarification
        gaps = state.get("gaps") or []
        has_non_retrievable_gaps = any(gap.get("gap_type") in ("subjective", "clarification") for gap in gaps)

        return {
            "next_state": "clarify" if has_non_retrievable_gaps else "synthesize",
            "domain_expansion_request": None,
            "is_partial": True,  # Signal to Synthesizer
        }

    # Build merged domain list (current + new, deduplicated)
    merged: list[str] = current_domains + [d for d in new_domains if d not in current_domains]

    logger.info("Domain expansion: adding %s (merged=%s)", new_domains, merged)

    # Rebuild context with expanded domains (AC #3)
    new_context = domain_selector.build_active_context(merged)

    return {
        "active_domain_context": new_context.model_dump(),
        "domain_expansion_history": history + new_domains,
        "domain_expansion_request": None,  # Clear request
        "next_state": "plan",  # Return to planning with new context
    }
