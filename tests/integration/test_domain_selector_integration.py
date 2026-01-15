"""Integration tests for DomainSelector with Swealog domains.

Tests the DomainSelector with actual Swealog domain modules (strength, running, nutrition)
and validates end-to-end flow from Router output to ActiveDomainContext.
"""

import pytest
from quilto import DomainModule, DomainSelector
from swealog.domains import general_fitness, nutrition, running, strength


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


class TestBaseDomainWithSwealogDomains:
    """Integration tests for base_domain with actual Swealog domains.

    Tests Story 6.2: Multi-Domain Combination with general_fitness as base domain.
    """

    @pytest.fixture
    def swealog_domains_with_base(self) -> list[DomainModule]:
        """Return Swealog domains including general_fitness."""
        return [general_fitness, strength, running, nutrition]

    @pytest.fixture
    def selector_with_base(
        self, swealog_domains_with_base: list[DomainModule]
    ) -> DomainSelector:
        """Create DomainSelector with general_fitness as base domain."""
        return DomainSelector(
            swealog_domains_with_base, base_domain=general_fitness
        )

    def test_base_domain_general_fitness_with_strength_selected(
        self, selector_with_base: DomainSelector
    ) -> None:
        """general_fitness as base + strength as selected merges correctly."""
        context = selector_with_base.build_active_context(["Strength"])

        # domains_loaded has base first
        assert context.domains_loaded == ["GeneralFitness", "Strength"]
        # Vocabulary from both domains
        assert "workout" in context.vocabulary  # From general_fitness
        assert "bp" in context.vocabulary  # From strength
        # Expertise from both domains
        assert "[GeneralFitness]" in context.expertise
        assert "[Strength]" in context.expertise
        # GeneralFitness expertise comes first
        gf_pos = context.expertise.find("[GeneralFitness]")
        strength_pos = context.expertise.find("[Strength]")
        assert gf_pos < strength_pos

    def test_merged_vocabulary_from_base_and_selected(
        self, selector_with_base: DomainSelector
    ) -> None:
        """Merged context has vocabulary from both general_fitness and strength."""
        context = selector_with_base.build_active_context(["Strength"])

        # General fitness vocabulary
        assert "workout" in context.vocabulary
        assert "cardio" in context.vocabulary
        assert "pr" in context.vocabulary  # Personal record
        # Strength vocabulary
        assert "bp" in context.vocabulary
        assert context.vocabulary["bp"] == "bench press"

    def test_merged_expertise_from_base_and_selected(
        self, selector_with_base: DomainSelector
    ) -> None:
        """Merged context has expertise from both domains with correct labels."""
        context = selector_with_base.build_active_context(["Strength"])

        # Both domain labels present
        assert "[GeneralFitness]" in context.expertise
        assert "[Strength]" in context.expertise
        # Content from both domains
        assert "progressive overload" in context.expertise  # Common fitness principle
        # Strength-specific content
        assert any(
            term in context.expertise.lower()
            for term in ["1rm", "bench", "squat", "deadlift", "rep", "set"]
        )

    def test_deduplication_when_general_fitness_both_base_and_selected(
        self, selector_with_base: DomainSelector
    ) -> None:
        """When general_fitness is both base AND selected, it appears only once."""
        context = selector_with_base.build_active_context(
            ["GeneralFitness", "Strength"]
        )

        # GeneralFitness appears only once in domains_loaded
        assert context.domains_loaded == ["GeneralFitness", "Strength"]
        assert context.domains_loaded.count("GeneralFitness") == 1
        # Expertise label also appears only once
        assert context.expertise.count("[GeneralFitness]") == 1

    def test_base_domain_with_multiple_selected_domains(
        self, selector_with_base: DomainSelector
    ) -> None:
        """Base domain + multiple selected domains merges correctly."""
        context = selector_with_base.build_active_context(["Strength", "Running"])

        # All three domains in domains_loaded (base + 2 selected)
        assert context.domains_loaded == ["GeneralFitness", "Strength", "Running"]
        # All three expertise labels
        assert "[GeneralFitness]" in context.expertise
        assert "[Strength]" in context.expertise
        assert "[Running]" in context.expertise

    def test_evaluation_rules_from_base_and_selected(
        self, selector_with_base: DomainSelector
    ) -> None:
        """Evaluation rules from both base and selected domains are combined."""
        context = selector_with_base.build_active_context(["Strength"])

        # Rules from general_fitness
        assert any(
            "injury" in rule.lower() or "recovery" in rule.lower()
            for rule in context.evaluation_rules
        )
        # Rules from strength
        assert any("1RM" in rule for rule in context.evaluation_rules)

    def test_clarification_patterns_from_base_and_selected(
        self, selector_with_base: DomainSelector
    ) -> None:
        """Clarification patterns from both domains are combined."""
        context = selector_with_base.build_active_context(["Strength"])

        # Should have patterns from both domains
        assert "SUBJECTIVE" in context.clarification_patterns
        subjective = context.clarification_patterns["SUBJECTIVE"]
        # Should have more questions than single domain alone
        assert len(subjective) > 0

    def test_backward_compatible_selector_without_base(
        self, swealog_domains_with_base: list[DomainModule]
    ) -> None:
        """Selector without base_domain works identically to Story 6.1."""
        selector_no_base = DomainSelector(swealog_domains_with_base)
        context = selector_no_base.build_active_context(["Strength"])

        # Only Strength in domains_loaded (no GeneralFitness base)
        assert context.domains_loaded == ["Strength"]
        assert "[GeneralFitness]" not in context.expertise
        assert "[Strength]" in context.expertise
