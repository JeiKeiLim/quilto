#!/usr/bin/env python3
"""Generate expected parser outputs from Strong CSV ground truth.

This script reads the strong_workouts.csv file and generates expected
ParserOutput JSON files for each workout date. These files serve as
ground truth for parser accuracy testing.

Usage:
    uv run python scripts/generate_expected_outputs.py
    uv run python scripts/generate_expected_outputs.py --dry-run
    uv run python scripts/generate_expected_outputs.py --verbose
"""

from __future__ import annotations

import argparse
import csv
import json
import logging
from collections import OrderedDict
from datetime import datetime
from pathlib import Path
from typing import Any

# CSV column names (Korean headers)
CSV_DATE = "날짜"
CSV_WORKOUT_NAME = "워크아웃 이름"
CSV_DURATION = "지속 시간"
CSV_EXERCISE = "운동 이름"
CSV_SET_NUM = "세트 순서"
CSV_WEIGHT = "체중"
CSV_REPS = "렙"
CSV_DISTANCE = "거리"
CSV_SECONDS = "초"
CSV_RPE = "RPE"

# Paths relative to project root
PROJECT_ROOT = Path(__file__).parent.parent
CSV_PATH = PROJECT_ROOT / "tests" / "corpus" / "fitness" / "ground_truth" / "strong_workouts.csv"
OUTPUT_DIR = PROJECT_ROOT / "tests" / "corpus" / "fitness" / "expected" / "parser"
EQUIVALENCES_PATH = PROJECT_ROOT / "tests" / "corpus" / "exercise_equivalences.yaml"

# Exercise translations from SYNTHESIS_RULES.md
EXERCISE_TRANSLATIONS: dict[str, list[str]] = {
    "Trap Bar Deadlift": ["트랩바 데드리프트"],
    "Push Press": ["푸쉬프레스"],
    "Bench Press (Barbell)": ["바벨 벤치프레스", "벤치프레스"],
    "Bench Press (Dumbbell)": ["덤벨 벤치프레스"],
    "Front Squat (Barbell)": ["프론트 스쿼트"],
    "Squat (Barbell)": ["바벨 스쿼트", "스쿼트"],
    "Incline Bench Press (Barbell)": ["인클라인 벤치프레스"],
    "Incline Bench Press (Dumbbell)": ["인클라인 덤벨프레스"],
    "Deadlift (Barbell)": ["데드리프트"],
    "Sumo Deadlift (Barbell)": ["스모 데드리프트"],
    "Overhead Press (Barbell)": ["오버헤드프레스"],
    "Seated Overhead Press (Barbell)": ["시티드 프레스"],
    "Strict Military Press (Barbell)": ["밀리터리프레스"],
    "T Bar Row": ["티바로우"],
    "Bent Over One Arm Row (Dumbbell)": ["원암 덤벨로우"],
    "Bent Over Row (Dumbbell)": ["덤벨로우"],
    "Pull Up": ["풀업"],
    "Lat Pulldown (Cable)": ["랫풀다운"],
    "Seated Row (Cable)": ["시티드 로우"],
    "Arnold Press (Dumbbell)": ["아놀드프레스"],
    "Lateral Raise (Dumbbell)": ["레터럴레이즈"],
    "Lateral Raise (Cable)": ["케이블 레터럴레이즈"],
    "Bicep Curl (Barbell)": ["바벨컬"],
    "Bicep Curl (Dumbbell)": ["덤벨컬"],
    "Floor Press (Barbell)": ["플로어프레스"],
    "Ab Mat Sit-up": ["싯업"],
    "Sit Up": ["싯업"],
    "Push Up": ["푸쉬업"],
    "Decline Crunch": ["크런치"],
    "Iso-Lateral Chest Press (Machine)": ["머신 체스트프레스"],
    "Iso-Lateral Row (Machine)": ["머신 로우"],
    "Overhead Squat (Barbell)": ["오버헤드 스쿼트"],
    "Standing Calf Raise (Dumbbell)": ["카프레이즈"],
}


def setup_logging(verbose: bool) -> None:
    """Configure logging based on verbosity.

    Args:
        verbose: If True, set logging level to DEBUG, otherwise INFO.
    """
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(levelname)s: %(message)s",
    )


def parse_csv(csv_path: Path) -> list[dict[str, str]]:
    """Parse the Strong workout CSV file.

    Args:
        csv_path: Path to the strong_workouts.csv file.

    Returns:
        List of dictionaries, one per CSV row.
    """
    rows: list[dict[str, str]] = []
    with csv_path.open(encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    return rows


def extract_date(datetime_str: str) -> str:
    """Extract YYYY-MM-DD date from CSV datetime string.

    Args:
        datetime_str: Datetime string in format "YYYY-MM-DD HH:MM:SS".

    Returns:
        Date string in YYYY-MM-DD format.
    """
    dt = datetime.strptime(datetime_str, "%Y-%m-%d %H:%M:%S")
    return dt.date().isoformat()


def parse_weight(weight_str: str) -> float | None:
    """Parse weight value, returning None for bodyweight exercises.

    Args:
        weight_str: Weight string from CSV.

    Returns:
        Float weight value, or None if weight is 0 (bodyweight).
    """
    weight = float(weight_str)
    if weight == 0:
        return None
    return weight


def parse_reps(reps_str: str) -> int:
    """Parse reps value, converting float to int.

    Args:
        reps_str: Reps string from CSV (may be float like "8.0").

    Returns:
        Integer reps count.
    """
    return int(float(reps_str))


def group_rows_by_date(rows: list[dict[str, str]]) -> dict[str, list[dict[str, str]]]:
    """Group CSV rows by workout date.

    Args:
        rows: List of CSV row dictionaries.

    Returns:
        Dictionary mapping date strings to list of rows for that date.
    """
    by_date: dict[str, list[dict[str, str]]] = OrderedDict()
    for row in rows:
        date = extract_date(row[CSV_DATE])
        if date not in by_date:
            by_date[date] = []
        by_date[date].append(row)
    return by_date


def build_exercise_record(
    exercise_name: str,
    exercise_rows: list[dict[str, str]],
) -> dict[str, Any]:
    """Build an ExpectedExerciseRecord from CSV rows for one exercise.

    Args:
        exercise_name: The exercise name.
        exercise_rows: CSV rows for this exercise (one per set).

    Returns:
        Dictionary matching ExpectedExerciseRecord schema.
    """
    set_details: list[dict[str, Any]] = []
    set_counter = 0

    for row in exercise_rows:
        # Handle "F" (failed set marker) - skip these rows
        set_num_str = row[CSV_SET_NUM]
        if set_num_str == "F":
            logging.debug("Skipping failed set marker for %s", exercise_name)
            continue

        set_counter += 1
        set_num = int(set_num_str)
        weight = parse_weight(row[CSV_WEIGHT])
        reps = parse_reps(row[CSV_REPS])

        set_detail: dict[str, Any] = {"set_num": set_num}
        if weight is not None:
            set_detail["weight"] = weight
        set_detail["reps"] = reps

        set_details.append(set_detail)

    return {
        "name": exercise_name,
        "sets": len(set_details),
        "weight_unit": "kg",
        "set_details": set_details,
    }


def build_expected_output(date: str, rows: list[dict[str, str]]) -> dict[str, Any]:
    """Build ExpectedParserOutput for a single workout date.

    Args:
        date: Date string in YYYY-MM-DD format.
        rows: CSV rows for this date.

    Returns:
        Dictionary matching ExpectedParserOutput schema.
    """
    # Group rows by exercise name, preserving CSV order
    exercises_order: list[str] = []
    exercises_rows: dict[str, list[dict[str, str]]] = {}

    for row in rows:
        exercise_name = row[CSV_EXERCISE].strip()  # Strip trailing whitespace
        if exercise_name not in exercises_rows:
            exercises_order.append(exercise_name)
            exercises_rows[exercise_name] = []
        exercises_rows[exercise_name].append(row)

    # Build exercise records in order
    exercises: list[dict[str, Any]] = []
    for exercise_name in exercises_order:
        record = build_exercise_record(exercise_name, exercises_rows[exercise_name])
        exercises.append(record)

    return {
        "activity_type": "workout",
        "exercises": exercises,
        "date": date,
    }


def write_expected_output(output_path: Path, data: dict[str, Any], dry_run: bool) -> None:
    """Write expected output JSON file.

    Args:
        output_path: Path to write the JSON file.
        data: ExpectedParserOutput dictionary.
        dry_run: If True, don't actually write the file.
    """
    if dry_run:
        logging.info("Would write: %s", output_path)
        return

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")

    logging.debug("Wrote: %s", output_path)


def collect_unique_exercises(rows: list[dict[str, str]]) -> list[str]:
    """Collect unique exercise names from CSV rows.

    Args:
        rows: List of CSV row dictionaries.

    Returns:
        List of unique exercise names in order of first appearance.
    """
    seen: set[str] = set()
    unique: list[str] = []
    for row in rows:
        name = row[CSV_EXERCISE].strip()
        if name not in seen:
            seen.add(name)
            unique.append(name)
    return unique


def write_equivalences_file(exercises: list[str], output_path: Path, dry_run: bool) -> None:
    """Write exercise equivalences YAML file.

    Args:
        exercises: List of unique exercise names from CSV.
        output_path: Path to write the YAML file.
        dry_run: If True, don't actually write the file.
    """
    if dry_run:
        logging.info("Would write equivalences: %s", output_path)
        return

    lines: list[str] = [
        "# Exercise name equivalences for semantic comparison",
        "# Canonical name (from CSV) → list of equivalent forms",
        "# Used by Story 1.7 accuracy tests for semantic matching",
        "",
    ]

    for exercise in exercises:
        lines.append(f'"{exercise}":')
        lines.append(f'  - "{exercise}"  # canonical')

        # Add Korean translations if available
        if exercise in EXERCISE_TRANSLATIONS:
            for translation in EXERCISE_TRANSLATIONS[exercise]:
                lines.append(f'  - "{translation}"')

        lines.append("")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    logging.info("Wrote equivalences: %s (%d exercises)", output_path, len(exercises))


def main() -> None:
    """Main entry point for generating expected outputs."""
    parser = argparse.ArgumentParser(
        description="Generate expected parser outputs from Strong CSV ground truth."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview without writing files",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose logging",
    )
    args = parser.parse_args()

    setup_logging(args.verbose)

    # Parse CSV
    logging.info("Parsing CSV: %s", CSV_PATH)
    rows = parse_csv(CSV_PATH)
    logging.info("Found %d rows", len(rows))

    # Group by date
    by_date = group_rows_by_date(rows)
    logging.info("Found %d workout dates", len(by_date))

    # Generate expected outputs
    for date, date_rows in by_date.items():
        expected = build_expected_output(date, date_rows)
        output_path = OUTPUT_DIR / f"{date}.json"
        write_expected_output(output_path, expected, args.dry_run)
        if args.verbose:
            logging.debug(
                "  %s: %d exercises",
                date,
                len(expected["exercises"]),
            )

    # Collect unique exercises and write equivalences
    unique_exercises = collect_unique_exercises(rows)
    logging.info("Found %d unique exercises", len(unique_exercises))
    write_equivalences_file(unique_exercises, EQUIVALENCES_PATH, args.dry_run)

    # Summary
    if not args.dry_run:
        logging.info("Generated %d expected output files", len(by_date))
        logging.info("Output directory: %s", OUTPUT_DIR)
    else:
        logging.info("Dry run complete. Would generate %d files.", len(by_date))


if __name__ == "__main__":
    main()
