"""Tests for eval_feedback type safety in orchestration nodes."""

from typing import Any


def _safe_get_feedback(eval_feedback: Any) -> str:
    """Helper that mimics the pattern used in orchestration.py."""
    return eval_feedback[0] if isinstance(eval_feedback, list) and eval_feedback else "insufficient"


class TestEvalFeedbackTypeSafety:
    """Test that eval_feedback access handles all edge cases."""

    def test_eval_feedback_none_returns_default(self) -> None:
        """eval_feedback=None should return default value."""
        result = _safe_get_feedback(None)
        assert result == "insufficient"

    def test_eval_feedback_empty_list_returns_default(self) -> None:
        """eval_feedback=[] should return default value."""
        result = _safe_get_feedback([])
        assert result == "insufficient"

    def test_eval_feedback_valid_list_returns_first_element(self) -> None:
        """eval_feedback=['reason'] should return 'reason'."""
        result = _safe_get_feedback(["actual feedback reason"])
        assert result == "actual feedback reason"

    def test_eval_feedback_string_returns_default_not_first_char(self) -> None:
        """eval_feedback='reason' (string) should NOT return 'r'."""
        result = _safe_get_feedback("accidental string")
        # Key assertion: should NOT be "a" (first character of string)
        assert result == "insufficient"
        assert result != "a"
