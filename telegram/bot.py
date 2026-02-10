import asyncio
import subprocess
import logging
import os
import json
import re
import uuid
from datetime import timedelta, timezone

from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, MessageHandler, CommandHandler, filters
from pathlib import Path

load_dotenv()

# --- Constants ---
TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
ANGEL_USER_ID = int(os.environ.get("ANGEL_USER_ID", "998346625"))
BOT_USER_ID = int(TOKEN.split(":")[0])
WORKDIR = "/home/angel/invest_value_manager_gobernator"
CONFIG_FILE = os.path.join(WORKDIR, "telegram", "config.json")
STATE_DIR = os.path.join(WORKDIR, "state")
GOBERNATOR_SESSION_FILE = os.path.join(STATE_DIR, "gobernator_session.txt")
SPECIALIST_SESSION_FILE = os.path.join(STATE_DIR, "specialist_session.txt")
STOP_FILE = os.path.join(STATE_DIR, "stop_requested")
QUEUE_FILE = os.path.join(STATE_DIR, "labestia_queue.jsonl")
GOBERNATOR_TIMEOUT = 3600  # 1 hour — gobernator may multi-turn with specialist
STOP_KEYWORDS = {"para", "stop", "parada"}
BASE_CHECKIN_INTERVAL = 30 * 60  # 30 min in seconds
MAX_CHECKIN_INTERVAL = 2 * 60 * 60  # 2h max backoff
CET = timezone(timedelta(hours=1))

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(message)s")
log = logging.getLogger("gobernator")

# --- Runtime state ---
busy = False
pending_angel_messages = []
bot_username = None
checkin_interval = BASE_CHECKIN_INTERVAL  # current interval (may be backed off)


# --- Session management ---

def get_session_id():
    """Read or create gobernator session ID. Persists across bot restarts."""
    os.makedirs(STATE_DIR, exist_ok=True)
    if os.path.exists(GOBERNATOR_SESSION_FILE):
        with open(GOBERNATOR_SESSION_FILE) as f:
            lines = f.read().strip().splitlines()
            if lines:
                return lines[0], len(lines) > 1 and lines[1] == "started"
    sid = str(uuid.uuid4())
    with open(GOBERNATOR_SESSION_FILE, "w") as f:
        f.write(f"{sid}\nnew\n")
    return sid, False


def mark_session_started(sid):
    with open(GOBERNATOR_SESSION_FILE, "w") as f:
        f.write(f"{sid}\nstarted\n")


def create_new_session():
    sid = str(uuid.uuid4())
    with open(GOBERNATOR_SESSION_FILE, "w") as f:
        f.write(f"{sid}\nnew\n")
    return sid


def create_new_specialist_session():
    sid = str(uuid.uuid4())
    os.makedirs(STATE_DIR, exist_ok=True)
    with open(SPECIALIST_SESSION_FILE, "w") as f:
        f.write(f"{sid}\nno\n")
    return sid


# --- Config ---

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE) as f:
            return json.load(f)
    return {}


def save_config(config):
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)


# --- Output cleaning ---

def clean_claude_output(text):
    text = re.sub(r'<thinking>.*?</thinking>', '', text, flags=re.DOTALL)
    return text.strip()


# --- Rate limit detection ---

def is_rate_limited(text):
    lower = text.lower()
    return any(k in lower for k in ("out of extra usage", "rate limit", "overloaded"))


# --- Gobernator invocation ---

async def run_gobernator(prompt):
    """Call gobernator claude -p. Returns (text, is_rate_limited)."""
    sid, started = get_session_id()
    cmd = ["claude", "-p", "--permission-mode", "bypassPermissions"]
    if started:
        cmd.extend(["--resume", sid])
    else:
        cmd.extend(["--session-id", sid])
        mark_session_started(sid)
    cmd.append(prompt)
    log.info(f"Gobernator [{len(prompt)} chars] resume={started}")

    try:
        result = await asyncio.to_thread(
            subprocess.run, cmd,
            capture_output=True, text=True,
            cwd=WORKDIR, timeout=GOBERNATOR_TIMEOUT
        )
    except subprocess.TimeoutExpired:
        return "Timeout del gobernator (10 min).", True

    output = clean_claude_output(result.stdout or result.stderr or "")
    if not output:
        log.warning("Gobernator returned empty response")
        return "", True
    if is_rate_limited(output):
        log.warning(f"Gobernator rate limited: {output[:200]}")
        return output, True
    return output, False


# --- Messaging ---

async def send_long_message(chat_id, text, bot):
    if not text.strip():
        return
    for i in range(0, len(text), 4000):
        await bot.send_message(chat_id=chat_id, text=text[i:i + 4000])


# --- LabestiaWatcher ---

class LabestiaWatcher:
    """Watches labestia_queue.jsonl and posts new entries to LaBestia group."""

    def __init__(self):
        self.offset = 0
        # Start from current end of file if it exists
        if os.path.exists(QUEUE_FILE):
            self.offset = os.path.getsize(QUEUE_FILE)

    async def poll(self, bot):
        if not os.path.exists(QUEUE_FILE):
            return
        size = os.path.getsize(QUEUE_FILE)
        if size <= self.offset:
            return

        config = load_config()
        specialist_chat = config.get("specialist_chat_id")
        if not specialist_chat:
            self.offset = size
            return

        try:
            with open(QUEUE_FILE, "r") as f:
                f.seek(self.offset)
                new_data = f.read()
            self.offset = size

            for line in new_data.strip().splitlines():
                if not line.strip():
                    continue
                try:
                    entry = json.loads(line)
                    sender = entry.get("from", "?").upper()
                    text = entry.get("text", "")
                    if sender == "SYSTEM":
                        label = "SISTEMA"
                    elif sender == "GOBERNATOR":
                        label = "GOBERNATOR → ESPECIALISTA"
                    else:
                        label = "ESPECIALISTA"
                    display = f"[{label}]\n{text}"
                    await send_long_message(specialist_chat, display, bot)
                except json.JSONDecodeError:
                    log.warning(f"Bad JSON in queue: {line[:100]}")
        except Exception as e:
            log.error(f"LabestiaWatcher error: {e}")


labestia_watcher = LabestiaWatcher()


# --- Backoff ---

def handle_backoff(app):
    """Double checkin interval on rate limit."""
    global checkin_interval
    old = checkin_interval
    checkin_interval = min(checkin_interval * 2, MAX_CHECKIN_INTERVAL)
    if checkin_interval != old:
        log.info(f"Backoff: checkin interval {old}s -> {checkin_interval}s")
        reschedule_checkin(app)


def reset_backoff(app):
    """Reset checkin interval after successful response."""
    global checkin_interval
    if checkin_interval != BASE_CHECKIN_INTERVAL:
        log.info(f"Backoff reset: {checkin_interval}s -> {BASE_CHECKIN_INTERVAL}s")
        checkin_interval = BASE_CHECKIN_INTERVAL
        reschedule_checkin(app)


def reschedule_checkin(app):
    """Remove and re-add the checkin job with current interval."""
    jobs = app.job_queue.get_jobs_by_name("checkin")
    for j in jobs:
        j.schedule_removal()
    app.job_queue.run_repeating(
        scheduled_checkin,
        interval=timedelta(seconds=checkin_interval),
        first=timedelta(seconds=checkin_interval),
        name="checkin"
    )


# --- Stop file ---

def request_stop():
    os.makedirs(STATE_DIR, exist_ok=True)
    Path(STOP_FILE).touch()


def clear_stop():
    if os.path.exists(STOP_FILE):
        os.remove(STOP_FILE)


# --- Message handler ---

async def on_message(update, context):
    global busy

    if not update.message or not update.message.text:
        return
    if update.effective_user.id != ANGEL_USER_ID:
        return

    chat_id = str(update.effective_chat.id)
    text = update.message.text or ""
    config = load_config()

    # Auto-save Angel's chat ID
    if config.get("angel_chat_id") != chat_id:
        config["angel_chat_id"] = chat_id
        save_config(config)
        log.info(f"Angel chat ID saved: {chat_id}")

    if bot_username:
        text = text.replace(f"@{bot_username}", "").strip()
    if not text:
        return

    # Stop keywords
    if busy and text.lower().strip() in STOP_KEYWORDS:
        request_stop()
        await update.message.reply_text("Parada solicitada. Termino lo actual y paro.")
        return

    # Queue if busy
    if busy:
        pending_angel_messages.append(text)
        await update.message.reply_text("Ocupado. Mensaje en cola, te atiendo al terminar.")
        return

    busy = True
    waiting = await update.message.reply_text("Procesando...")

    try:
        response, rate_limited = await run_gobernator(f"[Angel] {text}")
        log.info(f"Gobernator response [{len(response)} chars]: {response[:300]}")
        await waiting.delete()

        if rate_limited and not response:
            log.warning("Rate limited, no response to send")
            handle_backoff(context.application)
        elif rate_limited:
            handle_backoff(context.application)
            await send_long_message(chat_id, response, context.bot)
        else:
            reset_backoff(context.application)
            await send_long_message(chat_id, response, context.bot)

        # Process queued messages
        while pending_angel_messages:
            queued = pending_angel_messages.copy()
            pending_angel_messages.clear()
            combined = "\n".join(f"- {m}" for m in queued)
            resp, rl = await run_gobernator(f"[Angel - mensajes pendientes]\n{combined}")
            if resp:
                await send_long_message(chat_id, resp, context.bot)
            if rl:
                handle_backoff(context.application)

    except Exception as e:
        try:
            await waiting.edit_text(f"Error: {e}")
        except Exception:
            pass
        log.error(f"Error procesando mensaje: {e}")
    finally:
        busy = False


# --- Photo/Document handlers ---

async def handle_image(update, context, file_obj, file_unique_id, file_ext="jpg"):
    global busy

    if update.effective_user.id != ANGEL_USER_ID:
        return

    chat_id = str(update.effective_chat.id)
    config = load_config()
    if config.get("angel_chat_id") != chat_id:
        config["angel_chat_id"] = chat_id
        save_config(config)

    caption = update.message.caption or ""

    if busy:
        pending_angel_messages.append(f"[Imagen con caption: {caption or 'sin caption'}]")
        await update.message.reply_text("Ocupado. Imagen en cola.")
        return

    busy = True
    waiting = await update.message.reply_text("Procesando imagen...")

    try:
        file = await context.bot.get_file(file_obj.file_id)
        img_dir = os.path.join(WORKDIR, "telegram", "incoming_images")
        os.makedirs(img_dir, exist_ok=True)
        img_path = os.path.join(img_dir, f"{file_unique_id}.{file_ext}")
        await file.download_to_drive(img_path)
        log.info(f"Image saved: {img_path}")

        prompt = f"[Angel - Imagen] Guardada en: {img_path}. Caption: {caption or '(sin caption)'}"
        response, rate_limited = await run_gobernator(prompt)
        await waiting.delete()
        if response:
            await send_long_message(chat_id, response, context.bot)
        if rate_limited:
            handle_backoff(context.application)
        else:
            reset_backoff(context.application)

    except Exception as e:
        try:
            await waiting.edit_text(f"Error: {e}")
        except Exception:
            pass
        log.error(f"Error procesando imagen: {e}")
    finally:
        busy = False


async def on_photo(update, context):
    if not update.message or not update.message.photo:
        return
    photo = update.message.photo[-1]
    await handle_image(update, context, photo, photo.file_unique_id, "jpg")


async def on_document(update, context):
    if not update.message or not update.message.document:
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
    await handle_image(update, context, doc, doc.file_unique_id, ext)


# --- Commands ---

async def on_nueva(update, context):
    if update.effective_user.id != ANGEL_USER_ID:
        return
    sid = create_new_session()
    await update.message.reply_text(f"Nueva sesion gobernator ({sid[:8]}...).")


async def on_nueva_especialista(update, context):
    if update.effective_user.id != ANGEL_USER_ID:
        return
    sid = create_new_specialist_session()
    await update.message.reply_text(f"Nueva sesion especialista ({sid[:8]}...).")


async def on_status(update, context):
    if update.effective_user.id != ANGEL_USER_ID:
        return
    config = load_config()
    sid, started = get_session_id()
    sp_sid = "?"
    if os.path.exists(SPECIALIST_SESSION_FILE):
        with open(SPECIALIST_SESSION_FILE) as f:
            sp_sid = f.readline().strip()[:8]
    stop = os.path.exists(STOP_FILE)
    await update.message.reply_text(
        f"Bot Gobernator activo\n"
        f"Estado: {'OCUPADO' if busy else 'Libre'}\n"
        f"Mensajes en cola: {len(pending_angel_messages)}\n"
        f"Check-in interval: {checkin_interval // 60}min\n"
        f"Stop solicitado: {'SI' if stop else 'no'}\n"
        f"Angel chat: {config.get('angel_chat_id', 'no')}\n"
        f"LaBestia: {config.get('specialist_chat_id', 'no')}\n"
        f"Gobernator session: {sid[:8]}...\n"
        f"Specialist session: {sp_sid}..."
    )


async def on_conectar(update, context):
    if update.effective_user.id != ANGEL_USER_ID:
        return
    config = load_config()
    chat_id = str(update.effective_chat.id)
    config["specialist_chat_id"] = chat_id
    save_config(config)
    log.info(f"LaBestia registered: {chat_id}")
    await update.message.reply_text(f"LaBestia registrado (chat ID: {chat_id}).")


async def on_resumen(update, context):
    global busy
    if update.effective_user.id != ANGEL_USER_ID:
        return
    if busy:
        await update.message.reply_text("Ocupado. Intenta en unos minutos.")
        return
    busy = True
    waiting = await update.message.reply_text("Generando resumen...")
    try:
        response, _ = await run_gobernator("[Resumen para Angel]")
        await waiting.delete()
        if response:
            await send_long_message(str(update.effective_chat.id), response, context.bot)
    except Exception as e:
        try:
            await waiting.edit_text(f"Error: {e}")
        except Exception:
            pass
    finally:
        busy = False


# --- Scheduled tasks ---

async def scheduled_checkin(context):
    global busy
    if busy:
        log.info("Busy, skipping check-in")
        return
    config = load_config()
    angel_chat = config.get("angel_chat_id")
    if not angel_chat:
        log.warning("No angel_chat_id, skipping check-in")
        return

    busy = True
    log.info("Check-in periodico...")
    try:
        response, rate_limited = await run_gobernator("[Check-in]")
        log.info(f"Check-in response [{len(response)} chars]: {response[:300]}")
        if rate_limited:
            handle_backoff(context.application)
            if not response:
                return
        else:
            reset_backoff(context.application)
        # Gobernator stdout = message for Angel
        if response:
            await send_long_message(angel_chat, response, context.bot)
    except Exception as e:
        log.error(f"Check-in error: {e}")
    finally:
        busy = False


async def scheduled_summary(context):
    global busy
    if busy:
        log.info("Busy, deferring summary")
        return
    config = load_config()
    chat_id = config.get("angel_chat_id")
    if not chat_id:
        return

    busy = True
    log.info("Resumen periodico...")
    try:
        response, rate_limited = await run_gobernator("[Resumen para Angel]")
        if rate_limited:
            handle_backoff(context.application)
        else:
            reset_backoff(context.application)
        if response:
            await send_long_message(chat_id, response, context.bot)
    except Exception as e:
        log.error(f"Summary error: {e}")
    finally:
        busy = False


async def poll_labestia_queue(context):
    """Poll labestia_queue.jsonl every 5s and post new entries to LaBestia."""
    await labestia_watcher.poll(context.bot)


# --- Init ---

async def post_init(application):
    global bot_username
    bot_info = await application.bot.get_me()
    bot_username = bot_info.username
    log.info(f"Bot: @{bot_username}")


def main():
    app = Application.builder().token(TOKEN).build()
    app.post_init = post_init

    # Commands
    app.add_handler(CommandHandler("nueva", on_nueva))
    app.add_handler(CommandHandler("nueva_especialista", on_nueva_especialista))
    app.add_handler(CommandHandler("status", on_status))
    app.add_handler(CommandHandler("resumen", on_resumen))
    app.add_handler(CommandHandler("conectar", on_conectar))

    # Messages
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_message))
    app.add_handler(MessageHandler(filters.PHOTO, on_photo))
    app.add_handler(MessageHandler(filters.Document.ALL, on_document))

    # Scheduled tasks
    app.job_queue.run_repeating(
        scheduled_checkin,
        interval=timedelta(seconds=BASE_CHECKIN_INTERVAL),
        first=timedelta(minutes=1),
        name="checkin"
    )
    app.job_queue.run_repeating(
        scheduled_summary,
        interval=timedelta(hours=1),
        first=timedelta(hours=1),
        name="summary"
    )
    # Poll labestia queue every 5s
    app.job_queue.run_repeating(
        poll_labestia_queue,
        interval=timedelta(seconds=5),
        first=timedelta(seconds=10),
        name="labestia_poll"
    )

    sid, _ = get_session_id()
    log.info("Bot Gobernator iniciado")
    log.info(f"Gobernator session: {sid[:8]}...")
    log.info(f"Check-in: cada {BASE_CHECKIN_INTERVAL // 60} min | Resumen: cada 1 hora")
    app.run_polling()


if __name__ == "__main__":
    main()
