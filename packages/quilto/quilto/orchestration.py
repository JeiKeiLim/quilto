"""LangGraph orchestration for Quilto agent pipeline.

This module provides the StateGraph definition for orchestrating
Quilto agents through the processing flows:
- QUERY: Route → Plan → Retrieve → Analyze → Synthesize → Evaluate → Observe
- LOG: Route → Parse → Observe
- BOTH: Query flow first, then Parse → Observe
- CORRECTION: Route → Correction → Observe
"""

import inspect
import logging
import time
import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any, Final, Literal, TypedDict

from langgraph.graph import END, StateGraph

from quilto.agents import (
    AnalyzerAgent,
    AnalyzerInput,
    AnalyzerOutput,
    EvaluationFeedback,
    EvaluatorAgent,
    EvaluatorInput,
    EvaluatorOutput,
    Finding,
    InputType,
    ObserverAgent,
    ParserAgent,
    ParserInput,
    PlannerAgent,
    PlannerInput,
    QueryType,
    RetrieverAgent,
    RetrieverInput,
    RouterAgent,
    RouterInput,
    SynthesizerAgent,
    SynthesizerInput,
    Verdict,
)
from quilto.flow import CorrectionResult, process_correction
from quilto.state.observer_triggers import (
    get_combined_context_guidance,
    serialize_global_context,
)
from quilto.storage import GlobalContextManager
from quilto.storage.models import Entry

if TYPE_CHECKING:
    from quilto.agents.models import ActiveDomainContext
    from quilto.observability.provider import ObservabilityProvider
    from quilto.quilto import Quilto

logger = logging.getLogger(__name__)


class StateKeys:
    """Constants for QuiltoState dictionary keys.

    Using constants instead of string literals enables:
    - Compile-time typo detection via pyright
    - IDE autocomplete and navigation
    - Single source of truth for key names
    """

    # Internal
    QUILTO: Final[str] = "_quilto"
    TRACES: Final[str] = "traces"
    OBSERVABILITY: Final[str] = "_observability_provider"

    # Input
    USER_INPUT: Final[str] = "user_input"
    MODE: Final[str] = "mode"
    CONVERSATION_CONTEXT: Final[str] = "conversation_context"

    # Router output
    INPUT_TYPE: Final[str] = "input_type"
    SELECTED_DOMAINS: Final[str] = "selected_domains"
    ROUTER_OUTPUT: Final[str] = "router_output"

    # Planner output
    QUERY_TYPE: Final[str] = "query_type"
    RETRIEVAL_INSTRUCTIONS: Final[str] = "retrieval_instructions"
    NEXT_ACTION: Final[str] = "next_action"
    CLARIFY_QUESTIONS: Final[str] = "clarify_questions"
    PLANNER_OUTPUT: Final[str] = "planner_output"

    # Retriever output
    ENTRIES: Final[str] = "entries"
    RETRIEVAL_SUMMARY: Final[str] = "retrieval_summary"
    SOURCE_ENTRY_IDS: Final[str] = "source_entry_ids"
    RETRIEVER_OUTPUT: Final[str] = "retriever_output"

    # Analyzer output
    ANALYSIS_VERDICT: Final[str] = "analysis_verdict"
    ANALYSIS_FINDINGS: Final[str] = "analysis_findings"
    ANALYZER_OUTPUT: Final[str] = "analyzer_output"

    # Synthesizer output
    RESPONSE: Final[str] = "response"
    SYNTHESIZER_OUTPUT: Final[str] = "synthesizer_output"

    # Evaluator output
    EVAL_VERDICT: Final[str] = "eval_verdict"
    EVAL_FEEDBACK: Final[str] = "eval_feedback"
    EVALUATOR_OUTPUT: Final[str] = "evaluator_output"

    # Parser output
    PARSED_DATA: Final[str] = "parsed_data"
    PARSER_OUTPUT: Final[str] = "parser_output"

    # Correction output
    CORRECTION_RESULT: Final[str] = "correction_result"

    # Observer output
    OBSERVER_OUTPUT: Final[str] = "observer_output"
    OBSERVER_ERROR: Final[str] = "observer_error"

    # Analyzer error
    ANALYZER_ERROR: Final[str] = "analyzer_error"

    # Control
    RETRY_COUNT: Final[str] = "retry_count"
    MAX_RETRIES: Final[str] = "max_retries"
    IS_PARTIAL: Final[str] = "is_partial"
    ERROR: Final[str] = "error"

    # Context objects
    DOMAIN_CONTEXT: Final[str] = "domain_context"
    STORAGE_SUMMARY: Final[str] = "storage_summary"

    # Metrics
    CONFIDENCE: Final[str] = "confidence"
    TOTAL_ELAPSED_MS: Final[str] = "total_elapsed_ms"


# Confidence score constants
_CONFIDENCE_SUFFICIENT = 0.8
_CONFIDENCE_PARTIAL = 0.6
_CONFIDENCE_INSUFFICIENT = 0.4
_CONFIDENCE_ADJUSTMENT = 0.1


def _get_domain_context_with_fallback(state: "QuiltoState", caller: str) -> tuple["ActiveDomainContext", bool]:
    """Get domain context from state with validation fallback.

    Args:
        state: Current orchestration state.
        caller: Name of the calling function for logging.

    Returns:
        Tuple of (domain_context, was_fallback). If was_fallback is True,
        the context is a minimal valid fallback due to validation failure.
    """
    from pydantic import ValidationError

    from quilto.agents.models import ActiveDomainContext

    domain_context_dict = state.get(StateKeys.DOMAIN_CONTEXT, {})

    try:
        return (ActiveDomainContext.model_validate(domain_context_dict), False)
    except ValidationError as e:
        logger.warning(
            "%s: domain_context validation failed, using fallback. Error: %s",
            caller,
            e.errors(),
        )
        return (
            ActiveDomainContext(
                domains_loaded=[],
                vocabulary={},
                expertise="General assistant",
            ),
            True,
        )


class QuiltoState(TypedDict, total=False):
    """State for the Quilto orchestration graph.

    This TypedDict defines all fields that flow through the graph nodes.
    total=False makes all fields optional.
    """

    # Input
    user_input: str
    mode: str  # "auto", "log", "query"
    conversation_context: str | None

    # Router output
    input_type: str  # "log", "query", "both", "correction"
    selected_domains: list[str]
    router_output: dict[str, Any]

    # Planner output
    query_type: str
    retrieval_instructions: list[dict[str, Any]]
    next_action: str  # "retrieve", "clarify"
    clarify_questions: list[dict[str, Any]] | None
    planner_output: dict[str, Any]

    # Retriever output
    entries: list[dict[str, Any]]
    retrieval_summary: list[dict[str, Any]]
    source_entry_ids: list[str]
    retriever_output: dict[str, Any]

    # Analyzer output
    analysis_verdict: str
    analysis_findings: list[dict[str, Any]]
    analyzer_output: dict[str, Any]

    # Synthesizer output
    response: str
    synthesizer_output: dict[str, Any]

    # Evaluator output
    eval_verdict: str
    eval_feedback: list[str]
    evaluator_output: dict[str, Any]

    # Parser output (for LOG/BOTH)
    parsed_data: dict[str, Any] | None
    parser_output: dict[str, Any]

    # Correction output (for CORRECTION)
    correction_result: dict[str, Any] | None

    # Observer output
    observer_output: dict[str, Any]
    observer_error: str  # Error message if Observer failed

    # Analyzer error
    analyzer_error: str  # Error message if Analyzer failed

    # Control
    retry_count: int
    max_retries: int
    is_partial: bool
    error: str | None

    # Context objects (for agent calls)
    domain_context: dict[str, Any]
    storage_summary: dict[str, Any]

    # Progress callback
    _quilto: Any  # Reference to Quilto instance

    # Observability
    _observability_provider: Any  # ObservabilityProvider instance

    # Confidence
    confidence: float | None

    # Debug traces
    traces: list[dict[str, Any]]
    total_elapsed_ms: float


# Type alias for the compiled graph
OrchestrationGraph = Any  # CompiledStateGraph[QuiltoState]


def _calculate_confidence(analysis: AnalyzerOutput, evaluation: EvaluatorOutput) -> float:
    """Calculate overall confidence score.

    Args:
        analysis: Analyzer output with verdict.
        evaluation: Evaluator output with verdict.

    Returns:
        Confidence score between 0.0 and 1.0.
    """
    if analysis.verdict == Verdict.SUFFICIENT:
        base = _CONFIDENCE_SUFFICIENT
    elif analysis.verdict == Verdict.PARTIAL:
        base = _CONFIDENCE_PARTIAL
    else:
        base = _CONFIDENCE_INSUFFICIENT

    adjustment = _CONFIDENCE_ADJUSTMENT if evaluation.overall_verdict == Verdict.SUFFICIENT else -_CONFIDENCE_ADJUSTMENT
    return min(1.0, max(0.0, base + adjustment))


# Cache for handler method signatures (handler_id, method_name) -> param_count
_HANDLER_SIGNATURE_CACHE: dict[tuple[int, str], int] = {}


def _get_method_param_count(handler: Any, method_name: str) -> int:
    """Get parameter count for handler method (cached).

    Args:
        handler: Progress handler instance.
        method_name: Method name to check.

    Returns:
        Number of parameters (excluding self).
    """
    cache_key = (id(handler), method_name)
    if cache_key in _HANDLER_SIGNATURE_CACHE:
        return _HANDLER_SIGNATURE_CACHE[cache_key]

    method_fn = getattr(handler, method_name, None)
    if method_fn is None:
        _HANDLER_SIGNATURE_CACHE[cache_key] = 0
        return 0

    sig = inspect.signature(method_fn)
    # Parameters does not include 'self' for bound methods
    param_count = len(sig.parameters)
    _HANDLER_SIGNATURE_CACHE[cache_key] = param_count
    return param_count


async def _call_progress_handler(
    quilto: "Quilto",
    method: str,
    *args: Any,
) -> None:
    """Call progress handler method if available.

    Supports backward compatibility for on_agent_complete - handlers
    without the output parameter receive only (agent, elapsed).

    Args:
        quilto: Quilto instance with optional progress_handler.
        method: Method name to call.
        *args: Arguments to pass to method.
    """
    handler = quilto.progress_handler
    if handler is None:
        return

    method_fn = getattr(handler, method, None)
    if method_fn is None:
        return

    if method == "on_agent_complete":
        param_count = _get_method_param_count(handler, method)
        if param_count >= 3:  # agent, elapsed, output
            await method_fn(*args)
        else:
            # Old handler: only agent, elapsed (backward compatibility)
            await method_fn(args[0], args[1])
    else:
        await method_fn(*args)


def _add_trace(
    state: QuiltoState,
    agent_name: str,
    input_summary: str,
    output_summary: str,
    elapsed_ms: float,
) -> list[dict[str, Any]]:
    """Add a trace entry to state.

    Args:
        state: Current state.
        agent_name: Name of agent.
        input_summary: Summary of input.
        output_summary: Summary of output.
        elapsed_ms: Execution time in milliseconds.

    Returns:
        Updated traces list.
    """
    traces = list(state.get(StateKeys.TRACES, []))
    traces.append(
        {
            "agent_name": agent_name,
            "input_summary": input_summary,
            "output_summary": output_summary,
            "elapsed_ms": elapsed_ms,
            "timestamp": datetime.now(UTC),
        }
    )
    return traces


def _get_quilto(state: QuiltoState, node_name: str) -> "Quilto | None":
    """Get Quilto instance from state with error logging.

    Args:
        state: Current orchestration state.
        node_name: Name of the calling node for error messages.

    Returns:
        Quilto instance or None if missing.
    """
    quilto = state.get(StateKeys.QUILTO)
    if quilto is None:
        logger.error("%s: Missing _quilto in state - graph not initialized", node_name)
    return quilto


def _get_observability_provider(state: QuiltoState) -> "ObservabilityProvider":
    """Get observability provider from state, falling back to NoOp.

    Args:
        state: Current orchestration state.

    Returns:
        ObservabilityProvider instance (NoOpProvider if not configured).
    """
    from quilto.observability.noop import NoOpProvider
    from quilto.observability.provider import ObservabilityProvider

    # Check if provider is directly in state (set by QuiltoGraph wrapper)
    provider = state.get(StateKeys.OBSERVABILITY)
    if provider is not None and isinstance(provider, ObservabilityProvider):
        return provider

    # Fall back to getting it from Quilto instance (for Story 24.5)
    quilto = state.get(StateKeys.QUILTO)
    if quilto is not None:
        provider = getattr(quilto, "observability_provider", None)
        if provider is not None and isinstance(provider, ObservabilityProvider):
            return provider

    return NoOpProvider()


# =============================================================================
# Node Functions
# =============================================================================


async def route_node(state: QuiltoState) -> dict[str, Any]:
    """Route node - classifies input and selects domains.

    Args:
        state: Current orchestration state.

    Returns:
        Updated state with router output.
    """
    quilto = _get_quilto(state, "route_node")
    if quilto is None:
        return {StateKeys.ERROR: "Internal error: orchestration not initialized"}

    user_input: str = state.get(StateKeys.USER_INPUT, "")
    mode = state.get(StateKeys.MODE, "auto")

    await _call_progress_handler(quilto, "on_stage", "routing")

    # If mode is forced, skip Router
    if mode == "log":
        return {
            StateKeys.INPUT_TYPE: "log",
            StateKeys.SELECTED_DOMAINS: [d.name for d in quilto.domains],
            StateKeys.ROUTER_OUTPUT: {"forced_mode": "log"},
        }
    elif mode == "query":
        # Still need to select domains via Router
        pass

    # Run Router
    start = time.perf_counter()
    await _call_progress_handler(quilto, "on_agent_start", "router", user_input[:50])

    try:
        router = RouterAgent(quilto.llm_client)
        domain_infos = quilto.domain_selector.get_domain_infos()
        session_context = state.get(StateKeys.CONVERSATION_CONTEXT)
        router_input = RouterInput(
            raw_input=user_input,
            available_domains=domain_infos,
            session_context=session_context,
        )
        router_output = await router.classify(router_input)

        elapsed = (time.perf_counter() - start) * 1000
        await _call_progress_handler(
            quilto, "on_agent_complete", "router", elapsed / 1000, router_output.model_dump(mode="json")
        )

        # Map InputType to string
        input_type_map = {
            InputType.LOG: "log",
            InputType.QUERY: "query",
            InputType.BOTH: "both",
            InputType.CORRECTION: "correction",
        }
        input_type = input_type_map.get(router_output.input_type, "query")

        # If mode forces query, override
        if mode == "query":
            input_type = "query"

        # Build domain context
        domain_context = quilto.domain_selector.build_active_context(router_output.selected_domains)

        return {
            StateKeys.INPUT_TYPE: input_type,
            StateKeys.SELECTED_DOMAINS: router_output.selected_domains,
            StateKeys.ROUTER_OUTPUT: router_output.model_dump(),
            StateKeys.DOMAIN_CONTEXT: domain_context.model_dump(),
            StateKeys.TRACES: _add_trace(state, "router", user_input[:50], f"type={input_type}", elapsed),
        }
    except Exception as e:
        elapsed = (time.perf_counter() - start) * 1000
        await _call_progress_handler(quilto, "on_agent_complete", "router", elapsed / 1000, {})
        return {
            StateKeys.ERROR: f"Router failed: {e!s}",
            StateKeys.INPUT_TYPE: "query",  # Default to query on error
            StateKeys.SELECTED_DOMAINS: [],
        }


async def plan_node(state: QuiltoState) -> dict[str, Any]:
    """Plan node - creates retrieval plan.

    Args:
        state: Current orchestration state.

    Returns:
        Updated state with planner output.
    """
    quilto = _get_quilto(state, "plan_node")
    if quilto is None:
        return {StateKeys.ERROR: "Internal error: orchestration not initialized"}

    user_input: str = state.get(StateKeys.USER_INPUT, "")
    conversation_context = state.get(StateKeys.CONVERSATION_CONTEXT)

    await _call_progress_handler(quilto, "on_stage", "planning")

    start = time.perf_counter()
    await _call_progress_handler(quilto, "on_agent_start", "planner", "query analysis")

    try:
        # Get storage summary (required by Planner)
        storage_summary: dict[str, Any] = quilto.get_storage_summary()

        # Reconstruct domain context with defensive validation
        domain_context, _was_fallback = _get_domain_context_with_fallback(state, "plan_node")

        # Get evaluation feedback from previous retry if any
        evaluation_feedback: EvaluationFeedback | None = None
        if state.get(StateKeys.RETRY_COUNT, 0) > 0:
            eval_feedback = state.get(StateKeys.EVAL_FEEDBACK)
            if isinstance(eval_feedback, list) and eval_feedback:
                first_feedback = eval_feedback[0]
                if isinstance(first_feedback, EvaluationFeedback):
                    evaluation_feedback = first_feedback

        # Get retrieval history from previous retry if any
        retrieval_history: list[dict[str, Any]] = []
        if state.get(StateKeys.RETRY_COUNT, 0) > 0:
            raw_history = state.get(StateKeys.RETRIEVAL_SUMMARY)
            if isinstance(raw_history, list):
                retrieval_history = raw_history

        planner = PlannerAgent(quilto.llm_client)
        planner_input = PlannerInput(
            query=user_input,
            domain_context=domain_context,
            storage_summary=storage_summary,
            conversation_context=conversation_context,
            evaluation_feedback=evaluation_feedback,
            retrieval_history=retrieval_history,
        )
        planner_output = await planner.plan(planner_input)

        elapsed = (time.perf_counter() - start) * 1000
        await _call_progress_handler(
            quilto, "on_agent_complete", "planner", elapsed / 1000, planner_output.model_dump(mode="json")
        )

        # Get query type value - QueryType is an enum, extract string value
        query_type_str = planner_output.query_type.value

        # Get clarify questions if present (list[str] | None)
        clarify_q = planner_output.clarify_questions

        # Retrieval instructions are already list[dict[str, Any]]
        retrieval_instr = planner_output.retrieval_instructions

        return {
            StateKeys.QUERY_TYPE: query_type_str,
            StateKeys.RETRIEVAL_INSTRUCTIONS: retrieval_instr,
            StateKeys.NEXT_ACTION: planner_output.next_action,
            StateKeys.CLARIFY_QUESTIONS: clarify_q,
            StateKeys.PLANNER_OUTPUT: planner_output.model_dump(),
            StateKeys.STORAGE_SUMMARY: storage_summary,
            StateKeys.TRACES: _add_trace(
                state, "planner", "query analysis", f"action={planner_output.next_action}", elapsed
            ),
        }
    except Exception as e:
        elapsed = (time.perf_counter() - start) * 1000
        await _call_progress_handler(quilto, "on_agent_complete", "planner", elapsed / 1000, {})
        return {
            StateKeys.ERROR: f"Planner failed: {e!s}",
            StateKeys.NEXT_ACTION: "clarify",
        }


async def retrieve_node(state: QuiltoState) -> dict[str, Any]:
    """Retrieve node - fetches entries from storage.

    Args:
        state: Current orchestration state.

    Returns:
        Updated state with retriever output.
    """
    quilto = _get_quilto(state, "retrieve_node")
    if quilto is None:
        return {StateKeys.ERROR: "Internal error: orchestration not initialized"}

    await _call_progress_handler(quilto, "on_stage", "retrieving")

    start = time.perf_counter()
    instructions = state.get(StateKeys.RETRIEVAL_INSTRUCTIONS, [])
    await _call_progress_handler(quilto, "on_agent_start", "retriever", f"{len(instructions)} instructions")

    # Get observability provider for tool instrumentation
    provider = _get_observability_provider(state)

    try:
        # Instructions are already dict-based (from PlannerOutput.retrieval_instructions)
        retriever = RetrieverAgent(quilto.storage)
        retriever_input = RetrieverInput(
            instructions=instructions,
            max_entries=100,
        )

        # Wrap storage retrieval in observability span
        # Note: entries_found logged after operation completes via log_event
        selected_domains = state.get(StateKeys.SELECTED_DOMAINS, [])
        with provider.span(
            "storage.retrieve",
            metadata={
                "instructions_count": len(instructions),
                "max_entries": 100,
                "domains": selected_domains,
            },
        ):
            retriever_output = await retriever.retrieve(retriever_input)
            # Log result metadata (entries_found is only known after retrieval)
            provider.log_event(
                "retrieval_complete",
                metadata={
                    "entries_found": len(retriever_output.entries),
                    "retrieval_attempts": len(retriever_output.retrieval_summary),
                },
            )

        elapsed = (time.perf_counter() - start) * 1000
        await _call_progress_handler(
            quilto, "on_agent_complete", "retriever", elapsed / 1000, retriever_output.model_dump(mode="json")
        )

        return {
            StateKeys.ENTRIES: [e.model_dump() for e in retriever_output.entries],
            StateKeys.RETRIEVAL_SUMMARY: [s.model_dump() for s in retriever_output.retrieval_summary],
            StateKeys.SOURCE_ENTRY_IDS: [e.id for e in retriever_output.entries],
            StateKeys.RETRIEVER_OUTPUT: retriever_output.model_dump(),
            StateKeys.TRACES: _add_trace(
                state,
                "retriever",
                f"{len(instructions)} instructions",
                f"{len(retriever_output.entries)} entries",
                elapsed,
            ),
        }
    except Exception as e:
        elapsed = (time.perf_counter() - start) * 1000
        await _call_progress_handler(quilto, "on_agent_complete", "retriever", elapsed / 1000, {})
        return {
            StateKeys.ERROR: f"Retriever failed: {e!s}",
            StateKeys.ENTRIES: [],
            StateKeys.SOURCE_ENTRY_IDS: [],
        }


async def analyze_node(state: QuiltoState) -> dict[str, Any]:
    """Analyze node - analyzes retrieved entries.

    Args:
        state: Current orchestration state.

    Returns:
        Updated state with analyzer output.
    """
    quilto = _get_quilto(state, "analyze_node")
    if quilto is None:
        return {StateKeys.ERROR: "Internal error: orchestration not initialized"}

    user_input: str = state.get(StateKeys.USER_INPUT, "")

    await _call_progress_handler(quilto, "on_stage", "analyzing")

    start = time.perf_counter()
    entries = state.get(StateKeys.ENTRIES, [])
    await _call_progress_handler(quilto, "on_agent_start", "analyzer", f"{len(entries)} entries")

    try:
        # Reconstruct domain context with defensive validation
        domain_context, _was_fallback = _get_domain_context_with_fallback(state, "analyze_node")

        query_type_str = state.get(StateKeys.QUERY_TYPE, "factual")
        query_type = QueryType(query_type_str) if isinstance(query_type_str, str) else query_type_str
        retrieval_summary_raw = state.get(StateKeys.RETRIEVAL_SUMMARY, [])
        retrieval_summary = retrieval_summary_raw if isinstance(retrieval_summary_raw, list) else []
        conversation_context = state.get(StateKeys.CONVERSATION_CONTEXT)

        analyzer = AnalyzerAgent(quilto.llm_client)
        analyzer_input = AnalyzerInput(
            query=user_input,
            query_type=query_type,
            entries=entries,
            retrieval_summary=retrieval_summary,
            domain_context=domain_context,
            conversation_context=conversation_context,
        )
        analyzer_output = await analyzer.analyze(analyzer_input)

        elapsed = (time.perf_counter() - start) * 1000
        await _call_progress_handler(
            quilto, "on_agent_complete", "analyzer", elapsed / 1000, analyzer_output.model_dump(mode="json")
        )

        # Warn if entries exist but analyzer returned empty findings
        if entries and not analyzer_output.findings:
            logger.warning(
                "analyze_node: %d entries provided but analyzer returned empty findings for query: %s",
                len(entries),
                user_input[:50],
            )

        return {
            StateKeys.ANALYSIS_VERDICT: analyzer_output.verdict.value,
            StateKeys.ANALYSIS_FINDINGS: [f.model_dump() for f in analyzer_output.findings],
            StateKeys.ANALYZER_OUTPUT: analyzer_output.model_dump(),
            StateKeys.TRACES: _add_trace(
                state, "analyzer", f"{len(entries)} entries", f"verdict={analyzer_output.verdict.value}", elapsed
            ),
        }
    except Exception as e:
        elapsed = (time.perf_counter() - start) * 1000
        logger.exception("analyze_node failed for query: %s", user_input[:50])
        error_info = {"error": str(e), "error_type": type(e).__name__}
        await _call_progress_handler(quilto, "on_agent_complete", "analyzer", elapsed / 1000, error_info)

        fallback_output = {
            "query_intent": "Unable to analyze due to error",
            "findings": [],
            "patterns_identified": [],
            "sufficiency_evaluation": {
                "critical_gaps": [],
                "nice_to_have_gaps": [],
                "evidence_check_passed": False,
                "speculation_risk": "high",
            },
            "verdict_reasoning": f"Analysis failed with error: {e!s}",
            "verdict": "insufficient",
        }

        return {
            StateKeys.ERROR: f"Analyzer failed: {e!s}",
            StateKeys.ANALYZER_ERROR: str(e),
            StateKeys.ANALYSIS_VERDICT: "insufficient",
            StateKeys.ANALYSIS_FINDINGS: [],
            StateKeys.ANALYZER_OUTPUT: fallback_output,
            StateKeys.TRACES: _add_trace(state, "analyzer", f"{len(entries)} entries", f"ERROR: {e!s}", elapsed),
        }


async def synthesize_node(state: QuiltoState) -> dict[str, Any]:
    """Synthesize node - generates response.

    Args:
        state: Current orchestration state.

    Returns:
        Updated state with synthesizer output.
    """
    quilto = _get_quilto(state, "synthesize_node")
    if quilto is None:
        return {StateKeys.ERROR: "Internal error: orchestration not initialized"}

    user_input: str = state.get(StateKeys.USER_INPUT, "")

    await _call_progress_handler(quilto, "on_stage", "synthesizing")

    start = time.perf_counter()
    verdict = state.get(StateKeys.ANALYSIS_VERDICT, "insufficient")
    await _call_progress_handler(quilto, "on_agent_start", "synthesizer", f"verdict={verdict}")

    try:
        from quilto.agents.models import SufficiencyEvaluation

        # Reconstruct domain context with defensive validation
        domain_context, _was_fallback = _get_domain_context_with_fallback(state, "synthesize_node")

        # Reconstruct AnalyzerOutput with defensive validation
        analyzer_output_dict = state.get(StateKeys.ANALYZER_OUTPUT, {})
        try:
            analyzer_output = AnalyzerOutput.model_validate(analyzer_output_dict)
        except Exception as validation_err:
            logger.warning("Invalid analyzer_output, using minimal fallback: %s", validation_err)
            # Create minimal valid AnalyzerOutput for synthesizer
            analyzer_output = AnalyzerOutput(
                query_intent="Analysis unavailable",
                findings=[],
                patterns_identified=[],
                sufficiency_evaluation=SufficiencyEvaluation(
                    critical_gaps=[],
                    nice_to_have_gaps=[],
                    evidence_check_passed=False,
                    speculation_risk="high",
                ),
                verdict_reasoning="Analyzer output invalid or missing",
                verdict=Verdict.INSUFFICIENT,
            )

        # Fallback: If analyzer has empty findings but entries exist, create synthetic findings
        entries = state.get(StateKeys.ENTRIES, [])
        if not analyzer_output.findings and entries:
            logger.warning(
                "synthesize_node: Creating fallback findings from %d entries (analyzer returned empty)",
                len(entries),
            )
            fallback_findings = [
                Finding(
                    claim=f"Entry from {e.get('date', 'unknown')}: {str(e.get('raw_content', ''))[:100]}",
                    evidence=[str(e.get("id", ""))],
                    confidence="low",
                    indirect_estimate=False,
                )
                for e in entries[:10]  # Limit to avoid token overflow
            ]
            analyzer_output = AnalyzerOutput(
                query_intent=analyzer_output.query_intent or "Analysis unavailable - using raw entries",
                findings=fallback_findings,
                patterns_identified=[],
                sufficiency_evaluation=SufficiencyEvaluation(
                    critical_gaps=[],
                    nice_to_have_gaps=[],
                    evidence_check_passed=False,
                    speculation_risk="high",
                ),
                verdict_reasoning="FALLBACK: Analyzer failed or returned empty. Synthesizing from raw entries.",
                verdict=Verdict.PARTIAL,
            )

        query_type_str = state.get(StateKeys.QUERY_TYPE, "factual")
        query_type = QueryType(query_type_str) if isinstance(query_type_str, str) else query_type_str
        is_partial = state.get(StateKeys.IS_PARTIAL, False)
        conversation_context = state.get(StateKeys.CONVERSATION_CONTEXT)

        synthesizer = SynthesizerAgent(quilto.llm_client)
        synthesizer_input = SynthesizerInput(
            query=user_input,
            query_type=query_type,
            analysis=analyzer_output,
            vocabulary=domain_context.vocabulary,
            response_style="concise",
            is_partial=is_partial,
            conversation_context=conversation_context,
        )
        synthesizer_output = await synthesizer.synthesize(synthesizer_input)

        elapsed = (time.perf_counter() - start) * 1000
        await _call_progress_handler(
            quilto, "on_agent_complete", "synthesizer", elapsed / 1000, synthesizer_output.model_dump(mode="json")
        )

        return {
            StateKeys.RESPONSE: synthesizer_output.response,
            StateKeys.SYNTHESIZER_OUTPUT: synthesizer_output.model_dump(),
            StateKeys.TRACES: _add_trace(
                state, "synthesizer", f"verdict={verdict}", f"response_len={len(synthesizer_output.response)}", elapsed
            ),
        }
    except Exception as e:
        elapsed = (time.perf_counter() - start) * 1000
        logger.exception("synthesize_node failed for query: %s", user_input[:50])
        await _call_progress_handler(quilto, "on_agent_complete", "synthesizer", elapsed / 1000, {})
        # Sanitize error message (first line only)
        error_msg = str(e).split("\n")[0]
        return {
            StateKeys.ERROR: f"Synthesizer failed: {e!s}",
            StateKeys.RESPONSE: f"I encountered an error: Synthesizer failed - {error_msg}",
            StateKeys.TRACES: _add_trace(state, "synthesizer", f"verdict={verdict}", f"ERROR: {e!s}", elapsed),
        }


async def evaluate_node(state: QuiltoState) -> dict[str, Any]:
    """Evaluate node - quality checks response.

    Args:
        state: Current orchestration state.

    Returns:
        Updated state with evaluator output.
    """
    quilto = _get_quilto(state, "evaluate_node")
    if quilto is None:
        return {StateKeys.ERROR: "Internal error: orchestration not initialized"}

    user_input: str = state.get(StateKeys.USER_INPUT, "")

    await _call_progress_handler(quilto, "on_stage", "evaluating")

    start = time.perf_counter()
    retry_count = state.get(StateKeys.RETRY_COUNT, 0)
    await _call_progress_handler(quilto, "on_agent_start", "evaluator", f"attempt={retry_count + 1}")

    try:
        # Reconstruct domain context with defensive validation
        domain_context, _was_fallback = _get_domain_context_with_fallback(state, "evaluate_node")

        # Reconstruct AnalyzerOutput
        analyzer_output_dict = state.get(StateKeys.ANALYZER_OUTPUT, {})
        analyzer_output = AnalyzerOutput.model_validate(analyzer_output_dict)

        response = state.get(StateKeys.RESPONSE, "")
        entries = state.get(StateKeys.ENTRIES, [])

        # Format entries summary
        entries_summary = _format_entries_summary(entries)
        conversation_context = state.get(StateKeys.CONVERSATION_CONTEXT)

        evaluator = EvaluatorAgent(quilto.llm_client)
        evaluator_input = EvaluatorInput(
            query=user_input,
            response=response,
            analysis=analyzer_output,
            entries_summary=entries_summary,
            evaluation_rules=domain_context.evaluation_rules,
            attempt_number=retry_count + 1,
            conversation_context=conversation_context,
        )
        evaluator_output = await evaluator.evaluate(evaluator_input)

        elapsed = (time.perf_counter() - start) * 1000
        await _call_progress_handler(
            quilto, "on_agent_complete", "evaluator", elapsed / 1000, evaluator_output.model_dump(mode="json")
        )

        # Calculate confidence
        confidence = _calculate_confidence(analyzer_output, evaluator_output)

        return {
            StateKeys.EVAL_VERDICT: evaluator_output.overall_verdict.value,
            StateKeys.EVAL_FEEDBACK: evaluator_output.feedback,
            StateKeys.EVALUATOR_OUTPUT: evaluator_output.model_dump(),
            StateKeys.CONFIDENCE: confidence,
            StateKeys.TRACES: _add_trace(
                state,
                "evaluator",
                f"attempt={retry_count + 1}",
                f"verdict={evaluator_output.overall_verdict.value}",
                elapsed,
            ),
        }
    except Exception as e:
        elapsed = (time.perf_counter() - start) * 1000
        logger.exception("evaluate_node failed for query: %s", user_input[:50])
        await _call_progress_handler(quilto, "on_agent_complete", "evaluator", elapsed / 1000, {})
        return {
            StateKeys.ERROR: f"Evaluator failed: {e!s}",
            StateKeys.EVAL_VERDICT: "insufficient",
            StateKeys.CONFIDENCE: 0.5,
            StateKeys.TRACES: _add_trace(state, "evaluator", f"attempt={retry_count + 1}", f"ERROR: {e!s}", elapsed),
        }


def _format_entries_summary(entries: list[dict[str, Any]]) -> str:
    """Format entries into a summary string for Evaluator.

    Args:
        entries: List of entry dicts.

    Returns:
        Summary string of entries.
    """
    if not entries:
        return "(No entries retrieved)"

    lines: list[str] = []
    for entry in entries[:10]:
        date_str = str(entry.get("date", "unknown"))
        raw_content = entry.get("raw_content", "")
        summary = raw_content[:50] + "..." if len(raw_content) > 50 else raw_content
        lines.append(f"{date_str}: {summary}")

    return f"{len(entries)} entries: " + "; ".join(lines)


async def parse_node(state: QuiltoState) -> dict[str, Any]:
    """Parse node - parses LOG input.

    Args:
        state: Current orchestration state.

    Returns:
        Updated state with parser output.
    """
    quilto = _get_quilto(state, "parse_node")
    if quilto is None:
        return {StateKeys.ERROR: "Internal error: orchestration not initialized"}

    user_input: str = state.get(StateKeys.USER_INPUT, "")

    await _call_progress_handler(quilto, "on_stage", "parsing")

    start = time.perf_counter()
    await _call_progress_handler(quilto, "on_agent_start", "parser", user_input[:50])

    # Get observability provider for tool instrumentation
    provider = _get_observability_provider(state)

    try:
        # Reconstruct domain context with defensive validation
        domain_context, _was_fallback = _get_domain_context_with_fallback(state, "parse_node")

        # Build domain schemas from domains
        domain_schemas: dict[str, type] = {}
        for domain in quilto.domains:
            domain_schemas[domain.name] = domain.log_schema

        parser = ParserAgent(quilto.llm_client)
        parser_input = ParserInput(
            raw_input=user_input,
            timestamp=datetime.now(UTC),
            domain_schemas=domain_schemas,
            vocabulary=domain_context.vocabulary,
        )
        parser_output = await parser.parse(parser_input)

        elapsed = (time.perf_counter() - start) * 1000
        await _call_progress_handler(
            quilto, "on_agent_complete", "parser", elapsed / 1000, parser_output.model_dump(mode="json")
        )

        # Save entry to storage for LOG persistence
        try:
            now = datetime.now(UTC)
            entry = Entry(
                id=f"{now.strftime('%Y-%m-%d_%H-%M-%S')}_{uuid.uuid4().hex[:6]}",
                date=now.date(),
                timestamp=now,
                raw_content=user_input,
                parsed_data=parser_output.domain_data,
            )

            # Wrap storage save in observability span
            # Calculate file paths inline for observability (per AC#2 requirement)
            # Uses same path structure as StorageRepository._get_raw_path/_get_parsed_path
            base = quilto.storage.base_path
            d = entry.date
            raw_path = base / "raw" / str(d.year) / f"{d.month:02d}" / f"{d.isoformat()}.md"
            parsed_path = base / "parsed" / str(d.year) / f"{d.month:02d}" / f"{d.isoformat()}.json"
            with provider.span(
                "storage.save_entry",
                metadata={
                    "entry_id": entry.id,
                    "date": str(entry.date),
                    "domains": list(parser_output.domain_data.keys()),
                    "raw_file_path": str(raw_path),
                    "parsed_file_path": str(parsed_path),
                },
            ):
                quilto.storage.save_entry(entry)

            logger.debug("Saved LOG entry: %s", entry.id)
        except Exception as e:
            logger.warning("Failed to save LOG entry to storage: %s", e)
            # Continue - save failure should not block parse response

        return {
            StateKeys.PARSED_DATA: parser_output.domain_data,
            StateKeys.PARSER_OUTPUT: parser_output.model_dump(),
            StateKeys.TRACES: _add_trace(
                state, "parser", user_input[:50], f"domains={list(parser_output.domain_data.keys())}", elapsed
            ),
        }
    except Exception as e:
        elapsed = (time.perf_counter() - start) * 1000
        await _call_progress_handler(quilto, "on_agent_complete", "parser", elapsed / 1000, {})
        return {
            StateKeys.ERROR: f"Parser failed: {e!s}",
            StateKeys.PARSED_DATA: None,
        }


async def correction_node(state: QuiltoState) -> dict[str, Any]:
    """Correction node - handles CORRECTION input type.

    Args:
        state: Current orchestration state.

    Returns:
        Updated state with correction result.
    """
    quilto = _get_quilto(state, "correction_node")
    if quilto is None:
        return {StateKeys.ERROR: "Internal error: orchestration not initialized"}

    await _call_progress_handler(quilto, "on_stage", "correcting")

    start = time.perf_counter()
    await _call_progress_handler(quilto, "on_agent_start", "correction", "upsert")

    # Get observability provider for tool instrumentation
    provider = _get_observability_provider(state)

    try:
        from datetime import timedelta

        from quilto.agents.models import RouterOutput

        # Reconstruct domain context with defensive validation
        domain_context, _was_fallback = _get_domain_context_with_fallback(state, "correction_node")

        router_output_dict = state.get(StateKeys.ROUTER_OUTPUT, {})
        router_output = RouterOutput.model_validate(router_output_dict)

        # Build domain schemas
        domain_schemas: dict[str, type] = {}
        for domain in quilto.domains:
            domain_schemas[domain.name] = domain.log_schema

        # Get recent entries for correction target identification
        recent_date = datetime.now(UTC).date() - timedelta(days=7)
        end_date = datetime.now(UTC).date()

        # Wrap storage retrieval in observability span
        with provider.span(
            "storage.get_entries_by_date_range",
            metadata={
                "start_date": str(recent_date),
                "end_date": str(end_date),
                "purpose": "correction_target_identification",
            },
        ):
            recent_entries = quilto.storage.get_entries_by_date_range(recent_date, end_date)

        user_input: str = state.get(StateKeys.USER_INPUT, "")

        parser = ParserAgent(quilto.llm_client)

        # Wrap correction processing in observability span (includes internal storage operations)
        with provider.span(
            "process_correction",
            metadata={
                "recent_entries_count": len(recent_entries),
                "correction_target": router_output.correction_target,
            },
        ):
            result = await process_correction(
                router_output=router_output,
                parser_agent=parser,
                storage=quilto.storage,
                recent_entries=recent_entries,
                domain_schemas=domain_schemas,
                vocabulary=domain_context.vocabulary,
                user_input=user_input,
            )

        elapsed = (time.perf_counter() - start) * 1000
        await _call_progress_handler(
            quilto, "on_agent_complete", "correction", elapsed / 1000, result.model_dump(mode="json")
        )

        # Generate user-facing response
        if result.success:
            response = f"Corrected entry {result.target_entry_id}: {result.correction_delta}"
        else:
            response = f"Could not process correction: {result.error_message}"

        return {
            StateKeys.CORRECTION_RESULT: result.model_dump(),
            StateKeys.RESPONSE: response,
            StateKeys.TRACES: _add_trace(state, "correction", "upsert", f"success={result.success}", elapsed),
        }
    except Exception as e:
        elapsed = (time.perf_counter() - start) * 1000
        await _call_progress_handler(quilto, "on_agent_complete", "correction", elapsed / 1000, {})
        error_result = CorrectionResult(success=False, error_message=str(e))
        return {
            StateKeys.ERROR: f"Correction failed: {e!s}",
            StateKeys.CORRECTION_RESULT: error_result.model_dump(),
            StateKeys.RESPONSE: f"Could not process correction: {e!s}",
        }


async def observe_node(state: QuiltoState) -> dict[str, Any]:
    """Observe node - triggers Observer for learning.

    Args:
        state: Current orchestration state.

    Returns:
        Updated state after Observer.
    """
    quilto = _get_quilto(state, "observe_node")
    if quilto is None:
        return {StateKeys.ERROR: "Internal error: orchestration not initialized"}

    # Check if Observer is enabled
    if not quilto.observer_config.enable_post_query:
        return {}

    await _call_progress_handler(quilto, "on_stage", "observing")

    start = time.perf_counter()
    await _call_progress_handler(quilto, "on_agent_start", "observer", "post_query")

    # Get observability provider for tool instrumentation
    provider = _get_observability_provider(state)

    try:
        from quilto.agents.models import ObserverInput

        # Reconstruct domain context with defensive validation
        domain_context, was_fallback = _get_domain_context_with_fallback(state, "observer_node")
        if was_fallback:
            return {StateKeys.OBSERVER_ERROR: "No valid domain_context available"}

        # Get context manager
        context_manager = GlobalContextManager(quilto.storage)

        # Wrap context read in observability span
        with provider.span(
            "context_manager.read_context",
            metadata={"storage_base_path": str(quilto.storage.base_path)},
        ):
            global_context = context_manager.read_context()

        serialized_context = serialize_global_context(global_context)

        # Get combined guidance
        guidance = get_combined_context_guidance(domain_context)

        # Build ObserverInput
        user_input: str = state.get(StateKeys.USER_INPUT, "")
        response = state.get(StateKeys.RESPONSE, "")
        analyzer_output_dict = state.get(StateKeys.ANALYZER_OUTPUT, {})
        conversation_context = state.get(StateKeys.CONVERSATION_CONTEXT)

        observer_input = ObserverInput(
            trigger="post_query",
            current_global_context=serialized_context,
            context_management_guidance=guidance,
            query=user_input,
            analysis=analyzer_output_dict,
            response=response,
            conversation_context=conversation_context,
        )

        observer = ObserverAgent(quilto.llm_client)
        observer_output = await observer.observe(observer_input)

        # Apply updates if needed
        if observer_output.should_update:
            # Wrap context apply in observability span
            with provider.span(
                "context_manager.apply_updates",
                metadata={"updates_count": len(observer_output.updates)},
            ):
                context_manager.apply_updates(observer_output.updates)

        elapsed = (time.perf_counter() - start) * 1000
        await _call_progress_handler(
            quilto, "on_agent_complete", "observer", elapsed / 1000, observer_output.model_dump(mode="json")
        )

        return {
            StateKeys.OBSERVER_OUTPUT: observer_output.model_dump(),
            StateKeys.TRACES: _add_trace(
                state, "observer", "post_query", f"updates={len(observer_output.updates)}", elapsed
            ),
        }
    except Exception as e:
        # Observer failures are non-fatal but should be logged for debugging
        elapsed = (time.perf_counter() - start) * 1000
        error_info = {"error": str(e), "error_type": type(e).__name__}
        await _call_progress_handler(quilto, "on_agent_complete", "observer", elapsed / 1000, error_info)
        logger.warning("observe_node failed: %s", e)
        return {StateKeys.OBSERVER_ERROR: str(e)}


async def check_both_node(state: QuiltoState) -> dict[str, Any]:
    """Check if BOTH flow needs to run parse after query.

    Also sets is_partial=True if max_retries was reached without passing.

    Args:
        state: Current orchestration state.

    Returns:
        Dict with is_partial flag if max_retries reached.
    """
    eval_verdict = state.get(StateKeys.EVAL_VERDICT, "insufficient")
    retry_count = state.get(StateKeys.RETRY_COUNT, 0)
    max_retries = state.get(StateKeys.MAX_RETRIES, 2)

    # Set is_partial if we reached max_retries without passing
    if eval_verdict != "sufficient" and retry_count >= max_retries:
        return {StateKeys.IS_PARTIAL: True}

    return {}


async def retry_node(state: QuiltoState) -> dict[str, Any]:
    """Retry node - prepares for retry attempt.

    Args:
        state: Current orchestration state.

    Returns:
        Updated state with incremented retry count.
    """
    quilto = _get_quilto(state, "retry_node")
    if quilto is None:
        return {StateKeys.ERROR: "Internal error: orchestration not initialized"}

    retry_count = state.get(StateKeys.RETRY_COUNT, 0)

    # Get feedback reason
    eval_feedback = state.get(StateKeys.EVAL_FEEDBACK)
    reason = eval_feedback[0] if isinstance(eval_feedback, list) and eval_feedback else "insufficient"

    await _call_progress_handler(quilto, "on_retry", retry_count + 1, reason)

    return {
        StateKeys.RETRY_COUNT: retry_count + 1,
    }


# =============================================================================
# Routing Functions
# =============================================================================


def route_after_router(state: QuiltoState) -> Literal["plan", "parse", "correction"]:
    """Route after Router based on input_type.

    Args:
        state: Current orchestration state.

    Returns:
        Next node name.
    """
    input_type = state.get(StateKeys.INPUT_TYPE, "query")

    if input_type == "log":
        return "parse"
    elif input_type == "correction":
        return "correction"
    else:  # query or both
        return "plan"


def route_after_plan(state: QuiltoState) -> Literal["retrieve", "__end__"]:
    """Route after Planner based on next_action.

    Args:
        state: Current orchestration state.

    Returns:
        Next node name.
    """
    next_action = state.get(StateKeys.NEXT_ACTION, "retrieve")

    if next_action == "clarify":
        return "__end__"
    return "retrieve"


def route_after_evaluate(state: QuiltoState) -> Literal["check_both", "retry"]:
    """Route after Evaluator based on verdict and retry count.

    Args:
        state: Current orchestration state.

    Returns:
        Next node name.
    """
    eval_verdict = state.get(StateKeys.EVAL_VERDICT, "insufficient")
    retry_count = state.get(StateKeys.RETRY_COUNT, 0)
    max_retries = state.get(StateKeys.MAX_RETRIES, 2)

    # Check if passed
    if eval_verdict == "sufficient":
        return "check_both"

    # Check if max retries reached
    if retry_count >= max_retries:
        # Mark as partial and continue
        return "check_both"

    return "retry"


def route_after_check_both(state: QuiltoState) -> Literal["parse", "observe"]:
    """Route after check_both based on input_type.

    Args:
        state: Current orchestration state.

    Returns:
        Next node name.
    """
    input_type = state.get(StateKeys.INPUT_TYPE, "query")

    if input_type == "both":
        return "parse"
    return "observe"


# =============================================================================
# Graph Creation
# =============================================================================


def create_orchestration_graph(quilto: "Quilto") -> OrchestrationGraph:
    """Create the LangGraph orchestration graph.

    Args:
        quilto: Quilto instance for agent creation.

    Returns:
        Compiled StateGraph for orchestration.
    """
    # Create graph
    graph = StateGraph(QuiltoState)

    # Add nodes
    graph.add_node("route", route_node)
    graph.add_node("plan", plan_node)
    graph.add_node("retrieve", retrieve_node)
    graph.add_node("analyze", analyze_node)
    graph.add_node("synthesize", synthesize_node)
    graph.add_node("evaluate", evaluate_node)
    graph.add_node("retry", retry_node)
    graph.add_node("check_both", check_both_node)
    graph.add_node("parse", parse_node)
    graph.add_node("correction", correction_node)
    graph.add_node("observe", observe_node)

    # Set entry point
    graph.set_entry_point("route")

    # Add conditional edges after route
    graph.add_conditional_edges(
        "route",
        route_after_router,
        {
            "plan": "plan",
            "parse": "parse",
            "correction": "correction",
        },
    )

    # Add conditional edges after plan
    graph.add_conditional_edges(
        "plan",
        route_after_plan,
        {
            "retrieve": "retrieve",
            "__end__": END,
        },
    )

    # Linear edges for query flow
    graph.add_edge("retrieve", "analyze")
    graph.add_edge("analyze", "synthesize")
    graph.add_edge("synthesize", "evaluate")

    # Conditional edges after evaluate
    graph.add_conditional_edges(
        "evaluate",
        route_after_evaluate,
        {
            "check_both": "check_both",
            "retry": "retry",
        },
    )

    # Retry goes back to plan
    graph.add_edge("retry", "plan")

    # Conditional edges after check_both
    graph.add_conditional_edges(
        "check_both",
        route_after_check_both,
        {
            "parse": "parse",
            "observe": "observe",
        },
    )

    # Parse and correction go to observe
    graph.add_edge("parse", "observe")
    graph.add_edge("correction", "observe")

    # Observe goes to end
    graph.add_edge("observe", END)

    # Compile and return
    compiled = graph.compile()

    # Wrap to inject quilto reference
    class QuiltoGraph:
        """Wrapper to inject quilto reference into state."""

        def __init__(self, inner_graph: Any, quilto_ref: "Quilto") -> None:
            self._graph = inner_graph
            self._quilto = quilto_ref

        async def ainvoke(self, state: dict[str, Any]) -> dict[str, Any]:
            """Invoke graph with quilto reference injected."""
            state[StateKeys.QUILTO] = self._quilto
            return await self._graph.ainvoke(state)

    return QuiltoGraph(compiled, quilto)
