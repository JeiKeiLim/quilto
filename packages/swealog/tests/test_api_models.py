"""Tests for swealog.api.models module - Pydantic request/response models."""

import pytest
from pydantic import ValidationError
from swealog.api.models import (
    ErrorResponse,
    InputRequest,
    InputResponse,
    QueryRequest,
    QueryResponse,
)


class TestInputRequest:
    """Tests for InputRequest model."""

    def test_valid_input_request(self) -> None:
        """Test creating valid InputRequest."""
        req = InputRequest(text="Did bench press 5x5 at 185 lbs")
        assert req.text == "Did bench press 5x5 at 185 lbs"

    def test_empty_text_raises_error(self) -> None:
        """Test empty text fails validation."""
        with pytest.raises(ValidationError) as exc_info:
            InputRequest(text="")
        assert "string_too_short" in str(exc_info.value)

    def test_whitespace_only_text_passes(self) -> None:
        """Test whitespace-only text passes min_length (backend validates further)."""
        # min_length=1 allows single space, further validation is route's responsibility
        req = InputRequest(text=" ")
        assert req.text == " "


class TestInputResponse:
    """Tests for InputResponse model."""

    def test_full_response(self) -> None:
        """Test creating full InputResponse."""
        resp = InputResponse(
            status="accepted",
            input_type="LOG",
            entry_id="2026-01-15_10-30-00",
            message="Entry logged successfully",
        )
        assert resp.status == "accepted"
        assert resp.input_type == "LOG"
        assert resp.entry_id == "2026-01-15_10-30-00"
        assert resp.message == "Entry logged successfully"

    def test_minimal_response(self) -> None:
        """Test creating minimal InputResponse (no optional fields)."""
        resp = InputResponse(status="accepted", input_type="QUERY", entry_id=None, message=None)
        assert resp.status == "accepted"
        assert resp.input_type == "QUERY"
        assert resp.entry_id is None
        assert resp.message is None

    def test_all_input_types(self) -> None:
        """Test all valid input types."""
        for input_type in ["LOG", "QUERY", "BOTH", "CORRECTION"]:
            resp = InputResponse(status="accepted", input_type=input_type, entry_id=None, message=None)
            assert resp.input_type == input_type


class TestQueryRequest:
    """Tests for QueryRequest model."""

    def test_valid_query_request(self) -> None:
        """Test creating valid QueryRequest."""
        req = QueryRequest(text="How has my bench press progressed?")
        assert req.text == "How has my bench press progressed?"

    def test_empty_query_raises_error(self) -> None:
        """Test empty query text fails validation."""
        with pytest.raises(ValidationError) as exc_info:
            QueryRequest(text="")
        assert "string_too_short" in str(exc_info.value)


class TestQueryResponse:
    """Tests for QueryResponse model."""

    def test_full_response(self) -> None:
        """Test creating full QueryResponse."""
        resp = QueryResponse(
            response="Your bench press has improved by 10 lbs.",
            sources=["2026-01-10_09-00-00", "2026-01-03_10-30-00"],
            confidence=0.85,
            partial=False,
        )
        assert resp.response == "Your bench press has improved by 10 lbs."
        assert len(resp.sources) == 2
        assert resp.confidence == 0.85
        assert resp.partial is False

    def test_partial_response(self) -> None:
        """Test partial response flag."""
        resp = QueryResponse(
            response="Based on limited data...",
            sources=[],
            confidence=0.4,
            partial=True,
        )
        assert resp.partial is True
        assert resp.confidence == 0.4

    def test_confidence_bounds(self) -> None:
        """Test confidence must be between 0 and 1."""
        # Valid bounds
        QueryResponse(response="Test", sources=[], confidence=0.0, partial=False)
        QueryResponse(response="Test", sources=[], confidence=1.0, partial=False)

        # Invalid: below 0
        with pytest.raises(ValidationError) as exc_info:
            QueryResponse(response="Test", sources=[], confidence=-0.1, partial=False)
        assert "greater_than_equal" in str(exc_info.value)

        # Invalid: above 1
        with pytest.raises(ValidationError) as exc_info:
            QueryResponse(response="Test", sources=[], confidence=1.1, partial=False)
        assert "less_than_equal" in str(exc_info.value)

    def test_empty_sources(self) -> None:
        """Test response with no sources."""
        resp = QueryResponse(
            response="No data found.",
            sources=[],
            confidence=0.0,
            partial=True,
        )
        assert resp.sources == []


class TestErrorResponse:
    """Tests for ErrorResponse model."""

    def test_error_response(self) -> None:
        """Test creating ErrorResponse."""
        err = ErrorResponse(error="validation_error", detail="Invalid input format")
        assert err.error == "validation_error"
        assert err.detail == "Invalid input format"

    def test_model_dump(self) -> None:
        """Test ErrorResponse serialization for JSON response."""
        err = ErrorResponse(error="internal_error", detail="Something went wrong")
        data = err.model_dump()
        assert data == {"error": "internal_error", "detail": "Something went wrong"}
