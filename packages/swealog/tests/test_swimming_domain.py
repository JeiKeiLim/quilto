"""Tests for the Swimming domain module."""

import pytest
from pydantic import ValidationError


class TestSwimmingLapValidation:
    """Tests for SwimmingLap model validation."""

    def test_lap_number_boundary_one_succeeds(self) -> None:
        """Test that lap_number exactly 1 succeeds."""
        from swealog.domains import SwimmingLap

        lap = SwimmingLap(lap_number=1)
        assert lap.lap_number == 1

    def test_lap_number_boundary_zero_fails(self) -> None:
        """Test that lap_number 0 raises ValidationError."""
        from swealog.domains import SwimmingLap

        with pytest.raises(ValidationError) as exc_info:
            SwimmingLap(lap_number=0)
        assert "greater than or equal to 1" in str(exc_info.value)

    def test_lap_number_negative_fails(self) -> None:
        """Test that negative lap_number raises ValidationError."""
        from swealog.domains import SwimmingLap

        with pytest.raises(ValidationError) as exc_info:
            SwimmingLap(lap_number=-1)
        assert "greater than or equal to 1" in str(exc_info.value)

    def test_duration_seconds_boundary_zero_succeeds(self) -> None:
        """Test that duration_seconds 0.0 succeeds."""
        from swealog.domains import SwimmingLap

        lap = SwimmingLap(lap_number=1, duration_seconds=0.0)
        assert lap.duration_seconds == 0.0

    def test_duration_seconds_negative_fails(self) -> None:
        """Test that negative duration_seconds raises ValidationError."""
        from swealog.domains import SwimmingLap

        with pytest.raises(ValidationError) as exc_info:
            SwimmingLap(lap_number=1, duration_seconds=-1.0)
        assert "greater than or equal to 0" in str(exc_info.value)

    def test_stroke_type_all_valid_values(self) -> None:
        """Test that all stroke_type Literal values are valid."""
        from swealog.domains import SwimmingLap

        valid_strokes = ["freestyle", "backstroke", "breaststroke", "butterfly", "im"]
        for stroke in valid_strokes:
            lap = SwimmingLap(lap_number=1, stroke_type=stroke)  # type: ignore[arg-type]
            assert lap.stroke_type == stroke

    def test_stroke_type_invalid_fails(self) -> None:
        """Test that invalid stroke_type raises ValidationError."""
        from swealog.domains import SwimmingLap

        with pytest.raises(ValidationError):
            SwimmingLap(lap_number=1, stroke_type="crawl")  # type: ignore[arg-type]

    def test_optional_fields_can_be_none(self) -> None:
        """Test that optional fields can be None."""
        from swealog.domains import SwimmingLap

        lap = SwimmingLap(lap_number=1)
        assert lap.stroke_type is None
        assert lap.duration_seconds is None
        assert lap.notes is None


class TestSwimmingIntervalValidation:
    """Tests for SwimmingInterval model validation."""

    def test_repetitions_boundary_one_succeeds(self) -> None:
        """Test that repetitions exactly 1 succeeds."""
        from swealog.domains import SwimmingInterval

        interval = SwimmingInterval(repetitions=1, distance=100.0)
        assert interval.repetitions == 1

    def test_repetitions_boundary_zero_fails(self) -> None:
        """Test that repetitions 0 raises ValidationError."""
        from swealog.domains import SwimmingInterval

        with pytest.raises(ValidationError) as exc_info:
            SwimmingInterval(repetitions=0, distance=100.0)
        assert "greater than or equal to 1" in str(exc_info.value)

    def test_repetitions_negative_fails(self) -> None:
        """Test that negative repetitions raises ValidationError."""
        from swealog.domains import SwimmingInterval

        with pytest.raises(ValidationError) as exc_info:
            SwimmingInterval(repetitions=-1, distance=100.0)
        assert "greater than or equal to 1" in str(exc_info.value)

    def test_distance_boundary_zero_succeeds(self) -> None:
        """Test that distance 0.0 succeeds."""
        from swealog.domains import SwimmingInterval

        interval = SwimmingInterval(repetitions=1, distance=0.0)
        assert interval.distance == 0.0

    def test_distance_negative_fails(self) -> None:
        """Test that negative distance raises ValidationError."""
        from swealog.domains import SwimmingInterval

        with pytest.raises(ValidationError) as exc_info:
            SwimmingInterval(repetitions=1, distance=-1.0)
        assert "greater than or equal to 0" in str(exc_info.value)

    def test_interval_seconds_boundary_zero_succeeds(self) -> None:
        """Test that interval_seconds 0.0 succeeds."""
        from swealog.domains import SwimmingInterval

        interval = SwimmingInterval(repetitions=1, distance=100.0, interval_seconds=0.0)
        assert interval.interval_seconds == 0.0

    def test_interval_seconds_negative_fails(self) -> None:
        """Test that negative interval_seconds raises ValidationError."""
        from swealog.domains import SwimmingInterval

        with pytest.raises(ValidationError) as exc_info:
            SwimmingInterval(repetitions=1, distance=100.0, interval_seconds=-1.0)
        assert "greater than or equal to 0" in str(exc_info.value)

    def test_rest_seconds_boundary_zero_succeeds(self) -> None:
        """Test that rest_seconds 0.0 succeeds."""
        from swealog.domains import SwimmingInterval

        interval = SwimmingInterval(repetitions=1, distance=100.0, rest_seconds=0.0)
        assert interval.rest_seconds == 0.0

    def test_rest_seconds_negative_fails(self) -> None:
        """Test that negative rest_seconds raises ValidationError."""
        from swealog.domains import SwimmingInterval

        with pytest.raises(ValidationError) as exc_info:
            SwimmingInterval(repetitions=1, distance=100.0, rest_seconds=-1.0)
        assert "greater than or equal to 0" in str(exc_info.value)

    def test_stroke_type_all_valid_values(self) -> None:
        """Test that all stroke_type Literal values are valid including 'choice'."""
        from swealog.domains import SwimmingInterval

        valid_strokes = [
            "freestyle",
            "backstroke",
            "breaststroke",
            "butterfly",
            "im",
            "choice",
        ]
        for stroke in valid_strokes:
            interval = SwimmingInterval(
                repetitions=1, distance=100.0, stroke_type=stroke  # type: ignore[arg-type]
            )
            assert interval.stroke_type == stroke

    def test_stroke_type_invalid_fails(self) -> None:
        """Test that invalid stroke_type raises ValidationError."""
        from swealog.domains import SwimmingInterval

        with pytest.raises(ValidationError):
            SwimmingInterval(
                repetitions=1, distance=100.0, stroke_type="crawl"  # type: ignore[arg-type]
            )

    def test_distance_unit_all_valid_values(self) -> None:
        """Test that all distance_unit Literal values are valid."""
        from swealog.domains import SwimmingInterval

        valid_units = ["m", "y", "laps"]
        for unit in valid_units:
            interval = SwimmingInterval(
                repetitions=1, distance=100.0, distance_unit=unit  # type: ignore[arg-type]
            )
            assert interval.distance_unit == unit

    def test_distance_unit_invalid_fails(self) -> None:
        """Test that invalid distance_unit raises ValidationError."""
        from swealog.domains import SwimmingInterval

        with pytest.raises(ValidationError):
            SwimmingInterval(
                repetitions=1, distance=100.0, distance_unit="meters"  # type: ignore[arg-type]
            )

    def test_optional_fields_can_be_none(self) -> None:
        """Test that optional fields can be None."""
        from swealog.domains import SwimmingInterval

        interval = SwimmingInterval(repetitions=1, distance=100.0)
        assert interval.distance_unit is None
        assert interval.stroke_type is None
        assert interval.interval_seconds is None
        assert interval.rest_seconds is None
        assert interval.notes is None


class TestSwimmingEntryValidation:
    """Tests for SwimmingEntry model validation."""

    def test_laps_boundary_zero_succeeds(self) -> None:
        """Test that laps 0 succeeds."""
        from swealog.domains import SwimmingEntry

        entry = SwimmingEntry(laps=0)
        assert entry.laps == 0

    def test_laps_negative_fails(self) -> None:
        """Test that negative laps raises ValidationError."""
        from swealog.domains import SwimmingEntry

        with pytest.raises(ValidationError) as exc_info:
            SwimmingEntry(laps=-1)
        assert "greater than or equal to 0" in str(exc_info.value)

    def test_distance_boundary_zero_succeeds(self) -> None:
        """Test that distance 0.0 succeeds."""
        from swealog.domains import SwimmingEntry

        entry = SwimmingEntry(distance=0.0)
        assert entry.distance == 0.0

    def test_distance_negative_fails(self) -> None:
        """Test that negative distance raises ValidationError."""
        from swealog.domains import SwimmingEntry

        with pytest.raises(ValidationError) as exc_info:
            SwimmingEntry(distance=-1.0)
        assert "greater than or equal to 0" in str(exc_info.value)

    def test_duration_minutes_boundary_zero_succeeds(self) -> None:
        """Test that duration_minutes 0.0 succeeds."""
        from swealog.domains import SwimmingEntry

        entry = SwimmingEntry(duration_minutes=0.0)
        assert entry.duration_minutes == 0.0

    def test_duration_minutes_fractional_succeeds(self) -> None:
        """Test that duration_minutes can be fractional (float type)."""
        from swealog.domains import SwimmingEntry

        entry = SwimmingEntry(duration_minutes=30.5)
        assert entry.duration_minutes == 30.5

    def test_duration_minutes_negative_fails(self) -> None:
        """Test that negative duration_minutes raises ValidationError."""
        from swealog.domains import SwimmingEntry

        with pytest.raises(ValidationError) as exc_info:
            SwimmingEntry(duration_minutes=-1.0)
        assert "greater than or equal to 0" in str(exc_info.value)

    def test_pool_length_boundary_zero_succeeds(self) -> None:
        """Test that pool_length 0.0 succeeds."""
        from swealog.domains import SwimmingEntry

        entry = SwimmingEntry(pool_length=0.0)
        assert entry.pool_length == 0.0

    def test_pool_length_negative_fails(self) -> None:
        """Test that negative pool_length raises ValidationError."""
        from swealog.domains import SwimmingEntry

        with pytest.raises(ValidationError) as exc_info:
            SwimmingEntry(pool_length=-1.0)
        assert "greater than or equal to 0" in str(exc_info.value)

    def test_perceived_exertion_boundary_one_succeeds(self) -> None:
        """Test that perceived_exertion exactly 1 succeeds."""
        from swealog.domains import SwimmingEntry

        entry = SwimmingEntry(perceived_exertion=1)
        assert entry.perceived_exertion == 1

    def test_perceived_exertion_boundary_ten_succeeds(self) -> None:
        """Test that perceived_exertion exactly 10 succeeds."""
        from swealog.domains import SwimmingEntry

        entry = SwimmingEntry(perceived_exertion=10)
        assert entry.perceived_exertion == 10

    def test_perceived_exertion_below_one_fails(self) -> None:
        """Test that perceived_exertion below 1 raises ValidationError."""
        from swealog.domains import SwimmingEntry

        with pytest.raises(ValidationError) as exc_info:
            SwimmingEntry(perceived_exertion=0)
        assert "greater than or equal to 1" in str(exc_info.value)

    def test_perceived_exertion_above_ten_fails(self) -> None:
        """Test that perceived_exertion above 10 raises ValidationError."""
        from swealog.domains import SwimmingEntry

        with pytest.raises(ValidationError) as exc_info:
            SwimmingEntry(perceived_exertion=11)
        assert "less than or equal to 10" in str(exc_info.value)

    def test_average_heart_rate_boundary_zero_succeeds(self) -> None:
        """Test that average_heart_rate 0 succeeds."""
        from swealog.domains import SwimmingEntry

        entry = SwimmingEntry(average_heart_rate=0)
        assert entry.average_heart_rate == 0

    def test_average_heart_rate_negative_fails(self) -> None:
        """Test that negative average_heart_rate raises ValidationError."""
        from swealog.domains import SwimmingEntry

        with pytest.raises(ValidationError) as exc_info:
            SwimmingEntry(average_heart_rate=-1)
        assert "greater than or equal to 0" in str(exc_info.value)

    def test_max_heart_rate_boundary_zero_succeeds(self) -> None:
        """Test that max_heart_rate 0 succeeds."""
        from swealog.domains import SwimmingEntry

        entry = SwimmingEntry(max_heart_rate=0)
        assert entry.max_heart_rate == 0

    def test_max_heart_rate_negative_fails(self) -> None:
        """Test that negative max_heart_rate raises ValidationError."""
        from swealog.domains import SwimmingEntry

        with pytest.raises(ValidationError) as exc_info:
            SwimmingEntry(max_heart_rate=-1)
        assert "greater than or equal to 0" in str(exc_info.value)


class TestSwimmingEntryLiteralTypes:
    """Tests for SwimmingEntry Literal type validation."""

    def test_stroke_type_all_valid_values(self) -> None:
        """Test that all stroke_type Literal values are valid including 'mixed'."""
        from swealog.domains import SwimmingEntry

        valid_strokes = [
            "freestyle",
            "backstroke",
            "breaststroke",
            "butterfly",
            "im",
            "mixed",
        ]
        for stroke in valid_strokes:
            entry = SwimmingEntry(stroke_type=stroke)  # type: ignore[arg-type]
            assert entry.stroke_type == stroke

    def test_stroke_type_invalid_fails(self) -> None:
        """Test that invalid stroke_type raises ValidationError."""
        from swealog.domains import SwimmingEntry

        with pytest.raises(ValidationError):
            SwimmingEntry(stroke_type="crawl")  # type: ignore[arg-type]

    def test_workout_type_all_valid_values(self) -> None:
        """Test that all workout_type Literal values are valid."""
        from swealog.domains import SwimmingEntry

        valid_types = [
            "endurance",
            "sprint",
            "drill",
            "technique",
            "recovery",
            "race",
            "open_water",
        ]
        for wt in valid_types:
            entry = SwimmingEntry(workout_type=wt)  # type: ignore[arg-type]
            assert entry.workout_type == wt

    def test_workout_type_invalid_fails(self) -> None:
        """Test that invalid workout_type raises ValidationError."""
        from swealog.domains import SwimmingEntry

        with pytest.raises(ValidationError):
            SwimmingEntry(workout_type="casual")  # type: ignore[arg-type]

    def test_distance_unit_all_valid_values(self) -> None:
        """Test that all distance_unit Literal values are valid."""
        from swealog.domains import SwimmingEntry

        valid_units = ["m", "y", "laps"]
        for unit in valid_units:
            entry = SwimmingEntry(distance=100.0, distance_unit=unit)  # type: ignore[arg-type]
            assert entry.distance_unit == unit

    def test_distance_unit_invalid_fails(self) -> None:
        """Test that invalid distance_unit raises ValidationError."""
        from swealog.domains import SwimmingEntry

        with pytest.raises(ValidationError):
            SwimmingEntry(distance=100.0, distance_unit="meters")  # type: ignore[arg-type]

    def test_pool_length_unit_all_valid_values(self) -> None:
        """Test that all pool_length_unit Literal values are valid."""
        from swealog.domains import SwimmingEntry

        valid_units = ["m", "y"]
        for unit in valid_units:
            entry = SwimmingEntry(pool_length=25.0, pool_length_unit=unit)  # type: ignore[arg-type]
            assert entry.pool_length_unit == unit

    def test_pool_length_unit_invalid_fails(self) -> None:
        """Test that invalid pool_length_unit raises ValidationError."""
        from swealog.domains import SwimmingEntry

        with pytest.raises(ValidationError):
            SwimmingEntry(pool_length=25.0, pool_length_unit="meters")  # type: ignore[arg-type]


class TestSwimmingEntryDefaults:
    """Tests for SwimmingEntry default values."""

    def test_open_water_defaults_to_false(self) -> None:
        """Test that open_water defaults to False."""
        from swealog.domains import SwimmingEntry

        entry = SwimmingEntry()
        assert entry.open_water is False

    def test_lap_times_defaults_to_empty_list(self) -> None:
        """Test that lap_times defaults to empty list."""
        from swealog.domains import SwimmingEntry

        entry = SwimmingEntry()
        assert entry.lap_times == []

    def test_intervals_defaults_to_empty_list(self) -> None:
        """Test that intervals defaults to empty list."""
        from swealog.domains import SwimmingEntry

        entry = SwimmingEntry()
        assert entry.intervals == []

    def test_equipment_defaults_to_empty_list(self) -> None:
        """Test that equipment defaults to empty list."""
        from swealog.domains import SwimmingEntry

        entry = SwimmingEntry()
        assert entry.equipment == []


class TestSwimmingEntryOptionalStrings:
    """Tests for SwimmingEntry optional string fields."""

    def test_notes_empty_string_succeeds(self) -> None:
        """Test that notes can be an empty string."""
        from swealog.domains import SwimmingEntry

        entry = SwimmingEntry(notes="")
        assert entry.notes == ""

    def test_notes_none_succeeds(self) -> None:
        """Test that notes can be None."""
        from swealog.domains import SwimmingEntry

        entry = SwimmingEntry()
        assert entry.notes is None

    def test_average_pace_empty_string_succeeds(self) -> None:
        """Test that average_pace can be an empty string."""
        from swealog.domains import SwimmingEntry

        entry = SwimmingEntry(average_pace="")
        assert entry.average_pace == ""

    def test_date_empty_string_succeeds(self) -> None:
        """Test that date can be an empty string."""
        from swealog.domains import SwimmingEntry

        entry = SwimmingEntry(date="")
        assert entry.date == ""


class TestSwimmingEntryWaterTemperature:
    """Tests for SwimmingEntry water_temperature field."""

    def test_water_temperature_can_be_negative(self) -> None:
        """Test that water_temperature can be negative (cold water)."""
        from swealog.domains import SwimmingEntry

        entry = SwimmingEntry(water_temperature=-2.0, open_water=True)
        assert entry.water_temperature == -2.0

    def test_water_temperature_can_be_positive(self) -> None:
        """Test that water_temperature can be positive."""
        from swealog.domains import SwimmingEntry

        entry = SwimmingEntry(water_temperature=28.5)
        assert entry.water_temperature == 28.5

    def test_water_temperature_can_be_zero(self) -> None:
        """Test that water_temperature can be zero."""
        from swealog.domains import SwimmingEntry

        entry = SwimmingEntry(water_temperature=0.0)
        assert entry.water_temperature == 0.0


class TestSwimmingEntryWithNestedModels:
    """Tests for SwimmingEntry with nested lap_times and intervals."""

    def test_entry_with_lap_times(self) -> None:
        """Test creating entry with lap_times."""
        from swealog.domains import SwimmingEntry, SwimmingLap

        laps = [
            SwimmingLap(lap_number=1, stroke_type="freestyle", duration_seconds=35.0),
            SwimmingLap(lap_number=2, stroke_type="freestyle", duration_seconds=36.0),
        ]
        entry = SwimmingEntry(laps=2, lap_times=laps)
        assert len(entry.lap_times) == 2
        assert entry.lap_times[0].stroke_type == "freestyle"

    def test_entry_with_intervals(self) -> None:
        """Test creating entry with intervals."""
        from swealog.domains import SwimmingEntry, SwimmingInterval

        intervals = [
            SwimmingInterval(
                repetitions=10,
                distance=100.0,
                distance_unit="m",
                stroke_type="freestyle",
                interval_seconds=90.0,
            ),
        ]
        entry = SwimmingEntry(workout_type="endurance", intervals=intervals)
        assert len(entry.intervals) == 1
        assert entry.intervals[0].repetitions == 10

    def test_entry_with_equipment(self) -> None:
        """Test creating entry with equipment list."""
        from swealog.domains import SwimmingEntry

        entry = SwimmingEntry(equipment=["paddles", "pull buoy", "fins"])
        assert len(entry.equipment) == 3
        assert "paddles" in entry.equipment


class TestSwimmingDomainModule:
    """Tests for Swimming DomainModule configuration."""

    def test_instantiation(self) -> None:
        """Test that Swimming domain can be instantiated."""
        from swealog.domains import Swimming, swimming

        assert swimming is not None
        assert isinstance(swimming, Swimming)

    def test_name_defaults_to_class_name(self) -> None:
        """Test that domain name defaults to class name."""
        from swealog.domains import swimming

        assert swimming.name == "Swimming"

    def test_description_non_empty(self) -> None:
        """Test that description is non-empty."""
        from swealog.domains import swimming

        assert swimming.description
        assert len(swimming.description) > 0

    def test_log_schema_is_swimming_entry(self) -> None:
        """Test that Swimming domain's log_schema is SwimmingEntry."""
        from swealog.domains import SwimmingEntry, swimming

        assert swimming.log_schema is SwimmingEntry


class TestSwimmingVocabularyEnglishStrokes:
    """Tests for Swimming vocabulary - English stroke normalizations."""

    def test_vocabulary_free_to_freestyle(self) -> None:
        """Test that 'free' maps to 'freestyle'."""
        from swealog.domains import swimming

        assert swimming.vocabulary["free"] == "freestyle"

    def test_vocabulary_front_crawl_to_freestyle(self) -> None:
        """Test that 'front crawl' maps to 'freestyle'."""
        from swealog.domains import swimming

        assert swimming.vocabulary["front crawl"] == "freestyle"

    def test_vocabulary_back_to_backstroke(self) -> None:
        """Test that 'back' maps to 'backstroke'."""
        from swealog.domains import swimming

        assert swimming.vocabulary["back"] == "backstroke"

    def test_vocabulary_breast_to_breaststroke(self) -> None:
        """Test that 'breast' maps to 'breaststroke'."""
        from swealog.domains import swimming

        assert swimming.vocabulary["breast"] == "breaststroke"

    def test_vocabulary_fly_to_butterfly(self) -> None:
        """Test that 'fly' maps to 'butterfly'."""
        from swealog.domains import swimming

        assert swimming.vocabulary["fly"] == "butterfly"

    def test_vocabulary_butterfly_stroke_to_butterfly(self) -> None:
        """Test that 'butterfly stroke' maps to 'butterfly'."""
        from swealog.domains import swimming

        assert swimming.vocabulary["butterfly stroke"] == "butterfly"

    def test_vocabulary_im_to_individual_medley(self) -> None:
        """Test that 'im' maps to 'individual medley'."""
        from swealog.domains import swimming

        assert swimming.vocabulary["im"] == "individual medley"

    def test_vocabulary_medley_to_individual_medley(self) -> None:
        """Test that 'medley' maps to 'individual medley'."""
        from swealog.domains import swimming

        assert swimming.vocabulary["medley"] == "individual medley"


class TestSwimmingVocabularyKoreanStrokes:
    """Tests for Swimming vocabulary - Korean stroke normalizations."""

    def test_korean_freestyle(self) -> None:
        """Test Korean freestyle term."""
        from swealog.domains import swimming

        assert swimming.vocabulary["자유형"] == "freestyle"

    def test_korean_backstroke(self) -> None:
        """Test Korean backstroke term."""
        from swealog.domains import swimming

        assert swimming.vocabulary["배영"] == "backstroke"

    def test_korean_breaststroke(self) -> None:
        """Test Korean breaststroke term."""
        from swealog.domains import swimming

        assert swimming.vocabulary["평영"] == "breaststroke"

    def test_korean_butterfly(self) -> None:
        """Test Korean butterfly term."""
        from swealog.domains import swimming

        assert swimming.vocabulary["접영"] == "butterfly"

    def test_korean_individual_medley(self) -> None:
        """Test Korean individual medley term."""
        from swealog.domains import swimming

        assert swimming.vocabulary["개인혼영"] == "individual medley"


class TestSwimmingVocabularyDistanceAndPool:
    """Tests for Swimming vocabulary - distance and pool normalizations."""

    def test_vocabulary_m_to_meters(self) -> None:
        """Test that 'm' maps to 'meters'."""
        from swealog.domains import swimming

        assert swimming.vocabulary["m"] == "meters"

    def test_vocabulary_y_to_yards(self) -> None:
        """Test that 'y' maps to 'yards'."""
        from swealog.domains import swimming

        assert swimming.vocabulary["y"] == "yards"

    def test_vocabulary_olympic_to_50_meters(self) -> None:
        """Test that 'olympic' maps to '50 meters'."""
        from swealog.domains import swimming

        assert swimming.vocabulary["olympic"] == "50 meters"

    def test_vocabulary_short_course_to_25_meters(self) -> None:
        """Test that 'short course' maps to '25 meters'."""
        from swealog.domains import swimming

        assert swimming.vocabulary["short course"] == "25 meters"

    def test_vocabulary_sc_to_25_meters(self) -> None:
        """Test that 'sc' maps to '25 meters'."""
        from swealog.domains import swimming

        assert swimming.vocabulary["sc"] == "25 meters"

    def test_vocabulary_long_course_to_50_meters(self) -> None:
        """Test that 'long course' maps to '50 meters'."""
        from swealog.domains import swimming

        assert swimming.vocabulary["long course"] == "50 meters"

    def test_vocabulary_lc_to_50_meters(self) -> None:
        """Test that 'lc' maps to '50 meters'."""
        from swealog.domains import swimming

        assert swimming.vocabulary["lc"] == "50 meters"


class TestSwimmingVocabularyKoreanDistanceUnits:
    """Tests for Swimming vocabulary - Korean distance/unit terms."""

    def test_korean_meters(self) -> None:
        """Test Korean meters term."""
        from swealog.domains import swimming

        assert swimming.vocabulary["미터"] == "meters"

    def test_korean_yards(self) -> None:
        """Test Korean yards term."""
        from swealog.domains import swimming

        assert swimming.vocabulary["야드"] == "yards"


class TestSwimmingVocabularyEquipment:
    """Tests for Swimming vocabulary - equipment normalizations."""

    def test_vocabulary_hand_paddles_to_paddles(self) -> None:
        """Test that 'hand paddles' maps to 'paddles'."""
        from swealog.domains import swimming

        assert swimming.vocabulary["hand paddles"] == "paddles"

    def test_vocabulary_flippers_to_fins(self) -> None:
        """Test that 'flippers' maps to 'fins'."""
        from swealog.domains import swimming

        assert swimming.vocabulary["flippers"] == "fins"

    def test_vocabulary_pull_to_pull_buoy(self) -> None:
        """Test that 'pull' maps to 'pull buoy'."""
        from swealog.domains import swimming

        assert swimming.vocabulary["pull"] == "pull buoy"

    def test_vocabulary_kick_to_kickboard(self) -> None:
        """Test that 'kick' maps to 'kickboard'."""
        from swealog.domains import swimming

        assert swimming.vocabulary["kick"] == "kickboard"

    def test_vocabulary_center_snorkel_to_snorkel(self) -> None:
        """Test that 'center snorkel' maps to 'snorkel'."""
        from swealog.domains import swimming

        assert swimming.vocabulary["center snorkel"] == "snorkel"


class TestSwimmingVocabularyKoreanEquipment:
    """Tests for Swimming vocabulary - Korean equipment terms."""

    def test_korean_paddles(self) -> None:
        """Test Korean paddles term."""
        from swealog.domains import swimming

        assert swimming.vocabulary["패들"] == "paddles"

    def test_korean_fins(self) -> None:
        """Test Korean fins term."""
        from swealog.domains import swimming

        assert swimming.vocabulary["오리발"] == "fins"

    def test_korean_pull_buoy(self) -> None:
        """Test Korean pull buoy term."""
        from swealog.domains import swimming

        assert swimming.vocabulary["풀부이"] == "pull buoy"

    def test_korean_kickboard(self) -> None:
        """Test Korean kickboard term."""
        from swealog.domains import swimming

        assert swimming.vocabulary["킥보드"] == "kickboard"


class TestSwimmingVocabularyActivity:
    """Tests for Swimming vocabulary - activity normalizations."""

    def test_vocabulary_swam_to_swimming(self) -> None:
        """Test that 'swam' maps to 'swimming'."""
        from swealog.domains import swimming

        assert swimming.vocabulary["swam"] == "swimming"

    def test_vocabulary_swim_to_swimming(self) -> None:
        """Test that 'swim' maps to 'swimming'."""
        from swealog.domains import swimming

        assert swimming.vocabulary["swim"] == "swimming"

    def test_korean_swimming(self) -> None:
        """Test Korean swimming term."""
        from swealog.domains import swimming

        assert swimming.vocabulary["수영"] == "swimming"

    def test_korean_laps(self) -> None:
        """Test Korean laps term."""
        from swealog.domains import swimming

        assert swimming.vocabulary["랩"] == "laps"


class TestSwimmingExpertiseAndRules:
    """Tests for Swimming expertise, evaluation rules, and context guidance."""

    def test_expertise_non_empty(self) -> None:
        """Test that expertise is non-empty."""
        from swealog.domains import swimming

        assert swimming.expertise
        assert len(swimming.expertise) > 0

    def test_expertise_contains_swimming_concepts(self) -> None:
        """Test that expertise covers swimming-specific concepts."""
        from swealog.domains import swimming

        expertise_lower = swimming.expertise.lower()
        assert "stroke" in expertise_lower or "pace" in expertise_lower
        assert "interval" in expertise_lower

    def test_response_evaluation_rules_populated(self) -> None:
        """Test that response_evaluation_rules is populated."""
        from swealog.domains import swimming

        assert swimming.response_evaluation_rules
        assert len(swimming.response_evaluation_rules) > 0

    def test_response_evaluation_rules_contain_volume_rule(self) -> None:
        """Test that rules include the 10% volume increase rule."""
        from swealog.domains import swimming

        assert any("10%" in rule for rule in swimming.response_evaluation_rules)

    def test_context_management_guidance_populated(self) -> None:
        """Test that context_management_guidance is populated."""
        from swealog.domains import swimming

        assert swimming.context_management_guidance
        assert len(swimming.context_management_guidance) > 0


class TestSwimmingClarificationPatterns:
    """Tests for Swimming clarification patterns."""

    def test_subjective_patterns_populated(self) -> None:
        """Test that SUBJECTIVE patterns are populated."""
        from swealog.domains import swimming

        assert "SUBJECTIVE" in swimming.clarification_patterns
        assert len(swimming.clarification_patterns["SUBJECTIVE"]) > 0

    def test_clarification_patterns_populated(self) -> None:
        """Test that CLARIFICATION patterns are populated."""
        from swealog.domains import swimming

        assert "CLARIFICATION" in swimming.clarification_patterns
        assert len(swimming.clarification_patterns["CLARIFICATION"]) > 0


class TestSwimmingCoexistence:
    """Tests for Swimming domain coexisting with other domains."""

    def test_swimming_and_general_fitness_coexist(self) -> None:
        """Test that Swimming and GeneralFitness can coexist."""
        from swealog.domains import GeneralFitness, Swimming, general_fitness, swimming

        assert swimming is not None
        assert general_fitness is not None
        assert isinstance(swimming, Swimming)
        assert isinstance(general_fitness, GeneralFitness)
        assert swimming.name != general_fitness.name

    def test_swimming_and_strength_coexist(self) -> None:
        """Test that Swimming and Strength can coexist."""
        from swealog.domains import Strength, Swimming, strength, swimming

        assert swimming is not None
        assert strength is not None
        assert isinstance(swimming, Swimming)
        assert isinstance(strength, Strength)
        assert swimming.name != strength.name

    def test_swimming_and_running_coexist(self) -> None:
        """Test that Swimming and Running can coexist."""
        from swealog.domains import Running, Swimming, running, swimming

        assert swimming is not None
        assert running is not None
        assert isinstance(swimming, Swimming)
        assert isinstance(running, Running)
        assert swimming.name != running.name

    def test_swimming_and_nutrition_coexist(self) -> None:
        """Test that Swimming and Nutrition can coexist."""
        from swealog.domains import Nutrition, Swimming, nutrition, swimming

        assert swimming is not None
        assert nutrition is not None
        assert isinstance(swimming, Swimming)
        assert isinstance(nutrition, Nutrition)
        assert swimming.name != nutrition.name


class TestSwimmingExports:
    """Tests for Swimming exports from swealog.domains."""

    def test_all_exports_importable(self) -> None:
        """Test that all Swimming exports are importable from swealog.domains."""
        from swealog.domains import (
            Swimming,
            SwimmingEntry,
            SwimmingInterval,
            SwimmingLap,
            swimming,
        )

        assert Swimming is not None
        assert SwimmingEntry is not None
        assert SwimmingInterval is not None
        assert SwimmingLap is not None
        assert swimming is not None

    def test_swimming_in_all_list(self) -> None:
        """Test that Swimming exports are in __all__ list."""
        from swealog import domains

        assert "Swimming" in domains.__all__
        assert "SwimmingEntry" in domains.__all__
        assert "SwimmingInterval" in domains.__all__
        assert "SwimmingLap" in domains.__all__
        assert "swimming" in domains.__all__
