"""Shared agent types for Quilto framework.

This module defines common data models used across all Quilto agents,
including input types, domain information, and router-specific models.
"""

from enum import Enum

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
