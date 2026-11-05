import asyncio
import base64
import logging
import os
import threading
import time
import urllib.request
from http.server import BaseHTTPRequestHandler, HTTPServer
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("ultrabot")

# --- Веб-сервер для Render Web Service ---
PORT = int(os.environ.get("PORT", 10000))

class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.end_headers()
        self.wfile.write(b'{"status": "ok", "message": "UltraBot is running 24/7!"}')

    def do_HEAD(self):
        self.send_response(200)
        self.end_headers()

    def log_message(self, format, *args):
        # Скрываем частые HTTP-логи пингов, чтобы не засорять консоль
        logger.debug("HTTP: %s", format % args)

def run_http_server():
    server = HTTPServer(("0.0.0.0", PORT), SimpleHandler)
    logger.info(f"🌐 HTTP-сервер Render запущен на порту {PORT}")
    server.serve_forever()

# --- Механизм защиты от спячки (Anti-Sleep Keep-Alive) ---
def keep_alive_ping():
    """
    Фоновый пинг веб-сервиса каждые 10 минут.
    Бесплатные сервисы Render засыпают через 15 минут без входящих HTTP-запросов.
    Этот цикл делает GET-запрос к внешнему URL (RENDER_EXTERNAL_URL),
    сбрасывая таймер бездействия Render и сохраняя бота активным 24/7.
    """
    logger.info("⏳ Keep-Alive сервис инициализирован. Первый пинг через 30 секунд...")
    time.sleep(30)
    
    while True:
        url = os.environ.get("RENDER_EXTERNAL_URL") or os.environ.get("PING_URL")
        if url:
            if not url.startswith("http://") and not url.startswith("https://"):
                url = f"https://{url}"
            ping_url = f"{url.rstrip('/')}/health"
            try:
                req = urllib.request.Request(
                    ping_url,
                    headers={"User-Agent": "Render-KeepAlive-UltraBot/1.0"}
                )
                with urllib.request.urlopen(req, timeout=15) as resp:
                    logger.info(f"🟢 [Keep-Alive] Успешный пинг: {ping_url} (код {resp.status})")
            except Exception as e:
                logger.warning(f"⚠️ [Keep-Alive] Ошибка при пинге {ping_url}: {e}")
        else:
            logger.info("ℹ️ [Keep-Alive] Переменная RENDER_EXTERNAL_URL пока не установлена (на Render она добавляется автоматически).")
        
        # 10 минут интервал (600 секунд < 15 минут тайм-аута сна Render)
        time.sleep(600)

# --- Конфигурация ботов ---
DEFAULT_TOKEN_1 = base64.b64decode("OTIzNDA4MzM0MzpBQUZOMm9welV4dzJPRkVGelVsS1IwRktUWk82NUczLW1OVQ==").decode()
DEFAULT_TOKEN_2 = base64.b64decode("OTA5MDcxNjI0MDpBQUZSNlFJRERUUjRKalMyRmVEbC12ZndScXQ3c3VpbHJVOA==").decode()

BOT_TOKEN_1 = os.environ.get("BOT_TOKEN_1") or DEFAULT_TOKEN_1
SECOND_BOT_TOKEN = os.environ.get("SECOND_BOT_TOKEN") or DEFAULT_TOKEN_2

bot1 = Bot(token=BOT_TOKEN_1)
dp1 = Dispatcher()

bot2 = Bot(token=SECOND_BOT_TOKEN)
dp2 = Dispatcher()

# --- Контент сообщений ---
BOT_TEXT = (
    "⚠️ ПОМНИ ДРУЖИЩЕ: ВСЕ В ЭТОЙ СФЕРЕ СКАМ, ТОЛЬКО SAMPERLIFE ПЛАТИТ! ТО ЕСТЬ Я.\n\n"
    "Являюсь единственным честным скупом номер 1. В Telegram сделки НЕ ВЕДУ — здесь сплошной скам!\n"
    "Все переписки, сделки и выплаты веду строго через:\n"
    "• WhatsApp\n"
    "• Discord\n\n"
    "🎁 АКЦИЯ ДО 1 ЯНВАРЯ: Пригласи друга и получи 100 рублей за каждого!"
)

KEYBOARD = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="💬 Написать в WhatsApp", url="https://wa.me/79940602988")],
    [InlineKeyboardButton(text="🎮 Написать в Discord", url="https://discord.com/users/skup55")],
    [InlineKeyboardButton(text="▶️ YouTube (КЛИКНИ И УДОСТОВЕРЬСЯ САМ)", url="https://www.youtube.com/@SamperLife/featured")],
    [InlineKeyboardButton(text="🎵 TikTok (КЛИКНИ И УДОСТОВЕРЬСЯ САМ)", url="https://www.tiktok.com/@skupkapuskinskihcart")]
])

@dp1.message(CommandStart())
async def start_cmd_bot1(message: types.Message):
    await message.answer(BOT_TEXT, reply_markup=KEYBOARD)

@dp1.message()
async def any_msg_bot1(message: types.Message):
    await message.answer(BOT_TEXT, reply_markup=KEYBOARD)

@dp2.message(CommandStart())
async def start_cmd_bot2(message: types.Message):
    await message.answer(BOT_TEXT, reply_markup=KEYBOARD)

@dp2.message()
async def any_msg_bot2(message: types.Message):
    await message.answer(BOT_TEXT, reply_markup=KEYBOARD)

async def main():
    logger.info("🚀 Запуск Telegram ботов...")
    try:
        await bot1.delete_webhook(drop_pending_updates=True)
        await bot2.delete_webhook(drop_pending_updates=True)
        logger.info("✅ Вебхуки сброшены, обновления очищены.")
    except Exception as e:
        logger.error(f"Ошибка сброса вебхука: {e}")

    await asyncio.gather(
        dp1.start_polling(bot1),
        dp2.start_polling(bot2)
    )

if __name__ == "__main__":
    # Запуск фонового веб-сервера
    threading.Thread(target=run_http_server, daemon=True).start()
    
    # Запуск службы самопинга против сна
    threading.Thread(target=keep_alive_ping, daemon=True).start()

    # Запуск ботов
    asyncio.run(main())
