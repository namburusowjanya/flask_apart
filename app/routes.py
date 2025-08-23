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
    User, Flat, MaintenanceBill,
    Expense, FinancialReport, CategoryBudget,AdvancePayment,Credit)
from app.uploads import save_receipt
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
        flats_data.append({
            'flat_id': flat.flat_id,
            'flat_number': flat.flat_number,
            'owner_name': flat.owner_name,
            'owner_contact': flat.owner_contact,
            'tennant_name': flat.tennant_name,
            'tennant_contact': flat.tennant_contact
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
    flat.owner_contact = request.form.get('owner_contact')
    flat.tennant_name = request.form.get('tennant_name')
    flat.tennant_contact = request.form.get('tennant_contact')

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

# @main_bp.route("/pending-dues")
# def pending_dues():
#     dues = MaintenanceBill.query.filter_by(status="Pending").all()
#     return render_template("pending_dues.html", dues=dues)

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
    status = data.get('status')

    # Validate base_amount
    if base_amount is not None:
        try:
            base_amount = float(base_amount)
            if base_amount < 0:
                return jsonify({"error": "Base amount cannot be negative"}), 400
        except ValueError:
            return jsonify({"error": "Invalid base amount"}), 400

    # Normalize and validate status
    if status is not None:
        status = status.strip().title()  # Convert to 'Paid' or 'Pending'
        if status not in ['Paid', 'Pending']:
            return jsonify({"error": "Invalid status"}), 400

    # Update fields if provided
    if base_amount is not None:
        bill.base_amount = base_amount
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
        category = request.form['category']
        amount = float(request.form['amount'])
        date_str = request.form['date']
        date = datetime.strptime(date_str, '%Y-%m-%d').date()

        new_expense = Expense(
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
    month = request.form['month']
    method = request.form['method']

    flat = Flat.query.filter_by(flat_number=flat_number).first()
    if not flat:
        return "Flat not found", 404

    new_bill = MaintenanceBill(flat_id=flat.flat_id, base_amount=1500, month=month, status='Pending', method=method)
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

@main_bp.route("/advanced-payments")
@login_required
def advanced_payments():
    flats = Flat.query.all() 
    advance_payments = AdvancePayment.query.order_by(AdvancePayment.payment_date.desc()).all()
    return render_template(
        "advance_payment.html",flats=flats,advance_payments=advance_payments)

@main_bp.route("/add_advance_payment", methods=["POST"])
@login_required
def add_advance_payment():
    flat_no = request.form.get("flat_no")
    start_month = request.form.get("start_month")
    months_paid_for = int(request.form.get("months_paid_for"))
    monthly_amount = float(request.form.get("monthly_amount"))
    total_amount = float(request.form.get("amount"))
    method = request.form.get("method")
    receipt_no = request.form.get("receipt_no")

    flat = Flat.query.filter_by(flat_number=flat_no).first()
    if not flat:
        flash("Flat not found.", "danger")
        return redirect(url_for("main.advanced_payments"))

    adv_payment = AdvancePayment(
        flat_id=flat.flat_id,
        start_month=start_month,
        months_paid_for=months_paid_for,
        total_amount=total_amount,
        method=method,
        receipt_number=receipt_no
    )
    db.session.add(adv_payment)
    db.session.commit()
    flash("Advance payment recorded successfully.", "success")
    return redirect(url_for("main.advanced_payments"))
@main_bp.route("/pending-dues")
@login_required
def pending_dues():
    current_month = request.args.get("month")
    if not current_month:
        current_month = datetime.today().strftime("%Y-%m")

    flats = Flat.query.all()
    dues = []

    for flat in flats:
        pending_bills = MaintenanceBill.query.filter_by(flat_id=flat.flat_id, status="Pending").all()
        advances = AdvancePayment.query.filter_by(flat_id=flat.flat_id).all()

        for bill in pending_bills:
            covered = False
            advance_info = []

            for adv in advances:
                year, month = map(int, adv.start_month.split("-"))
                for i in range(adv.months_paid_for):
                    covered_month = f"{year}-{str(month).zfill(2)}"
                    if covered_month == bill.month:
                        covered = True
                    advance_info.append(covered_month)  
                    month += 1
                    if month > 12:
                        month = 1
                        year += 1

            if not covered:
                dues.append({
                    "bill": bill,
                    "advance_months": ", ".join(advance_info) if advance_info else "-"
                })

    return render_template("pending_dues.html", dues=dues)

@main_bp.route('/credits', methods=['GET'])
@login_required
def credits_page():
    flats = Flat.query.all()
    credits = Credit.query.order_by(Credit.created_at.desc()).all()
    return render_template('credits.html', flats=flats, credits=credits)

@main_bp.route('/add_credit', methods=['POST'])
@login_required
def add_credit():
    flat_no = request.form.get('flat_no')
    amount = request.form.get('amount')
    reason = request.form.get('reason')

    flat = Flat.query.filter_by(flat_number=flat_no).first()
    if not flat:
        flash("Flat not found.", "error")
        return redirect(url_for('main.credits_page'))

    try:
        amount = float(amount)
    except ValueError:
        flash("Invalid amount.", "error")
        return redirect(url_for('main.credits_page'))

    credit = Credit(flat_id=flat.flat_id, amount=amount, reason=reason)
    db.session.add(credit)
    db.session.commit()

    flash("Credit added successfully.", "success")
    return redirect(url_for('main.credits_page'))
