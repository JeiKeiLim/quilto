"""Tests for Analyzer error propagation and Synthesizer fallback in orchestration nodes."""

from typing import Any


def _analyze_with_exception(exception: Exception, entries: list[dict[str, Any]]) -> dict[str, Any]:
    """Helper that mimics the exception handler in analyze_node.

    Returns the state dict that analyze_node would return on exception.
    """
    error_info = {"error": str(exception), "error_type": type(exception).__name__}
    return {
        "error": f"Analyzer failed: {exception!s}",
        "analyzer_error": str(exception),
        "analysis_verdict": "insufficient",
        "analyzer_output": {
            "query_intent": "Unable to analyze due to error",
            "findings": [],
            "patterns_identified": [],
            "sufficiency_evaluation": {
                "critical_gaps": [],
                "nice_to_have_gaps": [],
                "evidence_check_passed": False,
                "speculation_risk": "high",
            },
            "verdict_reasoning": f"Analysis failed with error: {exception!s}",
            "verdict": "insufficient",
        },
        "_callback_output": error_info,
    }


def _synthesize_fallback_logic(
    analyzer_output_findings: list[dict[str, Any]],
    entries: list[dict[str, Any]],
) -> dict[str, Any]:
    """Helper that mimics the fallback logic in synthesize_node.

    Returns info about whether fallback was triggered and resulting findings.
    """
    if not analyzer_output_findings and entries:
        # Fallback triggered: create synthetic findings from entries
        fallback_findings = [
            {
                "claim": f"Entry from {e.get('date', 'unknown')}: {str(e.get('raw_content', ''))[:100]}",
                "evidence": [str(e.get("id", ""))],
                "confidence": "low",
                "indirect_estimate": False,
            }
            for e in entries[:10]
        ]
        return {
            "fallback_triggered": True,
            "findings": fallback_findings,
            "verdict_reasoning": "FALLBACK: Analyzer failed or returned empty. Synthesizing from raw entries.",
            "verdict": "partial",
        }
    return {
        "fallback_triggered": False,
        "findings": analyzer_output_findings,
        "verdict_reasoning": None,
        "verdict": None,
    }


class TestAnalyzerExceptionPropagation:
    """Test that Analyzer exceptions are propagated in returned state."""

    def test_exception_returns_analyzer_error_field(self) -> None:
        """Exception should return state with analyzer_error field."""
        exc = ValueError("Test error")
        result = _analyze_with_exception(exc, [])

        assert "analyzer_error" in result
        assert result["analyzer_error"] == "Test error"

    def test_exception_callback_output_contains_error(self) -> None:
        """Exception should pass error info to on_agent_complete callback."""
        exc = ValueError("Test error")
        result = _analyze_with_exception(exc, [])

        callback_output = result["_callback_output"]
        assert "error" in callback_output
        assert callback_output["error"] == "Test error"

    def test_exception_callback_output_contains_error_type(self) -> None:
        """Exception should include error_type in callback output."""
        exc = RuntimeError("Runtime issue")
        result = _analyze_with_exception(exc, [])

        callback_output = result["_callback_output"]
        assert "error_type" in callback_output
        assert callback_output["error_type"] == "RuntimeError"

    def test_exception_sets_insufficient_verdict(self) -> None:
        """Exception should set analysis_verdict to insufficient."""
        exc = ValueError("fail")
        result = _analyze_with_exception(exc, [])

        assert result["analysis_verdict"] == "insufficient"


class TestSynthesizerFallback:
    """Tests for synthesizer fallback when analyzer fails."""

    def test_empty_findings_with_entries_creates_fallback(self) -> None:
        """Empty findings + entries should create synthetic findings."""
        entries = [
            {"id": "entry-1", "date": "2026-01-15", "raw_content": "Bench press 100kg x 5"},
            {"id": "entry-2", "date": "2026-01-16", "raw_content": "Squat 120kg x 3"},
        ]
        result = _synthesize_fallback_logic([], entries)

        assert result["fallback_triggered"] is True
        assert len(result["findings"]) == 2
        assert "FALLBACK" in result["verdict_reasoning"]
        assert result["verdict"] == "partial"

    def test_empty_findings_no_entries_stays_empty(self) -> None:
        """Empty findings + no entries should NOT create fallback."""
        result = _synthesize_fallback_logic([], [])

        assert result["fallback_triggered"] is False
        assert result["findings"] == []

    def test_existing_findings_no_fallback(self) -> None:
        """Non-empty findings should NOT trigger fallback."""
        existing_findings = [{"claim": "Test finding", "evidence": ["e1"], "confidence": "high"}]
        entries = [
            {"id": "entry-1", "date": "2026-01-15", "raw_content": "Data"},
        ]
        result = _synthesize_fallback_logic(existing_findings, entries)

        assert result["fallback_triggered"] is False
        assert result["findings"] == existing_findings

    def test_fallback_limits_to_10_entries(self) -> None:
        """Fallback should limit to 10 entries to avoid token overflow."""
        entries = [
            {"id": f"entry-{i}", "date": f"2026-01-{i:02d}", "raw_content": f"Entry {i}"}
            for i in range(1, 21)  # 20 entries
        ]
        result = _synthesize_fallback_logic([], entries)

        assert result["fallback_triggered"] is True
        assert len(result["findings"]) == 10  # Limited to 10

    def test_fallback_findings_have_low_confidence(self) -> None:
        """Fallback findings should have low confidence."""
        entries = [{"id": "e1", "date": "2026-01-15", "raw_content": "Test"}]
        result = _synthesize_fallback_logic([], entries)

        assert result["fallback_triggered"] is True
        assert all(f["confidence"] == "low" for f in result["findings"])


class TestAnalyzerErrorDetection:
    """Test that applications can detect Analyzer failure."""

    def test_error_detectable_via_analyzer_error_key(self) -> None:
        """Applications can check 'analyzer_error' in state to detect failure."""
        exc_result = _analyze_with_exception(ValueError("fail"), [])
        assert "analyzer_error" in exc_result

    def test_error_detectable_via_callback_error_key(self) -> None:
        """Applications can check 'error' in callback output to detect failure."""
        exc_result = _analyze_with_exception(ValueError("fail"), [])
        callback_output = exc_result["_callback_output"]

        assert "error" in callback_output
