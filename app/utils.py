from flask import current_app,session, redirect, url_for
from functools import wraps


def notify_late_payment(email, phone, subject, message):
    from flask import current_app
    from twilio.rest import Client
    from flask_mail import Message
    from app import mail

    if email:
        try:
            msg = Message(subject, recipients=[email])
            msg.body = message
            mail.send(msg)
        except Exception as e:
            print(f"Email failed: {e}")

    # SMS
    if phone:
        try:
            twilio_client = Client(
                current_app.config['TWILIO_ACCOUNT_SID'],
                current_app.config['TWILIO_AUTH_TOKEN']
            )
            twilio_client.messages.create(
                body=message,
                from_=current_app.config['TWILIO_PHONE_NUMBER'],
                to=phone
            )
        except Exception as e:
            print(f"SMS failed: {e}")

def generate_pdf_report(report):
    folder = os.path.join(current_app.root_path,"generated_reports")  # You can choose a better name
    os.makedirs(folder, exist_ok=True)  # Create folder if it doesn’t exist

    filename = f"Financial_Report_{report.month}.pdf"
    path = os.path.join(folder, filename)

    # Generate the PDF as you already did
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet

    doc = SimpleDocTemplate(path, pagesize=A4)
    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph(f"Financial Report - {report.month}", styles['Title']))
    elements.append(Spacer(1, 12))

    data = [
        ['Opening Balance', 'Total Income', 'Total Expenses', 'Closing Balance'],
        [f"₹{report.opening_balance:.2f}",
         f"₹{report.total_income:.2f}",
         f"₹{report.total_expenses:.2f}",
         f"₹{report.closing_balance:.2f}"]
    ]

    table = Table(data, hAlign='LEFT')
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.gray),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    elements.append(table)
    doc.build(elements)
    return filename