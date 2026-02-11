#!/usr/bin/env bash
# talk_to_specialist.sh — Wrapper for specialist (claude -p) communication
# Deterministic: EVERY outgoing message gets a response OR an error logged. No ghosts.
# Handles: session persistence, JSON logging, thinking block cleanup,
#          auto-recovery from corrupted sessions, consecutive failure tracking
# Usage: ./talk_to_specialist.sh "message"   or   echo "message" | ./talk_to_specialist.sh
# Exit codes: 0=ok, 1=rate limit/empty, 2=timeout, 3=other error, 4=blocked/lock

set -uo pipefail
# NOTE: no -e (errexit) — we handle errors explicitly for deterministic logging

WORKDIR="/home/angel/invest_value_manager_gobernator"
SPECIALIST_DIR="$WORKDIR/invest_value_manager"
STATE_DIR="$WORKDIR/state"
SESSION_FILE="$STATE_DIR/specialist_session.txt"
QUEUE_FILE="$STATE_DIR/labestia_queue.jsonl"
FAILURE_FILE="$STATE_DIR/specialist_failures"
CALLING_FILE="$STATE_DIR/specialist_calling"
TIMEOUT=1800  # 30 minutes — complex tasks with multiple tools need time
MAX_CONSECUTIVE_FAILURES=3
LOCK_FILE="$STATE_DIR/specialist.lock"
COOLDOWN_MINUTES=30

# --- State tracking for deterministic cleanup ---
CALL_LOGGED=false    # true once outgoing message is logged to queue
CALL_RESULT=""       # set to non-empty once a result is logged (success/error)
TMPOUT=""
TMPERR=""

# --- Log to queue (fire-and-forget, never fails the script) ---
log_to_queue() {
    local from="$1" text="$2"
    python3 -c "
import json, sys, datetime
entry = {
    'from': sys.argv[1],
    'text': sys.argv[2],
    'ts': datetime.datetime.now(datetime.timezone.utc).isoformat()
}
print(json.dumps(entry, ensure_ascii=False))
" "$from" "$text" >> "$QUEUE_FILE" 2>/dev/null || true
}

# --- Cleanup trap: GUARANTEES a result is logged for every outgoing message ---
cleanup() {
    local exit_code=${1:-$?}

    # If we logged an outgoing message but never logged a result → log error
    if [ "$CALL_LOGGED" = true ] && [ -z "$CALL_RESULT" ]; then
        log_to_queue "system" "KILLED: specialist call interrupted before completion (exit=$exit_code)"
        # Count as failure
        local failures
        failures=$(cat "$FAILURE_FILE" 2>/dev/null || echo 0)
        [[ "$failures" =~ ^[0-9]+$ ]] || failures=0
        failures=$((failures + 1))
        echo "$failures" > "$FAILURE_FILE" 2>/dev/null || true
    fi

    # Remove calling state file
    rm -f "$CALLING_FILE" 2>/dev/null

    # Remove temp files
    rm -f "$TMPOUT" "$TMPERR" 2>/dev/null

    exit "$exit_code"
}

# Trap ALL catchable signals + normal exit
trap 'cleanup $?' EXIT
trap 'cleanup 130' INT
trap 'cleanup 143' TERM
trap 'cleanup 131' HUP

# --- Exclusive lock: only one specialist invocation at a time ---
mkdir -p "$STATE_DIR"
exec 9>"$LOCK_FILE"
if ! flock -n 9; then
    echo "Another specialist invocation is already running" >&2
    exit 4
fi

# --- Read message from arg or stdin ---
if [ $# -ge 1 ]; then
    MESSAGE="$1"
elif [ ! -t 0 ]; then
    MESSAGE=$(cat)
else
    echo "Usage: $0 \"message\" or echo \"message\" | $0" >&2
    exit 3
fi

if [ -z "$MESSAGE" ]; then
    echo "Empty message" >&2
    exit 3
fi

# --- Consecutive failure check with auto-cooldown ---
FAILURES=0
if [ -f "$FAILURE_FILE" ]; then
    FAILURES=$(cat "$FAILURE_FILE" 2>/dev/null || echo 0)
    if ! [[ "$FAILURES" =~ ^[0-9]+$ ]]; then
        FAILURES=0
    fi
fi

if [ "$FAILURES" -ge "$MAX_CONSECUTIVE_FAILURES" ]; then
    LAST_MOD=$(stat -c %Y "$FAILURE_FILE" 2>/dev/null || echo 0)
    NOW=$(date +%s)
    ELAPSED=$(( (NOW - LAST_MOD) / 60 ))
    if [ "$ELAPSED" -ge "$COOLDOWN_MINUTES" ]; then
        FAILURES=0
        echo 0 > "$FAILURE_FILE"
        log_to_queue "system" "Auto-reset after ${COOLDOWN_MINUTES}min cooldown. Retrying..."
    else
        REMAINING=$(( COOLDOWN_MINUTES - ELAPSED ))
        echo "BLOCKED: $FAILURES consecutive failures. Auto-retry in ${REMAINING}min." >&2
        exit 4
    fi
fi

# --- Session helpers ---
read_session() {
    if [ -f "$SESSION_FILE" ]; then
        SESSION_ID=$(head -1 "$SESSION_FILE")
        SESSION_STARTED=$(sed -n '2p' "$SESSION_FILE" 2>/dev/null || echo "no")
    else
        create_new_session
    fi
}

create_new_session() {
    SESSION_ID=$(python3 -c "import uuid; print(uuid.uuid4())")
    SESSION_STARTED="no"
    printf '%s\n%s\n' "$SESSION_ID" "$SESSION_STARTED" > "$SESSION_FILE"
}

read_session

# --- Log outgoing message + mark calling state ---
log_to_queue "gobernator" "$MESSAGE"
CALL_LOGGED=true
echo "$$:$(date +%s)" > "$CALLING_FILE"

# --- Temp files ---
TMPOUT=$(mktemp)
TMPERR=$(mktemp)

# --- Kill leftover specialist processes from previous stale runs ---
pkill -9 -f "timeout $TIMEOUT claude -p" 2>/dev/null || true

# --- Build and run specialist command ---
run_once() {
    local CMD=(claude -p --permission-mode bypassPermissions)
    if [ "$SESSION_STARTED" = "started" ]; then
        CMD+=(--resume "$SESSION_ID")
    else
        CMD+=(--session-id "$SESSION_ID")
        printf '%s\n%s\n' "$SESSION_ID" "started" > "$SESSION_FILE"
    fi

    local RC=0
    # CRITICAL: run from specialist directory so it reads ITS CLAUDE.md, not gobernator's
    cd "$SPECIALIST_DIR"
    timeout "$TIMEOUT" "${CMD[@]}" "$MESSAGE" > "$TMPOUT" 2> "$TMPERR" < /dev/null || RC=$?
    cd "$WORKDIR"
    echo "$RC"
}

RC=$(run_once)

# --- Auto-recovery: if --resume failed, create new session and retry ---
if grep -q "resume requires a valid session" "$TMPERR" 2>/dev/null; then
    log_to_queue "system" "Session corrupted, creating new session and retrying..."
    create_new_session
    RC=$(run_once)
fi

# --- Process result: EVERY path sets CALL_RESULT (deterministic) ---

# Timeout (exit code 124 from timeout command)
if [ "$RC" -eq 124 ]; then
    FAILURES=$((FAILURES + 1))
    echo "$FAILURES" > "$FAILURE_FILE"
    log_to_queue "system" "TIMEOUT: specialist did not respond in ${TIMEOUT}s (failures: $FAILURES/$MAX_CONSECUTIVE_FAILURES)"
    CALL_RESULT="timeout"
    echo "Specialist timeout (${TIMEOUT}s)" >&2
    exit 2
fi

# Clean thinking blocks
RAW=$(cat "$TMPOUT")
if [ -z "$RAW" ]; then
    RAW=$(cat "$TMPERR")
fi

CLEANED=$(python3 -c "
import re, sys
text = sys.stdin.read()
text = re.sub(r'<thinking>.*?</thinking>', '', text, flags=re.DOTALL)
print(text.strip())
" <<< "$RAW")

# Empty response
if [ -z "$CLEANED" ]; then
    FAILURES=$((FAILURES + 1))
    echo "$FAILURES" > "$FAILURE_FILE"
    log_to_queue "system" "EMPTY: specialist returned no output (rc=$RC, failures: $FAILURES/$MAX_CONSECUTIVE_FAILURES)"
    CALL_RESULT="empty"
    echo "Specialist returned empty response" >&2
    exit 1
fi

# Runtime crash detection
if echo "$CLEANED" | grep -qE "TypeError:.*CommonJS|SyntaxError:|ReferenceError:|bug in Bun|node:internal|FATAL ERROR|segmentation fault|panic:"; then
    FAILURES=$((FAILURES + 1))
    echo "$FAILURES" > "$FAILURE_FILE"
    create_new_session
    CRASH_PREVIEW=$(echo "$CLEANED" | head -3 | tr '\n' ' ')
    log_to_queue "system" "CRASH: runtime error detected, session reset (failures: $FAILURES/$MAX_CONSECUTIVE_FAILURES). Preview: $CRASH_PREVIEW"
    CALL_RESULT="crash"
    echo "Specialist crashed: $CRASH_PREVIEW" >&2
    exit 3
fi

# Rate limit detection
LOWER=$(echo "$CLEANED" | tr '[:upper:]' '[:lower:]')
if echo "$LOWER" | grep -q "out of extra usage\|you've exceeded\|rate_limit_error\|overloaded_error\|server is overloaded"; then
    FAILURES=$((FAILURES + 1))
    echo "$FAILURES" > "$FAILURE_FILE"
    log_to_queue "system" "RATE_LIMIT: $CLEANED (failures: $FAILURES/$MAX_CONSECUTIVE_FAILURES)"
    CALL_RESULT="rate_limit"
    echo "$CLEANED" >&2
    exit 1
fi

# --- Success ---
echo 0 > "$FAILURE_FILE"
log_to_queue "especialista" "$CLEANED"
CALL_RESULT="success"
echo "$CLEANED"
exit 0
