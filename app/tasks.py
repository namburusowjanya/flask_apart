from datetime import datetime, timedelta
from app import db
from app.models import MaintenanceBill,FinancialReport,Payment, Expense
from app.utils import notify_late_payment
from sqlalchemy import func
from datetime import datetime, timedelta
from app.utils import notify_late_payment

def apply_late_fees():
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

                # Prepare notification
                subject = "Late Payment Penalty Applied"
                message = (f"Dear {bill.flat.owner_name}, your maintenance bill for {bill.month} is overdue. "
                           f"A 2% late penalty of ₹{penalty:.2f} has been applied. Please pay soon to avoid further charges.")

                notify_tenant(
                    flat_contact_email=bill.flat.email,
                    flat_contact_phone=bill.flat.contact,
                    subject=subject,
                    message=message
                )
    db.session.commit()

def generate_monthly_report(month):
    """Generate report for a given month (format: 'YYYY-MM')"""
    try:
        start_date = datetime.strptime(month, "%Y-%m")
        end_date = (start_date.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)

        prev_month = (start_date.replace(day=1) - timedelta(days=1)).strftime('%Y-%m')
        prev_report = FinancialReport.query.filter_by(month=prev_month).first()
        opening_balance = prev_report.closing_balance if prev_report else 0.0

        payments = Payment.query.filter(
            Payment.payment_date.between(start_date, end_date)
        ).all()
        total_income = sum(p.amount for p in payments)

        expenses = Expense.query.filter(
            Expense.date.between(start_date.date(), end_date.date())
        ).all()
        total_expenses = sum(e.amount for e in expenses)

        closing_balance = opening_balance + total_income - total_expenses
        # Check if report exists
        report = FinancialReport.query.filter_by(month=month).first()
        if report:
            report.opening_balance = opening_balance
            report.total_income = total_income
            report.total_expenses = total_expenses
            report.closing_balance = closing_balance
        else:
            report = FinancialReport(
                month=month,
                opening_balance=opening_balance,
                total_income=total_income,
                total_expenses=total_expenses,
                closing_balance=closing_balance
            )
            db.session.add(report)
        db.session.commit()
        print(f"Report generated for {month}")
    except Exception as e:
        print(f"Failed to generate report for {month}: {e}")