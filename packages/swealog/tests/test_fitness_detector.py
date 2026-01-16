"""Unit tests for FitnessSignificantEntryDetector.

Tests fitness-specific significant entry detection including:
- PR detection (inherited from DefaultSignificantEntryDetector)
- Weight milestones (hit 200, broke 100kg, reached 300lbs)
- Distance milestones (first 5k, first marathon, 100 mile week)
- Injury mentions (pain, injury, pulled, strained)
- Negative cases (normal workout entries without significance markers)
"""

from datetime import date, datetime

from quilto.storage import Entry
from swealog.observer import FitnessSignificantEntryDetector


def create_entry(content: str) -> Entry:
    """Helper to create Entry with given content.

    Args:
        content: Raw content for the entry.

    Returns:
        Entry instance with the given content.
    """
    return Entry(
        id="2024-01-15_001",
        date=date(2024, 1, 15),
        timestamp=datetime(2024, 1, 15, 10, 0, 0),
        raw_content=content,
    )


class TestPRDetection:
    """Test PR/personal record detection (inherited from DefaultSignificantEntryDetector)."""

    def test_new_pr_on_bench(self) -> None:
        """Detect 'new PR' phrase in bench press context."""
        detector = FitnessSignificantEntryDetector()
        entry = create_entry("New PR on bench press today! 225x5 felt great.")
        assert detector.is_significant(entry, {}) is True

    def test_personal_record_deadlift(self) -> None:
        """Detect 'personal record' phrase."""
        detector = FitnessSignificantEntryDetector()
        entry = create_entry("Hit a personal record on deadlift - 405lbs!")
        assert detector.is_significant(entry, {}) is True

    def test_pb_5k(self) -> None:
        """Detect 'pb' abbreviation with word boundary."""
        detector = FitnessSignificantEntryDetector()
        entry = create_entry("Ran a PB 5k time of 22:30")
        assert detector.is_significant(entry, {}) is True

    def test_pr_abbreviation(self) -> None:
        """Detect 'pr' abbreviation with word boundary."""
        detector = FitnessSignificantEntryDetector()
        entry = create_entry("New PR! Squat 315x3")
        assert detector.is_significant(entry, {}) is True

    def test_personal_best(self) -> None:
        """Detect 'personal best' phrase."""
        detector = FitnessSignificantEntryDetector()
        entry = create_entry("Just set a new personal best in the 100m freestyle!")
        assert detector.is_significant(entry, {}) is True


class TestMilestoneDetection:
    """Test milestone detection."""

    def test_first_5k(self) -> None:
        """Detect first 5k milestone."""
        detector = FitnessSignificantEntryDetector()
        entry = create_entry("Completed my first 5k today! Feeling accomplished.")
        assert detector.is_significant(entry, {}) is True

    def test_100th_workout(self) -> None:
        """Detect 100th workout milestone (inherited)."""
        detector = FitnessSignificantEntryDetector()
        entry = create_entry("This is my 100th workout of the year!")
        assert detector.is_significant(entry, {}) is True

    def test_marathon_debut(self) -> None:
        """Detect marathon debut milestone."""
        detector = FitnessSignificantEntryDetector()
        entry = create_entry("Marathon debut in 4 hours 15 minutes. What an experience!")
        assert detector.is_significant(entry, {}) is True

    def test_first_marathon(self) -> None:
        """Detect first marathon."""
        detector = FitnessSignificantEntryDetector()
        entry = create_entry("Ran my first marathon today in Boston!")
        assert detector.is_significant(entry, {}) is True

    def test_first_half(self) -> None:
        """Detect first half marathon."""
        detector = FitnessSignificantEntryDetector()
        entry = create_entry("Finished my first half marathon in 1:55")
        assert detector.is_significant(entry, {}) is True

    def test_100_mile_week(self) -> None:
        """Detect 100 mile week milestone."""
        detector = FitnessSignificantEntryDetector()
        entry = create_entry("Finally hit my 100 mile week goal!")
        assert detector.is_significant(entry, {}) is True


class TestWeightMilestones:
    """Test weight milestone detection (fitness-specific)."""

    def test_hit_200lbs_squat(self) -> None:
        """Detect 'hit 200' weight milestone."""
        detector = FitnessSignificantEntryDetector()
        entry = create_entry("Hit 200lbs on squat for the first time!")
        assert detector.is_significant(entry, {}) is True

    def test_broke_100kg_deadlift(self) -> None:
        """Detect 'broke 100kg' weight milestone."""
        detector = FitnessSignificantEntryDetector()
        entry = create_entry("Finally broke 100kg on deadlift! 102.5kg x 3")
        assert detector.is_significant(entry, {}) is True

    def test_reached_300lbs(self) -> None:
        """Detect 'reached 300' weight milestone."""
        detector = FitnessSignificantEntryDetector()
        entry = create_entry("Reached 300lbs bench press today!")
        assert detector.is_significant(entry, {}) is True


class TestInjuryDetection:
    """Test injury/pain detection for cautionary tracking."""

    def test_pain_in_shoulder(self) -> None:
        """Detect 'pain' mention."""
        detector = FitnessSignificantEntryDetector()
        entry = create_entry("Felt some slight pain in my shoulder during overhead press")
        assert detector.is_significant(entry, {}) is True

    def test_hamstring_pull(self) -> None:
        """Detect 'pulled' mention."""
        detector = FitnessSignificantEntryDetector()
        entry = create_entry("Pulled my hamstring during sprints. Stopping early.")
        assert detector.is_significant(entry, {}) is True

    def test_strained_muscle(self) -> None:
        """Detect 'strained' mention."""
        detector = FitnessSignificantEntryDetector()
        entry = create_entry("Think I strained my lower back on deadlifts")
        assert detector.is_significant(entry, {}) is True

    def test_injury_mention(self) -> None:
        """Detect 'injury' mention."""
        detector = FitnessSignificantEntryDetector()
        entry = create_entry("Coming back from injury, taking it easy today")
        assert detector.is_significant(entry, {}) is True

    def test_hurt_during_exercise(self) -> None:
        """Detect 'hurt' mention."""
        detector = FitnessSignificantEntryDetector()
        entry = create_entry("My knee hurt a bit during squats today")
        assert detector.is_significant(entry, {}) is True


class TestEventDetection:
    """Test event detection (inherited from DefaultSignificantEntryDetector)."""

    def test_competition(self) -> None:
        """Detect competition mention."""
        detector = FitnessSignificantEntryDetector()
        entry = create_entry("Preparing for my upcoming powerlifting competition")
        assert detector.is_significant(entry, {}) is True

    def test_race(self) -> None:
        """Detect race mention."""
        detector = FitnessSignificantEntryDetector()
        entry = create_entry("Race day! Running the local 10k this morning.")
        assert detector.is_significant(entry, {}) is True

    def test_swim_meet(self) -> None:
        """Detect meet mention."""
        detector = FitnessSignificantEntryDetector()
        entry = create_entry("Good performance at the swim meet today")
        assert detector.is_significant(entry, {}) is True


class TestNegativeCases:
    """Test that normal entries are not flagged as significant."""

    def test_normal_bench_press(self) -> None:
        """Normal bench press entry without significance markers."""
        detector = FitnessSignificantEntryDetector()
        entry = create_entry("Bench press 185x5x3. Felt good, moving up next week.")
        assert detector.is_significant(entry, {}) is False

    def test_normal_run(self) -> None:
        """Normal running entry without significance markers."""
        detector = FitnessSignificantEntryDetector()
        entry = create_entry("Easy 5k run today, 28:00 pace. Nice weather.")
        assert detector.is_significant(entry, {}) is False

    def test_normal_swim(self) -> None:
        """Normal swimming entry without significance markers."""
        detector = FitnessSignificantEntryDetector()
        entry = create_entry("Swam 2000m freestyle, focused on technique.")
        assert detector.is_significant(entry, {}) is False

    def test_normal_nutrition(self) -> None:
        """Normal nutrition entry without significance markers."""
        detector = FitnessSignificantEntryDetector()
        entry = create_entry("Breakfast: eggs and toast, 400 cal, 30g protein")
        assert detector.is_significant(entry, {}) is False

    def test_press_without_pr(self) -> None:
        """Entry with 'press' should not match 'pr' abbreviation."""
        detector = FitnessSignificantEntryDetector()
        entry = create_entry("Did overhead press today, 135x8x3")
        assert detector.is_significant(entry, {}) is False

    def test_weights_without_milestones(self) -> None:
        """Entry with weights but no milestone keywords."""
        detector = FitnessSignificantEntryDetector()
        entry = create_entry("Squat 200lbs for 5 sets of 5")
        assert detector.is_significant(entry, {}) is False


class TestParsedDataUsage:
    """Test that parsed_data parameter is accepted (for future extension)."""

    def test_accepts_parsed_data(self) -> None:
        """Detector accepts parsed_data dict without error."""
        detector = FitnessSignificantEntryDetector()
        entry = create_entry("New PR on deadlift!")
        parsed_data = {"exercises": [{"name": "deadlift", "weight": 405}]}
        # Should still detect significance from raw_content
        assert detector.is_significant(entry, parsed_data) is True

    def test_empty_parsed_data(self) -> None:
        """Detector works with empty parsed_data."""
        detector = FitnessSignificantEntryDetector()
        entry = create_entry("Hit 200 on bench today!")
        assert detector.is_significant(entry, {}) is True
