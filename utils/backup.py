import asyncio
import pytz
from datetime import datetime, timedelta
from aiogram import Bot

BACKUP_FILE = "/home/oleg/UP_Bot/up.db"
ADMIN_ID = 723549701  # твой Telegram ID
TZ = pytz.timezone("Asia/Yekaterinburg")

async def daily_backup(bot: Bot):
    """
    Функция отправляет бэкап базы каждый день в 20:00 по Екатеринбургу
    """
    while True:
        now = datetime.now(TZ)
        # Целевое время сегодня 20:00
        target = now.replace(hour=20, minute=0, second=0, microsecond=0)
        if now > target:
            target += timedelta(days=1)  # если уже прошло 20:00, переносим на завтра
        wait_seconds = (target - now).total_seconds()
        await asyncio.sleep(wait_seconds)

        # Отправка файла администратору
        try:
            with open(BACKUP_FILE, "rb") as f:
                await bot.send_document(ADMIN_ID, f, caption=f"📦 Бэкап базы за {datetime.now(TZ).strftime('%Y-%m-%d')}")
        except Exception as e:
            print(f"Ошибка при отправке бэкапа: {e}")
