#!/usr/bin/env bash
#
# auto-dogfood.sh - Automated dogfooding for Quilto/Swealog with Full Project Context
#
# This script automates the feedback collection cycle with maximum context awareness:
# 1. Gather comprehensive project status (epics, stories, patterns, fixes)
# 2. Generate diverse test queries informed by current iteration context
# 3. Run queries through swealog auto --debug
# 4. Review outputs with Claude using full agent/architecture understanding
#
# The script is designed to be used across all dogfooding iterations (Epic 11, 12, 13, 14+).
#
# Usage:
#   ./scripts/auto-dogfood.sh [options]
#
# Options:
#   -n, --num-queries NUM   Number of queries to generate (default: 10)
#   -c, --config PATH       LLM config file (default: llm-config-openai.yaml)
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

# Context files (generated during runtime)
CONTEXT_DIR="$PROJECT_ROOT/tests/eval/feedback/.context"
PROJECT_CONTEXT_FILE="$CONTEXT_DIR/project-context.md"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[OK]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }
log_section() { echo -e "\n${CYAN}=== $1 ===${NC}"; }

usage() {
    head -27 "$0" | tail -22
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

# =============================================================================
# STEP 0: GATHER COMPREHENSIVE PROJECT CONTEXT
# =============================================================================
# This is the key enhancement - we build a complete context document that
# Claude will use for both query generation and feedback review.

gather_project_context() {
    log_section "GATHERING PROJECT CONTEXT"

    mkdir -p "$CONTEXT_DIR"

    log_info "Building comprehensive project context for Claude..."

    # Start building the context document
    cat > "$PROJECT_CONTEXT_FILE" << 'CONTEXT_HEADER'
# Quilto/Swealog Project Context for Dogfooding

This document provides comprehensive context for automated dogfooding. Use this information to:
1. Generate queries that test recent fixes and known edge cases
2. Provide informed feedback that understands the system's architecture and capabilities
3. Identify patterns that may indicate systemic issues vs one-off problems

---

CONTEXT_HEADER

    # -----------------------------------------------------
    # Section 1: Project Identity & Architecture
    # -----------------------------------------------------
    log_info "  [1/7] Adding project identity and architecture..."

    cat >> "$PROJECT_CONTEXT_FILE" << 'ARCH_SECTION'
## 1. Project Identity

**Quilto** is a domain-agnostic agent framework for transforming unstructured notes into structured insights.
**Swealog** is a fitness application built on Quilto.

### Agent Architecture (9 Agents)

| Agent | Purpose | Key Behaviors |
|-------|---------|---------------|
| **Router** | Classify input as LOG/QUERY/BOTH/CORRECTION, select domains | First agent in pipeline |
| **Planner** | Create retrieval strategy, detect information gaps | Decides DATE_RANGE, KEYWORD, TOPICAL strategies |
| **Retriever** | Fetch entries from storage | Uses storage tools, respects strategy ordering |
| **Analyzer** | Find patterns, assess data sufficiency | Outputs verdict: sufficient/insufficient/clarify_needed |
| **Synthesizer** | Generate user-facing response | Creates detailed, evidence-based responses |
| **Evaluator** | Quality check response | Pass/Fail with specific feedback |
| **Clarifier** | Generate questions for user | Human-in-the-loop when data is missing |
| **Parser** | Extract structured data from logs | Async, domain-aware parsing |
| **Observer** | Learn patterns, update global context | Background learning |

### Query Flow

```
User Query → Router → Planner → Retriever → Analyzer → Synthesizer → Evaluator → Response
                ↑                              |
                └──────── Retry Loop ──────────┘
```

If Analyzer finds insufficient data, it can:
- Request expanded date range
- Request domain expansion
- Trigger clarification (ask user)

---

ARCH_SECTION

    # -----------------------------------------------------
    # Section 2: Current Sprint Status
    # -----------------------------------------------------
    log_info "  [2/7] Adding current sprint status..."

    echo "## 2. Current Sprint Status" >> "$PROJECT_CONTEXT_FILE"
    echo "" >> "$PROJECT_CONTEXT_FILE"

    if [[ -f "$PROJECT_ROOT/_bmad-output/implementation-artifacts/sprint-status.yaml" ]]; then
        # Extract current epic and recent story status
        echo "### Active Development" >> "$PROJECT_CONTEXT_FILE"
        echo "\`\`\`yaml" >> "$PROJECT_CONTEXT_FILE"
        # Get the last 30 lines which typically contain the current epic
        tail -50 "$PROJECT_ROOT/_bmad-output/implementation-artifacts/sprint-status.yaml" >> "$PROJECT_CONTEXT_FILE"
        echo "\`\`\`" >> "$PROJECT_CONTEXT_FILE"
    else
        echo "_Sprint status file not found_" >> "$PROJECT_CONTEXT_FILE"
    fi
    echo "" >> "$PROJECT_CONTEXT_FILE"
    echo "---" >> "$PROJECT_CONTEXT_FILE"
    echo "" >> "$PROJECT_CONTEXT_FILE"

    # -----------------------------------------------------
    # Section 3: Previous Iteration Analysis
    # -----------------------------------------------------
    log_info "  [3/7] Adding previous iteration analysis..."

    echo "## 3. Previous Iteration Patterns & Fixes" >> "$PROJECT_CONTEXT_FILE"
    echo "" >> "$PROJECT_CONTEXT_FILE"

    # Find the most recent iteration analysis
    local latest_iter=""
    for iter_dir in "$PROJECT_ROOT/tests/eval/feedback/archive"/iter-*; do
        if [[ -d "$iter_dir" ]]; then
            latest_iter="$iter_dir"
        fi
    done

    if [[ -n "$latest_iter" && -f "$latest_iter/analysis.md" ]]; then
        local iter_name
        iter_name=$(basename "$latest_iter")
        echo "### Most Recent Analysis: $iter_name" >> "$PROJECT_CONTEXT_FILE"
        echo "" >> "$PROJECT_CONTEXT_FILE"

        # Extract the executive summary and patterns
        echo "**Executive Summary:**" >> "$PROJECT_CONTEXT_FILE"
        # Get lines between "## Executive Summary" and "---"
        sed -n '/## Executive Summary/,/^---$/p' "$latest_iter/analysis.md" | head -20 >> "$PROJECT_CONTEXT_FILE"
        echo "" >> "$PROJECT_CONTEXT_FILE"

        echo "**Patterns Identified:**" >> "$PROJECT_CONTEXT_FILE"
        # Extract pattern names and status
        grep -E "^### Pattern [0-9]+:" "$latest_iter/analysis.md" >> "$PROJECT_CONTEXT_FILE" || true
        echo "" >> "$PROJECT_CONTEXT_FILE"

        # Also include the recommendations
        echo "**Recommendations Applied:**" >> "$PROJECT_CONTEXT_FILE"
        sed -n '/## Recommendations/,/^---$/p' "$latest_iter/analysis.md" | head -15 >> "$PROJECT_CONTEXT_FILE" || true
    else
        echo "_No previous iteration analysis found_" >> "$PROJECT_CONTEXT_FILE"
    fi
    echo "" >> "$PROJECT_CONTEXT_FILE"
    echo "---" >> "$PROJECT_CONTEXT_FILE"
    echo "" >> "$PROJECT_CONTEXT_FILE"

    # -----------------------------------------------------
    # Section 4: Recent Code Changes (Stories Completed)
    # -----------------------------------------------------
    log_info "  [4/7] Adding recent code changes and fixes..."

    echo "## 4. Recent Code Changes (What Was Fixed)" >> "$PROJECT_CONTEXT_FILE"
    echo "" >> "$PROJECT_CONTEXT_FILE"

    # Get recent commits related to stories
    echo "### Recent Git Commits" >> "$PROJECT_CONTEXT_FILE"
    echo "\`\`\`" >> "$PROJECT_CONTEXT_FILE"
    git -C "$PROJECT_ROOT" log --oneline -20 2>/dev/null >> "$PROJECT_CONTEXT_FILE" || echo "Could not get git log"
    echo "\`\`\`" >> "$PROJECT_CONTEXT_FILE"
    echo "" >> "$PROJECT_CONTEXT_FILE"

    # Find recently completed story files and extract their dev notes
    echo "### Recently Completed Stories (Dev Notes Summary)" >> "$PROJECT_CONTEXT_FILE"
    echo "" >> "$PROJECT_CONTEXT_FILE"

    # Get the most recent epic directory
    local latest_epic_dir=""
    for epic_dir in "$PROJECT_ROOT/_bmad-output/implementation-artifacts"/epic-*; do
        if [[ -d "$epic_dir" ]]; then
            latest_epic_dir="$epic_dir"
        fi
    done

    if [[ -n "$latest_epic_dir" ]]; then
        local epic_name
        epic_name=$(basename "$latest_epic_dir")
        echo "**$epic_name Stories:**" >> "$PROJECT_CONTEXT_FILE"
        echo "" >> "$PROJECT_CONTEXT_FILE"

        # List story files and their status
        for story_file in "$latest_epic_dir"/*.md; do
            if [[ -f "$story_file" ]]; then
                local story_name
                story_name=$(basename "$story_file" .md)
                local story_title
                story_title=$(grep -m1 "^# Story" "$story_file" 2>/dev/null | head -1 || echo "Unknown")
                local story_status
                story_status=$(grep -m1 "^Status:" "$story_file" 2>/dev/null | head -1 || echo "Unknown")
                echo "- **$story_name**: $story_status" >> "$PROJECT_CONTEXT_FILE"

                # Extract a brief summary of what was done (from Completion Notes if available)
                local completion_notes
                completion_notes=$(sed -n '/### Completion Notes/,/^##/p' "$story_file" 2>/dev/null | head -10 || true)
                if [[ -n "$completion_notes" ]]; then
                    echo "  - $(echo "$completion_notes" | grep -v "^#" | head -3 | tr '\n' ' ')" >> "$PROJECT_CONTEXT_FILE"
                fi
            fi
        done
    fi
    echo "" >> "$PROJECT_CONTEXT_FILE"
    echo "---" >> "$PROJECT_CONTEXT_FILE"
    echo "" >> "$PROJECT_CONTEXT_FILE"

    # -----------------------------------------------------
    # Section 5: Known Technical Debt & Limitations
    # -----------------------------------------------------
    log_info "  [5/7] Adding known technical debt and limitations..."

    echo "## 5. Known Technical Debt & Limitations" >> "$PROJECT_CONTEXT_FILE"
    echo "" >> "$PROJECT_CONTEXT_FILE"

    # Check for tech debt documentation
    if [[ -f "$PROJECT_ROOT/_bmad-output/tech-debt.md" ]]; then
        head -50 "$PROJECT_ROOT/_bmad-output/tech-debt.md" >> "$PROJECT_CONTEXT_FILE"
    else
        # Extract from retrospectives or known issues
        echo "### Current Limitations" >> "$PROJECT_CONTEXT_FILE"
        echo "" >> "$PROJECT_CONTEXT_FILE"
        echo "- **No embeddings**: Retrieval uses date-range and keyword only (no semantic search)" >> "$PROJECT_CONTEXT_FILE"
        echo "- **Single storage**: File-based storage only (no database support yet)" >> "$PROJECT_CONTEXT_FILE"
        echo "- **English/Korean only**: Multilingual support limited to these languages" >> "$PROJECT_CONTEXT_FILE"
        echo "- **Local LLM quality**: Ollama models may have lower quality than cloud APIs" >> "$PROJECT_CONTEXT_FILE"
        echo "" >> "$PROJECT_CONTEXT_FILE"

        # Check for any tech debt in retrospectives
        local latest_retro=""
        for retro in "$PROJECT_ROOT/_bmad-output/implementation-artifacts"/epic-*/retro-*.md; do
            if [[ -f "$retro" ]]; then
                latest_retro="$retro"
            fi
        done

        if [[ -n "$latest_retro" ]]; then
            echo "### From Latest Retrospective" >> "$PROJECT_CONTEXT_FILE"
            sed -n '/## Tech Debt/,/^##/p' "$latest_retro" 2>/dev/null | head -20 >> "$PROJECT_CONTEXT_FILE" || true
            sed -n '/## Known Issues/,/^##/p' "$latest_retro" 2>/dev/null | head -20 >> "$PROJECT_CONTEXT_FILE" || true
        fi
    fi
    echo "" >> "$PROJECT_CONTEXT_FILE"
    echo "---" >> "$PROJECT_CONTEXT_FILE"
    echo "" >> "$PROJECT_CONTEXT_FILE"

    # -----------------------------------------------------
    # Section 6: User Data Context (Storage Summary)
    # -----------------------------------------------------
    log_info "  [6/7] Adding user data context (storage summary)..."

    echo "## 6. User Data Context (What's in Storage)" >> "$PROJECT_CONTEXT_FILE"
    echo "" >> "$PROJECT_CONTEXT_FILE"

    # Get storage summary if logs directory exists
    local logs_dir="$PROJECT_ROOT/logs"
    if [[ -d "$logs_dir" ]]; then
        echo "### Storage Overview" >> "$PROJECT_CONTEXT_FILE"
        echo "" >> "$PROJECT_CONTEXT_FILE"

        # Count raw entries
        local raw_count
        raw_count=$(find "$logs_dir/raw" -name "*.md" 2>/dev/null | wc -l | tr -d ' ' || echo "0")
        echo "- **Raw entries:** $raw_count markdown files" >> "$PROJECT_CONTEXT_FILE"

        # Count parsed entries
        local parsed_count
        parsed_count=$(find "$logs_dir/parsed" -name "*.json" 2>/dev/null | wc -l | tr -d ' ' || echo "0")
        echo "- **Parsed entries:** $parsed_count JSON files" >> "$PROJECT_CONTEXT_FILE"

        # Get date range
        local earliest_file latest_file earliest_date latest_date
        earliest_file=$(find "$logs_dir/raw" -name "*.md" 2>/dev/null | sort | head -1 || true)
        latest_file=$(find "$logs_dir/raw" -name "*.md" 2>/dev/null | sort | tail -1 || true)
        if [[ -n "$earliest_file" ]]; then
            earliest_date=$(basename "$earliest_file" .md)
        else
            earliest_date="unknown"
        fi
        if [[ -n "$latest_file" ]]; then
            latest_date=$(basename "$latest_file" .md)
        else
            latest_date="unknown"
        fi
        echo "- **Date range:** $earliest_date to $latest_date" >> "$PROJECT_CONTEXT_FILE"
        echo "" >> "$PROJECT_CONTEXT_FILE"

        # Sample recent entries to understand content
        echo "### Sample Recent Entry Titles" >> "$PROJECT_CONTEXT_FILE"
        echo "" >> "$PROJECT_CONTEXT_FILE"
        local recent_raw
        recent_raw=$(find "$logs_dir/raw" -name "*.md" 2>/dev/null | sort -r | head -5 || true)
        for raw_file in $recent_raw; do
            if [[ -f "$raw_file" ]]; then
                local entry_date
                entry_date=$(basename "$raw_file" .md)
                # Get first few lines as preview
                local preview
                preview=$(head -5 "$raw_file" | tr '\n' ' ' | cut -c1-100)
                echo "- **$entry_date**: $preview..." >> "$PROJECT_CONTEXT_FILE"
            fi
        done
    else
        echo "_No logs directory found. Storage appears empty._" >> "$PROJECT_CONTEXT_FILE"
    fi
    echo "" >> "$PROJECT_CONTEXT_FILE"
    echo "---" >> "$PROJECT_CONTEXT_FILE"
    echo "" >> "$PROJECT_CONTEXT_FILE"

    # -----------------------------------------------------
    # Section 7: Dogfooding Focus Areas
    # -----------------------------------------------------
    log_info "  [7/7] Adding dogfooding focus areas..."

    cat >> "$PROJECT_CONTEXT_FILE" << 'FOCUS_SECTION'
## 7. Dogfooding Focus Areas

When generating queries and reviewing feedback, pay special attention to:

### Query Generation Guidelines

1. **Test Recent Fixes**: Generate queries that specifically test the patterns that were supposedly fixed
2. **Edge Cases**: Include queries with:
   - Mixed languages (Korean + English)
   - Vague temporal references ("recently", "a while ago")
   - Goal statements that could be LOG or QUERY
   - Multi-part questions
   - References to specific exercises
   - Estimation requests (1RM, progress tracking)
3. **Realistic Usage**: Generate queries that a real fitness enthusiast would ask
4. **Failure Modes**: Include queries that might expose weaknesses:
   - Queries about data that doesn't exist
   - Very specific date ranges
   - Complex analytical questions

### Feedback Review Guidelines

When reviewing a response, consider:

1. **Did the Router classify correctly?** (LOG vs QUERY vs BOTH)
2. **Did the Planner choose appropriate retrieval strategies?**
3. **Did the Retriever find relevant entries?** (Check entries_found count)
4. **Did the Analyzer assess sufficiency correctly?** (Check verdict)
5. **Is the response accurate given the retrieved data?**
6. **Is the response helpful and actionable?**
7. **Does the response language match the query language?**
8. **For temporal queries: Does it account for recency?**
9. **For estimation queries: Does it attempt indirect estimation when direct data is missing?**

### Sentiment Guidelines

- **Positive**: Response answered the question well, retrieved appropriate data, provided actionable insights
- **Mixed**: Partially helpful but has room for improvement (wrong strategy, missing context, etc.)
- **Negative**: Failed to answer, wrong classification, hallucinated data, or major issues

---

FOCUS_SECTION

    # Add timestamp
    echo "_Context generated: $(date '+%Y-%m-%d %H:%M:%S')_" >> "$PROJECT_CONTEXT_FILE"

    local context_size
    context_size=$(wc -c < "$PROJECT_CONTEXT_FILE" | tr -d ' ')
    log_success "Project context built: $PROJECT_CONTEXT_FILE ($context_size bytes)"
}

# =============================================================================
# STEP 1: GENERATE TEST QUERIES (WITH FULL CONTEXT)
# =============================================================================

generate_queries() {
    if [[ "$SKIP_GENERATE" == "true" ]]; then
        if [[ ! -f "$QUERIES_FILE" ]]; then
            log_error "No queries file found at $QUERIES_FILE"
            exit 1
        fi
        log_info "Skipping query generation, using existing file"
        return
    fi

    log_section "GENERATING TEST QUERIES"
    log_info "Generating $NUM_QUERIES test queries with full project context..."

    # Read the project context
    local project_context
    project_context=$(cat "$PROJECT_CONTEXT_FILE")

    local prompt="You are a QA engineer dogfooding Swealog, a fitness logging AI assistant built on the Quilto framework.

## PROJECT CONTEXT

$project_context

---

## YOUR TASK

Generate exactly $NUM_QUERIES test queries that a real user might ask this fitness logging app.

### Guidelines

- **Be a real user**: Think like someone who actually logs workouts and wants insights
- **Be diverse**: Cover different intents (logging, querying, analysis, recommendations)
- **Be natural**: Use natural language as real users would, including typos, incomplete sentences, or ambiguous phrasing
- **Mix languages**: Some Korean, some English, some mixed (as a bilingual user would)
- **Explore edges**: Include queries that might challenge the system in unexpected ways
- **Don't repeat patterns**: Each query should test something meaningfully different

You decide what queries will best evaluate this system. Don't follow a formula - use your judgment as a QA engineer to find potential weaknesses.

### Output Format

Output ONLY the queries, one per line. No numbering, no explanations, no categories."

    claude -p "$prompt" --output-format text > "$QUERIES_FILE"

    local count
    count=$(wc -l < "$QUERIES_FILE" | tr -d ' ')
    log_success "Generated $count queries -> $QUERIES_FILE"

    # Show a preview
    log_info "Query preview:"
    head -5 "$QUERIES_FILE" | while read -r line; do
        echo "    $line"
    done
    echo "    ..."
}

# =============================================================================
# STEP 2: RUN QUERIES THROUGH SWEALOG
# =============================================================================

run_queries() {
    if [[ "$SKIP_RUN" == "true" ]]; then
        log_info "Skipping query execution, reviewing existing feedback files"
        return
    fi

    if [[ ! -f "$QUERIES_FILE" ]]; then
        log_error "No queries file found at $QUERIES_FILE"
        exit 1
    fi

    log_section "RUNNING QUERIES"
    log_info "Running queries through swealog auto..."

    mkdir -p "$FEEDBACK_DIR"

    local total
    total=$(wc -l < "$QUERIES_FILE" | tr -d ' ')
    local count=0

    while IFS= read -r query || [[ -n "$query" ]]; do
        # Skip empty lines
        [[ -z "$query" ]] && continue

        ((count++))
        log_info "[$count/$total] Running: ${query:0:60}..."

        # Run swealog auto with debug mode and non-interactive flag
        # This creates JSON files in tests/eval/feedback/active/
        # --non-interactive skips the feedback prompt (to be filled by auto-review)
        if ! uv run swealog run "$query" --debug --non-interactive --config "$LLM_CONFIG" --storage ./logs 2>/dev/null; then
            log_warn "Query failed: $query"
        fi

        # Small delay to avoid rate limiting
        sleep 1

    done < "$QUERIES_FILE"

    log_success "Executed $count queries"
}

# =============================================================================
# STEP 3: REVIEW AND FILL FEEDBACK (WITH FULL CONTEXT)
# =============================================================================

review_feedback() {
    log_section "REVIEWING FEEDBACK"
    log_info "Reviewing feedback files with Claude (direct edit mode)..."

    local files
    files=$(find "$FEEDBACK_DIR" -name "*.json" -type f 2>/dev/null || true)

    if [[ -z "$files" ]]; then
        log_warn "No feedback files found in $FEEDBACK_DIR"
        return
    fi

    # Read the project context once
    local project_context
    project_context=$(cat "$PROJECT_CONTEXT_FILE")

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

        # Create comprehensive review prompt - Claude will read and edit the file directly
        local review_prompt="You are an expert QA engineer evaluating a fitness AI assistant's response.

## PROJECT CONTEXT (CRITICAL - READ THIS FIRST)

$project_context

---

## YOUR TASK

1. Read the feedback file at: $json_file
2. Analyze the query, intermediate_outputs, and final_response
3. Evaluate the response quality using these criteria:
   - Classification Correctness: Did Router correctly identify LOG vs QUERY vs BOTH?
   - Retrieval Strategy: Did Planner choose appropriate strategies?
   - Data Retrieval: Did Retriever find relevant entries?
   - Analysis Quality: Did Analyzer correctly assess sufficiency?
   - Response Quality: Is the final response accurate, helpful, and actionable?
   - Language Match: Does response language match query language?
   - Temporal Awareness: For time-related queries, does it account for recency?
   - Known Pattern Check: Does this exhibit patterns from previous iterations?

4. Edit the file to add these three fields:
   - \"user_feedback\": Your detailed feedback (2-4 sentences, be specific about what worked or failed)
   - \"feedback_sentiment\": One of \"positive\", \"mixed\", or \"negative\"
   - \"issues_found\": Array of specific issue strings (empty array [] if none)

## SENTIMENT GUIDELINES
- **positive**: Response was helpful, agents worked correctly, no significant issues
- **mixed**: Partially helpful but has specific issues (wrong strategy, missing context, etc.)
- **negative**: Major failure - wrong classification, hallucinated data, or broke expected behavior

## IMPORTANT
- Be critical but fair
- Note any regression from supposedly fixed patterns
- If the response is genuinely good, say so clearly
- DO NOT output anything except reading and editing the file"

        # Let Claude directly read and edit the file
        if ! claude -p "$review_prompt" --allowedTools "Read,Edit" 2>/dev/null; then
            log_warn "Failed to review $filename"
            continue
        fi

        # Check what sentiment was assigned and display result
        local sentiment
        sentiment=$(jq -r '.feedback_sentiment // "unknown"' "$json_file")
        local feedback
        feedback=$(jq -r '.user_feedback // ""' "$json_file")

        case "$sentiment" in
            positive)
                log_success "Updated $filename: [POSITIVE] ${feedback:0:80}..."
                ;;
            mixed)
                log_warn "Updated $filename: [MIXED] ${feedback:0:80}..."
                ;;
            negative)
                log_error "Updated $filename: [NEGATIVE] ${feedback:0:80}..."
                ;;
            *)
                log_warn "Updated $filename: [UNKNOWN] Review may have failed"
                ;;
        esac

        # Small delay between API calls
        sleep 1

    done

    log_success "Reviewed $count files"
}

# =============================================================================
# STEP 4: GENERATE SUMMARY REPORT
# =============================================================================

generate_summary() {
    log_section "GENERATING SUMMARY"

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

    # Collect all issues for pattern analysis
    local all_issues=""

    for json_file in $files; do
        local sentiment
        sentiment=$(jq -r '.feedback_sentiment // "none"' "$json_file")

        # Collect issues
        local file_issues
        file_issues=$(jq -r '.issues_found[]? // empty' "$json_file" 2>/dev/null)
        if [[ -n "$file_issues" ]]; then
            all_issues="$all_issues$file_issues"$'\n'
        fi

        case "$sentiment" in
            positive) ((positive++)) ;;
            mixed) ((mixed++)) ;;
            negative) ((negative++)) ;;
            *) ((no_feedback++)) ;;
        esac
    done

    echo ""
    echo "╔═══════════════════════════════════════════════════════════╗"
    echo "║           AUTO-DOGFOOD SUMMARY                            ║"
    echo "╠═══════════════════════════════════════════════════════════╣"
    printf "║  Total records:     %3d                                   ║\n" "$total"
    printf "║  ✅ Positive:       %3d (%2d%%)                            ║\n" "$positive" $((positive * 100 / total))
    printf "║  ⚠️  Mixed:          %3d (%2d%%)                            ║\n" "$mixed" $((mixed * 100 / total))
    printf "║  ❌ Negative:       %3d (%2d%%)                            ║\n" "$negative" $((negative * 100 / total))
    if [[ $no_feedback -gt 0 ]]; then
        printf "║  ⏳ No feedback:    %3d                                   ║\n" "$no_feedback"
    fi
    echo "╚═══════════════════════════════════════════════════════════╝"
    echo ""

    # Show common issues if any
    if [[ -n "$all_issues" ]]; then
        echo "Common issues found:"
        echo "$all_issues" | sort | uniq -c | sort -rn | head -10 | while read -r count issue; do
            if [[ -n "$issue" ]]; then
                echo "  - ($count) $issue"
            fi
        done
        echo ""
    fi

    echo "Files:"
    echo "  - Feedback:        $FEEDBACK_DIR"
    echo "  - Project context: $PROJECT_CONTEXT_FILE"
    echo "  - Queries:         $QUERIES_FILE"
    echo ""
    echo "Next steps:"
    echo "  1. Review feedback files in $FEEDBACK_DIR"
    echo "  2. Run analysis story to identify patterns and generate Epic N+1 stories"
    echo "  3. Archive iteration when analysis is complete"
}

# =============================================================================
# MAIN
# =============================================================================

main() {
    echo ""
    log_section "AUTO-DOGFOOD SCRIPT (Full Context Mode)"
    log_info "Project: $PROJECT_ROOT"
    log_info "Config: $LLM_CONFIG"
    log_info "Queries: $NUM_QUERIES"
    echo ""

    check_dependencies

    # Change to project root
    cd "$PROJECT_ROOT"

    # Run steps
    gather_project_context
    generate_queries
    run_queries
    review_feedback
    generate_summary

    log_success "Auto-dogfood complete!"
}

main "$@"
