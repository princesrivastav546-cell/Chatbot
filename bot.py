import os
import logging
from threading import Thread
from flask import Flask

import google.generativeai as genai
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
PORT = int(os.environ.get("PORT", "10000"))

if not BOT_TOKEN:
    raise RuntimeError("Missing BOT_TOKEN env var")
if not GEMINI_API_KEY:
    raise RuntimeError("Missing GEMINI_API_KEY env var")

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

# ---- Flask (Render port bind) ----
app = Flask(__name__)

@app.get("/")
def home():
    return "OK - Free AI Telegram bot running"

def run_flask():
    app.run(host="0.0.0.0", port=PORT)

# ---- Telegram handlers ----
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hi! Send a message, I’ll reply using Gemini (free tier).")

async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (update.message.text or "").strip()
    if not text:
        return

    try:
        resp = model.generate_content(text)
        reply = (resp.text or "").strip() or "I couldn’t generate a reply."
        await update.message.reply_text(reply)
    except Exception as e:
        logging.exception("Gemini error")
        await update.message.reply_text(f"⚠️ Error: {e}")

def main():
    Thread(target=run_flask, daemon=True).start()

    tg = Application.builder().token(BOT_TOKEN).build()
    tg.add_handler(CommandHandler("start", start))
    tg.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))

    tg.run_polling()

if __name__ == "__main__":
    main()
