import asyncio
import subprocess
import logging
import os
import json
import re
import uuid
import tempfile
from datetime import time, timezone, timedelta

from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, MessageHandler, CommandHandler, filters
from pathlib import Path

load_dotenv()

TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
ANGEL_USER_ID = int(os.environ.get("ANGEL_USER_ID", "998346625"))
BOT_USER_ID = int(TOKEN.split(":")[0])
WORKDIR = "/home/angel/invest_value_manager_gobernator"
SPECIALIST_WORKDIR = os.path.join(WORKDIR, "invest_value_manager")
CONFIG_FILE = os.path.join(WORKDIR, "telegram", "config.json")
SPECIALIST_TIMEOUT = 3600  # 1 hour - match gobernator timeout, heavy tasks need time

# Session IDs - generated at startup to isolate from interactive Claude Code sessions
# /nueva and /nueva_especialista regenerate these for fresh sessions
gobernator_session_id = str(uuid.uuid4())
specialist_session_id = str(uuid.uuid4())

CET = timezone(timedelta(hours=1))

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(message)s")
log = logging.getLogger("gobernator")

# Session state
new_session = False
specialist_new_session = False
gobernator_session_started = False  # True after first successful call
specialist_session_started = False
bot_username = None

# Concurrency state
busy = False
stop_requested = False
specialist_turn = 0
MAX_SPECIALIST_TURNS = 10
pending_angel_messages = []

STOP_KEYWORDS = {"para", "stop", "parada"}


class SpecialistEmptyResponse(Exception):
    """Raised when specialist returns empty or rate-limited response."""
    pass


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
    """Strip thinking blocks and other artifacts from Claude output."""
    text = re.sub(r'<thinking>.*?</thinking>', '', text, flags=re.DOTALL)
    return text.strip()


# --- Claude CLI: Gobernator ---

async def run_claude(msg, use_continue=True):
    global gobernator_session_started
    cmd = ["claude", "-p", "--permission-mode", "bypassPermissions"]
    if use_continue and gobernator_session_started:
        cmd.extend(["--resume", gobernator_session_id])
    else:
        cmd.extend(["--session-id", gobernator_session_id])
        gobernator_session_started = True
    cmd.append(msg)
    log.info(f"Gobernator Claude [{len(msg)} chars] continue={use_continue}")

    result = await asyncio.to_thread(
        subprocess.run, cmd,
        capture_output=True, text=True,
        cwd=WORKDIR, timeout=3600
    )
    output = clean_claude_output(result.stdout or result.stderr or "")
    if not output:
        log.warning("Gobernator returned empty response")
        return "Sin respuesta del gobernator (posible rate limit)"
    return output


# --- Claude CLI: Especialista ---

async def run_specialist_claude(msg, use_continue=True):
    """Invoke the specialist's Claude instance locally."""
    global specialist_new_session, specialist_session_started
    cmd = ["claude", "-p", "--permission-mode", "bypassPermissions"]
    if use_continue and not specialist_new_session and specialist_session_started:
        cmd.extend(["--resume", specialist_session_id])
    else:
        cmd.extend(["--session-id", specialist_session_id])
        specialist_session_started = True
    specialist_new_session = False
    cmd.append(msg)
    log.info(f"Especialista Claude [{len(msg)} chars]")

    result = await asyncio.to_thread(
        subprocess.run, cmd,
        capture_output=True, text=True,
        cwd=SPECIALIST_WORKDIR, timeout=SPECIALIST_TIMEOUT
    )
    log.info(f"Specialist returncode={result.returncode} stdout=[{len(result.stdout or '')} chars] stderr=[{len(result.stderr or '')} chars]")
    if result.stderr:
        log.info(f"Specialist stderr: {result.stderr[:500]}")
    output = clean_claude_output(result.stdout or result.stderr or "")
    if not output or "out of extra usage" in output.lower():
        raise SpecialistEmptyResponse(output or f"Sin respuesta del especialista (rc={result.returncode})")
    return output


# --- Messaging ---

async def send_long_message(chat_id, text, bot):
    if not text.strip():
        return
    for i in range(0, len(text), 4000):
        await bot.send_message(chat_id=chat_id, text=text[i:i + 4000])


async def post_to_labestia(instruction, response, bot, turn=0):
    """Post both sides of the conversation to LaBestia for Angel to observe."""
    config = load_config()
    specialist_chat = config.get("specialist_chat_id")
    if not specialist_chat:
        log.warning("No specialist_chat_id, can't post to LaBestia")
        return

    turn_label = f" [Turno {turn}]" if turn > 0 else ""
    display = (
        f"GOBERNATOR → ESPECIALISTA{turn_label}:\n{instruction}\n\n"
        f"---\n\n"
        f"ESPECIALISTA:\n{response}"
    )
    await send_long_message(specialist_chat, display, bot)


async def trace_to_labestia(label, text, bot):
    """Post activity trace to LaBestia so Angel always has visibility."""
    config = load_config()
    specialist_chat = config.get("specialist_chat_id")
    if not specialist_chat:
        return
    await send_long_message(specialist_chat, f"[{label}]\n{text}", bot)


# --- Routing ---

ROUTING_INSTRUCTIONS = (
    "\n\nINSTRUCCIONES DE ENRUTAMIENTO:\n"
    "- Para responder a Angel: [PARA_ANGEL]texto[/PARA_ANGEL]\n"
    "- Para enviar al especialista: [PARA_ESPECIALISTA]texto[/PARA_ESPECIALISTA]\n"
    "- Puedes usar ambos tags en la misma respuesta.\n"
    "- Al especialista SIEMPRE hablas como Angel (humano), NUNCA revelas que eres IA.\n"
    "- El especialista se invoca localmente (claude -p), no por Telegram.\n"
    "- La conversacion se postea en LaBestia para que Angel observe.\n"
    "- Si no usas tags, el mensaje se envia solo al chat de origen."
)


async def route_response(response, source_chat_id, context, turn=0, scheduled=False):
    """Parse routing tags and act. Recursive for multi-turn specialist conversations."""
    global specialist_turn, stop_requested
    config = load_config()
    angel_chat = config.get("angel_chat_id")

    para_angel = re.findall(
        r'\[PARA_ANGEL\](.*?)\[/PARA_ANGEL\]', response, re.DOTALL
    )
    para_especialista = re.findall(
        r'\[PARA_ESPECIALISTA\](.*?)\[/PARA_ESPECIALISTA\]', response, re.DOTALL
    )

    # No tags: trace everything to LaBestia for visibility
    if not para_angel and not para_especialista:
        if scheduled:
            # Check-in without tags - gobernator didn't route. Retry once.
            log.warning(f"Check-in sin tags, reintentando: {response[:200]}")
            await trace_to_labestia("CHECK-IN (sin tags, reintentando)", response[:2000], context.bot)
            retry = await run_claude(
                "Tu respuesta anterior no incluyo tags de enrutamiento.\n"
                "DEBES hablar con el especialista en cada check-in.\n"
                "Usa [PARA_ESPECIALISTA]tu mensaje[/PARA_ESPECIALISTA] para enviarle una instruccion.\n"
                "Si tambien quieres informar a Angel: [PARA_ANGEL]texto[/PARA_ANGEL]",
                use_continue=True
            )
            log.info(f"Check-in retry [{len(retry)} chars]: {retry[:300]}")
            # Re-parse the retry (but don't recurse again to avoid loops)
            retry_angel = re.findall(r'\[PARA_ANGEL\](.*?)\[/PARA_ANGEL\]', retry, re.DOTALL)
            retry_esp = re.findall(r'\[PARA_ESPECIALISTA\](.*?)\[/PARA_ESPECIALISTA\]', retry, re.DOTALL)
            if retry_angel or retry_esp:
                # Got tags on retry - route normally (not scheduled, to avoid another retry)
                await route_response(retry, source_chat_id, context, turn, scheduled=False)
            else:
                await trace_to_labestia("CHECK-IN (sin tags tras retry)", retry[:2000], context.bot)
        else:
            log.info(f"Response sin tags: {response[:200]}")
            await trace_to_labestia("GOBERNATOR → ANGEL (sin tags)", response[:2000], context.bot)
            await send_long_message(source_chat_id, response, context.bot)
        return

    # Send messages to Angel
    for msg in para_angel:
        if angel_chat:
            await send_long_message(angel_chat, msg.strip(), context.bot)

    # Trace Angel-bound messages to LaBestia (only when no specialist interaction)
    if para_angel and not para_especialista:
        combined = "\n---\n".join(m.strip() for m in para_angel)
        await trace_to_labestia("GOBERNATOR→ANGEL", combined, context.bot)

    # Invoke specialist and recurse for multi-turn
    for msg in para_especialista:
        instruction = msg.strip()
        current_turn = turn + 1

        # Check stop request from Angel
        if stop_requested:
            stop_requested = False
            stop_msg = f"Conversacion detenida en turno {turn} por orden de Angel."
            log.info(stop_msg)
            if angel_chat:
                await send_long_message(angel_chat, stop_msg, context.bot)
            await trace_to_labestia("PARADA", stop_msg, context.bot)
            return

        # Safety: max turns limit
        if current_turn > MAX_SPECIALIST_TURNS:
            limit_msg = (
                f"Limite de {MAX_SPECIALIST_TURNS} turnos alcanzado. "
                f"Conversacion detenida."
            )
            log.warning(limit_msg)
            if angel_chat:
                await send_long_message(angel_chat, limit_msg, context.bot)
            await trace_to_labestia("LIMITE TURNOS", limit_msg, context.bot)
            return

        specialist_turn = current_turn
        log.info(f"Specialist turn {current_turn}: [{len(instruction)} chars]")

        try:
            specialist_response = await run_specialist_claude(instruction)
            await post_to_labestia(
                instruction, specialist_response, context.bot, current_turn
            )

            # Feed response back to gobernator for processing
            followup = (
                f"[RESPUESTA DEL ESPECIALISTA - Turno {current_turn}]\n"
                f"Le dijiste: {instruction[:300]}\n"
                f"Respondio: {specialist_response}\n\n"
                f"Procesa esta respuesta.\n"
                f"- Si hay algo relevante para Angel: [PARA_ANGEL]texto[/PARA_ANGEL]\n"
                f"- Si necesitas seguir hablando: [PARA_ESPECIALISTA]texto[/PARA_ESPECIALISTA]\n"
                f"- Puedes usar ambos tags.\n"
                f"- Si la conversacion termino, solo [PARA_ANGEL] con resumen."
            )
            gobernator_response = await run_claude(followup, use_continue=True)
            log.info(f"Gobernator followup response [{len(gobernator_response)} chars]: {gobernator_response[:300]}")
            await route_response(
                gobernator_response, source_chat_id, context, current_turn, scheduled
            )

        except SpecialistEmptyResponse as e:
            error_msg = (
                f"Especialista sin respuesta en turno {current_turn}. "
                f"Posible rate limit o error. Detalle: {e}"
            )
            log.warning(f"Specialist empty/rate-limited at turn {current_turn}: {e}")
            await trace_to_labestia("ERROR ESPECIALISTA", f"Instruccion: {instruction[:300]}\n\n{error_msg}", context.bot)
            if angel_chat:
                await send_long_message(angel_chat, error_msg, context.bot)
        except subprocess.TimeoutExpired:
            error_msg = (
                f"Especialista timeout en turno {current_turn} ({SPECIALIST_TIMEOUT//60}min). "
                f"Posible rate limit."
            )
            log.error(f"Specialist timeout at turn {current_turn}")
            await trace_to_labestia("TIMEOUT ESPECIALISTA", f"Instruccion: {instruction[:300]}\n\n{error_msg}", context.bot)
            if angel_chat:
                await send_long_message(angel_chat, error_msg, context.bot)
        except Exception as e:
            error_msg = f"Error con especialista: {e}"
            log.error(error_msg)
            await trace_to_labestia("ERROR ESPECIALISTA", f"Instruccion: {instruction[:300]}\n\n{error_msg}", context.bot)
            if angel_chat:
                await send_long_message(angel_chat, error_msg, context.bot)


# --- Message handler ---

async def on_message(update, context):
    """Handle incoming text messages from Angel."""
    global busy, specialist_turn, new_session, stop_requested

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

    # Stop keywords - interrupt specialist conversation immediately
    if busy and text.lower().strip() in STOP_KEYWORDS:
        stop_requested = True
        await update.message.reply_text(
            "Parada solicitada. Termino el turno actual y paro."
        )
        return

    # If busy, queue Angel's message
    if busy:
        pending_angel_messages.append(text)
        turn_info = (
            f" (turno {specialist_turn} con el especialista)"
            if specialist_turn > 0 else ""
        )
        await update.message.reply_text(
            f"Ocupado{turn_info}. Mensaje en cola, te atiendo al terminar.\n"
            f"Sigue la conversacion en LaBestia.\n"
            f"Escribe 'para' para detener la conversacion."
        )
        return

    busy = True
    use_continue = not new_session
    new_session = False
    waiting = await update.message.reply_text("Procesando...")

    try:
        # Trace Angel's message to LaBestia
        await trace_to_labestia("ANGEL", text, context.bot)

        prompt = (
            f"[TELEGRAM - Mensaje de Angel]\n"
            f"{text}"
            f"{ROUTING_INSTRUCTIONS}"
        )
        response = await run_claude(prompt, use_continue)
        log.info(f"Gobernator raw response [{len(response)} chars]: {response[:300]}")
        await waiting.delete()
        await route_response(response, chat_id, context)

        # Process any messages Angel sent while we were busy
        while pending_angel_messages:
            queued = pending_angel_messages.copy()
            pending_angel_messages.clear()
            combined = "\n".join(f"- {m}" for m in queued)
            qprompt = (
                f"[TELEGRAM - Mensajes pendientes de Angel]\n"
                f"{combined}"
                f"{ROUTING_INSTRUCTIONS}"
            )
            qresponse = await run_claude(qprompt, use_continue=True)
            await route_response(qresponse, chat_id, context)

    except subprocess.TimeoutExpired:
        await waiting.edit_text("Timeout (10 min).")
        await trace_to_labestia("TIMEOUT GOBERNATOR", "Timeout procesando mensaje de Angel (10min)", context.bot)
    except Exception as e:
        await waiting.edit_text(f"Error: {e}")
        log.error(f"Error procesando mensaje: {e}")
        await trace_to_labestia("ERROR GOBERNATOR", str(e), context.bot)
    finally:
        busy = False
        specialist_turn = 0


# --- Photo handler ---

async def handle_image(update, context, file_obj, file_unique_id, file_ext="jpg"):
    """Common handler for images (photo or document). Downloads, saves, and passes to gobernator."""
    global busy, specialist_turn, new_session

    if update.effective_user.id != ANGEL_USER_ID:
        return

    chat_id = str(update.effective_chat.id)
    config = load_config()

    # Auto-save Angel's chat ID
    if config.get("angel_chat_id") != chat_id:
        config["angel_chat_id"] = chat_id
        save_config(config)

    caption = update.message.caption or ""

    if busy:
        pending_angel_messages.append(f"[Imagen enviada con caption: {caption or 'sin caption'}]")
        await update.message.reply_text(
            "Ocupado. Imagen en cola, te atiendo al terminar."
        )
        return

    busy = True
    use_continue = not new_session
    new_session = False
    waiting = await update.message.reply_text("Procesando imagen...")

    try:
        # Download the file
        file = await context.bot.get_file(file_obj.file_id)

        # Save to a temp file in our workdir
        img_dir = os.path.join(WORKDIR, "telegram", "incoming_images")
        os.makedirs(img_dir, exist_ok=True)
        img_path = os.path.join(img_dir, f"{file_unique_id}.{file_ext}")
        await file.download_to_drive(img_path)
        log.info(f"Image saved: {img_path}")

        # Trace to LaBestia
        caption_info = f" (caption: {caption})" if caption else ""
        await trace_to_labestia("ANGEL", f"[Imagen enviada{caption_info}]", context.bot)

        # Tell gobernator to read the image
        prompt = (
            f"[TELEGRAM - Imagen de Angel]\n"
            f"Angel ha enviado una imagen. Esta guardada en: {img_path}\n"
            f"Usa la herramienta Read para ver la imagen.\n"
            f"Caption: {caption or '(sin caption)'}\n"
            f"{ROUTING_INSTRUCTIONS}"
        )
        response = await run_claude(prompt, use_continue)
        log.info(f"Gobernator photo response [{len(response)} chars]: {response[:300]}")
        await waiting.delete()
        await route_response(response, chat_id, context)

    except Exception as e:
        await waiting.edit_text(f"Error procesando imagen: {e}")
        log.error(f"Error procesando imagen: {e}")
        await trace_to_labestia("ERROR IMAGEN", str(e), context.bot)
    finally:
        busy = False
        specialist_turn = 0


async def on_photo(update, context):
    """Handle compressed photos sent by Angel."""
    if not update.message or not update.message.photo:
        return
    log.info("on_photo triggered")
    photo = update.message.photo[-1]  # Last = highest res
    await handle_image(update, context, photo, photo.file_unique_id, "jpg")


async def on_document(update, context):
    """Handle documents sent by Angel - catches images sent as files (PNG screenshots etc)."""
    if not update.message or not update.message.document:
        return
    doc = update.message.document
    mime = doc.mime_type or ""
    log.info(f"on_document triggered: {doc.file_name} ({mime})")
    # Only handle image documents
    if not mime.startswith("image/"):
        log.info(f"Document is not an image ({mime}), ignoring")
        return
    # Extract extension from filename or mime
    ext = "jpg"
    if doc.file_name:
        ext = doc.file_name.rsplit(".", 1)[-1].lower() if "." in doc.file_name else "jpg"
    elif "png" in mime:
        ext = "png"
    await handle_image(update, context, doc, doc.file_unique_id, ext)


# --- Commands ---

async def on_nueva(update, context):
    if update.effective_user.id != ANGEL_USER_ID:
        return
    global new_session, gobernator_session_id, gobernator_session_started
    new_session = True
    gobernator_session_id = str(uuid.uuid4())
    gobernator_session_started = False
    await update.message.reply_text("Nueva sesion gobernator. El proximo mensaje arranca de cero.")


async def on_nueva_especialista(update, context):
    """Start a fresh session with the specialist."""
    if update.effective_user.id != ANGEL_USER_ID:
        return
    global specialist_new_session, specialist_session_id, specialist_session_started
    specialist_new_session = True
    specialist_session_id = str(uuid.uuid4())
    specialist_session_started = False
    await update.message.reply_text("Nueva sesion para el especialista.")


async def on_status(update, context):
    if update.effective_user.id != ANGEL_USER_ID:
        return
    config = load_config()
    status = (
        f"EN CONVERSACION (turno {specialist_turn})" if busy else "Libre"
    )
    pending = len(pending_angel_messages)
    await update.message.reply_text(
        f"Bot Gobernator activo\n"
        f"Estado: {status}\n"
        f"Mensajes en cola: {pending}\n"
        f"Max turnos: {MAX_SPECIALIST_TURNS}\n"
        f"Angel chat: {config.get('angel_chat_id', 'no')}\n"
        f"LaBestia: {config.get('specialist_chat_id', 'no')}\n"
        f"Gobernator session: {gobernator_session_id[:8]}...\n"
        f"Specialist session: {specialist_session_id[:8]}...\n"
        f"Modo: PRUEBA (check-in 15min, resumen 1h)"
    )


async def on_conectar(update, context):
    """Register current group as the LaBestia display group."""
    if update.effective_user.id != ANGEL_USER_ID:
        return
    config = load_config()
    chat_id = str(update.effective_chat.id)
    config["specialist_chat_id"] = chat_id
    save_config(config)
    log.info(f"LaBestia registered: {chat_id}")
    await update.message.reply_text(f"LaBestia registrado (chat ID: {chat_id}).")


async def on_resumen(update, context):
    if update.effective_user.id != ANGEL_USER_ID:
        return
    if busy:
        await update.message.reply_text(
            "Ocupado con el especialista. Intenta en unos minutos."
        )
        return
    waiting = await update.message.reply_text("Generando resumen...")
    try:
        response = await run_claude(
            "[TAREA - Resumen bajo demanda]\n"
            "Angel pide un resumen. Sin tags de enrutamiento.",
            use_continue=True
        )
        await waiting.delete()
        await send_long_message(
            str(update.effective_chat.id), response, context.bot
        )
    except Exception as e:
        await waiting.edit_text(f"Error: {e}")


# --- Scheduled tasks (TEST MODE) ---

async def specialist_checkin(context):
    """Every 15 min - Wake up and talk to the specialist (test mode)."""
    global busy, specialist_turn
    if busy:
        log.info("Busy, skipping 15-min check-in")
        return
    config = load_config()
    angel_chat = config.get("angel_chat_id")
    if not angel_chat:
        log.warning("No angel_chat_id, skipping check-in")
        return

    busy = True
    log.info("Check-in periodico con especialista...")
    try:
        response = await run_claude(
            "[TAREA PROGRAMADA - Check-in periodico]\n"
            "Es tu check-in periodico. Tu trabajo es gobernar al especialista.\n"
            "DEBES hablar con el especialista - decide que preguntarle, verificar o delegar.\n"
            "OBLIGATORIO usar [PARA_ESPECIALISTA]instruccion[/PARA_ESPECIALISTA] para hablarle.\n"
            "Si ademas quieres informar a Angel, usa tambien [PARA_ANGEL]texto[/PARA_ANGEL].\n"
            f"{ROUTING_INSTRUCTIONS}",
            use_continue=True
        )
        log.info(f"Check-in raw response [{len(response)} chars]: {response[:300]}")
        await route_response(response, angel_chat, context, scheduled=True)
    except Exception as e:
        log.error(f"Check-in error: {e}")
        await trace_to_labestia("ERROR CHECK-IN", str(e), context.bot)
    finally:
        busy = False
        specialist_turn = 0


async def test_summary(context):
    """Every 1 hour - Summary for Angel (test mode, simulating daily summary)."""
    global busy, specialist_turn
    if busy:
        log.info("Busy, deferring test summary")
        return
    config = load_config()
    chat_id = config.get("angel_chat_id")
    if not chat_id:
        return

    busy = True
    log.info("Resumen periodico...")
    try:
        response = await run_claude(
            "[TAREA PROGRAMADA - Resumen periodico para Angel]\n"
            "Genera un resumen para Angel. Sin tags de enrutamiento.",
            use_continue=True
        )
        await send_long_message(chat_id, response, context.bot)
        await trace_to_labestia("RESUMEN → ANGEL", response[:2000], context.bot)
    except Exception as e:
        log.error(f"Test summary error: {e}")
        await trace_to_labestia("ERROR RESUMEN", str(e), context.bot)
    finally:
        busy = False
        specialist_turn = 0


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

    # Scheduled tasks - TEST MODE
    # Check-in with specialist every 15 minutes (first after 1 min)
    app.job_queue.run_repeating(
        specialist_checkin,
        interval=timedelta(minutes=15),
        first=timedelta(minutes=1),
        name="specialist_checkin"
    )
    # Summary every hour (simulating daily summary)
    app.job_queue.run_repeating(
        test_summary,
        interval=timedelta(hours=1),
        first=timedelta(hours=1),
        name="test_summary"
    )

    log.info("Bot Gobernator iniciado - MODO PRUEBA")
    log.info(f"Gobernator session: {gobernator_session_id}")
    log.info(f"Specialist session: {specialist_session_id}")
    log.info("Check-in: cada 15 min | Resumen: cada 1 hora")
    app.run_polling()


if __name__ == "__main__":
    main()
