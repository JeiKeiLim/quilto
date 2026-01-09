"""Test schemas for expected retrieval outputs.

These schemas define the structure for Retriever agent testing.
Used to validate retrieval accuracy in Epic 3 (Story 3-3: Implement Retriever Agent).
"""

from typing import Literal

from pydantic import BaseModel, ConfigDict

StrategyType = Literal["date_range", "keyword", "pattern"]


class RetrievalStrategy(BaseModel):
    """Strategy for retrieving entries.

    Attributes:
        type: Strategy type (date_range, keyword, pattern).
        start: Start date for date_range type (YYYY-MM-DD).
        end: End date for date_range type (YYYY-MM-DD).
        keywords: List of keywords/exercise names to match.
        pattern: Description of pattern to identify.
    """

    model_config = ConfigDict(strict=True)

    type: StrategyType
    start: str | None = None
    end: str | None = None
    keywords: list[str] = []
    pattern: str | None = None


class RetrievalTestCase(BaseModel):
    """Expected output for Retriever agent testing.

    Attributes:
        query: Natural language query from user.
        strategy: Retrieval strategy defining how to find entries.
        expected_entry_ids: List of entry IDs (dates/filenames) that should be returned.
    """

    model_config = ConfigDict(strict=True)

    query: str
    strategy: RetrievalStrategy
    expected_entry_ids: list[str]
