import os
import logging
import socket
from threading import Thread
from flask import Flask

from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

# ✅ New SDK (replaces google-generativeai)
from google import genai

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.environ.get("BOT_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# Render provides PORT. Locally you may not want to occupy 10000.
PORT = int(os.environ.get("PORT", "10000"))

if not BOT_TOKEN:
    raise RuntimeError("Missing BOT_TOKEN env var")
if not GEMINI_API_KEY:
    raise RuntimeError("Missing GEMINI_API_KEY env var")

client = genai.Client(api_key=GEMINI_API_KEY)

# ---- Flask (only to keep Render Web Service alive) ----
app = Flask(__name__)

@app.get("/")
def home():
    return "OK - Telegram Gemini bot running"

def _port_is_free(port: int) -> bool:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(("0.0.0.0", port))
        return True
    except OSError:
        return False

def run_flask():
    # On Render: must bind PORT
    # Locally: if PORT is busy, bind any free port instead (0)
    bind_port = PORT if _port_is_free(PORT) else 0
    try:
        app.run(host="0.0.0.0", port=bind_port)
    except Exception:
        # If Flask fails, the Telegram bot can still run (polling)
        logging.exception("Flask failed to start (non-fatal)")

# ---- Telegram handlers ----
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🤖 Free AI bot (Gemini). Send a message!")

async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (update.message.text or "").strip()
    if not text:
        return

    try:
        # ✅ Use model IDs shown in current docs (example: gemini-2.0-flash)
        resp = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=text,
        )
        reply = (resp.text or "").strip() or "No response generated."
        await update.message.reply_text(reply)
    except Exception as e:
        logging.exception("Gemini error")
        # Show real error once to debug quickly
        await update.message.reply_text(f"⚠️ Gemini error: {e}")

def main():
    Thread(target=run_flask, daemon=True).start()

    tg = Application.builder().token(BOT_TOKEN).build()
    tg.add_handler(CommandHandler("start", start))
    tg.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))
    tg.run_polling()

if __name__ == "__main__":
    main()
