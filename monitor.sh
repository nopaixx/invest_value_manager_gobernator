#!/bin/bash
# Lightweight system monitor - no API tokens consumed
# Checks daemon, bot, processes every 2 minutes
# Output: /tmp/monitor.log
# Also writes alerts to state/angel_outbox.jsonl if daemon is dead

WORKDIR="/home/angel/invest_value_manager_gobernator"
STATE="$WORKDIR/state"
LOG="/tmp/monitor.log"
OUTBOX="$STATE/angel_outbox.jsonl"
ALERT_SENT=""

echo "$(date '+%H:%M:%S') Monitor started" > "$LOG"

alert_angel() {
    local msg="$1"
    local ts
    ts=$(date -u '+%Y-%m-%dT%H:%M:%SZ')
    echo "{\"text\":\"[Monitor] $msg\",\"ts\":\"$ts\"}" >> "$OUTBOX"
    echo "  ALERT SENT: $msg" >> "$LOG"
}

while true; do
    echo "---" >> "$LOG"
    echo "$(date '+%H:%M:%S') CHECK" >> "$LOG"

    # Daemon alive?
    if pgrep -f "daemon.py" > /dev/null; then
        echo "  Daemon: OK" >> "$LOG"
        ALERT_SENT=""

        # Check if daemon is stalled (no log activity for >30min)
        if [ -f /tmp/daemon.log ]; then
            LAST_MOD=$(stat -c %Y /tmp/daemon.log 2>/dev/null || echo 0)
            NOW=$(date +%s)
            STALE=$((NOW - LAST_MOD))
            if [ "$STALE" -gt 1800 ]; then
                echo "  Daemon: STALLED ($((STALE/60))m no log activity)" >> "$LOG"
            fi
        fi
    else
        echo "  Daemon: DEAD!" >> "$LOG"
        # Alert Angel only once per daemon death
        if [ "$ALERT_SENT" != "daemon" ]; then
            alert_angel "Daemon DEAD. Needs restart: nohup python daemon.py > /tmp/daemon.log 2>&1 &"
            ALERT_SENT="daemon"
        fi
    fi

    # Bot alive?
    if pgrep -f "telegram/bot.py" > /dev/null; then
        echo "  Bot: OK" >> "$LOG"
    else
        echo "  Bot: DEAD!" >> "$LOG"
        if [ "$ALERT_SENT" != "bot" ]; then
            alert_angel "Bot DEAD. Needs restart: bash restart_bot.sh"
            ALERT_SENT="bot"
        fi
    fi

    # Claude processes?
    CLAUDE_COUNT=$(pgrep -c -f "claude -p" 2>/dev/null || echo 0)
    echo "  Claude processes: $CLAUDE_COUNT" >> "$LOG"

    # Last daemon log line
    LAST_LOG=$(tail -1 /tmp/daemon.log 2>/dev/null)
    echo "  Daemon last: ${LAST_LOG:0:120}" >> "$LOG"

    # Queue sizes
    OUTBOX_LINES=$(wc -l < "$OUTBOX" 2>/dev/null || echo 0)
    QUEUE_LINES=$(wc -l < "$STATE/labestia_queue.jsonl" 2>/dev/null || echo 0)
    echo "  Outbox: ${OUTBOX_LINES} lines, Queue: ${QUEUE_LINES} lines" >> "$LOG"

    # Stop file?
    if [ -f "$STATE/stop_requested" ]; then
        echo "  STOP FILE EXISTS!" >> "$LOG"
    fi

    # Angel inbox?
    if [ -f "$STATE/angel_inbox.txt" ]; then
        echo "  Angel inbox: HAS MESSAGE" >> "$LOG"
    fi

    # Specialist failures counter
    if [ -f "$STATE/specialist_failures" ]; then
        FAILURES=$(cat "$STATE/specialist_failures" 2>/dev/null)
        if [ "$FAILURES" -gt 3 ] 2>/dev/null; then
            echo "  Specialist failures: $FAILURES (HIGH)" >> "$LOG"
        fi
    fi

    sleep 120
done
