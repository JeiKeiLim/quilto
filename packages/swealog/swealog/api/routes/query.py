"""POST /query endpoint for processing user queries."""

import logging
import time
from collections.abc import Callable, Generator
from contextlib import contextmanager
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException
from quilto import (
    DomainModule,
    DomainSelector,
    LLMClient,
    RouterAgent,
    RouterInput,
    StorageRepository,
)
from quilto.agents import (
    AnalyzerAgent,
    AnalyzerInput,
    AnalyzerOutput,
    EvaluatorAgent,
    EvaluatorInput,
    EvaluatorOutput,
    PlannerAgent,
    PlannerInput,
    RetrieverAgent,
    RetrieverInput,
    SynthesizerAgent,
    SynthesizerInput,
    Verdict,
)

from swealog.api.dependencies import get_domains, get_llm_client, get_storage
from swealog.api.models import QueryRequest, QueryResponse

logger = logging.getLogger(__name__)

router = APIRouter()

MAX_RETRIES = 2

# Confidence score constants for _calculate_confidence
_CONFIDENCE_SUFFICIENT = 0.8
_CONFIDENCE_PARTIAL = 0.6
_CONFIDENCE_INSUFFICIENT = 0.4
_CONFIDENCE_ADJUSTMENT = 0.1

# Type alias for debug callback signature
# (agent_name, event, data, elapsed_time)
# data can be: input summary string (for "start"), full output dict (for "output"), empty (for "end")
DebugCallback = Callable[[str, str, Any, float], None]


class _DebugTimer:
    """Internal helper for timing agent execution with optional callback."""

    def __init__(self, callback: DebugCallback | None = None) -> None:
        self._callback = callback

    @contextmanager
    def track(self, agent_name: str, input_summary: str) -> Generator[dict[str, float]]:
        """Track agent execution time.

        Args:
            agent_name: Name of the agent being tracked.
            input_summary: Brief description of input.

        Yields:
            Dict that will contain 'elapsed' after context exits.
        """
        result: dict[str, float] = {"elapsed": 0.0}
        if self._callback:
            self._callback(agent_name, "start", input_summary, 0.0)
        start = time.perf_counter()
        yield result
        elapsed = time.perf_counter() - start
        result["elapsed"] = elapsed
        if self._callback:
            self._callback(agent_name, "end", None, elapsed)

    def log_output(self, agent_name: str, output_data: Any) -> None:
        """Log agent output.

        Args:
            agent_name: Name of the agent.
            output_data: Full output data (dict from model_dump() or any serializable).
        """
        if self._callback:
            self._callback(agent_name, "output", output_data, 0.0)


async def execute_query_pipeline(
    query: str,
    llm_client: LLMClient,
    storage: StorageRepository,
    domains: list[DomainModule],
    debug_callback: DebugCallback | None = None,
    collect_outputs: bool = False,
    conversation_context: str | None = None,
) -> dict[str, Any]:
    """Execute the full query pipeline.

    Routes query through: Router -> Planner -> Retriever -> Analyzer -> Synthesizer -> Evaluator
    with retry logic for failed evaluations.

    Args:
        query: The user's query text.
        llm_client: LLM client for agents.
        storage: Storage repository for entries.
        domains: Available domain modules.
        debug_callback: Optional callback for debug logging.
            Called with (agent_name, event, summary, elapsed_time).
            event is "start", "output", or "end".
        collect_outputs: If True, include intermediate_outputs in result.
            Note: router_output is NOT included here - capture it in auto_cmd.py
            since Router runs before this function in the auto flow.
        conversation_context: Recent context from same interaction (e.g., log_portion
            in BOTH-type inputs). Helps Planner interpret vague queries.

    Returns:
        Dict with response, sources, confidence, and is_partial.
        If collect_outputs=True, also includes intermediate_outputs dict
        (excluding router - that runs before pipeline in auto flow).
    """
    # Initialize domain selector and debug timer
    selector = DomainSelector(domains)
    domain_infos = selector.get_domain_infos()
    timer = _DebugTimer(debug_callback)

    # Step 1: Route query
    router_agent = RouterAgent(llm_client)
    router_input = RouterInput(raw_input=query, available_domains=domain_infos)
    with timer.track("Router", f'"{query[:50]}..."' if len(query) > 50 else f'"{query}"'):
        router_output = await router_agent.classify(router_input)
    timer.log_output("Router", router_output.model_dump())

    # Build active domain context from selected domains
    active_context = selector.build_active_context(router_output.selected_domains)

    # Get storage summary for Planner's date-range decisions (Story 13.2)
    storage_summary = storage.get_storage_summary().model_dump()

    # Step 2: Plan retrieval
    planner = PlannerAgent(llm_client)
    planner_input = PlannerInput(
        query=query,
        domain_context=active_context,
        storage_summary=storage_summary,
        conversation_context=conversation_context,
    )
    with timer.track("Planner", "query_type inference"):
        planner_output = await planner.plan(planner_input)
    timer.log_output("Planner", planner_output.model_dump())

    # Check if Planner requests clarification (AC #1, #3)
    if planner_output.next_action == "clarify" and planner_output.clarify_questions:
        result: dict[str, Any] = {
            "response": "",
            "sources": [],
            "confidence": 0.0,
            "is_partial": False,
            "needs_clarification": True,
            "clarification_questions": planner_output.clarify_questions,
        }
        if collect_outputs:
            # Note: router_output not included - captured in auto_cmd.py
            result["intermediate_outputs"] = {
                "planner": planner_output.model_dump(),
            }
        return result

    # Step 3: Retrieve entries
    retriever = RetrieverAgent(storage)
    retriever_input = RetrieverInput(
        instructions=planner_output.retrieval_instructions,
        max_entries=100,
    )
    with timer.track("Retriever", f"instructions={len(planner_output.retrieval_instructions)} filters"):
        retriever_output = await retriever.retrieve(retriever_input)
    timer.log_output("Retriever", retriever_output.model_dump())

    # Collect source entry IDs
    sources: list[str] = [entry.id for entry in retriever_output.entries]

    # Step 4-6: Analyze -> Synthesize -> Evaluate with retry loop
    retry_count = 0
    is_partial = False
    final_response = ""
    confidence = 0.0
    # Initialize for pyright - will be overwritten in loop (loop always runs at least once)
    analysis: AnalyzerOutput | None = None
    synthesizer_output: Any = None
    evaluation: EvaluatorOutput | None = None

    while retry_count <= MAX_RETRIES:
        # Step 4: Analyze retrieved entries
        analyzer = AnalyzerAgent(llm_client)
        analyzer_input = AnalyzerInput(
            query=query,
            query_type=planner_output.query_type,
            entries=[e.model_dump() for e in retriever_output.entries],
            retrieval_summary=retriever_output.retrieval_summary,
            domain_context=active_context,
        )
        with timer.track("Analyzer", f"entries={len(retriever_output.entries)}"):
            analysis = await analyzer.analyze(analyzer_input)
        timer.log_output("Analyzer", analysis.model_dump())

        # Check if we need to generate partial response
        if analysis.verdict == Verdict.INSUFFICIENT and retry_count == MAX_RETRIES:
            is_partial = True

        # Step 5: Synthesize response
        synthesizer = SynthesizerAgent(llm_client)
        synthesizer_input = SynthesizerInput(
            query=query,
            query_type=planner_output.query_type,
            analysis=analysis,
            vocabulary=active_context.vocabulary,
            response_style="concise",
            is_partial=is_partial,
        )
        with timer.track("Synthesizer", f"verdict={analysis.verdict.value}"):
            synthesizer_output = await synthesizer.synthesize(synthesizer_input)
        timer.log_output("Synthesizer", synthesizer_output.model_dump())

        # Step 6: Evaluate response
        evaluator = EvaluatorAgent(llm_client)
        entries_summary = _format_entries_summary(retriever_output.entries)
        evaluator_input = EvaluatorInput(
            query=query,
            response=synthesizer_output.response,
            analysis=analysis,
            entries_summary=entries_summary,
            evaluation_rules=active_context.evaluation_rules,
            attempt_number=retry_count + 1,
        )
        with timer.track("Evaluator", f"attempt={retry_count + 1}"):
            evaluation = await evaluator.evaluate(evaluator_input)
        timer.log_output("Evaluator", evaluation.model_dump())

        # Check if passed
        if evaluator.is_passed(evaluation):
            final_response = synthesizer_output.response
            confidence = _calculate_confidence(analysis, evaluation)
            break

        # Store feedback for next iteration and increment
        evaluation_feedback = evaluation.feedback[0] if evaluation.feedback else None
        retry_count += 1

        # If max retries reached, return partial/best-effort
        if retry_count > MAX_RETRIES:
            is_partial = True
            final_response = synthesizer_output.response
            confidence = _calculate_confidence(analysis, evaluation)
            break

        # Re-plan with feedback for next iteration
        planner_input = PlannerInput(
            query=query,
            domain_context=active_context,
            evaluation_feedback=evaluation_feedback,
            retrieval_history=[a.model_dump() for a in retriever_output.retrieval_summary],
            storage_summary=storage_summary,
        )
        planner_output = await planner.plan(planner_input)

        # Re-retrieve with updated instructions
        retriever_input = RetrieverInput(
            instructions=planner_output.retrieval_instructions,
            max_entries=100,
        )
        retriever_output = await retriever.retrieve(retriever_input)

    result: dict[str, Any] = {
        "response": final_response,
        "sources": sources,
        "confidence": confidence,
        "is_partial": is_partial,
        "needs_clarification": False,
        "clarification_questions": None,
    }

    if collect_outputs and analysis is not None and evaluation is not None:
        # Note: router_output not available here - captured in auto_cmd.py
        result["intermediate_outputs"] = {
            "planner": planner_output.model_dump(),
            "retriever": retriever_output.model_dump(),
            "analyzer": analysis.model_dump(),
            "synthesizer": synthesizer_output.model_dump(),
            "evaluator": evaluation.model_dump(),  # Last evaluation (may be after retry)
        }

    return result


def _format_entries_summary(entries: list[Any]) -> str:
    """Format entries into a summary string for Evaluator.

    Args:
        entries: List of Entry objects.

    Returns:
        Summary string of entries.
    """
    if not entries:
        return "(No entries retrieved)"

    lines: list[str] = []
    for entry in entries[:10]:  # Limit to first 10 for summary
        date_str = str(getattr(entry, "date", "unknown"))
        raw_content: str = getattr(entry, "raw_content", "")
        summary = raw_content[:50] + "..." if len(raw_content) > 50 else raw_content
        lines.append(f"{date_str}: {summary}")

    result = f"{len(entries)} entries: " + "; ".join(lines)
    return result


def _calculate_confidence(analysis: AnalyzerOutput, evaluation: EvaluatorOutput) -> float:
    """Calculate overall confidence score.

    Confidence is determined by analysis verdict (sufficient/partial/insufficient)
    with an adjustment based on evaluation verdict.

    Args:
        analysis: Analyzer output with findings.
        evaluation: Evaluator output with dimension scores.

    Returns:
        Confidence score between 0.0 and 1.0.
    """
    # Base confidence from analysis verdict
    if analysis.verdict == Verdict.SUFFICIENT:
        base = _CONFIDENCE_SUFFICIENT
    elif analysis.verdict == Verdict.PARTIAL:
        base = _CONFIDENCE_PARTIAL
    else:
        base = _CONFIDENCE_INSUFFICIENT

    # Adjust based on evaluation verdict
    adjustment = _CONFIDENCE_ADJUSTMENT if evaluation.overall_verdict == Verdict.SUFFICIENT else -_CONFIDENCE_ADJUSTMENT
    adjusted = base + adjustment

    return min(1.0, max(0.0, adjusted))


@router.post("/query", response_model=QueryResponse)
async def process_query(
    request: QueryRequest,
    llm_client: Annotated[LLMClient, Depends(get_llm_client)],
    storage: Annotated[StorageRepository, Depends(get_storage)],
    domains: Annotated[list[DomainModule], Depends(get_domains)],
) -> QueryResponse:
    """Process a user query through the full agent pipeline.

    Routes query through Router -> Planner -> Retriever -> Analyzer -> Synthesizer -> Evaluator
    with retry logic when evaluation fails.

    Args:
        request: Query request with text field.
        llm_client: LLM client for agents.
        storage: Storage repository for entries.
        domains: Available domain modules.

    Returns:
        QueryResponse with response, sources, confidence, and partial flag.

    Raises:
        HTTPException: If query processing fails.
    """
    try:
        result = await execute_query_pipeline(
            query=request.text,
            llm_client=llm_client,
            storage=storage,
            domains=domains,
        )

        return QueryResponse(
            response=result["response"],
            sources=result["sources"],
            confidence=result["confidence"],
            partial=result["is_partial"],
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        logger.exception("Query processing failed: %s", e)
        raise HTTPException(status_code=500, detail=f"Internal error: {type(e).__name__}") from e
