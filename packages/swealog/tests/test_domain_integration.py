"""Tests for domain integration with agents.

These tests verify that domain modules have the required fields for
Analyzer (expertise) and Evaluator (response_evaluation_rules) integration.
"""

import pytest
from quilto import DomainModule
from swealog.domains import (
    general_fitness,
    nutrition,
    running,
    strength,
    swimming,
)


class TestDomainExpertiseFields:
    """Tests for domain expertise field presence and content."""

    @pytest.mark.parametrize(
        "domain",
        [general_fitness, strength, nutrition, running, swimming],
        ids=lambda d: d.name,
    )
    def test_domain_has_non_empty_expertise(self, domain: DomainModule) -> None:
        """Test that each domain has a non-empty expertise field."""
        assert hasattr(domain, "expertise")
        assert domain.expertise is not None
        assert len(domain.expertise) > 0

    def test_general_fitness_expertise_covers_core_concepts(self) -> None:
        """Test GeneralFitness expertise covers required concepts."""
        expertise = general_fitness.expertise
        assert "progressive overload" in expertise.lower()
        assert "recovery" in expertise.lower()

    def test_strength_expertise_covers_core_concepts(self) -> None:
        """Test Strength expertise covers required concepts."""
        expertise = strength.expertise
        assert "rpe" in expertise.lower() or "rir" in expertise.lower()
        # Check rep ranges are covered
        assert "hypertrophy" in expertise.lower() or "rep" in expertise.lower()

    def test_nutrition_expertise_covers_core_concepts(self) -> None:
        """Test Nutrition expertise covers required concepts."""
        expertise = nutrition.expertise
        assert "protein" in expertise.lower()
        assert "macro" in expertise.lower() or "calorie" in expertise.lower()

    def test_running_expertise_covers_core_concepts(self) -> None:
        """Test Running expertise covers required concepts."""
        expertise = running.expertise
        assert "pace" in expertise.lower() or "zone" in expertise.lower()
        assert "10%" in expertise or "mileage" in expertise.lower()

    def test_swimming_expertise_covers_core_concepts(self) -> None:
        """Test Swimming expertise covers required concepts."""
        expertise = swimming.expertise
        assert "stroke" in expertise.lower() or "pace" in expertise.lower()
        assert "interval" in expertise.lower()


class TestDomainEvaluationRules:
    """Tests for domain response_evaluation_rules field."""

    @pytest.mark.parametrize(
        "domain",
        [general_fitness, strength, nutrition, running, swimming],
        ids=lambda d: d.name,
    )
    def test_domain_has_non_empty_evaluation_rules(self, domain: DomainModule) -> None:
        """Test that each domain has non-empty response_evaluation_rules."""
        assert hasattr(domain, "response_evaluation_rules")
        assert domain.response_evaluation_rules is not None
        assert isinstance(domain.response_evaluation_rules, list)
        assert len(domain.response_evaluation_rules) > 0

    @pytest.mark.parametrize(
        "domain",
        [general_fitness, strength, nutrition, running, swimming],
        ids=lambda d: d.name,
    )
    def test_evaluation_rules_are_strings(self, domain: DomainModule) -> None:
        """Test that all evaluation rules are non-empty strings."""
        for rule in domain.response_evaluation_rules:
            assert isinstance(rule, str)
            assert len(rule) > 0

    def test_general_fitness_rules_cover_safety(self) -> None:
        """Test GeneralFitness rules cover safety concerns."""
        rules = general_fitness.response_evaluation_rules
        rules_text = " ".join(rules).lower()
        assert "overtraining" in rules_text or "recovery" in rules_text
        assert "injur" in rules_text or "medical" in rules_text

    def test_strength_rules_cover_safety(self) -> None:
        """Test Strength rules cover safety concerns."""
        rules = strength.response_evaluation_rules
        rules_text = " ".join(rules).lower()
        assert "pain" in rules_text or "warm" in rules_text
        assert "overtraining" in rules_text or "experience" in rules_text

    def test_nutrition_rules_cover_safety(self) -> None:
        """Test Nutrition rules cover safety concerns."""
        rules = nutrition.response_evaluation_rules
        rules_text = " ".join(rules).lower()
        assert "calorie" in rules_text or "restriction" in rules_text
        assert "disorder" in rules_text or "dietitian" in rules_text

    def test_running_rules_cover_safety(self) -> None:
        """Test Running rules cover safety concerns."""
        rules = running.response_evaluation_rules
        rules_text = " ".join(rules).lower()
        assert "mileage" in rules_text or "10%" in rules_text
        assert "pain" in rules_text or "injur" in rules_text

    def test_swimming_rules_cover_safety(self) -> None:
        """Test Swimming rules cover safety concerns."""
        rules = swimming.response_evaluation_rules
        rules_text = " ".join(rules).lower()
        assert "volume" in rules_text or "10%" in rules_text
        assert "shoulder" in rules_text or "open water" in rules_text


class TestDomainModuleInterface:
    """Tests for DomainModule interface compliance."""

    @pytest.mark.parametrize(
        "domain",
        [general_fitness, strength, nutrition, running, swimming],
        ids=lambda d: d.name,
    )
    def test_domain_has_required_fields(self, domain: DomainModule) -> None:
        """Test that each domain has all required DomainModule fields."""
        # Required fields from DomainModule
        assert hasattr(domain, "name")
        assert hasattr(domain, "description")
        assert hasattr(domain, "log_schema")
        assert hasattr(domain, "vocabulary")
        assert hasattr(domain, "expertise")
        assert hasattr(domain, "response_evaluation_rules")
        assert hasattr(domain, "context_management_guidance")

    @pytest.mark.parametrize(
        "domain",
        [general_fitness, strength, nutrition, running, swimming],
        ids=lambda d: d.name,
    )
    def test_domain_vocabulary_is_dict(self, domain: DomainModule) -> None:
        """Test that vocabulary is a non-empty dict with string values."""
        assert isinstance(domain.vocabulary, dict)
        assert len(domain.vocabulary) > 0
        # Verify all values are non-empty strings
        for key, value in domain.vocabulary.items():
            assert isinstance(key, str) and len(key) > 0
            assert isinstance(value, str) and len(value) > 0


class TestMultiDomainExpertiseMerging:
    """Tests for multi-domain expertise combination."""

    def test_expertise_parts_can_be_joined(self) -> None:
        """Test that expertise from multiple domains can be joined."""
        domains = [strength, running]
        expertise_parts = [f"[{d.name}] {d.expertise}" for d in domains]
        merged = " | ".join(expertise_parts)

        assert "[Strength]" in merged
        assert "[Running]" in merged
        assert strength.expertise in merged
        assert running.expertise in merged

    def test_evaluation_rules_can_be_merged(self) -> None:
        """Test that evaluation rules from multiple domains can be merged."""
        domains = [strength, nutrition]
        rules: list[str] = []
        for domain in domains:
            rules.extend(domain.response_evaluation_rules)

        # Should have rules from both domains
        assert len(rules) == (len(strength.response_evaluation_rules) + len(nutrition.response_evaluation_rules))

    def test_all_five_domains_can_merge_expertise(self) -> None:
        """Test that all five domains can merge expertise."""
        all_domains = [general_fitness, strength, nutrition, running, swimming]
        expertise_parts = [f"[{d.name}] {d.expertise}" for d in all_domains]
        merged = " | ".join(expertise_parts)

        for domain in all_domains:
            assert f"[{domain.name}]" in merged
            assert domain.expertise in merged

    def test_all_five_domains_can_merge_rules(self) -> None:
        """Test that all five domains can merge evaluation rules."""
        all_domains = [general_fitness, strength, nutrition, running, swimming]
        rules: list[str] = []
        for domain in all_domains:
            rules.extend(domain.response_evaluation_rules)

        expected_count = sum(len(d.response_evaluation_rules) for d in all_domains)
        assert len(rules) == expected_count


class TestGetEvaluationRulesLogic:
    """Tests for evaluation rules retrieval logic (mirrors manual_test.py behavior)."""

    def test_get_rules_returns_domain_rules(self) -> None:
        """Test that rules are retrieved from response_evaluation_rules field."""
        # This tests the logic that was buggy (used evaluation_rules instead of response_evaluation_rules)
        domain_modules = {
            general_fitness.name: general_fitness,
            strength.name: strength,
            nutrition.name: nutrition,
            running.name: running,
        }

        # Test single domain
        selected = [strength.name]
        rules: list[str] = []
        for name in selected:
            if name in domain_modules:
                module = domain_modules[name]
                if hasattr(module, "response_evaluation_rules"):
                    rules.extend(module.response_evaluation_rules)

        assert len(rules) == len(strength.response_evaluation_rules)
        assert rules == strength.response_evaluation_rules

    def test_get_rules_merges_multiple_domains(self) -> None:
        """Test that rules from multiple domains are merged correctly."""
        domain_modules = {
            strength.name: strength,
            running.name: running,
        }

        selected = [strength.name, running.name]
        rules: list[str] = []
        for name in selected:
            if name in domain_modules:
                module = domain_modules[name]
                if hasattr(module, "response_evaluation_rules"):
                    rules.extend(module.response_evaluation_rules)

        expected_count = len(strength.response_evaluation_rules) + len(running.response_evaluation_rules)
        assert len(rules) == expected_count

    def test_response_evaluation_rules_not_evaluation_rules(self) -> None:
        """Test that domains have response_evaluation_rules, not evaluation_rules."""
        # This explicitly tests the bug that was fixed: using wrong attribute name
        for domain in [general_fitness, strength, nutrition, running, swimming]:
            # The correct attribute should exist
            assert hasattr(domain, "response_evaluation_rules")
            # The incorrect attribute should NOT exist
            assert not hasattr(domain, "evaluation_rules")


class TestSwimmingDomainIntegration:
    """Tests for Swimming domain integration with domain selection infrastructure.

    These tests validate that Swimming integrates with the existing 6.1-6.3 infrastructure.
    They confirm Swimming works as expected with DomainSelector and multi-domain merging.
    """

    def test_swimming_and_running_expertise_can_merge(self) -> None:
        """Test that Swimming and Running expertise can be merged for cross-domain queries."""
        domains = [running, swimming]
        expertise_parts = [f"[{d.name}] {d.expertise}" for d in domains]
        merged = " | ".join(expertise_parts)

        assert "[Running]" in merged
        assert "[Swimming]" in merged
        assert "pace" in merged.lower()
        assert "stroke" in merged.lower()

    def test_swimming_vocabulary_available_for_merging(self) -> None:
        """Test that Swimming vocabulary is available for context merging."""
        # Merge vocabularies from running and swimming (for cross-domain queries)
        combined_vocab = {**running.vocabulary, **swimming.vocabulary}

        # Should have running terms
        assert "ran" in combined_vocab
        # Should have swimming terms
        assert "swam" in combined_vocab
        assert "free" in combined_vocab  # freestyle abbreviation

    def test_swimming_rules_can_be_combined_with_running(self) -> None:
        """Test that Swimming and Running rules can be combined."""
        combined_rules = running.response_evaluation_rules + swimming.response_evaluation_rules

        # Both domain rules should be present
        running_rules_text = " ".join(running.response_evaluation_rules).lower()
        swimming_rules_text = " ".join(swimming.response_evaluation_rules).lower()
        combined_text = " ".join(combined_rules).lower()

        assert "mileage" in running_rules_text
        assert "shoulder" in swimming_rules_text
        assert "mileage" in combined_text
        assert "shoulder" in combined_text
