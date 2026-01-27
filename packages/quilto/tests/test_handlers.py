"""Unit tests for quilto/handlers.py ProgressHandler protocol."""

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

            async def on_agent_start(self, agent: str, input_summary: str) -> None:
                self.events.append(("start", agent, input_summary))

            async def on_agent_complete(self, agent: str, elapsed: float) -> None:
                self.events.append(("complete", agent, str(elapsed)))

            async def on_retry(self, attempt: int, reason: str) -> None:
                self.events.append(("retry", str(attempt), reason))

            async def on_stage(self, stage: str) -> None:
                self.events.append(("stage", stage))

        handler = MockProgressHandler()

        # Verify handler implements ProgressHandler protocol
        assert isinstance(handler, ProgressHandler)

        # Test all callback methods
        await handler.on_agent_start("router", "Processing user input")
        await handler.on_agent_complete("router", 0.15)
        await handler.on_retry(1, "Malformed JSON response")
        await handler.on_stage("planning")

        assert len(handler.events) == 4
        assert handler.events[0] == ("start", "router", "Processing user input")
        assert handler.events[1] == ("complete", "router", "0.15")
        assert handler.events[2] == ("retry", "1", "Malformed JSON response")
        assert handler.events[3] == ("stage", "planning")

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
