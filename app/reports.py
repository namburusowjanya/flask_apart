from app import db
from app.models import MaintenanceBill, Payment, Expense
from sqlalchemy import func
from datetime import datetime
from flask import send_file
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
import io

def get_defaulters():
    defaulters = []
    bills = MaintenanceBill.query.filter_by(status='Pending').all()
    for bill in bills:
        due_date = datetime.strptime(bill.month + '-15', '%Y-%m-%d')
        days_late = (datetime.today() - due_date).days
        if days_late > 0:
            defaulters.append({
                "flat_id": bill.flat_id,
                "owner": bill.flat.owner_name,
                "amount_due": bill.base_amount + bill.late_fee,
                "days_late": days_late
            })
    return defaulters

def lock_month(month):
    # Placeholder for month locking logic (e.g., set a flag or archive data)
    return f"Month {month} is now locked for editing."

def generate_expense_pdf():
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    data = [['Date', 'Vendor', 'Category', 'Amount', 'Description']]

    expenses = Expense.query.all()
    for exp in expenses:
        data.append([
            exp.date.strftime('%Y-%m-%d'),
            exp.vendor,
            exp.category,
            f"₹{exp.amount:.2f}",
            exp.description or ""
        ])

    table = Table(data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold')
    ]))

    doc.build([table])
    buffer.seek(0)
    return buffer