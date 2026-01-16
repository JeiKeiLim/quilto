"""Global context storage and management.

This module provides classes for persisting and managing
the global user context that Observer generates.
"""

import re
from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from quilto.agents.models import ContextUpdate
from quilto.storage.repository import StorageRepository


class ContextEntry(BaseModel):
    """A single entry in the global context.

    Note: This is DISTINCT from ContextUpdate (agents.models).
    ContextUpdate is the INPUT from Observer.
    ContextEntry is the PERSISTED form with added_date metadata.

    Attributes:
        key: Unique identifier for this entry.
        value: The value to store.
        confidence: Confidence level (certain, likely, tentative).
        source: What triggered this entry.
        category: Entry category.
        added_date: ISO date when first added.

    Example:
        >>> entry = ContextEntry(
        ...     key="unit_preference",
        ...     value="metric",
        ...     confidence="certain",
        ...     source="user_correction: changed lbs to kg",
        ...     category="preference",
        ...     added_date="2026-01-16"
        ... )
    """

    model_config = ConfigDict(strict=True)

    key: str = Field(min_length=1)
    value: str = Field(min_length=1)
    confidence: Literal["certain", "likely", "tentative"]
    source: str = Field(min_length=1)
    category: Literal["preference", "pattern", "fact", "insight"]
    added_date: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}$")

    @field_validator("added_date", mode="after")
    @classmethod
    def validate_added_date(cls, v: str) -> str:
        """Validate added_date is a real date, not just format-valid."""
        date.fromisoformat(v)  # Raises ValueError if invalid
        return v


class GlobalContextFrontmatter(BaseModel):
    """YAML frontmatter for global context file.

    Attributes:
        last_updated: ISO date of last update.
        version: Incremental version number.
        token_estimate: Estimated token count.

    Example:
        >>> fm = GlobalContextFrontmatter(
        ...     last_updated="2026-01-16",
        ...     version=15,
        ...     token_estimate=450
        ... )
    """

    model_config = ConfigDict(strict=True)

    last_updated: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}$")
    version: int = Field(ge=1)
    token_estimate: int = Field(ge=0)

    @field_validator("last_updated", mode="after")
    @classmethod
    def validate_last_updated(cls, v: str) -> str:
        """Validate last_updated is a real date, not just format-valid."""
        date.fromisoformat(v)  # Raises ValueError if invalid
        return v


class GlobalContext(BaseModel):
    """Complete global context with all sections.

    Attributes:
        frontmatter: YAML frontmatter metadata.
        preferences: User preferences (certain confidence).
        patterns: Behavioral patterns (likely confidence).
        facts: Objective facts (certain confidence).
        insights: Observations (tentative confidence).

    Example:
        >>> ctx = GlobalContext(
        ...     frontmatter=GlobalContextFrontmatter(
        ...         last_updated="2026-01-16",
        ...         version=1,
        ...         token_estimate=0
        ...     ),
        ...     preferences=[],
        ...     facts=[]
        ... )
    """

    model_config = ConfigDict(strict=True)

    frontmatter: GlobalContextFrontmatter
    preferences: list[ContextEntry] = Field(default_factory=list)  # pyright: ignore[reportUnknownVariableType]
    patterns: list[ContextEntry] = Field(default_factory=list)  # pyright: ignore[reportUnknownVariableType]
    facts: list[ContextEntry] = Field(default_factory=list)  # pyright: ignore[reportUnknownVariableType]
    insights: list[ContextEntry] = Field(default_factory=list)  # pyright: ignore[reportUnknownVariableType]


class GlobalContextManager:
    """Manager for global context persistence and size management.

    Handles reading, writing, updating, and archiving the global
    context markdown file. Integrates with StorageRepository.

    Attributes:
        storage: StorageRepository instance for file operations.
        token_limit: Maximum tokens before archival (default 2000).

    Example:
        >>> from quilto.storage import StorageRepository
        >>> storage = StorageRepository(Path("/data"))
        >>> manager = GlobalContextManager(storage, token_limit=2000)
        >>> context = manager.read_context()
        >>> updated = manager.apply_updates(observer_output.updates)
    """

    def __init__(self, storage: StorageRepository, token_limit: int = 2000) -> None:
        """Initialize the GlobalContextManager.

        Args:
            storage: StorageRepository for file operations.
            token_limit: Maximum estimated tokens before archival.
        """
        self.storage = storage
        self.token_limit = token_limit

    def _create_default_context(self) -> GlobalContext:
        """Create a default empty context with today's date.

        Returns:
            GlobalContext with default frontmatter and empty sections.
        """
        today = date.today().isoformat()
        return GlobalContext(
            frontmatter=GlobalContextFrontmatter(
                last_updated=today,
                version=1,
                token_estimate=0,
            ),
            preferences=[],
            patterns=[],
            facts=[],
            insights=[],
        )

    def _serialize_context(self, context: GlobalContext) -> str:
        """Serialize GlobalContext to markdown string.

        Args:
            context: The GlobalContext to serialize.

        Returns:
            Markdown string with YAML frontmatter and sections.
        """
        lines: list[str] = []

        # YAML frontmatter
        lines.append("---")
        lines.append(f"last_updated: {context.frontmatter.last_updated}")
        lines.append(f"version: {context.frontmatter.version}")
        lines.append(f"token_estimate: {context.frontmatter.token_estimate}")
        lines.append("---")
        lines.append("")
        lines.append("# Global Context")
        lines.append("")

        # Preferences section
        lines.append("## Preferences (certain)")
        if context.preferences:
            for entry in context.preferences:
                # Format: - [date|confidence|source] key: value
                lines.append(
                    f"- [{entry.added_date}|{entry.confidence}|{entry.source}] "
                    f"{entry.key}: {entry.value}"
                )
        lines.append("")

        # Patterns section
        lines.append("## Patterns (likely)")
        if context.patterns:
            for entry in context.patterns:
                lines.append(
                    f"- [{entry.added_date}|{entry.confidence}|{entry.source}] "
                    f"{entry.key}: {entry.value}"
                )
        lines.append("")

        # Facts section
        lines.append("## Facts (certain)")
        if context.facts:
            for entry in context.facts:
                lines.append(
                    f"- [{entry.added_date}|{entry.confidence}|{entry.source}] "
                    f"{entry.key}: {entry.value}"
                )
        lines.append("")

        # Insights section
        lines.append("## Insights (tentative)")
        if context.insights:
            for entry in context.insights:
                lines.append(
                    f"- [{entry.added_date}|{entry.confidence}|{entry.source}] "
                    f"{entry.key}: {entry.value}"
                )
        lines.append("")

        return "\n".join(lines)

    def _parse_context(self, content: str) -> GlobalContext:
        """Parse markdown content into GlobalContext.

        Args:
            content: Raw markdown content with YAML frontmatter.

        Returns:
            Parsed GlobalContext object.

        Raises:
            ValueError: If frontmatter is invalid or missing.
        """
        if not content.strip():
            return self._create_default_context()

        lines = content.split("\n")

        # Parse YAML frontmatter
        if lines[0].strip() != "---":
            return self._create_default_context()

        frontmatter_end = -1
        for i, line in enumerate(lines[1:], start=1):
            if line.strip() == "---":
                frontmatter_end = i
                break

        if frontmatter_end == -1:
            return self._create_default_context()

        # Extract frontmatter values
        frontmatter_lines = lines[1:frontmatter_end]
        fm_data: dict[str, str | int] = {}
        for line in frontmatter_lines:
            if ":" in line:
                key, value = line.split(":", 1)
                key = key.strip()
                value = value.strip()
                if key in ("version", "token_estimate"):
                    fm_data[key] = int(value)
                else:
                    fm_data[key] = value

        # Create frontmatter with defaults if missing
        try:
            frontmatter = GlobalContextFrontmatter(
                last_updated=str(fm_data.get("last_updated", date.today().isoformat())),
                version=int(fm_data.get("version", 1)),
                token_estimate=int(fm_data.get("token_estimate", 0)),
            )
        except (ValueError, TypeError):
            return self._create_default_context()

        # Parse sections
        body = "\n".join(lines[frontmatter_end + 1 :])
        preferences = self._parse_section(body, "Preferences")
        patterns = self._parse_section(body, "Patterns")
        facts = self._parse_section(body, "Facts")
        insights = self._parse_section(body, "Insights")

        return GlobalContext(
            frontmatter=frontmatter,
            preferences=preferences,
            patterns=patterns,
            facts=facts,
            insights=insights,
        )

    def _parse_section(self, body: str, section_name: str) -> list[ContextEntry]:
        """Parse a section from markdown body into ContextEntry list.

        Args:
            body: Markdown body content (after frontmatter).
            section_name: Section name (Preferences, Patterns, Facts, Insights).

        Returns:
            List of ContextEntry objects from the section.
        """
        entries: list[ContextEntry] = []

        # Map section names to categories and confidence levels
        section_map = {
            "Preferences": ("preference", "certain"),
            "Patterns": ("pattern", "likely"),
            "Facts": ("fact", "certain"),
            "Insights": ("insight", "tentative"),
        }

        if section_name not in section_map:
            return entries

        category, confidence = section_map[section_name]

        # Find section start
        pattern = rf"^## {section_name}.*$"
        match = re.search(pattern, body, re.MULTILINE)
        if not match:
            return entries

        start_idx = match.end()

        # Find next section or end
        next_section = re.search(r"^## ", body[start_idx:], re.MULTILINE)
        section_content = (
            body[start_idx : start_idx + next_section.start()]
            if next_section
            else body[start_idx:]
        )

        # Parse bullet points
        # New format: - [date|confidence|source] key: value
        # Legacy format: - [YYYY-MM-DD] key: value  OR  - key: value
        full_pattern = re.compile(
            r"^\[(\d{4}-\d{2}-\d{2})\|([^|]+)\|([^\]]+)\]\s*(.+)$"
        )
        date_only_pattern = re.compile(r"^\[(\d{4}-\d{2}-\d{2})\]\s*(.+)$")

        for line in section_content.split("\n"):
            line = line.strip()
            if line.startswith("- ") and ":" in line:
                item = line[2:]  # Remove "- "

                # Try new format first: [date|confidence|source]
                full_match = full_pattern.match(item)
                if full_match:
                    added_date = full_match.group(1)
                    parsed_confidence = full_match.group(2)
                    source = full_match.group(3)
                    item = full_match.group(4)
                else:
                    # Try legacy format: [date] only
                    date_match = date_only_pattern.match(item)
                    if date_match:
                        added_date = date_match.group(1)
                        item = date_match.group(2)
                    else:
                        added_date = date.today().isoformat()
                    # Use section default for legacy entries
                    parsed_confidence = confidence
                    source = "parsed_from_file"

                if ":" not in item:
                    continue

                key, value = item.split(":", 1)
                key = key.strip()
                value = value.strip()
                if key and value:
                    entries.append(
                        ContextEntry(
                            key=key,
                            value=value,
                            confidence=parsed_confidence,  # type: ignore[arg-type]
                            source=source,
                            category=category,  # type: ignore[arg-type]
                            added_date=added_date,
                        )
                    )

        return entries

    def read_context(self) -> GlobalContext:
        """Read the global context from storage.

        Returns:
            GlobalContext object (default if file doesn't exist).
        """
        content = self.storage.get_global_context()
        if not content:
            return self._create_default_context()
        return self._parse_context(content)

    def write_context(self, context: GlobalContext) -> None:
        """Write the global context to storage.

        Args:
            context: The GlobalContext to persist.
        """
        markdown = self._serialize_context(context)
        self.storage.update_global_context(markdown)

    def estimate_tokens(self, context: GlobalContext) -> int:
        """Estimate token count for the context.

        Uses word count * 1.3 as approximation.
        This is intentionally simple - not accurate but good enough
        for size management purposes.

        Args:
            context: The GlobalContext to estimate.

        Returns:
            Estimated token count.
        """
        markdown = self._serialize_context(context)
        words = len(markdown.split())
        return int(words * 1.3)

    def _archive_if_needed(self, context: GlobalContext) -> GlobalContext:
        """Archive oldest items if context exceeds token limit.

        Archival priority:
        1. Insights (tentative) - archived first
        2. Patterns (likely) - archived if still over limit
        3. Preferences and Facts - NEVER archived

        Args:
            context: The GlobalContext to check and potentially archive.

        Returns:
            Modified GlobalContext with archived items removed.
        """
        def _entry_date_key(e: ContextEntry) -> str:
            """Sort key for entries by added_date (oldest first)."""
            return e.added_date

        while context.frontmatter.token_estimate > self.token_limit:
            # Try to archive insights first
            if context.insights:
                sorted_insights = sorted(context.insights, key=_entry_date_key)
                to_archive = sorted_insights[0]
                self._write_to_archive([to_archive])
                context.insights = [e for e in context.insights if e.key != to_archive.key]

                # Recalculate token estimate
                context.frontmatter = GlobalContextFrontmatter(
                    last_updated=context.frontmatter.last_updated,
                    version=context.frontmatter.version,
                    token_estimate=self.estimate_tokens(context),
                )
                continue

            # Then try patterns
            if context.patterns:
                sorted_patterns = sorted(context.patterns, key=_entry_date_key)
                to_archive = sorted_patterns[0]
                self._write_to_archive([to_archive])
                context.patterns = [e for e in context.patterns if e.key != to_archive.key]

                context.frontmatter = GlobalContextFrontmatter(
                    last_updated=context.frontmatter.last_updated,
                    version=context.frontmatter.version,
                    token_estimate=self.estimate_tokens(context),
                )
                continue

            # No more archivable items (only preferences/facts left)
            break

        return context

    def _write_to_archive(self, entries: list[ContextEntry]) -> None:
        """Write entries to the archive file.

        Archive file path: logs/context/archive/global-{today}.md
        Appends to existing file if same-day archival.

        Args:
            entries: List of entries to archive.
        """
        today = date.today().isoformat()
        archive_dir = self.storage.base_path / "logs" / "context" / "archive"
        archive_dir.mkdir(parents=True, exist_ok=True)
        archive_path = archive_dir / f"global-{today}.md"

        # Check if archive file exists for today
        if archive_path.exists():
            existing_content = archive_path.read_text(encoding="utf-8")
            lines = existing_content.rstrip("\n").split("\n")
        else:
            # Create new archive with frontmatter
            lines = [
                "---",
                "archived_from: global.md",
                f"archived_date: {today}",
                "reason: size_management",
                "---",
                "",
                f"# Archived Context ({today})",
                "",
                "## Archived Items",
            ]

        # Append entries
        for entry in entries:
            lines.append(f"- [{entry.added_date}] {entry.key}: {entry.value}")

        lines.append("")
        archive_path.write_text("\n".join(lines), encoding="utf-8")

    def apply_updates(self, updates: list[ContextUpdate]) -> GlobalContext:
        """Apply a list of updates to the global context.

        Converts ContextUpdate objects to ContextEntry objects,
        superseding existing entries with matching keys.

        Args:
            updates: List of ContextUpdate objects from Observer.

        Returns:
            Updated GlobalContext object.
        """
        context = self.read_context()
        today = date.today().isoformat()

        for update in updates:
            # Get the appropriate section list
            section_map: dict[str, list[ContextEntry]] = {
                "preference": context.preferences,
                "pattern": context.patterns,
                "fact": context.facts,
                "insight": context.insights,
            }

            section = section_map.get(update.category)
            if section is None:
                continue

            # Check if key exists and update or add
            existing_idx = None
            existing_added_date = today
            for idx, entry in enumerate(section):
                if entry.key == update.key:
                    existing_idx = idx
                    existing_added_date = entry.added_date  # Preserve original date
                    break

            new_entry = ContextEntry(
                key=update.key,
                value=update.value,
                confidence=update.confidence,
                source=update.source,
                category=update.category,
                added_date=existing_added_date,
            )

            if existing_idx is not None:
                section[existing_idx] = new_entry
            else:
                section.append(new_entry)

        # Increment version and update timestamp
        new_version = context.frontmatter.version + 1
        token_estimate = self.estimate_tokens(context)

        context.frontmatter = GlobalContextFrontmatter(
            last_updated=today,
            version=new_version,
            token_estimate=token_estimate,
        )

        # Check archival after token estimation
        context = self._archive_if_needed(context)

        # Write and return
        self.write_context(context)
        return context
