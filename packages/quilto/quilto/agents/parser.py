"""Parser agent for extracting structured data from raw input.

This module provides the ParserAgent class which converts freeform
user input into structured entries using domain schemas. Supports
multi-domain parsing, vocabulary normalization, and correction mode.
"""

import json
from typing import Any

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

    def _extract_time_from_entry_id(self, entry_id: str) -> str:
        """Extract time (HH:MM) from entry ID.

        Args:
            entry_id: Entry ID in format YYYY-MM-DD_HH-MM-SS.

        Returns:
            Time string in HH:MM format, or "??" if parsing fails.
        """
        try:
            # Entry ID format: YYYY-MM-DD_HH-MM-SS
            if "_" in entry_id:
                time_part = entry_id.split("_")[1]  # HH-MM-SS
                parts = time_part.split("-")
                if len(parts) >= 2:
                    return f"{parts[0]}:{parts[1]}"
        except (IndexError, ValueError):
            pass
        return "??"

    def _extract_domain_summary(self, parsed_data: dict[str, Any] | None) -> str:
        """Extract domain type and key values from parsed data.

        Provides domain-agnostic summary for LLM matching:
        - Domain type (e.g., "STRENGTH", "CARDIO", "NUTRITION")
        - Key values based on domain (exercise name, distance, food items)

        Args:
            parsed_data: Domain-specific parsed data from entry.

        Returns:
            Summary string like "STRENGTH: bench press 80kg" or "UNKNOWN".
        """
        if not parsed_data:
            return "UNKNOWN"

        # Get domain type from first key
        domain_keys = list(parsed_data.keys())
        if not domain_keys:
            return "UNKNOWN"

        domain_type = domain_keys[0].upper()
        domain_data = parsed_data.get(domain_keys[0], {})

        if not isinstance(domain_data, dict):
            return domain_type

        # Extract key values based on common domain patterns
        key_parts: list[str] = []

        # Exercise/activity name (strength, cardio)
        for field in ("exercise", "activity", "type"):
            if value := domain_data.get(field):
                key_parts.append(str(value))
                break

        # Weight (strength)
        if weight := domain_data.get("weight_kg"):
            key_parts.append(f"{weight}kg")

        # Reps/sets (strength)
        reps = domain_data.get("reps")
        sets = domain_data.get("sets")
        if reps and sets:
            key_parts.append(f"{reps}x{sets}")
        elif reps:
            key_parts.append(f"{reps} reps")
        elif sets:
            key_parts.append(f"{sets} sets")

        # Distance (cardio)
        if distance := domain_data.get("distance_km"):
            key_parts.append(f"{distance}km")

        # Duration (cardio)
        if duration := domain_data.get("duration_min"):
            key_parts.append(f"{duration}min")

        # Food items (nutrition)
        items = domain_data.get("items")
        if isinstance(items, list) and items:
            key_parts.append(", ".join(str(i) for i in items[:3]))

        key_summary = " ".join(key_parts) if key_parts else ""
        return f"{domain_type}: {key_summary}" if key_summary else domain_type

    def format_recent_entries(self, entries: list[Any], *, correction_mode: bool = False) -> str:
        """Format recent entries for LLM prompt.

        Enhanced format includes time, domain type, and key values for
        better correction target matching.

        Format: "- {entry_id} | {HH:MM} | {DOMAIN: key_values} | {summary}"

        In correction mode, the full raw_content is preserved (not truncated)
        so the Parser can merge correction with original content.

        Args:
            entries: List of recent Entry objects.
            correction_mode: If True, preserve full raw_content for merging.

        Returns:
            Formatted string with entry summaries, or "(No recent entries)"
            if the entries list is empty.
        """
        if not entries:
            return "(No recent entries)"

        lines: list[str] = []
        for entry in entries:
            entry_id = getattr(entry, "id", "unknown")
            parsed_data = getattr(entry, "parsed_data", None)
            raw_content: str = getattr(entry, "raw_content", "")

            # Extract time from entry_id (format: YYYY-MM-DD_HH-MM-SS)
            time_str = self._extract_time_from_entry_id(entry_id)

            # Extract domain and key values
            domain_summary = self._extract_domain_summary(parsed_data)

            # In correction mode, preserve full raw_content for merge capability
            # Otherwise truncate to 80 chars for context efficiency
            if correction_mode:
                summary = raw_content
            else:
                summary = raw_content[:80] + "..." if len(raw_content) > 80 else raw_content

            # Enhanced format: entry_id | time | domain_summary | content
            lines.append(f"- {entry_id} | {time_str} | {domain_summary} | {summary}")
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
        recent_entries_text = self.format_recent_entries(
            parser_input.recent_entries, correction_mode=parser_input.correction_mode
        )

        # Build correction mode section
        correction_section = ""
        if parser_input.correction_mode:
            correction_target = parser_input.correction_target or "Not specified"
            correction_section = f"""
=== CORRECTION MODE ===

This is a CORRECTION to a previous entry. You MUST:
- Set is_correction = true (this is MANDATORY in correction mode)
- Identify which entry from recent_entries is being corrected
- Set target_entry_id to the identified entry's ID
- Set correction_delta to ONLY the fields that are changing
- The domain_data should contain the full corrected data

=== TARGET IDENTIFICATION ===

Given the correction_target hint: "{correction_target}"

Entry format: "{{entry_id}} | {{HH:MM}} | {{DOMAIN: key_values}} | {{content_summary}}"
- entry_id: Unique ID for the entry (use this for target_entry_id)
- HH:MM: Time of day the entry was created
- DOMAIN: Type of entry (STRENGTH, CARDIO, NUTRITION, etc.)
- key_values: Key data like exercise name, weight, distance, items
- content_summary: Raw text snippet

=== MATCHING PRIORITY ORDER ===

Use this priority when identifying the target entry:
1. EXACT TIME MATCH: If hint mentions a time (e.g., "10:30"), match time in HH:MM column
2. EXERCISE/ACTIVITY KEYWORD: If hint mentions activity (e.g., "running"), match in DOMAIN/key_values
3. VALUE MATCH: If hint mentions numbers (e.g., "5km", "80kg"), match in key_values
4. MOST RECENT: If still ambiguous after above, prefer the most recent entry

=== MATCHING EXAMPLES ===

Example 1 - Exercise match:
  correction_target: "fix the bench press entry"
  recent_entries:
    - 2026-01-26_10-30-00 | 10:30 | CARDIO: treadmill 40min | 40 minutes treadmill...
    - 2026-01-26_18-33-00 | 18:33 | STRENGTH: bench press 80kg | Bench press 80kg...
  CORRECT: target_entry_id = "2026-01-26_18-33-00" (bench press keyword match)

Example 2 - Time match:
  correction_target: "the 10:30 workout"
  recent_entries:
    - 2026-01-26_10-30-00 | 10:30 | CARDIO: treadmill 40min | 40 minutes...
    - 2026-01-26_18-33-00 | 18:33 | STRENGTH: bench press | Bench...
  CORRECT: target_entry_id = "2026-01-26_10-30-00" (10:30 time match)

Example 3 - Running vs Treadmill:
  correction_target: "the running entry" or "the run"
  recent_entries:
    - 2026-01-26_10-30-00 | 10:30 | CARDIO: treadmill 40min | 40 minutes on treadmill...
    - 2026-01-25_09-00-00 | 09:00 | CARDIO: running 3km | Morning run 3km...
  CORRECT: target_entry_id = "2026-01-25_09-00-00" ("running" matches "running" not "treadmill")

Example 4 - Value match:
  correction_target: "where I said 3km"
  recent_entries:
    - 2026-01-26_10-30-00 | 10:30 | CARDIO: treadmill 40min | ...
    - 2026-01-25_09-00-00 | 09:00 | CARDIO: running 3km | ...
  CORRECT: target_entry_id = "2026-01-25_09-00-00" (3km value match)

Example 5 - Ambiguous (return null):
  correction_target: "my workout"
  recent_entries: [2 strength workouts on same day]
  CORRECT: target_entry_id = null
           extraction_notes = ["Ambiguous: 2 strength workouts found, need clarification"]

=== FAILURE GUIDANCE ===

If AMBIGUOUS (multiple entries could match equally well):
- Set target_entry_id = null
- Keep is_correction = true (it IS a correction attempt)
- Add explanation to extraction_notes: "Ambiguous: [describe the conflict]"

If NO MATCH FOUND (no entry matches the hint):
- Set target_entry_id = null
- Keep is_correction = true
- Add explanation to extraction_notes: "No matching entry found for: [hint]"

=== CORRECTION MERGE RULES ===

CRITICAL: When generating raw_content in correction mode, you MUST:
1. MERGE the correction INTO the original entry's raw_content
2. PRESERVE all context from the original that is NOT being corrected
3. OUTPUT a complete standalone description, NOT the literal correction text

The original raw_content of the target entry is provided in recent_entries (full text, not truncated).
Use it as the base, then apply the user's correction to create merged output.

=== CORRECTION MERGE EXAMPLES ===

Example 1 - Value correction:
  original_raw_content: "Ran treadmill for 35 minutes at 8kph"
  correction_input: "actually it was 20 minutes at 7.5kph"
  CORRECT raw_content: "Ran treadmill for 20 minutes at 7.5kph"
  WRONG raw_content: "actually it was 20 minutes at 7.5kph"  ← LOSES CONTEXT

Example 2 - Partial correction:
  original_raw_content: "Did 5 sets of bench press at 80kg, felt strong"
  correction_input: "it was 4 sets not 5"
  CORRECT raw_content: "Did 4 sets of bench press at 80kg, felt strong"
  (preserves weight and notes)

Example 3 - Addition:
  original_raw_content: "Morning run 5km"
  correction_input: "I also did stretching after"
  CORRECT raw_content: "Morning run 5km, followed by stretching"
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
- raw_content: the MERGED content (in correction mode) OR exact input text (in normal mode)
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
        return result
