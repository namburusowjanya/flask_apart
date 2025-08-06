from datetime import datetime, timedelta
from app import db
from app.models import MaintenanceBill,FinancialReport,Payment, Expense
from app.utils import notify_late_payment
from sqlalchemy import func
from datetime import datetime, timedelta

def apply_late_fees():
    """Apply 2% late fee if unpaid after 15th of the month"""
    today = datetime.today()
    current_month = today.strftime('%Y-%m')

    bills = MaintenanceBill.query.filter_by(month=current_month, status='Pending').all()
    for bill in bills:
        bill_due_date = datetime.strptime(current_month + '-15', '%Y-%m-%d')
        if today > bill_due_date:
            total_due = bill.base_amount + bill.late_fee
            total_paid = sum(p.amount for p in bill.payments)
            if total_paid < total_due:
                penalty = bill.base_amount * 0.02
                bill.late_fee = round(penalty, 2)
                db.session.add(bill)
                notify_late_payment(bill.flat.contact, bill.flat.owner_name, penalty)
    db.session.commit()

def generate_monthly_report():
    today = datetime.today()
    current_month = today.strftime('%Y-%m')
    prev_month = (today.replace(day=1) - timedelta(days=1)).strftime('%Y-%m')
    prev_report = FinancialReport.query.filter_by(month=prev_month).first()
    opening_balance = prev_report.closing_balance if prev_report else 0.0
    payments = Payment.query.filter(Payment.payment_date.between(
        today.replace(day=1), today)).all()
    total_income = sum(p.amount for p in payments)
    expenses = Expense.query.filter(Expense.date.between(
        today.replace(day=1).date(), today.date())).all()
    total_expenses = sum(e.amount for e in expenses)
    closing_balance = opening_balance + total_income - total_expenses
    report = FinancialReport.query.filter_by(month=current_month).first()
    if report:
        report.opening_balance = opening_balance
        report.total_income = total_income
        report.total_expenses = total_expenses
        report.closing_balance = closing_balance
    else:
        report = FinancialReport(
            month=current_month,
            opening_balance=opening_balance,
            total_income=total_income,
            total_expenses=total_expenses,
            closing_balance=closing_balance
        )
        db.session.add(report)
    db.session.commit()
    print(f"Report generated for {current_month}")