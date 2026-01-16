"""LLM client with provider abstraction for Quilto framework.

This module provides a unified client for making LLM calls across
different providers (Ollama, Anthropic, OpenAI, Azure, OpenRouter)
using litellm as the underlying API.
"""

import asyncio
import logging
import random
from typing import Any

import litellm
from pydantic import BaseModel

from quilto.llm.config import (
    AgentConfig,
    LLMConfig,
    ModelResolution,
    ProviderName,
)
from quilto.llm.errors import ErrorType, PartialResult, classify_error

logger = logging.getLogger(__name__)


class LLMClient:
    """Unified LLM client with provider abstraction.

    Resolves the correct provider and model based on agent tier
    configuration, handles litellm model name prefixing, and
    provides fallback support on errors.

    Attributes:
        config: The LLM configuration.

    Example:
        >>> from quilto.llm import LLMClient, load_llm_config
        >>> config = load_llm_config(Path("config.yaml"))
        >>> client = LLMClient(config)
        >>> response = await client.complete(
        ...     agent="analyzer",
        ...     messages=[{"role": "user", "content": "Hello"}],
        ... )
    """

    def __init__(self, config: LLMConfig) -> None:
        """Initialize the LLM client.

        Args:
            config: The LLM configuration specifying providers,
                tiers, and agent settings.
        """
        self.config = config

    def _get_litellm_model(self, provider: ProviderName, model: str) -> str:
        """Get the litellm-formatted model name.

        LiteLLM uses prefixes to identify providers:
        - ollama: ollama/<model>
        - anthropic: <model> (no prefix)
        - openai: <model> (no prefix)
        - azure: azure/<deployment>
        - openrouter: openrouter/<provider>/<model>

        Args:
            provider: The provider name.
            model: The raw model name.

        Returns:
            The model name formatted for litellm.
        """
        if provider == "ollama":
            return f"ollama/{model}"
        if provider == "azure":
            return f"azure/{model}"
        if provider == "openrouter":
            return f"openrouter/{model}"
        # anthropic and openai use model name directly
        return model

    def resolve_model(self, agent: str, force_cloud: bool = False) -> ModelResolution:
        """Resolve provider and model for an agent.

        Determines which provider and model to use based on the agent's
        tier configuration, optional provider override, and force_cloud flag.

        Args:
            agent: The agent name (e.g., "analyzer", "router").
            force_cloud: If True, use fallback_provider instead of default.

        Returns:
            ModelResolution with provider, model, litellm_model, api_base, api_key.

        Raises:
            ValueError: If provider has no model configured for the agent's tier.
        """
        agent_config = self.config.agents.get(agent, AgentConfig())

        # Determine provider
        if agent_config.provider:
            provider = agent_config.provider
        elif force_cloud and self.config.fallback_provider:
            provider = self.config.fallback_provider
        else:
            provider = self.config.default_provider

        # Get model for tier
        tier_models = self.config.tiers.get(agent_config.tier)
        if tier_models is None:
            raise ValueError(
                f"Tier '{agent_config.tier}' not configured. Available tiers: {list(self.config.tiers.keys())}"
            )

        model = getattr(tier_models, provider, None)
        if model is None:
            configured_providers = [
                p
                for p in ["ollama", "anthropic", "openai", "azure", "openrouter"]
                if getattr(tier_models, p, None) is not None
            ]
            raise ValueError(
                f"No model configured for provider '{provider}' at tier '{agent_config.tier}'. "
                f"Configured providers for this tier: {configured_providers}"
            )

        # Get provider config
        provider_config = self.config.providers.get(provider)
        api_base = provider_config.api_base if provider_config else None
        api_key = provider_config.api_key if provider_config else None

        # Format for litellm
        litellm_model = self._get_litellm_model(provider, model)

        return ModelResolution(
            provider=provider,
            model=model,
            litellm_model=litellm_model,
            api_base=api_base,
            api_key=api_key,
        )

    async def complete(
        self,
        agent: str,
        messages: list[dict[str, Any]],
        force_cloud: bool = False,
        **kwargs: Any,
    ) -> str:
        """Complete a chat request via litellm.

        Resolves the model for the agent and makes an async completion
        request using litellm.

        Args:
            agent: The agent name.
            messages: Chat messages in OpenAI format.
            force_cloud: If True, use fallback_provider.
            **kwargs: Additional arguments passed to litellm.acompletion.

        Returns:
            The response content as a string.
        """
        resolution = self.resolve_model(agent, force_cloud=force_cloud)

        # Build kwargs for litellm
        completion_kwargs: dict[str, Any] = {
            "model": resolution.litellm_model,
            "messages": messages,
            **kwargs,
        }

        if resolution.api_base:
            completion_kwargs["api_base"] = resolution.api_base
        if resolution.api_key:
            completion_kwargs["api_key"] = resolution.api_key

        response = await litellm.acompletion(**completion_kwargs)  # type: ignore[reportUnknownMemberType]
        return response.choices[0].message.content or ""  # type: ignore[reportUnknownMemberType,reportAttributeAccessIssue]

    async def complete_structured(
        self,
        agent: str,
        messages: list[dict[str, Any]],
        response_model: type[BaseModel],
        force_cloud: bool = False,
        **kwargs: Any,
    ) -> BaseModel:
        """Complete with Pydantic validation.

        Makes a completion request with JSON response format and
        validates the response against the provided Pydantic model.

        Args:
            agent: The agent name.
            messages: Chat messages in OpenAI format.
            response_model: Pydantic model class for response validation.
            force_cloud: If True, use fallback_provider.
            **kwargs: Additional arguments passed to complete.

        Returns:
            Validated Pydantic model instance.

        Raises:
            ValueError: If LLM returns invalid JSON or response doesn't
                match the expected schema.
        """
        response = await self.complete(
            agent=agent,
            messages=messages,
            force_cloud=force_cloud,
            response_format={"type": "json_object"},
            **kwargs,
        )
        try:
            return response_model.model_validate_json(response)
        except Exception as e:
            logger.error(
                "Failed to parse structured response for agent '%s'. Expected schema: %s. Raw response: %s",
                agent,
                response_model.__name__,
                response[:500] if len(response) > 500 else response,
            )
            raise ValueError(f"LLM response failed schema validation for {response_model.__name__}: {e}") from e

    async def complete_with_fallback(
        self,
        agent: str,
        messages: list[dict[str, Any]],
        **kwargs: Any,
    ) -> str:
        """Try default provider, fall back on failure.

        Attempts completion with the default provider. On any error,
        retries with the fallback_provider if configured.

        Note: This method is preserved for backward compatibility.
        Consider using `complete_with_cascade()` for full error handling
        with retry, fallback, and graceful degradation support.

        Args:
            agent: The agent name.
            messages: Chat messages in OpenAI format.
            **kwargs: Additional arguments passed to complete.

        Returns:
            The response content as a string.

        Raises:
            Exception: If both providers fail or no fallback configured.
        """
        result = await self.complete_with_cascade(agent, messages, allow_degradation=False, **kwargs)
        # Since allow_degradation=False, result is always str (raises on failure)
        return result  # type: ignore[return-value]

    async def _retry_with_backoff(
        self,
        agent: str,
        messages: list[dict[str, Any]],
        force_cloud: bool = False,
        **kwargs: Any,
    ) -> tuple[str | None, Exception | None, int]:
        """Retry completion with exponential backoff.

        Attempts the completion up to max_retries times, applying
        exponential backoff with jitter between attempts. Stops early
        if a permanent error is encountered.

        Args:
            agent: The agent name.
            messages: Chat messages.
            force_cloud: If True, use fallback provider.
            **kwargs: Additional litellm arguments.

        Returns:
            Tuple of (result, last_exception, actual_attempts).
            result is None if all retries failed.
            actual_attempts is the number of attempts made (may be less than
            max_retries if a permanent error caused early termination).
        """
        last_exception: Exception | None = None
        actual_attempts = 0

        for attempt in range(self.config.max_retries):
            actual_attempts = attempt + 1
            try:
                result = await self.complete(agent, messages, force_cloud=force_cloud, **kwargs)
                return result, None, actual_attempts
            except Exception as e:
                last_exception = e
                error_type = classify_error(e)

                logger.warning(
                    "LLM call failed (attempt %d/%d, type=%s): %s",
                    actual_attempts,
                    self.config.max_retries,
                    error_type.value,
                    str(e),
                )

                # Don't retry permanent errors
                if error_type == ErrorType.PERMANENT:
                    break

                # Apply backoff before next retry (except on last attempt)
                if attempt < self.config.max_retries - 1:
                    delay = self.config.base_retry_delay * (2**attempt)
                    delay += random.uniform(0, 0.5)  # Jitter
                    await asyncio.sleep(delay)

        return None, last_exception, actual_attempts

    async def complete_with_cascade(
        self,
        agent: str,
        messages: list[dict[str, Any]],
        allow_degradation: bool = True,
        **kwargs: Any,
    ) -> str | PartialResult:
        """Complete with full error cascade: retry → fallback → degrade.

        Attempts the completion with the primary provider, retrying on
        transient errors. If all retries fail and a fallback provider
        is configured, tries the fallback with its own retry cycle.
        If all attempts fail and allow_degradation is True, returns
        a PartialResult instead of raising.

        Args:
            agent: The agent name.
            messages: Chat messages.
            allow_degradation: If True, return PartialResult on total failure.
            **kwargs: Additional litellm arguments.

        Returns:
            Response string on success, PartialResult on degradation.

        Raises:
            Exception: If allow_degradation is False and all providers fail.
        """
        providers_attempted: list[str] = []
        total_retries = 0
        last_exception: Exception | None = None

        # Try primary provider
        resolution = self.resolve_model(agent, force_cloud=False)
        providers_attempted.append(resolution.provider)

        result, exception, retries = await self._retry_with_backoff(agent, messages, force_cloud=False, **kwargs)
        total_retries += retries

        if result is not None:
            return result
        last_exception = exception

        # Try fallback provider if configured
        if self.config.fallback_provider:
            logger.warning(
                "Primary provider %s failed after %d retries, trying fallback %s",
                resolution.provider,
                retries,
                self.config.fallback_provider,
            )

            providers_attempted.append(self.config.fallback_provider)

            result, exception, retries = await self._retry_with_backoff(agent, messages, force_cloud=True, **kwargs)
            total_retries += retries

            if result is not None:
                return result
            last_exception = exception

        # All providers failed
        error_msg = f"All LLM providers failed. Last error: {last_exception}"

        if allow_degradation and self.config.enable_graceful_degradation:
            logger.error(
                "LLM cascade failed, returning partial result. Providers: %s, Total retries: %d",
                providers_attempted,
                total_retries,
            )
            return PartialResult(
                success=False,
                content=None,
                error_message=error_msg,
                error_type="degraded",
                providers_attempted=providers_attempted,
                retry_count=total_retries,
            )

        logger.error("LLM cascade failed, raising exception. Providers: %s", providers_attempted)
        raise last_exception or Exception(error_msg)

    async def complete_structured_with_cascade(
        self,
        agent: str,
        messages: list[dict[str, Any]],
        response_model: type[BaseModel],
        allow_degradation: bool = True,
        **kwargs: Any,
    ) -> BaseModel | PartialResult:
        """Complete structured response with full error cascade.

        Attempts structured completion with retry and fallback support.
        Schema validation errors (JSONDecodeError, ValidationError) are
        treated as permanent errors and immediately trigger fallback.

        Args:
            agent: The agent name.
            messages: Chat messages.
            response_model: Pydantic model class for response validation.
            allow_degradation: If True, return PartialResult on total failure.
            **kwargs: Additional litellm arguments.

        Returns:
            Validated Pydantic model on success, PartialResult on degradation.

        Raises:
            Exception: If allow_degradation is False and all providers fail.
        """
        providers_attempted: list[str] = []
        total_retries = 0
        last_exception: Exception | None = None

        # Try primary provider
        resolution = self.resolve_model(agent, force_cloud=False)
        providers_attempted.append(resolution.provider)

        result, exception, retries = await self._retry_structured_with_backoff(
            agent, messages, response_model, force_cloud=False, **kwargs
        )
        total_retries += retries

        if result is not None:
            return result
        last_exception = exception

        # Try fallback provider if configured
        if self.config.fallback_provider:
            logger.warning(
                "Primary provider %s failed after %d retries for structured response, trying fallback %s",
                resolution.provider,
                retries,
                self.config.fallback_provider,
            )

            providers_attempted.append(self.config.fallback_provider)

            result, exception, retries = await self._retry_structured_with_backoff(
                agent, messages, response_model, force_cloud=True, **kwargs
            )
            total_retries += retries

            if result is not None:
                return result
            last_exception = exception

        # All providers failed
        error_msg = f"All LLM providers failed for {response_model.__name__}. Last error: {last_exception}"

        if allow_degradation and self.config.enable_graceful_degradation:
            logger.error(
                "LLM structured cascade failed, returning partial result. Schema: %s, Providers: %s, Total retries: %d",
                response_model.__name__,
                providers_attempted,
                total_retries,
            )
            return PartialResult(
                success=False,
                content=None,
                error_message=error_msg,
                error_type="degraded",
                providers_attempted=providers_attempted,
                retry_count=total_retries,
            )

        logger.error(
            "LLM structured cascade failed, raising exception. Schema: %s, Providers: %s",
            response_model.__name__,
            providers_attempted,
        )
        raise last_exception or Exception(error_msg)

    async def _retry_structured_with_backoff(
        self,
        agent: str,
        messages: list[dict[str, Any]],
        response_model: type[BaseModel],
        force_cloud: bool = False,
        **kwargs: Any,
    ) -> tuple[BaseModel | None, Exception | None, int]:
        """Retry structured completion with exponential backoff.

        Similar to _retry_with_backoff but for structured responses.
        Schema errors are treated as permanent (no retry).

        Args:
            agent: The agent name.
            messages: Chat messages.
            response_model: Pydantic model class for response validation.
            force_cloud: If True, use fallback provider.
            **kwargs: Additional litellm arguments.

        Returns:
            Tuple of (result, last_exception, actual_attempts).
            result is None if all retries failed.
        """
        last_exception: Exception | None = None
        actual_attempts = 0

        for attempt in range(self.config.max_retries):
            actual_attempts = attempt + 1
            try:
                result = await self.complete_structured(
                    agent, messages, response_model, force_cloud=force_cloud, **kwargs
                )
                return result, None, actual_attempts
            except Exception as e:
                last_exception = e
                error_type = classify_error(e)

                logger.warning(
                    "LLM structured call failed (attempt %d/%d, type=%s, schema=%s): %s",
                    actual_attempts,
                    self.config.max_retries,
                    error_type.value,
                    response_model.__name__,
                    str(e),
                )

                # Don't retry permanent errors (including schema validation)
                if error_type == ErrorType.PERMANENT:
                    break

                # Apply backoff before next retry (except on last attempt)
                if attempt < self.config.max_retries - 1:
                    delay = self.config.base_retry_delay * (2**attempt)
                    delay += random.uniform(0, 0.5)  # Jitter
                    await asyncio.sleep(delay)

        return None, last_exception, actual_attempts
