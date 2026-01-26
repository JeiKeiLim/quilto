"""Retriever agent for fetching entries from storage.

This module provides the RetrieverAgent class which executes retrieval
instructions from the Planner agent, fetching entries using StorageRepository
methods. Only DATE_RANGE strategy is supported.
"""

from datetime import date, timedelta
from typing import Any

from quilto.agents.models import (
    RetrievalAttempt,
    RetrieverInput,
    RetrieverOutput,
)
from quilto.storage.models import DateRange, Entry
from quilto.storage.repository import StorageRepository


class RetrieverAgent:
    """Retriever agent for executing retrieval instructions.

    Fetches entries from storage based on Planner's retrieval instructions.
    This agent is deterministic - it does NOT use LLM calls. It simply
    executes date-range retrieval against StorageRepository.

    Only DATE_RANGE strategy is supported. Keyword and topical searches were
    removed in Story 13.2 due to language/spacing edge cases. Analyzer performs
    LLM-based relevance filtering instead.

    Attributes:
        storage: The storage repository for fetching entries.
        EXPANSION_TIERS: Days to expand to when date range returns empty results.

    Example:
        >>> from pathlib import Path
        >>> from quilto.storage import StorageRepository
        >>> from quilto.agents import RetrieverAgent, RetrieverInput
        >>> storage = StorageRepository(Path("/tmp/storage"))
        >>> retriever = RetrieverAgent(storage)
        >>> input = RetrieverInput(
        ...     instructions=[{
        ...         "strategy": "date_range",
        ...         "params": {"start_date": "2026-01-01", "end_date": "2026-01-07"},
        ...         "sub_query_id": 1
        ...     }],
        ...     max_entries=100
        ... )
        >>> output = await retriever.retrieve(input)
    """

    AGENT_NAME = "retriever"
    EXPANSION_TIERS: list[int] = [7, 14, 30, 90]

    def __init__(self, storage: StorageRepository) -> None:
        """Initialize the Retriever agent.

        Args:
            storage: StorageRepository instance for fetching entries.
        """
        self.storage = storage

    async def retrieve(self, retriever_input: RetrieverInput) -> RetrieverOutput:
        """Execute retrieval instructions and return entries.

        Processes each instruction in order, executes date-range retrieval,
        deduplicates results, and enforces limits. Supports progressive
        expansion when date range returns empty results.

        Args:
            retriever_input: RetrieverInput with instructions and max_entries limit.

        Returns:
            RetrieverOutput with entries, retrieval_summary, and warnings.
        """
        all_entries: list[Entry] = []
        retrieval_summary: list[RetrievalAttempt] = []
        warnings: list[str] = []
        expansion_exhausted = False
        strategies_used: list[str] = []

        # Sort instructions by priority (lower = higher priority, default=1)
        # Defensive: handle non-int priority values gracefully
        def get_priority(instruction: dict[str, Any]) -> int:
            """Extract priority with defensive handling for malformed values."""
            priority = instruction.get("priority", 1)
            if isinstance(priority, int):
                return priority
            if isinstance(priority, float):
                return int(priority)
            return 1  # Default for strings, None, or other invalid types

        sorted_instructions = sorted(
            retriever_input.instructions,
            key=get_priority,
        )

        # Process each instruction in priority order
        for i, instruction in enumerate(sorted_instructions, start=1):
            strategy = instruction.get("strategy", "")
            params = instruction.get("params", {})

            # Check if explicit_date flag is set (disables expansion)
            explicit_date = params.get("explicit_date", False)
            enable_expansion = (
                retriever_input.enable_progressive_expansion and not explicit_date and strategy.lower() == "date_range"
            )

            # Execute strategy (with expansion for date_range if enabled)
            if enable_expansion:
                entries, attempts, exhausted = self._execute_date_range_with_expansion(
                    attempt_number=i,
                    params=params,
                    warnings=warnings,
                )
                retrieval_summary.extend(attempts)
                if exhausted:
                    expansion_exhausted = True
            else:
                entries, attempt = self._execute_strategy(
                    attempt_number=i,
                    strategy=strategy,
                    params=params,
                    warnings=warnings,
                )

                if attempt is not None:
                    retrieval_summary.append(attempt)

                    # Add warning for empty results
                    if attempt.entries_found == 0:
                        warnings.append(f"Retrieval instruction {i} ({strategy}) returned 0 entries")

            # Track strategy if it contributed entries
            if entries:
                strategy_name = strategy.lower()
                if strategy_name and strategy_name not in strategies_used:
                    strategies_used.append(strategy_name)

            all_entries.extend(entries)

        # Deduplicate entries by ID, keeping first occurrence
        seen_ids: set[str] = set()
        unique_entries: list[Entry] = []
        for entry in all_entries:
            if entry.id not in seen_ids:
                seen_ids.add(entry.id)
                unique_entries.append(entry)

        # Calculate total before truncation
        total_entries_found = len(unique_entries)

        # Apply max_entries limit
        truncated = False
        if len(unique_entries) > retriever_input.max_entries:
            truncated = True
            warnings.append(
                f"Results truncated: {total_entries_found} entries found, returning {retriever_input.max_entries}"
            )
            unique_entries = unique_entries[: retriever_input.max_entries]

        # Calculate date range covered
        date_range_covered = self._calculate_date_range(unique_entries)

        return RetrieverOutput(
            entries=unique_entries,
            retrieval_summary=retrieval_summary,
            total_entries_found=total_entries_found,
            date_range_covered=date_range_covered,
            warnings=warnings,
            truncated=truncated,
            expansion_exhausted=expansion_exhausted,
            strategies_used=strategies_used,
        )

    def _execute_strategy(
        self,
        attempt_number: int,
        strategy: str,
        params: dict[str, Any],
        warnings: list[str],
    ) -> tuple[list[Entry], RetrievalAttempt | None]:
        """Execute a single retrieval strategy.

        Only DATE_RANGE is supported.

        Args:
            attempt_number: Sequential number of this attempt (1-based).
            strategy: The strategy to execute (only date_range supported).
            params: Strategy-specific parameters.
            warnings: List to append warnings to (modified in place).

        Returns:
            Tuple of (entries found, RetrievalAttempt record).
        """
        strategy_lower = strategy.lower()

        if strategy_lower == "date_range":
            return self._execute_date_range(
                attempt_number=attempt_number,
                params=params,
                warnings=warnings,
            )
        else:
            # Unknown strategy - only DATE_RANGE is supported
            warnings.append(
                f"Unknown strategy '{strategy}' in instruction {attempt_number}, only 'date_range' is supported"
            )
            return [], None

    def _execute_date_range(
        self,
        attempt_number: int,
        params: dict[str, Any],
        warnings: list[str],
    ) -> tuple[list[Entry], RetrievalAttempt | None]:
        """Execute DATE_RANGE strategy.

        Args:
            attempt_number: Sequential number of this attempt.
            params: Must contain start_date and end_date.
            warnings: List to append warnings to.

        Returns:
            Tuple of (entries found, RetrievalAttempt record).
        """
        start_str = params.get("start_date")
        end_str = params.get("end_date")

        if not start_str:
            warnings.append(f"Missing required param 'start_date' for date_range in instruction {attempt_number}")
            return [], None

        if not end_str:
            warnings.append(f"Missing required param 'end_date' for date_range in instruction {attempt_number}")
            return [], None

        try:
            start_date = date.fromisoformat(start_str)
            end_date = date.fromisoformat(end_str)
        except ValueError as e:
            warnings.append(f"Invalid date format in instruction {attempt_number}: {e}")
            return [], None

        entries = self.storage.get_entries_by_date_range(start_date, end_date)

        attempt = RetrievalAttempt(
            attempt_number=attempt_number,
            strategy="date_range",
            params=params,
            entries_found=len(entries),
            summary=f"Retrieved {len(entries)} entries from {start_str} to {end_str}",
        )

        return entries, attempt

    def _calculate_date_range(self, entries: list[Entry]) -> DateRange | None:
        """Calculate the date range covered by entries.

        Args:
            entries: List of entries to calculate range for.

        Returns:
            DateRange covering all entries, or None if empty.
        """
        if not entries:
            return None

        dates = [entry.date for entry in entries]
        return DateRange(start=min(dates), end=max(dates))

    def _execute_date_range_with_expansion(
        self,
        attempt_number: int,
        params: dict[str, Any],
        warnings: list[str],
    ) -> tuple[list[Entry], list[RetrievalAttempt], bool]:
        """Execute date range with progressive expansion on empty results.

        Tries the original date range first, then progressively expands
        through tiers (7, 14, 30, 90 days) until entries are found or
        expansion is exhausted.

        Args:
            attempt_number: Base attempt number.
            params: Original date_range params with start_date, end_date.
            warnings: List to append warnings to.

        Returns:
            Tuple of (entries, list of RetrievalAttempts, expansion_exhausted).
        """
        attempts: list[RetrievalAttempt] = []

        # Tier 0: Original date range
        entries, attempt = self._execute_date_range(
            attempt_number=attempt_number,
            params=params,
            warnings=warnings,
        )

        if attempt is not None:
            attempt.expansion_tier = 0
            attempts.append(attempt)

            if attempt.entries_found > 0:
                return entries, attempts, False

        # If original date range failed validation (attempt is None), skip expansion
        if attempt is None:
            return [], attempts, False

        # Progressive expansion through tiers
        today = date.today()
        for tier_index, days in enumerate(self.EXPANSION_TIERS, start=1):
            expanded_params = {
                "start_date": (today - timedelta(days=days)).isoformat(),
                "end_date": today.isoformat(),
            }

            entries, tier_attempt = self._execute_date_range(
                attempt_number=attempt_number,
                params=expanded_params,
                warnings=[],  # Don't add warnings for expansion attempts
            )

            if tier_attempt is not None:
                tier_attempt.expansion_tier = tier_index
                tier_attempt.summary = f"Expanded to {days} days: {tier_attempt.summary}"
                attempts.append(tier_attempt)

                if tier_attempt.entries_found > 0:
                    return entries, attempts, False

        # Exhausted all tiers
        warnings.append("Progressive expansion exhausted all tiers with no results")
        return [], attempts, True
