"""Fitness-specific significant entry detection for Observer triggers.

This module extends Quilto's DefaultSignificantEntryDetector with
fitness-specific patterns for PRs, milestones, and injury mentions.
"""

import re
from typing import Any

from quilto.state import DefaultSignificantEntryDetector
from quilto.storage import Entry


class FitnessSignificantEntryDetector(DefaultSignificantEntryDetector):
    """Fitness-specific significant entry detector.

    Extends DefaultSignificantEntryDetector with fitness-specific patterns:
    - Weight milestones (hit 200, broke 100kg, reached 300lbs)
    - Distance milestones (first 5k, first marathon, 100 mile week)
    - Injury/pain mentions (for cautionary tracking)

    Note: DefaultSignificantEntryDetector already handles:
    - PR indicators (personal record, pb, pr with word boundaries)
    - Generic milestones (first, 100th, 1000th)
    - Events (competition, race, meet, tournament)

    Example:
        >>> from quilto.storage import Entry
        >>> from datetime import date, datetime
        >>> detector = FitnessSignificantEntryDetector()
        >>> entry = Entry(
        ...     id="2024-01-15_001",
        ...     date=date(2024, 1, 15),
        ...     timestamp=datetime(2024, 1, 15, 10, 0, 0),
        ...     raw_content="New PR on bench press! Hit 200lbs for 5 reps."
        ... )
        >>> detector.is_significant(entry, {})
        True
    """

    def is_significant(self, entry: Entry, parsed_data: dict[str, Any]) -> bool:
        """Check for fitness-specific significant patterns.

        First checks the base implementation for PRs, milestones, and events.
        Then checks additional fitness-specific patterns.

        Args:
            entry: The log entry to evaluate.
            parsed_data: Parsed domain data from the entry.

        Returns:
            True if the entry is significant, False otherwise.
        """
        # First check base implementation (PRs, milestones, events)
        if super().is_significant(entry, parsed_data):
            return True

        content_lower = entry.raw_content.lower()

        # Weight milestones (strength training)
        # Patterns like "hit 200", "broke 100kg", "reached 300lbs"
        weight_patterns = [
            r"\bhit \d+",  # hit 200, hit 300
            r"\bbroke \d+",  # broke 100kg
            r"\breached \d+",  # reached 200lbs
        ]
        if any(re.search(pat, content_lower) for pat in weight_patterns):
            return True

        # Distance milestones (running/swimming)
        # These are beyond what DefaultDetector handles
        distance_keywords = [
            "first 5k",
            "first 10k",
            "first marathon",
            "first half",
            "100 mile",
            "1000km",
            "marathon debut",
        ]
        if any(kw in content_lower for kw in distance_keywords):
            return True

        # Injury mentions (cautionary tracking)
        # Important for tracking patterns that may need attention
        injury_keywords = ["injury", "injured", "pain", "hurt", "pulled", "strained"]
        return any(kw in content_lower for kw in injury_keywords)
