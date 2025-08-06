from flask import Blueprint, request, jsonify, render_template, redirect, url_for, session,flash
from functools import wraps
from datetime import datetime
from sqlalchemy import extract, func
from flask import flash
from werkzeug.utils import secure_filename
import os
from app.tasks import generate_monthly_report
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta
from flask import current_app
from app import db
from app.models import (
    User, Flat, MaintenanceBill, Payment,
    Expense, FinancialReport, CategoryBudget
)
from app.uploads import save_receipt
from app.utils import notify_unusual_expense
from app.reports import generate_monthly_financial_report
main_bp = Blueprint('main', __name__, url_prefix='')

# --- authentication decorator ---
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated

# --- Dashboard Home ---
@main_bp.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')
@main_bp.route('/flats/info')
@login_required
def flats_info():
    flats = Flat.query.all()
    flats_data = []
    for flat in flats:
        # Use the Flat model's field directly instead of MaintenanceBill
        status = flat.maintenance_status if flat.maintenance_status else "No Data"
        flats_data.append({
            'flat_id': flat.flat_id,
            'flat_number': flat.flat_number,
            'owner_name': flat.owner_name,
            'contact': flat.contact,
            'email': flat.email or 'N/A',
            'maintenance_status': status
        })
    return render_template('total_flats.html', flats=flats_data)

@main_bp.route('/save_flat', methods=['POST'])
@login_required
def save_flat():
    flat_id = request.form.get('flat_id')

    if flat_id:
        flat = Flat.query.get(flat_id)
        if not flat:
            return "Flat not found", 404
    else:
        flat = Flat()
        db.session.add(flat)  # only add new flats

    flat.flat_number = request.form.get('flat_number')
    flat.owner_name = request.form.get('owner_name')
    flat.contact = request.form.get('contact')
    flat.email = request.form.get('email')
    flat.maintenance_status = request.form.get('maintenance_status')

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return f"Error saving flat: {e}", 500

    return redirect(url_for('main.flats_info'))

@main_bp.route('/flats/delete/<int:flat_id>', methods=['POST'])
@login_required
def delete_flat(flat_id):
    f = Flat.query.get_or_404(flat_id)
    db.session.delete(f)
    db.session.commit()
    # return redirect(url_for('main.flats'))
    flash('Flat successfully deleted!', 'success')
    return redirect(url_for('main.flats_info'))

@main_bp.route('/payments')
@login_required
def payments():
    all_payments = Payment.query.all()
    return render_template('payment.html', payments=all_payments)

@main_bp.route('/notifications')
@login_required
def notifications():
    return render_template('notifications.html')

@main_bp.route('/maintenance-bills')
@login_required
def maintenance_bills_old():
    all_bills = MaintenanceBill.query.all()
    current_month = datetime.now().strftime('%B %Y')
    return render_template('maintainance.html', bills=all_bills, current_month=current_month)

@main_bp.route('/update_bill_status/<int:bill_id>', methods=['POST'])
@login_required
def update_bill_status(bill_id):
    bill = MaintenanceBill.query.get_or_404(bill_id)
    data = request.get_json()

    if not data or 'status' not in data:
        return jsonify({"error": "Missing status"}), 400

    new_status = data['status']
    if new_status not in ['Paid', 'Pending']:
        return jsonify({"error": "Invalid status"}), 400

    bill.status = new_status
    db.session.commit()
    return jsonify({"message": "Status updated successfully"}), 200


@main_bp.route('/edit_bill_amount/<int:bill_id>', methods=['POST'])
@login_required
def edit_bill_amount(bill_id):
    bill = MaintenanceBill.query.get_or_404(bill_id)
    data = request.get_json()

    if not data:
        return jsonify({"error": "Missing JSON data"}), 400

    base_amount = data.get('base_amount')
    late_fee = data.get('late_fee')
    status = data.get('status')

    # Validate base_amount
    if base_amount is not None:
        try:
            base_amount = float(base_amount)
            if base_amount < 0:
                return jsonify({"error": "Base amount cannot be negative"}), 400
        except ValueError:
            return jsonify({"error": "Invalid base amount"}), 400

    # Validate late_fee
    if late_fee is not None:
        try:
            late_fee = float(late_fee)
            if late_fee < 0:
                return jsonify({"error": "Late fee cannot be negative"}), 400
        except ValueError:
            return jsonify({"error": "Invalid late fee"}), 400

    # Normalize and validate status
    if status is not None:
        status = status.strip().title()  # Convert to 'Paid' or 'Pending'
        if status not in ['Paid', 'Pending']:
            return jsonify({"error": "Invalid status"}), 400

    # Update fields if provided
    if base_amount is not None:
        bill.base_amount = base_amount
    if late_fee is not None:
        bill.late_fee = late_fee
    if status is not None:
        bill.status = status

    db.session.commit()

    return jsonify({"message": "Bill updated successfully"})

@main_bp.route('/expenses', methods=['GET'])
@login_required
def expenses():
    all_expenses = Expense.query.order_by(Expense.date.desc()).all()
    return render_template('expenses.html', expenses=all_expenses)

# Route to add a new expense
@main_bp.route('/add-expense', methods=['POST'])
@login_required
def add_expense():
    try:
        vendor = request.form['vendor']
        category = request.form['category']
        amount = float(request.form['amount'])
        date_str = request.form['date']
        date = datetime.strptime(date_str, '%Y-%m-%d').date()

        new_expense = Expense(
            vendor=vendor,
            category=category,
            amount=amount,
            date=date
        )
        db.session.add(new_expense)
        db.session.commit()
        flash("Expense added successfully.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error saving expense: {str(e)}", "danger")

    return redirect(url_for('main.expenses'))

@main_bp.route('/maintenance-bills')
def maintenance_bills():
    # You can render a template or return something here
    return render_template('maintenance_bills.html')  # Or whatever fits your app

@main_bp.route('/expenses/download/pdf')
@login_required
def download_pdf():
    buf = generate_expense_pdf()
    return send_file(buf, as_attachment=True,
                     download_name='expenses.pdf',
                     mimetype='application/pdf')

# --- REPORTS page ---
@main_bp.route('/reports', methods=['GET'])
@login_required
def reports():
    month = request.args.get('month')
    if month:
        reports = FinancialReport.query.filter_by(month=month).all()
    else:
        reports = FinancialReport.query.order_by(FinancialReport.month.desc()).all()
    return render_template('reports.html', reports=reports, selected_month=month)

@login_required
def check_and_send_notifications():
    with current_app.app_context():
        # 1. Payment due dates 3 days prior
        due_date_limit = datetime.utcnow() + timedelta(days=3)
        upcoming_bills = MaintenanceBill.query.filter_by(status='Pending').all()

        for bill in upcoming_bills:
            # Assuming you have a due_date field or use month + day logic here
            # For example: Due date is 5th of month stored in bill.month YYYY-MM
            year, month = map(int, bill.month.split('-'))
            due_date = datetime(year, month, 5)  # change this as per your rules
            if due_date.date() == due_date_limit.date():
                # Notify tenant via email/SMS
                user_email = bill.flat.owner_email  # Assume flat has owner email
                user_phone = bill.flat.owner_phone  # Assume flat has owner phone
                message = f"Reminder: Your maintenance bill for {bill.month} is due on {due_date.date()}."
                if user_email:
                    send_email(user_email, "Maintenance Bill Due Reminder", message)
                if user_phone:
                    send_sms(user_phone, message)

        # 2. Late payments (apply penalties)
        late_fee_date = datetime.utcnow() - timedelta(days=15)
        late_bills = MaintenanceBill.query.filter(
            MaintenanceBill.status == 'Pending',
            MaintenanceBill.month <= late_fee_date.strftime('%Y-%m')
        ).all()

        for bill in late_bills:
            # Auto apply 2% penalty if not already applied
            if bill.late_fee == 0:
                penalty = bill.base_amount * 0.02
                bill.late_fee = penalty
                db.session.commit()

                message = f"Your maintenance bill for {bill.month} is overdue. A 2% late penalty of {penalty:.2f} has been applied."
                user_email = bill.flat.owner_email
                user_phone = bill.flat.owner_phone
                if user_email:
                    send_email(user_email, "Late Payment Penalty Applied", message)
                if user_phone:
                    send_sms(user_phone, message)

        # 3. Unusual expenses alert (20% above monthly average)
        # Assuming you have an Expense model with fields: amount, month
        from app.models import Expense

        avg_expense = db.session.query(db.func.avg(Expense.amount)).scalar() or 0
        expenses = Expense.query.all()
        for expense in expenses:
            if expense.amount > avg_expense * 1.20:
                # Notify admin or responsible person
                admin_email = current_app.config.get('ADMIN_EMAIL', 'admin@example.com')
                subject = "Unusual Expense Alert"
                body = f"Expense of {expense.amount} in {expense.month} is 20% above the average monthly expense."
                send_email(admin_email, subject, body)
                # You can also add SMS notification if needed
def send_email(to, subject, body):
    msg = Message(subject, recipients=[to])
    msg.body = body
    mail.send(msg)

def send_sms(to_phone, body):
    twilio_client.messages.create(
        body=body,
        from_=current_app.config['TWILIO_PHONE_NUMBER'],
        to=to_phone
    )
@main_bp.route('/generate-financial-report', methods=['GET'])
@login_required
def manual_generate_report():
    month = request.args.get('month')
    if not month:
        flash("Please select a month.", "warning")
        return redirect(url_for('main.reports'))
    generate_monthly_financial_report(month)
    return redirect(url_for('main.reports', month=month))
