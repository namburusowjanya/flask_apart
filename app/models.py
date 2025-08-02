from app import db
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

class Flat(db.Model):
    __tablename__ = 'flats'
    flat_id = db.Column(db.Integer, primary_key=True)
    flat_number = db.Column(db.String(10), nullable=False)
    owner_name = db.Column(db.String(100), nullable=False)
    contact = db.Column(db.String(20))
    parking_slot = db.Column(db.String(20))

    bills = db.relationship('MaintenanceBill', backref='flat', lazy=True)

class MaintenanceBill(db.Model):
    __tablename__ = 'maintenance_bills'
    bill_id = db.Column(db.Integer, primary_key=True)
    flat_id = db.Column(db.Integer, db.ForeignKey('flats.flat_id'), nullable=False)
    month = db.Column(db.String(7), nullable=False)  # e.g. '2025-07'
    base_amount = db.Column(db.Float, nullable=False)
    late_fee = db.Column(db.Float, default=0.0)
    status = db.Column(db.String(10), default='Pending')  # Paid / Pending

    payments = db.relationship('Payment', backref='bill', lazy=True)

class Payment(db.Model):
    __tablename__ = 'payments'
    payment_id = db.Column(db.Integer, primary_key=True)
    bill_id = db.Column(db.Integer, db.ForeignKey('maintenance_bills.bill_id'), nullable=False)
    payment_date = db.Column(db.DateTime, default=datetime.utcnow)
    amount = db.Column(db.Float, nullable=False)
    mode = db.Column(db.String(20))  # Cash / Online
    receipt_url = db.Column(db.String(255))  # Path to receipt image

class Expense(db.Model):
    __tablename__ = 'expenses'
    expense_id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, default=datetime.utcnow)
    vendor = db.Column(db.String(100))
    category = db.Column(db.String(50))
    amount = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text)
    receipt_url = db.Column(db.String(255))
    approval_status = db.Column(db.String(20), default='Auto')  # Auto / Pending / Approved / Rejected

class FinancialReport(db.Model):
    __tablename__ = 'financial_reports'
    report_id = db.Column(db.Integer, primary_key=True)
    month = db.Column(db.String(7))  # e.g. '2025-07'
    opening_balance = db.Column(db.Float, default=0.0)
    total_income = db.Column(db.Float, default=0.0)
    total_expenses = db.Column(db.Float, default=0.0)
    closing_balance = db.Column(db.Float, default=0.0)

class CategoryBudget(db.Model):
    __tablename__ = 'category_budgets'
    category = db.Column(db.String(50), primary_key=True)
    monthly_limit = db.Column(db.Float, nullable=False)

from app import db
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True)
    password_hash = db.Column(db.String(255))

    def set_password(self, pw):
        self.password_hash = generate_password_hash(pw)
    def check_password(self, pw):
        return check_password_hash(self.password_hash, pw)
