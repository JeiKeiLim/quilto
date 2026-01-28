"""Feedback recording infrastructure for dogfooding iterations.

This module provides Pydantic schemas and utilities for recording user feedback
after swealog auto responses. Feedback is stored in tests/eval/feedback/active/
for analysis during dogfooding iterations.
"""

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Literal, TypedDict

from pydantic import BaseModel, ConfigDict, Field


class TraceDict(TypedDict):
    """Type-safe dict structure for agent traces from ProcessResult.debug.traces.

    This documents the expected structure. At runtime, traces are passed as
    dict[str, Any] for Pydantic compatibility with list invariance.
    """

    agent_name: str
    input_summary: str
    output_summary: str
    elapsed_ms: float
    timestamp: str


class IntermediateOutputs(BaseModel):
    """Intermediate agent outputs from query pipeline.

    All fields store model_dump() output from respective agent outputs.
    These are dicts, not typed models, for flexibility and JSON serialization.
    All fields default to empty dict - not all agents run in every flow.
    """

    model_config = ConfigDict(strict=True)

    router: dict[str, Any] = Field(default_factory=dict)  # RouterOutput.model_dump()
    planner: dict[str, Any] = Field(default_factory=dict)  # PlannerOutput.model_dump()
    retriever: dict[str, Any] = Field(default_factory=dict)  # RetrieverOutput.model_dump()
    analyzer: dict[str, Any] = Field(default_factory=dict)  # AnalyzerOutput.model_dump()
    synthesizer: dict[str, Any] = Field(default_factory=dict)  # SynthesizerOutput.model_dump()
    evaluator: dict[str, Any] = Field(default_factory=dict)  # EvaluatorOutput.model_dump()
    parser: dict[str, Any] = Field(default_factory=dict)  # ParserOutput.model_dump()
    observer: dict[str, Any] = Field(default_factory=dict)  # ObserverOutput.model_dump()
    correction: dict[str, Any] = Field(default_factory=dict)  # CorrectionResult.model_dump()


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


class SimplifiedFeedbackRecord(BaseModel):
    """Simplified feedback record using ProcessResult traces.

    Records user feedback with traces from Quilto ProcessResult instead of
    full intermediate outputs. Used after migration to Quilto API.
    """

    model_config = ConfigDict(strict=True)

    id: str = Field(..., min_length=1)  # {YYYY-MM-DD}_{short-hash}
    query: str = Field(..., min_length=1)
    traces: list[dict[str, Any]]  # Structure documented in TraceDict
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


class FeedbackProgressHandler:
    """ProgressHandler that captures agent outputs for feedback recording.

    Implements the Quilto ProgressHandler Protocol via duck typing.
    Stores full agent outputs for later retrieval via get_intermediate_outputs().

    Note: Not thread-safe. Intended for single-session use within CLI command.
    """

    def __init__(self, debug: bool = False) -> None:
        """Initialize the feedback progress handler.

        Args:
            debug: If True, print agent outputs to terminal as they complete.
        """
        self._outputs: dict[str, dict[str, Any]] = {}
        self._debug = debug

    async def on_agent_start(self, agent: str, input_summary: str) -> None:
        """Track agent start (no-op for feedback recording).

        Args:
            agent: Name of the agent starting.
            input_summary: Brief summary of input being processed.
        """
        pass

    async def on_agent_complete(self, agent: str, elapsed: float, output: dict[str, Any]) -> None:
        """Capture agent output and optionally print debug info.

        Args:
            agent: Name of the agent that completed.
            elapsed: Execution time in seconds.
            output: Agent output as dictionary.
        """
        self._outputs[agent] = output
        if self._debug:
            from swealog.cli.output import print_info

            print_info(f"[{agent.capitalize()}]")
            print_info(json.dumps(output, indent=2, ensure_ascii=False))

    async def on_retry(self, attempt: int, reason: str) -> None:
        """Track retries (no-op for feedback recording).

        Args:
            attempt: Current retry attempt number.
            reason: Why the retry is happening.
        """
        pass

    async def on_stage(self, stage: str) -> None:
        """Track stage transitions (no-op for feedback recording).

        Args:
            stage: Name of the stage.
        """
        pass

    def get_outputs(self) -> dict[str, dict[str, Any]]:
        """Get all captured outputs.

        Returns:
            Copy of the captured outputs dictionary.
        """
        return self._outputs.copy()

    def get_intermediate_outputs(self) -> IntermediateOutputs:
        """Convert captured outputs to IntermediateOutputs model.

        Returns:
            IntermediateOutputs with captured agent data.
            Agents that weren't called have empty dict {}.
        """
        return IntermediateOutputs(
            router=self._outputs.get("router", {}),
            planner=self._outputs.get("planner", {}),
            retriever=self._outputs.get("retriever", {}),
            analyzer=self._outputs.get("analyzer", {}),
            synthesizer=self._outputs.get("synthesizer", {}),
            evaluator=self._outputs.get("evaluator", {}),
            parser=self._outputs.get("parser", {}),
            observer=self._outputs.get("observer", {}),
            correction=self._outputs.get("correction", {}),
        )


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

    def record_simplified(self, feedback: SimplifiedFeedbackRecord) -> Path:
        """Write simplified feedback record to disk.

        Args:
            feedback: The SimplifiedFeedbackRecord to persist (uses traces instead of full outputs).

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
