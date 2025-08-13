from app import db
from app.models import MaintenanceBill,FinancialReport,Expense
from sqlalchemy import func
from datetime import datetime, timedelta

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