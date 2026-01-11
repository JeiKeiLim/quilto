"""Parser agent for extracting structured data from raw input.

This module provides the ParserAgent class which converts freeform
user input into structured entries using domain schemas. Supports
multi-domain parsing, vocabulary normalization, and correction mode.
"""

import json
from typing import Any, cast

from pydantic import BaseModel

from quilto.agents.models import ParserInput, ParserOutput
from quilto.llm import LLMClient

__all__ = ["ParserAgent"]


class ParserAgent:
    """Parser agent for extracting structured data from raw input.

    Converts freeform user input into structured entries using domain
    schemas. Supports multi-domain parsing, vocabulary normalization,
    and correction mode for updating existing entries.

    Attributes:
        llm_client: The LLM client for making inference calls.

    Example:
        >>> from pathlib import Path
        >>> from datetime import datetime
        >>> from quilto import LLMClient, load_llm_config
        >>> from quilto.agents import ParserAgent, ParserInput
        >>> config = load_llm_config(Path("llm-config.yaml"))
        >>> client = LLMClient(config)
        >>> parser = ParserAgent(client)
        >>> parser_input = ParserInput(
        ...     raw_input="Bench pressed 185x5 today",
        ...     timestamp=datetime.now(),
        ...     domain_schemas={"strength": StrengthSchema},
        ...     vocabulary={"bp": "bench press"},
        ... )
        >>> output = await parser.parse(parser_input)
    """

    AGENT_NAME = "parser"

    def __init__(self, llm_client: LLMClient) -> None:
        """Initialize the Parser agent.

        Args:
            llm_client: LLM client configured with tier settings.
        """
        self.llm_client = llm_client

    def _format_domain_schemas(self, schemas: dict[str, type[BaseModel]]) -> str:
        """Format domain schemas for LLM prompt.

        Args:
            schemas: Map of domain names to Pydantic schema classes.

        Returns:
            Formatted string with JSON schemas for each domain.
        """
        if not schemas:
            return "(No domain schemas provided)"

        descriptions: list[str] = []
        for name, schema_class in schemas.items():
            json_schema = schema_class.model_json_schema()
            descriptions.append(f"### {name}\n{json.dumps(json_schema, indent=2)}")
        return "\n\n".join(descriptions)

    def _format_vocabulary(self, vocabulary: dict[str, str]) -> str:
        """Format vocabulary for LLM prompt.

        Args:
            vocabulary: Term normalization mapping.

        Returns:
            Formatted string with vocabulary entries.
        """
        if not vocabulary:
            return "(No vocabulary provided)"

        lines = [f'- "{term}" -> "{normalized}"' for term, normalized in vocabulary.items()]
        return "\n".join(lines)

    def format_recent_entries(self, entries: list[Any]) -> str:
        """Format recent entries for LLM prompt.

        Public method for testability.

        Args:
            entries: List of recent Entry objects.

        Returns:
            Formatted string with entry summaries.
        """
        if not entries:
            return "(No recent entries)"

        lines: list[str] = []
        for entry in entries:
            # Format: {id}, {date}, {raw_content summary}
            entry_id = getattr(entry, "id", "unknown")
            entry_date = getattr(entry, "date", "unknown")
            raw_content: str = getattr(entry, "raw_content", "")
            summary = raw_content[:50] + "..." if len(raw_content) > 50 else raw_content
            lines.append(f"- {entry_id}, {entry_date}, {summary}")
        return "\n".join(lines)

    def build_prompt(self, parser_input: ParserInput) -> str:
        """Build the system prompt with extraction rules.

        Args:
            parser_input: ParserInput with schemas, vocabulary, and context.

        Returns:
            The formatted system prompt string.
        """
        domain_schemas_text = self._format_domain_schemas(parser_input.domain_schemas)
        vocabulary_text = self._format_vocabulary(parser_input.vocabulary)
        global_context = parser_input.global_context or "(No global context)"
        recent_entries_text = self.format_recent_entries(parser_input.recent_entries)

        # Build correction mode section
        correction_section = ""
        if parser_input.correction_mode:
            correction_section = f"""
=== CORRECTION MODE ===

This is a CORRECTION to a previous entry.
Correction target hint: {parser_input.correction_target or "Not specified"}

IMPORTANT:
- Set is_correction = true
- Identify which entry from recent_entries is being corrected
- Set target_entry_id to the identified entry's ID
- Set correction_delta to ONLY the fields that are changing
- The domain_data should contain the full corrected data
"""

        # Build the full prompt
        return f"""ROLE: You are a structured extraction agent that converts freeform logs into structured data.

TASK: Extract structured data from the user's input using the provided domain schemas.

=== VOCABULARY ===
Use this to normalize terms:
{vocabulary_text}

Example: If user writes "bp", normalize to "bench press" if vocabulary maps it.

=== DOMAIN SCHEMAS ===
Extract data according to these schemas:
{domain_schemas_text}

=== EXTRACTION RULES ===

1. PRESERVE raw input exactly in raw_content field
2. NORMALIZE terms using vocabulary before extraction
3. EXTRACT only what is explicitly stated or clearly implied
4. NEVER invent data that isn't in the input
5. Mark uncertain extractions in uncertain_fields
6. Set confidence based on extraction clarity (0.0 = very uncertain, 1.0 = fully confident)
7. Add extraction_notes for ambiguities or assumptions
8. Extract date from input if mentioned, otherwise use timestamp date
9. Extract any hashtags or keywords as tags

=== MULTI-DOMAIN EXTRACTION ===

If multiple domain schemas are provided, extract independently for each.
An input may match multiple domains (e.g., mentions both activity and meal).
{correction_section}
=== INPUT ===

Raw input: {parser_input.raw_input}
Timestamp: {parser_input.timestamp.isoformat()}
Global context (for inference): {global_context}
Recent entries (for context): {recent_entries_text}

=== OUTPUT (JSON) ===

Respond with a JSON object containing:
- date: "YYYY-MM-DD" format
- timestamp: ISO format datetime string
- tags: list of extracted tags/keywords
- domain_data: dict mapping domain names to extracted data
- raw_content: the exact input text (preserved as-is)
- confidence: number between 0.0 and 1.0
- extraction_notes: list of notes about ambiguities
- uncertain_fields: list of field names with uncertain values
- is_correction: boolean (true if correcting previous entry)
- target_entry_id: string or null (ID of entry being corrected)
- correction_delta: dict or null (only changed fields)"""

    async def parse(self, parser_input: ParserInput) -> ParserOutput:
        """Parse raw input and extract structured data.

        Args:
            parser_input: ParserInput with raw_input, domain_schemas, etc.

        Returns:
            ParserOutput with extracted data per domain.

        Raises:
            ValueError: If raw_input is empty or whitespace-only.
        """
        if not parser_input.raw_input or not parser_input.raw_input.strip():
            raise ValueError("raw_input cannot be empty or whitespace-only")

        system_prompt = self.build_prompt(parser_input)
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": parser_input.raw_input},
        ]

        result = await self.llm_client.complete_structured(
            agent=self.AGENT_NAME,
            messages=messages,
            response_model=ParserOutput,
        )
        return cast(ParserOutput, result)
