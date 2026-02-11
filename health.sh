#!/bin/bash
# Health check — estado completo del sistema en un vistazo
set -euo pipefail

WORKDIR="/home/angel/invest_value_manager_gobernator"
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

ok() { echo -e "  ${GREEN}OK${NC}  $1"; }
warn() { echo -e "  ${YELLOW}!!${NC}  $1"; }
fail() { echo -e "  ${RED}FAIL${NC}  $1"; }

echo "=== Gobernator Health Check ==="
echo ""

# 1. Processes
echo "--- Procesos ---"
if pgrep -f "python.*daemon.py" > /dev/null 2>&1; then
    pid=$(pgrep -f "python.*daemon.py" | head -1)
    uptime=$(ps -o etime= -p "$pid" 2>/dev/null | xargs)
    ok "Daemon corriendo (PID $pid, uptime $uptime)"
else
    fail "Daemon NO está corriendo"
fi

if pgrep -f "python.*bot.py" > /dev/null 2>&1; then
    pid=$(pgrep -f "python.*bot.py" | head -1)
    uptime=$(ps -o etime= -p "$pid" 2>/dev/null | xargs)
    ok "Bot corriendo (PID $pid, uptime $uptime)"
else
    fail "Bot NO está corriendo"
fi

# 2. Last daemon activity
echo ""
echo "--- Última actividad ---"
if [ -f /tmp/daemon.log ]; then
    last_line=$(tail -1 /tmp/daemon.log)
    last_time=$(echo "$last_line" | grep -oP '^\[\K[0-9:]+' || echo "?")
    echo "  Daemon: [$last_time] $(echo "$last_line" | sed 's/^\[[^]]*\] //' | head -c 100)"

    # Check if last activity is recent (within 15 min)
    if [ "$last_time" != "?" ]; then
        last_epoch=$(date -d "today $last_time" +%s 2>/dev/null || echo 0)
        now_epoch=$(date +%s)
        diff=$(( now_epoch - last_epoch ))
        if [ "$diff" -gt 900 ]; then
            warn "Sin actividad hace $(( diff / 60 )) minutos"
        else
            ok "Activo hace $(( diff / 60 )) min"
        fi
    fi
else
    warn "No hay daemon.log"
fi

# 3. Signal files
echo ""
echo "--- Señales ---"
if [ -f "$WORKDIR/state/angel_inbox.txt" ]; then
    content=$(cat "$WORKDIR/state/angel_inbox.txt")
    warn "angel_inbox.txt PENDIENTE: '$content'"
else
    ok "angel_inbox.txt vacío (bien)"
fi

if [ -f "$WORKDIR/state/stop_requested" ]; then
    fail "stop_requested EXISTE — daemon se parará"
else
    ok "No hay stop_requested"
fi

# 4. Outbox health
echo ""
echo "--- Mensajes ---"
if [ -f "$WORKDIR/state/angel_outbox.jsonl" ]; then
    total=$(wc -l < "$WORKDIR/state/angel_outbox.jsonl")
    last_ts=$(tail -1 "$WORKDIR/state/angel_outbox.jsonl" | python3 -c "import sys,json; print(json.load(sys.stdin).get('ts','?'))" 2>/dev/null || echo "?")
    ok "angel_outbox: $total mensajes, último: $last_ts"

    # Check for corrupted lines
    corrupt=$(python3 -c "
import json
count = 0
with open('$WORKDIR/state/angel_outbox.jsonl') as f:
    for line in f:
        line = line.strip()
        if not line: continue
        try: json.loads(line)
        except: count += 1
print(count)
" 2>/dev/null || echo "?")
    if [ "$corrupt" != "0" ] && [ "$corrupt" != "?" ]; then
        fail "angel_outbox: $corrupt líneas corruptas!"
    fi
fi

if [ -f "$WORKDIR/state/labestia_queue.jsonl" ]; then
    total=$(wc -l < "$WORKDIR/state/labestia_queue.jsonl")
    ok "labestia_queue: $total entradas"
fi

# 5. Bot delivery
echo ""
echo "--- Bot Telegram ---"
if [ -f /tmp/gobernator_bot.log ]; then
    sent=$(grep -c "sendMessage.*200 OK" /tmp/gobernator_bot.log 2>/dev/null || echo 0)
    errors=$(grep -ci "error" /tmp/gobernator_bot.log 2>/dev/null || echo "0")
    ok "Mensajes enviados: $sent, errores: $errors"
fi

# 6. Sessions
echo ""
echo "--- Sesiones ---"
for name in gobernator specialist; do
    file="$WORKDIR/state/${name}_session.txt"
    if [ -f "$file" ]; then
        sid=$(head -1 "$file" | head -c 8)
        status=$(sed -n '2p' "$file" 2>/dev/null || echo "?")
        ok "$name: $sid... ($status)"
    else
        warn "$name: sin sesión"
    fi
done

echo ""
echo "=== Fin ==="
