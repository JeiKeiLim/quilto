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
