#!/usr/bin/env python3
r"""Convert Obsidian markdown files to Quilto StorageRepository format.

This script converts markdown files from an Obsidian vault (or any directory)
to the format expected by Quilto's StorageRepository.

Expected output structure:
    {output_dir}/logs/raw/{YYYY}/{MM}/{YYYY-MM-DD}.md

Usage:
    # Preview what will be converted (dry-run)
    python scripts/convert_obsidian.py /path/to/obsidian/vault /path/to/output --dry-run

    # Actually convert files
    python scripts/convert_obsidian.py /path/to/obsidian/vault /path/to/output

    # With custom date pattern in filename
    python scripts/convert_obsidian.py /path/to/vault /path/to/output --date-pattern "YYYY-MM-DD"

Examples:
    python scripts/convert_obsidian.py \
        /path/to/obsidian/vault \
        ./test-storage \
        --dry-run
"""

import argparse
import re
from datetime import date
from pathlib import Path


def extract_date_from_filename(filename: str) -> date | None:
    """Extract date from filename using common patterns.

    Supports:
        - YYYY-MM-DD (ISO format)
        - YYYY.MM.DD
        - YYYY_MM_DD
        - DD-MM-YYYY
        - DD.MM.YYYY
        - YYYYMMDD

    Args:
        filename: Filename without extension.

    Returns:
        Extracted date or None if no pattern matches.
    """
    patterns = [
        # ISO format: 2026-01-14, 2026.01.14, 2026_01_14
        (r"(\d{4})[-._](\d{2})[-._](\d{2})", lambda m: (int(m[1]), int(m[2]), int(m[3]))),
        # European format: 14-01-2026, 14.01.2026
        (r"(\d{2})[-.](\d{2})[-.](\d{4})", lambda m: (int(m[3]), int(m[2]), int(m[1]))),
        # Compact: 20260114
        (r"(\d{4})(\d{2})(\d{2})", lambda m: (int(m[1]), int(m[2]), int(m[3]))),
    ]

    for pattern, extractor in patterns:
        match = re.search(pattern, filename)
        if match:
            try:
                year, month, day = extractor(match)
                return date(year, month, day)
            except ValueError:
                continue

    return None


def extract_date_from_content(content: str) -> date | None:
    """Extract date from file content (front matter or first line).

    Looks for:
        - YAML front matter: date: 2026-01-14
        - First line date patterns

    Args:
        content: File content.

    Returns:
        Extracted date or None if not found.
    """
    # Check YAML front matter
    yaml_match = re.search(r"^---\s*\n(.*?)\n---", content, re.DOTALL)
    if yaml_match:
        front_matter = yaml_match.group(1)
        date_match = re.search(r"date:\s*(\d{4}-\d{2}-\d{2})", front_matter)
        if date_match:
            try:
                return date.fromisoformat(date_match.group(1))
            except ValueError:
                pass

    # Check first few lines for date patterns
    first_lines = content[:500]
    iso_match = re.search(r"(\d{4}-\d{2}-\d{2})", first_lines)
    if iso_match:
        try:
            return date.fromisoformat(iso_match.group(1))
        except ValueError:
            pass

    return None


def has_time_headers(content: str) -> bool:
    """Check if content already has ## HH:MM headers.

    Args:
        content: File content.

    Returns:
        True if content has time headers.
    """
    return bool(re.search(r"^## \d{2}:\d{2}", content, re.MULTILINE))


def add_default_time_header(content: str, file_date: date) -> str:
    """Add default ## HH:MM header if missing.

    Args:
        content: Original file content.
        file_date: Date of the file for default timestamp.

    Returns:
        Content with time header added.
    """
    if has_time_headers(content):
        return content

    # Strip YAML front matter if present
    content_without_frontmatter = re.sub(r"^---\s*\n.*?\n---\s*\n?", "", content, flags=re.DOTALL)

    # Add default time header (09:00)
    return f"## 09:00\n{content_without_frontmatter.strip()}\n"


def convert_file(
    source_path: Path,
    output_dir: Path,
    dry_run: bool = False,
) -> tuple[bool, str]:
    """Convert a single file to StorageRepository format.

    Args:
        source_path: Path to source markdown file.
        output_dir: Root output directory.
        dry_run: If True, only preview without writing.

    Returns:
        Tuple of (success, message).
    """
    # Read content
    try:
        content = source_path.read_text(encoding="utf-8")
    except Exception as e:
        return False, f"Failed to read: {e}"

    # Extract date
    file_date = extract_date_from_filename(source_path.stem)
    if not file_date:
        file_date = extract_date_from_content(content)

    if not file_date:
        return False, "Could not extract date from filename or content"

    # Prepare output path
    output_path = (
        output_dir / "logs" / "raw" / str(file_date.year) / f"{file_date.month:02d}" / f"{file_date.isoformat()}.md"
    )

    # Prepare content with time header
    converted_content = add_default_time_header(content, file_date)

    if dry_run:
        return True, f"Would write to: {output_path}"

    # Create directories and write
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # If file exists, append instead of overwrite
        if output_path.exists():
            existing = output_path.read_text(encoding="utf-8")
            # Extract just the content part (after ## HH:MM header)
            new_content = re.sub(r"^## \d{2}:\d{2}\n", "", converted_content)
            converted_content = f"{existing.rstrip()}\n\n## 09:01\n{new_content}"

        output_path.write_text(converted_content, encoding="utf-8")
        return True, f"Written to: {output_path}"
    except Exception as e:
        return False, f"Failed to write: {e}"


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Convert Obsidian markdown files to Quilto StorageRepository format.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Preview conversion
    python scripts/convert_obsidian.py /path/to/obsidian /path/to/output --dry-run

    # Convert all files
    python scripts/convert_obsidian.py /path/to/obsidian /path/to/output

    # Convert specific date range
    python scripts/convert_obsidian.py /path/to/obsidian /path/to/output --after 2025-01-01
        """,
    )
    parser.add_argument(
        "source_dir",
        type=Path,
        help="Source directory containing markdown files",
    )
    parser.add_argument(
        "output_dir",
        type=Path,
        help="Output directory for StorageRepository format",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without writing files",
    )
    parser.add_argument(
        "--after",
        type=str,
        help="Only convert files with dates after this date (YYYY-MM-DD)",
    )
    parser.add_argument(
        "--recursive",
        action="store_true",
        default=True,
        help="Recursively search subdirectories (default: True)",
    )

    args = parser.parse_args()

    if not args.source_dir.exists():
        print(f"Error: Source directory does not exist: {args.source_dir}")
        return

    # Parse after date filter
    after_date: date | None = None
    if args.after:
        try:
            after_date = date.fromisoformat(args.after)
        except ValueError:
            print(f"Error: Invalid date format for --after: {args.after}")
            return

    # Find all markdown files
    pattern = "**/*.md" if args.recursive else "*.md"
    md_files = list(args.source_dir.glob(pattern))

    if not md_files:
        print(f"No markdown files found in: {args.source_dir}")
        return

    print(f"Found {len(md_files)} markdown files in {args.source_dir}")
    if args.dry_run:
        print("DRY RUN - No files will be written\n")

    success_count = 0
    skip_count = 0
    fail_count = 0

    for file_path in sorted(md_files):
        # Skip hidden files and directories
        if any(part.startswith(".") for part in file_path.parts):
            continue

        success, message = convert_file(file_path, args.output_dir, args.dry_run)

        # Apply date filter
        if after_date and success:
            file_date = extract_date_from_filename(file_path.stem)
            if file_date and file_date < after_date:
                skip_count += 1
                continue

        status = "[OK]" if success else "[SKIP]"
        print(f"{status} {file_path.name}: {message}")

        if success:
            success_count += 1
        elif "Could not extract date" in message:
            skip_count += 1
        else:
            fail_count += 1

    print(f"\nSummary: {success_count} converted, {skip_count} skipped, {fail_count} failed")

    if args.dry_run and success_count > 0:
        print("\nRun without --dry-run to actually convert files.")


if __name__ == "__main__":
    main()
