import asyncio
from utils.backup import daily_backup
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import Message
from aiogram.client.default import DefaultBotProperties
from handlers import user
from keyboards import main_menu_kb
from db import init_db, add_user
from handlers import admin
from dotenv import load_dotenv
import os

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_IDS = [int(x.strip()) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip()]
# ✅ Передаём parse_mode правильно
bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)
dp = Dispatcher()
dp.include_router(user.router)
dp.include_router(admin.router)

@dp.message(CommandStart())
async def start_handler(message: Message):
    user_id = message.from_user.id
    username = message.from_user.username
    full_name = f"{message.from_user.first_name or ''} {message.from_user.last_name or ''}".strip()
    is_admin = user_id in ADMIN_IDS

    add_user(user_id, username, full_name, is_admin)

    await message.answer(
        f"👋 Привет, {full_name}!\n"
        f"Бот готов к работе!",
        reply_markup=main_menu_kb(is_admin)
    )

async def main():
    init_db()
    asyncio.create_task(daily_backup(bot))
    try:
        print("Бот запущен. Нажмите Ctrl+C для остановки.")
        await dp.start_polling(bot)
    except (KeyboardInterrupt, SystemExit):
        print("Бот остановлен вручную.")
    except asyncio.CancelledError:
        # Игнорируем CancelledError при shutdown
        pass
    finally:
        await bot.session.close()
        print("Сессия бота закрыта.")


if __name__ == "__main__":
    asyncio.run(main())

