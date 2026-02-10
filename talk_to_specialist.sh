#!/usr/bin/env bash
# talk_to_specialist.sh — Wrapper for specialist (claude -p) communication
# Handles: session persistence, JSON logging to labestia_queue, thinking block cleanup,
#          auto-recovery from corrupted sessions, consecutive failure tracking
# Usage: ./talk_to_specialist.sh "message"   or   echo "message" | ./talk_to_specialist.sh
# Exit codes: 0=ok, 1=rate limit/empty, 2=timeout, 3=other error, 4=too many consecutive failures

set -euo pipefail

WORKDIR="/home/angel/invest_value_manager_gobernator"
SPECIALIST_DIR="$WORKDIR/invest_value_manager"
STATE_DIR="$WORKDIR/state"
SESSION_FILE="$STATE_DIR/specialist_session.txt"
QUEUE_FILE="$STATE_DIR/labestia_queue.jsonl"
FAILURE_FILE="$STATE_DIR/specialist_failures"
TIMEOUT=3600
MAX_CONSECUTIVE_FAILURES=3
LOCK_FILE="$STATE_DIR/specialist.lock"

# --- Exclusive lock: only one specialist invocation at a time ---
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
mkdir -p "$STATE_DIR"
COOLDOWN_MINUTES=30
FAILURES=0
if [ -f "$FAILURE_FILE" ]; then
    FAILURES=$(cat "$FAILURE_FILE" 2>/dev/null || echo 0)
    if ! [[ "$FAILURES" =~ ^[0-9]+$ ]]; then
        FAILURES=0
    fi
fi

if [ "$FAILURES" -ge "$MAX_CONSECUTIVE_FAILURES" ]; then
    # Check if cooldown period has passed since last failure
    LAST_MOD=$(stat -c %Y "$FAILURE_FILE" 2>/dev/null || echo 0)
    NOW=$(date +%s)
    ELAPSED=$(( (NOW - LAST_MOD) / 60 ))
    if [ "$ELAPSED" -ge "$COOLDOWN_MINUTES" ]; then
        # Cooldown passed — auto-reset and retry
        FAILURES=0
        echo 0 > "$FAILURE_FILE"
        log_to_queue "system" "Auto-reset after ${COOLDOWN_MINUTES}min cooldown. Retrying specialist..."
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

# --- Log to queue ---
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
" "$from" "$text" >> "$QUEUE_FILE"
}

# Log gobernator message immediately (dedup handled by flock + failure counter)
log_to_queue "gobernator" "$MESSAGE"

# --- Temp files ---
TMPOUT=$(mktemp)
TMPERR=$(mktemp)
trap 'rm -f "$TMPOUT" "$TMPERR"' EXIT

# --- Kill leftover specialist processes (NOT gobernator) ---
# Specialist always runs via "timeout 300 claude -p", gobernator does not use timeout
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

# timeout returns 124 on timeout, 137 on SIGKILL
if [ "$RC" -eq 124 ]; then
    FAILURES=$((FAILURES + 1))
    echo "$FAILURES" > "$FAILURE_FILE"
    log_to_queue "system" "TIMEOUT: specialist did not respond in ${TIMEOUT}s (failures: $FAILURES/$MAX_CONSECUTIVE_FAILURES)"
    echo "Specialist timeout (${TIMEOUT}s)" >&2
    exit 2
fi

# --- Clean thinking blocks ---
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

# --- Check for empty/rate-limited response ---
if [ -z "$CLEANED" ]; then
    FAILURES=$((FAILURES + 1))
    echo "$FAILURES" > "$FAILURE_FILE"
    log_to_queue "system" "EMPTY: specialist returned no output (rc=$RC, failures: $FAILURES/$MAX_CONSECUTIVE_FAILURES)"
    echo "Specialist returned empty response" >&2
    exit 1
fi

# --- Check for runtime crashes (Bun, Node, etc.) ---
# These are garbage output, not real specialist responses
if echo "$CLEANED" | grep -qE "TypeError:.*CommonJS|SyntaxError:|ReferenceError:|bug in Bun|node:internal|FATAL ERROR|segmentation fault|panic:"; then
    FAILURES=$((FAILURES + 1))
    echo "$FAILURES" > "$FAILURE_FILE"
    # Session is likely corrupted after a crash — reset it
    create_new_session
    CRASH_PREVIEW=$(echo "$CLEANED" | head -3 | tr '\n' ' ')
    log_to_queue "system" "CRASH: runtime error detected, session reset (failures: $FAILURES/$MAX_CONSECUTIVE_FAILURES). Preview: $CRASH_PREVIEW"
    echo "Specialist crashed: $CRASH_PREVIEW" >&2
    exit 3
fi

LOWER=$(echo "$CLEANED" | tr '[:upper:]' '[:lower:]')
if echo "$LOWER" | grep -q "out of extra usage\|you've exceeded\|rate_limit_error\|overloaded_error\|server is overloaded"; then
    FAILURES=$((FAILURES + 1))
    echo "$FAILURES" > "$FAILURE_FILE"
    log_to_queue "system" "RATE_LIMIT: $CLEANED (failures: $FAILURES/$MAX_CONSECUTIVE_FAILURES)"
    echo "$CLEANED" >&2
    exit 1
fi

# --- Success: reset failure counter ---
echo 0 > "$FAILURE_FILE"

# --- Log specialist response on success ---
log_to_queue "especialista" "$CLEANED"
echo "$CLEANED"
exit 0
