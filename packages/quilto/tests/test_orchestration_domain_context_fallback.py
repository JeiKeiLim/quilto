"""Tests for defensive domain context validation fallback.

Story 17.8: Add Domain Context Validation Fallback
"""

from typing import Any, cast

import pytest
from quilto.orchestration import (
    QuiltoState,
    StateKeys,
    _get_domain_context_with_fallback,  # type: ignore[reportPrivateUsage]
)


class TestDomainContextFallback:
    """Tests for defensive domain context validation."""

    def test_valid_context_passes_through(self) -> None:
        """Valid domain context is returned unchanged."""
        valid_dict: dict[str, Any] = {
            "domains_loaded": ["fitness"],
            "vocabulary": {"squat": "squat"},
            "expertise": "Fitness expert",
        }
        state = cast(QuiltoState, {StateKeys.DOMAIN_CONTEXT: valid_dict})

        context, was_fallback = _get_domain_context_with_fallback(state, "test")

        assert was_fallback is False
        assert context.domains_loaded == ["fitness"]
        assert context.vocabulary == {"squat": "squat"}
        assert context.expertise == "Fitness expert"

    def test_corrupted_context_triggers_fallback(self, caplog: pytest.LogCaptureFixture) -> None:
        """Corrupted context returns fallback with warning."""
        # Missing required field 'domains_loaded'
        corrupted_dict: dict[str, Any] = {
            "vocabulary": {"squat": "squat"},
            "expertise": "Fitness expert",
        }
        state = cast(QuiltoState, {StateKeys.DOMAIN_CONTEXT: corrupted_dict})

        context, was_fallback = _get_domain_context_with_fallback(state, "test")

        assert was_fallback is True
        assert context.domains_loaded == []
        assert context.vocabulary == {}
        assert "validation failed" in caplog.text.lower()

    def test_empty_context_triggers_fallback(self, caplog: pytest.LogCaptureFixture) -> None:
        """Empty context dict triggers fallback."""
        state = cast(QuiltoState, {StateKeys.DOMAIN_CONTEXT: {}})

        context, was_fallback = _get_domain_context_with_fallback(state, "test")

        assert was_fallback is True
        assert context.expertise == "General assistant"
        assert "validation failed" in caplog.text.lower()

    def test_missing_context_key_triggers_fallback(self, caplog: pytest.LogCaptureFixture) -> None:
        """Missing context key triggers fallback."""
        state = cast(QuiltoState, {})  # No DOMAIN_CONTEXT key

        context, was_fallback = _get_domain_context_with_fallback(state, "test")

        assert was_fallback is True
        assert context.expertise == "General assistant"
        assert "validation failed" in caplog.text.lower()

    def test_wrong_type_triggers_fallback(self, caplog: pytest.LogCaptureFixture) -> None:
        """Wrong type in context dict triggers fallback."""
        # domains_loaded should be list[str], not str
        corrupted_dict: dict[str, Any] = {
            "domains_loaded": "fitness",  # Wrong: should be list
            "vocabulary": {},
            "expertise": "Fitness expert",
        }
        state = cast(QuiltoState, {StateKeys.DOMAIN_CONTEXT: corrupted_dict})

        _, was_fallback = _get_domain_context_with_fallback(state, "test")

        assert was_fallback is True
        assert "validation failed" in caplog.text.lower()

    def test_fallback_returns_minimal_valid_context(self) -> None:
        """Fallback returns minimal valid ActiveDomainContext."""
        state = cast(QuiltoState, {StateKeys.DOMAIN_CONTEXT: {"invalid": "data"}})

        context, was_fallback = _get_domain_context_with_fallback(state, "test")

        assert was_fallback is True
        # Verify minimal valid structure
        assert context.domains_loaded == []
        assert context.vocabulary == {}
        assert context.expertise == "General assistant"
        # Optional fields should have defaults
        assert context.evaluation_rules == []
        assert context.context_guidance == ""
        assert context.available_domains == []
        assert context.clarification_patterns == {}

    def test_caller_name_in_warning_message(self, caplog: pytest.LogCaptureFixture) -> None:
        """Caller name is included in the warning message."""
        state = cast(QuiltoState, {StateKeys.DOMAIN_CONTEXT: {}})

        _get_domain_context_with_fallback(state, "my_special_node")

        assert "my_special_node" in caplog.text
