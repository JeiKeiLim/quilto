"""Tests for StateKeys constant definitions.

Pyright Typo Detection Example:
    Using StateKeys enables compile-time typo detection. For instance:

    # This typo would silently use default with string literals:
    user_input = state.get("user_imput", "")  # Bug: typo undetected

    # With StateKeys, pyright catches it:
    user_input = state.get(StateKeys.USER_IMPUT, "")
    # Error: "USER_IMPUT" is not a member of "StateKeys"
"""

from typing import Any

from quilto.orchestration import QuiltoState, StateKeys


class TestStateKeysConstants:
    """Tests for StateKeys constant definitions."""

    def test_all_quilto_state_fields_have_constants(self) -> None:
        """Verify StateKeys covers all QuiltoState TypedDict fields."""
        # Get all QuiltoState field names
        state_fields = set(QuiltoState.__annotations__.keys())

        # Get all StateKeys constant values
        constant_values = {
            getattr(StateKeys, name) for name in dir(StateKeys) if name.isupper() and not name.startswith("_")
        }

        # Every QuiltoState field should have a corresponding constant
        missing = state_fields - constant_values
        assert not missing, f"Missing constants for: {missing}"

    def test_constant_values_match_typeddict_keys(self) -> None:
        """Verify constant values are valid string keys."""
        for name in dir(StateKeys):
            if name.isupper() and not name.startswith("_"):
                value = getattr(StateKeys, name)
                assert isinstance(value, str), f"{name} should be a string"

    def test_no_duplicate_constant_values(self) -> None:
        """Verify no two constants have the same value."""
        values: list[str] = []
        for name in dir(StateKeys):
            if name.isupper() and not name.startswith("_"):
                values.append(getattr(StateKeys, name))

        assert len(values) == len(set(values)), "Duplicate constant values found"


class TestStateKeysUsage:
    """Tests for StateKeys usage patterns."""

    def test_state_get_with_constant(self) -> None:
        """Verify state.get() works correctly with constants."""
        state: dict[str, Any] = {"user_input": "test input"}
        result = state.get(StateKeys.USER_INPUT, "")
        assert result == "test input"

    def test_state_get_default_with_constant(self) -> None:
        """Verify default value works with constants."""
        state: dict[str, Any] = {}
        result = state.get(StateKeys.USER_INPUT, "default")
        assert result == "default"

    def test_state_assignment_with_constant(self) -> None:
        """Verify state assignment works with constants."""
        state: dict[str, Any] = {}
        state[StateKeys.USER_INPUT] = "new input"
        assert state["user_input"] == "new input"

    def test_constant_resolves_to_expected_string(self) -> None:
        """Verify key constants resolve to expected string values."""
        assert StateKeys.QUILTO == "_quilto"
        assert StateKeys.USER_INPUT == "user_input"
        assert StateKeys.DOMAIN_CONTEXT == "domain_context"
        assert StateKeys.RETRY_COUNT == "retry_count"
        assert StateKeys.EVAL_VERDICT == "eval_verdict"
