import asyncio
import logging
import os
import aiohttp
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiohttp import web

# Bot kaliti (Token) - Muhit o'zgaruvchisidan yoki to'g'ridan-to'g'ri olinadi
BOT_TOKEN = os.getenv("BOT_TOKEN", "8740002148:AAFKrFZvJ__pR3Phgw19-7T4BargIsV8IBs")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

@dp.message(CommandStart())
async def handle_start(message: types.Message):
    # Foydalanuvchida username bormi yo'qmi tekshiramiz
    if message.from_user and message.from_user.username:
        response_text = f"Assalomu alekum, @{message.from_user.username}"
    else:
        response_text = "Assalomu alekum, hurmatli mijoz"

    await message.answer(response_text)

async def health_check(request):
    return web.Response(text="Bot muvaffaqiyatli ishlamoqda!")

async def start_web_server():
    port = int(os.getenv("PORT", 8080))
    app = web.Application()
    app.router.add_get("/", health_check)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    logging.info(f"Web server {port}-portda ishga tushdi.")

async def keep_alive():
    """Render bepul tarifida bot uxlab qolmasligi uchun o'z-o'ziga so'rov yuborib turadi."""
    external_url = os.getenv("RENDER_EXTERNAL_URL")
    if not external_url:
        return
    
    logging.info(f"Render Keep-Alive faollashdi: {external_url}")
    await asyncio.sleep(60)
    
    async with aiohttp.ClientSession() as session:
        while True:
            try:
                async with session.get(external_url) as resp:
                    logging.info(f"Keep-alive ping muvaffaqiyatli: {resp.status}")
            except Exception as e:
                logging.warning(f"Keep-alive ping xatosi: {e}")
            await asyncio.sleep(600)

async def main():
    logging.basicConfig(level=logging.INFO)
    
    # Render bepul Web Service port tekshiruvidan o'tishi uchun veb-server va keep-alive
    if os.getenv("PORT"):
        await start_web_server()
        asyncio.create_task(keep_alive())

    print("Bot muvaffaqiyatli ishga tushdi va xabarlarni kutmoqda...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
