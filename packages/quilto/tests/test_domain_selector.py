"""Unit tests for DomainSelector.

Tests the domain selection and ActiveDomainContext building functionality.
"""

import logging

import pytest
from pydantic import BaseModel
from quilto import DomainModule, DomainSelector


class MockSchema(BaseModel):
    """Simple schema for testing."""

    value: str | None = None


@pytest.fixture
def domain_a() -> DomainModule:
    """Create test domain A with full fields."""
    return DomainModule(
        name="domain_a",
        description="Domain A for testing",
        log_schema=MockSchema,
        vocabulary={"term1": "value1", "common": "a_value"},
        expertise="Domain A expertise",
        response_evaluation_rules=["Rule A1", "Rule A2"],
        context_management_guidance="Guidance for domain A",
        clarification_patterns={
            "SUBJECTIVE": ["How do you feel about A?"],
            "CLARIFICATION": ["Which A option?"],
        },
    )


@pytest.fixture
def domain_b() -> DomainModule:
    """Create test domain B with full fields."""
    return DomainModule(
        name="domain_b",
        description="Domain B for testing",
        log_schema=MockSchema,
        vocabulary={"term2": "value2", "common": "b_value"},
        expertise="Domain B expertise",
        response_evaluation_rules=["Rule B1"],
        context_management_guidance="Guidance for domain B",
        clarification_patterns={
            "SUBJECTIVE": ["How do you feel about B?"],
            "CLARIFICATION": ["Which B option?"],
        },
    )


@pytest.fixture
def empty_domain() -> DomainModule:
    """Create test domain with empty optional fields."""
    return DomainModule(
        name="empty_domain",
        description="Empty domain for testing",
        log_schema=MockSchema,
        vocabulary={},
        expertise="",
        response_evaluation_rules=[],
        context_management_guidance="",
        clarification_patterns={},
    )


class TestDomainSelectorInit:
    """Tests for DomainSelector initialization."""

    def test_init_with_domains(self, domain_a: DomainModule) -> None:
        """DomainSelector stores domains by name."""
        selector = DomainSelector([domain_a])
        assert "domain_a" in selector.domains
        assert selector.domains["domain_a"] is domain_a

    def test_init_with_multiple_domains(
        self, domain_a: DomainModule, domain_b: DomainModule
    ) -> None:
        """DomainSelector stores multiple domains."""
        selector = DomainSelector([domain_a, domain_b])
        assert len(selector.domains) == 2
        assert "domain_a" in selector.domains
        assert "domain_b" in selector.domains

    def test_init_empty_list(self) -> None:
        """DomainSelector accepts empty domain list."""
        selector = DomainSelector([])
        assert len(selector.domains) == 0


class TestGetDomainInfos:
    """Tests for get_domain_infos method."""

    def test_get_domain_infos_returns_correct_list(
        self, domain_a: DomainModule, domain_b: DomainModule
    ) -> None:
        """get_domain_infos returns DomainInfo for all domains."""
        selector = DomainSelector([domain_a, domain_b])
        infos = selector.get_domain_infos()

        assert len(infos) == 2
        names = {info.name for info in infos}
        assert names == {"domain_a", "domain_b"}

    def test_get_domain_infos_includes_description(
        self, domain_a: DomainModule
    ) -> None:
        """get_domain_infos includes domain descriptions."""
        selector = DomainSelector([domain_a])
        infos = selector.get_domain_infos()

        assert infos[0].name == "domain_a"
        assert infos[0].description == "Domain A for testing"

    def test_get_domain_infos_empty_selector(self) -> None:
        """get_domain_infos returns empty list for empty selector."""
        selector = DomainSelector([])
        infos = selector.get_domain_infos()
        assert infos == []


class TestBuildActiveContextSingleDomain:
    """Tests for build_active_context with single domain."""

    def test_single_domain_selection(self, domain_a: DomainModule) -> None:
        """build_active_context works with single domain."""
        selector = DomainSelector([domain_a])
        context = selector.build_active_context(["domain_a"])

        assert context.domains_loaded == ["domain_a"]
        assert context.vocabulary == {"term1": "value1", "common": "a_value"}
        assert "[domain_a] Domain A expertise" in context.expertise
        assert context.evaluation_rules == ["Rule A1", "Rule A2"]
        assert "[domain_a] Guidance for domain A" in context.context_guidance

    def test_single_domain_clarification_patterns(
        self, domain_a: DomainModule
    ) -> None:
        """Single domain clarification patterns are included."""
        selector = DomainSelector([domain_a])
        context = selector.build_active_context(["domain_a"])

        assert "SUBJECTIVE" in context.clarification_patterns
        assert "How do you feel about A?" in context.clarification_patterns["SUBJECTIVE"]


class TestBuildActiveContextMultipleDomains:
    """Tests for build_active_context with multiple domains."""

    def test_multiple_domains_selection(
        self, domain_a: DomainModule, domain_b: DomainModule
    ) -> None:
        """build_active_context works with multiple domains."""
        selector = DomainSelector([domain_a, domain_b])
        context = selector.build_active_context(["domain_a", "domain_b"])

        assert context.domains_loaded == ["domain_a", "domain_b"]
        assert "term1" in context.vocabulary
        assert "term2" in context.vocabulary

    def test_multiple_domains_expertise_combined(
        self, domain_a: DomainModule, domain_b: DomainModule
    ) -> None:
        """Expertise from multiple domains is combined with labels."""
        selector = DomainSelector([domain_a, domain_b])
        context = selector.build_active_context(["domain_a", "domain_b"])

        assert "[domain_a] Domain A expertise" in context.expertise
        assert "[domain_b] Domain B expertise" in context.expertise

    def test_multiple_domains_evaluation_rules_combined(
        self, domain_a: DomainModule, domain_b: DomainModule
    ) -> None:
        """Evaluation rules from multiple domains are combined."""
        selector = DomainSelector([domain_a, domain_b])
        context = selector.build_active_context(["domain_a", "domain_b"])

        assert "Rule A1" in context.evaluation_rules
        assert "Rule A2" in context.evaluation_rules
        assert "Rule B1" in context.evaluation_rules

    def test_multiple_domains_clarification_patterns_merged(
        self, domain_a: DomainModule, domain_b: DomainModule
    ) -> None:
        """Clarification patterns from multiple domains are merged."""
        selector = DomainSelector([domain_a, domain_b])
        context = selector.build_active_context(["domain_a", "domain_b"])

        assert "SUBJECTIVE" in context.clarification_patterns
        subjective = context.clarification_patterns["SUBJECTIVE"]
        assert "How do you feel about A?" in subjective
        assert "How do you feel about B?" in subjective


class TestBuildActiveContextEmptySelection:
    """Tests for build_active_context with empty selection."""

    def test_empty_selection(
        self, domain_a: DomainModule, domain_b: DomainModule
    ) -> None:
        """build_active_context handles empty selection gracefully."""
        selector = DomainSelector([domain_a, domain_b])
        context = selector.build_active_context([])

        assert context.domains_loaded == []
        assert context.vocabulary == {}
        assert context.expertise == ""
        assert context.evaluation_rules == []
        assert context.context_guidance == ""
        assert context.clarification_patterns == {}

    def test_empty_selection_still_has_available_domains(
        self, domain_a: DomainModule
    ) -> None:
        """Empty selection still includes available_domains."""
        selector = DomainSelector([domain_a])
        context = selector.build_active_context([])

        assert len(context.available_domains) == 1
        assert context.available_domains[0].name == "domain_a"


class TestBuildActiveContextWithEmptyFields:
    """Tests for build_active_context with domains having empty optional fields."""

    def test_empty_optional_fields_handled(
        self, empty_domain: DomainModule
    ) -> None:
        """Domains with empty optional fields work correctly."""
        selector = DomainSelector([empty_domain])
        context = selector.build_active_context(["empty_domain"])

        assert context.domains_loaded == ["empty_domain"]
        assert context.vocabulary == {}
        assert context.expertise == ""
        assert context.evaluation_rules == []
        assert context.context_guidance == ""
        assert context.clarification_patterns == {}

    def test_mixed_empty_and_full_domains(
        self, domain_a: DomainModule, empty_domain: DomainModule
    ) -> None:
        """Mixed domains with empty and full fields work correctly."""
        selector = DomainSelector([domain_a, empty_domain])
        context = selector.build_active_context(["domain_a", "empty_domain"])

        # Full domain's content should be present
        assert "term1" in context.vocabulary
        assert "[domain_a] Domain A expertise" in context.expertise
        # Empty domain shouldn't add empty entries
        assert "[empty_domain]" not in context.expertise


class TestVocabularyMerging:
    """Tests for vocabulary merging logic."""

    def test_no_conflict_merge(
        self, domain_a: DomainModule, domain_b: DomainModule
    ) -> None:
        """Non-conflicting vocabularies merge correctly."""
        selector = DomainSelector([domain_a, domain_b])
        context = selector.build_active_context(["domain_a", "domain_b"])

        assert context.vocabulary["term1"] == "value1"
        assert context.vocabulary["term2"] == "value2"

    def test_conflict_later_overrides(
        self, domain_a: DomainModule, domain_b: DomainModule
    ) -> None:
        """Later domain's vocabulary value wins on conflict."""
        selector = DomainSelector([domain_a, domain_b])
        context = selector.build_active_context(["domain_a", "domain_b"])

        # domain_b processed after domain_a, so b_value wins
        assert context.vocabulary["common"] == "b_value"

    def test_conflict_logs_warning(
        self,
        domain_a: DomainModule,
        domain_b: DomainModule,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Vocabulary conflict logs a warning."""
        selector = DomainSelector([domain_a, domain_b])

        with caplog.at_level(logging.WARNING):
            selector.build_active_context(["domain_a", "domain_b"])

        assert "Vocabulary conflict for 'common'" in caplog.text
        assert "'b_value' overrides 'a_value'" in caplog.text


class TestUnknownDomainSelection:
    """Tests for selecting unknown domains."""

    def test_unknown_domain_ignored(self, domain_a: DomainModule) -> None:
        """Unknown domain names in selection are ignored."""
        selector = DomainSelector([domain_a])
        context = selector.build_active_context(["domain_a", "unknown_domain"])

        # Only domain_a should be processed
        assert context.domains_loaded == ["domain_a", "unknown_domain"]
        assert context.vocabulary == {"term1": "value1", "common": "a_value"}

    def test_all_unknown_domains(self, domain_a: DomainModule) -> None:
        """All unknown domains results in empty context data."""
        selector = DomainSelector([domain_a])
        context = selector.build_active_context(["unknown1", "unknown2"])

        assert context.domains_loaded == ["unknown1", "unknown2"]
        assert context.vocabulary == {}
        assert context.expertise == ""


class TestBaseDomainSupport:
    """Tests for base_domain support in DomainSelector."""

    @pytest.fixture
    def base_domain(self) -> DomainModule:
        """Create a base domain for testing."""
        return DomainModule(
            name="base_domain",
            description="Base domain for testing",
            log_schema=MockSchema,
            vocabulary={"base_term": "base_value", "shared": "base_shared_value"},
            expertise="Base domain expertise",
            response_evaluation_rules=["Base Rule 1", "Base Rule 2"],
            context_management_guidance="Base guidance",
            clarification_patterns={
                "SUBJECTIVE": ["Base subjective question?"],
                "BASE_TYPE": ["Base specific question?"],
            },
        )

    def test_init_with_base_domain(
        self, domain_a: DomainModule, base_domain: DomainModule
    ) -> None:
        """DomainSelector stores base_domain when provided."""
        selector = DomainSelector([domain_a], base_domain=base_domain)
        assert selector.base_domain is base_domain

    def test_init_without_base_domain(self, domain_a: DomainModule) -> None:
        """DomainSelector has base_domain=None by default."""
        selector = DomainSelector([domain_a])
        assert selector.base_domain is None

    def test_base_domain_with_single_selected(
        self, domain_a: DomainModule, base_domain: DomainModule
    ) -> None:
        """build_active_context merges base_domain + single selected domain."""
        selector = DomainSelector([domain_a], base_domain=base_domain)
        context = selector.build_active_context(["domain_a"])

        # domains_loaded includes base_domain first
        assert context.domains_loaded == ["base_domain", "domain_a"]
        # Both vocabularies merged
        assert "base_term" in context.vocabulary
        assert "term1" in context.vocabulary
        # Both expertise combined with base first
        assert context.expertise.index("[base_domain]") < context.expertise.index(
            "[domain_a]"
        )
        # Both evaluation rules combined
        assert "Base Rule 1" in context.evaluation_rules
        assert "Rule A1" in context.evaluation_rules

    def test_base_domain_with_multiple_selected(
        self, domain_a: DomainModule, domain_b: DomainModule, base_domain: DomainModule
    ) -> None:
        """build_active_context merges base_domain + multiple selected domains."""
        selector = DomainSelector([domain_a, domain_b], base_domain=base_domain)
        context = selector.build_active_context(["domain_a", "domain_b"])

        # domains_loaded: base first, then selected in order
        assert context.domains_loaded == ["base_domain", "domain_a", "domain_b"]
        # All vocabularies merged
        assert "base_term" in context.vocabulary
        assert "term1" in context.vocabulary
        assert "term2" in context.vocabulary
        # All expertise combined
        assert "[base_domain]" in context.expertise
        assert "[domain_a]" in context.expertise
        assert "[domain_b]" in context.expertise

    def test_base_domain_none_backward_compatible(
        self, domain_a: DomainModule, domain_b: DomainModule
    ) -> None:
        """base_domain=None produces identical results to Story 6.1 implementation."""
        selector_without_base = DomainSelector([domain_a, domain_b])
        selector_with_none = DomainSelector([domain_a, domain_b], base_domain=None)

        context1 = selector_without_base.build_active_context(["domain_a", "domain_b"])
        context2 = selector_with_none.build_active_context(["domain_a", "domain_b"])

        assert context1.domains_loaded == context2.domains_loaded
        assert context1.vocabulary == context2.vocabulary
        assert context1.expertise == context2.expertise
        assert context1.evaluation_rules == context2.evaluation_rules
        assert context1.context_guidance == context2.context_guidance
        assert context1.clarification_patterns == context2.clarification_patterns

    def test_vocabulary_merge_order_base_first(
        self, base_domain: DomainModule
    ) -> None:
        """Base domain vocabulary applied first, selected domain overrides conflicts."""
        # Create domain with conflicting 'shared' key
        domain_with_override = DomainModule(
            name="domain_override",
            description="Domain with override",
            log_schema=MockSchema,
            vocabulary={"unique": "unique_value", "shared": "override_value"},
            expertise="Override expertise",
            response_evaluation_rules=[],
            context_management_guidance="",
            clarification_patterns={},
        )
        selector = DomainSelector([domain_with_override], base_domain=base_domain)
        context = selector.build_active_context(["domain_override"])

        # Selected domain should override base domain's 'shared' value
        assert context.vocabulary["shared"] == "override_value"
        # Non-conflicting keys remain
        assert context.vocabulary["base_term"] == "base_value"
        assert context.vocabulary["unique"] == "unique_value"

    def test_domains_loaded_base_first(
        self, domain_a: DomainModule, base_domain: DomainModule
    ) -> None:
        """domains_loaded includes base_domain.name first."""
        selector = DomainSelector([domain_a], base_domain=base_domain)
        context = selector.build_active_context(["domain_a"])

        assert context.domains_loaded[0] == "base_domain"
        assert context.domains_loaded[1] == "domain_a"

    def test_deduplication_base_also_selected(
        self, domain_a: DomainModule, base_domain: DomainModule
    ) -> None:
        """When base_domain.name is in selected_domains, it appears only once."""
        # Register base_domain in selector.domains as well
        selector = DomainSelector([domain_a, base_domain], base_domain=base_domain)
        context = selector.build_active_context(["base_domain", "domain_a"])

        # base_domain appears only once in domains_loaded
        assert context.domains_loaded == ["base_domain", "domain_a"]
        assert context.domains_loaded.count("base_domain") == 1
        # Expertise label also appears only once
        assert context.expertise.count("[base_domain]") == 1

    def test_expertise_base_domain_label_first(
        self, domain_a: DomainModule, base_domain: DomainModule
    ) -> None:
        """Base domain expertise appears first in combined expertise."""
        selector = DomainSelector([domain_a], base_domain=base_domain)
        context = selector.build_active_context(["domain_a"])

        # Base domain expertise should come before selected domain
        base_pos = context.expertise.find("[base_domain]")
        selected_pos = context.expertise.find("[domain_a]")
        assert base_pos < selected_pos

    def test_vocabulary_conflict_warning_base_vs_selected(
        self,
        base_domain: DomainModule,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """Vocabulary conflict between base_domain and selected domain logs warning."""
        domain_with_conflict = DomainModule(
            name="conflict_domain",
            description="Domain with conflict",
            log_schema=MockSchema,
            vocabulary={"shared": "conflict_value"},
            expertise="",
            response_evaluation_rules=[],
            context_management_guidance="",
            clarification_patterns={},
        )
        selector = DomainSelector([domain_with_conflict], base_domain=base_domain)

        with caplog.at_level(logging.WARNING):
            selector.build_active_context(["conflict_domain"])

        assert "Vocabulary conflict for 'shared'" in caplog.text
        assert "'conflict_value' overrides 'base_shared_value'" in caplog.text

    def test_clarification_patterns_combined(
        self, domain_a: DomainModule, base_domain: DomainModule
    ) -> None:
        """Clarification patterns from base and selected domains are combined."""
        selector = DomainSelector([domain_a], base_domain=base_domain)
        context = selector.build_active_context(["domain_a"])

        # SUBJECTIVE has questions from both base and domain_a
        assert "SUBJECTIVE" in context.clarification_patterns
        subjective = context.clarification_patterns["SUBJECTIVE"]
        assert "Base subjective question?" in subjective
        assert "How do you feel about A?" in subjective
        # BASE_TYPE is unique to base_domain
        assert "BASE_TYPE" in context.clarification_patterns
        assert "Base specific question?" in context.clarification_patterns["BASE_TYPE"]

    def test_evaluation_rules_combined(
        self, domain_a: DomainModule, base_domain: DomainModule
    ) -> None:
        """Evaluation rules from base and selected domains are combined."""
        selector = DomainSelector([domain_a], base_domain=base_domain)
        context = selector.build_active_context(["domain_a"])

        # Base rules come first
        assert "Base Rule 1" in context.evaluation_rules
        assert "Base Rule 2" in context.evaluation_rules
        # Selected domain rules included
        assert "Rule A1" in context.evaluation_rules
        assert "Rule A2" in context.evaluation_rules

    def test_context_guidance_combined(
        self, domain_a: DomainModule, base_domain: DomainModule
    ) -> None:
        """Context guidance from base and selected domains are combined."""
        selector = DomainSelector([domain_a], base_domain=base_domain)
        context = selector.build_active_context(["domain_a"])

        assert "[base_domain] Base guidance" in context.context_guidance
        assert "[domain_a] Guidance for domain A" in context.context_guidance
        # Base guidance appears first
        base_pos = context.context_guidance.find("[base_domain]")
        selected_pos = context.context_guidance.find("[domain_a]")
        assert base_pos < selected_pos

    def test_empty_selection_with_base_domain(
        self, base_domain: DomainModule
    ) -> None:
        """Empty selection with base_domain returns only base_domain context."""
        selector = DomainSelector([], base_domain=base_domain)
        context = selector.build_active_context([])

        # Only base_domain in domains_loaded
        assert context.domains_loaded == ["base_domain"]
        # Base domain vocabulary only
        assert context.vocabulary == {
            "base_term": "base_value",
            "shared": "base_shared_value",
        }
        # Base domain expertise
        assert "[base_domain] Base domain expertise" in context.expertise
