import os
import logging
from threading import Thread
from flask import Flask

import google.generativeai as genai
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)

logging.basicConfig(level=logging.INFO)

# ---------- ENV ----------
BOT_TOKEN = os.environ.get("BOT_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
PORT = int(os.environ.get("PORT", "10000"))

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN missing")
if not GEMINI_API_KEY:
    raise RuntimeError("GEMINI_API_KEY missing")

# ---------- GEMINI ----------
genai.configure(api_key=GEMINI_API_KEY)

# ✅ FREE + WORKING MODEL
model = genai.GenerativeModel("gemini-1.5-flash-latest")

# ---------- FLASK (Render port binding) ----------
app = Flask(__name__)

@app.route("/")
def home():
    return "Telegram Gemini bot is running"

def run_flask():
    app.run(host="0.0.0.0", port=PORT)

# ---------- TELEGRAM ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 Free AI Bot (Gemini)\n\nJust send a message!"
    )

async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    if not user_text:
        return

    try:
        response = model.generate_content(user_text)
        reply = response.text or "No response generated."
        await update.message.reply_text(reply)
    except Exception as e:
        logging.exception("Gemini error")
        await update.message.reply_text("⚠️ AI error, try again later.")

def main():
    Thread(target=run_flask, daemon=True).start()

    app_tg = Application.builder().token(BOT_TOKEN).build()
    app_tg.add_handler(CommandHandler("start", start))
    app_tg.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))

    app_tg.run_polling()

if __name__ == "__main__":
    main()
