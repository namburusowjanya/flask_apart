from app import db
from app.models import MaintenanceBill, Payment, Expense
from sqlalchemy import func
from datetime import datetime
from flask import send_file
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
import io
from app.models import FinancialReport, Payment, Expense
from datetime import datetime
from sqlalchemy import extract
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

# def generate_expense_pdf():
#     buffer = io.BytesIO()
#     doc = SimpleDocTemplate(buffer, pagesize=letter)
#     data = [['Date', 'Vendor', 'Category', 'Amount', 'Description']]

#     expenses = Expense.query.all()
#     for exp in expenses:
#         data.append([
#             exp.date.strftime('%Y-%m-%d'),
#             exp.vendor,
#             exp.category,
#             f"₹{exp.amount:.2f}",
#             exp.description or ""
#         ])

#     table = Table(data)
#     table.setStyle(TableStyle([
#         ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
#         ('GRID', (0, 0), (-1, -1), 1, colors.black),
#         ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold')
#     ]))

#     doc.build([table])
#     buffer.seek(0)
#     return buffer
def generate_monthly_financial_report(month):
    """Generate or update the financial report for a given month (format: YYYY-MM)"""
    year, month_num = map(int, month.split("-"))

    # Total Maintenance Income
    total_income = db.session.query(
        db.func.sum(Payment.amount)
    ).join(Payment.bill_id).filter(
        extract('year', Payment.payment_date) == year,
        extract('month', Payment.payment_date) == month_num
    ).scalar() or 0.0

    # Total Expenses
    total_expenses = db.session.query(
        db.func.sum(Expense.amount)
    ).filter(
        extract('year', Expense.date) == year,
        extract('month', Expense.date) == month_num
    ).scalar() or 0.0

    # Get opening balance from previous month
    previous_month_obj = datetime(year, month_num, 1) - timedelta(days=1)
    prev_month = previous_month_obj.strftime('%Y-%m')

    previous_report = FinancialReport.query.filter_by(month=prev_month).first()
    opening_balance = previous_report.closing_balance if previous_report else 0.0

    closing_balance = opening_balance + total_income - total_expenses

    # Check if already exists
    report = FinancialReport.query.filter_by(month=month).first()
    if not report:
        report = FinancialReport(month=month)

    report.opening_balance = opening_balance
    report.total_income = total_income
    report.total_expenses = total_expenses
    report.closing_balance = closing_balance

    db.session.add(report)
    db.session.commit()

    return report
