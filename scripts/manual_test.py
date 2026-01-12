#!/usr/bin/env python3
"""Manual validation script for Quilto/Swealog components.

This script allows hands-on testing of the Router and Parser agents
with Swealog domain modules (GeneralFitness, Strength, Nutrition).

Usage:
    # Single input mode
    python scripts/manual_test.py "bench 185x5 felt heavy"
    python scripts/manual_test.py "점심: 닭가슴살 샐러드 500칼로리"

    # Interactive mode
    python scripts/manual_test.py

    # Skip parser (router only)
    python scripts/manual_test.py --router-only "bench 185x5"

Requirements:
    - Ollama running locally (ollama serve)
    - llm-config.yaml in project root
"""

import argparse
import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "packages" / "quilto"))
sys.path.insert(0, str(PROJECT_ROOT / "packages" / "swealog"))

from quilto import (
    DomainInfo,
    InputType,
    LLMClient,
    ParserAgent,
    ParserInput,
    RouterAgent,
    RouterInput,
    load_llm_config,
)
from swealog.domains import (
    GeneralFitnessEntry,
    NutritionEntry,
    StrengthEntry,
    general_fitness,
    nutrition,
    strength,
)


def print_header(text: str) -> None:
    """Print a formatted header."""
    print(f"\n{'=' * 60}")
    print(f"  {text}")
    print(f"{'=' * 60}")


def print_section(text: str) -> None:
    """Print a section header."""
    print(f"\n--- {text} ---")


def print_json(data: dict[str, Any], indent: int = 2) -> None:
    """Print formatted JSON."""
    print(json.dumps(data, indent=indent, default=str, ensure_ascii=False))


def get_available_domains() -> list[DomainInfo]:
    """Get list of available domain info for Router."""
    return [
        DomainInfo(name=general_fitness.name, description=general_fitness.description),
        DomainInfo(name=strength.name, description=strength.description),
        DomainInfo(name=nutrition.name, description=nutrition.description),
    ]


def get_domain_schemas(selected_domains: list[str]) -> dict[str, type]:
    """Get domain schemas for selected domains."""
    domain_map = {
        general_fitness.name: GeneralFitnessEntry,
        strength.name: StrengthEntry,
        nutrition.name: NutritionEntry,
    }
    return {name: domain_map[name] for name in selected_domains if name in domain_map}


def get_merged_vocabulary(selected_domains: list[str]) -> dict[str, str]:
    """Get merged vocabulary from selected domains."""
    domain_modules = {
        general_fitness.name: general_fitness,
        strength.name: strength,
        nutrition.name: nutrition,
    }
    vocabulary: dict[str, str] = {}
    for name in selected_domains:
        if name in domain_modules:
            vocabulary.update(domain_modules[name].vocabulary)
    return vocabulary


async def run_router(client: LLMClient, raw_input: str) -> dict[str, Any]:
    """Run Router agent and return results."""
    router = RouterAgent(client)
    router_input = RouterInput(
        raw_input=raw_input,
        available_domains=get_available_domains(),
    )

    print_section("Router Input")
    print(f"Raw input: {raw_input}")
    print(f"Available domains: {[d.name for d in router_input.available_domains]}")

    print_section("Running Router...")
    output = await router.classify(router_input)

    result = {
        "input_type": output.input_type.value,
        "confidence": output.confidence,
        "selected_domains": output.selected_domains,
        "domain_selection_reasoning": output.domain_selection_reasoning,
        "reasoning": output.reasoning,
    }

    if output.log_portion:
        result["log_portion"] = output.log_portion
    if output.query_portion:
        result["query_portion"] = output.query_portion
    if output.correction_target:
        result["correction_target"] = output.correction_target

    return result


async def run_parser(
    client: LLMClient,
    raw_input: str,
    selected_domains: list[str],
) -> dict[str, Any]:
    """Run Parser agent and return results."""
    parser = ParserAgent(client)

    domain_schemas = get_domain_schemas(selected_domains)
    vocabulary = get_merged_vocabulary(selected_domains)

    parser_input = ParserInput(
        raw_input=raw_input,
        timestamp=datetime.now(),
        domain_schemas=domain_schemas,
        vocabulary=vocabulary,
    )

    print_section("Parser Input")
    print(f"Domain schemas: {list(domain_schemas.keys())}")
    print(f"Vocabulary terms: {len(vocabulary)} terms")

    print_section("Running Parser...")
    output = await parser.parse(parser_input)

    return {
        "date": str(output.date),
        "timestamp": str(output.timestamp),
        "tags": output.tags,
        "domain_data": output.domain_data,
        "raw_content": output.raw_content,
        "confidence": output.confidence,
        "extraction_notes": output.extraction_notes,
        "uncertain_fields": output.uncertain_fields,
        "is_correction": output.is_correction,
    }


async def process_input(
    client: LLMClient,
    raw_input: str,
    router_only: bool = False,
) -> None:
    """Process a single input through Router and optionally Parser."""
    print_header(f"Processing: {raw_input[:50]}{'...' if len(raw_input) > 50 else ''}")

    # Run Router
    try:
        router_result = await run_router(client, raw_input)
        print_section("Router Output")
        print_json(router_result)
    except Exception as e:
        print(f"\nRouter ERROR: {e}")
        return

    # Skip parser if router-only mode
    if router_only:
        print("\n(--router-only: skipping Parser)")
        return

    # Skip parser for pure QUERY
    input_type = InputType(router_result["input_type"])
    if input_type == InputType.QUERY:
        print("\n(Input classified as QUERY - skipping Parser)")
        return

    # Run Parser for LOG, BOTH, CORRECTION
    selected_domains = router_result["selected_domains"]
    if not selected_domains:
        print("\n(No domains selected - skipping Parser)")
        return

    # For BOTH, use log_portion; otherwise use full input
    parser_input_text = router_result.get("log_portion", raw_input)

    try:
        parser_result = await run_parser(client, parser_input_text, selected_domains)
        print_section("Parser Output")
        print_json(parser_result)
    except Exception as e:
        print(f"\nParser ERROR: {e}")


async def interactive_mode(client: LLMClient, router_only: bool = False) -> None:
    """Run in interactive mode, accepting inputs until 'quit'."""
    print_header("Quilto/Swealog Manual Validation")
    print("\nAvailable domains:")
    for domain in [general_fitness, strength, nutrition]:
        print(f"  - {domain.name}: {domain.description[:60]}...")

    print("\nEnter text to process (or 'quit' to exit):")
    print("Examples:")
    print("  - bench 185x5 felt heavy")
    print("  - 점심: 닭가슴살 샐러드 500칼로리")
    print("  - How has my bench press progressed?")
    print("  - ran 5k in 25 minutes, how's my pace?")

    while True:
        try:
            print("\n" + "-" * 40)
            raw_input = input("Input> ").strip()

            if not raw_input:
                continue
            if raw_input.lower() in ("quit", "exit", "q"):
                print("Goodbye!")
                break

            await process_input(client, raw_input, router_only)

        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except EOFError:
            print("\nGoodbye!")
            break


async def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Manual validation script for Quilto/Swealog components.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/manual_test.py "bench 185x5 felt heavy"
  python scripts/manual_test.py "점심: 닭가슴살 샐러드"
  python scripts/manual_test.py --router-only "bench 185x5"
  python scripts/manual_test.py  # interactive mode
        """,
    )
    parser.add_argument(
        "input",
        nargs="?",
        help="Input text to process (omit for interactive mode)",
    )
    parser.add_argument(
        "--router-only",
        action="store_true",
        help="Only run Router, skip Parser",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=PROJECT_ROOT / "llm-config.yaml",
        help="Path to LLM config file (default: llm-config.yaml)",
    )

    args = parser.parse_args()

    # Load LLM config
    if not args.config.exists():
        print(f"ERROR: Config file not found: {args.config}")
        print("Make sure Ollama is running and llm-config.yaml exists.")
        sys.exit(1)

    print(f"Loading config from: {args.config}")
    config = load_llm_config(args.config)
    client = LLMClient(config)

    # Verify Ollama is accessible
    print(f"Using provider: {config.default_provider}")
    if config.default_provider == "ollama":
        ollama_config = config.providers.get("ollama")
        if ollama_config:
            print(f"Ollama API base: {ollama_config.api_base}")

    if args.input:
        # Single input mode
        await process_input(client, args.input, args.router_only)
    else:
        # Interactive mode
        await interactive_mode(client, args.router_only)


if __name__ == "__main__":
    asyncio.run(main())
