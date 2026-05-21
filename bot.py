"""
ТеорМех Бот — Webhook режим (без 409)
Railway 24/7 | Claude Opus
"""

import os
import requests
import telebot
from flask import Flask, request, jsonify
from flask_cors import CORS
from telebot.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    MenuButtonWebApp,
    WebAppInfo,
)

# ── НАСТРОЙКИ ──────────────────────────────────────────────
BOT_TOKEN     = os.environ.get("BOT_TOKEN", "")
MINI_APP_URL  = os.environ.get("MINI_APP_URL", "")
ANTHROPIC_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
RAILWAY_URL   = os.environ.get("RAILWAY_PUBLIC_DOMAIN", "")
PORT          = int(os.environ.get("PORT", 8080))

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не задан!")
if not MINI_APP_URL:
    raise ValueError("MINI_APP_URL не задан!")

WEBHOOK_PATH = f"/webhook/{BOT_TOKEN}"
WEBHOOK_URL  = f"https://{RAILWAY_URL}{WEBHOOK_PATH}" if RAILWAY_URL else ""

# ── FLASK ──────────────────────────────────────────────────
app = Flask(__name__)
CORS(app, origins="*")

bot = telebot.TeleBot(BOT_TOKEN)


# ── WEBHOOK ENDPOINT ───────────────────────────────────────
@app.route(WEBHOOK_PATH, methods=["POST"])
def webhook():
    if request.headers.get("content-type") == "application/json":
        update = telebot.types.Update.de_json(request.get_data(as_text=True))
        bot.process_new_updates([update])
        return jsonify({"ok": True})
    return jsonify({"error": "bad request"}), 400


# ── HEALTH ─────────────────────────────────────────────────
@app.route("/health")
def health():
    return jsonify({
        "status": "ok",
        "mode": "webhook",
        "webhook_url": WEBHOOK_URL,
        "api_key": "✅ задан" if ANTHROPIC_KEY else "❌ НЕ ЗАДАН"
    })


# ── ANTHROPIC PROXY ────────────────────────────────────────
@app.route("/proxy/anthropic", methods=["POST", "OPTIONS"])
def proxy_anthropic():
    if request.method == "OPTIONS":
        return jsonify({}), 200
    if not ANTHROPIC_KEY:
        return jsonify({"error": {"message": "ANTHROPIC_API_KEY не задан"}}), 400
    try:
        resp = requests.post(
            "https://aiprimetech.io/v1/messages",
            headers={
                "Content-Type": "application/json",
                "x-api-key": ANTHROPIC_KEY,
                "anthropic-version": "2023-06-01",
            },
            json=request.get_json(),
            timeout=120,
        )
        return jsonify(resp.json()), resp.status_code
    except Exception as e:
        return jsonify({"error": {"message": str(e)}}), 500


# ── BOT HANDLERS ───────────────────────────────────────────
def main_kb():
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton(
        text="⚙️ Открыть ТеорМех Бот",
        web_app=WebAppInfo(url=MINI_APP_URL),
    ))
    return markup


@bot.message_handler(commands=["start"])
def cmd_start(message):
    name = message.from_user.first_name or "студент"
    bot.send_message(
        message.chat.id,
        f"👋 Привет, {name}!\n\n"
        "Я решаю задачи по *теоретической механике*:\n"
        "• 📐 Статика — равновесие, фермы, рамы\n"
        "• 🔄 Кинематика — скорости, ускорения, МЦС\n"
        "• 💥 Динамика — уравнения движения, энергия\n\n"
        "Загрузи фото задачи или введи условие.\n\n"
        "👇 Нажми кнопку:",
        parse_mode="Markdown",
        reply_markup=main_kb(),
    )


@bot.message_handler(commands=["app"])
def cmd_app(message):
    bot.send_message(message.chat.id, "⚙️ Открывай:", reply_markup=main_kb())


@bot.message_handler(commands=["help"])
def cmd_help(message):
    bot.send_message(
        message.chat.id,
        "📚 *Как пользоваться:*\n\n"
        "1. Нажми *Открыть ТеорМех Бот*\n"
        "2. Введи условие или загрузи фото\n"
        "3. Выбери режим: Решить / Проверить / Схема\n"
        "4. Получи решение + схему + самопроверку\n\n"
        "/start — главное меню",
        parse_mode="Markdown",
        reply_markup=main_kb(),
    )


@bot.message_handler(content_types=["text", "photo", "document"])
def handle_any(message):
    bot.send_message(
        message.chat.id,
        "👇 Открой приложение:",
        reply_markup=main_kb(),
    )


# ── СТАРТ ──────────────────────────────────────────────────
def setup():
    """Устанавливает webhook и кнопку меню"""
    if WEBHOOK_URL:
        # Удаляем старый webhook/polling
        bot.delete_webhook(drop_pending_updates=True)
        # Устанавливаем новый webhook
        bot.set_webhook(url=WEBHOOK_URL)
        print(f"✅ Webhook установлен: {WEBHOOK_URL}")
    else:
        print("⚠️ RAILWAY_PUBLIC_DOMAIN не задан — webhook не установлен")

    try:
        bot.set_chat_menu_button(
            menu_button=MenuButtonWebApp(
                text="⚙️ ТеорМех",
                web_app=WebAppInfo(url=MINI_APP_URL),
            )
        )
        print("✅ Кнопка меню установлена")
    except Exception as e:
        print(f"⚠️ Кнопка меню: {e}")


if __name__ == "__main__":
    print(f"🚀 ТеорМех webhook-режим, порт {PORT}")
    print(f"📱 Mini App: {MINI_APP_URL}")
    print(f"🔑 API key: {'✅' if ANTHROPIC_KEY else '❌'}")
    setup()
    app.run(host="0.0.0.0", port=PORT)
