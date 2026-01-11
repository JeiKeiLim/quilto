"""Quilto agents module.

This module provides the agent classes for the Quilto framework,
including the RouterAgent for input classification and domain selection,
and the ParserAgent for structured data extraction.
"""

from quilto.agents.models import (
    DomainInfo,
    InputType,
    ParserInput,
    ParserOutput,
    RouterInput,
    RouterOutput,
)
from quilto.agents.parser import ParserAgent
from quilto.agents.router import RouterAgent

__all__ = [
    "DomainInfo",
    "InputType",
    "ParserAgent",
    "ParserInput",
    "ParserOutput",
    "RouterAgent",
    "RouterInput",
    "RouterOutput",
]
