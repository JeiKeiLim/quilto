#!/usr/bin/env bash
#
# auto-dogfood.sh - Automated dogfooding for Quilto/Swealog
#
# This script automates the feedback collection cycle:
# 1. Generate diverse test queries using Claude
# 2. Run queries through swealog auto --debug
# 3. Review outputs with Claude and fill feedback
#
# Usage:
#   ./scripts/auto-dogfood.sh [options]
#
# Options:
#   -n, --num-queries NUM   Number of queries to generate (default: 10)
#   -c, --config PATH       LLM config file (default: llm-config.yaml)
#   -s, --skip-generate     Skip query generation, use existing queries file
#   -r, --skip-run          Skip running queries, review existing feedback files
#   -h, --help              Show this help message
#
# Requirements:
#   - claude CLI (Anthropic Claude Code)
#   - uv (Python package manager)
#   - jq (JSON processor)

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
FEEDBACK_DIR="$PROJECT_ROOT/tests/eval/feedback/active"
QUERIES_FILE="$PROJECT_ROOT/tests/eval/feedback/auto-queries.txt"
LLM_CONFIG="llm-config-openai.yaml"
NUM_QUERIES=10
SKIP_GENERATE=false
SKIP_RUN=false

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[OK]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

usage() {
    head -25 "$0" | tail -20
    exit 0
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -n|--num-queries)
            NUM_QUERIES="$2"
            shift 2
            ;;
        -c|--config)
            LLM_CONFIG="$2"
            shift 2
            ;;
        -s|--skip-generate)
            SKIP_GENERATE=true
            shift
            ;;
        -r|--skip-run)
            SKIP_RUN=true
            shift
            ;;
        -h|--help)
            usage
            ;;
        *)
            log_error "Unknown option: $1"
            usage
            ;;
    esac
done

# Check dependencies
check_dependencies() {
    log_info "Checking dependencies..."

    if ! command -v claude &> /dev/null; then
        log_error "claude CLI not found. Install with: npm install -g @anthropic-ai/claude-code"
        exit 1
    fi

    if ! command -v uv &> /dev/null; then
        log_error "uv not found. Install with: curl -LsSf https://astral.sh/uv/install.sh | sh"
        exit 1
    fi

    if ! command -v jq &> /dev/null; then
        log_error "jq not found. Install with: brew install jq"
        exit 1
    fi

    log_success "All dependencies found"
}

# Step 1: Generate test queries
generate_queries() {
    if [[ "$SKIP_GENERATE" == "true" ]]; then
        if [[ ! -f "$QUERIES_FILE" ]]; then
            log_error "No queries file found at $QUERIES_FILE"
            exit 1
        fi
        log_info "Skipping query generation, using existing file"
        return
    fi

    log_info "Generating $NUM_QUERIES test queries..."

    local prompt="Generate exactly $NUM_QUERIES diverse test queries for a fitness logging app called Swealog.

The app allows users to:
- Log workouts in natural language (Korean or English)
- Ask questions about their workout history
- Get recommendations based on their logs

Generate queries covering these categories (mix of Korean and English):
1. Temporal queries (\"last week\", \"yesterday\", \"in January\")
2. Specific exercise queries (bench press, running, squats)
3. Recommendation queries (\"what should I do today?\")
4. Analysis queries (\"how has my strength progressed?\")
5. Edge cases (vague queries, goal statements, mixed language)
6. 1RM estimation queries
7. Comparison queries (\"compare my running vs lifting\")

Output format: One query per line, no numbering, no explanations.
Mix languages naturally (some Korean, some English, some mixed).

Example outputs:
지난주 벤치프레스 기록 보여줘
What was my heaviest deadlift?
오늘 뭐 하면 좋을까?
How has my running pace improved?"

    claude -p "$prompt" --output-format text > "$QUERIES_FILE"

    local count
    count=$(wc -l < "$QUERIES_FILE" | tr -d ' ')
    log_success "Generated $count queries -> $QUERIES_FILE"
}

# Step 2: Run queries through swealog
run_queries() {
    if [[ "$SKIP_RUN" == "true" ]]; then
        log_info "Skipping query execution, reviewing existing feedback files"
        return
    fi

    if [[ ! -f "$QUERIES_FILE" ]]; then
        log_error "No queries file found at $QUERIES_FILE"
        exit 1
    fi

    log_info "Running queries through swealog auto..."

    mkdir -p "$FEEDBACK_DIR"

    local total
    total=$(wc -l < "$QUERIES_FILE" | tr -d ' ')
    local count=0

    while IFS= read -r query || [[ -n "$query" ]]; do
        # Skip empty lines
        [[ -z "$query" ]] && continue

        ((count++))
        log_info "[$count/$total] Running: ${query:0:50}..."

        # Run swealog auto with debug mode and non-interactive flag
        # This creates JSON files in tests/eval/feedback/active/
        # --non-interactive skips the feedback prompt (to be filled by auto-review)
        if ! uv run swealog auto "$query" --debug --non-interactive --config "$LLM_CONFIG" 2>/dev/null; then
            log_warn "Query failed: $query"
        fi

        # Small delay to avoid rate limiting
        sleep 1

    done < "$QUERIES_FILE"

    log_success "Executed $count queries"
}

# Step 3: Review and fill feedback using Claude
review_feedback() {
    log_info "Reviewing feedback files with Claude..."

    local files
    files=$(find "$FEEDBACK_DIR" -name "*.json" -type f 2>/dev/null || true)

    if [[ -z "$files" ]]; then
        log_warn "No feedback files found in $FEEDBACK_DIR"
        return
    fi

    local total
    total=$(echo "$files" | wc -l | tr -d ' ')
    local count=0

    for json_file in $files; do
        ((count++))
        local filename
        filename=$(basename "$json_file")

        # Check if feedback already filled
        local existing_feedback
        existing_feedback=$(jq -r '.user_feedback // ""' "$json_file")

        if [[ -n "$existing_feedback" && "$existing_feedback" != "null" ]]; then
            log_info "[$count/$total] Skipping $filename (feedback exists)"
            continue
        fi

        log_info "[$count/$total] Reviewing $filename..."

        # Extract key fields for review
        local query final_response
        query=$(jq -r '.query' "$json_file")
        final_response=$(jq -r '.final_response' "$json_file")

        # Get intermediate outputs summary
        local router_type planner_action retriever_count analyzer_verdict
        router_type=$(jq -r '.intermediate_outputs.router.input_type // "unknown"' "$json_file")
        planner_action=$(jq -r '.intermediate_outputs.planner.next_action // "unknown"' "$json_file")
        retriever_count=$(jq -r '.intermediate_outputs.retriever.total_entries_found // 0' "$json_file")
        analyzer_verdict=$(jq -r '.intermediate_outputs.analyzer.verdict // "unknown"' "$json_file")

        # Create review prompt
        local review_prompt="You are evaluating a fitness AI assistant's response. Act as a critical but fair user.

## Query
$query

## System Classification
- Router: $router_type
- Planner action: $planner_action
- Entries retrieved: $retriever_count
- Analyzer verdict: $analyzer_verdict

## Final Response
$final_response

## Your Task
Evaluate this response as if you were the user who asked the question. Consider:
1. Did it answer the question appropriately?
2. Was the retrieved data relevant (if any)?
3. Is the response helpful and actionable?
4. Any obvious errors, hallucinations, or issues?
5. What could be improved?

Provide your evaluation in this exact JSON format:
{
  \"feedback\": \"Your detailed feedback as the user would give it (1-3 sentences)\",
  \"sentiment\": \"positive|mixed|negative\"
}

Rules:
- Be critical but fair - don't be overly harsh or overly lenient
- \"positive\" = response was helpful and answered the question well
- \"mixed\" = partially helpful but has issues or room for improvement
- \"negative\" = failed to answer, wrong information, or major issues
- Write feedback naturally, as a real user would

Output ONLY the JSON, no other text."

        # Get Claude's review
        local review_result
        if ! review_result=$(claude -p "$review_prompt" --output-format text 2>/dev/null); then
            log_warn "Failed to review $filename"
            continue
        fi

        # Parse the review result
        local feedback sentiment
        feedback=$(echo "$review_result" | jq -r '.feedback // empty' 2>/dev/null || echo "")
        sentiment=$(echo "$review_result" | jq -r '.sentiment // empty' 2>/dev/null || echo "")

        if [[ -z "$feedback" || -z "$sentiment" ]]; then
            log_warn "Failed to parse review for $filename"
            echo "Raw result: $review_result"
            continue
        fi

        # Update the JSON file with feedback
        local tmp_file
        tmp_file=$(mktemp)
        jq --arg fb "$feedback" --arg sent "$sentiment" \
            '.user_feedback = $fb | .feedback_sentiment = $sent' \
            "$json_file" > "$tmp_file"
        mv "$tmp_file" "$json_file"

        log_success "Updated $filename: [$sentiment] ${feedback:0:60}..."

        # Small delay between API calls
        sleep 2

    done

    log_success "Reviewed $count files"
}

# Summary report
generate_summary() {
    log_info "Generating summary..."

    local files
    files=$(find "$FEEDBACK_DIR" -name "*.json" -type f 2>/dev/null || true)

    if [[ -z "$files" ]]; then
        log_warn "No feedback files to summarize"
        return
    fi

    local total positive mixed negative no_feedback
    total=$(echo "$files" | wc -l | tr -d ' ')
    positive=0
    mixed=0
    negative=0
    no_feedback=0

    for json_file in $files; do
        local sentiment
        sentiment=$(jq -r '.feedback_sentiment // "none"' "$json_file")

        case "$sentiment" in
            positive) ((positive++)) ;;
            mixed) ((mixed++)) ;;
            negative) ((negative++)) ;;
            *) ((no_feedback++)) ;;
        esac
    done

    echo ""
    echo "╔═══════════════════════════════════════╗"
    echo "║     AUTO-DOGFOOD SUMMARY              ║"
    echo "╠═══════════════════════════════════════╣"
    printf "║  Total records:     %3d               ║\n" "$total"
    printf "║  ✅ Positive:       %3d (%2d%%)         ║\n" "$positive" $((positive * 100 / total))
    printf "║  ⚠️  Mixed:          %3d (%2d%%)         ║\n" "$mixed" $((mixed * 100 / total))
    printf "║  ❌ Negative:       %3d (%2d%%)         ║\n" "$negative" $((negative * 100 / total))
    if [[ $no_feedback -gt 0 ]]; then
        printf "║  ⏳ No feedback:    %3d               ║\n" "$no_feedback"
    fi
    echo "╚═══════════════════════════════════════╝"
    echo ""
    echo "Feedback files: $FEEDBACK_DIR"
    echo ""
    echo "Next steps:"
    echo "  1. Review feedback files manually if needed"
    echo "  2. Run: /bmad:bmm:workflows:retrospective to analyze patterns"
    echo "  3. Or manually analyze with Story 12.6 methodology"
}

# Main
main() {
    echo ""
    log_info "=== AUTO-DOGFOOD SCRIPT ==="
    log_info "Project: $PROJECT_ROOT"
    log_info "Config: $LLM_CONFIG"
    echo ""

    check_dependencies

    # Change to project root
    cd "$PROJECT_ROOT"

    # Run steps
    generate_queries
    run_queries
    review_feedback
    generate_summary

    log_success "Auto-dogfood complete!"
}

main "$@"
