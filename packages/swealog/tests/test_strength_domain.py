"""Tests for the Strength domain module."""

import pytest
from pydantic import ValidationError


class TestStrengthSetValidation:
    """Tests for StrengthSet model validation."""

    def test_valid_rpe_range(self) -> None:
        """Test that RPE within 1-10 range is valid."""
        from swealog.domains import StrengthSet

        s = StrengthSet(reps=5, weight=100.0, weight_unit="kg", rpe=8.0)
        assert s.rpe == 8.0

    def test_rpe_boundary_one_succeeds(self) -> None:
        """Test that RPE exactly 1.0 succeeds."""
        from swealog.domains import StrengthSet

        s = StrengthSet(rpe=1.0)
        assert s.rpe == 1.0

    def test_rpe_boundary_ten_succeeds(self) -> None:
        """Test that RPE exactly 10.0 succeeds."""
        from swealog.domains import StrengthSet

        s = StrengthSet(rpe=10.0)
        assert s.rpe == 10.0

    def test_rpe_below_one_raises(self) -> None:
        """Test that RPE below 1 raises ValidationError."""
        from swealog.domains import StrengthSet

        with pytest.raises(ValidationError) as exc_info:
            StrengthSet(rpe=0.5)
        assert "greater than or equal to 1" in str(exc_info.value)

    def test_rpe_above_ten_raises(self) -> None:
        """Test that RPE above 10 raises ValidationError."""
        from swealog.domains import StrengthSet

        with pytest.raises(ValidationError) as exc_info:
            StrengthSet(rpe=10.5)
        assert "less than or equal to 10" in str(exc_info.value)

    def test_valid_rir_non_negative(self) -> None:
        """Test that non-negative RIR is valid."""
        from swealog.domains import StrengthSet

        s = StrengthSet(reps=5, weight=100.0, weight_unit="kg", rir=2)
        assert s.rir == 2

    def test_rir_boundary_zero_succeeds(self) -> None:
        """Test that RIR exactly 0 succeeds."""
        from swealog.domains import StrengthSet

        s = StrengthSet(rir=0)
        assert s.rir == 0

    def test_rir_negative_raises(self) -> None:
        """Test that negative RIR raises ValidationError."""
        from swealog.domains import StrengthSet

        with pytest.raises(ValidationError) as exc_info:
            StrengthSet(rir=-1)
        assert "greater than or equal to 0" in str(exc_info.value)

    def test_weight_unit_kg_succeeds(self) -> None:
        """Test that weight_unit 'kg' is valid."""
        from swealog.domains import StrengthSet

        s = StrengthSet(weight=100.0, weight_unit="kg")
        assert s.weight_unit == "kg"

    def test_weight_unit_lbs_succeeds(self) -> None:
        """Test that weight_unit 'lbs' is valid."""
        from swealog.domains import StrengthSet

        s = StrengthSet(weight=225.0, weight_unit="lbs")
        assert s.weight_unit == "lbs"

    def test_weight_unit_invalid_raises(self) -> None:
        """Test that invalid weight_unit raises ValidationError."""
        from swealog.domains import StrengthSet

        with pytest.raises(ValidationError):
            StrengthSet(weight=100.0, weight_unit="lb")  # type: ignore[arg-type]

    def test_weight_unit_pounds_raises(self) -> None:
        """Test that 'pounds' as weight_unit raises ValidationError."""
        from swealog.domains import StrengthSet

        with pytest.raises(ValidationError):
            StrengthSet(weight=100.0, weight_unit="pounds")  # type: ignore[arg-type]

    def test_rpe_and_rir_both_set_raises(self) -> None:
        """Test that setting both rpe and rir raises ValueError."""
        from swealog.domains import StrengthSet

        with pytest.raises(ValidationError) as exc_info:
            StrengthSet(reps=5, weight=100.0, weight_unit="kg", rpe=8.0, rir=2)
        assert "rpe and rir are mutually exclusive" in str(exc_info.value)

    def test_rpe_only_succeeds(self) -> None:
        """Test that rpe alone is valid."""
        from swealog.domains import StrengthSet

        s = StrengthSet(reps=5, weight=100.0, weight_unit="kg", rpe=8.0)
        assert s.rpe == 8.0
        assert s.rir is None

    def test_rir_only_succeeds(self) -> None:
        """Test that rir alone is valid."""
        from swealog.domains import StrengthSet

        s = StrengthSet(reps=5, weight=100.0, weight_unit="kg", rir=2)
        assert s.rir == 2
        assert s.rpe is None

    def test_neither_rpe_nor_rir_succeeds(self) -> None:
        """Test that neither rpe nor rir being set is valid."""
        from swealog.domains import StrengthSet

        s = StrengthSet(reps=5, weight=100.0, weight_unit="kg")
        assert s.rpe is None
        assert s.rir is None


class TestStrengthExerciseModel:
    """Tests for StrengthExercise model."""

    def test_exercise_name_required(self) -> None:
        """Test that exercise name is required."""
        from swealog.domains import StrengthExercise

        e = StrengthExercise(name="bench press")
        assert e.name == "bench press"

    def test_exercise_missing_name_raises(self) -> None:
        """Test that missing name raises ValidationError."""
        from swealog.domains import StrengthExercise

        with pytest.raises(ValidationError):
            StrengthExercise()  # type: ignore[call-arg]

    def test_exercise_empty_name_raises(self) -> None:
        """Test that empty name raises ValidationError."""
        from swealog.domains import StrengthExercise

        with pytest.raises(ValidationError) as exc_info:
            StrengthExercise(name="")
        assert "at least 1" in str(exc_info.value).lower()

    def test_sets_list_default_empty(self) -> None:
        """Test that sets list defaults to empty."""
        from swealog.domains import StrengthExercise

        e = StrengthExercise(name="squat")
        assert e.sets == []

    def test_notes_optional(self) -> None:
        """Test that notes field is optional."""
        from swealog.domains import StrengthExercise

        e1 = StrengthExercise(name="deadlift")
        assert e1.notes is None

        e2 = StrengthExercise(name="deadlift", notes="felt heavy")
        assert e2.notes == "felt heavy"

    def test_exercise_with_sets(self) -> None:
        """Test exercise with multiple sets."""
        from swealog.domains import StrengthExercise, StrengthSet

        sets = [
            StrengthSet(reps=5, weight=135.0, weight_unit="lbs"),
            StrengthSet(reps=5, weight=155.0, weight_unit="lbs"),
            StrengthSet(reps=5, weight=175.0, weight_unit="lbs", rpe=8.0),
        ]
        e = StrengthExercise(name="bench press", sets=sets)
        assert len(e.sets) == 3
        assert e.sets[2].rpe == 8.0


class TestStrengthEntryModel:
    """Tests for StrengthEntry log schema."""

    def test_exercises_list_default_empty(self) -> None:
        """Test that exercises list defaults to empty."""
        from swealog.domains import StrengthEntry

        entry = StrengthEntry()
        assert entry.exercises == []

    def test_valid_entry_with_exercises(self) -> None:
        """Test creating a valid entry with exercises."""
        from swealog.domains import StrengthEntry, StrengthExercise, StrengthSet

        exercises = [
            StrengthExercise(
                name="squat",
                sets=[StrengthSet(reps=5, weight=225.0, weight_unit="lbs")],
            ),
            StrengthExercise(
                name="bench press",
                sets=[StrengthSet(reps=5, weight=185.0, weight_unit="lbs", rpe=8.0)],
            ),
        ]
        entry = StrengthEntry(
            exercises=exercises,
            session_notes="Good session",
            date="2024-01-15",
            duration_minutes=60,
        )
        assert len(entry.exercises) == 2
        assert entry.exercises[0].name == "squat"
        assert entry.exercises[1].name == "bench press"
        assert entry.session_notes == "Good session"

    def test_perceived_difficulty_range(self) -> None:
        """Test that perceived_difficulty within 1-10 is valid."""
        from swealog.domains import StrengthEntry

        entry = StrengthEntry(perceived_difficulty=7)
        assert entry.perceived_difficulty == 7

    def test_perceived_difficulty_boundary_one_succeeds(self) -> None:
        """Test that perceived_difficulty exactly 1 succeeds."""
        from swealog.domains import StrengthEntry

        entry = StrengthEntry(perceived_difficulty=1)
        assert entry.perceived_difficulty == 1

    def test_perceived_difficulty_boundary_ten_succeeds(self) -> None:
        """Test that perceived_difficulty exactly 10 succeeds."""
        from swealog.domains import StrengthEntry

        entry = StrengthEntry(perceived_difficulty=10)
        assert entry.perceived_difficulty == 10

    def test_perceived_difficulty_below_one_raises(self) -> None:
        """Test that perceived_difficulty below 1 raises ValidationError."""
        from swealog.domains import StrengthEntry

        with pytest.raises(ValidationError) as exc_info:
            StrengthEntry(perceived_difficulty=0)
        assert "greater than or equal to 1" in str(exc_info.value)

    def test_perceived_difficulty_above_ten_raises(self) -> None:
        """Test that perceived_difficulty above 10 raises ValidationError."""
        from swealog.domains import StrengthEntry

        with pytest.raises(ValidationError) as exc_info:
            StrengthEntry(perceived_difficulty=11)
        assert "less than or equal to 10" in str(exc_info.value)


class TestStrengthDomainModule:
    """Tests for Strength DomainModule configuration."""

    def test_instantiation(self) -> None:
        """Test that Strength domain can be instantiated."""
        from swealog.domains import Strength, strength

        assert strength is not None
        assert isinstance(strength, Strength)

    def test_name_defaults_to_class_name(self) -> None:
        """Test that domain name defaults to class name."""
        from swealog.domains import strength

        assert strength.name == "Strength"

    def test_description_non_empty(self) -> None:
        """Test that description is non-empty."""
        from swealog.domains import strength

        assert strength.description
        assert len(strength.description) > 0

    def test_vocabulary_contains_abbreviations(self) -> None:
        """Test that vocabulary contains common abbreviations."""
        from swealog.domains import strength

        assert strength.vocabulary["bp"] == "bench press"
        assert strength.vocabulary["sq"] == "squat"
        assert strength.vocabulary["dl"] == "deadlift"
        assert strength.vocabulary["ohp"] == "overhead press"

    def test_vocabulary_contains_korean_terms(self) -> None:
        """Test that vocabulary contains Korean exercise names."""
        from swealog.domains import strength

        assert "벤치프레스" in strength.vocabulary
        assert "스쿼트" in strength.vocabulary
        assert "데드리프트" in strength.vocabulary

    def test_vocabulary_korean_maps_to_canonical_csv_names(self) -> None:
        """Test that Korean terms map to canonical CSV names."""
        from swealog.domains import strength

        assert strength.vocabulary["벤치프레스"] == "Bench Press (Barbell)"
        assert strength.vocabulary["스쿼트"] == "Squat (Barbell)"
        assert strength.vocabulary["데드리프트"] == "Deadlift (Barbell)"
        assert strength.vocabulary["풀업"] == "Pull Up"
        assert strength.vocabulary["트랩바 데드리프트"] == "Trap Bar Deadlift"

    def test_vocabulary_contains_weight_units(self) -> None:
        """Test that vocabulary contains weight unit normalizations."""
        from swealog.domains import strength

        assert strength.vocabulary["lb"] == "lbs"
        assert strength.vocabulary["pounds"] == "lbs"
        assert strength.vocabulary["#"] == "lbs"
        assert strength.vocabulary["kilos"] == "kg"
        assert strength.vocabulary["kilograms"] == "kg"

    def test_vocabulary_contains_intensity_notations(self) -> None:
        """Test that vocabulary contains intensity notations."""
        from swealog.domains import strength

        assert strength.vocabulary["@"] == "RPE"
        assert strength.vocabulary["rpe"] == "RPE"
        assert strength.vocabulary["rir"] == "RIR"

    def test_expertise_non_empty(self) -> None:
        """Test that expertise is non-empty."""
        from swealog.domains import strength

        assert strength.expertise
        assert len(strength.expertise) > 0
        assert "progressive overload" in strength.expertise

    def test_response_evaluation_rules_populated(self) -> None:
        """Test that response_evaluation_rules is populated."""
        from swealog.domains import strength

        assert strength.response_evaluation_rules
        assert len(strength.response_evaluation_rules) > 0
        assert any("1RM" in rule for rule in strength.response_evaluation_rules)

    def test_context_management_guidance_populated(self) -> None:
        """Test that context_management_guidance is populated."""
        from swealog.domains import strength

        assert strength.context_management_guidance
        assert len(strength.context_management_guidance) > 0
        assert "PRs" in strength.context_management_guidance


class TestStrengthSingleton:
    """Tests for strength singleton instance."""

    def test_singleton_importable(self) -> None:
        """Test that strength singleton is importable from swealog.domains."""
        from swealog.domains import strength as imported_strength

        assert imported_strength is not None

    def test_singleton_is_strength_instance(self) -> None:
        """Test that singleton is a Strength instance."""
        from swealog.domains import Strength, strength

        assert isinstance(strength, Strength)


class TestStrengthIntegration:
    """Integration tests with GeneralFitness domain."""

    def test_strength_and_general_fitness_coexist(self) -> None:
        """Test that both domains can coexist."""
        from swealog.domains import GeneralFitness, Strength, general_fitness, strength

        assert strength is not None
        assert general_fitness is not None
        assert isinstance(strength, Strength)
        assert isinstance(general_fitness, GeneralFitness)
        assert strength.name != general_fitness.name

    def test_imports_from_swealog_domains(self) -> None:
        """Test that all exports are importable from swealog.domains."""
        from swealog.domains import (
            Strength,
            StrengthEntry,
            StrengthExercise,
            StrengthSet,
            strength,
        )

        assert Strength is not None
        assert StrengthEntry is not None
        assert StrengthExercise is not None
        assert StrengthSet is not None
        assert strength is not None

    def test_log_schema_is_strength_entry(self) -> None:
        """Test that Strength domain's log_schema is StrengthEntry."""
        from swealog.domains import StrengthEntry, strength

        assert strength.log_schema is StrengthEntry
