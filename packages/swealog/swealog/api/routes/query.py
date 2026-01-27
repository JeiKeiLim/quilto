"""POST /query endpoint for processing user queries."""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from quilto import Quilto

from swealog.api.dependencies import create_quilto
from swealog.api.models import QueryRequest, QueryResponse

logger = logging.getLogger(__name__)

router = APIRouter()


def get_quilto_dependency() -> Quilto:
    """FastAPI dependency that creates a Quilto instance per request.

    Returns:
        Configured Quilto instance for query processing.
    """
    return create_quilto()


@router.post("/query", response_model=QueryResponse)
async def process_query(
    request: QueryRequest,
    quilto: Annotated[Quilto, Depends(get_quilto_dependency)],
) -> QueryResponse:
    """Process a user query through the Quilto orchestration pipeline.

    Routes query through Quilto's LangGraph orchestration with automatic
    Observer integration and retry logic.

    Args:
        request: Query request with text field.
        quilto: Quilto instance from dependency injection.

    Returns:
        QueryResponse with response, sources, confidence, and partial flag.

    Raises:
        HTTPException: If query processing fails.
    """
    try:
        # Create session and process query
        session = quilto.create_session()
        result = await session.process(request.text, mode="query")

        # Handle clarification questions - return empty response with message
        if result.clarification_questions:
            questions_text = "; ".join(q.question for q in result.clarification_questions)
            return QueryResponse(
                response=f"Clarification needed: {questions_text}",
                sources=[],
                confidence=0.0,
                partial=False,
            )

        # Determine is_partial from retry_count (ProcessResult lacks is_partial field)
        is_partial = result.debug is not None and result.debug.retry_count >= 2

        # Map ProcessResult to QueryResponse
        return QueryResponse(
            response=result.response or "",
            sources=result.source_entry_ids,
            confidence=result.confidence or 0.0,
            partial=is_partial,
        )

    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=f"Session error: {e}") from e
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        logger.exception("Query processing failed: %s", e)
        raise HTTPException(status_code=500, detail=f"Internal error: {type(e).__name__}") from e
