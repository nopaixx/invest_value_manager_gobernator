import asyncio
import subprocess
import logging
import os
import json
from datetime import time, timezone, timedelta

from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, MessageHandler, CommandHandler, filters

load_dotenv()

TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
ANGEL_USER_ID = int(os.environ.get("ANGEL_USER_ID", "998346625"))
WORKDIR = "/home/angel/invest_value_manager_gobernator"
CONFIG_FILE = os.path.join(WORKDIR, "telegram", "config.json")

# CET timezone (UTC+1, Spain winter)
CET = timezone(timedelta(hours=1))

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(message)s")
log = logging.getLogger("gobernator")

new_session = False
bot_username = None


def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE) as f:
            return json.load(f)
    return {}


def save_config(config):
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)


async def run_claude(msg, use_continue=True):
    cmd = ["claude", "-p", "--permission-mode", "bypassPermissions"]
    if use_continue:
        cmd.append("--continue")
    cmd.append(msg)

    log.info(f"Invocando Claude [{len(msg)} chars] continue={use_continue}")

    result = await asyncio.to_thread(
        subprocess.run, cmd,
        capture_output=True, text=True,
        cwd=WORKDIR, timeout=600
    )
    return result.stdout or result.stderr or "Sin respuesta"


async def send_long_message(chat_id, text, bot):
    if not text.strip():
        text = "Sin respuesta"
    for i in range(0, len(text), 4000):
        await bot.send_message(chat_id=chat_id, text=text[i:i + 4000])


async def send_response(update, text):
    if not text.strip():
        text = "Sin respuesta"
    for i in range(0, len(text), 4000):
        await update.message.reply_text(text[i:i + 4000])


async def on_message(update, context):
    if update.effective_user.id != ANGEL_USER_ID:
        return

    # Save chat ID for proactive messaging
    config = load_config()
    chat_id = str(update.effective_chat.id)
    if config.get("angel_chat_id") != chat_id:
        config["angel_chat_id"] = chat_id
        save_config(config)
        log.info(f"Chat ID de Angel guardado: {chat_id}")

    global new_session
    use_continue = not new_session
    new_session = False

    text = update.message.text or ""
    if bot_username:
        text = text.replace(f"@{bot_username}", "").strip()
    if not text:
        return

    waiting = await update.message.reply_text("Procesando...")

    prompt = f"[TELEGRAM - Mensaje de Angel]\nAngel dice: {text}"

    try:
        response = await run_claude(prompt, use_continue)
        await waiting.delete()
        await send_response(update, response)
    except subprocess.TimeoutExpired:
        await waiting.edit_text("Timeout (10 min). Intenta con algo mas corto.")
    except Exception as e:
        await waiting.edit_text(f"Error: {e}")
        log.error(f"Error procesando mensaje: {e}")


async def on_nueva(update, context):
    if update.effective_user.id != ANGEL_USER_ID:
        return
    global new_session
    new_session = True
    await update.message.reply_text("Nueva sesion. El proximo mensaje arranca de cero.")


async def on_status(update, context):
    if update.effective_user.id != ANGEL_USER_ID:
        return
    config = load_config()
    chat_id = config.get("angel_chat_id", "no configurado")
    await update.message.reply_text(
        f"Bot Gobernator activo.\n"
        f"Chat ID: {chat_id}\n"
        f"Resumen diario: 22:00 CET"
    )


async def on_resumen(update, context):
    if update.effective_user.id != ANGEL_USER_ID:
        return
    waiting = await update.message.reply_text("Generando resumen...")
    try:
        response = await run_claude(
            "[TAREA - Resumen bajo demanda]\n"
            "Angel pide un resumen. Lee los state files (state/), "
            "revisa el git log del especialista (invest_value_manager/), "
            "y genera un resumen conciso del estado actual.",
            use_continue=True
        )
        await waiting.delete()
        await send_response(update, response)
    except Exception as e:
        await waiting.edit_text(f"Error: {e}")


async def daily_summary(context):
    config = load_config()
    chat_id = config.get("angel_chat_id")
    if not chat_id:
        log.warning("No hay chat ID de Angel, saltando resumen diario")
        return

    log.info("Generando resumen diario...")
    try:
        response = await run_claude(
            "[TAREA PROGRAMADA - Resumen diario 22:00]\n"
            "Genera el resumen diario para Angel. Lee los state files (state/), "
            "revisa el git log del especialista (invest_value_manager/), "
            "y envia un resumen conciso con:\n"
            "1. Estado del portfolio (si hay datos)\n"
            "2. Que hizo el especialista hoy (git log)\n"
            "3. Alertas o problemas si los hay\n"
            "4. Ordenes pendientes de ejecutar en eToro (si las hay)\n"
            "Maximo 2-3 parrafos.",
            use_continue=True
        )
        await send_long_message(chat_id, response, context.bot)
    except Exception as e:
        log.error(f"Error en resumen diario: {e}")
        try:
            await context.bot.send_message(
                chat_id=chat_id,
                text=f"Error generando resumen diario: {e}"
            )
        except Exception:
            pass


async def post_init(application):
    global bot_username
    bot_info = await application.bot.get_me()
    bot_username = bot_info.username
    log.info(f"Bot username: @{bot_username}")


def main():
    app = Application.builder().token(TOKEN).build()
    app.post_init = post_init

    # Commands
    app.add_handler(CommandHandler("nueva", on_nueva))
    app.add_handler(CommandHandler("status", on_status))
    app.add_handler(CommandHandler("resumen", on_resumen))

    # Messages
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_message))

    # Daily summary at 22:00 CET
    app.job_queue.run_daily(
        daily_summary,
        time=time(hour=22, minute=0, tzinfo=CET),
        name="daily_summary"
    )

    log.info("Bot Gobernator iniciado. Esperando mensajes...")
    log.info("Resumen diario programado a las 22:00 CET")
    app.run_polling()


if __name__ == "__main__":
    main()
