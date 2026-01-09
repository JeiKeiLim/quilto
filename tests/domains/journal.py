"""JournalDomain module for testing Quilto's domain-agnostic interface.

This module is TEST INFRASTRUCTURE, not application code. It demonstrates
that DomainModule works for non-fitness domains.
"""

from quilto import DomainModule

from tests.corpus.schemas import JournalEntry

__all__ = ["JournalDomain", "journal_domain"]


class JournalDomain(DomainModule):
    """Test domain for personal journal entries.

    This domain covers personal journal and diary entries including
    mood tracking, daily reflections, and personal notes. Used to
    validate DomainModule works for non-fitness use cases.
    """


journal_domain = JournalDomain(
    description=(
        "Personal journal and diary entries including mood tracking, "
        "daily reflections, personal notes, and emotional states. "
        "Covers topics like work, family, health, and daily activities."
    ),
    log_schema=JournalEntry,
    vocabulary={
        "felt": "feeling",
        "stressed": "stress",
        "anxious": "anxiety",
        "happy": "happiness",
        "sad": "sadness",
        "tired": "fatigue",
        "기분": "mood",
        "스트레스": "stress",
        "피곤": "fatigue",
        "행복": "happiness",
        "met": "meeting",
        "talked": "conversation",
        "만남": "meeting",
    },
    expertise=(
        "Emotional awareness and mood tracking patterns. Daily reflection "
        "and journaling conventions. Topic extraction from narrative text. "
        "Recognition of emotional states expressed implicitly or explicitly."
    ),
)
