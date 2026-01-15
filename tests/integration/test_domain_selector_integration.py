"""Integration tests for DomainSelector with Swealog domains.

Tests the DomainSelector with actual Swealog domain modules (strength, running, nutrition)
and validates end-to-end flow from Router output to ActiveDomainContext.
"""

import pytest
from quilto import DomainModule, DomainSelector
from swealog.domains import nutrition, running, strength


@pytest.fixture
def swealog_domains() -> list[DomainModule]:
    """Return all Swealog fitness domains."""
    return [strength, running, nutrition]


@pytest.fixture
def selector(swealog_domains: list[DomainModule]) -> DomainSelector:
    """Create DomainSelector with Swealog domains."""
    return DomainSelector(swealog_domains)


class TestDomainSelectorWithSwealogDomains:
    """Integration tests using actual Swealog domain modules."""

    def test_get_domain_infos_returns_all_swealog_domains(
        self, selector: DomainSelector
    ) -> None:
        """get_domain_infos includes all Swealog domains."""
        infos = selector.get_domain_infos()

        assert len(infos) == 3
        names = {info.name for info in infos}
        assert names == {"Strength", "Running", "Nutrition"}

    def test_single_domain_strength(self, selector: DomainSelector) -> None:
        """Build context with single strength domain."""
        context = selector.build_active_context(["Strength"])

        assert context.domains_loaded == ["Strength"]
        # Check strength vocabulary is present
        assert "bp" in context.vocabulary
        assert context.vocabulary["bp"] == "bench press"
        # Check strength expertise
        assert "[Strength]" in context.expertise
        assert "progressive overload" in context.expertise
        # Check evaluation rules
        assert len(context.evaluation_rules) > 0
        assert any("1RM" in rule for rule in context.evaluation_rules)

    def test_single_domain_running(self, selector: DomainSelector) -> None:
        """Build context with single running domain."""
        context = selector.build_active_context(["Running"])

        assert context.domains_loaded == ["Running"]
        # Check running vocabulary is present
        assert "[Running]" in context.expertise
        # Running should have pace-related expertise
        assert len(context.evaluation_rules) > 0

    def test_single_domain_nutrition(self, selector: DomainSelector) -> None:
        """Build context with single nutrition domain."""
        context = selector.build_active_context(["Nutrition"])

        assert context.domains_loaded == ["Nutrition"]
        assert "[Nutrition]" in context.expertise
        assert len(context.evaluation_rules) > 0

    def test_multi_domain_strength_and_running(
        self, selector: DomainSelector
    ) -> None:
        """Build context with strength and running domains combined."""
        context = selector.build_active_context(["Strength", "Running"])

        assert context.domains_loaded == ["Strength", "Running"]
        # Expertise from both domains
        assert "[Strength]" in context.expertise
        assert "[Running]" in context.expertise
        # Vocabularies merged
        assert "bp" in context.vocabulary  # From strength
        # Evaluation rules combined
        assert len(context.evaluation_rules) > len(strength.response_evaluation_rules)

    def test_multi_domain_all_three(self, selector: DomainSelector) -> None:
        """Build context with all three domains."""
        context = selector.build_active_context(["Strength", "Running", "Nutrition"])

        assert context.domains_loaded == ["Strength", "Running", "Nutrition"]
        assert "[Strength]" in context.expertise
        assert "[Running]" in context.expertise
        assert "[Nutrition]" in context.expertise
        # All available domains listed
        assert len(context.available_domains) == 3

    def test_clarification_patterns_from_strength(
        self, selector: DomainSelector
    ) -> None:
        """Strength domain clarification patterns are included."""
        context = selector.build_active_context(["Strength"])

        assert "SUBJECTIVE" in context.clarification_patterns
        assert "CLARIFICATION" in context.clarification_patterns
        # Check that strength-specific questions are included
        subjective_questions = context.clarification_patterns["SUBJECTIVE"]
        assert len(subjective_questions) > 0

    def test_clarification_patterns_merged_multi_domain(
        self, selector: DomainSelector
    ) -> None:
        """Clarification patterns from multiple domains are merged."""
        context = selector.build_active_context(["Strength", "Running"])

        # Both domains contribute to clarification patterns
        if "SUBJECTIVE" in context.clarification_patterns:
            # Questions from both domains should be present
            subjective = context.clarification_patterns["SUBJECTIVE"]
            # Should have more questions than single domain
            single_context = selector.build_active_context(["Strength"])
            if "SUBJECTIVE" in single_context.clarification_patterns:
                assert len(subjective) >= len(
                    single_context.clarification_patterns["SUBJECTIVE"]
                )

    def test_empty_selection_has_available_domains(
        self, selector: DomainSelector
    ) -> None:
        """Empty selection still knows about available domains."""
        context = selector.build_active_context([])

        assert context.domains_loaded == []
        assert context.vocabulary == {}
        assert context.expertise == ""
        # But available_domains should list all domains
        assert len(context.available_domains) == 3
        names = {d.name for d in context.available_domains}
        assert names == {"Strength", "Running", "Nutrition"}


class TestRouterOutputIntegration:
    """Tests simulating Router output → DomainSelector flow."""

    def test_router_selected_domains_format(self, selector: DomainSelector) -> None:
        """DomainSelector handles Router's selected_domains format correctly.

        Router outputs: {"selected_domains": ["Strength", "Running"]}
        """
        # Simulated Router output
        router_selected_domains = ["Strength", "Running"]

        context = selector.build_active_context(router_selected_domains)

        assert context.domains_loaded == ["Strength", "Running"]
        assert "[Strength]" in context.expertise
        assert "[Running]" in context.expertise

    def test_router_single_domain_selection(self, selector: DomainSelector) -> None:
        """DomainSelector handles single domain from Router."""
        router_selected_domains = ["Nutrition"]

        context = selector.build_active_context(router_selected_domains)

        assert context.domains_loaded == ["Nutrition"]
        assert "[Nutrition]" in context.expertise

    def test_router_empty_selection(self, selector: DomainSelector) -> None:
        """DomainSelector handles empty selection from Router gracefully."""
        router_selected_domains: list[str] = []

        context = selector.build_active_context(router_selected_domains)

        assert context.domains_loaded == []
        assert len(context.available_domains) == 3  # Still knows all domains
