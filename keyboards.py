from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from data.up_actions import ACTIONS

def main_menu_kb(is_admin=False):
    buttons = [
        [KeyboardButton(text="Новый клиент")],
        [KeyboardButton(text="Добавить УП")],
        [KeyboardButton(text="Отчёт")]
    ]
    if is_admin:
        buttons.append([KeyboardButton(text="Отчёт по сотруднику")])
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

def action_kb():
    kb = []
    row = []
    for i, name in enumerate(ACTIONS):
        row.append(InlineKeyboardButton(text=name, callback_data=name))
        if len(row) == 2:
            kb.append(row)
            row = []
    if row:
        kb.append(row)
    return InlineKeyboardMarkup(inline_keyboard=kb)

def confirm_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Да", callback_data="yes"),
            InlineKeyboardButton(text="❌ Нет", callback_data="no")
        ]
    ])
