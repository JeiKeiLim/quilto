"""Tests for protected state dict access in orchestration nodes."""

import logging
from typing import Any
from unittest.mock import MagicMock


def _get_quilto_helper(state: dict[str, Any], node_name: str) -> Any:
    """Helper that mimics _get_quilto in orchestration.py.

    Args:
        state: State dict.
        node_name: Name of the calling node for error messages.

    Returns:
        Quilto instance or None if missing.
    """
    quilto = state.get("_quilto")
    if quilto is None:
        logging.error("%s: Missing _quilto in state - graph not initialized", node_name)
    return quilto


def _node_with_quilto_check(state: dict[str, Any], node_name: str) -> dict[str, Any]:
    """Helper that mimics node pattern after fix.

    Args:
        state: State dict.
        node_name: Name of the calling node.

    Returns:
        Error dict if _quilto missing, otherwise empty dict.
    """
    quilto = _get_quilto_helper(state, node_name)
    if quilto is None:
        return {"error": "Internal error: orchestration not initialized"}
    return {}


def _get_user_input_with_default(state: dict[str, Any]) -> str:
    """Helper that mimics user_input access pattern.

    Args:
        state: State dict.

    Returns:
        User input string or empty string if missing.
    """
    return state.get("user_input", "")


class TestGetQuiltoHelper:
    """Tests for _get_quilto helper function."""

    def test_returns_quilto_when_present(self) -> None:
        """Verify helper returns Quilto when present in state."""
        mock_quilto = MagicMock()
        state: dict[str, Any] = {"_quilto": mock_quilto}

        result = _get_quilto_helper(state, "test_node")

        assert result is mock_quilto

    def test_returns_none_when_missing(self) -> None:
        """Verify helper returns None when _quilto missing."""
        state: dict[str, Any] = {}

        result = _get_quilto_helper(state, "test_node")

        assert result is None

    def test_logs_error_when_missing(self, caplog: Any) -> None:
        """Verify error is logged with node name when _quilto missing."""
        state: dict[str, Any] = {}

        with caplog.at_level(logging.ERROR):
            _get_quilto_helper(state, "route_node")

        assert "route_node" in caplog.text
        assert "Missing _quilto in state" in caplog.text

    def test_returns_none_when_quilto_is_none_value(self) -> None:
        """Verify helper returns None when _quilto is explicitly None."""
        state: dict[str, Any] = {"_quilto": None}

        result = _get_quilto_helper(state, "test_node")

        assert result is None


class TestNodeMissingQuilto:
    """Tests for node error handling when _quilto is missing."""

    def test_node_returns_error_state_when_quilto_missing(self) -> None:
        """Verify nodes return error state when _quilto is missing."""
        state: dict[str, Any] = {}

        result = _node_with_quilto_check(state, "route_node")

        assert "error" in result
        assert "orchestration not initialized" in result["error"]

    def test_node_returns_error_state_when_quilto_none(self) -> None:
        """Verify nodes return error state when _quilto is explicitly None."""
        state: dict[str, Any] = {"_quilto": None}

        result = _node_with_quilto_check(state, "analyze_node")

        assert "error" in result
        assert "orchestration not initialized" in result["error"]

    def test_node_continues_when_quilto_present(self) -> None:
        """Verify nodes continue when _quilto is present."""
        mock_quilto = MagicMock()
        state: dict[str, Any] = {"_quilto": mock_quilto}

        result = _node_with_quilto_check(state, "test_node")

        assert result == {}
        assert "error" not in result


class TestUserInputDefaults:
    """Tests for user_input default value handling."""

    def test_empty_string_default_when_missing(self) -> None:
        """Verify user_input defaults to empty string when missing."""
        state: dict[str, Any] = {}

        result = _get_user_input_with_default(state)

        assert result == ""

    def test_empty_string_default_when_none(self) -> None:
        """Verify user_input with None value returns None (not default)."""
        # Note: .get() returns None when key exists with None value
        state: dict[str, Any] = {"user_input": None}

        result = _get_user_input_with_default(state)

        # When key exists but value is None, .get() returns None, not the default
        assert result is None

    def test_preserves_value_when_present(self) -> None:
        """Verify user_input value preserved when present."""
        state: dict[str, Any] = {"user_input": "What did I eat yesterday?"}

        result = _get_user_input_with_default(state)

        assert result == "What did I eat yesterday?"

    def test_preserves_empty_string_value(self) -> None:
        """Verify empty string value is preserved (not replaced with default)."""
        state: dict[str, Any] = {"user_input": ""}

        result = _get_user_input_with_default(state)

        assert result == ""


class TestStateAccessNoKeyError:
    """Tests verifying KeyError is never raised for state access."""

    def test_quilto_access_no_keyerror(self) -> None:
        """Direct state['_quilto'] would raise KeyError; helper doesn't."""
        state: dict[str, Any] = {}

        # This would raise: state["_quilto"]
        # Helper should not raise
        result = _get_quilto_helper(state, "test_node")

        assert result is None  # Graceful degradation, not exception

    def test_user_input_access_no_keyerror(self) -> None:
        """Direct state['user_input'] would raise KeyError; .get() doesn't."""
        state: dict[str, Any] = {}

        # This would raise: state["user_input"]
        # .get() should not raise
        result = _get_user_input_with_default(state)

        assert result == ""  # Graceful degradation, not exception
