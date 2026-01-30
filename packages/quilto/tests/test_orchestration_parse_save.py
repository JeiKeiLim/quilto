"""Tests for parse_node save_entry behavior.

Story 23.2: Fix LOG Persistence - Unit tests for AC #4
"""

import re
from datetime import UTC, date, datetime
from typing import Any, cast
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from quilto.agents.models import ParserOutput
from quilto.orchestration import QuiltoState, StateKeys, parse_node


def create_mock_quilto(storage_mock: MagicMock) -> MagicMock:
    """Create a mock Quilto instance with storage.

    Args:
        storage_mock: Mock for storage repository.

    Returns:
        Mock Quilto instance.
    """
    quilto = MagicMock()
    quilto.storage = storage_mock
    quilto.domains = []
    quilto.llm_client = MagicMock()
    quilto.progress_handler = None  # Disable progress handler to avoid async issues
    return quilto


def create_valid_domain_context() -> dict[str, Any]:
    """Create a valid domain context dict.

    Returns:
        Valid domain context dictionary.
    """
    return {
        "domains_loaded": ["fitness"],
        "vocabulary": {},
        "expertise": "Fitness expert",
        "evaluation_rules": [],
        "context_guidance": "",
        "available_domains": [],
        "clarification_patterns": {},
    }


def create_mock_parser_output() -> ParserOutput:
    """Create a mock parser output.

    Returns:
        Valid ParserOutput instance.
    """
    return ParserOutput(
        date=date(2026, 1, 30),
        timestamp=datetime(2026, 1, 30, 10, 30, 0, tzinfo=UTC),
        domain_data={"fitness": {"exercise": "pushups", "reps": 10}},
        raw_content="I did 10 pushups",
        confidence=0.9,
        is_correction=False,
    )


class TestParseNodeCallsSaveEntry:
    """Tests for parse_node calling storage.save_entry."""

    @pytest.mark.asyncio
    async def test_parse_node_calls_save_entry(self) -> None:
        """Verify parse_node calls storage.save_entry after parsing."""
        storage_mock = MagicMock()
        quilto_mock = create_mock_quilto(storage_mock)
        parser_output = create_mock_parser_output()

        state = cast(
            QuiltoState,
            {
                StateKeys.QUILTO: quilto_mock,
                StateKeys.USER_INPUT: "I did 10 pushups",
                StateKeys.DOMAIN_CONTEXT: create_valid_domain_context(),
                StateKeys.TRACES: [],
            },
        )

        with patch("quilto.orchestration.ParserAgent") as parser_class:
            mock_parser = AsyncMock()
            mock_parser.parse.return_value = parser_output
            parser_class.return_value = mock_parser

            await parse_node(state)

            storage_mock.save_entry.assert_called_once()

    @pytest.mark.asyncio
    async def test_parse_node_saves_correct_entry_fields(self) -> None:
        """Verify Entry has correct id format, date, timestamp, raw_content, parsed_data."""
        storage_mock = MagicMock()
        quilto_mock = create_mock_quilto(storage_mock)
        parser_output = create_mock_parser_output()

        state = cast(
            QuiltoState,
            {
                StateKeys.QUILTO: quilto_mock,
                StateKeys.USER_INPUT: "I did 10 pushups",
                StateKeys.DOMAIN_CONTEXT: create_valid_domain_context(),
                StateKeys.TRACES: [],
            },
        )

        # Capture expected date before calling parse_node to avoid midnight boundary issues
        expected_date = datetime.now(UTC).date()
        before_call = datetime.now(UTC)

        with patch("quilto.orchestration.ParserAgent") as parser_class:
            mock_parser = AsyncMock()
            mock_parser.parse.return_value = parser_output
            parser_class.return_value = mock_parser

            await parse_node(state)

            after_call = datetime.now(UTC)

            # Get the Entry passed to save_entry
            call_args = storage_mock.save_entry.call_args
            entry = call_args[0][0]

            # Verify ID format: YYYY-MM-DD_HH-MM-SS_xxxxxx
            assert re.match(r"\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}_[a-f0-9]{6}", entry.id)

            # Verify date is within expected range (handles midnight boundary)
            assert entry.date in (expected_date, after_call.date())

            # Verify timestamp is between before and after call
            assert before_call <= entry.timestamp <= after_call

            # Verify raw_content matches user input
            assert entry.raw_content == "I did 10 pushups"

            # Verify parsed_data matches parser output
            assert entry.parsed_data == parser_output.domain_data


class TestParseNodeSaveErrorHandling:
    """Tests for parse_node handling save errors gracefully."""

    @pytest.mark.asyncio
    async def test_parse_node_handles_save_error_gracefully(self) -> None:
        """Verify parse_node still returns successfully when save_entry raises."""
        storage_mock = MagicMock()
        storage_mock.save_entry.side_effect = Exception("Storage write failed")
        quilto_mock = create_mock_quilto(storage_mock)
        parser_output = create_mock_parser_output()

        state = cast(
            QuiltoState,
            {
                StateKeys.QUILTO: quilto_mock,
                StateKeys.USER_INPUT: "I did 10 pushups",
                StateKeys.DOMAIN_CONTEXT: create_valid_domain_context(),
                StateKeys.TRACES: [],
            },
        )

        with patch("quilto.orchestration.ParserAgent") as parser_class:
            mock_parser = AsyncMock()
            mock_parser.parse.return_value = parser_output
            parser_class.return_value = mock_parser

            result = await parse_node(state)

            # Verify parse succeeded despite save failure
            assert StateKeys.ERROR not in result
            assert result[StateKeys.PARSED_DATA] == parser_output.domain_data
            assert result[StateKeys.PARSER_OUTPUT] == parser_output.model_dump()

    @pytest.mark.asyncio
    async def test_parse_node_logs_save_error(self, caplog: pytest.LogCaptureFixture) -> None:
        """Verify save error is logged as warning."""
        storage_mock = MagicMock()
        storage_mock.save_entry.side_effect = Exception("Disk full")
        quilto_mock = create_mock_quilto(storage_mock)
        parser_output = create_mock_parser_output()

        state = cast(
            QuiltoState,
            {
                StateKeys.QUILTO: quilto_mock,
                StateKeys.USER_INPUT: "I did 10 pushups",
                StateKeys.DOMAIN_CONTEXT: create_valid_domain_context(),
                StateKeys.TRACES: [],
            },
        )

        with patch("quilto.orchestration.ParserAgent") as parser_class:
            mock_parser = AsyncMock()
            mock_parser.parse.return_value = parser_output
            parser_class.return_value = mock_parser

            import logging

            with caplog.at_level(logging.WARNING):
                await parse_node(state)

            assert "Failed to save LOG entry to storage" in caplog.text
            assert "Disk full" in caplog.text
