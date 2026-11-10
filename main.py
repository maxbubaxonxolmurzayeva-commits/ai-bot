import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart

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

async def main():
    logging.basicConfig(level=logging.INFO)
    print("Bot muvaffaqiyatli ishga tushdi va xabarlarni kutmoqda...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
