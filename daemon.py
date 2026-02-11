#!/usr/bin/env python3
"""Daemon: ping-pong gobernator <-> specialist.

Normal mode: gob output → specialist → specialist output → gob → repeat
Angel mode:  Angel writes to angel_inbox.txt → daemon routes to gob
             gob response → angel_outbox.jsonl → bot sends to Telegram
             Until Angel says "sigue" → back to normal mode.

Between each turn: 10s quick check (angel/stop).
"""

import subprocess
import signal
import os
import re
import json
import uuid
import time
import sys
from datetime import datetime, timezone

WORKDIR = "/home/angel/invest_value_manager_gobernator"
SPECIALIST_DIR = os.path.join(WORKDIR, "invest_value_manager")
STATE_DIR = os.path.join(WORKDIR, "state")
GOB_SESSION = os.path.join(STATE_DIR, "gobernator_session.txt")
SPEC_SESSION = os.path.join(STATE_DIR, "specialist_session.txt")
QUEUE_FILE = os.path.join(STATE_DIR, "labestia_queue.jsonl")
ANGEL_INBOX = os.path.join(STATE_DIR, "angel_inbox.txt")
ANGEL_OUTBOX = os.path.join(STATE_DIR, "angel_outbox.jsonl")
STOP_FILE = os.path.join(STATE_DIR, "stop_requested")
TURN_SLEEP = 10        # quick check between turns (angel/stop)
POLL_INTERVAL = 5      # check angel/stop every 5s
RETRY_WAIT = 60        # retry on error/rate limit
TIMEOUT = 1800         # 30 min max per claude call
ANGEL_MODE_TIMEOUT = 300  # 5 min max for gobernator in angel mode
ANGEL_IDLE_TIMEOUT = 60   # 60s without angel messages → auto-resume
HEARTBEAT_INTERVAL = 300  # status heartbeat during specialist wait (5 min, was 60s)
RESUME_KEYWORDS = {"sigue", "continue", "resume", "seguir", "adelante"}

# Context injected into initial gobernator message (especially after session reset)
DAEMON_MODE_DISCLAIMER = (
    " IMPORTANTE: Estás en DAEMON MODE. Tu stdout va DIRECTO al especialista. "
    "NO uses talk_to_specialist.sh ni claude -p directamente — el daemon lo gestiona."
)

RATE_LIMIT_PATTERNS = [
    "out of extra usage", "rate_limit_error", "overloaded_error",
    "server is overloaded", "you've exceeded", "resets 12am"
]


def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)


def log_to_queue(sender, text):
    # Never log rate-limit or crash noise to LaBestia
    if is_rate_limited(text) or is_crash_output(text):
        log(f"Skipping queue log ({sender}): rate-limit/crash noise")
        return
    entry = {"from": sender, "text": text, "ts": datetime.now(timezone.utc).isoformat()}
    with open(QUEUE_FILE, "a") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def write_angel_outbox(text):
    entry = {"text": text, "ts": datetime.now(timezone.utc).isoformat()}
    prefix = ""
    if os.path.exists(ANGEL_OUTBOX) and os.path.getsize(ANGEL_OUTBOX) > 0:
        with open(ANGEL_OUTBOX, "rb") as f:
            f.seek(-1, 2)
            if f.read(1) != b'\n':
                prefix = "\n"
    with open(ANGEL_OUTBOX, "a") as f:
        f.write(prefix + json.dumps(entry, ensure_ascii=False) + "\n")


def clean(text):
    return re.sub(r'<thinking>.*?</thinking>', '', text, flags=re.DOTALL).strip()


def sanitize_for_cli(text):
    """Strip null bytes and other control chars that crash Bun when passed as CLI args."""
    return text.replace('\x00', '').replace('\u0000', '')


def is_rate_limited(text):
    lower = text.lower()
    return any(p in lower for p in RATE_LIMIT_PATTERNS)


CRASH_PATTERNS = [
    "Bun has crashed", "Segmentation fault", "panic(main thread)",
    "bun.report", "oh no: Bun has crashed"
]


def is_crash_output(text):
    """Detect if output is a Bun/runtime crash dump instead of a real response."""
    return any(p in text for p in CRASH_PATTERNS)


def get_session(path):
    os.makedirs(STATE_DIR, exist_ok=True)
    if os.path.exists(path):
        with open(path) as f:
            lines = f.read().strip().splitlines()
            if lines:
                return lines[0], len(lines) > 1 and lines[1] == "started"
    sid = str(uuid.uuid4())
    with open(path, "w") as f:
        f.write(f"{sid}\nnew\n")
    return sid, False


def mark_started(path, sid):
    with open(path, "w") as f:
        f.write(f"{sid}\nstarted\n")


def run_claude(session_path, workdir, message, handle_angel_during_wait=False,
               timeout_override=None):
    """Run claude -p, polling every POLL_INTERVAL for stop/angel.

    handle_angel_during_wait: if True, checks angel_inbox while waiting
    and handles Angel mode without killing the subprocess.
    timeout_override: custom timeout (default: TIMEOUT).
    """
    effective_timeout = timeout_override or TIMEOUT
    sid, started = get_session(session_path)
    cmd = ["claude", "-p", "--permission-mode", "bypassPermissions"]
    if started:
        cmd.extend(["--resume", sid])
    else:
        cmd.extend(["--session-id", sid])
        mark_started(session_path, sid)
    cmd.append("--")  # end of options — prevents message starting with -- being parsed as flag
    cmd.append(sanitize_for_cli(message))

    proc = subprocess.Popen(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
        cwd=workdir, preexec_fn=os.setsid
    )
    child_pids.add(proc.pid)

    start = time.time()
    last_heartbeat = start
    while True:
        try:
            stdout, stderr = proc.communicate(timeout=POLL_INTERVAL)
            child_pids.discard(proc.pid)
            return clean(stdout or stderr or "")
        except subprocess.TimeoutExpired:
            elapsed = time.time() - start
            if elapsed > effective_timeout:
                log(f"Timeout after {int(elapsed)}s (limit {int(effective_timeout)}s)")
                proc.kill()
                proc.communicate()
                child_pids.discard(proc.pid)
                raise subprocess.TimeoutExpired(cmd, effective_timeout)
            if check_stop():
                proc.kill()
                proc.communicate()
                child_pids.discard(proc.pid)
                return ""
            if handle_angel_during_wait:
                # Heartbeat: send status to Angel periodically
                now = time.time()
                if now - last_heartbeat >= HEARTBEAT_INTERVAL:
                    mins = int(elapsed / 60)
                    # Only log to daemon stdout, not to Angel's Telegram
                    log(f"Specialist still processing... ({mins}m)")
                    last_heartbeat = now
                angel_msg = check_angel_inbox()
                if angel_msg:
                    log(f"Angel interrupt while waiting: {angel_msg[:80]}")
                    r, _ = handle_angel_mode(angel_msg)
                    if r == "stop":
                        proc.kill()
                        proc.communicate()
                        child_pids.discard(proc.pid)
                        return ""


def check_angel_inbox():
    if os.path.exists(ANGEL_INBOX):
        with open(ANGEL_INBOX) as f:
            msg = f.read().strip()
        if msg:
            os.remove(ANGEL_INBOX)
            return msg
    return None


def check_stop():
    if os.path.exists(STOP_FILE):
        os.remove(STOP_FILE)
        return True
    return False


def interruptible_sleep(seconds):
    """Sleep in small chunks, checking for Angel messages or stop."""
    elapsed = 0
    while elapsed < seconds:
        time.sleep(POLL_INTERVAL)
        elapsed += POLL_INTERVAL
        if check_stop():
            return "stop"
        if os.path.exists(ANGEL_INBOX):
            return "angel"
    return "ok"


def interruptible_wait(seconds):
    """Wait with angel interrupt support. Returns 'ok' or 'stop'."""
    result = interruptible_sleep(seconds)
    if result == "stop":
        return "stop"
    if result == "angel":
        angel_msg = check_angel_inbox()
        if angel_msg:
            r, _ = handle_angel_mode(angel_msg)
            if r == "stop":
                return "stop"
    return "ok"


def process_angel_response(gob_output):
    """Check gob output for [FIN_ANGEL] marker. Returns tuple or None."""
    if not gob_output:
        return None

    if "[FIN_ANGEL]" in gob_output:
        parts = gob_output.split("[FIN_ANGEL]", 1)
        angel_part = parts[0].strip()
        specialist_part = parts[1].strip()
        if angel_part:
            log(f"Gob -> Angel: {angel_part[:120]}")
            write_angel_outbox(angel_part)
        if specialist_part:
            log(f"Gob -> Specialist (auto-resume): {specialist_part[:120]}")
            return "resume_with_msg", specialist_part
        return "resume", None
    else:
        log(f"Gob -> Angel: {gob_output[:120]}")
        write_angel_outbox(gob_output)
        return None


def handle_angel_mode(initial_msg):
    """Handle Angel conversation. Returns ('resume', msg) or ('stop', None)."""
    log(f"Angel mode: {initial_msg[:80]}")

    try:
        gob_output = run_claude(GOB_SESSION, WORKDIR,
                                f"[MENSAJE_DE_ANGEL] {initial_msg}",
                                timeout_override=ANGEL_MODE_TIMEOUT)
    except subprocess.TimeoutExpired:
        log(f"Angel mode: gob timed out ({ANGEL_MODE_TIMEOUT}s). Auto-resuming.")
        write_angel_outbox("[Auto] Procesando tu mensaje. Sigo trabajando con el especialista.")
        return "resume", None

    if not gob_output:
        log("Angel mode: gob empty response. Auto-resuming.")
        write_angel_outbox("[Auto] Mensaje recibido. Sigo trabajando.")
        return "resume", None

    result = process_angel_response(gob_output)
    if result:
        return result

    # Wait for Angel follow-up with idle timeout
    idle_start = time.time()
    while True:
        if check_stop():
            log("Stop requested during Angel mode.")
            return "stop", None

        if time.time() - idle_start > ANGEL_IDLE_TIMEOUT:
            log(f"Angel mode: idle {ANGEL_IDLE_TIMEOUT}s. Auto-resuming to specialist.")
            return "resume", None

        time.sleep(POLL_INTERVAL)
        angel_msg = check_angel_inbox()
        if not angel_msg:
            continue

        idle_start = time.time()  # reset idle timer on new message

        if angel_msg.lower().strip() in RESUME_KEYWORDS:
            log("Angel: resume -> back to specialist")
            return "resume", None

        log(f"Angel: {angel_msg[:80]}")
        try:
            gob_output = run_claude(GOB_SESSION, WORKDIR,
                                    f"[MENSAJE_DE_ANGEL] {angel_msg}",
                                    timeout_override=ANGEL_MODE_TIMEOUT)
        except subprocess.TimeoutExpired:
            log(f"Angel mode: gob timed out. Auto-resuming.")
            write_angel_outbox("[Auto] Timeout procesando. Sigo con el especialista.")
            return "resume", None

        if not gob_output:
            log("Angel mode: gob empty response. Auto-resuming.")
            return "resume", None

        result = process_angel_response(gob_output)
        if result:
            return result
        idle_start = time.time()  # reset after sending response


child_pids = set()


def cleanup_children(signum=None, frame=None):
    """Kill any orphaned claude -p children on daemon exit."""
    for pid in list(child_pids):
        try:
            os.killpg(os.getpgid(pid), signal.SIGKILL)
            log(f"Cleanup: killed process group for PID {pid}")
        except (ProcessLookupError, PermissionError):
            pass
    if signum:
        sys.exit(0)


def main():
    signal.signal(signal.SIGTERM, cleanup_children)
    signal.signal(signal.SIGINT, cleanup_children)
    import atexit
    atexit.register(cleanup_children)

    message = sys.argv[1] if len(sys.argv) > 1 else "Empezamos. ¿Qué tenemos pendiente?"
    # Always inject daemon mode context into initial message
    if DAEMON_MODE_DISCLAIMER not in message:
        message = message + DAEMON_MODE_DISCLAIMER
    last_spec_output = None

    log(f"Daemon started. Initial: {message[:80]}")

    while True:
        if check_stop():
            log("Stop requested. Exiting.")
            break

        try:
            # --- Check Angel inbox first (priority) ---
            angel_msg = check_angel_inbox()
            if angel_msg:
                result, msg = handle_angel_mode(angel_msg)
                if result == "stop":
                    break
                elif result == "resume_with_msg":
                    message = msg
                else:
                    message = last_spec_output or "Continúa con lo que estabas haciendo."
                continue

            # --- Gobernator turn ---
            log(f"-> Gob [{len(message)} chars]")
            gob_output = run_claude(GOB_SESSION, WORKDIR, message)

            if not gob_output:
                log(f"Gob: empty. Retry in {RETRY_WAIT}s...")
                if interruptible_wait(RETRY_WAIT) == "stop":
                    break
                continue

            if is_crash_output(gob_output):
                log(f"Gob: CRASH DETECTED. Resetting gob session. Retry in 60s...")
                # Reset session so next call creates fresh one
                sid = str(uuid.uuid4())
                with open(GOB_SESSION, "w") as f:
                    f.write(f"{sid}\nnew\n")
                if interruptible_wait(60) == "stop":
                    break
                continue

            if is_rate_limited(gob_output):
                log(f"Gob: RATE LIMITED. Sleeping {RETRY_WAIT}s...")
                if interruptible_wait(RETRY_WAIT) == "stop":
                    break
                continue

            log(f"<- Gob [{len(gob_output)} chars]: {gob_output[:120]}")
            log_to_queue("gobernator", gob_output)

            # --- Specialist turn ---
            log(f"-> Spec [{len(gob_output)} chars]")
            spec_output = run_claude(SPEC_SESSION, SPECIALIST_DIR, gob_output,
                                     handle_angel_during_wait=True)

            if not spec_output:
                log(f"Spec: empty. Retry in {RETRY_WAIT}s...")
                message = gob_output
                if interruptible_wait(RETRY_WAIT) == "stop":
                    break
                continue

            if is_crash_output(spec_output):
                log(f"Spec: CRASH DETECTED. Resetting spec session. Retry in 60s...")
                sid = str(uuid.uuid4())
                with open(SPEC_SESSION, "w") as f:
                    f.write(f"{sid}\nnew\n")
                message = gob_output  # retry with same gob message
                if interruptible_wait(60) == "stop":
                    break
                continue

            if is_rate_limited(spec_output):
                log(f"Spec: RATE LIMITED. Sleeping {RETRY_WAIT}s...")
                message = gob_output
                if interruptible_wait(RETRY_WAIT) == "stop":
                    break
                continue

            log(f"<- Spec [{len(spec_output)} chars]: {spec_output[:120]}")
            log_to_queue("especialista", spec_output)

            message = spec_output
            last_spec_output = spec_output

            # --- 5-minute interruptible sleep ---
            log(f"Next turn in {TURN_SLEEP}s...")
            result = interruptible_sleep(TURN_SLEEP)
            if result == "stop":
                log("Stop requested during sleep. Exiting.")
                break
            elif result == "angel":
                angel_msg = check_angel_inbox()
                if angel_msg:
                    r, msg = handle_angel_mode(angel_msg)
                    if r == "stop":
                        break
                    elif r == "resume_with_msg":
                        message = msg
                    else:
                        message = last_spec_output or "Continúa con lo que estabas haciendo."

        except subprocess.TimeoutExpired:
            log(f"Timeout. Retry in {RETRY_WAIT}s...")
            if interruptible_wait(RETRY_WAIT) == "stop":
                break
        except KeyboardInterrupt:
            log("Stopped.")
            break
        except Exception as e:
            log(f"Error: {e}. Retry in 60s...")
            if interruptible_wait(60) == "stop":
                break


if __name__ == "__main__":
    main()
