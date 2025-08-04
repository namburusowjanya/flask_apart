from flask import Blueprint, request, jsonify, render_template, redirect, url_for, session
from functools import wraps
from datetime import datetime
from sqlalchemy import extract, func
from flask import flash
from werkzeug.utils import secure_filename
import os

from app import db
from app.models import (
    User, Flat, MaintenanceBill, Payment,
    Expense, FinancialReport, CategoryBudget
)
from app.uploads import save_receipt
from app.utils import notify_unusual_expense
from app.reports import generate_expense_pdf

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
def maintenance_bills():
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

    if not data or 'amount' not in data:
        return jsonify({"error": "Missing amount"}), 400

    try:
        amount = float(data['amount'])
        if amount < 0:
            raise ValueError
    except ValueError:
        return jsonify({"error": "Invalid amount"}), 400

    # Set base_amount; you can customize how late_fee is handled if needed
    bill.base_amount = amount
    db.session.commit()

    return jsonify({"message": "Amount updated successfully"}), 200
from datetime import datetime

@main_bp.route('/add-expense', methods=['POST'])
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
        return redirect(url_for('main.expenses'))

    except Exception as e:
        db.session.rollback()
        flash(f"Error saving expense: {str(e)}", "danger")
        return redirect(url_for('main.expenses'))



# @main_bp.route('/expenses', methods=['GET', 'POST'])
# @login_required
# def add_expense():
#     if request.method == 'POST':
#         vendor = request.form['vendor']
#         category = request.form['category']
#         amount = float(request.form['amount'])
#         date = request.form['date']
#         description = request.form.get('description')
        
#         receipt_file = request.files.get('receipt')
#         receipt_url = None

#         if receipt_file and receipt_file.filename != '':
#             filename = secure_filename(receipt_file.filename)
#             filepath = os.path.join('static/uploads', filename)
#             receipt_file.save(filepath)
#             receipt_url = f'uploads/{filename}'

#         new_expense = Expense(
#             vendor=vendor,
#             category=category,
#             amount=amount,
#             date=date,
#             description=description,
#             receipt_url=receipt_url
#         )
#         db.session.add(new_expense)
#         db.session.commit()
#         flash("Expense added successfully", "success")
#         return redirect(url_for('main.add_expense'))

#     expenses = Expense.query.order_by(Expense.date.desc()).all()
#     return render_template('expenses.html', expenses=expenses)

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
    all_reports = FinancialReport.query.all()
    return render_template('reports.html', reports=all_reports)
