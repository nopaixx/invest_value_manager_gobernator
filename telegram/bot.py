import asyncio
import subprocess
import logging
import os
import json
import re
from datetime import time, timezone, timedelta

from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, MessageHandler, CommandHandler, filters

load_dotenv()

TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
ANGEL_USER_ID = int(os.environ.get("ANGEL_USER_ID", "998346625"))
BOT_USER_ID = int(TOKEN.split(":")[0])
WORKDIR = "/home/angel/invest_value_manager_gobernator"
SPECIALIST_WORKDIR = os.path.join(WORKDIR, "invest_value_manager")
CONFIG_FILE = os.path.join(WORKDIR, "telegram", "config.json")
SPECIALIST_TIMEOUT = 300  # 5 min - if no response, likely rate limited

CET = timezone(timedelta(hours=1))

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(message)s")
log = logging.getLogger("gobernator")

# Session state
new_session = False
specialist_new_session = False
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
    cmd = ["claude", "-p", "--permission-mode", "bypassPermissions"]
    if use_continue:
        cmd.append("--continue")
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
    global specialist_new_session
    cmd = ["claude", "-p", "--permission-mode", "bypassPermissions"]
    if use_continue and not specialist_new_session:
        cmd.append("--continue")
    specialist_new_session = False
    cmd.append(msg)
    log.info(f"Especialista Claude [{len(msg)} chars]")

    result = await asyncio.to_thread(
        subprocess.run, cmd,
        capture_output=True, text=True,
        cwd=SPECIALIST_WORKDIR, timeout=SPECIALIST_TIMEOUT
    )
    output = clean_claude_output(result.stdout or result.stderr or "")
    if not output or "out of extra usage" in output.lower():
        raise SpecialistEmptyResponse(output or "Sin respuesta del especialista")
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
        f"GOBERNATOR{turn_label}:\n{instruction}\n\n"
        f"---\n\n"
        f"ESPECIALISTA:\n{response}"
    )
    await send_long_message(specialist_chat, display, bot)


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


async def route_response(response, source_chat_id, context, turn=0):
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

    # No tags -> send everything to source chat
    if not para_angel and not para_especialista:
        await send_long_message(source_chat_id, response, context.bot)
        return

    # Send messages to Angel
    for msg in para_angel:
        if angel_chat:
            await send_long_message(angel_chat, msg.strip(), context.bot)

    # Invoke specialist and recurse for multi-turn
    for msg in para_especialista:
        instruction = msg.strip()
        current_turn = turn + 1

        # Check stop request from Angel
        if stop_requested:
            stop_requested = False
            log.info(f"Stop requested at turn {current_turn}")
            if angel_chat:
                await send_long_message(
                    angel_chat,
                    f"Conversacion detenida en turno {turn} por tu orden.",
                    context.bot
                )
            return

        # Safety: max turns limit
        if current_turn > MAX_SPECIALIST_TURNS:
            log.warning(f"Max turns ({MAX_SPECIALIST_TURNS}) reached, stopping")
            if angel_chat:
                await send_long_message(
                    angel_chat,
                    f"Limite de {MAX_SPECIALIST_TURNS} turnos alcanzado. "
                    f"Conversacion detenida.",
                    context.bot
                )
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
            await route_response(
                gobernator_response, source_chat_id, context, current_turn
            )

        except SpecialistEmptyResponse as e:
            log.warning(f"Specialist empty/rate-limited at turn {current_turn}: {e}")
            if angel_chat:
                await send_long_message(
                    angel_chat,
                    f"Especialista sin respuesta en turno {current_turn}. "
                    f"Posible rate limit o error. Detalle: {e}",
                    context.bot
                )
        except subprocess.TimeoutExpired:
            log.error(f"Specialist timeout at turn {current_turn}")
            if angel_chat:
                await send_long_message(
                    angel_chat,
                    f"Especialista timeout en turno {current_turn} ({SPECIALIST_TIMEOUT//60}min). "
                    f"Posible rate limit.",
                    context.bot
                )
        except Exception as e:
            log.error(f"Specialist error: {e}")
            if angel_chat:
                await send_long_message(
                    angel_chat, f"Error con especialista: {e}", context.bot
                )


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
        prompt = (
            f"[TELEGRAM - Mensaje de Angel]\n"
            f"{text}"
            f"{ROUTING_INSTRUCTIONS}"
        )
        response = await run_claude(prompt, use_continue)
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
    except Exception as e:
        await waiting.edit_text(f"Error: {e}")
        log.error(f"Error procesando mensaje: {e}")
    finally:
        busy = False
        specialist_turn = 0


# --- Commands ---

async def on_nueva(update, context):
    if update.effective_user.id != ANGEL_USER_ID:
        return
    global new_session
    new_session = True
    await update.message.reply_text("Nueva sesion. El proximo mensaje arranca de cero.")


async def on_nueva_especialista(update, context):
    """Start a fresh session with the specialist."""
    if update.effective_user.id != ANGEL_USER_ID:
        return
    global specialist_new_session
    specialist_new_session = True
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
            "[TAREA PROGRAMADA - Check-in periodico con el especialista]\n"
            "Es tu check-in periodico. Decide que hablar con el especialista.\n"
            f"{ROUTING_INSTRUCTIONS}",
            use_continue=True
        )
        await route_response(response, angel_chat, context)
    except Exception as e:
        log.error(f"Check-in error: {e}")
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
    except Exception as e:
        log.error(f"Test summary error: {e}")
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
    log.info("Check-in: cada 15 min | Resumen: cada 1 hora")
    app.run_polling()


if __name__ == "__main__":
    main()
