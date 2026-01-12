"""Tests for the Running domain module."""

import pytest
from pydantic import ValidationError


class TestRunningSplitValidation:
    """Tests for RunningSplit model validation."""

    def test_split_number_boundary_one_succeeds(self) -> None:
        """Test that split_number exactly 1 succeeds."""
        from swealog.domains import RunningSplit

        s = RunningSplit(split_number=1, distance=1.0, duration_seconds=300.0)
        assert s.split_number == 1

    def test_split_number_boundary_zero_fails(self) -> None:
        """Test that split_number 0 raises ValidationError."""
        from swealog.domains import RunningSplit

        with pytest.raises(ValidationError) as exc_info:
            RunningSplit(split_number=0, distance=1.0, duration_seconds=300.0)
        assert "greater than or equal to 1" in str(exc_info.value)

    def test_distance_boundary_zero_succeeds(self) -> None:
        """Test that distance 0.0 succeeds."""
        from swealog.domains import RunningSplit

        s = RunningSplit(split_number=1, distance=0.0, duration_seconds=0.0)
        assert s.distance == 0.0

    def test_distance_negative_fails(self) -> None:
        """Test that negative distance raises ValidationError."""
        from swealog.domains import RunningSplit

        with pytest.raises(ValidationError) as exc_info:
            RunningSplit(split_number=1, distance=-1.0, duration_seconds=300.0)
        assert "greater than or equal to 0" in str(exc_info.value)

    def test_duration_seconds_boundary_zero_succeeds(self) -> None:
        """Test that duration_seconds 0.0 succeeds."""
        from swealog.domains import RunningSplit

        s = RunningSplit(split_number=1, distance=1.0, duration_seconds=0.0)
        assert s.duration_seconds == 0.0

    def test_duration_seconds_negative_fails(self) -> None:
        """Test that negative duration_seconds raises ValidationError."""
        from swealog.domains import RunningSplit

        with pytest.raises(ValidationError) as exc_info:
            RunningSplit(split_number=1, distance=1.0, duration_seconds=-1.0)
        assert "greater than or equal to 0" in str(exc_info.value)

    def test_pace_optional(self) -> None:
        """Test that pace field is optional."""
        from swealog.domains import RunningSplit

        s1 = RunningSplit(split_number=1, distance=1.0, duration_seconds=300.0)
        assert s1.pace is None

        s2 = RunningSplit(split_number=1, distance=1.0, duration_seconds=300.0, pace="5:00 min/km")
        assert s2.pace == "5:00 min/km"


class TestRunningIntervalValidation:
    """Tests for RunningInterval model validation."""

    def test_repetitions_boundary_one_succeeds(self) -> None:
        """Test that repetitions exactly 1 succeeds."""
        from swealog.domains import RunningInterval

        i = RunningInterval(repetitions=1)
        assert i.repetitions == 1

    def test_repetitions_boundary_zero_fails(self) -> None:
        """Test that repetitions 0 raises ValidationError."""
        from swealog.domains import RunningInterval

        with pytest.raises(ValidationError) as exc_info:
            RunningInterval(repetitions=0)
        assert "greater than or equal to 1" in str(exc_info.value)

    def test_work_distance_boundary_zero_succeeds(self) -> None:
        """Test that work_distance 0.0 succeeds."""
        from swealog.domains import RunningInterval

        i = RunningInterval(work_distance=0.0)
        assert i.work_distance == 0.0

    def test_work_distance_negative_fails(self) -> None:
        """Test that negative work_distance raises ValidationError."""
        from swealog.domains import RunningInterval

        with pytest.raises(ValidationError) as exc_info:
            RunningInterval(work_distance=-1.0)
        assert "greater than or equal to 0" in str(exc_info.value)

    def test_work_duration_seconds_boundary_zero_succeeds(self) -> None:
        """Test that work_duration_seconds 0.0 succeeds."""
        from swealog.domains import RunningInterval

        i = RunningInterval(work_duration_seconds=0.0)
        assert i.work_duration_seconds == 0.0

    def test_work_duration_seconds_negative_fails(self) -> None:
        """Test that negative work_duration_seconds raises ValidationError."""
        from swealog.domains import RunningInterval

        with pytest.raises(ValidationError) as exc_info:
            RunningInterval(work_duration_seconds=-1.0)
        assert "greater than or equal to 0" in str(exc_info.value)

    def test_rest_duration_seconds_boundary_zero_succeeds(self) -> None:
        """Test that rest_duration_seconds 0.0 succeeds."""
        from swealog.domains import RunningInterval

        i = RunningInterval(rest_duration_seconds=0.0)
        assert i.rest_duration_seconds == 0.0

    def test_rest_duration_seconds_negative_fails(self) -> None:
        """Test that negative rest_duration_seconds raises ValidationError."""
        from swealog.domains import RunningInterval

        with pytest.raises(ValidationError) as exc_info:
            RunningInterval(rest_duration_seconds=-1.0)
        assert "greater than or equal to 0" in str(exc_info.value)

    def test_notes_optional(self) -> None:
        """Test that notes field is optional."""
        from swealog.domains import RunningInterval

        i1 = RunningInterval()
        assert i1.notes is None

        i2 = RunningInterval(notes="hard set")
        assert i2.notes == "hard set"

    def test_all_fields_optional(self) -> None:
        """Test that all fields can be None."""
        from swealog.domains import RunningInterval

        i = RunningInterval()
        assert i.work_distance is None
        assert i.work_duration_seconds is None
        assert i.rest_duration_seconds is None
        assert i.repetitions is None
        assert i.notes is None


class TestRunningEntryValidation:
    """Tests for RunningEntry model validation."""

    def test_perceived_exertion_boundary_one_succeeds(self) -> None:
        """Test that perceived_exertion exactly 1 succeeds."""
        from swealog.domains import RunningEntry

        e = RunningEntry(perceived_exertion=1)
        assert e.perceived_exertion == 1

    def test_perceived_exertion_boundary_ten_succeeds(self) -> None:
        """Test that perceived_exertion exactly 10 succeeds."""
        from swealog.domains import RunningEntry

        e = RunningEntry(perceived_exertion=10)
        assert e.perceived_exertion == 10

    def test_perceived_exertion_below_one_fails(self) -> None:
        """Test that perceived_exertion below 1 raises ValidationError."""
        from swealog.domains import RunningEntry

        with pytest.raises(ValidationError) as exc_info:
            RunningEntry(perceived_exertion=0)
        assert "greater than or equal to 1" in str(exc_info.value)

    def test_perceived_exertion_above_ten_fails(self) -> None:
        """Test that perceived_exertion above 10 raises ValidationError."""
        from swealog.domains import RunningEntry

        with pytest.raises(ValidationError) as exc_info:
            RunningEntry(perceived_exertion=11)
        assert "less than or equal to 10" in str(exc_info.value)

    def test_distance_boundary_zero_succeeds(self) -> None:
        """Test that distance 0.0 succeeds."""
        from swealog.domains import RunningEntry

        e = RunningEntry(distance=0.0)
        assert e.distance == 0.0

    def test_distance_negative_fails(self) -> None:
        """Test that negative distance raises ValidationError."""
        from swealog.domains import RunningEntry

        with pytest.raises(ValidationError) as exc_info:
            RunningEntry(distance=-1.0)
        assert "greater than or equal to 0" in str(exc_info.value)

    def test_duration_minutes_boundary_zero_succeeds(self) -> None:
        """Test that duration_minutes 0 succeeds."""
        from swealog.domains import RunningEntry

        e = RunningEntry(duration_minutes=0)
        assert e.duration_minutes == 0

    def test_duration_minutes_negative_fails(self) -> None:
        """Test that negative duration_minutes raises ValidationError."""
        from swealog.domains import RunningEntry

        with pytest.raises(ValidationError) as exc_info:
            RunningEntry(duration_minutes=-1)
        assert "greater than or equal to 0" in str(exc_info.value)

    def test_average_heart_rate_boundary_zero_succeeds(self) -> None:
        """Test that average_heart_rate 0 succeeds."""
        from swealog.domains import RunningEntry

        e = RunningEntry(average_heart_rate=0)
        assert e.average_heart_rate == 0

    def test_average_heart_rate_negative_fails(self) -> None:
        """Test that negative average_heart_rate raises ValidationError."""
        from swealog.domains import RunningEntry

        with pytest.raises(ValidationError) as exc_info:
            RunningEntry(average_heart_rate=-1)
        assert "greater than or equal to 0" in str(exc_info.value)

    def test_max_heart_rate_boundary_zero_succeeds(self) -> None:
        """Test that max_heart_rate 0 succeeds."""
        from swealog.domains import RunningEntry

        e = RunningEntry(max_heart_rate=0)
        assert e.max_heart_rate == 0

    def test_max_heart_rate_negative_fails(self) -> None:
        """Test that negative max_heart_rate raises ValidationError."""
        from swealog.domains import RunningEntry

        with pytest.raises(ValidationError) as exc_info:
            RunningEntry(max_heart_rate=-1)
        assert "greater than or equal to 0" in str(exc_info.value)

    def test_cadence_boundary_zero_succeeds(self) -> None:
        """Test that cadence 0 succeeds."""
        from swealog.domains import RunningEntry

        e = RunningEntry(cadence=0)
        assert e.cadence == 0

    def test_cadence_negative_fails(self) -> None:
        """Test that negative cadence raises ValidationError."""
        from swealog.domains import RunningEntry

        with pytest.raises(ValidationError) as exc_info:
            RunningEntry(cadence=-1)
        assert "greater than or equal to 0" in str(exc_info.value)

    def test_elevation_gain_boundary_zero_succeeds(self) -> None:
        """Test that elevation_gain 0.0 succeeds."""
        from swealog.domains import RunningEntry

        e = RunningEntry(elevation_gain=0.0)
        assert e.elevation_gain == 0.0

    def test_elevation_gain_negative_fails(self) -> None:
        """Test that negative elevation_gain raises ValidationError."""
        from swealog.domains import RunningEntry

        with pytest.raises(ValidationError) as exc_info:
            RunningEntry(elevation_gain=-1.0)
        assert "greater than or equal to 0" in str(exc_info.value)

    def test_elevation_loss_boundary_zero_succeeds(self) -> None:
        """Test that elevation_loss 0.0 succeeds."""
        from swealog.domains import RunningEntry

        e = RunningEntry(elevation_loss=0.0)
        assert e.elevation_loss == 0.0

    def test_elevation_loss_negative_fails(self) -> None:
        """Test that negative elevation_loss raises ValidationError."""
        from swealog.domains import RunningEntry

        with pytest.raises(ValidationError) as exc_info:
            RunningEntry(elevation_loss=-1.0)
        assert "greater than or equal to 0" in str(exc_info.value)


class TestRunningEntryOptionalStrings:
    """Tests for RunningEntry optional string fields with empty strings."""

    def test_notes_empty_string_succeeds(self) -> None:
        """Test that notes can be an empty string."""
        from swealog.domains import RunningEntry

        e = RunningEntry(notes="")
        assert e.notes == ""

    def test_weather_empty_string_succeeds(self) -> None:
        """Test that weather can be an empty string."""
        from swealog.domains import RunningEntry

        e = RunningEntry(weather="")
        assert e.weather == ""

    def test_pace_empty_string_succeeds(self) -> None:
        """Test that pace can be an empty string."""
        from swealog.domains import RunningEntry

        e = RunningEntry(pace="")
        assert e.pace == ""

    def test_date_empty_string_succeeds(self) -> None:
        """Test that date can be an empty string."""
        from swealog.domains import RunningEntry

        e = RunningEntry(date="")
        assert e.date == ""


class TestRunningEntryLiteralTypes:
    """Tests for RunningEntry Literal type validation."""

    def test_distance_unit_km_succeeds(self) -> None:
        """Test that distance_unit 'km' is valid."""
        from swealog.domains import RunningEntry

        e = RunningEntry(distance=5.0, distance_unit="km")
        assert e.distance_unit == "km"

    def test_distance_unit_mi_succeeds(self) -> None:
        """Test that distance_unit 'mi' is valid."""
        from swealog.domains import RunningEntry

        e = RunningEntry(distance=3.0, distance_unit="mi")
        assert e.distance_unit == "mi"

    def test_distance_unit_m_succeeds(self) -> None:
        """Test that distance_unit 'm' is valid."""
        from swealog.domains import RunningEntry

        e = RunningEntry(distance=800.0, distance_unit="m")
        assert e.distance_unit == "m"

    def test_distance_unit_invalid_fails(self) -> None:
        """Test that invalid distance_unit raises ValidationError."""
        from swealog.domains import RunningEntry

        with pytest.raises(ValidationError):
            RunningEntry(distance=5.0, distance_unit="kilometers")  # type: ignore[arg-type]

    def test_pace_unit_min_km_succeeds(self) -> None:
        """Test that pace_unit 'min/km' is valid."""
        from swealog.domains import RunningEntry

        e = RunningEntry(pace="5:00", pace_unit="min/km")
        assert e.pace_unit == "min/km"

    def test_pace_unit_min_mi_succeeds(self) -> None:
        """Test that pace_unit 'min/mi' is valid."""
        from swealog.domains import RunningEntry

        e = RunningEntry(pace="8:00", pace_unit="min/mi")
        assert e.pace_unit == "min/mi"

    def test_pace_unit_invalid_fails(self) -> None:
        """Test that invalid pace_unit raises ValidationError."""
        from swealog.domains import RunningEntry

        with pytest.raises(ValidationError):
            RunningEntry(pace="5:00", pace_unit="sec/km")  # type: ignore[arg-type]

    def test_workout_type_all_valid_values(self) -> None:
        """Test that all workout_type Literal values are valid."""
        from swealog.domains import RunningEntry

        valid_types = [
            "easy",
            "tempo",
            "threshold",
            "interval",
            "long_run",
            "recovery",
            "race",
            "fartlek",
        ]
        for wt in valid_types:
            e = RunningEntry(workout_type=wt)  # type: ignore[arg-type]
            assert e.workout_type == wt

    def test_workout_type_invalid_fails(self) -> None:
        """Test that invalid workout_type raises ValidationError."""
        from swealog.domains import RunningEntry

        with pytest.raises(ValidationError):
            RunningEntry(workout_type="sprint")  # type: ignore[arg-type]

    def test_terrain_all_valid_values(self) -> None:
        """Test that all terrain Literal values are valid."""
        from swealog.domains import RunningEntry

        valid_terrains = ["road", "trail", "track", "treadmill", "mixed"]
        for t in valid_terrains:
            e = RunningEntry(terrain=t)  # type: ignore[arg-type]
            assert e.terrain == t

    def test_terrain_invalid_fails(self) -> None:
        """Test that invalid terrain raises ValidationError."""
        from swealog.domains import RunningEntry

        with pytest.raises(ValidationError):
            RunningEntry(terrain="mountain")  # type: ignore[arg-type]


class TestRunningEntryWithNestedModels:
    """Tests for RunningEntry with splits and intervals."""

    def test_splits_default_empty(self) -> None:
        """Test that splits list defaults to empty."""
        from swealog.domains import RunningEntry

        e = RunningEntry()
        assert e.splits == []

    def test_entry_with_splits(self) -> None:
        """Test creating entry with splits."""
        from swealog.domains import RunningEntry, RunningSplit

        splits = [
            RunningSplit(split_number=1, distance=1.0, duration_seconds=300.0),
            RunningSplit(split_number=2, distance=1.0, duration_seconds=295.0),
            RunningSplit(split_number=3, distance=1.0, duration_seconds=290.0, pace="4:50 min/km"),
        ]
        e = RunningEntry(distance=3.0, distance_unit="km", splits=splits)
        assert len(e.splits) == 3
        assert e.splits[2].pace == "4:50 min/km"

    def test_intervals_default_empty(self) -> None:
        """Test that intervals list defaults to empty."""
        from swealog.domains import RunningEntry

        e = RunningEntry()
        assert e.intervals == []

    def test_entry_with_intervals(self) -> None:
        """Test creating entry with intervals."""
        from swealog.domains import RunningEntry, RunningInterval

        intervals = [
            RunningInterval(
                work_distance=400.0,
                work_duration_seconds=90.0,
                rest_duration_seconds=60.0,
                repetitions=4,
            ),
        ]
        e = RunningEntry(workout_type="interval", intervals=intervals)
        assert len(e.intervals) == 1
        assert e.intervals[0].repetitions == 4


class TestRunningDomainModule:
    """Tests for Running DomainModule configuration."""

    def test_instantiation(self) -> None:
        """Test that Running domain can be instantiated."""
        from swealog.domains import Running, running

        assert running is not None
        assert isinstance(running, Running)

    def test_name_defaults_to_class_name(self) -> None:
        """Test that domain name defaults to class name."""
        from swealog.domains import running

        assert running.name == "Running"

    def test_description_non_empty(self) -> None:
        """Test that description is non-empty."""
        from swealog.domains import running

        assert running.description
        assert len(running.description) > 0

    def test_log_schema_is_running_entry(self) -> None:
        """Test that Running domain's log_schema is RunningEntry."""
        from swealog.domains import RunningEntry, running

        assert running.log_schema is RunningEntry


class TestRunningVocabularyEnglish:
    """Tests for Running vocabulary - English terms."""

    def test_vocabulary_distance_abbreviations(self) -> None:
        """Test that vocabulary contains distance abbreviations."""
        from swealog.domains import running

        assert running.vocabulary["5k"] == "5 kilometers"
        assert running.vocabulary["10k"] == "10 kilometers"
        assert running.vocabulary["hm"] == "half marathon"
        assert running.vocabulary["fm"] == "full marathon"

    def test_vocabulary_unit_abbreviations(self) -> None:
        """Test that vocabulary contains unit abbreviations."""
        from swealog.domains import running

        assert running.vocabulary["mi"] == "miles"
        assert running.vocabulary["km"] == "kilometers"
        assert running.vocabulary["m"] == "meters"

    def test_vocabulary_activity_variations(self) -> None:
        """Test that vocabulary contains activity variations."""
        from swealog.domains import running

        assert running.vocabulary["ran"] == "running"
        assert running.vocabulary["run"] == "running"
        assert running.vocabulary["jog"] == "jogging"
        assert running.vocabulary["jogged"] == "jogging"
        assert running.vocabulary["sprint"] == "sprinting"
        assert running.vocabulary["tempo"] == "tempo run"
        assert running.vocabulary["intervals"] == "interval training"

    def test_vocabulary_terrain_terms(self) -> None:
        """Test that vocabulary contains terrain normalization terms."""
        from swealog.domains import running

        # Non-identity terrain mappings
        assert running.vocabulary["hills"] == "hilly"
        assert running.vocabulary["flat"] == "flat terrain"
        # Korean terrain terms
        assert running.vocabulary["트레일"] == "trail"
        assert running.vocabulary["트랙"] == "track"

    def test_vocabulary_workout_type_normalizations(self) -> None:
        """Test that vocabulary contains workout type normalizations."""
        from swealog.domains import running

        assert running.vocabulary["easy run"] == "easy"
        assert running.vocabulary["recovery run"] == "recovery"
        assert running.vocabulary["tempo run"] == "tempo"
        assert running.vocabulary["speed work"] == "interval"
        # Note: "fartlek" removed as redundant identity mapping


class TestRunningVocabularyKorean:
    """Tests for Running vocabulary - Korean terms."""

    def test_korean_running_terms(self) -> None:
        """Test Korean running activity terms."""
        from swealog.domains import running

        assert running.vocabulary["러닝"] == "running"
        assert running.vocabulary["달리기"] == "running"
        assert running.vocabulary["조깅"] == "jogging"

    def test_korean_workout_types(self) -> None:
        """Test Korean workout type terms map to Literal values."""
        from swealog.domains import running

        assert running.vocabulary["템포런"] == "tempo"
        assert running.vocabulary["인터벌"] == "interval"
        assert running.vocabulary["롱런"] == "long_run"

    def test_korean_distance_units(self) -> None:
        """Test Korean distance/unit terms."""
        from swealog.domains import running

        assert running.vocabulary["킬로미터"] == "kilometers"
        assert running.vocabulary["마일"] == "miles"
        assert running.vocabulary["미터"] == "meters"

    def test_korean_terrain_terms(self) -> None:
        """Test Korean terrain terms."""
        from swealog.domains import running

        assert running.vocabulary["러닝머신"] == "treadmill"
        assert running.vocabulary["트레일"] == "trail"
        assert running.vocabulary["트랙"] == "track"


class TestRunningExpertiseAndRules:
    """Tests for Running expertise, evaluation rules, and context guidance."""

    def test_expertise_non_empty(self) -> None:
        """Test that expertise is non-empty."""
        from swealog.domains import running

        assert running.expertise
        assert len(running.expertise) > 0
        assert "base building" in running.expertise or "progressive" in running.expertise

    def test_response_evaluation_rules_populated(self) -> None:
        """Test that response_evaluation_rules is populated."""
        from swealog.domains import running

        assert running.response_evaluation_rules
        assert len(running.response_evaluation_rules) > 0
        assert any("10%" in rule for rule in running.response_evaluation_rules)

    def test_context_management_guidance_populated(self) -> None:
        """Test that context_management_guidance is populated."""
        from swealog.domains import running

        assert running.context_management_guidance
        assert len(running.context_management_guidance) > 0
        assert "mileage" in running.context_management_guidance.lower()


class TestRunningCoexistence:
    """Tests for Running domain coexisting with other domains."""

    def test_running_and_general_fitness_coexist(self) -> None:
        """Test that Running and GeneralFitness can coexist."""
        from swealog.domains import GeneralFitness, Running, general_fitness, running

        assert running is not None
        assert general_fitness is not None
        assert isinstance(running, Running)
        assert isinstance(general_fitness, GeneralFitness)
        assert running.name != general_fitness.name

    def test_running_and_strength_coexist(self) -> None:
        """Test that Running and Strength can coexist."""
        from swealog.domains import Running, Strength, running, strength

        assert running is not None
        assert strength is not None
        assert isinstance(running, Running)
        assert isinstance(strength, Strength)
        assert running.name != strength.name

    def test_running_and_nutrition_coexist(self) -> None:
        """Test that Running and Nutrition can coexist."""
        from swealog.domains import Nutrition, Running, nutrition, running

        assert running is not None
        assert nutrition is not None
        assert isinstance(running, Running)
        assert isinstance(nutrition, Nutrition)
        assert running.name != nutrition.name


class TestRunningExports:
    """Tests for Running exports from swealog.domains."""

    def test_all_exports_importable(self) -> None:
        """Test that all Running exports are importable from swealog.domains."""
        from swealog.domains import (
            Running,
            RunningEntry,
            RunningInterval,
            RunningSplit,
            running,
        )

        assert Running is not None
        assert RunningEntry is not None
        assert RunningInterval is not None
        assert RunningSplit is not None
        assert running is not None

    def test_running_in_all_list(self) -> None:
        """Test that Running exports are in __all__ list."""
        from swealog import domains

        assert "Running" in domains.__all__
        assert "RunningEntry" in domains.__all__
        assert "RunningInterval" in domains.__all__
        assert "RunningSplit" in domains.__all__
        assert "running" in domains.__all__
