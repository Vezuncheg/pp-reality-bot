"""export.py — выгрузка БД в Excel"""
import io
from db import get_all_payments

def export_to_excel() -> bytes:
    import openpyxl
    from openpyxl.styles import Font, PatternFill, Alignment

    rows = get_all_payments()
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Оплаты"

    headers = ["#", "Имя", "Email", "Telegram ID", "Username",
               "Тариф", "Сумма ₽", "Дата оплаты", "Клуб до", "Статус"]

    header_fill = PatternFill("solid", fgColor="7C3AED")
    for col, h in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col, value=h)
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal="center")

    for row_idx, row in enumerate(rows, 2):
        for col_idx, val in enumerate(row, 1):
            ws.cell(row=row_idx, column=col_idx, value=val)

    widths = [5, 20, 25, 15, 15, 20, 10, 20, 20, 10]
    for col, w in enumerate(widths, 1):
        ws.column_dimensions[ws.cell(row=1, column=col).column_letter].width = w

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf.read()
