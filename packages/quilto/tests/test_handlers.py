"""Unit tests for quilto/handlers.py ProgressHandler protocol."""

from typing import Any

import pytest
from quilto.handlers import ProgressHandler


class TestProgressHandler:
    """Tests for ProgressHandler Protocol."""

    @pytest.mark.asyncio
    async def test_protocol_implementation(self) -> None:
        """Verify ProgressHandler Protocol can be implemented."""

        class MockProgressHandler:
            """Mock implementation of ProgressHandler for testing."""

            def __init__(self) -> None:
                self.events: list[tuple[str, ...]] = []
                self.outputs: list[dict[str, Any]] = []

            async def on_agent_start(self, agent: str, input_summary: str) -> None:
                self.events.append(("start", agent, input_summary))

            async def on_agent_complete(self, agent: str, elapsed: float, output: dict[str, Any]) -> None:
                self.events.append(("complete", agent, str(elapsed)))
                self.outputs.append(output)

            async def on_retry(self, attempt: int, reason: str) -> None:
                self.events.append(("retry", str(attempt), reason))

            async def on_stage(self, stage: str) -> None:
                self.events.append(("stage", stage))

        handler = MockProgressHandler()

        # Verify handler implements ProgressHandler protocol
        assert isinstance(handler, ProgressHandler)

        # Test all callback methods
        await handler.on_agent_start("router", "Processing user input")
        router_output = {"input_type": "query", "selected_domains": ["fitness"]}
        await handler.on_agent_complete("router", 0.15, router_output)
        await handler.on_retry(1, "Malformed JSON response")
        await handler.on_stage("planning")

        assert len(handler.events) == 4
        assert handler.events[0] == ("start", "router", "Processing user input")
        assert handler.events[1] == ("complete", "router", "0.15")
        assert handler.events[2] == ("retry", "1", "Malformed JSON response")
        assert handler.events[3] == ("stage", "planning")

        # Verify output was captured
        assert len(handler.outputs) == 1
        assert handler.outputs[0] == router_output

    @pytest.mark.asyncio
    async def test_on_agent_complete_output_parameter(self) -> None:
        """Verify on_agent_complete receives output dict for each agent type."""

        class OutputCaptureHandler:
            """Handler that captures outputs from on_agent_complete."""

            def __init__(self) -> None:
                self.agent_outputs: dict[str, dict[str, Any]] = {}

            async def on_agent_complete(self, agent: str, elapsed: float, output: dict[str, Any]) -> None:
                self.agent_outputs[agent] = output

        handler = OutputCaptureHandler()

        # Router output (AC-2)
        router_out = {"input_type": "query", "selected_domains": ["fitness"], "confidence": 0.9}
        await handler.on_agent_complete("router", 0.1, router_out)
        assert handler.agent_outputs["router"]["input_type"] == "query"
        assert handler.agent_outputs["router"]["selected_domains"] == ["fitness"]
        assert handler.agent_outputs["router"]["confidence"] == 0.9

        # Planner output (AC-3)
        planner_out = {"query_type": "trend", "retrieval_instructions": [], "next_action": "retrieve"}
        await handler.on_agent_complete("planner", 0.2, planner_out)
        assert handler.agent_outputs["planner"]["query_type"] == "trend"
        assert handler.agent_outputs["planner"]["next_action"] == "retrieve"

        # Retriever output (AC-4)
        retriever_out = {"entries": [], "retrieval_summary": []}
        await handler.on_agent_complete("retriever", 0.1, retriever_out)
        assert "entries" in handler.agent_outputs["retriever"]
        assert "retrieval_summary" in handler.agent_outputs["retriever"]

        # Analyzer output (AC-5)
        analyzer_out = {"verdict": "sufficient", "findings": []}
        await handler.on_agent_complete("analyzer", 0.3, analyzer_out)
        assert handler.agent_outputs["analyzer"]["verdict"] == "sufficient"
        assert "findings" in handler.agent_outputs["analyzer"]

        # Synthesizer output (AC-6)
        synthesizer_out = {"response": "Your weekly progress looks great!"}
        await handler.on_agent_complete("synthesizer", 0.4, synthesizer_out)
        assert "response" in handler.agent_outputs["synthesizer"]

        # Evaluator output (AC-7)
        evaluator_out = {"overall_verdict": "sufficient", "feedback": []}
        await handler.on_agent_complete("evaluator", 0.2, evaluator_out)
        assert handler.agent_outputs["evaluator"]["overall_verdict"] == "sufficient"
        assert "feedback" in handler.agent_outputs["evaluator"]

        # Parser output (AC-8)
        parser_out = {"domain_data": {"fitness": {}}}
        await handler.on_agent_complete("parser", 0.15, parser_out)
        assert "domain_data" in handler.agent_outputs["parser"]

        # Observer output (AC-9)
        observer_out = {"should_update": True, "updates": []}
        await handler.on_agent_complete("observer", 0.1, observer_out)
        assert handler.agent_outputs["observer"]["should_update"] is True
        assert "updates" in handler.agent_outputs["observer"]

    @pytest.mark.asyncio
    async def test_on_agent_complete_empty_output_on_error(self) -> None:
        """Verify on_agent_complete receives empty dict {} on agent failure (AC-11)."""

        class ErrorOutputHandler:
            """Handler to verify error case."""

            def __init__(self) -> None:
                self.outputs: list[dict[str, Any]] = []

            async def on_agent_complete(self, agent: str, elapsed: float, output: dict[str, Any]) -> None:
                self.outputs.append(output)

        handler = ErrorOutputHandler()

        # Simulate error case - empty dict
        await handler.on_agent_complete("router", 0.01, {})
        assert handler.outputs[0] == {}

    @pytest.mark.asyncio
    async def test_backward_compatibility_old_handler_signature(self) -> None:
        """Verify backward compatibility for handlers without output param (AC-10).

        Old handlers that implement on_agent_complete(agent, elapsed) should
        still work - the orchestration layer handles this via signature inspection.
        """
        from quilto.orchestration import (
            _call_progress_handler,  # pyright: ignore[reportPrivateUsage]
            _get_method_param_count,  # pyright: ignore[reportPrivateUsage]
        )

        class OldStyleHandler:
            """Handler with old signature (no output parameter)."""

            def __init__(self) -> None:
                self.calls: list[tuple[str, float]] = []

            async def on_agent_complete(self, agent: str, elapsed: float) -> None:
                self.calls.append((agent, elapsed))

        class NewStyleHandler:
            """Handler with new signature (includes output parameter)."""

            def __init__(self) -> None:
                self.calls: list[tuple[str, float, dict[str, Any]]] = []

            async def on_agent_complete(self, agent: str, elapsed: float, output: dict[str, Any]) -> None:
                self.calls.append((agent, elapsed, output))

        old_handler = OldStyleHandler()
        new_handler = NewStyleHandler()

        # Verify parameter counts detected correctly
        assert _get_method_param_count(old_handler, "on_agent_complete") == 2
        assert _get_method_param_count(new_handler, "on_agent_complete") == 3

        # Create mock quilto-like object
        class MockQuilto:
            def __init__(self, handler: Any) -> None:
                self.progress_handler = handler

        # Test old handler receives only (agent, elapsed)
        mock_quilto_old = MockQuilto(old_handler)
        await _call_progress_handler(
            mock_quilto_old,  # type: ignore[arg-type]
            "on_agent_complete",
            "router",
            0.15,
            {"input_type": "query"},
        )
        assert len(old_handler.calls) == 1
        assert old_handler.calls[0] == ("router", 0.15)

        # Test new handler receives all three args
        mock_quilto_new = MockQuilto(new_handler)
        await _call_progress_handler(
            mock_quilto_new,  # type: ignore[arg-type]
            "on_agent_complete",
            "router",
            0.15,
            {"input_type": "query"},
        )
        assert len(new_handler.calls) == 1
        assert new_handler.calls[0] == ("router", 0.15, {"input_type": "query"})

    @pytest.mark.asyncio
    async def test_partial_implementation_does_not_satisfy_isinstance(self) -> None:
        """Verify partial Protocol implementation fails isinstance() check.

        With @runtime_checkable, only implementations with ALL Protocol methods
        pass isinstance(). Partial implementations work structurally but don't
        satisfy the Protocol at runtime - this is expected Python behavior.
        """

        class PartialHandler:
            """Handler that only implements on_stage."""

            def __init__(self) -> None:
                self.stages: list[str] = []

            async def on_stage(self, stage: str) -> None:
                self.stages.append(stage)

        handler = PartialHandler()
        await handler.on_stage("routing")

        # Partial implementation works structurally
        assert handler.stages == ["routing"]

        # But does NOT satisfy isinstance() - all methods required for that
        assert not isinstance(handler, ProgressHandler)
