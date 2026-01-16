"""POST /query endpoint for processing user queries."""

import logging
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


async def execute_query_pipeline(
    query: str,
    llm_client: LLMClient,
    storage: StorageRepository,
    domains: list[DomainModule],
) -> dict[str, Any]:
    """Execute the full query pipeline.

    Routes query through: Router -> Planner -> Retriever -> Analyzer -> Synthesizer -> Evaluator
    with retry logic for failed evaluations.

    Args:
        query: The user's query text.
        llm_client: LLM client for agents.
        storage: Storage repository for entries.
        domains: Available domain modules.

    Returns:
        Dict with response, sources, confidence, and is_partial.
    """
    # Initialize domain selector
    selector = DomainSelector(domains)
    domain_infos = selector.get_domain_infos()

    # Step 1: Route query
    router_agent = RouterAgent(llm_client)
    router_input = RouterInput(raw_input=query, available_domains=domain_infos)
    router_output = await router_agent.classify(router_input)

    # Build active domain context from selected domains
    active_context = selector.build_active_context(router_output.selected_domains)

    # Step 2: Plan retrieval
    planner = PlannerAgent(llm_client)
    planner_input = PlannerInput(query=query, domain_context=active_context)
    planner_output = await planner.plan(planner_input)

    # Step 3: Retrieve entries
    retriever = RetrieverAgent(storage)
    retriever_input = RetrieverInput(
        instructions=planner_output.retrieval_instructions,
        vocabulary=active_context.vocabulary,
        max_entries=100,
    )
    retriever_output = await retriever.retrieve(retriever_input)

    # Collect source entry IDs
    sources: list[str] = [entry.id for entry in retriever_output.entries]

    # Step 4-6: Analyze -> Synthesize -> Evaluate with retry loop
    retry_count = 0
    is_partial = False
    final_response = ""
    confidence = 0.0

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
        analysis = await analyzer.analyze(analyzer_input)

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
        synthesizer_output = await synthesizer.synthesize(synthesizer_input)

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
        evaluation = await evaluator.evaluate(evaluator_input)

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
        )
        planner_output = await planner.plan(planner_input)

        # Re-retrieve with updated instructions
        retriever_input = RetrieverInput(
            instructions=planner_output.retrieval_instructions,
            vocabulary=active_context.vocabulary,
            max_entries=100,
        )
        retriever_output = await retriever.retrieve(retriever_input)

    return {
        "response": final_response,
        "sources": sources,
        "confidence": confidence,
        "is_partial": is_partial,
    }


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
