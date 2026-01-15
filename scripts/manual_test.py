#!/usr/bin/env python3
"""Manual validation script for Quilto/Swealog components.

This script allows hands-on testing of the Router, Parser, Planner, Retriever,
Analyzer, Clarifier, Synthesizer, and Evaluator agents with Swealog domain modules
(GeneralFitness, Strength, Nutrition, Running).

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
from typing import Any, Literal

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
    AnalyzerAgent,
    AnalyzerInput,
    AnalyzerOutput,
    ClarifierAgent,
    ClarifierInput,
    ClarifierOutput,
    EvaluationFeedback,
    EvaluatorAgent,
    EvaluatorInput,
    EvaluatorOutput,
    GapType,
    PlannerAgent,
    PlannerInput,
    PlannerOutput,
    RetrieverAgent,
    RetrieverInput,
    RetrieverOutput,
    SynthesizerAgent,
    SynthesizerInput,
    SynthesizerOutput,
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


def get_merged_clarification_patterns(selected_domains: list[str]) -> dict[str, list[str]]:
    """Get merged clarification_patterns from selected domains."""
    domain_modules = {
        general_fitness.name: general_fitness,
        strength.name: strength,
        nutrition.name: nutrition,
        running.name: running,
    }
    patterns: dict[str, list[str]] = {}
    for name in selected_domains:
        if name in domain_modules:
            module = domain_modules[name]
            for gap_type, questions in module.clarification_patterns.items():
                if gap_type not in patterns:
                    patterns[gap_type] = []
                patterns[gap_type].extend(questions)
    return patterns


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
            # Add domain label for multi-domain queries
            expertise_parts.append(f"[{module.name}] {module.expertise}")

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
) -> tuple[dict[str, Any], RetrieverOutput]:
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
        "expansion_exhausted": output.expansion_exhausted,
        "warnings": output.warnings,
        "retrieval_summary": [
            {
                "attempt": attempt.attempt_number,
                "strategy": attempt.strategy,
                "entries_found": attempt.entries_found,
                "summary": attempt.summary,
                "expansion_tier": attempt.expansion_tier,
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

    return result, output


async def run_analyzer(
    client: LLMClient,
    query: str,
    retriever_output: RetrieverOutput,
    planner_output: PlannerOutput,
    domain_context: ActiveDomainContext,
) -> tuple[dict[str, Any], AnalyzerOutput]:
    """Run Analyzer agent and return results."""
    analyzer = AnalyzerAgent(client)

    analyzer_input = AnalyzerInput(
        query=query,
        query_type=planner_output.query_type,
        entries=retriever_output.entries,
        retrieval_summary=retriever_output.retrieval_summary,
        domain_context=domain_context,
    )

    print_section("Analyzer Input")
    print(f"Query: {query}")
    print(f"Query type: {planner_output.query_type.value}")
    print(f"Entries to analyze: {len(retriever_output.entries)}")

    print_section("Running Analyzer...")
    output = await analyzer.analyze(analyzer_input)

    result: dict[str, Any] = {
        "query_intent": output.query_intent,
        "verdict": output.verdict.value,
        "verdict_reasoning": output.verdict_reasoning,
        "patterns_identified": output.patterns_identified,
        "findings": [
            {
                "claim": f.claim,
                "evidence": f.evidence,
                "confidence": f.confidence,
            }
            for f in output.findings
        ],
        "sufficiency_evaluation": {
            "critical_gaps": [g.description for g in output.sufficiency_evaluation.critical_gaps],
            "nice_to_have_gaps": [g.description for g in output.sufficiency_evaluation.nice_to_have_gaps],
            "evidence_check_passed": output.sufficiency_evaluation.evidence_check_passed,
            "speculation_risk": output.sufficiency_evaluation.speculation_risk,
        },
    }

    # Add expansion hint if needed
    if analyzer.needs_domain_expansion(output.sufficiency_evaluation):
        expansion_gaps = [
            g for g in analyzer.get_all_gaps(output.sufficiency_evaluation) if g.outside_current_expertise
        ]
        result["domain_expansion_hints"] = [
            {"description": g.description, "suspected_domain": g.suspected_domain} for g in expansion_gaps
        ]

    return result, output


async def run_clarifier(
    client: LLMClient,
    query: str,
    analyzer_output: AnalyzerOutput,
    vocabulary: dict[str, str],
    clarification_patterns: dict[str, list[str]],
    retrieval_summary: list[Any] | None = None,
) -> tuple[dict[str, Any], ClarifierOutput]:
    """Run Clarifier agent when there are non-retrievable gaps.

    Args:
        client: LLM client.
        query: Original query.
        analyzer_output: AnalyzerOutput with gaps.
        vocabulary: Domain vocabulary.
        clarification_patterns: Domain-specific example questions by gap type.
        retrieval_summary: Optional retrieval history.

    Returns:
        Tuple of result dict and ClarifierOutput.
    """
    clarifier = ClarifierAgent(client)

    # Collect all gaps from analyzer
    all_gaps = (
        analyzer_output.sufficiency_evaluation.critical_gaps
        + analyzer_output.sufficiency_evaluation.nice_to_have_gaps
    )

    clarifier_input = ClarifierInput(
        original_query=query,
        gaps=all_gaps,
        vocabulary=vocabulary,
        retrieval_history=retrieval_summary or [],
        previous_clarifications=[],
        clarification_patterns=clarification_patterns,
    )

    print_section("Clarifier Input")
    print(f"Query: {query}")
    print(f"Total gaps: {len(all_gaps)}")
    non_retrievable = clarifier.filter_non_retrievable_gaps(all_gaps)
    print(f"Non-retrievable gaps: {len(non_retrievable)}")
    for gap in non_retrievable:
        print(f"  - {gap.gap_type.value}: {gap.description}")
    print(f"Clarification patterns: {len(clarification_patterns)} gap types")
    for gap_type, questions in clarification_patterns.items():
        print(f"  - {gap_type}: {len(questions)} example questions")

    print_section("Running Clarifier...")
    output = await clarifier.clarify(clarifier_input)

    result: dict[str, Any] = {
        "has_questions": clarifier.has_questions(output),
        "question_count": len(output.questions),
        "context_explanation": output.context_explanation,
        "fallback_action": output.fallback_action,
    }

    if output.questions:
        result["questions"] = [
            {
                "question": q.question,
                "gap_addressed": q.gap_addressed,
                "options": q.options,
                "required": q.required,
            }
            for q in output.questions
        ]

    return result, output


def collect_clarification_answers(clarifier_output: ClarifierOutput) -> dict[str, str]:
    """Interactively collect user answers to clarification questions.

    Args:
        clarifier_output: Output from Clarifier with questions.

    Returns:
        Dict mapping question text to user's answer.
    """
    answers: dict[str, str] = {}

    if not clarifier_output.questions:
        return answers

    print_section("Clarification Needed")
    print(f"\n{clarifier_output.context_explanation}\n")

    for i, q in enumerate(clarifier_output.questions, 1):
        print(f"\nQuestion {i}/{len(clarifier_output.questions)}:")
        print(f"  {q.question}")
        if q.gap_addressed:
            print(f"  (Addresses: {q.gap_addressed})")

        if q.options:
            print("\n  Options:")
            for j, opt in enumerate(q.options, 1):
                print(f"    {j}. {opt}")
            print(f"    {len(q.options) + 1}. (Other - type your answer)")

            while True:
                try:
                    choice = input(f"\n  Select option (1-{len(q.options) + 1}) or type answer: ").strip()
                    if not choice:
                        print("  Please enter an answer.")
                        continue

                    if choice.isdigit():
                        idx = int(choice)
                        if 1 <= idx <= len(q.options):
                            answers[q.question] = q.options[idx - 1]
                            break
                        elif idx == len(q.options) + 1:
                            custom = input("  Your answer: ").strip()
                            if custom:
                                answers[q.question] = custom
                                break
                            print("  Please enter an answer.")
                            continue
                        else:
                            print(f"  Please select 1-{len(q.options) + 1}")
                            continue

                    # Free-form answer - store with options context for LLM
                    options_ctx = ", ".join(f"{i+1}={opt}" for i, opt in enumerate(q.options))
                    answers[q.question] = f"{choice} (options were: {options_ctx})"
                    break
                except (KeyboardInterrupt, EOFError):
                    print("\n  (Skipped)")
                    break
        else:
            # Free-form question
            while True:
                try:
                    answer = input("  Your answer: ").strip()
                    if answer:
                        answers[q.question] = answer
                        break
                    elif not q.required:
                        print("  (Skipped - optional question)")
                        break
                    print("  This question is required. Please enter an answer.")
                except (KeyboardInterrupt, EOFError):
                    print("\n  (Skipped)")
                    break

    return answers


def format_clarification_context(answers: dict[str, str]) -> str:
    """Format collected answers as context for synthesis.

    Args:
        answers: Dict mapping questions to user answers.

    Returns:
        Formatted context string.
    """
    if not answers:
        return ""

    lines = ["User clarifications:"]
    for question, answer in answers.items():
        # Shorten question for readability
        short_q = question[:60] + "..." if len(question) > 60 else question
        lines.append(f"- Q: {short_q}")
        lines.append(f"  A: {answer}")

    return "\n".join(lines)


def build_user_responses_for_evaluator(
    raw_answers: dict[str, str],
    clarifier_output: ClarifierOutput,
) -> dict[str, str]:
    """Convert raw answers to user_responses format for Evaluator.

    Args:
        raw_answers: Dict mapping question text to user's answer.
        clarifier_output: ClarifierOutput containing question metadata.

    Returns:
        Dict mapping gap_addressed to user's answer.
    """
    user_responses: dict[str, str] = {}
    for q in clarifier_output.questions:
        if q.question in raw_answers:
            user_responses[q.gap_addressed] = raw_answers[q.question]
    return user_responses


async def run_synthesizer(
    client: LLMClient,
    query: str,
    analyzer_output: AnalyzerOutput,
    planner_output: PlannerOutput,
    vocabulary: dict[str, str],
    response_style: Literal["concise", "detailed"] = "concise",
    clarification_context: str = "",
) -> tuple[dict[str, Any], SynthesizerOutput]:
    """Run Synthesizer agent and return results.

    Args:
        client: LLM client.
        query: Original query.
        analyzer_output: AnalyzerOutput with findings.
        planner_output: PlannerOutput with query type.
        vocabulary: Domain vocabulary.
        response_style: "concise" or "detailed".
        clarification_context: Optional context from user clarification answers.

    Returns:
        Tuple of result dict and SynthesizerOutput.
    """
    synthesizer = SynthesizerAgent(client)

    # Augment query with clarification context if provided
    augmented_query = query
    if clarification_context:
        augmented_query = f"{query}\n\n{clarification_context}"

    synthesizer_input = SynthesizerInput(
        query=augmented_query,
        query_type=planner_output.query_type,
        analysis=analyzer_output,
        vocabulary=vocabulary,
        is_partial=False,
        response_style=response_style,
    )

    print_section("Synthesizer Input")
    print(f"Query: {query}")
    if clarification_context:
        print(f"Clarification context: {len(clarification_context)} chars")
    print(f"Query type: {planner_output.query_type.value}")
    print(f"Response style: {response_style}")
    print(f"Analyzer verdict: {analyzer_output.verdict.value}")

    print_section("Running Synthesizer...")
    output = await synthesizer.synthesize(synthesizer_input)

    result: dict[str, Any] = {
        "response": output.response,
        "key_points": output.key_points,
        "evidence_cited": output.evidence_cited,
        "confidence": output.confidence,
    }

    if output.gaps_disclosed:
        result["gaps_disclosed"] = output.gaps_disclosed

    return result, output


# Default evaluation rules for testing
DEFAULT_EVALUATION_RULES = [
    "Do not make claims without supporting data",
    "Acknowledge uncertainty when evidence is limited",
    "Never provide medical, legal, or financial advice without disclaimers",
]


def get_evaluation_rules(selected_domains: list[str]) -> list[str]:
    """Get merged evaluation rules from selected domains.

    Args:
        selected_domains: List of selected domain names.

    Returns:
        List of evaluation rules (defaults if domains have none).
    """
    domain_modules = {
        general_fitness.name: general_fitness,
        strength.name: strength,
        nutrition.name: nutrition,
        running.name: running,
    }

    rules: list[str] = []
    for name in selected_domains:
        if name in domain_modules:
            module = domain_modules[name]
            # Check if module has response_evaluation_rules attribute
            if hasattr(module, "response_evaluation_rules"):
                rules.extend(module.response_evaluation_rules)

    return rules if rules else DEFAULT_EVALUATION_RULES


def build_entries_summary(entries: list[Any]) -> str:
    """Build a summary of retrieved entries for evaluator context.

    Args:
        entries: List of Entry objects.

    Returns:
        Summary string of entries.
    """
    if not entries:
        return "(No entries available)"

    lines: list[str] = []
    lines.append(f"{len(entries)} entries found:")

    for entry in entries[:10]:  # Limit to first 10 for summary
        date_str = str(entry.date) if hasattr(entry, "date") else "unknown"
        content = entry.raw_content if hasattr(entry, "raw_content") else str(entry)
        # Truncate content if too long
        if len(content) > 100:
            content = content[:100] + "..."
        lines.append(f"- {date_str}: {content}")

    if len(entries) > 10:
        lines.append(f"... and {len(entries) - 10} more entries")

    return "\n".join(lines)


async def run_evaluator(
    client: LLMClient,
    query: str,
    response: str,
    analyzer_output: AnalyzerOutput,
    entries_summary: str,
    evaluation_rules: list[str],
    attempt_number: int = 1,
    previous_feedback: list[EvaluationFeedback] | None = None,
    user_responses: dict[str, str] | None = None,
) -> tuple[dict[str, Any], EvaluatorOutput]:
    """Run Evaluator agent and return results.

    Args:
        client: LLM client.
        query: Original query.
        response: Synthesized response to evaluate.
        analyzer_output: AnalyzerOutput with findings.
        entries_summary: Summary of retrieved entries.
        evaluation_rules: Domain-specific rules.
        attempt_number: Current attempt number.
        previous_feedback: Feedback from previous attempts.
        user_responses: User's answers to clarification questions (gap_addressed -> answer).

    Returns:
        Tuple of result dict and EvaluatorOutput.
    """
    evaluator = EvaluatorAgent(client)

    evaluator_input = EvaluatorInput(
        query=query,
        response=response,
        analysis=analyzer_output,
        entries_summary=entries_summary,
        evaluation_rules=evaluation_rules,
        attempt_number=attempt_number,
        previous_feedback=previous_feedback or [],
        user_responses=user_responses or {},
    )

    print_section("Evaluator Input")
    print(f"Query: {query}")
    print(f"Response length: {len(response)} chars")
    print(f"Attempt: {attempt_number}")
    print(f"Evaluation rules: {len(evaluation_rules)} rules")
    if user_responses:
        print(f"User responses: {len(user_responses)} clarification answer(s)")

    print_section("Running Evaluator...")
    output = await evaluator.evaluate(evaluator_input)

    result: dict[str, Any] = {
        "overall_verdict": output.overall_verdict.value,
        "recommendation": output.recommendation,
        "dimensions": [
            {
                "dimension": d.dimension,
                "verdict": d.verdict.value,
                "reasoning": d.reasoning[:100] + "..." if len(d.reasoning) > 100 else d.reasoning,
                "issues": d.issues,
            }
            for d in output.dimensions
        ],
    }

    if output.feedback:
        result["feedback"] = [{"issue": f.issue, "suggestion": f.suggestion} for f in output.feedback]

    # Add helper method results
    result["is_passed"] = evaluator.is_passed(output)
    failed_dims = evaluator.get_failed_dimensions(output)
    if failed_dims:
        result["failed_dimensions"] = [d.dimension for d in failed_dims]
        result["all_issues"] = evaluator.get_all_issues(output)
    result["should_retry"] = evaluator.should_retry(output, attempt_number)

    return result, output


async def run_retry_loop(
    client: LLMClient,
    query: str,
    planner_output: PlannerOutput,
    analyzer_output: AnalyzerOutput,
    vocabulary: dict[str, str],
    entries_summary: str,
    evaluation_rules: list[str],
    max_retries: int = 2,
) -> tuple[dict[str, Any], SynthesizerOutput, EvaluatorOutput]:
    """Run synthesis + evaluation loop with retry on FAIL.

    Args:
        client: LLM client.
        query: Original query.
        planner_output: PlannerOutput from planner.
        analyzer_output: AnalyzerOutput from analyzer.
        vocabulary: Domain vocabulary.
        entries_summary: Summary of retrieved entries.
        evaluation_rules: Domain-specific rules.
        max_retries: Maximum retry attempts.

    Returns:
        Tuple of result dict, final SynthesizerOutput, final EvaluatorOutput.
    """
    synthesizer = SynthesizerAgent(client)
    evaluator = EvaluatorAgent(client)

    attempt_number = 1
    previous_feedback: list[EvaluationFeedback] = []
    synth_output: SynthesizerOutput | None = None
    eval_output: EvaluatorOutput | None = None

    while attempt_number <= max_retries + 1:  # +1 for initial attempt
        print_section(f"Retry Loop - Attempt {attempt_number}/{max_retries + 1}")

        # Generate response
        synthesizer_input = SynthesizerInput(
            query=query,
            query_type=planner_output.query_type,
            analysis=analyzer_output,
            vocabulary=vocabulary,
            is_partial=False,
            response_style="concise",
        )

        print_section("Running Synthesizer...")
        synth_output = await synthesizer.synthesize(synthesizer_input)
        response_text = synth_output.response
        response_preview = response_text[:200] + "..." if len(response_text) > 200 else response_text
        print(f"Response: {response_preview}")

        # Evaluate response
        evaluator_input = EvaluatorInput(
            query=query,
            response=synth_output.response,
            analysis=analyzer_output,
            entries_summary=entries_summary,
            evaluation_rules=evaluation_rules,
            attempt_number=attempt_number,
            previous_feedback=previous_feedback,
        )

        print_section("Running Evaluator...")
        eval_output = await evaluator.evaluate(evaluator_input)

        print(f"Verdict: {eval_output.overall_verdict.value}")
        print(f"Recommendation: {eval_output.recommendation}")

        # Check result
        if evaluator.is_passed(eval_output):
            print("\n** PASSED - Returning response **")
            break

        # Collect feedback for next attempt
        previous_feedback.extend(eval_output.feedback)
        print(f"Failed dimensions: {[d.dimension for d in evaluator.get_failed_dimensions(eval_output)]}")
        print(f"Collected {len(previous_feedback)} feedback items for retry")

        attempt_number += 1

    assert synth_output is not None
    assert eval_output is not None

    # Compile result
    result: dict[str, Any] = {
        "total_attempts": attempt_number,
        "final_verdict": eval_output.overall_verdict.value,
        "final_recommendation": eval_output.recommendation,
        "response": synth_output.response,
        "key_points": synth_output.key_points,
        "confidence": synth_output.confidence,
    }

    if not evaluator.is_passed(eval_output):
        result["note"] = "Retry limit exceeded - returning best available response"
        result["remaining_issues"] = evaluator.get_all_issues(eval_output)

    return result, synth_output, eval_output


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
        # QUERY: Run Planner, then Retriever, then Analyzer
        planner_output: PlannerOutput | None = None
        retriever_output: RetrieverOutput | None = None
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
                retriever_result, retriever_output = await run_retriever(storage, planner_output, vocabulary)
                print_section("Retriever Output")
                print_json(retriever_result)
            except Exception as e:
                print(f"\nRetriever ERROR: {e}")

            # Run Analyzer if retriever succeeded
            analyzer_output: AnalyzerOutput | None = None
            if retriever_output is not None:
                try:
                    domain_context = build_active_domain_context(selected_domains)
                    analyzer_result, analyzer_output = await run_analyzer(
                        client, raw_input, retriever_output, planner_output, domain_context
                    )
                    print_section("Analyzer Output")
                    print_json(analyzer_result)
                except Exception as e:
                    print(f"\nAnalyzer ERROR: {e}")

                # Track clarification context for synthesis and user_responses for evaluator
                clarification_context = ""
                user_responses: dict[str, str] = {}

                # Run Clarifier if there are non-retrievable gaps
                if analyzer_output is not None:
                    all_gaps = (
                        analyzer_output.sufficiency_evaluation.critical_gaps
                        + analyzer_output.sufficiency_evaluation.nice_to_have_gaps
                    )
                    non_retrievable_types = {GapType.SUBJECTIVE, GapType.CLARIFICATION}
                    has_non_retrievable = any(g.gap_type in non_retrievable_types for g in all_gaps)

                    if has_non_retrievable:
                        try:
                            vocabulary = get_merged_vocabulary(selected_domains)
                            patterns = get_merged_clarification_patterns(selected_domains)
                            clarifier_result, clarifier_output = await run_clarifier(
                                client,
                                raw_input,
                                analyzer_output,
                                vocabulary,
                                patterns,
                                retriever_output.retrieval_summary if retriever_output else None,
                            )
                            print_section("Clarifier Output")
                            print_json(clarifier_result)

                            # Collect user answers if there are questions
                            if clarifier_output.questions:
                                answers = collect_clarification_answers(clarifier_output)
                                if answers:
                                    clarification_context = format_clarification_context(answers)
                                    # Convert to gap_addressed -> answer format for Evaluator
                                    user_responses = build_user_responses_for_evaluator(
                                        answers, clarifier_output
                                    )
                                    print_section("Collected Answers")
                                    print(clarification_context)
                        except Exception as e:
                            print(f"\nClarifier ERROR: {e}")

                # Run Synthesizer + Evaluator if analyzer succeeded
                if analyzer_output is not None:
                    try:
                        vocabulary = get_merged_vocabulary(selected_domains)
                        synthesizer_result, synthesizer_output = await run_synthesizer(
                            client,
                            raw_input,
                            analyzer_output,
                            planner_output,
                            vocabulary,
                            clarification_context=clarification_context,
                        )
                        print_section("Synthesizer Output")
                        print_json(synthesizer_result)

                        # Run Evaluator after Synthesizer
                        try:
                            entries_summary = build_entries_summary(retriever_output.entries)
                            evaluation_rules = get_evaluation_rules(selected_domains)
                            evaluator_result, _ = await run_evaluator(
                                client,
                                raw_input,
                                synthesizer_output.response,
                                analyzer_output,
                                entries_summary,
                                evaluation_rules,
                                user_responses=user_responses,
                            )
                            print_section("Evaluator Output")
                            print_json(evaluator_result)
                        except Exception as e:
                            print(f"\nEvaluator ERROR: {e}")
                    except Exception as e:
                        print(f"\nSynthesizer ERROR: {e}")
        elif not storage:
            print("\n(No --storage-dir specified, skipping Retriever and Analyzer)")

    elif input_type == InputType.BOTH:
        # BOTH: Run Parser on log_portion, Planner + Retriever + Analyzer on query_portion
        log_portion = router_result.get("log_portion", raw_input)
        query_portion = router_result.get("query_portion", "")

        # Run Parser on log portion
        try:
            parser_result = await run_parser(client, log_portion, selected_domains)
            print_section("Parser Output (log portion)")
            print_json(parser_result)
        except Exception as e:
            print(f"\nParser ERROR: {e}")

        # Run Planner + Retriever + Analyzer on query portion
        planner_output: PlannerOutput | None = None
        retriever_output: RetrieverOutput | None = None
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
                    retriever_result, retriever_output = await run_retriever(storage, planner_output, vocabulary)
                    print_section("Retriever Output (query portion)")
                    print_json(retriever_result)
                except Exception as e:
                    print(f"\nRetriever ERROR: {e}")

                # Run Analyzer if retriever succeeded
                analyzer_output: AnalyzerOutput | None = None
                if retriever_output is not None:
                    try:
                        domain_context = build_active_domain_context(selected_domains)
                        analyzer_result, analyzer_output = await run_analyzer(
                            client, query_portion, retriever_output, planner_output, domain_context
                        )
                        print_section("Analyzer Output (query portion)")
                        print_json(analyzer_result)
                    except Exception as e:
                        print(f"\nAnalyzer ERROR: {e}")

                    # Track clarification context for synthesis and user_responses for evaluator
                    clarification_context = ""
                    user_responses_both: dict[str, str] = {}

                    # Run Clarifier if there are non-retrievable gaps
                    if analyzer_output is not None:
                        all_gaps = (
                            analyzer_output.sufficiency_evaluation.critical_gaps
                            + analyzer_output.sufficiency_evaluation.nice_to_have_gaps
                        )
                        non_retrievable_types = {GapType.SUBJECTIVE, GapType.CLARIFICATION}
                        has_non_retrievable = any(g.gap_type in non_retrievable_types for g in all_gaps)

                        if has_non_retrievable:
                            try:
                                vocabulary = get_merged_vocabulary(selected_domains)
                                patterns = get_merged_clarification_patterns(selected_domains)
                                clarifier_result, clarifier_output = await run_clarifier(
                                    client,
                                    query_portion,
                                    analyzer_output,
                                    vocabulary,
                                    patterns,
                                    retriever_output.retrieval_summary if retriever_output else None,
                                )
                                print_section("Clarifier Output (query portion)")
                                print_json(clarifier_result)

                                # Collect user answers if there are questions
                                if clarifier_output.questions:
                                    answers = collect_clarification_answers(clarifier_output)
                                    if answers:
                                        clarification_context = format_clarification_context(answers)
                                        # Convert to gap_addressed -> answer format for Evaluator
                                        user_responses_both = build_user_responses_for_evaluator(
                                            answers, clarifier_output
                                        )
                                        print_section("Collected Answers (query portion)")
                                        print(clarification_context)
                            except Exception as e:
                                print(f"\nClarifier ERROR: {e}")

                    # Run Synthesizer + Evaluator if analyzer succeeded
                    if analyzer_output is not None:
                        try:
                            vocabulary = get_merged_vocabulary(selected_domains)
                            synthesizer_result, synthesizer_output = await run_synthesizer(
                                client,
                                query_portion,
                                analyzer_output,
                                planner_output,
                                vocabulary,
                                clarification_context=clarification_context,
                            )
                            print_section("Synthesizer Output (query portion)")
                            print_json(synthesizer_result)

                            # Run Evaluator after Synthesizer
                            try:
                                entries_summary = build_entries_summary(retriever_output.entries)
                                evaluation_rules = get_evaluation_rules(selected_domains)
                                evaluator_result, _ = await run_evaluator(
                                    client,
                                    query_portion,
                                    synthesizer_output.response,
                                    analyzer_output,
                                    entries_summary,
                                    evaluation_rules,
                                    user_responses=user_responses_both,
                                )
                                print_section("Evaluator Output (query portion)")
                                print_json(evaluator_result)
                            except Exception as e:
                                print(f"\nEvaluator ERROR: {e}")
                        except Exception as e:
                            print(f"\nSynthesizer ERROR: {e}")
            elif not storage:
                print("\n(No --storage-dir specified, skipping Retriever and Analyzer)")
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
