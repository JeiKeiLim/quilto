"""Tests for GeneralFitness domain module."""

import pytest
from pydantic import ValidationError


class TestExerciseRecord:
    """Tests for ExerciseRecord model."""

    def test_creates_with_name_only(self) -> None:
        """Test ExerciseRecord can be created with only name field."""
        from swealog import ExerciseRecord

        record = ExerciseRecord(name="Bench Press")
        assert record.name == "Bench Press"
        assert record.sets is None
        assert record.reps is None
        assert record.weight is None
        assert record.weight_unit is None
        assert record.duration_seconds is None
        assert record.distance is None
        assert record.distance_unit is None

    def test_creates_with_all_fields(self) -> None:
        """Test ExerciseRecord can be created with all fields."""
        from swealog import ExerciseRecord

        record = ExerciseRecord(
            name="Squat",
            sets=3,
            reps=5,
            weight=100.0,
            weight_unit="kg",
            duration_seconds=120,
            distance=0.0,
            distance_unit="meters",
        )
        assert record.name == "Squat"
        assert record.sets == 3
        assert record.reps == 5
        assert record.weight == 100.0
        assert record.weight_unit == "kg"
        assert record.duration_seconds == 120
        assert record.distance == 0.0
        assert record.distance_unit == "meters"

    def test_strict_mode_rejects_wrong_types(self) -> None:
        """Test strict mode rejects invalid types for name field."""
        from swealog import ExerciseRecord

        with pytest.raises(ValidationError):
            ExerciseRecord(name=123)  # type: ignore[arg-type]


class TestGeneralFitnessEntry:
    """Tests for GeneralFitnessEntry model."""

    def test_creates_with_activity_type_only(self) -> None:
        """Test GeneralFitnessEntry can be created with only activity_type."""
        from swealog import GeneralFitnessEntry

        entry = GeneralFitnessEntry(activity_type="workout")
        assert entry.activity_type == "workout"
        assert entry.exercises == []
        assert entry.duration_minutes is None
        assert entry.notes is None
        assert entry.perceived_effort is None
        assert entry.date is None

    def test_creates_with_all_fields(self) -> None:
        """Test GeneralFitnessEntry can be created with all fields."""
        from swealog import ExerciseRecord, GeneralFitnessEntry

        exercises = [
            ExerciseRecord(name="Bench Press", sets=3, reps=10),
            ExerciseRecord(name="Squats", sets=3, reps=8),
        ]
        entry = GeneralFitnessEntry(
            activity_type="strength",
            exercises=exercises,
            duration_minutes=60,
            notes="Great workout",
            perceived_effort=7,
            date="2026-01-08",
        )
        assert entry.activity_type == "strength"
        assert len(entry.exercises) == 2
        assert entry.duration_minutes == 60
        assert entry.notes == "Great workout"
        assert entry.perceived_effort == 7
        assert entry.date == "2026-01-08"

    def test_validates_perceived_effort_minimum(self) -> None:
        """Test perceived_effort must be at least 1."""
        from swealog import GeneralFitnessEntry

        with pytest.raises(ValidationError, match="between 1 and 10"):
            GeneralFitnessEntry(activity_type="workout", perceived_effort=0)

    def test_validates_perceived_effort_maximum(self) -> None:
        """Test perceived_effort must be at most 10."""
        from swealog import GeneralFitnessEntry

        with pytest.raises(ValidationError, match="between 1 and 10"):
            GeneralFitnessEntry(activity_type="workout", perceived_effort=11)

    def test_accepts_valid_perceived_effort(self) -> None:
        """Test valid perceived_effort values are accepted."""
        from swealog import GeneralFitnessEntry

        for effort in [1, 5, 10]:
            entry = GeneralFitnessEntry(activity_type="workout", perceived_effort=effort)
            assert entry.perceived_effort == effort

    def test_strict_mode_rejects_wrong_types(self) -> None:
        """Test strict mode rejects invalid types for activity_type field."""
        from swealog import GeneralFitnessEntry

        with pytest.raises(ValidationError):
            GeneralFitnessEntry(activity_type=123)  # type: ignore[arg-type]


class TestGeneralFitness:
    """Tests for GeneralFitness domain module."""

    def test_has_required_domain_fields(self) -> None:
        """Test GeneralFitness has all required DomainModule fields."""
        from swealog import GeneralFitness, GeneralFitnessEntry
        from swealog.domains.general_fitness import general_fitness

        assert general_fitness.description
        assert general_fitness.log_schema == GeneralFitnessEntry
        assert isinstance(general_fitness.vocabulary, dict)
        assert isinstance(general_fitness, GeneralFitness)

    def test_name_defaults_to_class_name(self) -> None:
        """Test name defaults to class name when not provided."""
        from swealog import GeneralFitness, GeneralFitnessEntry

        domain = GeneralFitness(
            description="test",
            log_schema=GeneralFitnessEntry,
            vocabulary={},
        )
        assert domain.name == "GeneralFitness"

    def test_vocabulary_has_expected_normalizations(self) -> None:
        """Test vocabulary contains expected fitness term normalizations."""
        from swealog.domains.general_fitness import general_fitness

        assert general_fitness.vocabulary["workout"] == "training session"
        assert general_fitness.vocabulary["lifting"] == "weight training"
        assert general_fitness.vocabulary["cardio"] == "cardiovascular exercise"
        assert general_fitness.vocabulary["stretching"] == "flexibility training"
        assert general_fitness.vocabulary["warmup"] == "warm up"
        assert general_fitness.vocabulary["warm-up"] == "warm up"
        assert general_fitness.vocabulary["cooldown"] == "cool down"
        assert general_fitness.vocabulary["cool-down"] == "cool down"
        assert general_fitness.vocabulary["pr"] == "personal record"
        assert general_fitness.vocabulary["PR"] == "personal record"
        assert general_fitness.vocabulary["pb"] == "personal best"
        assert general_fitness.vocabulary["PB"] == "personal best"

    def test_description_is_fitness_related(self) -> None:
        """Test description is non-empty and covers fitness activities."""
        from swealog.domains.general_fitness import general_fitness

        assert general_fitness.description
        assert len(general_fitness.description) > 50
        # Description should mention fitness-related terms
        desc_lower = general_fitness.description.lower()
        assert any(
            term in desc_lower
            for term in ["fitness", "workout", "exercise", "health", "training"]
        )

    def test_log_schema_is_general_fitness_entry_class(self) -> None:
        """Test log_schema is the GeneralFitnessEntry class."""
        from swealog import GeneralFitnessEntry
        from swealog.domains.general_fitness import general_fitness

        assert general_fitness.log_schema is GeneralFitnessEntry

    def test_expertise_is_set(self) -> None:
        """Test expertise field is populated with fitness knowledge."""
        from swealog.domains.general_fitness import general_fitness

        assert general_fitness.expertise
        assert len(general_fitness.expertise) > 20

    def test_response_evaluation_rules_is_list(self) -> None:
        """Test response_evaluation_rules is a non-empty list with expected content."""
        from swealog.domains.general_fitness import general_fitness

        assert isinstance(general_fitness.response_evaluation_rules, list)
        assert len(general_fitness.response_evaluation_rules) >= 1
        # Verify rules contain fitness-related guidance
        rules_text = " ".join(general_fitness.response_evaluation_rules).lower()
        assert any(term in rules_text for term in ["exercise", "fitness", "workout", "recovery", "medical"])

    def test_general_fitness_singleton_importable_from_domains(self) -> None:
        """Test general_fitness singleton is importable from swealog.domains."""
        from swealog.domains import general_fitness

        assert general_fitness.name == "GeneralFitness"

    def test_general_fitness_singleton_importable_from_top_level(self) -> None:
        """Test general_fitness singleton is importable from swealog top-level."""
        from swealog import general_fitness

        assert general_fitness.name == "GeneralFitness"

    def test_context_management_guidance_is_set(self) -> None:
        """Test context_management_guidance is populated."""
        from swealog.domains.general_fitness import general_fitness

        assert general_fitness.context_management_guidance
        assert len(general_fitness.context_management_guidance) > 20
