from flask import Blueprint, request, jsonify, render_template, redirect, url_for, session
from functools import wraps
from datetime import datetime
from sqlalchemy import extract, func

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

# --- FLATS pages & APIs ---
@main_bp.route('/flats/info')
@login_required
def flats_info():
    flats = Flat.query.all()
    flats_data = []
    for flat in flats:
        latest_bill = MaintenanceBill.query.filter_by(flat_id=flat.flat_id)\
                          .order_by(MaintenanceBill.month.desc()).first()
        status = latest_bill.status if latest_bill else "No Data"
        flats_data.append({
            'flat_number': flat.flat_number,
            'owner_name': flat.owner_name,
            'contact': flat.contact,
            'email': getattr(flat, 'email', 'N/A'),  
            'maintenance_status': status
        })
    return render_template('total_flats.html', flats=flats_data)

@main_bp.route('/flats/delete/<int:flat_id>', methods=['POST'])
@login_required
def delete_flat(flat_id):
    f = Flat.query.get_or_404(flat_id)
    db.session.delete(f)
    db.session.commit()
    return redirect(url_for('main.flats'))

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
    return render_template('maintainance.html', bills=all_bills)

# --- EXPENSES page & API ---
@main_bp.route('/expenses', methods=['GET', 'POST'])
@login_required
def expenses():
    if request.method == 'POST':
        form = request.form
        vendor = form['vendor']
        category = form['category']
        try:
            amount = float(form['amount'])
        except:
            amount = 0.0
        description = form.get('description')
        file = request.files.get('receipt')
        receipt_url = save_receipt(file) if file else None

        # budget check
        now = datetime.today()
        total = db.session.query(func.sum(Expense.amount)).filter(
            Expense.category==category,
            extract('month', Expense.date)==now.month,
            extract('year', Expense.date)==now.year
        ).scalar() or 0.0
        bud = CategoryBudget.query.get(category)
        over = bud and (total+amount>bud.monthly_limit)

        status = 'Pending' if amount>5000 or over else 'Auto'
        if status=='Pending':
            notify_unusual_expense({
                "vendor":vendor,"amount":amount,
                "category":category,"reason":"High/Over budget"
            })

        e = Expense(
            vendor=vendor,
            category=category,
            amount=amount,
            description=description,
            date=now,
            receipt_url=receipt_url,
            approval_status=status
        )
        db.session.add(e)
        db.session.commit()
        return redirect(url_for('main.expenses'))

    all_exp = Expense.query.all()
    return render_template('expenses.html', expenses=all_exp)

# --- DOWNLOAD PDF ---
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
