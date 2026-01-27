"""Public API models for Quilto framework.

This module defines the Pydantic models that form the public contract
for interacting with Quilto. These are distinct from internal agent models
in quilto/agents/models.py.
"""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class ClarificationQuestion(BaseModel):
    """A question to ask the user for clarification.

    This is the public API version for UI rendering. It contains only the
    question text and optional predefined answer choices. The internal
    agent version (quilto/agents/models.py) has additional fields for
    priority and gap tracking.

    Attributes:
        question: The clarification question text.
        options: Optional predefined answer choices. None means free-form input.
    """

    model_config = ConfigDict(strict=True)

    question: str = Field(min_length=1)
    options: list[str] | None = None


class AgentTrace(BaseModel):
    """Trace of a single agent execution for debugging.

    Captures timing and input/output summaries for observability.

    Attributes:
        agent_name: Name of the agent (e.g., "router", "planner").
        input_summary: Summary of input provided to agent.
        output_summary: Summary of agent output.
        elapsed_ms: Execution time in milliseconds.
        timestamp: When the agent started execution.
    """

    model_config = ConfigDict(strict=True)

    agent_name: str = Field(min_length=1)
    input_summary: str = Field(min_length=1)
    output_summary: str = Field(min_length=1)
    elapsed_ms: float = Field(ge=0)
    timestamp: datetime


class ProcessDebug(BaseModel):
    """Debug information for a processing run.

    Aggregates all agent traces for a single processing request.

    Attributes:
        traces: List of agent execution traces in order.
        total_elapsed_ms: Total processing time in milliseconds.
        retry_count: Number of retries attempted.
    """

    model_config = ConfigDict(strict=True)

    traces: list[AgentTrace] = Field(default_factory=lambda: [])
    total_elapsed_ms: float = Field(default=0, ge=0)
    retry_count: int = Field(ge=0, default=0)


class ProcessResult(BaseModel):
    """Result of processing user input through Quilto.

    This is the primary return type for session.process().

    For QUERY inputs:
        - response, confidence, source_entry_ids are populated
    For LOG inputs:
        - parsed_data is populated
    For BOTH inputs:
        - Both response and parsed_data may be populated
    When clarification needed:
        - clarification_questions is populated

    Attributes:
        response: Generated response text (for QUERY).
        confidence: Confidence score 0.0-1.0 (for QUERY).
        source_entry_ids: IDs of entries used to generate response.
        parsed_data: Structured data extracted (for LOG).
        input_type: Classification of the input.
        selected_domains: Domains that were activated.
        clarification_questions: Questions needing user answers.
        debug: Debug traces if debug mode enabled.
    """

    model_config = ConfigDict(strict=True)

    # Core response (for QUERY)
    response: str | None = None
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    source_entry_ids: list[str] = Field(default_factory=list)

    # For LOG inputs
    parsed_data: dict[str, Any] | None = None

    # Classification
    input_type: Literal["log", "query", "both", "correction"]
    selected_domains: list[str] = Field(default_factory=list)

    # Clarification (if needed)
    clarification_questions: list[ClarificationQuestion] | None = None

    # Debug (if enabled)
    debug: ProcessDebug | None = None
