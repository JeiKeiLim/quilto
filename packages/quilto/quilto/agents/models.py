"""Shared agent types for Quilto framework.

This module defines common data models used across all Quilto agents,
including input types, domain information, router, and parser models.
"""

from datetime import date, datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator


class InputType(str, Enum):
    """Classification of user input type.

    Attributes:
        LOG: Declarative statements recording activities, events, or observations.
        QUERY: Questions seeking information, insights, or recommendations.
        BOTH: Input that logs something AND asks a question.
        CORRECTION: User fixing previously recorded information.
    """

    LOG = "LOG"
    QUERY = "QUERY"
    BOTH = "BOTH"
    CORRECTION = "CORRECTION"


class DomainInfo(BaseModel):
    """Domain information for Router domain selection.

    Attributes:
        name: The unique identifier for the domain.
        description: Human-readable description of what the domain handles.
    """

    model_config = ConfigDict(strict=True)

    name: str
    description: str


class RouterInput(BaseModel):
    """Input to Router agent.

    Attributes:
        raw_input: The raw user input text to classify.
        session_context: Optional recent conversation for context.
        available_domains: List of domains available for selection.
    """

    model_config = ConfigDict(strict=True)

    raw_input: str
    session_context: str | None = None
    available_domains: list[DomainInfo]


class RouterOutput(BaseModel):
    """Output from Router agent.

    Attributes:
        input_type: The classified input type (LOG, QUERY, BOTH, CORRECTION).
        confidence: Confidence score for the classification (0.0 to 1.0).
        selected_domains: List of domain names to activate for this input.
        domain_selection_reasoning: Explanation of why domains were selected.
        log_portion: The logging portion of input (required if input_type is BOTH).
        query_portion: The query portion of input (required if input_type is BOTH).
        correction_target: What is being corrected (required if input_type is CORRECTION).
        reasoning: Brief explanation of the classification decision.
    """

    model_config = ConfigDict(strict=True)

    input_type: InputType
    confidence: float = Field(ge=0.0, le=1.0)

    selected_domains: list[str]
    domain_selection_reasoning: str

    log_portion: str | None = None
    query_portion: str | None = None

    correction_target: str | None = None

    reasoning: str

    @model_validator(mode="after")
    def validate_type_specific_fields(self) -> "RouterOutput":
        """Validate that BOTH has portions and CORRECTION has target.

        Returns:
            The validated RouterOutput instance.

        Raises:
            ValueError: If BOTH is missing portions or CORRECTION is missing target.
        """
        if self.input_type == InputType.BOTH and (not self.log_portion or not self.query_portion):
            raise ValueError("BOTH input_type requires both log_portion and query_portion")
        if self.input_type == InputType.CORRECTION and not self.correction_target:
            raise ValueError("CORRECTION input_type requires correction_target")
        return self


class ParserInput(BaseModel):
    """Input to Parser agent.

    Attributes:
        raw_input: The raw user input text to parse.
        timestamp: Timestamp when the entry was created.
        domain_schemas: Map of domain names to their Pydantic schema classes.
        vocabulary: Term normalization mapping for extraction.
        global_context: Optional global context for inference.
        recent_entries: Recent entries for correction mode target identification.
        correction_mode: Whether this is a correction to existing entry.
        correction_target: Natural language hint about what's being corrected.
    """

    model_config = ConfigDict(strict=True, arbitrary_types_allowed=True)

    raw_input: str
    timestamp: datetime

    domain_schemas: dict[str, type[BaseModel]]
    vocabulary: dict[str, str]

    global_context: str | None = None
    recent_entries: list[Any] = []

    correction_mode: bool = False
    correction_target: str | None = None


class ParserOutput(BaseModel):
    """Output from Parser agent.

    Attributes:
        date: Date of the entry.
        timestamp: Full timestamp of the entry.
        tags: Extracted tags from content.
        domain_data: Domain-specific parsed data, one entry per domain.
        raw_content: Original raw input (preserved exactly).
        confidence: Overall extraction confidence (0.0 to 1.0).
        extraction_notes: Notes about ambiguities or assumptions made.
        uncertain_fields: List of field names with uncertain extraction.
        is_correction: Whether this is a correction output.
        target_entry_id: ID of entry being corrected (if correction).
        correction_delta: Fields that changed (if correction).
    """

    model_config = ConfigDict(strict=True)

    date: date
    timestamp: datetime
    tags: list[str] = []

    domain_data: dict[str, Any]

    raw_content: str

    confidence: float = Field(ge=0.0, le=1.0)
    extraction_notes: list[str] = []
    uncertain_fields: list[str] = []

    is_correction: bool = False
    target_entry_id: str | None = None
    correction_delta: dict[str, Any] | None = None

    @model_validator(mode="after")
    def validate_required_fields(self) -> "ParserOutput":
        """Validate that raw_content is not empty.

        Returns:
            The validated ParserOutput instance.

        Raises:
            ValueError: If raw_content is empty or whitespace-only.
        """
        if not self.raw_content or not self.raw_content.strip():
            raise ValueError("raw_content cannot be empty")
        return self
