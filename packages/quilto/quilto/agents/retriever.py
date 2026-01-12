"""Retriever agent for fetching entries from storage.

This module provides the RetrieverAgent class which executes retrieval
instructions from the Planner agent, fetching entries using StorageRepository
methods and applying vocabulary expansion for better search coverage.
"""

from datetime import date
from typing import Any

from quilto.agents.models import (
    RetrievalAttempt,
    RetrieverInput,
    RetrieverOutput,
)
from quilto.storage.models import DateRange, Entry
from quilto.storage.repository import StorageRepository


def expand_terms(
    terms: list[str],
    vocabulary: dict[str, str],
    semantic_expansion: bool = False,
) -> list[str]:
    """Expand terms using vocabulary mapping.

    Args:
        terms: Original search terms.
        vocabulary: Term normalization mapping (abbreviation -> full form).
        semantic_expansion: If True, include related terms more aggressively.

    Returns:
        Expanded list of terms (deduplicated).

    Example:
        >>> vocabulary = {"pr": "personal record", "bench": "bench press"}
        >>> terms = ["pr", "bench"]
        >>> expand_terms(terms, vocabulary)
        ['pr', 'personal record', 'bench', 'bench press']
    """
    expanded: list[str] = []
    for term in terms:
        expanded.append(term)
        # Add expansion if exists (case-insensitive lookup)
        if term.lower() in vocabulary:
            expanded.append(vocabulary[term.lower()])
        # Also check if term is a value (reverse lookup)
        for k, v in vocabulary.items():
            if term.lower() == v.lower() and k not in expanded:
                expanded.append(k)

    # If semantic_expansion is True, add more related terms
    if semantic_expansion:
        # Add partial matches from vocabulary values
        for k, v in vocabulary.items():
            for term in terms:
                if term.lower() in v.lower() and v not in expanded:
                    expanded.append(v)
                    if k not in expanded:
                        expanded.append(k)

    return list(set(expanded))  # Deduplicate


class RetrieverAgent:
    """Retriever agent for executing retrieval instructions.

    Fetches entries from storage based on Planner's retrieval instructions.
    This agent is deterministic - it does NOT use LLM calls. It simply
    executes the retrieval strategies against StorageRepository.

    Attributes:
        storage: The storage repository for fetching entries.

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
        ...     vocabulary={"pr": "personal record"},
        ...     max_entries=100
        ... )
        >>> output = await retriever.retrieve(input)
    """

    AGENT_NAME = "retriever"

    def __init__(self, storage: StorageRepository) -> None:
        """Initialize the Retriever agent.

        Args:
            storage: StorageRepository instance for fetching entries.
        """
        self.storage = storage

    async def retrieve(self, retriever_input: RetrieverInput) -> RetrieverOutput:
        """Execute retrieval instructions and return entries.

        Processes each instruction in order, executes the appropriate
        retrieval strategy, deduplicates results, and enforces limits.

        Args:
            retriever_input: RetrieverInput with instructions, vocabulary,
                and max_entries limit.

        Returns:
            RetrieverOutput with entries, retrieval_summary, and warnings.
        """
        all_entries: list[Entry] = []
        retrieval_summary: list[RetrievalAttempt] = []
        warnings: list[str] = []

        # Process each instruction in order
        for i, instruction in enumerate(retriever_input.instructions, start=1):
            strategy = instruction.get("strategy", "")
            params = instruction.get("params", {})
            sub_query_id = instruction.get("sub_query_id", i)

            # Execute strategy
            entries, attempt = self._execute_strategy(
                attempt_number=i,
                strategy=strategy,
                params=params,
                sub_query_id=sub_query_id,
                vocabulary=retriever_input.vocabulary,
                warnings=warnings,
            )

            if attempt is not None:
                retrieval_summary.append(attempt)

                # Add warning for empty results
                if attempt.entries_found == 0:
                    warnings.append(f"Retrieval instruction {i} ({strategy}) returned 0 entries")

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
        )

    def _execute_strategy(
        self,
        attempt_number: int,
        strategy: str,
        params: dict[str, Any],
        sub_query_id: int,
        vocabulary: dict[str, str],
        warnings: list[str],
    ) -> tuple[list[Entry], RetrievalAttempt | None]:
        """Execute a single retrieval strategy.

        Args:
            attempt_number: Sequential number of this attempt (1-based).
            strategy: The strategy to execute (date_range, keyword, topical).
            params: Strategy-specific parameters.
            sub_query_id: ID of the sub-query this instruction belongs to.
            vocabulary: Term normalization mapping.
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
        elif strategy_lower == "keyword":
            return self._execute_keyword(
                attempt_number=attempt_number,
                params=params,
                vocabulary=vocabulary,
                warnings=warnings,
            )
        elif strategy_lower == "topical":
            return self._execute_topical(
                attempt_number=attempt_number,
                params=params,
                vocabulary=vocabulary,
                warnings=warnings,
            )
        else:
            # Unknown strategy
            warnings.append(f"Unknown strategy '{strategy}' in instruction {attempt_number}, skipping")
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
            expanded_terms=[],
        )

        return entries, attempt

    def _execute_keyword(
        self,
        attempt_number: int,
        params: dict[str, Any],
        vocabulary: dict[str, str],
        warnings: list[str],
    ) -> tuple[list[Entry], RetrievalAttempt | None]:
        """Execute KEYWORD strategy with vocabulary expansion.

        Args:
            attempt_number: Sequential number of this attempt.
            params: Must contain keywords list, optional semantic_expansion and date_range.
            vocabulary: Term normalization mapping.
            warnings: List to append warnings to.

        Returns:
            Tuple of (entries found, RetrievalAttempt record).
        """
        keywords = params.get("keywords", [])

        if not keywords:
            warnings.append(f"Missing required param 'keywords' for keyword in instruction {attempt_number}")
            return [], None

        # Expand keywords using vocabulary
        semantic_expansion = params.get("semantic_expansion", False)
        expanded = expand_terms(keywords, vocabulary, semantic_expansion)

        # Parse optional date range
        date_range = self._parse_date_range(params)

        entries = self.storage.search_entries(expanded, date_range=date_range)

        attempt = RetrievalAttempt(
            attempt_number=attempt_number,
            strategy="keyword",
            params=params,
            entries_found=len(entries),
            summary=f"Searched for {len(expanded)} terms, found {len(entries)} entries",
            expanded_terms=expanded,
        )

        return entries, attempt

    def _execute_topical(
        self,
        attempt_number: int,
        params: dict[str, Any],
        vocabulary: dict[str, str],
        warnings: list[str],
    ) -> tuple[list[Entry], RetrievalAttempt | None]:
        """Execute TOPICAL strategy.

        Args:
            attempt_number: Sequential number of this attempt.
            params: Must contain topics list, optional related_terms and date_range.
            vocabulary: Term normalization mapping.
            warnings: List to append warnings to.

        Returns:
            Tuple of (entries found, RetrievalAttempt record).
        """
        topics = params.get("topics", [])
        related_terms = params.get("related_terms", [])

        if not topics:
            warnings.append(f"Missing required param 'topics' for topical in instruction {attempt_number}")
            return [], None

        # Combine topics and related_terms
        combined = topics + related_terms

        # Expand using vocabulary
        expanded = expand_terms(combined, vocabulary, semantic_expansion=False)

        # Parse optional date range
        date_range = self._parse_date_range(params)

        entries = self.storage.search_entries(expanded, date_range=date_range)

        attempt = RetrievalAttempt(
            attempt_number=attempt_number,
            strategy="topical",
            params=params,
            entries_found=len(entries),
            summary=f"Searched topics {topics} with {len(expanded)} expanded terms, found {len(entries)} entries",
            expanded_terms=expanded,
        )

        return entries, attempt

    def _parse_date_range(self, params: dict[str, Any]) -> DateRange | None:
        """Parse optional date_range from params.

        Args:
            params: Parameters dict that may contain date_range.

        Returns:
            DateRange if present and valid, None otherwise.
        """
        date_range_param = params.get("date_range")
        if not date_range_param:
            return None

        try:
            start_str = date_range_param.get("start")
            end_str = date_range_param.get("end")
            if start_str and end_str:
                return DateRange(
                    start=date.fromisoformat(start_str),
                    end=date.fromisoformat(end_str),
                )
        except (ValueError, AttributeError):
            pass

        return None

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
