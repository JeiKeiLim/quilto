"""Tests for expected parser output schemas.

These tests verify the Pydantic models in tests/corpus/schemas/ behave correctly
for validating expected parser output JSON files.
"""

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from tests.corpus.schemas import (
    ExpectedExerciseRecord,
    ExpectedParserOutput,
    ExpectedSetDetail,
)


class TestExpectedSetDetail:
    """Tests for ExpectedSetDetail model."""

    def test_creates_with_all_fields(self) -> None:
        """Test creating a set detail with all fields."""
        detail = ExpectedSetDetail(set_num=1, weight=100.0, reps=8)
        assert detail.set_num == 1
        assert detail.weight == 100.0
        assert detail.reps == 8

    def test_creates_with_bodyweight(self) -> None:
        """Test creating a set detail with no weight (bodyweight exercise)."""
        detail = ExpectedSetDetail(set_num=1, weight=None, reps=10)
        assert detail.set_num == 1
        assert detail.weight is None
        assert detail.reps == 10

    def test_weight_defaults_to_none(self) -> None:
        """Test that weight defaults to None when not provided."""
        detail = ExpectedSetDetail(set_num=1, reps=10)
        assert detail.weight is None

    def test_strict_mode_rejects_wrong_types(self) -> None:
        """Test that strict mode rejects incorrect types."""
        with pytest.raises(ValidationError):
            ExpectedSetDetail(set_num="1", reps=10)  # type: ignore[arg-type]


class TestExpectedExerciseRecord:
    """Tests for ExpectedExerciseRecord model."""

    def test_creates_with_minimal_fields(self) -> None:
        """Test creating with just name and sets."""
        record = ExpectedExerciseRecord(name="Pull Up", sets=3)
        assert record.name == "Pull Up"
        assert record.sets == 3
        assert record.weight_unit == "kg"
        assert record.set_details == []

    def test_creates_with_set_details(self) -> None:
        """Test creating with set details."""
        details = [
            ExpectedSetDetail(set_num=1, weight=100.0, reps=8),
            ExpectedSetDetail(set_num=2, weight=100.0, reps=6),
        ]
        record = ExpectedExerciseRecord(
            name="Bench Press", sets=2, set_details=details
        )
        assert len(record.set_details) == 2
        assert record.set_details[0].weight == 100.0

    def test_strict_mode_rejects_wrong_types(self) -> None:
        """Test that strict mode rejects incorrect types."""
        with pytest.raises(ValidationError):
            ExpectedExerciseRecord(name=123, sets=3)  # type: ignore[arg-type]


class TestExpectedParserOutput:
    """Tests for ExpectedParserOutput model."""

    def test_creates_with_minimal_fields(self) -> None:
        """Test creating with required fields only."""
        output = ExpectedParserOutput(
            exercises=[ExpectedExerciseRecord(name="Pull Up", sets=3)],
            date="2019-01-28",
        )
        assert output.activity_type == "workout"
        assert output.date == "2019-01-28"
        assert len(output.exercises) == 1

    def test_creates_with_full_structure(self) -> None:
        """Test creating with complete structure matching JSON output."""
        output = ExpectedParserOutput(
            activity_type="workout",
            exercises=[
                ExpectedExerciseRecord(
                    name="Trap Bar Deadlift",
                    sets=5,
                    weight_unit="kg",
                    set_details=[
                        ExpectedSetDetail(set_num=1, weight=180.0, reps=8),
                        ExpectedSetDetail(set_num=2, weight=190.0, reps=6),
                    ],
                )
            ],
            date="2019-01-28",
        )
        assert output.exercises[0].name == "Trap Bar Deadlift"
        assert len(output.exercises[0].set_details) == 2

    def test_strict_mode_rejects_wrong_types(self) -> None:
        """Test that strict mode rejects incorrect types."""
        with pytest.raises(ValidationError):
            ExpectedParserOutput(exercises="not a list", date="2019-01-28")  # type: ignore[arg-type]


class TestGeneratedJsonValidation:
    """Tests validating generated JSON files against schemas."""

    def test_all_generated_json_files_validate(self) -> None:
        """Verify all generated JSON files pass schema validation."""
        output_dir = Path(__file__).parent / "fitness" / "expected" / "parser"
        json_files = list(output_dir.glob("*.json"))

        assert len(json_files) == 93, f"Expected 93 JSON files, found {len(json_files)}"

        for json_file in json_files:
            data = json.loads(json_file.read_text())
            output = ExpectedParserOutput.model_validate(data)
            assert output.date == json_file.stem, (
                f"Date mismatch in {json_file.name}"
            )

    def test_spot_check_2019_01_28(self) -> None:
        """Spot check: 2019-01-28 should have 2 exercises."""
        json_path = (
            Path(__file__).parent
            / "fitness"
            / "expected"
            / "parser"
            / "2019-01-28.json"
        )
        data = json.loads(json_path.read_text())
        output = ExpectedParserOutput.model_validate(data)

        assert len(output.exercises) == 2
        assert output.exercises[0].name == "Trap Bar Deadlift"
        assert output.exercises[0].sets == 5
        assert output.exercises[1].name == "Push Press"
        assert output.exercises[1].sets == 5
