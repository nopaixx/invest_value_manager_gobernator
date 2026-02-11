#!/usr/bin/env python3
"""Thin Telegram bot — file I/O bridge between Angel and the daemon.

NO gobernator invocation. NO session management. NO intelligence.
Just moves text: Telegram ↔ files in state/.
"""

import asyncio
import logging
import os
import json
import subprocess
from datetime import datetime, timedelta, timezone

from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, MessageHandler, CommandHandler, filters
from pathlib import Path

load_dotenv()

TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
ANGEL_USER_ID = int(os.environ.get("ANGEL_USER_ID", "998346625"))
WORKDIR = "/home/angel/invest_value_manager_gobernator"
CONFIG_FILE = os.path.join(WORKDIR, "telegram", "config.json")
STATE_DIR = os.path.join(WORKDIR, "state")
ANGEL_INBOX = os.path.join(STATE_DIR, "angel_inbox.txt")
ANGEL_OUTBOX = os.path.join(STATE_DIR, "angel_outbox.jsonl")
QUEUE_FILE = os.path.join(STATE_DIR, "labestia_queue.jsonl")
STOP_FILE = os.path.join(STATE_DIR, "stop_requested")
GOB_SESSION = os.path.join(STATE_DIR, "gobernator_session.txt")
STOP_KEYWORDS = {"para", "stop", "parada"}

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(message)s")
log = logging.getLogger("bot")

bot_username = None


# --- Config ---

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE) as f:
            return json.load(f)
    return {}


def save_config(config):
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)


# --- Messaging ---

async def send_long(chat_id, text, bot):
    if not text.strip():
        return
    for i in range(0, len(text), 4000):
        await bot.send_message(chat_id=chat_id, text=text[i:i + 4000])


# --- Angel writes → angel_inbox.txt ---

async def on_message(update, context):
    if not update.message or not update.message.text:
        return
    if update.effective_user.id != ANGEL_USER_ID:
        return

    chat_id = str(update.effective_chat.id)
    config = load_config()
    if config.get("angel_chat_id") != chat_id:
        config["angel_chat_id"] = chat_id
        save_config(config)

    text = update.message.text or ""
    if bot_username:
        text = text.replace(f"@{bot_username}", "").strip()
    if not text:
        return

    # Stop keywords
    if text.lower().strip() in STOP_KEYWORDS:
        Path(STOP_FILE).touch()
        await update.message.reply_text("Stop solicitado.")
        return

    # Write to inbox — daemon picks it up
    os.makedirs(STATE_DIR, exist_ok=True)
    with open(ANGEL_INBOX, "w") as f:
        f.write(text)
    await update.message.reply_text("Recibido.")


async def on_photo(update, context):
    if not update.message or not update.message.photo:
        return
    if update.effective_user.id != ANGEL_USER_ID:
        return

    photo = update.message.photo[-1]
    caption = update.message.caption or ""

    file = await context.bot.get_file(photo.file_id)
    img_dir = os.path.join(WORKDIR, "telegram", "incoming_images")
    os.makedirs(img_dir, exist_ok=True)
    img_path = os.path.join(img_dir, f"{photo.file_unique_id}.jpg")
    await file.download_to_drive(img_path)

    os.makedirs(STATE_DIR, exist_ok=True)
    with open(ANGEL_INBOX, "w") as f:
        f.write(f"[Imagen guardada en {img_path}] {caption}")
    await update.message.reply_text("Imagen recibida.")


async def on_document(update, context):
    if not update.message or not update.message.document:
        return
    if update.effective_user.id != ANGEL_USER_ID:
        return

    doc = update.message.document
    mime = doc.mime_type or ""
    if not mime.startswith("image/"):
        return

    ext = "jpg"
    if doc.file_name and "." in doc.file_name:
        ext = doc.file_name.rsplit(".", 1)[-1].lower()
    elif "png" in mime:
        ext = "png"

    file = await context.bot.get_file(doc.file_id)
    img_dir = os.path.join(WORKDIR, "telegram", "incoming_images")
    os.makedirs(img_dir, exist_ok=True)
    img_path = os.path.join(img_dir, f"{doc.file_unique_id}.{ext}")
    await file.download_to_drive(img_path)

    caption = update.message.caption or ""
    os.makedirs(STATE_DIR, exist_ok=True)
    with open(ANGEL_INBOX, "w") as f:
        f.write(f"[Imagen guardada en {img_path}] {caption}")
    await update.message.reply_text("Imagen recibida.")


# --- Commands ---

DAEMON_LOG = "/tmp/daemon.log"
WATCHDOG_INTERVAL = 300       # check every 5 min
DAEMON_STALE_THRESHOLD = 900  # 15 min without activity = stale
last_watchdog_alert = None


def get_daemon_status():
    """Get real daemon health info."""
    info = {}
    # Process alive?
    try:
        result = subprocess.run(["pgrep", "-f", "python.*daemon.py"],
                                capture_output=True, text=True, timeout=5)
        info["daemon_alive"] = result.returncode == 0
    except Exception:
        info["daemon_alive"] = False

    # Last activity from log
    info["last_activity"] = None
    info["last_line"] = ""
    if os.path.exists(DAEMON_LOG):
        try:
            result = subprocess.run(["tail", "-1", DAEMON_LOG],
                                    capture_output=True, text=True, timeout=5)
            line = result.stdout.strip()
            info["last_line"] = line[:120]
            # Extract timestamp [HH:MM:SS]
            if line.startswith("[") and "]" in line:
                ts_str = line[1:line.index("]")]
                today = datetime.now().strftime("%Y-%m-%d")
                info["last_activity"] = datetime.strptime(
                    f"{today} {ts_str}", "%Y-%m-%d %H:%M:%S")
        except Exception:
            pass

    # Stale?
    info["stale"] = False
    if info["last_activity"]:
        diff = (datetime.now() - info["last_activity"]).total_seconds()
        info["stale"] = diff > DAEMON_STALE_THRESHOLD
        info["idle_min"] = int(diff / 60)
    else:
        info["idle_min"] = -1

    # Signal files
    info["stop"] = os.path.exists(STOP_FILE)
    info["inbox_pending"] = os.path.exists(ANGEL_INBOX)

    return info


async def on_status(update, context):
    if update.effective_user.id != ANGEL_USER_ID:
        return
    info = get_daemon_status()

    daemon = "CORRIENDO" if info["daemon_alive"] else "PARADO"
    stop = "SI" if info["stop"] else "no"
    inbox = "SI" if info["inbox_pending"] else "no"
    idle = f'{info["idle_min"]} min' if info["idle_min"] >= 0 else "?"
    stale = " (SIN ACTIVIDAD)" if info["stale"] else ""

    await update.message.reply_text(
        f"Daemon: {daemon}{stale}\n"
        f"Idle: {idle}\n"
        f"Stop: {stop}\n"
        f"Inbox pendiente: {inbox}\n"
        f"Última: {info['last_line']}"
    )


async def on_conectar(update, context):
    if update.effective_user.id != ANGEL_USER_ID:
        return
    config = load_config()
    config["specialist_chat_id"] = str(update.effective_chat.id)
    save_config(config)
    await update.message.reply_text("LaBestia registrado.")


async def on_stop(update, context):
    if update.effective_user.id != ANGEL_USER_ID:
        return
    Path(STOP_FILE).touch()
    await update.message.reply_text("Stop solicitado al daemon.")


# --- File pollers ---

class FilePoller:
    """Polls a JSONL file for new entries."""

    def __init__(self, filepath):
        self.filepath = filepath
        self.offset = 0
        if os.path.exists(filepath):
            self.offset = os.path.getsize(filepath)

    def read_new(self):
        if not os.path.exists(self.filepath):
            return []
        size = os.path.getsize(self.filepath)
        if size <= self.offset:
            return []
        entries = []
        with open(self.filepath) as f:
            f.seek(self.offset)
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    # Handle concatenated JSON objects (missing newline)
                    for part in line.replace("}{", "}\n{").split("\n"):
                        part = part.strip()
                        if part:
                            try:
                                entries.append(json.loads(part))
                            except json.JSONDecodeError:
                                log.warning(f"Skipping malformed JSON: {part[:80]}")
        self.offset = size
        return entries


angel_outbox_poller = FilePoller(ANGEL_OUTBOX)
labestia_poller = FilePoller(QUEUE_FILE)


async def watchdog(context):
    """Monitor daemon health. Alert Angel + auto-restart if daemon dies."""
    global last_watchdog_alert
    info = get_daemon_status()
    config = load_config()
    angel_chat = config.get("angel_chat_id")
    if not angel_chat:
        return

    now = datetime.now()
    # Don't spam — max 1 alert per 30 min
    if last_watchdog_alert and (now - last_watchdog_alert).total_seconds() < 1800:
        return

    if not info["daemon_alive"]:
        log.warning("Watchdog: daemon not running. Restarting...")
        try:
            subprocess.Popen(
                ["nohup", "python", os.path.join(WORKDIR, "daemon.py")],
                stdout=open(DAEMON_LOG, "a"),
                stderr=subprocess.STDOUT,
                cwd=WORKDIR,
                start_new_session=True
            )
            await context.bot.send_message(
                chat_id=angel_chat,
                text="[WATCHDOG] Daemon estaba muerto. Reiniciado automáticamente."
            )
        except Exception as e:
            await context.bot.send_message(
                chat_id=angel_chat,
                text=f"[WATCHDOG] Daemon muerto. Error al reiniciar: {e}"
            )
        last_watchdog_alert = now

    elif info["stale"] and not info["stop"]:
        await context.bot.send_message(
            chat_id=angel_chat,
            text=f"[WATCHDOG] Daemon sin actividad hace {info['idle_min']} min.\n"
                 f"Última: {info['last_line']}"
        )
        last_watchdog_alert = now


async def poll_angel_outbox(context):
    """Gobernator's messages for Angel → Telegram."""
    config = load_config()
    angel_chat = config.get("angel_chat_id")
    if not angel_chat:
        return
    for entry in angel_outbox_poller.read_new():
        text = entry.get("text", "")
        if text:
            await send_long(angel_chat, text, context.bot)


async def poll_labestia(context):
    """Gob/spec conversation → LaBestia."""
    config = load_config()
    chat_id = config.get("specialist_chat_id")
    if not chat_id:
        return
    for entry in labestia_poller.read_new():
        sender = entry.get("from", "?").upper()
        text = entry.get("text", "")
        if sender == "GOBERNATOR":
            label = "GOBERNATOR -> ESPECIALISTA"
        elif sender == "SYSTEM":
            label = "SISTEMA"
        else:
            label = "ESPECIALISTA"
        await send_long(chat_id, f"[{label}]\n{text}", context.bot)


# --- Init ---

async def post_init(application):
    global bot_username
    bot_info = await application.bot.get_me()
    bot_username = bot_info.username
    log.info(f"Bot: @{bot_username}")


def main():
    app = Application.builder().token(TOKEN).build()
    app.post_init = post_init

    app.add_handler(CommandHandler("status", on_status))
    app.add_handler(CommandHandler("conectar", on_conectar))
    app.add_handler(CommandHandler("stop", on_stop))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_message))
    app.add_handler(MessageHandler(filters.PHOTO, on_photo))
    app.add_handler(MessageHandler(filters.Document.ALL, on_document))

    app.job_queue.run_repeating(poll_angel_outbox, interval=timedelta(seconds=5), first=timedelta(seconds=5))
    app.job_queue.run_repeating(poll_labestia, interval=timedelta(seconds=5), first=timedelta(seconds=10))
    app.job_queue.run_repeating(watchdog, interval=timedelta(seconds=WATCHDOG_INTERVAL), first=timedelta(seconds=60))

    log.info("Bot Telegram (thin) iniciado")
    app.run_polling()


if __name__ == "__main__":
    main()
