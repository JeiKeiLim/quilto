"""LLM client abstraction for Quilto framework.

This module provides a unified interface for making LLM calls
across different providers (Ollama, Anthropic, OpenAI, Azure, OpenRouter).
"""

from quilto.llm.client import LLMClient
from quilto.llm.config import (
    AgentConfig,
    LLMConfig,
    ModelResolution,
    ProviderConfig,
    TierModels,
)
from quilto.llm.errors import ErrorType, PartialResult, classify_error
from quilto.llm.loader import load_llm_config, load_llm_config_from_dict

__all__ = [
    "AgentConfig",
    "ErrorType",
    "LLMClient",
    "LLMConfig",
    "ModelResolution",
    "PartialResult",
    "ProviderConfig",
    "TierModels",
    "classify_error",
    "load_llm_config",
    "load_llm_config_from_dict",
]
