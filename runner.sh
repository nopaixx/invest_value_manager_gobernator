#!/usr/bin/env bash
# runner.sh — Loop: wake gobernator, sleep, repeat.
# Replaces daemon.py. The gobernator decides what to do each cycle.
set -euo pipefail

WORKDIR="$(cd "$(dirname "$0")" && pwd)"
STATE="$WORKDIR/state"
SESSION_FILE="$STATE/gobernator_session.txt"
STOP_FILE="$STATE/stop_requested"
WAKE_FILE="$STATE/next_wake_seconds"
LAST_CYCLE="$STATE/last_cycle.txt"
LOG="/tmp/gobernator_runner.log"

mkdir -p "$STATE"

# Ensure session exists
if [ ! -f "$SESSION_FILE" ] || [ ! -s "$SESSION_FILE" ]; then
    uuidgen > "$SESSION_FILE"
fi
SESSION_ID="$(head -1 "$SESSION_FILE")"

log() { echo "[$(date '+%H:%M:%S')] $1" | tee -a "$LOG"; }

log "Runner started. Session: $SESSION_ID"

while true; do
    # Check stop
    if [ -f "$STOP_FILE" ]; then
        log "Stop requested. Exiting."
        rm -f "$STOP_FILE"
        exit 0
    fi

    log "Waking gobernator..."
    date -Iseconds > "$LAST_CYCLE"

    # Invoke gobernator — single turn, then return
    claude -p --session-id "$SESSION_ID" \
        "Wake up. Check inbox, check specialist repo, do your job. Write state/next_wake_seconds when done." \
        2>>"$LOG" || log "Gobernator exited with error ($?)"

    # Read sleep duration (default 5 min)
    SLEEP=300
    if [ -f "$WAKE_FILE" ]; then
        SLEEP="$(cat "$WAKE_FILE")"
        # Validate it's a number
        if ! [[ "$SLEEP" =~ ^[0-9]+$ ]]; then
            SLEEP=300
        fi
    fi

    log "Sleeping ${SLEEP}s..."

    # Sleep with stop-check every 10s
    ELAPSED=0
    while [ "$ELAPSED" -lt "$SLEEP" ]; do
        if [ -f "$STOP_FILE" ]; then
            log "Stop requested during sleep. Exiting."
            rm -f "$STOP_FILE"
            exit 0
        fi
        sleep 10
        ELAPSED=$((ELAPSED + 10))
    done
done
