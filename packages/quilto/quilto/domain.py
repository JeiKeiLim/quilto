"""Domain module interface for Quilto framework.

This module defines the DomainModule base class that applications use to
configure domain-specific behavior for the agent framework.
"""

from typing import Any, Self

from pydantic import BaseModel, ConfigDict, field_validator, model_validator


class DomainModule(BaseModel):
    """Domain configuration provided to the framework.

    Applications register one or more domain modules to customize
    how the framework parses, analyzes, and evaluates domain-specific content.

    Attributes:
        name: Domain identifier. Defaults to class name if not provided.
        description: Used by Router to auto-select relevant domain(s) for a
            given input. Write a clear description of what this domain covers
            so agents can match it.
        log_schema: Pydantic model defining structured output for parsed entries.
        vocabulary: Term normalization mapping. E.g., {"bench": "bench press"}.
        expertise: Domain knowledge injected into agent prompts (Analyzer, Planner).
            Can include retrieval guidance, pattern recognition hints, domain principles.
        response_evaluation_rules: Rules for evaluating Synthesizer's response
            before returning to user. E.g., "Never recommend exercises for injured
            body parts".
        context_management_guidance: Instructions for Observer agent on what patterns
            to track over time. E.g., "Track personal records, workout frequency,
            recovery patterns".
        clarification_patterns: Example questions for clarification, grouped by gap
            type. E.g., {"SUBJECTIVE": ["How are you feeling?"], "CLARIFICATION":
            ["Which exercise?"]}.

    Example:
        >>> from pydantic import BaseModel
        >>> class WorkoutEntry(BaseModel):
        ...     exercise: str
        ...     sets: int | None = None
        >>> class FitnessDomain(DomainModule):
        ...     pass
        >>> domain = FitnessDomain(
        ...     description="General fitness workouts",
        ...     log_schema=WorkoutEntry,
        ...     vocabulary={"bench": "bench press"},
        ... )
        >>> domain.name
        'FitnessDomain'
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    name: str = ""
    """Domain identifier. Defaults to class name if not provided."""

    description: str
    """Used by Router to auto-select relevant domain(s) for a given input."""

    log_schema: type[BaseModel]
    """Pydantic model defining structured output for parsed entries."""

    vocabulary: dict[str, str]
    """Term normalization mapping. E.g., {"bench": "bench press"}."""

    expertise: str = ""
    """Domain knowledge injected into agent prompts (Analyzer, Planner)."""

    response_evaluation_rules: list[str] = []
    """Rules for evaluating Synthesizer's response before returning to user."""

    context_management_guidance: str = ""
    """Instructions for Observer agent on what patterns to track over time."""

    clarification_patterns: dict[str, list[str]] = {}
    """Example questions for clarification, grouped by gap type.

    Maps gap type names (SUBJECTIVE, CLARIFICATION) to example questions
    that guide the Clarifier agent in asking domain-appropriate questions.

    Example:
        clarification_patterns = {
            "SUBJECTIVE": ["How are you feeling today?"],
            "CLARIFICATION": ["Which exercise are you asking about?"],
        }
    """

    @field_validator("log_schema", mode="before")
    @classmethod
    def validate_log_schema(cls, v: Any) -> type[BaseModel]:
        """Validate that log_schema is a BaseModel subclass.

        Args:
            v: The value to validate.

        Returns:
            The validated value.

        Raises:
            ValueError: If v is not a class or not a BaseModel subclass.
        """
        if not isinstance(v, type):
            raise ValueError("log_schema must be a class, not an instance")
        if not issubclass(v, BaseModel):
            raise ValueError("log_schema must be a subclass of BaseModel")
        return v

    @model_validator(mode="after")
    def set_default_name(self) -> Self:
        """Set name to class name if not provided.

        Returns:
            Self with name defaulted to class name if empty.
        """
        if not self.name:
            self.name = self.__class__.__name__
        return self
