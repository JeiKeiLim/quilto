"""Pairwise LLM-as-Judge evaluation with position swap.

This module implements pairwise comparison between Quilto and Claude responses
using an LLM judge with position swap to reduce bias.

Usage:
    evaluator = PairwiseEvaluator(judge_model="gpt-4o-mini")
    result = await evaluator.evaluate_with_swap(test_case, quilto_response, claude_response)
"""

import asyncio
import json
import logging
import random
import re
from pathlib import Path
from typing import Any

import litellm
import yaml

from tests.eval.generate_baseline import CORPUS_PATH
from tests.eval.schema import (
    CriterionScore,
    JudgeResult,
    PairwiseResult,
    Rubric,
    TestCase,
)

logger = logging.getLogger(__name__)

# Constants
PROJECT_ROOT = Path(__file__).parent.parent.parent
RUBRIC_PATH = PROJECT_ROOT / "tests" / "eval" / "rubric.yaml"

MAX_JUDGE_RETRIES = 2

# Model pricing per 1M tokens (as of 2026-01)
MODEL_PRICING: dict[str, dict[str, float]] = {
    "gpt-4o-mini": {"input": 0.15, "output": 0.60},
    "gpt-4o": {"input": 2.50, "output": 10.00},
    "openrouter/anthropic/claude-sonnet-4": {"input": 3.00, "output": 15.00},
    "openrouter/openai/gpt-4o-mini": {"input": 0.15, "output": 0.60},
    "openrouter/openai/gpt-4o": {"input": 2.50, "output": 10.00},
}


def _load_rubric() -> Rubric:
    """Load and validate the evaluation rubric.

    Returns:
        Validated Rubric instance.

    Raises:
        FileNotFoundError: If rubric.yaml doesn't exist.
        ValueError: If rubric fails validation.
    """
    if not RUBRIC_PATH.exists():
        raise FileNotFoundError(f"Rubric not found: {RUBRIC_PATH}")

    with open(RUBRIC_PATH) as f:
        data = yaml.safe_load(f)

    return Rubric.model_validate(data)


def _build_judge_system_prompt(rubric: Rubric) -> str:
    """Build the system prompt for the judge LLM.

    Args:
        rubric: The evaluation rubric.

    Returns:
        System prompt string.
    """
    criteria_text = []
    for name, criterion in rubric.criteria.items():
        criteria_text.append(
            f"""### {name.upper()} (weight: {criterion.weight})
{criterion.description}

**Scoring Guidance:**
- Good (4-5): {criterion.scoring.good.strip()}
- Medium (3): {criterion.scoring.medium.strip()}
- Poor (1-2): {criterion.scoring.poor.strip()}
"""
        )

    return f"""You are an expert evaluator comparing two AI assistant responses to a fitness query.
Your task is to determine which response is better based on specific criteria.

## Evaluation Criteria

{chr(10).join(criteria_text)}

## Instructions

1. Read the query and both responses carefully
2. For EACH criterion, score both responses from 1-5 with reasoning
3. Calculate weighted aggregate scores for each response
4. Determine the overall winner based on aggregate scores
5. If scores are within 0.3 points, call it a Tie

## Response Format

You MUST respond with valid JSON in this exact format:
```json
{{
    "reasoning": "Your chain-of-thought reasoning comparing the responses",
    "criterion_scores_a": [
        {{"criterion": "accuracy", "score": 4, "reasoning": "Response A correctly..."}},
        {{"criterion": "completeness", "score": 3, "reasoning": "..."}}
    ],
    "criterion_scores_b": [
        {{"criterion": "accuracy", "score": 3, "reasoning": "Response B incorrectly..."}},
        {{"criterion": "completeness", "score": 4, "reasoning": "..."}}
    ],
    "aggregate_score_a": 3.7,
    "aggregate_score_b": 3.5,
    "winner": "A"
}}
```

The winner field must be exactly "A", "B", or "Tie".
"""


def _build_judge_user_prompt(
    test_case: TestCase,
    response_a: str,
    response_b: str,
    rubric: Rubric,
) -> str:
    """Build the user prompt for judge evaluation.

    Args:
        test_case: The test case being evaluated.
        response_a: First response (anonymized).
        response_b: Second response (anonymized).
        rubric: The evaluation rubric.

    Returns:
        User prompt string.
    """
    # Get applicable criteria for this category
    profile = rubric.criterion_profiles.get(test_case.category)
    criteria_to_evaluate = profile.required if profile else list(rubric.criteria.keys())
    if profile and profile.optional:
        criteria_to_evaluate.extend(profile.optional)

    hints_text = ""
    if test_case.evaluation_hints:
        hints_text = f"""
## Evaluation Hints
- Should mention: {", ".join(test_case.evaluation_hints.should_mention)}
- Should NOT: {", ".join(test_case.evaluation_hints.should_not)}
"""

    return f"""## Query
{test_case.query}

## Context Category
{test_case.category}

## Criteria to Evaluate
{", ".join(criteria_to_evaluate)}
{hints_text}
## Response A
{response_a}

## Response B
{response_b}

Please evaluate both responses and provide your judgment in JSON format.
Think step-by-step before scoring.
"""


def _parse_judge_response(raw: str) -> dict[str, Any] | None:
    """Parse JSON from judge response, handling common issues.

    Args:
        raw: Raw response from judge LLM.

    Returns:
        Parsed JSON dict or None if parsing fails.
    """
    # Try direct JSON parse
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass

    # Try extracting JSON from markdown code block
    json_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", raw)
    if json_match:
        try:
            return json.loads(json_match.group(1))
        except json.JSONDecodeError:
            pass

    # Try finding JSON object in response
    brace_match = re.search(r"\{[\s\S]*\}", raw)
    if brace_match:
        try:
            return json.loads(brace_match.group(0))
        except json.JSONDecodeError:
            pass

    return None


def _calculate_weighted_score(scores: list[CriterionScore], rubric: Rubric) -> float:
    """Calculate weighted aggregate score from criterion scores.

    Args:
        scores: List of CriterionScore objects.
        rubric: Rubric with weights.

    Returns:
        Weighted aggregate score.
    """
    total_weight = 0.0
    weighted_sum = 0.0

    for score in scores:
        weight = rubric.criteria.get(score.criterion)
        if weight:
            weighted_sum += score.score * weight.weight
            total_weight += weight.weight

    if total_weight == 0:
        return 0.0

    return weighted_sum / total_weight


class PairwiseEvaluator:
    """Orchestrates pairwise LLM-as-judge evaluations with position swap."""

    def __init__(
        self,
        judge_model: str = "gpt-4o-mini",
        max_concurrent: int = 2,
        temperature: float = 0.0,
        max_tokens: int = 2000,
    ) -> None:
        """Initialize the evaluator.

        Args:
            judge_model: LiteLLM model identifier for the judge.
            max_concurrent: Maximum concurrent judge calls.
            temperature: Judge temperature (0 for deterministic).
            max_tokens: Max tokens for judge response.
        """
        self.judge_model = judge_model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self._semaphore = asyncio.Semaphore(max_concurrent)
        self._rubric = _load_rubric()

        # Token tracking for cost estimation
        self.total_input_tokens = 0
        self.total_output_tokens = 0

    async def evaluate_pair(
        self,
        test_case: TestCase,
        response_a: str,
        response_b: str,
    ) -> JudgeResult | None:
        """Evaluate a single pair of responses (A vs B).

        Args:
            test_case: The test case being evaluated.
            response_a: First response (will be presented as "Response A").
            response_b: Second response (will be presented as "Response B").

        Returns:
            JudgeResult or None if evaluation fails after retries.
        """
        system_prompt = _build_judge_system_prompt(self._rubric)
        user_prompt = _build_judge_user_prompt(test_case, response_a, response_b, self._rubric)

        for attempt in range(MAX_JUDGE_RETRIES + 1):
            try:
                async with self._semaphore:
                    response = await litellm.acompletion(
                        model=self.judge_model,
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt},
                        ],
                        temperature=self.temperature,
                        max_tokens=self.max_tokens,
                    )

                raw_output = response.choices[0].message.content or ""

                # Track token usage for cost estimation
                if hasattr(response, "usage") and response.usage:
                    self.total_input_tokens += getattr(response.usage, "prompt_tokens", 0)
                    self.total_output_tokens += getattr(response.usage, "completion_tokens", 0)

                parsed = _parse_judge_response(raw_output)

                if parsed is None:
                    logger.warning("Failed to parse judge response (attempt %d)", attempt + 1)
                    continue

                # Validate and construct JudgeResult
                criterion_scores_a = [CriterionScore.model_validate(s) for s in parsed.get("criterion_scores_a", [])]
                criterion_scores_b = [CriterionScore.model_validate(s) for s in parsed.get("criterion_scores_b", [])]

                # Recalculate aggregates for consistency
                aggregate_a = _calculate_weighted_score(criterion_scores_a, self._rubric)
                aggregate_b = _calculate_weighted_score(criterion_scores_b, self._rubric)

                # Determine winner from aggregates
                diff = aggregate_a - aggregate_b
                if diff > 0.3:
                    winner = "A"
                elif diff < -0.3:
                    winner = "B"
                else:
                    winner = "Tie"

                return JudgeResult(
                    winner=winner,
                    criterion_scores_a=criterion_scores_a,
                    criterion_scores_b=criterion_scores_b,
                    aggregate_score_a=aggregate_a,
                    aggregate_score_b=aggregate_b,
                    reasoning=parsed.get("reasoning", ""),
                    raw_output=raw_output,
                )

            except Exception as e:
                logger.error("Judge evaluation failed (attempt %d): %s", attempt + 1, e)
                if attempt == MAX_JUDGE_RETRIES:
                    return None

        return None

    async def evaluate_with_swap(
        self,
        test_case: TestCase,
        quilto_response: str,
        claude_response: str,
    ) -> PairwiseResult:
        """Evaluate with both orderings, randomizing first position.

        This implements position swap to reduce systematic bias. The final
        winner is only counted if both orderings agree.

        Args:
            test_case: The test case being evaluated.
            quilto_response: Quilto's response.
            claude_response: Claude's baseline response.

        Returns:
            PairwiseResult with aggregated judgment.
        """
        # Randomize first evaluation order to avoid systematic bias
        quilto_first = random.choice([True, False])

        if quilto_first:
            # First: Quilto=A, Claude=B
            judgment_ab = await self.evaluate_pair(test_case, quilto_response, claude_response)
            # Second: Claude=A, Quilto=B
            judgment_ba = await self.evaluate_pair(test_case, claude_response, quilto_response)
        else:
            # First: Claude=A, Quilto=B
            judgment_ba = await self.evaluate_pair(test_case, claude_response, quilto_response)
            # Second: Quilto=A, Claude=B
            judgment_ab = await self.evaluate_pair(test_case, quilto_response, claude_response)

        # Handle evaluation failures
        if judgment_ab is None or judgment_ba is None:
            return PairwiseResult(
                test_case_id=test_case.id,
                quilto_response=quilto_response,
                claude_response=claude_response,
                judgment_ab=judgment_ab,
                judgment_ba=judgment_ba,
                final_winner="error",
                is_consistent=False,
                quilto_aggregate=None,
                claude_aggregate=None,
                error_message="Judge evaluation failed",
            )

        # Determine consistent winner
        # judgment_ab: winner="A" means Quilto wins (Quilto was A)
        # judgment_ba: winner="B" means Quilto wins (Quilto was B)
        quilto_wins_ab = judgment_ab.winner == "A"
        quilto_wins_ba = judgment_ba.winner == "B"
        ab_tie = judgment_ab.winner == "Tie"
        ba_tie = judgment_ba.winner == "Tie"

        # Calculate aggregates (average from both orderings)
        quilto_aggregate = (judgment_ab.aggregate_score_a + judgment_ba.aggregate_score_b) / 2
        claude_aggregate = (judgment_ab.aggregate_score_b + judgment_ba.aggregate_score_a) / 2

        # Consistent win logic
        if quilto_wins_ab and quilto_wins_ba:
            final_winner = "quilto"
            is_consistent = True
        elif not quilto_wins_ab and not quilto_wins_ba and not ab_tie and not ba_tie:
            final_winner = "claude"
            is_consistent = True
        elif ab_tie and ba_tie:
            # Both judges said tie
            final_winner = "tie"
            is_consistent = True
        else:
            # Inconsistent results (including one tie and one winner)
            final_winner = "tie"
            is_consistent = False

        return PairwiseResult(
            test_case_id=test_case.id,
            quilto_response=quilto_response,
            claude_response=claude_response,
            judgment_ab=judgment_ab,
            judgment_ba=judgment_ba,
            final_winner=final_winner,
            is_consistent=is_consistent,
            quilto_aggregate=quilto_aggregate,
            claude_aggregate=claude_aggregate,
        )

    def get_cost_estimate(self) -> float:
        """Estimate cost based on model and accumulated tokens.

        Returns:
            Estimated cost in USD.
        """
        # Normalize model name for lookup
        model_key = self.judge_model
        if model_key not in MODEL_PRICING:
            # Try without openrouter prefix
            for key in MODEL_PRICING:
                if key.endswith(model_key) or model_key.endswith(key.split("/")[-1]):
                    model_key = key
                    break

        pricing = MODEL_PRICING.get(model_key, MODEL_PRICING["gpt-4o-mini"])

        input_cost = (self.total_input_tokens / 1_000_000) * pricing["input"]
        output_cost = (self.total_output_tokens / 1_000_000) * pricing["output"]
        return input_cost + output_cost

    def get_token_usage(self) -> dict[str, int]:
        """Get accumulated token usage.

        Returns:
            Dict with input_tokens and output_tokens.
        """
        return {
            "input_tokens": self.total_input_tokens,
            "output_tokens": self.total_output_tokens,
        }

    def reset_token_tracking(self) -> None:
        """Reset token tracking counters."""
        self.total_input_tokens = 0
        self.total_output_tokens = 0


# ============================================================================
# Quilto Response Generation
# ============================================================================


async def generate_quilto_response(
    query: str,
    context_dates: list[str],
) -> str | None:
    """Generate Quilto response using actual agent pipeline.

    Args:
        query: The user query.
        context_dates: List of dates for context (from test case).

    Returns:
        Quilto's synthesized response string, or None on error.
    """
    try:
        # Import here to avoid circular imports and allow mocking
        from quilto import LLMClient, load_llm_config
        from swealog.api.dependencies import get_domains
        from swealog.api.routes.query import execute_query_pipeline

        # Load LLM config
        config_path = Path("llm-config.yaml")
        if not config_path.exists():
            logger.error("llm-config.yaml not found")
            return None

        config = load_llm_config(config_path)
        llm_client = LLMClient(config)

        # Create storage adapter for test corpus
        # The test corpus uses flat structure, so we need to set up proper paths
        storage_result = _create_eval_storage(context_dates)
        if storage_result is None:
            logger.error("Failed to create storage for evaluation")
            return None

        # Unpack storage and temp dir reference (hold temp_dir_obj to prevent cleanup)
        storage, _temp_dir_obj = storage_result

        # Get all fitness domains
        domains = get_domains()

        # Execute full pipeline
        result = await execute_query_pipeline(
            query=query,
            llm_client=llm_client,
            storage=storage,
            domains=domains,
        )

        return result["response"]

    except Exception as e:
        logger.error("Quilto generation failed for query '%s': %s", query[:50], e)
        return None


def _create_eval_storage(context_dates: list[str]) -> tuple[Any, Any] | None:
    """Create a storage repository with test corpus data.

    The test corpus uses flat file structure (YYYY-MM-DD.md), but StorageRepository
    expects nested structure (logs/raw/YYYY/MM/YYYY-MM-DD.md). This function
    creates a temporary structure that maps correctly.

    Args:
        context_dates: Dates to make available in storage.

    Returns:
        Tuple of (StorageRepository, TemporaryDirectory) or None on error.
        The caller should hold the TemporaryDirectory reference to prevent cleanup.
    """
    import tempfile
    from datetime import date

    from quilto import StorageRepository

    try:
        # Create temporary directory with proper structure
        temp_dir_obj = tempfile.TemporaryDirectory(prefix="quilto_eval_")
        temp_dir = Path(temp_dir_obj.name)

        # Create the logs/raw/ structure
        raw_dir = temp_dir / "logs" / "raw"

        for date_str in context_dates:
            entry_date = date.fromisoformat(date_str)
            source_path = CORPUS_PATH / f"{date_str}.md"

            if not source_path.exists():
                logger.warning("Missing corpus entry: %s", date_str)
                continue

            # Create year/month directories
            target_dir = raw_dir / str(entry_date.year) / f"{entry_date.month:02d}"
            target_dir.mkdir(parents=True, exist_ok=True)

            # Copy the file with proper naming
            target_path = target_dir / f"{date_str}.md"

            # Transform flat structure to expected format
            content = source_path.read_text()
            # Add time header if not present (StorageRepository expects ## HH:MM format)
            if not content.strip().startswith("## "):
                content = f"## 12:00\n{content}"

            target_path.write_text(content)

        return StorageRepository(base_path=temp_dir), temp_dir_obj

    except Exception as e:
        logger.error("Failed to create eval storage: %s", e)
        return None


# Cache for Quilto responses to avoid regenerating
_quilto_response_cache: dict[str, str | None] = {}


async def generate_quilto_response_cached(
    test_case: TestCase,
    use_cache: bool = True,
) -> str | None:
    """Generate Quilto response with optional caching.

    Args:
        test_case: The test case to generate response for.
        use_cache: Whether to use cached responses.

    Returns:
        Quilto's response or None on error.
    """
    cache_key = test_case.id

    if use_cache and cache_key in _quilto_response_cache:
        return _quilto_response_cache[cache_key]

    response = await generate_quilto_response(test_case.query, test_case.context_entries)

    if use_cache:
        _quilto_response_cache[cache_key] = response

    return response


def clear_quilto_cache() -> None:
    """Clear the Quilto response cache."""
    _quilto_response_cache.clear()
