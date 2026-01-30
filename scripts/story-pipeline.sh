#!/bin/bash
# story-pipeline.sh - Automates the full BMAD story workflow
# Usage: ./scripts/story-pipeline.sh [story-id] [options]
# Example: ./scripts/story-pipeline.sh                      # Auto-discover next backlog story
# Example: ./scripts/story-pipeline.sh 1-2-user-auth        # Specific story
# Example: ./scripts/story-pipeline.sh 1-2-user-auth -s 2   # Start from step 2
# Example: ./scripts/story-pipeline.sh 1-2-user-auth -s 1 -e 2  # Run steps 1-2 only
# Example: ./scripts/story-pipeline.sh --with-tests         # Include test generation
#
# BMAD Method v6.0 - Updated for skill-based workflow invocation
# Note: Validation is now built into create-story workflow (step 6 runs checklist validation)

set -e  # Exit on first error

STORY=""
START_STEP=1
END_STEP=99  # Default to run all steps
WITH_TESTS=false
DRY_RUN=false
SPRINT_STATUS="_bmad-output/implementation-artifacts/sprint-status.yaml"

# Execute or preview command
run_claude() {
    if [ "$DRY_RUN" = true ]; then
        echo "[DRY-RUN] claude -p \"$1\""
    else
        claude -p "$1"
    fi
}

# Logging helper
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --step|-s)
            START_STEP="$2"
            shift 2
            ;;
        --end|-e)
            END_STEP="$2"
            shift 2
            ;;
        --with-tests|-t)
            WITH_TESTS=true
            shift
            ;;
        --dry-run|-n)
            DRY_RUN=true
            shift
            ;;
        --help|-h)
            echo "Usage: $0 [story-id] [options]"
            echo ""
            echo "Arguments:"
            echo "  story-id              Optional. If omitted, auto-discovers next backlog story"
            echo ""
            echo "Options:"
            echo "  -s, --step N          Start from step N (default: 1)"
            echo "  -e, --end N           End at step N (default: all)"
            echo "  -t, --with-tests      Include test generation after implementation"
            echo "  -n, --dry-run         Preview commands without executing"
            echo "  -h, --help            Show this help message"
            echo ""
            echo "Steps:"
            echo "  1: Create story (includes validation)"
            echo "  2: Implement story (dev-story)"
            echo "  3: Code review + commit"
            echo "  4: Generate tests (only with --with-tests)"
            exit 0
            ;;
        -*)
            echo "ERROR: Unknown option: $1"
            echo "Use --help for usage information."
            exit 1
            ;;
        *)
            if [ -z "$STORY" ]; then
                STORY="$1"
            else
                echo "ERROR: Unexpected argument: $1"
                echo "Story ID already set to: $STORY"
                exit 1
            fi
            shift
            ;;
    esac
done

# Pre-flight check: Verify sprint-status.yaml exists for auto-discovery
if [ -z "$STORY" ]; then
    if [ ! -f "$SPRINT_STATUS" ]; then
        echo "ERROR: No story specified and sprint-status.yaml not found."
        echo ""
        echo "Options:"
        echo "  1. Run '/bmad-bmm-sprint-planning' to initialize sprint tracking"
        echo "  2. Specify a story ID: $0 1-2-user-auth"
        exit 1
    fi
    log "No story specified - will auto-discover next backlog story from sprint-status.yaml"
fi

# Determine total steps
TOTAL_STEPS=3
if [ "$WITH_TESTS" = true ]; then
    TOTAL_STEPS=4
fi

echo "========================================"
log "Starting story pipeline"
if [ -n "$STORY" ]; then
    echo "Story: $STORY"
else
    echo "Story: (auto-discover)"
fi
if [ "$START_STEP" -gt 1 ] || [ "$END_STEP" -lt "$TOTAL_STEPS" ]; then
    echo "Running steps $START_STEP-$END_STEP"
fi
if [ "$WITH_TESTS" = true ]; then
    echo "Test generation: enabled"
fi
if [ "$DRY_RUN" = true ]; then
    echo "Mode: DRY-RUN (no commands will be executed)"
fi
echo "========================================"

# Build story argument (empty string triggers auto-discovery in create-story)
STORY_ARG=""
if [ -n "$STORY" ]; then
    STORY_ARG="$STORY"
fi

# Step 1: Create Story (validation is now built-in)
if [ "$START_STEP" -le 1 ] && [ "$END_STEP" -ge 1 ]; then
    echo ""
    log "Step 1/$TOTAL_STEPS: Creating story (with built-in validation)..."
    echo "----------------------------------------"
    run_claude "/bmad-bmm-create-story $STORY_ARG - auto-proceed without asking, select YOLO [y] if prompted"
fi

# Step 2: Dev Story
if [ "$START_STEP" -le 2 ] && [ "$END_STEP" -ge 2 ]; then
    echo ""
    log "Step 2/$TOTAL_STEPS: Implementing story..."
    echo "----------------------------------------"
    if [ -n "$STORY_ARG" ]; then
        run_claude "/bmad-bmm-dev-story $STORY_ARG - auto-proceed without asking, select YOLO [y] if prompted"
    else
        # For auto-discovered stories, dev-story will find the ready-for-dev story
        run_claude "/bmad-bmm-dev-story - auto-proceed without asking, select YOLO [y] if prompted"
    fi
fi

# Step 3: Code Review
if [ "$START_STEP" -le 3 ] && [ "$END_STEP" -ge 3 ]; then
    echo ""
    log "Step 3/$TOTAL_STEPS: Code review and commit..."
    echo "----------------------------------------"
    if [ -n "$STORY_ARG" ]; then
        run_claude "/bmad-bmm-code-review $STORY_ARG - auto-proceed, apply all fixes, update sprint status, commit. Select YOLO [y] if prompted"
    else
        run_claude "/bmad-bmm-code-review - auto-proceed, apply all fixes, update sprint status, commit. Select YOLO [y] if prompted"
    fi
fi

# Step 4: Test Generation (optional)
if [ "$WITH_TESTS" = true ] && [ "$START_STEP" -le 4 ] && [ "$END_STEP" -ge 4 ]; then
    echo ""
    log "Step 4/$TOTAL_STEPS: Generating guardrail tests..."
    echo "----------------------------------------"
    if [ -n "$STORY_ARG" ]; then
        run_claude "/bmad-tea-testarch-automate $STORY_ARG - auto-proceed without asking"
    else
        run_claude "/bmad-tea-testarch-automate - auto-proceed without asking"
    fi
fi

echo ""
echo "========================================"
log "Story pipeline complete!"
echo "========================================"
