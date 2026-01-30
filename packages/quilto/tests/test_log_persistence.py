"""Integration tests for LOG file creation via parse_node.

Story 23.2: Fix LOG Persistence - Integration tests for AC #5
"""

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from quilto.agents.models import ParserOutput
from quilto.orchestration import QuiltoState, StateKeys, parse_node
from quilto.storage import StorageRepository


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


def create_mock_parser_output(
    raw_content: str = "I did 10 pushups",
    domain_data: dict[str, Any] | None = None,
) -> ParserOutput:
    """Create a mock parser output.

    Args:
        raw_content: Raw user input.
        domain_data: Parsed domain data.

    Returns:
        Valid ParserOutput instance.
    """
    if domain_data is None:
        domain_data = {"fitness": {"exercise": "pushups", "reps": 10}}

    return ParserOutput(
        date=datetime.now(UTC).date(),
        timestamp=datetime.now(UTC),
        domain_data=domain_data,
        raw_content=raw_content,
        confidence=0.9,
        is_correction=False,
    )


class TestLogCreatesRawFile:
    """Tests for raw markdown file creation."""

    @pytest.mark.asyncio
    async def test_log_creates_raw_file(self, tmp_path: Path) -> None:
        """Verify parse_node creates raw markdown file."""
        storage = StorageRepository(tmp_path)
        quilto_mock = MagicMock()
        quilto_mock.storage = storage
        quilto_mock.domains = []
        quilto_mock.llm_client = MagicMock()
        quilto_mock.progress_handler = None

        user_input = "I did 10 pushups"
        parser_output = create_mock_parser_output(raw_content=user_input)

        state = cast(
            QuiltoState,
            {
                StateKeys.QUILTO: quilto_mock,
                StateKeys.USER_INPUT: user_input,
                StateKeys.DOMAIN_CONTEXT: create_valid_domain_context(),
                StateKeys.TRACES: [],
            },
        )

        with patch("quilto.orchestration.ParserAgent") as parser_class:
            mock_parser = AsyncMock()
            mock_parser.parse.return_value = parser_output
            parser_class.return_value = mock_parser

            await parse_node(state)

            # Check raw file was created
            today = datetime.now(UTC).date()
            raw_path = tmp_path / "raw" / str(today.year) / f"{today.month:02d}" / f"{today.strftime('%Y-%m-%d')}.md"
            assert raw_path.exists(), f"Raw file not found at {raw_path}"

            # Verify content
            content = raw_path.read_text()
            assert user_input in content

    @pytest.mark.asyncio
    async def test_log_appends_to_existing_raw_file(self, tmp_path: Path) -> None:
        """Verify parse_node appends to existing raw file."""
        storage = StorageRepository(tmp_path)
        quilto_mock = MagicMock()
        quilto_mock.storage = storage
        quilto_mock.domains = []
        quilto_mock.llm_client = MagicMock()
        quilto_mock.progress_handler = None

        # Create initial raw file
        today = datetime.now(UTC).date()
        raw_dir = tmp_path / "raw" / str(today.year) / f"{today.month:02d}"
        raw_dir.mkdir(parents=True)
        raw_path = raw_dir / f"{today.strftime('%Y-%m-%d')}.md"
        raw_path.write_text("## 08:00\nEarlier entry\n\n")

        user_input = "I ran 5 miles"
        parser_output = create_mock_parser_output(
            raw_content=user_input,
            domain_data={"fitness": {"exercise": "running", "distance": 5}},
        )

        state = cast(
            QuiltoState,
            {
                StateKeys.QUILTO: quilto_mock,
                StateKeys.USER_INPUT: user_input,
                StateKeys.DOMAIN_CONTEXT: create_valid_domain_context(),
                StateKeys.TRACES: [],
            },
        )

        with patch("quilto.orchestration.ParserAgent") as parser_class:
            mock_parser = AsyncMock()
            mock_parser.parse.return_value = parser_output
            parser_class.return_value = mock_parser

            await parse_node(state)

            # Verify both entries exist
            content = raw_path.read_text()
            assert "Earlier entry" in content
            assert user_input in content


class TestLogCreatesParsedJson:
    """Tests for parsed JSON file creation."""

    @pytest.mark.asyncio
    async def test_log_creates_parsed_json(self, tmp_path: Path) -> None:
        """Verify parse_node creates parsed JSON file."""
        storage = StorageRepository(tmp_path)
        quilto_mock = MagicMock()
        quilto_mock.storage = storage
        quilto_mock.domains = []
        quilto_mock.llm_client = MagicMock()
        quilto_mock.progress_handler = None

        user_input = "I did 10 pushups"
        domain_data = {"fitness": {"exercise": "pushups", "reps": 10}}
        parser_output = create_mock_parser_output(raw_content=user_input, domain_data=domain_data)

        state = cast(
            QuiltoState,
            {
                StateKeys.QUILTO: quilto_mock,
                StateKeys.USER_INPUT: user_input,
                StateKeys.DOMAIN_CONTEXT: create_valid_domain_context(),
                StateKeys.TRACES: [],
            },
        )

        with patch("quilto.orchestration.ParserAgent") as parser_class:
            mock_parser = AsyncMock()
            mock_parser.parse.return_value = parser_output
            parser_class.return_value = mock_parser

            await parse_node(state)

            # Check parsed JSON file was created
            today = datetime.now(UTC).date()
            parsed_path = (
                tmp_path / "parsed" / str(today.year) / f"{today.month:02d}" / f"{today.strftime('%Y-%m-%d')}.json"
            )
            assert parsed_path.exists(), f"Parsed file not found at {parsed_path}"

            # Verify content
            parsed_data = json.loads(parsed_path.read_text())
            # There should be at least one entry with our domain data
            assert len(parsed_data) > 0
            entry_id = list(parsed_data.keys())[0]
            assert parsed_data[entry_id] == domain_data

    @pytest.mark.asyncio
    async def test_log_updates_existing_parsed_json(self, tmp_path: Path) -> None:
        """Verify parse_node adds to existing parsed JSON file."""
        storage = StorageRepository(tmp_path)
        quilto_mock = MagicMock()
        quilto_mock.storage = storage
        quilto_mock.domains = []
        quilto_mock.llm_client = MagicMock()
        quilto_mock.progress_handler = None

        # Create initial parsed JSON
        today = datetime.now(UTC).date()
        parsed_dir = tmp_path / "parsed" / str(today.year) / f"{today.month:02d}"
        parsed_dir.mkdir(parents=True)
        parsed_path = parsed_dir / f"{today.strftime('%Y-%m-%d')}.json"
        existing_data = {"existing-entry-id": {"exercise": "squat", "weight": 200}}
        parsed_path.write_text(json.dumps(existing_data))

        # Also create corresponding raw file
        raw_dir = tmp_path / "raw" / str(today.year) / f"{today.month:02d}"
        raw_dir.mkdir(parents=True)
        raw_path = raw_dir / f"{today.strftime('%Y-%m-%d')}.md"
        raw_path.write_text("## 08:00\nSquat 200\n\n")

        user_input = "I did 10 pushups"
        domain_data = {"fitness": {"exercise": "pushups", "reps": 10}}
        parser_output = create_mock_parser_output(raw_content=user_input, domain_data=domain_data)

        state = cast(
            QuiltoState,
            {
                StateKeys.QUILTO: quilto_mock,
                StateKeys.USER_INPUT: user_input,
                StateKeys.DOMAIN_CONTEXT: create_valid_domain_context(),
                StateKeys.TRACES: [],
            },
        )

        with patch("quilto.orchestration.ParserAgent") as parser_class:
            mock_parser = AsyncMock()
            mock_parser.parse.return_value = parser_output
            parser_class.return_value = mock_parser

            await parse_node(state)

            # Verify both entries exist in parsed JSON
            parsed_data = json.loads(parsed_path.read_text())
            assert len(parsed_data) == 2
            assert "existing-entry-id" in parsed_data
            # New entry should be present with domain data
            new_entries = [k for k in parsed_data if k != "existing-entry-id"]
            assert len(new_entries) == 1
            assert parsed_data[new_entries[0]] == domain_data
