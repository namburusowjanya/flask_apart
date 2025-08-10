from flask import Blueprint, request, jsonify, render_template, redirect, url_for, session,flash,current_app,send_from_directory
from functools import wraps
from sqlalchemy import extract, func
from werkzeug.utils import secure_filename
import os
import logging
from app.tasks import generate_monthly_report
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta
from app import db
from app.models import (
    User, Flat, MaintenanceBill, Payment,
    Expense, FinancialReport, CategoryBudget,Notification
)
from app.uploads import save_receipt
from app.utils import notify_late_payment
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
    flash('Flat successfully deleted!', 'success')
    return redirect(url_for('main.flats_info'))

@main_bp.route('/payments',methods=['GET'])
@login_required
def payments():
    all_payments = Payment.query.join(MaintenanceBill).join(Flat).order_by(Payment.payment_date.desc()).all()
    return render_template('payment.html', payments=all_payments)

@main_bp.route('/add_payments', methods=['POST'])
@login_required
def add_payments():
    try:
        flat_no = request.form.get('flat_no')
        owner = request.form.get('owner')
        amount = request.form.get('amount')
        status = request.form.get('status')
        date_str = request.form.get('date')
        mode = request.form.get('mode')
        receipt_no = request.form.get('receipt_no')

        if not all([flat_no, owner, amount, status]):
            flash("Please fill in all required fields.", "error")
            return redirect(url_for('main.payments'))

        # Convert amount safely
        try:
            amount = float(amount)
        except ValueError:
            flash("Invalid amount format.", "error")
            return redirect(url_for('main.payments'))

        # If paid, require and parse date
        if status.lower() == 'paid':
            if not date_str:
                flash("Date is required for paid payments.", "error")
                return redirect(url_for('main.payments'))
            try:
                payment_date = datetime.strptime(date_str, '%Y-%m-%d')
            except ValueError:
                flash("Invalid date format.", "error")
                return redirect(url_for('main.payments'))
        else:
            payment_date = None

        # Get flat
        flat = Flat.query.filter_by(flat_number=flat_no).first()
        if not flat:
            flash(f"Flat number {flat_no} not found.", "error")
            return redirect(url_for('main.payments'))

        # Determine month for bill
        month_str = payment_date.strftime('%Y-%m') if payment_date else datetime.now().strftime('%Y-%m')

        # Find or create bill
        bill = MaintenanceBill.query.filter_by(flat_id=flat.flat_id, month=month_str).first()
        if not bill:
            bill = MaintenanceBill(flat_id=flat.flat_id, month=month_str, base_amount=amount, status='Pending')
            db.session.add(bill)
            db.session.commit()

        # Only add payment record if status is paid
        if status.lower() == 'paid':
            payment = Payment(
                bill_id=bill.bill_id,
                amount=amount,
                payment_date=payment_date,
                method=mode if mode else None,
                receipt_number=receipt_no if receipt_no else None
            )
            db.session.add(payment)

        # Update bill status
        bill.status = 'Paid' if status.lower() == 'paid' else 'Pending'

        db.session.commit()
        flash("Payment record added successfully.", "success")
        return redirect(url_for('main.payments'))
    except Exception as e:
        current_app.logger.error(f"Error adding payment: {e}", exc_info=True)
        flash("Internal server error. Please try again.", "error")
        return redirect(url_for('main.payments'))

@main_bp.route("/pending-dues")
def pending_dues():
    dues = MaintenanceBill.query.filter_by(status="Pending").all()
    return render_template("pending_dues.html", dues=dues)

@main_bp.route('/notifications', methods=['GET', 'POST'])
@login_required
def notifications():
    flats = Flat.query.all()
    sent_notifications = Notification.query.order_by(Notification.date.desc()).all()
    if request.method == 'POST':
        send_type = request.form.get('type')
        subject = request.form.get('subject')
        message = request.form.get('message')

        if not subject or not message:
            flash("Subject and message are required.", "danger")
            return render_template('notifications.html', flats=flats)

        if send_type == 'all':
            status = "Delivered"
            try:
                for flat in flats:
                    notify_late_payment(flat.email, subject, message)
            except Exception as e:
                status = f"Failed: {e}"
            new_notification = Notification(
                recipient="All",
                message=f"{subject}\n{message}",
                status=status
            )
            db.session.add(new_notification)

        elif send_type == 'individual':
            flat_number = request.form.get('flat_number')
            flat = Flat.query.filter_by(flat_number=flat_number).first()
            if not flat:
                flash("Flat not found", "danger")
                return render_template('notifications.html', flats=flats,sent_notifications=sent_notifications)
            status = "Delivered"
            try:
                notify_late_payment(flat.email, subject, message)
            except Exception as e:
                status = f"Failed: {e}"
            new_notification = Notification(
                recipient=f"Flat {flat_number}",
                message=f"{subject}\n{message}",
                status=status)
            db.session.add(new_notification)
        db.session.commit()
        flash(f"Notification sent to Flat {flat_number}.", "success")
        return redirect(url_for('main.notifications'))
        
    return render_template('notifications.html', flats=flats)

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

@main_bp.route('/maintenance_bills')
@login_required
def maintenance_bills():
    current_month = request.args.get('month')
    if not current_month:
        current_month = datetime.today().strftime('%Y-%m')

    bills = MaintenanceBill.query.filter_by(month=current_month).join(Flat).all()
    return render_template('maintainance.html', bills=bills, current_month=current_month)

@main_bp.route('/add_maintenance_bill', methods=['POST'])
@login_required
def add_maintenance_bill():
    flat_number = request.form['flat_number']
    base_amount = float(request.form['base_amount'])
    late_fee = float(request.form['late_fee'])
    month = request.form['month']

    flat = Flat.query.filter_by(flat_number=flat_number).first()
    if not flat:
        return "Flat not found", 404

    new_bill = MaintenanceBill(flat_id=flat.flat_id, base_amount=base_amount, late_fee=late_fee, month=month, status='Pending')
    db.session.add(new_bill)
    db.session.commit()

    return redirect(url_for('main.maintenance_bills', month=month))

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

# @main_bp.route('/send_notification/<int:flat_number>', methods=['GET', 'POST'])
# @login_required
# def send_notification(flat_number):
#     flat = Flat.query.filter_by(flat_number=flat_number)get_or_404() 

#     if request.method == 'POST':
#         subject = request.form.get('subject')
#         message = request.form.get('message')

#         if not subject or not message:
#             flash("Subject and message are required", "danger")
#             return redirect(request.url)

#         from app.utils import notify_tenant
#         notify_tenant(flat.email, flat.contact, subject, message)
#         flash("Notification sent successfully!", "success")
#         return redirect(url_for('main.flats_info'))

#     return render_template('notifications.html', flat=flat)

@main_bp.route('/generate-financial-report', methods=['GET'])
@login_required
def manual_generate_report():
    month = request.args.get('month')
    if not month:
        flash("Please select a month.", "warning")
        return redirect(url_for('main.reports'))
    # Check if report already exists
    existing = FinancialReport.query.filter_by(month=month).first()
    if existing:
        flash(f"Report for {month} already exists. Regeneration will overwrite the existing report.", "danger")
        return redirect(url_for('main.reports', month=month))

    from app.tasks import generate_monthly_report
    generate_monthly_report(month)
    flash(f"Report for {month} generated successfully.", "success")
    return redirect(url_for('main.reports', month=month))

@main_bp.route('/download-report/<string:month>', methods=['GET'])
def download_report(month):
    folder_path = os.path.join(os.getcwd(), 'app', 'generated_reports')
    filename = f"Financial_Report_{month}.pdf"
    full_path = os.path.join(folder_path, filename)

    if not os.path.exists(full_path):
        return "Report not found", 404

    return send_from_directory(folder_path, filename, as_attachment=True)