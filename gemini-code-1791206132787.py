import os
import re
import threading
from flask import Flask
import requests
from telegram import Update
from telegram.ext import Application, ContextTypes, MessageHandler, filters

app = Flask(__name__)

# Variáveis carregadas do painel do Render
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
EVOLUTION_API_URL = os.getenv("EVOLUTION_API_URL")
EVOLUTION_API_KEY = os.getenv("EVOLUTION_API_KEY")
INSTANCE_NAME = os.getenv("INSTANCE_NAME")
WHATSAPP_GROUP_ID = os.getenv("WHATSAPP_GROUP_ID")
SHOPEE_SUBID = os.getenv("SHOPEE_SUBID")


@app.route("/")
def health_check():
    return "Bot de ofertas ativo!", 200


def convert_shopee_link(text: str) -> str:
    pattern = r"(https?://[^\s]*(?:shopee\.com\.br|shope\.ee)[^\s]*)"

    def replace_link(match):
        url = match.group(0)
        separator = "&" if "?" in url else "?"
        return f"{url}{separator}sub_id={SHOPEE_SUBID}"

    return re.sub(pattern, replace_link, text)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.channel_post or update.message
    if not msg or not msg.text:
        return

    text_content = convert_shopee_link(msg.text)
    endpoint = f"{EVOLUTION_API_URL}/message/sendText/{INSTANCE_NAME}"
    headers = {
        "apikey": EVOLUTION_API_KEY,
        "Content-Type": "application/json",
    }
    payload = {
        "number": WHATSAPP_GROUP_ID,
        "options": {"delay": 1200, "presence": "composing"},
        "textMessage": {"text": text_content},
    }

    try:
        requests.post(endpoint, json=payload, headers=headers, timeout=10)
    except Exception as e:
        print(f"Erro no disparo para o WhatsApp: {e}")


def run_bot():
    telegram_app = (
        Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    )
    telegram_app.add_handler(
        MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message)
    )
    telegram_app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    threading.Thread(target=run_bot, daemon=True).start()
    port = int(os.getenv("PORT", 10000))
    app.run(host="0.0.0.0", port=port)