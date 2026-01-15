"""Domain selector for building ActiveDomainContext from DomainModules.

This module provides the DomainSelector class that bridges Router's
selected_domains output to a merged ActiveDomainContext for downstream agents.
"""

import logging
from collections.abc import Sequence

from quilto.agents.models import ActiveDomainContext, DomainInfo
from quilto.domain import DomainModule

logger = logging.getLogger(__name__)


class DomainSelector:
    """Bridges Router's selected_domains to ActiveDomainContext for downstream agents.

    DomainSelector takes a list of DomainModule instances and provides methods to:
    - Get DomainInfo list for Router input
    - Build merged ActiveDomainContext from Router's selected_domains output

    Attributes:
        domains: Dictionary mapping domain names to DomainModule instances.

    Example:
        >>> selector = DomainSelector([strength_domain, running_domain])
        >>> domain_infos = selector.get_domain_infos()  # For Router
        >>> # After Router returns selected_domains
        >>> context = selector.build_active_context(["strength", "running"])
    """

    def __init__(
        self,
        domains: Sequence[DomainModule],
        base_domain: DomainModule | None = None,
    ) -> None:
        """Initialize DomainSelector with available domains and optional base domain.

        Args:
            domains: Sequence of DomainModule instances to manage.
            base_domain: Optional base domain that is always included in merged context.
                When set, base domain's data is applied FIRST, then selected domains
                are merged on top (later domains override vocabulary conflicts).
        """
        self.domains: dict[str, DomainModule] = {d.name: d for d in domains}
        self.base_domain = base_domain

    def get_domain_infos(self) -> list[DomainInfo]:
        """Get DomainInfo list for Router input.

        Returns:
            List of DomainInfo objects for all registered domains.
        """
        return [
            DomainInfo(name=d.name, description=d.description)
            for d in self.domains.values()
        ]

    def build_active_context(self, selected_domains: list[str]) -> ActiveDomainContext:
        """Build merged context from selected domain names.

        When base_domain is set, it is applied FIRST, then selected domains
        are merged on top. If base_domain is also in selected_domains, it
        appears only once (no duplication).

        Args:
            selected_domains: List of domain names selected by Router.

        Returns:
            ActiveDomainContext with merged data from base (if set) + selected domains.
        """
        selected = [
            self.domains[name] for name in selected_domains if name in self.domains
        ]

        # Build merge list: base_domain first (if set), then selected (deduplicated)
        domains_to_merge: list[DomainModule] = []
        if self.base_domain is not None:
            domains_to_merge.append(self.base_domain)
        for d in selected:
            # Prevent double-merge if base_domain is also selected
            if self.base_domain is None or d.name != self.base_domain.name:
                domains_to_merge.append(d)

        # Build domains_loaded: base_domain.name first (if set), then selected (deduplicated)
        domains_loaded: list[str] = []
        if self.base_domain is not None:
            domains_loaded.append(self.base_domain.name)
        for name in selected_domains:
            if name not in domains_loaded:
                domains_loaded.append(name)

        return ActiveDomainContext(
            domains_loaded=domains_loaded,
            vocabulary=self._merge_vocabularies(domains_to_merge),
            expertise=self._combine_expertise(domains_to_merge),
            evaluation_rules=self._combine_evaluation_rules(domains_to_merge),
            context_guidance=self._combine_context_guidance(domains_to_merge),
            clarification_patterns=self._combine_clarification_patterns(domains_to_merge),
            available_domains=self.get_domain_infos(),
        )

    def _merge_vocabularies(self, domains: list[DomainModule]) -> dict[str, str]:
        """Merge vocabularies from multiple domains.

        Later domains override earlier domains for conflicting keys.
        Logs a warning when conflicts occur.

        Args:
            domains: List of DomainModule instances to merge.

        Returns:
            Merged vocabulary dictionary.
        """
        merged: dict[str, str] = {}
        for domain in domains:
            for key, value in domain.vocabulary.items():
                if key in merged and merged[key] != value:
                    logger.warning(
                        "Vocabulary conflict for '%s': '%s' overrides '%s' "
                        "(from domain '%s')",
                        key,
                        value,
                        merged[key],
                        domain.name,
                    )
                merged[key] = value
        return merged

    def _combine_expertise(self, domains: list[DomainModule]) -> str:
        """Combine expertise strings from multiple domains with labels.

        Args:
            domains: List of DomainModule instances to combine.

        Returns:
            Combined expertise string with domain labels.
        """
        parts = [f"[{d.name}] {d.expertise}" for d in domains if d.expertise]
        return "\n\n".join(parts)

    def _combine_evaluation_rules(self, domains: list[DomainModule]) -> list[str]:
        """Combine evaluation rules from multiple domains.

        Args:
            domains: List of DomainModule instances to combine.

        Returns:
            Combined list of evaluation rules.
        """
        rules: list[str] = []
        for domain in domains:
            rules.extend(domain.response_evaluation_rules)
        return rules

    def _combine_context_guidance(self, domains: list[DomainModule]) -> str:
        """Combine context management guidance from multiple domains.

        Args:
            domains: List of DomainModule instances to combine.

        Returns:
            Combined context guidance string with domain labels.
        """
        parts = [
            f"[{d.name}] {d.context_management_guidance}"
            for d in domains
            if d.context_management_guidance
        ]
        return "\n\n".join(parts)

    def _combine_clarification_patterns(
        self, domains: list[DomainModule]
    ) -> dict[str, list[str]]:
        """Combine clarification patterns from multiple domains.

        Args:
            domains: List of DomainModule instances to combine.

        Returns:
            Merged clarification patterns dictionary.
        """
        merged: dict[str, list[str]] = {}
        for domain in domains:
            for gap_type, questions in domain.clarification_patterns.items():
                if gap_type not in merged:
                    merged[gap_type] = []
                merged[gap_type].extend(questions)
        return merged
