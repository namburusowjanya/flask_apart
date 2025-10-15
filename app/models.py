from . import db
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
# app/models.py
class Flat(db.Model):
    __tablename__ = 'flats'
    flat_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    flat_number = db.Column(db.String(10),unique=True,nullable=False,)
    owner_name = db.Column(db.String(100), nullable=False)
    owner_contact = db.Column(db.String(15), nullable=False)
    owner_email = db.Column(db.String(100),nullable=False)
    tennant_name = db.Column(db.String(100), nullable=True)  
    tennant_contact = db.Column(db.String(15), nullable=True)
    tennant_email = db.Column(db.String(100),nullable=False)

    bills = db.relationship(
        'MaintenanceBill',
        backref='flat',
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    expenses = db.relationship(
        'Expense',
        backref='flat',
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class MaintenanceBill(db.Model):
    __tablename__ = 'maintenance_bills'
    bill_id = db.Column(db.Integer, primary_key=True)
    flat_id = db.Column(db.Integer, db.ForeignKey('flats.flat_id',ondelete="CASCADE"), nullable=False)
    month = db.Column(db.String(7), nullable=False)  # e.g. '2025-07'
    base_amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(10), default='Pending')  # Paid / Pending
    method = db.Column(db.String(50))

class Expense(db.Model):
    __tablename__ = 'expenses'
    expense_id = db.Column(db.Integer, primary_key=True)
    flat_id = db.Column(db.Integer, db.ForeignKey('flats.flat_id', ondelete="CASCADE"))  # link to flat
    category = db.Column(db.String(50), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    date = db.Column(db.Date, nullable=False)
    receipt_url = db.Column(db.String(255))

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

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True)
    password_hash = db.Column(db.String(255))
    role = db.Column(db.String(20), default='admin') 
    def set_password(self, pw):
        self.password_hash = generate_password_hash(pw)
    def check_password(self, pw):
        return check_password_hash(self.password_hash, pw)

class AdvancePayment(db.Model):
    __tablename__ = 'advance_payments'

    id = db.Column(db.Integer, primary_key=True)
    flat_id = db.Column(db.Integer, db.ForeignKey('flats.flat_id'), nullable=False)
    start_month = db.Column(db.String(7), nullable=False)  # e.g. "2025-08"
    months_paid_for = db.Column(db.Integer, nullable=False)  # e.g. 12 or 2
    total_amount = db.Column(db.Float, nullable=False)
    payment_date = db.Column(db.Date, default=datetime.utcnow)
    method = db.Column(db.String(50))
    receipt_number = db.Column(db.String(100))  

    flat = db.relationship('Flat', backref=db.backref('advanced_payments', lazy=True))


class Credit(db.Model):
    __tablename__ = 'credits'

    id = db.Column(db.Integer, primary_key=True)
    flat_id = db.Column(db.Integer, db.ForeignKey('flats.flat_id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    reason = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    used = db.Column(db.Boolean, default=False)  

    flat = db.relationship('Flat', backref='credits')