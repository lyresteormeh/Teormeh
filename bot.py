"""
ТеорМех Бот — Telegram Mini App + Anthropic Proxy
Railway 24/7 | Claude Opus
"""

import os
import time
import threading
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
PORT          = int(os.environ.get("PORT", 8080))

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не задан!")
if not MINI_APP_URL:
    raise ValueError("MINI_APP_URL не задан!")

# ── FLASK + PROXY ──────────────────────────────────────────
app = Flask(__name__)
CORS(app, origins="*")


@app.route("/health")
def health():
    key_ok = "✅ задан" if ANTHROPIC_KEY else "❌ НЕ ЗАДАН"
    return jsonify({"status": "ok", "bot": "ТеорМех", "api_key": key_ok})


@app.route("/proxy/anthropic", methods=["POST", "OPTIONS"])
def proxy_anthropic():
    if request.method == "OPTIONS":
        return jsonify({}), 200

    if not ANTHROPIC_KEY:
        return jsonify({"error": {"message": "ANTHROPIC_API_KEY не задан в Railway Variables"}}), 400

    try:
        resp = requests.post(
            "https://api.anthropic.com/v1/messages",
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


# ── TELEGRAM BOT ───────────────────────────────────────────
bot = telebot.TeleBot(BOT_TOKEN, threaded=False)


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
        "Загрузи фото задачи или введи условие — решу пошагово, нарисую схему и проверю ответ.\n\n"
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
        "2. Введи условие или загрузи фото задачи\n"
        "3. Выбери режим: Решить / Проверить / Схема\n"
        "4. Получи пошаговое решение + Canvas-схему + самопроверку\n\n"
        "/start — главное меню\n"
        "/app — открыть приложение",
        parse_mode="Markdown",
        reply_markup=main_kb(),
    )


@bot.message_handler(content_types=["text", "photo", "document"])
def handle_any(message):
    bot.send_message(
        message.chat.id,
        "👇 Открой приложение для решения задачи:",
        reply_markup=main_kb(),
    )


def setup_menu_button():
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


def run_bot():
    print("🤖 Запуск Telegram бота...")
    setup_menu_button()
    while True:
        try:
            print("⏳ Polling started...")
            bot.polling(none_stop=True, interval=2, timeout=30)
        except telebot.apihelper.ApiTelegramException as e:
            if "409" in str(e):
                print("⚠️ 409 Conflict — жду 15 сек...")
                time.sleep(15)
            else:
                print(f"❌ Telegram ошибка: {e}")
                time.sleep(5)
        except Exception as e:
            print(f"❌ Ошибка: {e}")
            time.sleep(5)


# ── СТАРТ ──────────────────────────────────────────────────
if __name__ == "__main__":
    print(f"🚀 ТеорМех стартует на порту {PORT}")
    print(f"📱 Mini App: {MINI_APP_URL}")
    print(f"🔑 Anthropic key: {'✅ задан' if ANTHROPIC_KEY else '❌ НЕ ЗАДАН'}")
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
    app.run(host="0.0.0.0", port=PORT)
