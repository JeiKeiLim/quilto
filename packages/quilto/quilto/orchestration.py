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
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any, Literal, TypedDict

from langgraph.graph import END, StateGraph

from quilto.agents import (
    AnalyzerAgent,
    AnalyzerInput,
    AnalyzerOutput,
    EvaluatorAgent,
    EvaluatorInput,
    EvaluatorOutput,
    InputType,
    ObserverAgent,
    ParserAgent,
    ParserInput,
    PlannerAgent,
    PlannerInput,
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

if TYPE_CHECKING:
    from quilto.quilto import Quilto

logger = logging.getLogger(__name__)


# Confidence score constants
_CONFIDENCE_SUFFICIENT = 0.8
_CONFIDENCE_PARTIAL = 0.6
_CONFIDENCE_INSUFFICIENT = 0.4
_CONFIDENCE_ADJUSTMENT = 0.1


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
    traces = list(state.get("traces", []))
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
    quilto: Quilto = state["_quilto"]  # type: ignore[typeddict-item]
    user_input: str = state["user_input"]  # type: ignore[typeddict-item]
    mode = state.get("mode", "auto")

    await _call_progress_handler(quilto, "on_stage", "routing")

    # If mode is forced, skip Router
    if mode == "log":
        return {
            "input_type": "log",
            "selected_domains": [d.name for d in quilto.domains],
            "router_output": {"forced_mode": "log"},
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
        router_input = RouterInput(raw_input=user_input, available_domains=domain_infos)
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
            "input_type": input_type,
            "selected_domains": router_output.selected_domains,
            "router_output": router_output.model_dump(),
            "domain_context": domain_context.model_dump(),
            "traces": _add_trace(state, "router", user_input[:50], f"type={input_type}", elapsed),
        }
    except Exception as e:
        elapsed = (time.perf_counter() - start) * 1000
        await _call_progress_handler(quilto, "on_agent_complete", "router", elapsed / 1000, {})
        return {
            "error": f"Router failed: {e!s}",
            "input_type": "query",  # Default to query on error
            "selected_domains": [],
        }


async def plan_node(state: QuiltoState) -> dict[str, Any]:
    """Plan node - creates retrieval plan.

    Args:
        state: Current orchestration state.

    Returns:
        Updated state with planner output.
    """
    quilto: Quilto = state["_quilto"]  # type: ignore[typeddict-item]
    user_input: str = state["user_input"]  # type: ignore[typeddict-item]
    conversation_context = state.get("conversation_context")

    await _call_progress_handler(quilto, "on_stage", "planning")

    start = time.perf_counter()
    await _call_progress_handler(quilto, "on_agent_start", "planner", "query analysis")

    try:
        # Get storage summary (required by Planner)
        storage_summary: dict[str, Any] = quilto._get_storage_summary()  # type: ignore[reportPrivateUsage]  # noqa: SLF001

        # Reconstruct domain context
        from quilto.agents.models import ActiveDomainContext

        domain_context_dict = state.get("domain_context", {})
        domain_context = ActiveDomainContext.model_validate(domain_context_dict)

        # Get evaluation feedback from previous retry if any
        eval_feedback = state.get("eval_feedback")
        if state.get("retry_count", 0) > 0:
            evaluation_feedback = eval_feedback[0] if isinstance(eval_feedback, list) and eval_feedback else None
        else:
            evaluation_feedback = None

        # Get retrieval history from previous retry if any
        retrieval_history: list[dict[str, Any]] = []
        if state.get("retry_count", 0) > 0 and state.get("retrieval_summary"):
            retrieval_history = state.get("retrieval_summary") or []

        planner = PlannerAgent(quilto.llm_client)
        planner_input = PlannerInput(
            query=user_input,
            domain_context=domain_context,
            storage_summary=storage_summary,  # type: ignore[arg-type]
            conversation_context=conversation_context,
            evaluation_feedback=evaluation_feedback,  # type: ignore[arg-type]
            retrieval_history=retrieval_history,
        )
        planner_output = await planner.plan(planner_input)

        elapsed = (time.perf_counter() - start) * 1000
        await _call_progress_handler(
            quilto, "on_agent_complete", "planner", elapsed / 1000, planner_output.model_dump(mode="json")
        )

        # Get query type value
        query_type_val = planner_output.query_type
        query_type_str = query_type_val.value if hasattr(query_type_val, "value") else str(query_type_val)

        # Get clarify questions if present
        clarify_q: list[dict[str, Any]] | None = None
        if planner_output.clarify_questions:
            clarify_q = [q.model_dump() for q in planner_output.clarify_questions]  # type: ignore[union-attr]

        # Get retrieval instructions
        retrieval_instr: list[dict[str, Any]] = []
        for i in planner_output.retrieval_instructions:
            if hasattr(i, "model_dump"):
                retrieval_instr.append(i.model_dump())  # type: ignore[union-attr]
            else:
                retrieval_instr.append(i)  # type: ignore[arg-type]

        return {
            "query_type": query_type_str,
            "retrieval_instructions": retrieval_instr,
            "next_action": planner_output.next_action,
            "clarify_questions": clarify_q,
            "planner_output": planner_output.model_dump(),
            "storage_summary": storage_summary,
            "traces": _add_trace(state, "planner", "query analysis", f"action={planner_output.next_action}", elapsed),
        }
    except Exception as e:
        elapsed = (time.perf_counter() - start) * 1000
        await _call_progress_handler(quilto, "on_agent_complete", "planner", elapsed / 1000, {})
        return {
            "error": f"Planner failed: {e!s}",
            "next_action": "clarify",
        }


async def retrieve_node(state: QuiltoState) -> dict[str, Any]:
    """Retrieve node - fetches entries from storage.

    Args:
        state: Current orchestration state.

    Returns:
        Updated state with retriever output.
    """
    quilto: Quilto = state["_quilto"]  # type: ignore[typeddict-item]

    await _call_progress_handler(quilto, "on_stage", "retrieving")

    start = time.perf_counter()
    instructions = state.get("retrieval_instructions", [])
    await _call_progress_handler(quilto, "on_agent_start", "retriever", f"{len(instructions)} instructions")

    try:
        # Instructions are already dict-based (from PlannerOutput.retrieval_instructions)
        retriever = RetrieverAgent(quilto.storage)
        retriever_input = RetrieverInput(
            instructions=instructions,
            max_entries=100,
        )
        retriever_output = await retriever.retrieve(retriever_input)

        elapsed = (time.perf_counter() - start) * 1000
        await _call_progress_handler(
            quilto, "on_agent_complete", "retriever", elapsed / 1000, retriever_output.model_dump(mode="json")
        )

        return {
            "entries": [e.model_dump() for e in retriever_output.entries],
            "retrieval_summary": [s.model_dump() for s in retriever_output.retrieval_summary],
            "source_entry_ids": [e.id for e in retriever_output.entries],
            "retriever_output": retriever_output.model_dump(),
            "traces": _add_trace(
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
            "error": f"Retriever failed: {e!s}",
            "entries": [],
            "source_entry_ids": [],
        }


async def analyze_node(state: QuiltoState) -> dict[str, Any]:
    """Analyze node - analyzes retrieved entries.

    Args:
        state: Current orchestration state.

    Returns:
        Updated state with analyzer output.
    """
    quilto: Quilto = state["_quilto"]
    user_input: str = state["user_input"]

    await _call_progress_handler(quilto, "on_stage", "analyzing")

    start = time.perf_counter()
    entries = state.get("entries", [])
    await _call_progress_handler(quilto, "on_agent_start", "analyzer", f"{len(entries)} entries")

    try:
        from quilto.agents.models import ActiveDomainContext

        domain_context_dict = state.get("domain_context", {})
        domain_context = ActiveDomainContext.model_validate(domain_context_dict)

        query_type = state.get("query_type", "factual")
        retrieval_summary = state.get("retrieval_summary", [])

        analyzer = AnalyzerAgent(quilto.llm_client)
        analyzer_input = AnalyzerInput(
            query=user_input,
            query_type=query_type,  # type: ignore[arg-type]
            entries=entries,
            retrieval_summary=retrieval_summary,  # type: ignore[arg-type]
            domain_context=domain_context,
        )
        analyzer_output = await analyzer.analyze(analyzer_input)

        elapsed = (time.perf_counter() - start) * 1000
        await _call_progress_handler(
            quilto, "on_agent_complete", "analyzer", elapsed / 1000, analyzer_output.model_dump(mode="json")
        )

        return {
            "analysis_verdict": analyzer_output.verdict.value,
            "analysis_findings": [f.model_dump() for f in analyzer_output.findings],
            "analyzer_output": analyzer_output.model_dump(),
            "traces": _add_trace(
                state, "analyzer", f"{len(entries)} entries", f"verdict={analyzer_output.verdict.value}", elapsed
            ),
        }
    except Exception as e:
        elapsed = (time.perf_counter() - start) * 1000
        logger.exception("analyze_node failed for query: %s", user_input[:50])
        await _call_progress_handler(quilto, "on_agent_complete", "analyzer", elapsed / 1000, {})

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
            "error": f"Analyzer failed: {e!s}",
            "analysis_verdict": "insufficient",
            "analyzer_output": fallback_output,
            "traces": _add_trace(state, "analyzer", f"{len(entries)} entries", f"ERROR: {e!s}", elapsed),
        }


async def synthesize_node(state: QuiltoState) -> dict[str, Any]:
    """Synthesize node - generates response.

    Args:
        state: Current orchestration state.

    Returns:
        Updated state with synthesizer output.
    """
    quilto: Quilto = state["_quilto"]
    user_input: str = state["user_input"]

    await _call_progress_handler(quilto, "on_stage", "synthesizing")

    start = time.perf_counter()
    verdict = state.get("analysis_verdict", "insufficient")
    await _call_progress_handler(quilto, "on_agent_start", "synthesizer", f"verdict={verdict}")

    try:
        from quilto.agents.models import ActiveDomainContext, SufficiencyEvaluation

        domain_context_dict = state.get("domain_context", {})
        domain_context = ActiveDomainContext.model_validate(domain_context_dict)

        # Reconstruct AnalyzerOutput with defensive validation
        analyzer_output_dict = state.get("analyzer_output", {})
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

        query_type = state.get("query_type", "factual")
        is_partial = state.get("is_partial", False)

        synthesizer = SynthesizerAgent(quilto.llm_client)
        synthesizer_input = SynthesizerInput(
            query=user_input,
            query_type=query_type,  # type: ignore[arg-type]
            analysis=analyzer_output,
            vocabulary=domain_context.vocabulary,
            response_style="concise",
            is_partial=is_partial,
        )
        synthesizer_output = await synthesizer.synthesize(synthesizer_input)

        elapsed = (time.perf_counter() - start) * 1000
        await _call_progress_handler(
            quilto, "on_agent_complete", "synthesizer", elapsed / 1000, synthesizer_output.model_dump(mode="json")
        )

        return {
            "response": synthesizer_output.response,
            "synthesizer_output": synthesizer_output.model_dump(),
            "traces": _add_trace(
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
            "error": f"Synthesizer failed: {e!s}",
            "response": f"I encountered an error: Synthesizer failed - {error_msg}",
            "traces": _add_trace(state, "synthesizer", f"verdict={verdict}", f"ERROR: {e!s}", elapsed),
        }


async def evaluate_node(state: QuiltoState) -> dict[str, Any]:
    """Evaluate node - quality checks response.

    Args:
        state: Current orchestration state.

    Returns:
        Updated state with evaluator output.
    """
    quilto: Quilto = state["_quilto"]
    user_input: str = state["user_input"]

    await _call_progress_handler(quilto, "on_stage", "evaluating")

    start = time.perf_counter()
    retry_count = state.get("retry_count", 0)
    await _call_progress_handler(quilto, "on_agent_start", "evaluator", f"attempt={retry_count + 1}")

    try:
        from quilto.agents.models import ActiveDomainContext

        domain_context_dict = state.get("domain_context", {})
        domain_context = ActiveDomainContext.model_validate(domain_context_dict)

        # Reconstruct AnalyzerOutput
        analyzer_output_dict = state.get("analyzer_output", {})
        analyzer_output = AnalyzerOutput.model_validate(analyzer_output_dict)

        response = state.get("response", "")
        entries = state.get("entries", [])

        # Format entries summary
        entries_summary = _format_entries_summary(entries)

        evaluator = EvaluatorAgent(quilto.llm_client)
        evaluator_input = EvaluatorInput(
            query=user_input,
            response=response,
            analysis=analyzer_output,
            entries_summary=entries_summary,
            evaluation_rules=domain_context.evaluation_rules,
            attempt_number=retry_count + 1,
        )
        evaluator_output = await evaluator.evaluate(evaluator_input)

        elapsed = (time.perf_counter() - start) * 1000
        await _call_progress_handler(
            quilto, "on_agent_complete", "evaluator", elapsed / 1000, evaluator_output.model_dump(mode="json")
        )

        # Calculate confidence
        confidence = _calculate_confidence(analyzer_output, evaluator_output)

        return {
            "eval_verdict": evaluator_output.overall_verdict.value,
            "eval_feedback": evaluator_output.feedback,
            "evaluator_output": evaluator_output.model_dump(),
            "confidence": confidence,
            "traces": _add_trace(
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
            "error": f"Evaluator failed: {e!s}",
            "eval_verdict": "insufficient",
            "confidence": 0.5,
            "traces": _add_trace(state, "evaluator", f"attempt={retry_count + 1}", f"ERROR: {e!s}", elapsed),
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
    quilto: Quilto = state["_quilto"]
    user_input = state["user_input"]

    await _call_progress_handler(quilto, "on_stage", "parsing")

    start = time.perf_counter()
    await _call_progress_handler(quilto, "on_agent_start", "parser", user_input[:50])

    try:
        from quilto.agents.models import ActiveDomainContext

        domain_context_dict = state.get("domain_context", {})
        domain_context = ActiveDomainContext.model_validate(domain_context_dict)

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

        return {
            "parsed_data": parser_output.domain_data,
            "parser_output": parser_output.model_dump(),
            "traces": _add_trace(
                state, "parser", user_input[:50], f"domains={list(parser_output.domain_data.keys())}", elapsed
            ),
        }
    except Exception as e:
        elapsed = (time.perf_counter() - start) * 1000
        await _call_progress_handler(quilto, "on_agent_complete", "parser", elapsed / 1000, {})
        return {
            "error": f"Parser failed: {e!s}",
            "parsed_data": None,
        }


async def correction_node(state: QuiltoState) -> dict[str, Any]:
    """Correction node - handles CORRECTION input type.

    Args:
        state: Current orchestration state.

    Returns:
        Updated state with correction result.
    """
    quilto: Quilto = state["_quilto"]

    await _call_progress_handler(quilto, "on_stage", "correcting")

    start = time.perf_counter()
    await _call_progress_handler(quilto, "on_agent_start", "correction", "upsert")

    try:
        from quilto.agents.models import ActiveDomainContext, RouterOutput

        domain_context_dict = state.get("domain_context", {})
        domain_context = ActiveDomainContext.model_validate(domain_context_dict)

        router_output_dict = state.get("router_output", {})
        router_output = RouterOutput.model_validate(router_output_dict)

        # Build domain schemas
        domain_schemas: dict[str, type] = {}
        for domain in quilto.domains:
            domain_schemas[domain.name] = domain.log_schema

        # Get recent entries for correction target identification
        from datetime import timedelta

        recent_date = datetime.now(UTC).date() - timedelta(days=7)
        recent_entries = quilto.storage.get_entries_by_date_range(recent_date, datetime.now(UTC).date())

        parser = ParserAgent(quilto.llm_client)
        result = await process_correction(
            router_output=router_output,
            parser_agent=parser,
            storage=quilto.storage,
            recent_entries=recent_entries,
            domain_schemas=domain_schemas,
            vocabulary=domain_context.vocabulary,
        )

        elapsed = (time.perf_counter() - start) * 1000
        await _call_progress_handler(
            quilto, "on_agent_complete", "correction", elapsed / 1000, result.model_dump(mode="json")
        )

        return {
            "correction_result": result.model_dump(),
            "traces": _add_trace(state, "correction", "upsert", f"success={result.success}", elapsed),
        }
    except Exception as e:
        elapsed = (time.perf_counter() - start) * 1000
        await _call_progress_handler(quilto, "on_agent_complete", "correction", elapsed / 1000, {})
        return {
            "error": f"Correction failed: {e!s}",
            "correction_result": CorrectionResult(success=False, error_message=str(e)).model_dump(),
        }


async def observe_node(state: QuiltoState) -> dict[str, Any]:
    """Observe node - triggers Observer for learning.

    Args:
        state: Current orchestration state.

    Returns:
        Updated state after Observer.
    """
    quilto: Quilto = state["_quilto"]

    # Check if Observer is enabled
    if not quilto.observer_config.enable_post_query:
        return {}

    await _call_progress_handler(quilto, "on_stage", "observing")

    start = time.perf_counter()
    await _call_progress_handler(quilto, "on_agent_start", "observer", "post_query")

    try:
        from quilto.agents.models import ActiveDomainContext, ObserverInput

        domain_context_dict = state.get("domain_context", {})
        if not domain_context_dict:
            return {}

        domain_context = ActiveDomainContext.model_validate(domain_context_dict)

        # Get context manager
        context_manager = GlobalContextManager(quilto.storage)

        # Get current global context
        global_context = context_manager.read_context()
        serialized_context = serialize_global_context(global_context)

        # Get combined guidance
        guidance = get_combined_context_guidance(domain_context)

        # Build ObserverInput
        user_input = state["user_input"]
        response = state.get("response", "")
        analyzer_output_dict = state.get("analyzer_output", {})

        observer_input = ObserverInput(
            trigger="post_query",
            current_global_context=serialized_context,
            context_management_guidance=guidance,
            query=user_input,
            analysis=analyzer_output_dict,
            response=response,
        )

        observer = ObserverAgent(quilto.llm_client)
        observer_output = await observer.observe(observer_input)

        # Apply updates if needed
        if observer_output.should_update:
            context_manager.apply_updates(observer_output.updates)

        elapsed = (time.perf_counter() - start) * 1000
        await _call_progress_handler(
            quilto, "on_agent_complete", "observer", elapsed / 1000, observer_output.model_dump(mode="json")
        )

        return {
            "observer_output": observer_output.model_dump(),
            "traces": _add_trace(state, "observer", "post_query", f"updates={len(observer_output.updates)}", elapsed),
        }
    except Exception as e:
        # Observer failures are non-fatal but should be logged for debugging
        elapsed = (time.perf_counter() - start) * 1000
        await _call_progress_handler(quilto, "on_agent_complete", "observer", elapsed / 1000, {})
        logger.warning("observe_node failed: %s", e)
        return {}


async def check_both_node(state: QuiltoState) -> dict[str, Any]:
    """Check if BOTH flow needs to run parse after query.

    Also sets is_partial=True if max_retries was reached without passing.

    Args:
        state: Current orchestration state.

    Returns:
        Dict with is_partial flag if max_retries reached.
    """
    eval_verdict = state.get("eval_verdict", "insufficient")
    retry_count = state.get("retry_count", 0)
    max_retries = state.get("max_retries", 2)

    # Set is_partial if we reached max_retries without passing
    if eval_verdict != "sufficient" and retry_count >= max_retries:
        return {"is_partial": True}

    return {}


async def retry_node(state: QuiltoState) -> dict[str, Any]:
    """Retry node - prepares for retry attempt.

    Args:
        state: Current orchestration state.

    Returns:
        Updated state with incremented retry count.
    """
    quilto: Quilto = state["_quilto"]
    retry_count = state.get("retry_count", 0)

    # Get feedback reason
    eval_feedback = state.get("eval_feedback")
    reason = eval_feedback[0] if isinstance(eval_feedback, list) and eval_feedback else "insufficient"

    await _call_progress_handler(quilto, "on_retry", retry_count + 1, reason)

    return {
        "retry_count": retry_count + 1,
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
    input_type = state.get("input_type", "query")

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
    next_action = state.get("next_action", "retrieve")

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
    eval_verdict = state.get("eval_verdict", "insufficient")
    retry_count = state.get("retry_count", 0)
    max_retries = state.get("max_retries", 2)

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
    input_type = state.get("input_type", "query")

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
            state["_quilto"] = self._quilto
            return await self._graph.ainvoke(state)

    return QuiltoGraph(compiled, quilto)
