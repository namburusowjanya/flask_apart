from app import create_app, db
from app.models import Payment, Expense, FinancialReport, MaintenanceBill
from datetime import datetime

app = create_app()

with app.app_context():
    # Simulate a payment
    p = Payment(bill_id=1, amount=1200.0, mode="Online")
    db.session.add(p)

    # Add test expense
    e = Expense(vendor="Electrician", category="repairs", amount=4500.0,
                description="Lighting Fix", date=datetime(2025, 7, 12))
    db.session.add(e)

    # Add a report manually
    r = FinancialReport(month="2025-07", opening_balance=10000.0,
                        total_income=48000.0, total_expenses=9500.0,
                        closing_balance=48500.0)
    db.session.add(r)

    db.session.commit()
    print("Test data inserted.")
