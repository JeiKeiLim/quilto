"""Quilto agents module.

This module provides the agent classes for the Quilto framework,
including the RouterAgent for input classification and domain selection.
"""

from quilto.agents.models import DomainInfo, InputType, RouterInput, RouterOutput
from quilto.agents.router import RouterAgent

__all__ = [
    "DomainInfo",
    "InputType",
    "RouterAgent",
    "RouterInput",
    "RouterOutput",
]
