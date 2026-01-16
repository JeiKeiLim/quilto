"""Pydantic request and response models for API endpoints."""

from pydantic import BaseModel, Field


class InputRequest(BaseModel):
    """Request body for /input endpoint."""

    text: str = Field(..., min_length=1, description="Raw input text")


class InputResponse(BaseModel):
    """Response for /input endpoint."""

    status: str = Field(..., description="Processing status: accepted, error")
    input_type: str = Field(..., description="Classified input type: LOG, QUERY, BOTH, CORRECTION")
    entry_id: str | None = Field(None, description="Entry ID for LOG inputs")
    message: str | None = Field(None, description="Additional message")


class QueryRequest(BaseModel):
    """Request body for /query endpoint."""

    text: str = Field(..., min_length=1, description="Query text")


class QueryResponse(BaseModel):
    """Response for /query endpoint."""

    response: str = Field(..., description="Generated response")
    sources: list[str] = Field(default_factory=list, description="Source entry IDs used")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Response confidence")
    partial: bool = Field(False, description="True if response is partial due to insufficient data")


class ErrorResponse(BaseModel):
    """Error response model."""

    error: str = Field(..., description="Error type")
    detail: str = Field(..., description="Error details")
