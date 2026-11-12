import asyncio
import logging
import os
import sys
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiohttp import web

from config import BOT_TOKEN, validate_config
from handlers import router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [%(levelname)s] - %(name)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

async def handle_ping(request):
    """Render va Cron-Job uchun salomatlik tekshiruvi (Healthcheck)"""
    return web.Response(text="Bot is running 24/7!", status=200)

async def start_web_server():
    """Render Web Service talab qiladigan HTTP portni ochish"""
    port = int(os.getenv("PORT", "8080"))
    app = web.Application()
    app.router.add_get("/", handle_ping)
    app.router.add_get("/health", handle_ping)
    
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    logger.info(f"Render Web Server 0.0.0.0:{port} manzilida muvaffaqiyatli ishga tushdi.")

async def main():
    validate_config()
    
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=None)
    )
    dp = Dispatcher()
    dp.include_router(router)

    # Eski yangilanishlarni tozalash
    await bot.delete_webhook(drop_pending_updates=True)

    bot_info = await bot.get_me()
    logger.info(f"Bot muvaffaqiyatli ishga tushdi: @{bot_info.username}")
    logger.info("4-bosqich: Google Search, Model Fallback Pool, Audio Q&A, Admin Dashboard.")

    # Render uchun HTTP serverni ishga tushirish
    await start_web_server()

    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot to'xtatildi.")
