"""Placeholder parser for accuracy testing.

This module provides a mock parser implementation until the real Parser
agent is implemented in Story 2.3. The mock returns empty workout data.
"""

from quilto import DomainModule

from tests.corpus.schemas import ExpectedParserOutput


async def parse_entry(raw_text: str, domain: DomainModule) -> ExpectedParserOutput:
    """Placeholder parser - returns empty workout until Parser exists.

    This function provides the interface that the real Parser will implement
    in Story 2.3. Until then, it returns an empty workout structure.

    Args:
        raw_text: The raw log entry text to parse.
        domain: The domain module to use for parsing context.

    Returns:
        An empty ExpectedParserOutput with no exercises.
    """
    _ = raw_text  # Unused until Parser implementation
    _ = domain  # Unused until Parser implementation
    return ExpectedParserOutput(exercises=[], date="placeholder")
