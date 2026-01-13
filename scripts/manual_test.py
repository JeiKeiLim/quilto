#!/usr/bin/env python3
"""Manual validation script for Quilto/Swealog components.

This script allows hands-on testing of the Router, Parser, Planner, and Retriever
agents with Swealog domain modules (GeneralFitness, Strength, Nutrition, Running).

Usage:
    # Single input mode - LOG entries
    python scripts/manual_test.py "bench 185x5 felt heavy"
    python scripts/manual_test.py "점심: 닭가슴살 샐러드 500칼로리"
    python scripts/manual_test.py "ran 5k in 25:30, felt good"

    # Single input mode - QUERY
    python scripts/manual_test.py "How has my bench press progressed?"
    python scripts/manual_test.py "What's my average running pace this month?"

    # Single input mode - BOTH (log + query)
    python scripts/manual_test.py "ran 5k in 25 minutes, how's my pace?"

    # Interactive mode
    python scripts/manual_test.py

    # Skip parser/planner/retriever (router only)
    python scripts/manual_test.py --router-only "bench 185x5"

    # Specify storage directory for retrieval
    python scripts/manual_test.py --storage-dir ./data "How has my bench progressed?"

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

from quilto import (  # noqa: E402
    DomainInfo,
    InputType,
    LLMClient,
    ParserAgent,
    ParserInput,
    RouterAgent,
    RouterInput,
    load_llm_config,
)
from quilto.agents import (  # noqa: E402
    ActiveDomainContext,
    PlannerAgent,
    PlannerInput,
    PlannerOutput,
    RetrieverAgent,
    RetrieverInput,
)
from quilto.storage import StorageRepository  # noqa: E402
from swealog.domains import (  # noqa: E402
    GeneralFitnessEntry,
    NutritionEntry,
    RunningEntry,
    StrengthEntry,
    general_fitness,
    nutrition,
    running,
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
        DomainInfo(name=running.name, description=running.description),
    ]


def get_domain_schemas(selected_domains: list[str]) -> dict[str, type]:
    """Get domain schemas for selected domains."""
    domain_map = {
        general_fitness.name: GeneralFitnessEntry,
        strength.name: StrengthEntry,
        nutrition.name: NutritionEntry,
        running.name: RunningEntry,
    }
    return {name: domain_map[name] for name in selected_domains if name in domain_map}


def get_merged_vocabulary(selected_domains: list[str]) -> dict[str, str]:
    """Get merged vocabulary from selected domains."""
    domain_modules = {
        general_fitness.name: general_fitness,
        strength.name: strength,
        nutrition.name: nutrition,
        running.name: running,
    }
    vocabulary: dict[str, str] = {}
    for name in selected_domains:
        if name in domain_modules:
            vocabulary.update(domain_modules[name].vocabulary)
    return vocabulary


def build_active_domain_context(selected_domains: list[str]) -> ActiveDomainContext:
    """Build ActiveDomainContext from selected domains."""
    domain_modules = {
        general_fitness.name: general_fitness,
        strength.name: strength,
        nutrition.name: nutrition,
        running.name: running,
    }

    # Merge vocabulary and expertise from selected domains
    vocabulary: dict[str, str] = {}
    expertise_parts: list[str] = []

    for name in selected_domains:
        if name in domain_modules:
            module = domain_modules[name]
            vocabulary.update(module.vocabulary)
            expertise_parts.append(module.expertise)

    # Get available domains (those not selected)
    available = [
        DomainInfo(name=m.name, description=m.description)
        for m in domain_modules.values()
        if m.name not in selected_domains
    ]

    return ActiveDomainContext(
        domains_loaded=selected_domains,
        vocabulary=vocabulary,
        expertise=" | ".join(expertise_parts) if expertise_parts else "General fitness tracking",
        available_domains=available,
    )


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


async def run_planner(
    client: LLMClient,
    query: str,
    selected_domains: list[str],
) -> tuple[dict[str, Any], PlannerOutput]:
    """Run Planner agent and return results."""
    planner = PlannerAgent(client)

    domain_context = build_active_domain_context(selected_domains)

    planner_input = PlannerInput(
        query=query,
        domain_context=domain_context,
    )

    print_section("Planner Input")
    print(f"Query: {query}")
    print(f"Domains loaded: {domain_context.domains_loaded}")
    print(f"Available for expansion: {[d.name for d in domain_context.available_domains]}")

    print_section("Running Planner...")
    output = await planner.plan(planner_input)

    result: dict[str, Any] = {
        "original_query": output.original_query,
        "query_type": output.query_type.value,
        "execution_strategy": output.execution_strategy.value,
        "sub_queries": [
            {
                "id": sq.id,
                "question": sq.question,
                "retrieval_strategy": sq.retrieval_strategy,
                "retrieval_params": sq.retrieval_params,
            }
            for sq in output.sub_queries
        ],
        "execution_order": output.execution_order,
        "next_action": output.next_action,
        "reasoning": output.reasoning,
    }

    if output.dependencies:
        result["dependencies"] = output.dependencies
    if output.domain_expansion_request:
        result["domain_expansion_request"] = output.domain_expansion_request
        result["expansion_reasoning"] = output.expansion_reasoning
    if output.clarify_questions:
        result["clarify_questions"] = output.clarify_questions

    return result, output


async def run_retriever(
    storage: StorageRepository,
    planner_output: PlannerOutput,
    vocabulary: dict[str, str],
) -> dict[str, Any]:
    """Run Retriever agent and return results."""
    retriever = RetrieverAgent(storage)

    # Build retrieval instructions from planner output
    instructions = [
        {
            "strategy": sq.retrieval_strategy,
            "params": sq.retrieval_params,
            "sub_query_id": sq.id,
        }
        for sq in planner_output.sub_queries
    ]

    retriever_input = RetrieverInput(
        instructions=instructions,
        vocabulary=vocabulary,
        max_entries=100,
    )

    print_section("Retriever Input")
    print(f"Instructions: {len(instructions)}")
    for i, inst in enumerate(instructions, 1):
        print(f"  {i}. Strategy: {inst['strategy']}, Params: {inst['params']}")
    print(f"Vocabulary terms: {len(vocabulary)}")

    print_section("Running Retriever...")
    output = await retriever.retrieve(retriever_input)

    result: dict[str, Any] = {
        "total_entries_found": output.total_entries_found,
        "entries_returned": len(output.entries),
        "truncated": output.truncated,
        "warnings": output.warnings,
        "retrieval_summary": [
            {
                "attempt": attempt.attempt_number,
                "strategy": attempt.strategy,
                "entries_found": attempt.entries_found,
                "summary": attempt.summary,
                "expanded_terms": attempt.expanded_terms,
            }
            for attempt in output.retrieval_summary
        ],
    }

    if output.date_range_covered:
        result["date_range_covered"] = {
            "start": str(output.date_range_covered.start),
            "end": str(output.date_range_covered.end),
        }

    if output.entries:
        result["entries_preview"] = [
            {
                "id": entry.id,
                "date": str(entry.date),
                "content_preview": (
                    entry.raw_content[:100] + "..." if len(entry.raw_content) > 100 else entry.raw_content
                ),
            }
            for entry in output.entries[:5]  # Show first 5
        ]
        if len(output.entries) > 5:
            result["entries_preview"].append({"...": f"and {len(output.entries) - 5} more entries"})

    return result


async def process_input(
    client: LLMClient,
    raw_input: str,
    router_only: bool = False,
    storage: StorageRepository | None = None,
) -> None:
    """Process a single input through Router, Parser, Planner, and/or Retriever."""
    print_header(f"Processing: {raw_input[:50]}{'...' if len(raw_input) > 50 else ''}")

    # Run Router
    try:
        router_result = await run_router(client, raw_input)
        print_section("Router Output")
        print_json(router_result)
    except Exception as e:
        print(f"\nRouter ERROR: {e}")
        return

    # Skip further processing if router-only mode
    if router_only:
        print("\n(--router-only: skipping Parser and Planner)")
        return

    input_type = InputType(router_result["input_type"])
    selected_domains = router_result["selected_domains"]

    if not selected_domains:
        print("\n(No domains selected - skipping Parser and Planner)")
        return

    # Handle based on input type
    if input_type == InputType.LOG:
        # LOG: Run Parser only
        try:
            parser_result = await run_parser(client, raw_input, selected_domains)
            print_section("Parser Output")
            print_json(parser_result)
        except Exception as e:
            print(f"\nParser ERROR: {e}")

    elif input_type == InputType.QUERY:
        # QUERY: Run Planner, then Retriever
        planner_output: PlannerOutput | None = None
        try:
            planner_result, planner_output = await run_planner(client, raw_input, selected_domains)
            print_section("Planner Output")
            print_json(planner_result)
        except Exception as e:
            print(f"\nPlanner ERROR: {e}")

        # Run Retriever if storage is available and planner succeeded
        if storage and planner_output is not None and planner_output.sub_queries:
            try:
                vocabulary = get_merged_vocabulary(selected_domains)
                retriever_result = await run_retriever(storage, planner_output, vocabulary)
                print_section("Retriever Output")
                print_json(retriever_result)
            except Exception as e:
                print(f"\nRetriever ERROR: {e}")
        elif not storage:
            print("\n(No --storage-dir specified, skipping Retriever)")

    elif input_type == InputType.BOTH:
        # BOTH: Run Parser on log_portion, Planner + Retriever on query_portion
        log_portion = router_result.get("log_portion", raw_input)
        query_portion = router_result.get("query_portion", "")

        # Run Parser on log portion
        try:
            parser_result = await run_parser(client, log_portion, selected_domains)
            print_section("Parser Output (log portion)")
            print_json(parser_result)
        except Exception as e:
            print(f"\nParser ERROR: {e}")

        # Run Planner + Retriever on query portion
        planner_output: PlannerOutput | None = None
        if query_portion:
            try:
                planner_result, planner_output = await run_planner(client, query_portion, selected_domains)
                print_section("Planner Output (query portion)")
                print_json(planner_result)
            except Exception as e:
                print(f"\nPlanner ERROR: {e}")

            # Run Retriever if storage is available and planner succeeded
            if storage and planner_output is not None and planner_output.sub_queries:
                try:
                    vocabulary = get_merged_vocabulary(selected_domains)
                    retriever_result = await run_retriever(storage, planner_output, vocabulary)
                    print_section("Retriever Output (query portion)")
                    print_json(retriever_result)
                except Exception as e:
                    print(f"\nRetriever ERROR: {e}")
            elif not storage:
                print("\n(No --storage-dir specified, skipping Retriever)")
        else:
            print("\n(No query_portion found for Planner)")

    elif input_type == InputType.CORRECTION:
        # CORRECTION: Run Parser with correction mode
        try:
            parser_result = await run_parser(client, raw_input, selected_domains)
            print_section("Parser Output (correction)")
            print_json(parser_result)
        except Exception as e:
            print(f"\nParser ERROR: {e}")


async def interactive_mode(
    client: LLMClient,
    router_only: bool = False,
    storage: StorageRepository | None = None,
) -> None:
    """Run in interactive mode, accepting inputs until 'quit'."""
    print_header("Quilto/Swealog Manual Validation")
    print("\nAvailable domains:")
    for domain in [general_fitness, strength, nutrition, running]:
        print(f"  - {domain.name}: {domain.description[:60]}...")

    if storage:
        print(f"\nStorage: {storage.base_path}")
    else:
        print("\nStorage: Not configured (use --storage-dir for retrieval)")

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

            await process_input(client, raw_input, router_only, storage)

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
  # LOG inputs (different domains)
  python scripts/manual_test.py "bench 185x5 felt heavy"        # Strength
  python scripts/manual_test.py "점심: 닭가슴살 샐러드"              # Nutrition
  python scripts/manual_test.py "ran 5k in 25:30"               # Running

  # QUERY inputs
  python scripts/manual_test.py "How has my bench progressed?"
  python scripts/manual_test.py "What's my average running pace?"

  # BOTH (log + query)
  python scripts/manual_test.py "ran 5k in 25 minutes, how's my pace?"

  # Options
  python scripts/manual_test.py --router-only "bench 185x5"
  python scripts/manual_test.py --storage-dir ./data "How has my bench progressed?"
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
        help="Only run Router, skip Parser/Planner/Retriever",
    )
    parser.add_argument(
        "--storage-dir",
        type=Path,
        help="Path to storage directory for Retriever (enables retrieval)",
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

    # Initialize storage if specified
    storage: StorageRepository | None = None
    if args.storage_dir:
        if not args.storage_dir.exists():
            print(f"WARNING: Storage directory does not exist: {args.storage_dir}")
            print("Retriever will be skipped.")
        else:
            storage = StorageRepository(args.storage_dir)
            print(f"Storage directory: {args.storage_dir}")

    if args.input:
        # Single input mode
        await process_input(client, args.input, args.router_only, storage)
    else:
        # Interactive mode
        await interactive_mode(client, args.router_only, storage)


if __name__ == "__main__":
    asyncio.run(main())
