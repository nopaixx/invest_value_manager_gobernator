#!/usr/bin/env python3
"""Telegram bot — Angel <-> Gobernator bridge via file I/O.

Simplified v2: no LaBestia, no watchdog, no /conectar.
Just moves text: Angel (Telegram) <-> state/ files.
"""

import asyncio
import json
import logging
import os
import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path

from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters

load_dotenv()

TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
ANGEL_USER_ID = int(os.environ.get("ANGEL_USER_ID", "998346625"))
WORKDIR = Path("/home/angel/invest_value_manager_gobernator")
STATE = WORKDIR / "state"
INBOX = STATE / "angel_inbox.jsonl"
OUTBOX = STATE / "angel_outbox.jsonl"
STOP_FILE = STATE / "stop_requested"
LAST_CYCLE = STATE / "last_cycle.txt"
WAKE_FILE = STATE / "next_wake_seconds"
CONFIG_FILE = WORKDIR / "telegram" / "config.json"

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(message)s")
log = logging.getLogger("bot")


# --- Config ---

def load_config():
    if CONFIG_FILE.exists():
        return json.loads(CONFIG_FILE.read_text())
    return {}

def save_config(cfg):
    CONFIG_FILE.write_text(json.dumps(cfg, indent=2))


# --- Helpers ---

async def send_long(chat_id, text, bot):
    if not text.strip():
        return
    for i in range(0, len(text), 4000):
        await bot.send_message(chat_id=chat_id, text=text[i:i + 4000])


def is_angel(update):
    return update.effective_user and update.effective_user.id == ANGEL_USER_ID


# --- Handlers ---

async def on_message(update, context):
    if not update.message or not update.message.text or not is_angel(update):
        return

    # Auto-save angel chat_id
    cfg = load_config()
    chat_id = str(update.effective_chat.id)
    if cfg.get("angel_chat_id") != chat_id:
        cfg["angel_chat_id"] = chat_id
        save_config(cfg)

    text = update.message.text.strip()
    if not text:
        return

    # Stop keywords
    if text.lower() in {"para", "stop", "parada"}:
        STOP_FILE.touch()
        await update.message.reply_text("Stop solicitado.")
        return

    # Append to inbox (JSONL)
    STATE.mkdir(exist_ok=True)
    entry = json.dumps({"text": text, "ts": datetime.now(timezone.utc).isoformat()})
    with open(INBOX, "a") as f:
        f.write(entry + "\n")
    await update.message.reply_text("Recibido.")


async def on_photo(update, context):
    if not update.message or not update.message.photo or not is_angel(update):
        return

    photo = update.message.photo[-1]
    caption = update.message.caption or ""

    file = await context.bot.get_file(photo.file_id)
    img_dir = WORKDIR / "telegram" / "incoming_images"
    img_dir.mkdir(exist_ok=True)
    img_path = img_dir / f"{photo.file_unique_id}.jpg"
    await file.download_to_drive(str(img_path))

    entry = json.dumps({
        "text": f"[Imagen: {img_path}] {caption}",
        "ts": datetime.now(timezone.utc).isoformat()
    })
    with open(INBOX, "a") as f:
        f.write(entry + "\n")
    await update.message.reply_text("Imagen recibida.")


async def on_status(update, context):
    if not is_angel(update):
        return

    # Runner alive?
    try:
        r = subprocess.run(["pgrep", "-f", "runner.sh"], capture_output=True, timeout=5)
        runner = "RUNNING" if r.returncode == 0 else "STOPPED"
    except Exception:
        runner = "UNKNOWN"

    # Last cycle
    last = LAST_CYCLE.read_text().strip() if LAST_CYCLE.exists() else "never"

    # Next wake
    wake = WAKE_FILE.read_text().strip() + "s" if WAKE_FILE.exists() else "default (300s)"

    # Stop requested?
    stop = "YES" if STOP_FILE.exists() else "no"

    # Inbox pending
    inbox_lines = 0
    if INBOX.exists():
        inbox_lines = sum(1 for _ in open(INBOX))

    await update.message.reply_text(
        f"Runner: {runner}\n"
        f"Last cycle: {last}\n"
        f"Next wake: {wake}\n"
        f"Stop: {stop}\n"
        f"Inbox pending: {inbox_lines} msg"
    )


async def on_stop(update, context):
    if not is_angel(update):
        return
    STOP_FILE.touch()
    await update.message.reply_text("Stop solicitado.")


# --- Outbox poller ---

class JsonlPoller:
    def __init__(self, path):
        self.path = path
        self.offset = path.stat().st_size if path.exists() else 0

    def read_new(self):
        if not self.path.exists():
            return []
        size = self.path.stat().st_size
        if size <= self.offset:
            return []
        entries = []
        with open(self.path) as f:
            f.seek(self.offset)
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    for part in line.replace("}{", "}\n{").split("\n"):
                        part = part.strip()
                        if part:
                            try:
                                entries.append(json.loads(part))
                            except json.JSONDecodeError:
                                pass
        self.offset = size
        return entries


outbox_poller = JsonlPoller(OUTBOX)


async def poll_outbox(context):
    cfg = load_config()
    chat_id = cfg.get("angel_chat_id")
    if not chat_id:
        return
    for entry in outbox_poller.read_new():
        text = entry.get("text", "")
        if text:
            await send_long(chat_id, text, context.bot)


# --- Main ---

async def post_init(app):
    info = await app.bot.get_me()
    log.info(f"Bot: @{info.username}")


def main():
    app = Application.builder().token(TOKEN).build()
    app.post_init = post_init

    app.add_handler(CommandHandler("status", on_status))
    app.add_handler(CommandHandler("stop", on_stop))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_message))
    app.add_handler(MessageHandler(filters.PHOTO, on_photo))

    app.job_queue.run_repeating(poll_outbox, interval=timedelta(seconds=5), first=timedelta(seconds=5))

    log.info("Bot v2 started")
    app.run_polling()


if __name__ == "__main__":
    main()
