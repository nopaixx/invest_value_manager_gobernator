#!/usr/bin/env bash
# talk_to_specialist.sh — Wrapper for specialist (claude -p) communication
# Handles: session persistence, JSON logging to labestia_queue, thinking block cleanup
# Usage: ./talk_to_specialist.sh "message"   or   echo "message" | ./talk_to_specialist.sh
# Exit codes: 0=ok, 1=rate limit/empty, 2=timeout, 3=other error

set -euo pipefail

WORKDIR="/home/angel/invest_value_manager_gobernator"
SPECIALIST_DIR="$WORKDIR/invest_value_manager"
STATE_DIR="$WORKDIR/state"
SESSION_FILE="$STATE_DIR/specialist_session.txt"
QUEUE_FILE="$STATE_DIR/labestia_queue.jsonl"
TIMEOUT=300

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

# --- Session management ---
mkdir -p "$STATE_DIR"

if [ -f "$SESSION_FILE" ]; then
    SESSION_ID=$(head -1 "$SESSION_FILE")
    SESSION_STARTED=$(sed -n '2p' "$SESSION_FILE" 2>/dev/null || echo "no")
else
    SESSION_ID=$(python3 -c "import uuid; print(uuid.uuid4())")
    SESSION_STARTED="no"
    printf '%s\n%s\n' "$SESSION_ID" "$SESSION_STARTED" > "$SESSION_FILE"
fi

# --- Log my message to queue ---
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

log_to_queue "gobernator" "$MESSAGE"

# --- Build claude command ---
CMD=(claude -p --permission-mode bypassPermissions)
if [ "$SESSION_STARTED" = "started" ]; then
    CMD+=(--resume "$SESSION_ID")
else
    CMD+=(--session-id "$SESSION_ID")
    # Mark session as started for next call
    printf '%s\n%s\n' "$SESSION_ID" "started" > "$SESSION_FILE"
fi

# --- Run specialist ---
TMPOUT=$(mktemp)
TMPERR=$(mktemp)
trap 'rm -f "$TMPOUT" "$TMPERR"' EXIT

RC=0
timeout "$TIMEOUT" "${CMD[@]}" "$MESSAGE" > "$TMPOUT" 2> "$TMPERR" < /dev/null || RC=$?

# timeout returns 124 on timeout
if [ "$RC" -eq 124 ]; then
    log_to_queue "system" "TIMEOUT: specialist did not respond in ${TIMEOUT}s"
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
    log_to_queue "system" "EMPTY: specialist returned no output (rc=$RC)"
    echo "Specialist returned empty response" >&2
    exit 1
fi

LOWER=$(echo "$CLEANED" | tr '[:upper:]' '[:lower:]')
if echo "$LOWER" | grep -q "out of extra usage\|rate limit\|overloaded"; then
    log_to_queue "system" "RATE_LIMIT: $CLEANED"
    echo "$CLEANED" >&2
    exit 1
fi

# --- Log response and output ---
log_to_queue "especialista" "$CLEANED"
echo "$CLEANED"
exit 0
