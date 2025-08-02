from flask_mail import Message
from app import mail
from flask import current_app

def send_email(subject, recipients, body):
    msg = Message(subject=subject, recipients=recipients, body=body,
                  sender=current_app.config['MAIL_USERNAME'])
    mail.send(msg)

def notify_payment_due(flat_contact, flat_owner, amount, due_date):
    # Example email/SMS notification
    subject = f"Maintenance Fee Due Reminder for Flat"
    body = f"Dear {flat_owner}, your maintenance fee of ₹{amount} is due by {due_date}. Please pay on time to avoid penalties."
    # Call send_email or SMS API here

def notify_late_payment(flat_contact, flat_owner, penalty_amount):
    # Notify user about late penalty applied
    pass

def notify_unusual_expense(expense):
    # Notify treasurer or manager about flagged expense
    pass
