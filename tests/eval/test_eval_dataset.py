"""Tests for E2E evaluation dataset validation."""

from pathlib import Path

import pytest
import yaml

from tests.eval.schema import GoldenDataset, Rubric

EVAL_DIR = Path(__file__).parent
GOLDEN_DIR = EVAL_DIR / "golden"


class TestRubricValidation:
    """Tests for rubric.yaml validation."""

    def test_rubric_loads_and_validates(self) -> None:
        """Rubric file should load and pass schema validation."""
        rubric_path = EVAL_DIR / "rubric.yaml"
        assert rubric_path.exists(), "rubric.yaml not found"

        with open(rubric_path) as f:
            data = yaml.safe_load(f)

        rubric = Rubric.model_validate(data)

        # Verify required criteria exist
        required_criteria = ["accuracy", "completeness", "conciseness", "domain_expertise"]
        for criterion in required_criteria:
            assert criterion in rubric.criteria, f"Missing criterion: {criterion}"

    def test_rubric_criteria_have_scoring_guidance(self) -> None:
        """Each criterion should have good/medium/poor scoring guidance."""
        rubric_path = EVAL_DIR / "rubric.yaml"
        with open(rubric_path) as f:
            data = yaml.safe_load(f)

        rubric = Rubric.model_validate(data)

        for name, criterion in rubric.criteria.items():
            assert criterion.scoring.good, f"{name} missing 'good' scoring"
            assert criterion.scoring.medium, f"{name} missing 'medium' scoring"
            assert criterion.scoring.poor, f"{name} missing 'poor' scoring"


class TestGoldenDatasetValidation:
    """Tests for golden dataset YAML validation."""

    @pytest.fixture
    def golden_files(self) -> list[Path]:
        """Get all golden dataset files."""
        return list(GOLDEN_DIR.glob("v*.yaml"))

    def test_golden_directory_exists(self) -> None:
        """Golden directory should exist."""
        assert GOLDEN_DIR.exists(), "golden/ directory not found"

    def test_at_least_one_golden_file(self, golden_files: list[Path]) -> None:
        """At least one versioned golden dataset should exist."""
        assert len(golden_files) > 0, "No golden dataset files found"

    def test_golden_files_load_and_validate(self, golden_files: list[Path]) -> None:
        """All golden dataset files should load and pass schema validation."""
        for golden_path in golden_files:
            with open(golden_path) as f:
                data = yaml.safe_load(f)

            dataset = GoldenDataset.model_validate(data)
            assert len(dataset.test_cases) == dataset.case_count

    def test_test_case_ids_unique(self, golden_files: list[Path]) -> None:
        """All test case IDs should be unique within a dataset."""
        for golden_path in golden_files:
            with open(golden_path) as f:
                data = yaml.safe_load(f)

            ids = [tc["id"] for tc in data.get("test_cases", [])]
            assert len(ids) == len(set(ids)), f"Duplicate IDs in {golden_path.name}"

    def test_context_entries_sorted(self, golden_files: list[Path]) -> None:
        """All context_entries should be chronologically sorted."""
        for golden_path in golden_files:
            with open(golden_path) as f:
                data = yaml.safe_load(f)

            for tc in data.get("test_cases", []):
                entries = tc.get("context_entries", [])
                assert entries == sorted(entries), f"Unsorted context_entries in {tc['id']}: {entries}"

    def test_context_entries_reference_corpus(self, golden_files: list[Path]) -> None:
        """All context_entries should reference valid corpus dates."""
        corpus_dir = Path("tests/corpus/fitness/entries/from_csv")
        if not corpus_dir.exists():
            pytest.skip("Corpus directory not found")

        valid_dates = {f.stem for f in corpus_dir.glob("*.md")}

        for golden_path in golden_files:
            with open(golden_path) as f:
                data = yaml.safe_load(f)

            for tc in data.get("test_cases", []):
                for entry in tc.get("context_entries", []):
                    assert entry in valid_dates, f"Invalid corpus reference in {tc['id']}: {entry}"

    def test_rubric_criteria_valid(self, golden_files: list[Path]) -> None:
        """All rubric_criteria should reference valid criteria names."""
        valid_criteria = {"accuracy", "completeness", "conciseness", "domain_expertise"}

        for golden_path in golden_files:
            with open(golden_path) as f:
                data = yaml.safe_load(f)

            for tc in data.get("test_cases", []):
                for criterion in tc.get("rubric_criteria", []):
                    assert criterion in valid_criteria, f"Invalid criterion in {tc['id']}: {criterion}"

    def test_category_counts_match(self, golden_files: list[Path]) -> None:
        """Category counts in metadata should match actual test case counts."""
        for golden_path in golden_files:
            with open(golden_path) as f:
                data = yaml.safe_load(f)

            metadata_cats = data.get("categories", {})
            actual_cats: dict[str, int] = {}

            for tc in data.get("test_cases", []):
                cat = tc.get("category", "unknown")
                actual_cats[cat] = actual_cats.get(cat, 0) + 1

            for cat, expected_count in metadata_cats.items():
                actual_count = actual_cats.get(cat, 0)
                assert expected_count == actual_count, (
                    f"Category {cat} mismatch in {golden_path.name}: metadata={expected_count}, actual={actual_count}"
                )
