"""Unit tests for DomainModule."""

import pytest
from pydantic import BaseModel, ValidationError
from quilto.domain import DomainModule


class SampleLogEntry(BaseModel):
    """Sample log entry for testing."""

    exercise: str
    weight: float | None = None


class TestDomainModuleRequiredFields:
    """Test that DomainModule requires mandatory fields."""

    def test_requires_description(self) -> None:
        """DomainModule requires description field."""
        with pytest.raises(ValidationError) as exc_info:
            DomainModule(
                log_schema=SampleLogEntry,
                vocabulary={"test": "test value"},
            )  # type: ignore[call-arg]
        assert "description" in str(exc_info.value)

    def test_requires_log_schema(self) -> None:
        """DomainModule requires log_schema field."""
        with pytest.raises(ValidationError) as exc_info:
            DomainModule(
                description="Test domain",
                vocabulary={"test": "test value"},
            )  # type: ignore[call-arg]
        assert "log_schema" in str(exc_info.value)

    def test_requires_vocabulary(self) -> None:
        """DomainModule requires vocabulary field."""
        with pytest.raises(ValidationError) as exc_info:
            DomainModule(
                description="Test domain",
                log_schema=SampleLogEntry,
            )  # type: ignore[call-arg]
        assert "vocabulary" in str(exc_info.value)

    def test_accepts_all_required_fields(self) -> None:
        """DomainModule accepts all required fields."""
        domain = DomainModule(
            description="Test domain",
            log_schema=SampleLogEntry,
            vocabulary={"test": "test value"},
        )
        assert domain.description == "Test domain"
        assert domain.log_schema is SampleLogEntry
        assert domain.vocabulary == {"test": "test value"}


class TestDomainModuleNameDefault:
    """Test name field defaulting behavior."""

    def test_name_defaults_to_class_name(self) -> None:
        """Name defaults to class name when not provided."""

        class FitnessDomain(DomainModule):
            pass

        domain = FitnessDomain(
            description="Test domain",
            log_schema=SampleLogEntry,
            vocabulary={"test": "test value"},
        )
        assert domain.name == "FitnessDomain"

    def test_name_can_be_explicitly_set(self) -> None:
        """Name can be explicitly provided."""
        domain = DomainModule(
            name="custom_name",
            description="Test domain",
            log_schema=SampleLogEntry,
            vocabulary={"test": "test value"},
        )
        assert domain.name == "custom_name"

    def test_empty_name_defaults_to_class_name(self) -> None:
        """Empty string name defaults to class name."""
        domain = DomainModule(
            name="",
            description="Test domain",
            log_schema=SampleLogEntry,
            vocabulary={"test": "test value"},
        )
        assert domain.name == "DomainModule"


class TestDomainModuleOptionalFields:
    """Test optional fields have correct defaults."""

    def test_expertise_defaults_to_empty_string(self) -> None:
        """Expertise defaults to empty string."""
        domain = DomainModule(
            description="Test domain",
            log_schema=SampleLogEntry,
            vocabulary={"test": "test value"},
        )
        assert domain.expertise == ""

    def test_response_evaluation_rules_defaults_to_empty_list(self) -> None:
        """Response evaluation rules defaults to empty list."""
        domain = DomainModule(
            description="Test domain",
            log_schema=SampleLogEntry,
            vocabulary={"test": "test value"},
        )
        assert domain.response_evaluation_rules == []

    def test_context_management_guidance_defaults_to_empty_string(self) -> None:
        """Context management guidance defaults to empty string."""
        domain = DomainModule(
            description="Test domain",
            log_schema=SampleLogEntry,
            vocabulary={"test": "test value"},
        )
        assert domain.context_management_guidance == ""

    def test_optional_fields_can_be_set(self) -> None:
        """Optional fields can be explicitly set."""
        domain = DomainModule(
            description="Test domain",
            log_schema=SampleLogEntry,
            vocabulary={"test": "test value"},
            expertise="Domain expertise text",
            response_evaluation_rules=["Rule 1", "Rule 2"],
            context_management_guidance="Track patterns",
        )
        assert domain.expertise == "Domain expertise text"
        assert domain.response_evaluation_rules == ["Rule 1", "Rule 2"]
        assert domain.context_management_guidance == "Track patterns"


class TestDomainModuleLogSchemaValidation:
    """Test log_schema type validation."""

    def test_log_schema_must_be_basemodel_subclass(self) -> None:
        """log_schema must be a BaseModel subclass."""

        class NotAModel:
            pass

        with pytest.raises(ValidationError):
            DomainModule(
                description="Test domain",
                log_schema=NotAModel,  # type: ignore[arg-type]
                vocabulary={"test": "test value"},
            )

    def test_log_schema_rejects_instance(self) -> None:
        """log_schema must be a class, not an instance."""
        instance = SampleLogEntry(exercise="test")
        with pytest.raises(ValidationError):
            DomainModule(
                description="Test domain",
                log_schema=instance,  # type: ignore[arg-type]
                vocabulary={"test": "test value"},
            )


class TestDomainModuleVocabularyValidation:
    """Test vocabulary dict validation."""

    def test_vocabulary_accepts_valid_dict(self) -> None:
        """Vocabulary accepts dict[str, str]."""
        domain = DomainModule(
            description="Test domain",
            log_schema=SampleLogEntry,
            vocabulary={"bench": "bench press", "dl": "deadlift"},
        )
        assert domain.vocabulary == {"bench": "bench press", "dl": "deadlift"}

    def test_vocabulary_accepts_empty_dict(self) -> None:
        """Vocabulary accepts empty dict."""
        domain = DomainModule(
            description="Test domain",
            log_schema=SampleLogEntry,
            vocabulary={},
        )
        assert domain.vocabulary == {}

    def test_vocabulary_rejects_non_dict_type(self) -> None:
        """Vocabulary rejects non-dict types."""
        with pytest.raises(ValidationError):
            DomainModule(
                description="Test domain",
                log_schema=SampleLogEntry,
                vocabulary="not a dict",  # type: ignore[arg-type]
            )

    def test_vocabulary_rejects_list_type(self) -> None:
        """Vocabulary rejects list type."""
        with pytest.raises(ValidationError):
            DomainModule(
                description="Test domain",
                log_schema=SampleLogEntry,
                vocabulary=["key", "value"],  # type: ignore[arg-type]
            )

    def test_vocabulary_rejects_non_string_keys(self) -> None:
        """Vocabulary rejects non-string keys (Pydantic strict validation)."""
        with pytest.raises(ValidationError) as exc_info:
            DomainModule(
                description="Test domain",
                log_schema=SampleLogEntry,
                vocabulary={1: "one", 2: "two"},  # type: ignore[dict-item]
            )
        assert "string" in str(exc_info.value).lower()

    def test_vocabulary_rejects_non_string_values(self) -> None:
        """Vocabulary rejects non-string values (Pydantic strict validation)."""
        with pytest.raises(ValidationError) as exc_info:
            DomainModule(
                description="Test domain",
                log_schema=SampleLogEntry,
                vocabulary={"one": 1, "two": 2},  # type: ignore[dict-item]
            )
        assert "string" in str(exc_info.value).lower()
