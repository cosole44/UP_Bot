import sqlite3

# Список операций, которые отображаются в отчёте
REPORT_ACTIONS = [
    "Вклад", "Детская карта", "ЗЛС", "КК", "Прайм", "СЗ", "ПК", "ПДС", "ОПС",
    "Сберправо", "Пенсия", "Бокс/бум", "Свое дело",
    "Мобайл", "Адафа", "Амана", "Осаго", "Открытие расчётного счета"
]

def get_user_report(user_id: int, date_from: str, date_to: str):
    conn = sqlite3.connect("up.db")
    cur = conn.cursor()

    # Получаем данные по операциям
    cur.execute("""
        SELECT action, COUNT(*), SUM(value)
        FROM entries
        WHERE user_id=? AND date BETWEEN ? AND ?
        GROUP BY action
    """, (user_id, date_from, date_to))
    results = cur.fetchall()

    # Получаем количество клиентов
    cur.execute("""
        SELECT SUM(clients)
        FROM clients_count
        WHERE user_id=? AND date BETWEEN ? AND ?
    """, (user_id, date_from, date_to))
    clients_total = cur.fetchone()[0] or 0
    conn.close()

    report_dict = {action: {'count': 0, 'value': 0} for action in REPORT_ACTIONS}
    for action, count, value_sum in results:
        if action in REPORT_ACTIONS:
            report_dict[action]['count'] = count
            report_dict[action]['value'] = value_sum

    # Итоговая сумма всех операций
    total_all = sum(value_sum for _, _, value_sum in results)

    # Формируем текст отчёта
    text = f"🧮 Итого: {total_all:.2f} УП\n"
    text += f"\n👥 Количество клиентов: {clients_total}\n\n"
    # Подробности по операциям
    for action, data in report_dict.items():
        text += f"{action} {data['count']}\n"

    # Заголовок теперь внизу
    if date_from == date_to:
        header = f"📊 Отчёт за {date_from}"
    else:
        header = f"📊 Отчёт с {date_from} по {date_to}"



    text += f"\n{header}"

    return text