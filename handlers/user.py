from aiogram import Router, types, F
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime, timedelta
from utils.report import get_user_report
from data.up_actions import ACTIONS
from db import add_entry
import sqlite3
import re

router = Router()

# FSM состояния
class AddUP(StatesGroup):
    choosing_action = State()
    choosing_variant = State()  # для подвариантов
    confirming = State()

# Подварианты операций
VARIANT_ACTIONS = {
    "Мобайл": {
        "С переносом": 0.55,
        "Без переноса": 0.25
    },
    "Сберкарта": {
        "Моментальная": 0.2,
        "Именная": 0.05
    }
}


@router.message(F.text.lower() == "новый клиент")
async def new_client(message: types.Message):
    await message.delete()
    today = datetime.now().date().isoformat()
    user_id = message.from_user.id

    conn = sqlite3.connect("up.db")
    cur = conn.cursor()

    # Проверяем, есть ли запись на сегодня
    cur.execute("SELECT clients FROM clients_count WHERE user_id=? AND date=?", (user_id, today))
    res = cur.fetchone()

    if res:
        cur.execute("UPDATE clients_count SET clients = clients + 1 WHERE user_id=? AND date=?", (user_id, today))
    else:
        cur.execute("INSERT INTO clients_count (user_id, date, clients) VALUES (?, ?, 1)", (user_id, today))

    conn.commit()
    conn.close()
    await message.answer("✅ Новый клиент учтён.")

# Главное меню (в reply_keyboard)
@router.message(F.text.lower() == "добавить уп")
async def show_action_list(message: types.Message, state: FSMContext):
    await message.delete()
    await state.set_state(AddUP.choosing_action)

    # формируем кнопки в два столбца
    buttons = []
    action_list = list(ACTIONS.keys())
    for i in range(0, len(action_list), 2):
        row = [InlineKeyboardButton(text=action_list[i], callback_data=action_list[i])]
        if i + 1 < len(action_list):
            row.append(InlineKeyboardButton(text=action_list[i+1], callback_data=action_list[i+1]))
        buttons.append(row)

    kb = InlineKeyboardMarkup(inline_keyboard=buttons)
    await message.answer("Выбери операцию:", reply_markup=kb)


# Выбор действия
@router.callback_query(AddUP.choosing_action)
async def choose_action(callback: CallbackQuery, state: FSMContext):
    action = callback.data

    # Проверяем, есть ли подварианты
    if action in VARIANT_ACTIONS:
        await state.update_data(action=action)
        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text=name, callback_data=name)]
                for name in VARIANT_ACTIONS[action]
            ]
        )
        await state.set_state(AddUP.choosing_variant)
        await callback.message.edit_text(f"Выбери вариант для <b>{action}</b>:", reply_markup=kb)
        return

    # Если подвариантов нет, сразу к подтверждению
    value = ACTIONS[action]
    await state.update_data(action=action, value=value)
    await state.set_state(AddUP.confirming)
    kb_confirm = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Да", callback_data="yes"),
            InlineKeyboardButton(text="❌ Нет", callback_data="no")
        ]
    ])
    await callback.message.edit_text(f"Добавить операцию <b>{action}</b> (УП: {value})?", reply_markup=kb_confirm)

# Выбор подварианта
@router.callback_query(AddUP.choosing_variant)
async def choose_variant(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    action = data['action']
    variant = callback.data
    value = VARIANT_ACTIONS[action][variant]

    await state.update_data(value=value, variant=variant)
    await state.set_state(AddUP.confirming)

    kb_confirm = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Да", callback_data="yes"),
            InlineKeyboardButton(text="❌ Нет", callback_data="no")
        ]
    ])
    await callback.message.edit_text(
        f"Добавить операцию <b>{action}</b> ({variant}, УП: {value})?",
        reply_markup=kb_confirm
    )

# Подтверждение операции
@router.callback_query(AddUP.confirming, F.data.in_(['yes', 'no']))
async def confirm_action(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    if callback.data == 'yes':
        add_entry(
            user_id=callback.from_user.id,
            action=data['action'],
            value=data['value'],
            date=datetime.now().date().isoformat()
        )
        await callback.message.edit_text(f"✅ Добавлено: {data['action']} ({data['value']} УП)")
    else:
        await callback.message.edit_text("❌ Отменено.")
    await state.clear()

@router.message(F.text.lower() == "отчёт")
async def choose_report_period(message: types.Message):
    await message.delete()
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📅 Сегодня", callback_data="rep_today"),
            InlineKeyboardButton(text="🗓️ Неделя", callback_data="rep_week"),
            InlineKeyboardButton(text="📆 Месяц", callback_data="rep_month")
        ]
    ])
    await message.answer("Выбери период:", reply_markup=kb)

async def send_report(callback: CallbackQuery, start: str, end: str):
    user_id = callback.from_user.id
    report_text = get_user_report(user_id, start, end)

    # Кнопка "Обновить"
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Обновить", callback_data=f"refresh_report|{start}|{end}")]
    ])

    await callback.message.edit_text(report_text, reply_markup=kb)
    await callback.answer("Отчет получен! ✅ ")

@router.callback_query(F.data.startswith("rep_"))
async def handle_report(callback: CallbackQuery):
    today = datetime.now().date()
    data = callback.data

    if data == "rep_today":
        start, end = today, today
    elif data == "rep_week":
        start = today - timedelta(days=6)
        end = today
    elif data == "rep_month":
        start = today.replace(day=1)
        end = today
    else:
        await callback.answer("Ошибка")
        return

    await send_report(callback, str(start), str(end))

# Обработчик нажатия кнопки "Обновить"
@router.callback_query(F.data.startswith("refresh_report|"))
async def refresh_report_callback(callback: CallbackQuery):
    _, start, end = callback.data.split("|")
    await callback.answer("Обновлено ✅ ")
    await send_report(callback, start, end)

@router.message(F.text.regexp(r'^[+-]\d+(\.\d{1,2})?$'))
async def handle_manual_input(message: types.Message, state: FSMContext):
    # Игнорируем, если пользователь в состоянии FSM
    current_state = await state.get_state()
    if current_state is not None:
        return

    user_id = message.from_user.id
    text = message.text.strip()

    match = re.match(r'^([+-])(\d+(?:\.\d{1,2})?)$', text)
    if not match:
        return

    sign, number_str = match.groups()
    value = float(number_str)
    if sign == "-":
        value = -value

    date = datetime.now().date().isoformat()
    action_name = "Ручная корректировка"

    add_entry(user_id, action_name, value, date)
    await message.answer(f"✅ Добавлено {value:+.2f} УП в статистику.")
