from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
import os
from db import get_all_users, get_user_name
from utils.report import get_user_report
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

ADMIN_IDS = [int(x) for x in os.getenv("ADMIN_IDS").split(",")]

router = Router()

# Шаг 1: выбор сотрудника
@router.message(F.text.lower() == "отчёт по сотруднику")
async def show_user_list(message):
    await message.delete()
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("⛔ У тебя нет прав.")
        return

    users = get_all_users()
    buttons = [
        [InlineKeyboardButton(text=u[2], callback_data=f"admin_user_{u[0]}")]
        for u in users
    ]
    kb = InlineKeyboardMarkup(inline_keyboard=buttons)
    await message.answer("👤 Выбери сотрудника:", reply_markup=kb)

# Шаг 2: выбор периода
@router.callback_query(F.data.startswith("admin_user_"))
async def choose_period(callback: CallbackQuery):
    user_id = callback.data.replace("admin_user_", "")
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📅 Сегодня", callback_data=f"adminrep_{user_id}_today"),
            InlineKeyboardButton(text="🗓️ Неделя", callback_data=f"adminrep_{user_id}_week"),
            InlineKeyboardButton(text="📆 Месяц", callback_data=f"adminrep_{user_id}_month")
        ]
    ])
    full_name = get_user_name(int(user_id))
    await callback.message.edit_text(f"📊 Период отчёта для {full_name}:", reply_markup=kb)

# Шаг 3: показ отчёта
@router.callback_query(F.data.startswith("adminrep_"))
async def show_user_report(callback: CallbackQuery):
    parts = callback.data.split("_")  # adminrep_<user_id>_<period>
    user_id = int(parts[1])
    period = parts[2]

    today = datetime.now().date()
    if period == "today":
        start, end = today, today
    elif period == "week":
        start = today - timedelta(days=6)
        end = today
    elif period == "month":
        start = today.replace(day=1)
        end = today
    else:
        await callback.answer("❌ Неизвестный период")
        return

    # Получаем отчёт
    report = get_user_report(user_id, str(start), str(end))
    full_name = get_user_name(user_id)
    await callback.message.edit_text(f"📄 Отчёт по сотруднику {full_name}:\n\n{report}")
