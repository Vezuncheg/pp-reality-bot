"""
export.py — команда /export для выгрузки БД в Excel
Подключается к bot.py
"""
import sqlite3
import io
import os
from datetime import datetime

DB_PATH = "/app/payments.db"

def export_to_excel() -> bytes:
    """Выгружает payments в Excel и возвращает байты файла"""
    import openpyxl
    from openpyxl.styles import Font, PatternFill, Alignment

    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute("""
        SELECT id, name, email, tg_id, tg_username, plan_name,
               amount, paid_at, club_until, status
        FROM payments ORDER BY paid_at DESC
    """).fetchall()
    conn.close()

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Оплаты"

    headers = ["#", "Имя", "Email", "Telegram ID", "Username",
               "Тариф", "Сумма ₽", "Дата оплаты", "Клуб до", "Статус"]

    # Заголовки
    header_fill = PatternFill("solid", fgColor="7C3AED")
    for col, h in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col, value=h)
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal="center")

    # Данные
    for row_idx, row in enumerate(rows, 2):
        for col_idx, val in enumerate(row, 1):
            ws.cell(row=row_idx, column=col_idx, value=val)

    # Ширина колонок
    widths = [5, 20, 25, 15, 15, 20, 10, 20, 20, 10]
    for col, w in enumerate(widths, 1):
        ws.column_dimensions[ws.cell(row=1, column=col).column_letter].width = w

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf.read()
