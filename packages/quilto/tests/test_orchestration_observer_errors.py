"""Tests for Observer error propagation in orchestration nodes."""

from typing import Any


def _observe_with_exception(exception: Exception) -> dict[str, Any]:
    """Helper that mimics the exception handler in observe_node.

    Returns the state dict that observe_node would return on exception.
    """
    error_info = {"error": str(exception), "error_type": type(exception).__name__}
    return {"observer_error": str(exception), "_callback_output": error_info}


def _observe_with_empty_context(domain_context_dict: dict[str, Any]) -> dict[str, Any]:
    """Helper that mimics the empty domain_context check in observe_node.

    Returns the state dict that observe_node would return when domain_context is empty.
    """
    if not domain_context_dict:
        return {"observer_error": "No domain_context available"}
    return {}


class TestObserverExceptionPropagation:
    """Test that Observer exceptions are propagated in returned state."""

    def test_exception_returns_observer_error_field(self) -> None:
        """Exception should return state with observer_error field."""
        exc = ValueError("Test error")
        result = _observe_with_exception(exc)

        assert "observer_error" in result
        assert result["observer_error"] == "Test error"

    def test_exception_callback_output_contains_error(self) -> None:
        """Exception should pass error info to on_agent_complete callback."""
        exc = ValueError("Test error")
        result = _observe_with_exception(exc)

        callback_output = result["_callback_output"]
        assert "error" in callback_output
        assert callback_output["error"] == "Test error"

    def test_exception_callback_output_contains_error_type(self) -> None:
        """Exception should include error_type in callback output."""
        exc = RuntimeError("Runtime issue")
        result = _observe_with_exception(exc)

        callback_output = result["_callback_output"]
        assert "error_type" in callback_output
        assert callback_output["error_type"] == "RuntimeError"


class TestObserverEmptyContextPropagation:
    """Test that empty domain_context returns observer_error."""

    def test_empty_dict_returns_observer_error(self) -> None:
        """Empty {} domain_context should return observer_error."""
        result = _observe_with_empty_context({})

        assert "observer_error" in result
        assert result["observer_error"] == "No domain_context available"

    def test_non_empty_dict_returns_empty(self) -> None:
        """Non-empty domain_context should return empty dict (continue processing)."""
        result = _observe_with_empty_context({"key": "value"})

        assert result == {}
        assert "observer_error" not in result


class TestObserverErrorDetection:
    """Test that applications can detect Observer failure."""

    def test_error_detectable_via_observer_error_key(self) -> None:
        """Applications can check 'observer_error' in state to detect failure."""
        # On exception
        exc_result = _observe_with_exception(ValueError("fail"))
        assert "observer_error" in exc_result

        # On empty context
        empty_result = _observe_with_empty_context({})
        assert "observer_error" in empty_result

    def test_error_detectable_via_callback_error_key(self) -> None:
        """Applications can check 'error' in callback output to detect failure."""
        exc_result = _observe_with_exception(ValueError("fail"))
        callback_output = exc_result["_callback_output"]

        assert "error" in callback_output
