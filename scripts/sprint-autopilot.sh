#!/bin/bash
# sprint-autopilot.sh - Autonomous sprint execution with Claude as supervisor
# Usage: ./scripts/sprint-autopilot.sh [options]
#
# Loops through all backlog stories, executing each via story-pipeline.sh
# Claude analyzes results and decides next action after each story.
#
# BMAD Method v6.0

set -e

SPRINT_STATUS="_bmad-output/implementation-artifacts/sprint-status.yaml"
STORY_DIR="_bmad-output/implementation-artifacts"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PIPELINE_SCRIPT="$SCRIPT_DIR/story-pipeline.sh"
LOG_FILE="_bmad-output/sprint-autopilot.log"
DRY_RUN=false
WITH_TESTS=false
MAX_STORIES=0  # 0 = unlimited
RESUME_STORY=""  # Story ID to resume from
EPIC_FILTER=""   # Filter to specific epic

# Logging helper
log() {
    local msg="[$(date '+%Y-%m-%d %H:%M:%S')] $1"
    echo "$msg"
    echo "$msg" >> "$LOG_FILE"
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --dry-run|-n)
            DRY_RUN=true
            shift
            ;;
        --with-tests|-t)
            WITH_TESTS=true
            shift
            ;;
        --max|-m)
            MAX_STORIES="$2"
            shift 2
            ;;
        --resume|-r)
            RESUME_STORY="$2"
            shift 2
            ;;
        --epic|-E)
            EPIC_FILTER="$2"
            shift 2
            ;;
        --help|-h)
            echo "Usage: $0 [options]"
            echo ""
            echo "Autonomous sprint execution - processes stories until sprint complete."
            echo ""
            echo "Options:"
            echo "  -r, --resume STORY    Resume from specific story (Claude detects which step)"
            echo "  -E, --epic N          Only process stories from epic N"
            echo "  -n, --dry-run         Preview what would be executed"
            echo "  -t, --with-tests      Include test generation for each story"
            echo "  -m, --max N           Process at most N stories then stop (default: unlimited)"
            echo "  -h, --help            Show this help message"
            echo ""
            echo "The autopilot will:"
            echo "  1. Read sprint-status.yaml for backlog stories"
            echo "  2. For each story, Claude analyzes the story file to detect progress"
            echo "  3. Execute story-pipeline.sh starting from the right step"
            echo "  4. Ask Claude to analyze results and decide next action"
            echo "  5. Continue until all stories done or critical failure"
            echo ""
            echo "Resume mode (-r):"
            echo "  Claude analyzes story file AND git state to detect progress:"
            echo "  - Story done in sprint-status → skip (0)"
            echo "  - No story file, no code changes → create (1)"
            echo "  - No story file, but code changes exist → review (3)"
            echo "  - Story exists, tasks pending → dev (2)"
            echo "  - Story exists, uncommitted changes → review (3)"
            echo ""
            echo "Log file: $LOG_FILE"
            exit 0
            ;;
        *)
            echo "ERROR: Unknown option: $1"
            echo "Use --help for usage information."
            exit 1
            ;;
    esac
done

# Pre-flight checks
if [ ! -f "$SPRINT_STATUS" ]; then
    echo "ERROR: Sprint status file not found: $SPRINT_STATUS"
    echo "Run '/bmad-bmm-sprint-planning' first to initialize sprint tracking."
    exit 1
fi

if [ ! -f "$PIPELINE_SCRIPT" ]; then
    echo "ERROR: Pipeline script not found: $PIPELINE_SCRIPT"
    exit 1
fi

# Ensure log directory exists
mkdir -p "$(dirname "$LOG_FILE")"

# Build pipeline options
PIPELINE_OPTS=""
if [ "$WITH_TESTS" = true ]; then
    PIPELINE_OPTS="$PIPELINE_OPTS --with-tests"
fi

echo "========================================"
log "Sprint Autopilot Starting"
echo "Sprint status: $SPRINT_STATUS"
echo "Pipeline script: $PIPELINE_SCRIPT"
if [ -n "$RESUME_STORY" ]; then
    echo "Resume from: $RESUME_STORY"
fi
if [ -n "$EPIC_FILTER" ]; then
    echo "Epic filter: $EPIC_FILTER"
fi
if [ "$DRY_RUN" = true ]; then
    echo "Mode: DRY-RUN"
fi
if [ "$MAX_STORIES" -gt 0 ]; then
    echo "Max stories: $MAX_STORIES"
fi
echo "Log file: $LOG_FILE"
echo "========================================"
echo ""

STORIES_PROCESSED=0
STORIES_SUCCEEDED=0
STORIES_FAILED=0
FIRST_ITERATION=true

# Function to detect which step to start from for a story
detect_start_step() {
    local story_key="$1"
    local story_file="$STORY_DIR/story-${story_key}.md"

    if [ "$DRY_RUN" = true ]; then
        echo "1"
        return
    fi

    # Ask Claude to analyze story file AND code state to determine the step
    local step=$(claude -p "Analyze the story progress and determine which pipeline step to start from.

Story key: $story_key
Story file location: $story_file
Sprint status: $SPRINT_STATUS

Please check:
1. Read $SPRINT_STATUS to find this story's current status
2. Check if story file exists at $story_file (read it if so)
3. Run 'git status' and 'git diff --stat' to see uncommitted changes
4. Check for recent commits related to this story

Pipeline steps:
1 = Create story (story file doesn't exist)
2 = Dev story (story exists, but implementation not started or incomplete)
3 = Code review (code changes exist but not reviewed/committed)

Decision rules:
- If story status is 'done' in sprint-status → 0 (skip)
- If story file doesn't exist AND no related code changes → 1
- If story file doesn't exist BUT code changes exist → 3 (review existing work)
- If story exists with tasks 'pending' and no code changes → 2
- If story exists with tasks 'in-progress' or uncommitted changes → 3
- If uncertain, prefer step 3 (review) to avoid losing manual work

Respond with EXACTLY one number (0, 1, 2, or 3). Nothing else.")

    echo "$step"
}

# Main loop - let Claude orchestrate
while true; do
    DECISION=""
    RESUME_START_STEP=""

    # Check if we've hit the max stories limit
    if [ "$MAX_STORIES" -gt 0 ] && [ "$STORIES_PROCESSED" -ge "$MAX_STORIES" ]; then
        log "Reached max stories limit ($MAX_STORIES). Stopping."
        break
    fi

    # Handle resume story on first iteration
    if [ "$FIRST_ITERATION" = true ] && [ -n "$RESUME_STORY" ]; then
        FIRST_ITERATION=false
        log "Resuming from story: $RESUME_STORY"
        echo "----------------------------------------"

        START_STEP=$(detect_start_step "$RESUME_STORY")
        log "Detected start step: $START_STEP"

        if [ "$START_STEP" = "0" ]; then
            log "Story $RESUME_STORY is already done, continuing to next..."
        else
            DECISION="NEXT_STORY: $RESUME_STORY"
            # Store start step for use below
            RESUME_START_STEP="$START_STEP"
        fi

        if [ -z "$DECISION" ]; then
            # Fall through to normal discovery
            :
        else
            log "Claude decision: $DECISION (resume mode)"
        fi
    fi

    # Normal story discovery (if not resuming or resume story was done)
    if [ -z "$DECISION" ] || [ "$DECISION" = "" ]; then
        FIRST_ITERATION=false
        log "Asking Claude to check sprint status and determine next action..."
        echo "----------------------------------------"

        if [ "$DRY_RUN" = true ]; then
            echo "[DRY-RUN] claude -p \"Read $SPRINT_STATUS and determine next action...\""
            echo "[DRY-RUN] Would execute story pipeline for next backlog story"
            STORIES_PROCESSED=$((STORIES_PROCESSED + 1))

            if [ "$STORIES_PROCESSED" -ge 3 ]; then
                echo "[DRY-RUN] Simulating completion after 3 stories"
                break
            fi
            continue
        fi

        # Build epic filter clause if specified
        EPIC_CLAUSE=""
        if [ -n "$EPIC_FILTER" ]; then
            EPIC_CLAUSE="
IMPORTANT: Only consider stories from Epic $EPIC_FILTER (story keys starting with '$EPIC_FILTER-')."
        fi

        # Ask Claude to analyze sprint status and decide next action
        # Claude will output JSON-like response we can parse
        DECISION=$(claude -p "Read $SPRINT_STATUS file. Analyze the development_status section.

Your task: Determine what to do next.
$EPIC_CLAUSE
Rules:
1. Find stories with status 'backlog' or 'ready-for-dev' (in order, lowest epic-story number first)
2. If a 'ready-for-dev' story exists, that takes priority (continue implementation)
3. If only 'backlog' stories exist, pick the first one
4. If all stories are 'done', check if epic retrospective is needed
5. If everything is complete, we're done

Respond with EXACTLY one line in this format (no other text):
- NEXT_STORY: <story-key> (e.g., NEXT_STORY: 1-2-user-auth)
- RUN_RETROSPECTIVE: <epic-num> (e.g., RUN_RETROSPECTIVE: 1)
- SPRINT_COMPLETE: true
- ERROR: <message>

Just the one line, nothing else.")

        log "Claude decision: $DECISION"
        RESUME_START_STEP=""  # Clear any resume step
    fi

    log "Claude decision: $DECISION"

    # Parse Claude's decision
    if [[ "$DECISION" == NEXT_STORY:* ]]; then
        STORY_KEY=$(echo "$DECISION" | sed 's/NEXT_STORY: *//')
        log "Processing story: $STORY_KEY"

        # Detect start step (use resume step if available, otherwise detect)
        if [ -n "$RESUME_START_STEP" ]; then
            START_STEP="$RESUME_START_STEP"
            RESUME_START_STEP=""  # Clear for next iteration
        else
            START_STEP=$(detect_start_step "$STORY_KEY")
        fi

        if [ "$START_STEP" = "0" ]; then
            log "Story $STORY_KEY already done, skipping..."
            DECISION=""  # Clear for next iteration
            continue
        fi

        log "Starting from step $START_STEP"

        # Build pipeline command with start step
        PIPELINE_CMD="$PIPELINE_SCRIPT $STORY_KEY -s $START_STEP $PIPELINE_OPTS"

        # Run the story pipeline
        if $PIPELINE_CMD; then
            log "Story $STORY_KEY completed successfully"
            STORIES_SUCCEEDED=$((STORIES_SUCCEEDED + 1))
        else
            log "Story $STORY_KEY failed with exit code $?"
            STORIES_FAILED=$((STORIES_FAILED + 1))

            # Ask Claude what to do about the failure
            log "Asking Claude to analyze failure..."
            RECOVERY=$(claude -p "The story pipeline for '$STORY_KEY' just failed.

Check:
1. The story file in _bmad-output/implementation-artifacts/
2. Recent git status
3. Any error patterns

Respond with EXACTLY one line:
- RETRY: $STORY_KEY (try again)
- SKIP: $STORY_KEY (mark as blocked, move on)
- STOP: <reason> (critical failure, stop autopilot)

Just the one line, nothing else.")

            log "Recovery decision: $RECOVERY"

            if [[ "$RECOVERY" == RETRY:* ]]; then
                log "Retrying story..."
                continue
            elif [[ "$RECOVERY" == SKIP:* ]]; then
                log "Skipping story, moving to next..."
            elif [[ "$RECOVERY" == STOP:* ]]; then
                log "Critical failure - stopping autopilot"
                break
            fi
        fi

        STORIES_PROCESSED=$((STORIES_PROCESSED + 1))

    elif [[ "$DECISION" == RUN_RETROSPECTIVE:* ]]; then
        EPIC_NUM=$(echo "$DECISION" | sed 's/RUN_RETROSPECTIVE: *//')
        log "Running retrospective for Epic $EPIC_NUM"

        claude -p "/bmad-bmm-retrospective Epic $EPIC_NUM - auto-proceed without asking, select YOLO [y] if prompted"

    elif [[ "$DECISION" == SPRINT_COMPLETE:* ]]; then
        log "Sprint complete! All stories processed."
        break

    elif [[ "$DECISION" == ERROR:* ]]; then
        log "Error from Claude: $DECISION"
        break

    else
        log "Unexpected response from Claude: $DECISION"
        log "Stopping to avoid infinite loop."
        break
    fi

    # Clear decision for next iteration
    DECISION=""
    echo ""
done

echo ""
echo "========================================"
log "Sprint Autopilot Summary"
echo "Stories processed: $STORIES_PROCESSED"
echo "Succeeded: $STORIES_SUCCEEDED"
echo "Failed: $STORIES_FAILED"
echo "Log file: $LOG_FILE"
echo "========================================"
