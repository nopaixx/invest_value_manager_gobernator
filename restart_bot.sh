#!/bin/bash
# Restart gobernator bot
# Uses setsid to create a new process session that survives parent death
#
# Safe to call from inside the bot itself.

cd /home/angel/invest_value_manager_gobernator

# Find current bot PID (matches both "python bot.py" and "/path/to/python bot.py")
OLD_PID=$(pgrep -f "telegram/bot.py" | head -1)

# Launch new bot in a NEW SESSION (setsid) — survives parent death
setsid bash -c 'sleep 3 && cd /home/angel/invest_value_manager_gobernator && exec python telegram/bot.py' > /tmp/gobernator.log 2>&1 &

echo "New bot scheduled. Killing old bot (PID: $OLD_PID)..."

# Kill only the old bot by PID
if [ -n "$OLD_PID" ]; then
    kill -9 "$OLD_PID" 2>/dev/null
    echo "Done. New bot starts in 3 seconds."
else
    echo "No running bot found. New bot starts in 3 seconds."
fi

echo "Check: tail -f /tmp/gobernator.log"
