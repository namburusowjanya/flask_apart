from datetime import datetime, timedelta
from app import db
from app.models import MaintenanceBill, Payment
from app.utils import notify_late_payment
from sqlalchemy import func

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
