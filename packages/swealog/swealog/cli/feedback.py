"""Feedback recording infrastructure for dogfooding iterations.

This module provides Pydantic schemas and utilities for recording user feedback
after swealog auto responses. Feedback is stored in tests/eval/feedback/active/
for analysis during dogfooding iterations.
"""

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class IntermediateOutputs(BaseModel):
    """Intermediate agent outputs from query pipeline.

    All fields store model_dump() output from respective agent outputs.
    These are dicts, not typed models, for flexibility and JSON serialization.
    """

    model_config = ConfigDict(strict=True)

    router: dict[str, Any]  # RouterOutput.model_dump()
    planner: dict[str, Any]  # PlannerOutput.model_dump()
    retriever: dict[str, Any]  # RetrieverOutput.model_dump()
    analyzer: dict[str, Any]  # AnalyzerOutput.model_dump()
    synthesizer: dict[str, Any]  # SynthesizerOutput.model_dump()
    evaluator: dict[str, Any]  # Last EvaluatorOutput.model_dump() (may be after retry)


class SessionMetadata(BaseModel):
    """Session context for the feedback record."""

    model_config = ConfigDict(strict=True)

    timestamp: datetime
    input_type: Literal["LOG", "QUERY", "BOTH", "CORRECTION"]
    config_path: str | None = None
    storage_path: str | None = None
    debug_enabled: bool = True
    non_interactive: bool = False  # True when run via auto-dogfood script


class FeedbackRecord(BaseModel):
    """Complete feedback record for dogfooding analysis.

    Records user feedback after a swealog auto response for quality tracking.
    Stored in tests/eval/feedback/active/ as JSON files.
    """

    model_config = ConfigDict(strict=True)

    id: str = Field(..., min_length=1)  # {YYYY-MM-DD}_{short-hash}
    query: str = Field(..., min_length=1)
    intermediate_outputs: IntermediateOutputs
    final_response: str
    user_feedback: str  # Empty string if skipped
    session: SessionMetadata
    feedback_sentiment: str | None = None  # Future: auto-classify


def generate_feedback_id(query: str) -> str:
    """Generate unique ID for feedback record.

    Args:
        query: The query string to hash.

    Returns:
        ID in format YYYY-MM-DD_xxxxxxxx where x is first 8 chars of SHA256.
    """
    date_str = datetime.now().strftime("%Y-%m-%d")
    query_hash = hashlib.sha256(query.encode()).hexdigest()[:8]
    return f"{date_str}_{query_hash}"


def get_unique_feedback_path(base_dir: Path, feedback_id: str) -> Path:
    """Get unique file path, handling duplicates.

    Args:
        base_dir: Directory to write feedback files.
        feedback_id: Base ID from generate_feedback_id().

    Returns:
        Unique path (appends timestamp if needed).
    """
    base_path = base_dir / f"{feedback_id}.json"
    if not base_path.exists():
        return base_path

    # Append timestamp for uniqueness
    timestamp = datetime.now().strftime("%H%M%S")
    return base_dir / f"{feedback_id}_{timestamp}.json"


class FeedbackRecorder:
    """Utility class for recording user feedback to disk.

    Writes FeedbackRecord instances as JSON files to the feedback directory.
    Handles duplicate queries by appending timestamp suffix.
    """

    def __init__(self, feedback_dir: Path | None = None) -> None:
        """Initialize the feedback recorder.

        Args:
            feedback_dir: Directory for feedback files. Defaults to
                tests/eval/feedback/active/ relative to project root.
        """
        if feedback_dir is None:
            # Find project root (contains pyproject.toml)
            feedback_dir = self._find_project_root() / "tests" / "eval" / "feedback" / "active"
        self._feedback_dir = feedback_dir

    def _find_project_root(self) -> Path:
        """Find project root by looking for pyproject.toml."""
        current = Path.cwd()
        while current != current.parent:
            if (current / "pyproject.toml").exists():
                return current
            current = current.parent
        return Path.cwd()  # Fallback

    def get_feedback_dir(self) -> Path:
        """Get the feedback directory path.

        Returns:
            Path to tests/eval/feedback/active/ (or custom dir).
        """
        return self._feedback_dir

    def record(self, feedback: FeedbackRecord) -> Path:
        """Write feedback record to disk.

        Args:
            feedback: The FeedbackRecord to persist.

        Returns:
            Path to the created feedback file.
        """
        self._feedback_dir.mkdir(parents=True, exist_ok=True)
        file_path = get_unique_feedback_path(self._feedback_dir, feedback.id)
        file_path.write_text(
            json.dumps(feedback.model_dump(), indent=2, default=str, ensure_ascii=False),
            encoding="utf-8",
        )
        return file_path
