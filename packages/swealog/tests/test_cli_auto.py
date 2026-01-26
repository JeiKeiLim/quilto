"""Tests for swealog auto CLI command."""

from dataclasses import dataclass
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from swealog.cli import app
from typer.testing import CliRunner


@dataclass
class MockDomain:
    """Mock domain for testing."""

    name: str
    log_schema: dict[str, Any]
    vocabulary: dict[str, str]


@pytest.fixture
def runner() -> CliRunner:
    """Create CLI test runner."""
    return CliRunner()


@pytest.fixture
def mock_dependencies() -> tuple[MagicMock, MagicMock, list[MockDomain]]:
    """Create mock dependencies tuple."""
    mock_client = MagicMock()
    mock_storage = MagicMock()
    mock_domains = [MockDomain(name="GeneralFitness", log_schema={}, vocabulary={})]
    return (mock_client, mock_storage, mock_domains)


class TestAutoCommandRoutesLog:
    """AC1: Auto command routes LOG correctly."""

    def test_auto_routes_log(
        self, runner: CliRunner, mock_dependencies: tuple[MagicMock, MagicMock, list[MockDomain]]
    ) -> None:
        """Auto routes LOG input to log flow and shows success message."""
        with (
            patch("swealog.cli.auto_cmd.get_dependencies", return_value=mock_dependencies),
            patch("swealog.cli.auto_cmd.DomainSelector") as mock_selector,
            patch("swealog.cli.auto_cmd.RouterAgent") as mock_router_cls,
            patch("swealog.cli.auto_cmd.execute_log_flow") as mock_log_flow,
        ):
            mock_selector.return_value.get_domain_infos.return_value = []
            mock_router_cls.return_value.classify = AsyncMock(
                return_value=MagicMock(
                    input_type=MagicMock(value="LOG"),
                    selected_domains=["GeneralFitness"],
                    query_portion=None,
                    correction_target=None,
                    confidence=0.9,
                )
            )
            mock_log_flow.return_value = "2026-01-19_12-00-00"

            result = runner.invoke(app, ["auto", "bench 185x5"])

            assert result.exit_code == 0
            assert "Logged entry:" in result.output
            mock_log_flow.assert_called_once()


class TestAutoCommandRoutesQuery:
    """AC2: Auto command routes QUERY correctly."""

    def test_auto_routes_query(
        self, runner: CliRunner, mock_dependencies: tuple[MagicMock, MagicMock, list[MockDomain]]
    ) -> None:
        """Auto routes QUERY input to query flow and shows response panel."""
        with (
            patch("swealog.cli.auto_cmd.get_dependencies", return_value=mock_dependencies),
            patch("swealog.cli.auto_cmd.DomainSelector") as mock_selector,
            patch("swealog.cli.auto_cmd.RouterAgent") as mock_router_cls,
            patch("swealog.cli.auto_cmd.execute_query_pipeline") as mock_query_flow,
        ):
            mock_selector.return_value.get_domain_infos.return_value = []
            mock_router_cls.return_value.classify = AsyncMock(
                return_value=MagicMock(
                    input_type=MagicMock(value="QUERY"),
                    selected_domains=["GeneralFitness"],
                    query_portion=None,
                    correction_target=None,
                    confidence=0.9,
                )
            )
            mock_query_flow.return_value = {
                "response": "Your bench improved by 10 lbs.",
                "sources": ["2026-01-15"],
                "confidence": 0.85,
                "is_partial": False,
            }

            result = runner.invoke(app, ["auto", "how's my bench progress?"])

            assert result.exit_code == 0
            assert "bench improved" in result.output
            mock_query_flow.assert_called_once()


class TestAutoCommandHandlesBoth:
    """AC3: Auto command handles BOTH."""

    def test_auto_handles_both(
        self, runner: CliRunner, mock_dependencies: tuple[MagicMock, MagicMock, list[MockDomain]]
    ) -> None:
        """Auto with BOTH logs first, then queries with query_portion."""
        with (
            patch("swealog.cli.auto_cmd.get_dependencies", return_value=mock_dependencies),
            patch("swealog.cli.auto_cmd.DomainSelector") as mock_selector,
            patch("swealog.cli.auto_cmd.RouterAgent") as mock_router_cls,
            patch("swealog.cli.auto_cmd.execute_log_flow") as mock_log_flow,
            patch("swealog.cli.auto_cmd.execute_query_pipeline") as mock_query_flow,
        ):
            mock_selector.return_value.get_domain_infos.return_value = []
            mock_router_cls.return_value.classify = AsyncMock(
                return_value=MagicMock(
                    input_type=MagicMock(value="BOTH"),
                    selected_domains=["GeneralFitness"],
                    query_portion="how does this compare to last week?",
                    correction_target=None,
                    confidence=0.9,
                )
            )
            mock_log_flow.return_value = "2026-01-19_12-00-00"
            mock_query_flow.return_value = {
                "response": "Compared to last week, you lifted 5 more lbs.",
                "sources": ["2026-01-12", "2026-01-19"],
                "confidence": 0.8,
                "is_partial": False,
            }

            result = runner.invoke(app, ["auto", "bench 185x5, how does this compare to last week?"])

            assert result.exit_code == 0
            # Both results shown
            assert "Logged entry:" in result.output
            assert "Compared to last week" in result.output
            mock_log_flow.assert_called_once()
            mock_query_flow.assert_called_once()


class TestAutoCommandHandlesCorrection:
    """AC4: Auto command handles CORRECTION."""

    def test_auto_handles_correction(
        self, runner: CliRunner, mock_dependencies: tuple[MagicMock, MagicMock, list[MockDomain]]
    ) -> None:
        """Auto with CORRECTION executes correction flow."""
        with (
            patch("swealog.cli.auto_cmd.get_dependencies", return_value=mock_dependencies),
            patch("swealog.cli.auto_cmd.DomainSelector") as mock_selector,
            patch("swealog.cli.auto_cmd.RouterAgent") as mock_router_cls,
            patch("swealog.cli.auto_cmd.execute_log_flow") as mock_log_flow,
        ):
            mock_selector.return_value.get_domain_infos.return_value = []
            mock_router_cls.return_value.classify = AsyncMock(
                return_value=MagicMock(
                    input_type=MagicMock(value="CORRECTION"),
                    selected_domains=["GeneralFitness"],
                    query_portion=None,
                    correction_target="yesterday",
                    confidence=0.9,
                )
            )
            mock_log_flow.return_value = "2026-01-19_12-00-00"

            result = runner.invoke(app, ["auto", "actually yesterday was 195x5 not 185x5"])

            assert result.exit_code == 0
            assert "Logged entry:" in result.output
            # Verify correction mode was passed
            call_kwargs = mock_log_flow.call_args.kwargs
            assert call_kwargs.get("is_correction") is True


class TestAutoCommandDebugFlag:
    """AC5: Debug flag support."""

    def test_auto_debug_shows_timing(
        self, runner: CliRunner, mock_dependencies: tuple[MagicMock, MagicMock, list[MockDomain]]
    ) -> None:
        """Auto --debug shows all agent timing."""
        with (
            patch("swealog.cli.auto_cmd.get_dependencies", return_value=mock_dependencies),
            patch("swealog.cli.auto_cmd.DomainSelector") as mock_selector,
            patch("swealog.cli.auto_cmd.RouterAgent") as mock_router_cls,
            patch("swealog.cli.auto_cmd.execute_log_flow") as mock_log_flow,
        ):
            mock_selector.return_value.get_domain_infos.return_value = []
            mock_router_cls.return_value.classify = AsyncMock(
                return_value=MagicMock(
                    input_type=MagicMock(value="LOG"),
                    selected_domains=["GeneralFitness"],
                    query_portion=None,
                    correction_target=None,
                    confidence=0.9,
                )
            )
            mock_log_flow.return_value = "2026-01-19_12-00-00"

            result = runner.invoke(app, ["auto", "--debug", "bench 185x5"])

            assert result.exit_code == 0
            # Debug output shows Router timing (AC5 format: [AgentName] time: Xs)
            assert "[Router]" in result.output
            assert "time:" in result.output


class TestAutoCommandOptions:
    """Test auto command options work correctly."""

    def test_auto_with_config_option(
        self, runner: CliRunner, mock_dependencies: tuple[MagicMock, MagicMock, list[MockDomain]]
    ) -> None:
        """Auto command respects --config option."""
        with (
            patch("swealog.cli.auto_cmd.get_dependencies", return_value=mock_dependencies) as mock_get_deps,
            patch("swealog.cli.auto_cmd.DomainSelector") as mock_selector,
            patch("swealog.cli.auto_cmd.RouterAgent") as mock_router_cls,
            patch("swealog.cli.auto_cmd.execute_log_flow") as mock_log_flow,
        ):
            mock_selector.return_value.get_domain_infos.return_value = []
            mock_router_cls.return_value.classify = AsyncMock(
                return_value=MagicMock(
                    input_type=MagicMock(value="LOG"),
                    selected_domains=["GeneralFitness"],
                    query_portion=None,
                    correction_target=None,
                    confidence=0.9,
                )
            )
            mock_log_flow.return_value = "2026-01-19_12-00-00"

            result = runner.invoke(app, ["auto", "--config", "/custom/config.yaml", "bench 185x5"])

            assert result.exit_code == 0
            call_args = mock_get_deps.call_args
            assert call_args is not None
            assert str(call_args[0][0]) == "/custom/config.yaml"

    def test_auto_with_storage_option(
        self, runner: CliRunner, mock_dependencies: tuple[MagicMock, MagicMock, list[MockDomain]]
    ) -> None:
        """Auto command respects --storage option."""
        with (
            patch("swealog.cli.auto_cmd.get_dependencies", return_value=mock_dependencies) as mock_get_deps,
            patch("swealog.cli.auto_cmd.DomainSelector") as mock_selector,
            patch("swealog.cli.auto_cmd.RouterAgent") as mock_router_cls,
            patch("swealog.cli.auto_cmd.execute_log_flow") as mock_log_flow,
        ):
            mock_selector.return_value.get_domain_infos.return_value = []
            mock_router_cls.return_value.classify = AsyncMock(
                return_value=MagicMock(
                    input_type=MagicMock(value="LOG"),
                    selected_domains=["GeneralFitness"],
                    query_portion=None,
                    correction_target=None,
                    confidence=0.9,
                )
            )
            mock_log_flow.return_value = "2026-01-19_12-00-00"

            result = runner.invoke(app, ["auto", "--storage", "/custom/storage", "bench 185x5"])

            assert result.exit_code == 0
            call_args = mock_get_deps.call_args
            assert call_args is not None
            assert str(call_args[0][1]) == "/custom/storage"


class TestAutoCommandErrors:
    """Test error handling in auto command."""

    def test_auto_error_shows_message(self, runner: CliRunner) -> None:
        """Auto error shows user-friendly message and exits with error code."""
        with patch("swealog.cli.auto_cmd.get_dependencies", side_effect=Exception("Config error")):
            result = runner.invoke(app, ["auto", "test"])

            assert result.exit_code == 1
            assert "Failed to process input" in result.output


class TestAutoCommandUnexpectedInputType:
    """Test fallback for unexpected input types."""

    def test_auto_unexpected_input_type_falls_back_to_log(
        self, runner: CliRunner, mock_dependencies: tuple[MagicMock, MagicMock, list[MockDomain]]
    ) -> None:
        """Auto with unexpected input_type falls back to LOG flow."""
        with (
            patch("swealog.cli.auto_cmd.get_dependencies", return_value=mock_dependencies),
            patch("swealog.cli.auto_cmd.DomainSelector") as mock_selector,
            patch("swealog.cli.auto_cmd.RouterAgent") as mock_router_cls,
            patch("swealog.cli.auto_cmd.execute_log_flow") as mock_log_flow,
        ):
            mock_selector.return_value.get_domain_infos.return_value = []
            # Simulate an unexpected input type (e.g., future enum value)
            mock_router_cls.return_value.classify = AsyncMock(
                return_value=MagicMock(
                    input_type=MagicMock(value="UNKNOWN_FUTURE_TYPE"),
                    selected_domains=["GeneralFitness"],
                    query_portion=None,
                    correction_target=None,
                    confidence=0.9,
                )
            )
            mock_log_flow.return_value = "2026-01-19_12-00-00"

            result = runner.invoke(app, ["auto", "test input"])

            assert result.exit_code == 0
            # Falls back to LOG flow
            assert "Logged entry:" in result.output
            mock_log_flow.assert_called_once()


class TestPromptForFeedback:
    """Tests for _prompt_for_feedback() helper function (Story 11.2 Task 5.6)."""

    def test_returns_none_when_debug_disabled(self) -> None:
        """_prompt_for_feedback returns None when debug=False."""
        from swealog.cli.auto_cmd import _prompt_for_feedback  # pyright: ignore[reportPrivateUsage]

        result = _prompt_for_feedback(debug=False, non_interactive=False)
        assert result is None

    def test_returns_user_input_when_debug_enabled(self) -> None:
        """_prompt_for_feedback returns user input when debug=True."""
        from swealog.cli.auto_cmd import _prompt_for_feedback  # pyright: ignore[reportPrivateUsage]

        with patch("swealog.cli.auto_cmd.typer.prompt", return_value="Great response!"):
            result = _prompt_for_feedback(debug=True, non_interactive=False)
            assert result == "Great response!"

    def test_returns_empty_string_when_user_skips(self) -> None:
        """_prompt_for_feedback returns empty string when user presses Enter."""
        from swealog.cli.auto_cmd import _prompt_for_feedback  # pyright: ignore[reportPrivateUsage]

        with patch("swealog.cli.auto_cmd.typer.prompt", return_value=""):
            result = _prompt_for_feedback(debug=True, non_interactive=False)
            assert result == ""

    def test_prompt_message_is_correct(self) -> None:
        """_prompt_for_feedback uses correct prompt message."""
        from swealog.cli.auto_cmd import _prompt_for_feedback  # pyright: ignore[reportPrivateUsage]

        with patch("swealog.cli.auto_cmd.typer.prompt", return_value="feedback") as mock_prompt:
            _prompt_for_feedback(debug=True, non_interactive=False)
            mock_prompt.assert_called_once_with(
                "How was this response? (press Enter to skip)",
                default="",
                show_default=False,
            )


class TestRecordFeedback:
    """Tests for _record_feedback() helper function (Story 11.2 Task 6.6)."""

    def test_returns_none_when_no_intermediate_outputs(self, tmp_path: Any) -> None:
        """_record_feedback returns None when result has no intermediate_outputs."""
        from swealog.cli.auto_cmd import _record_feedback  # pyright: ignore[reportPrivateUsage]

        result: dict[str, Any] = {
            "response": "Test response",
            "sources": [],
            "confidence": 0.8,
            "is_partial": False,
        }

        path = _record_feedback(  # pyright: ignore[reportPrivateUsage]
            query="test query",
            input_type="QUERY",
            router_output={"input_type": "QUERY"},
            result=result,
            user_feedback="Good",
            config_path=None,
            storage_path=None,
        )

        assert path is None

    def test_records_feedback_with_intermediate_outputs(self, tmp_path: Any) -> None:
        """_record_feedback creates file when intermediate_outputs present."""
        from pathlib import Path as PathLib

        from swealog.cli.auto_cmd import _record_feedback  # pyright: ignore[reportPrivateUsage]

        result: dict[str, Any] = {
            "response": "Test response",
            "sources": [],
            "confidence": 0.8,
            "is_partial": False,
            "intermediate_outputs": {
                "planner": {"query": "test"},
                "retriever": {"entries": []},
                "analyzer": {"verdict": "SUFFICIENT"},
                "synthesizer": {"response": "test"},
                "evaluator": {"verdict": "PASS"},
            },
        }

        with patch("swealog.cli.auto_cmd.FeedbackRecorder") as mock_recorder_cls:
            mock_recorder = MagicMock()
            mock_recorder.record.return_value = tmp_path / "feedback.json"
            mock_recorder_cls.return_value = mock_recorder

            path = _record_feedback(  # pyright: ignore[reportPrivateUsage]
                query="test query",
                input_type="QUERY",
                router_output={"input_type": "QUERY", "confidence": 0.9},
                result=result,
                user_feedback="Great!",
                config_path=PathLib("/config.yaml"),
                storage_path=PathLib("/storage"),
            )

            assert path is not None
            mock_recorder.record.assert_called_once()
            # Verify FeedbackRecord was created with correct data
            call_args = mock_recorder.record.call_args[0][0]
            assert call_args.query == "test query"
            assert call_args.user_feedback == "Great!"
            assert call_args.intermediate_outputs.router["input_type"] == "QUERY"

    def test_records_empty_feedback_when_skipped(self, tmp_path: Any) -> None:
        """_record_feedback records empty string when user skips feedback."""
        from swealog.cli.auto_cmd import _record_feedback  # pyright: ignore[reportPrivateUsage]

        result: dict[str, Any] = {
            "response": "Test response",
            "sources": [],
            "confidence": 0.8,
            "is_partial": False,
            "intermediate_outputs": {
                "planner": {"query": "test"},
                "retriever": {"entries": []},
                "analyzer": {"verdict": "SUFFICIENT"},
                "synthesizer": {"response": "test"},
                "evaluator": {"verdict": "PASS"},
            },
        }

        with patch("swealog.cli.auto_cmd.FeedbackRecorder") as mock_recorder_cls:
            mock_recorder = MagicMock()
            mock_recorder.record.return_value = tmp_path / "feedback.json"
            mock_recorder_cls.return_value = mock_recorder

            _record_feedback(  # pyright: ignore[reportPrivateUsage]
                query="test query",
                input_type="QUERY",
                router_output={"input_type": "QUERY"},
                result=result,
                user_feedback="",  # Empty = skipped
                config_path=None,
                storage_path=None,
            )

            call_args = mock_recorder.record.call_args[0][0]
            assert call_args.user_feedback == ""


class TestAutoCommandFeedbackIntegration:
    """Integration tests for feedback recording in auto command (Story 11.2 Task 6.6)."""

    def test_query_flow_prompts_feedback_when_debug(
        self, runner: CliRunner, mock_dependencies: tuple[MagicMock, MagicMock, list[MockDomain]]
    ) -> None:
        """Auto QUERY flow with --debug prompts for feedback and records it."""
        with (
            patch("swealog.cli.auto_cmd.get_dependencies", return_value=mock_dependencies),
            patch("swealog.cli.auto_cmd.DomainSelector") as mock_selector,
            patch("swealog.cli.auto_cmd.RouterAgent") as mock_router_cls,
            patch("swealog.cli.auto_cmd.execute_query_pipeline") as mock_query_flow,
            patch("swealog.cli.auto_cmd.typer.prompt", return_value="Good answer!"),
            patch("swealog.cli.auto_cmd.FeedbackRecorder") as mock_recorder_cls,
        ):
            mock_selector.return_value.get_domain_infos.return_value = []
            mock_router_cls.return_value.classify = AsyncMock(
                return_value=MagicMock(
                    input_type=MagicMock(value="QUERY"),
                    selected_domains=["GeneralFitness"],
                    query_portion=None,
                    correction_target=None,
                    confidence=0.9,
                    model_dump=MagicMock(return_value={"input_type": "QUERY"}),
                )
            )
            mock_query_flow.return_value = {
                "response": "Your progress is good.",
                "sources": ["2026-01-15"],
                "confidence": 0.85,
                "is_partial": False,
                "intermediate_outputs": {
                    "planner": {"query": "test"},
                    "retriever": {"entries": []},
                    "analyzer": {"verdict": "SUFFICIENT"},
                    "synthesizer": {"response": "test"},
                    "evaluator": {"verdict": "PASS"},
                },
            }
            mock_recorder = MagicMock()
            mock_recorder_cls.return_value = mock_recorder

            result = runner.invoke(app, ["auto", "--debug", "how's my progress?"])

            assert result.exit_code == 0
            # Verify feedback was recorded
            mock_recorder.record.assert_called_once()

    def test_query_flow_no_feedback_prompt_without_debug(
        self, runner: CliRunner, mock_dependencies: tuple[MagicMock, MagicMock, list[MockDomain]]
    ) -> None:
        """Auto QUERY flow without --debug does not prompt for feedback."""
        with (
            patch("swealog.cli.auto_cmd.get_dependencies", return_value=mock_dependencies),
            patch("swealog.cli.auto_cmd.DomainSelector") as mock_selector,
            patch("swealog.cli.auto_cmd.RouterAgent") as mock_router_cls,
            patch("swealog.cli.auto_cmd.execute_query_pipeline") as mock_query_flow,
            patch("swealog.cli.auto_cmd.typer.prompt") as mock_prompt,
            patch("swealog.cli.auto_cmd.FeedbackRecorder") as mock_recorder_cls,
        ):
            mock_selector.return_value.get_domain_infos.return_value = []
            mock_router_cls.return_value.classify = AsyncMock(
                return_value=MagicMock(
                    input_type=MagicMock(value="QUERY"),
                    selected_domains=["GeneralFitness"],
                    query_portion=None,
                    correction_target=None,
                    confidence=0.9,
                )
            )
            mock_query_flow.return_value = {
                "response": "Your progress is good.",
                "sources": ["2026-01-15"],
                "confidence": 0.85,
                "is_partial": False,
            }

            result = runner.invoke(app, ["auto", "how's my progress?"])

            assert result.exit_code == 0
            # No prompt, no recording
            mock_prompt.assert_not_called()
            mock_recorder_cls.return_value.record.assert_not_called()

    def test_both_flow_prompts_feedback_when_debug(
        self, runner: CliRunner, mock_dependencies: tuple[MagicMock, MagicMock, list[MockDomain]]
    ) -> None:
        """Auto BOTH flow with --debug prompts for feedback after query portion."""
        with (
            patch("swealog.cli.auto_cmd.get_dependencies", return_value=mock_dependencies),
            patch("swealog.cli.auto_cmd.DomainSelector") as mock_selector,
            patch("swealog.cli.auto_cmd.RouterAgent") as mock_router_cls,
            patch("swealog.cli.auto_cmd.execute_log_flow") as mock_log_flow,
            patch("swealog.cli.auto_cmd.execute_query_pipeline") as mock_query_flow,
            patch("swealog.cli.auto_cmd.typer.prompt", return_value="Helpful!"),
            patch("swealog.cli.auto_cmd.FeedbackRecorder") as mock_recorder_cls,
        ):
            mock_selector.return_value.get_domain_infos.return_value = []
            mock_router_cls.return_value.classify = AsyncMock(
                return_value=MagicMock(
                    input_type=MagicMock(value="BOTH"),
                    selected_domains=["GeneralFitness"],
                    query_portion="how does this compare?",
                    correction_target=None,
                    confidence=0.9,
                    model_dump=MagicMock(return_value={"input_type": "BOTH"}),
                )
            )
            mock_log_flow.return_value = "2026-01-20_12-00-00"
            mock_query_flow.return_value = {
                "response": "Compared to last week...",
                "sources": [],
                "confidence": 0.8,
                "is_partial": False,
                "intermediate_outputs": {
                    "planner": {"query": "test"},
                    "retriever": {"entries": []},
                    "analyzer": {"verdict": "SUFFICIENT"},
                    "synthesizer": {"response": "test"},
                    "evaluator": {"verdict": "PASS"},
                },
            }
            mock_recorder = MagicMock()
            mock_recorder_cls.return_value = mock_recorder

            result = runner.invoke(app, ["auto", "--debug", "bench 200x5, how does this compare?"])

            assert result.exit_code == 0
            mock_recorder.record.assert_called_once()

    def test_log_flow_no_feedback_prompt(
        self, runner: CliRunner, mock_dependencies: tuple[MagicMock, MagicMock, list[MockDomain]]
    ) -> None:
        """Auto LOG flow does not prompt for feedback even with --debug."""
        with (
            patch("swealog.cli.auto_cmd.get_dependencies", return_value=mock_dependencies),
            patch("swealog.cli.auto_cmd.DomainSelector") as mock_selector,
            patch("swealog.cli.auto_cmd.RouterAgent") as mock_router_cls,
            patch("swealog.cli.auto_cmd.execute_log_flow") as mock_log_flow,
            patch("swealog.cli.auto_cmd.typer.prompt") as mock_prompt,
        ):
            mock_selector.return_value.get_domain_infos.return_value = []
            mock_router_cls.return_value.classify = AsyncMock(
                return_value=MagicMock(
                    input_type=MagicMock(value="LOG"),
                    selected_domains=["GeneralFitness"],
                    query_portion=None,
                    correction_target=None,
                    confidence=0.9,
                )
            )
            mock_log_flow.return_value = "2026-01-20_12-00-00"

            result = runner.invoke(app, ["auto", "--debug", "bench 200x5"])

            assert result.exit_code == 0
            # LOG flow should never prompt for feedback
            mock_prompt.assert_not_called()
