from . import db
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

class Flat(db.Model):
    __tablename__ = 'flats'
    flat_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    flat_number = db.Column(db.String(10), unique=True, nullable=False,index=True)
    owner_name = db.Column(db.String(100), nullable=False)
    owner_contact = db.Column(db.String(15), nullable=False)
    owner_email = db.Column(db.String(100), nullable=False)
    tennant_name = db.Column(db.String(100), nullable=True)
    tennant_contact = db.Column(db.String(15), nullable=True)
    tennant_email = db.Column(db.String(100), nullable=True)
    is_active = db.Column(db.Boolean, default=True,index=True)

    bills = db.relationship(
        'MaintenanceBill',
        backref='flat',
        passive_deletes=True
    )

    expenses = db.relationship(
        'Expense',
        backref='flat',
        passive_deletes=True
    )

    advanced_payments = db.relationship(
        'AdvancePayment',
        backref='flat',
        lazy=True
    )

class MaintenanceBill(db.Model):
    __tablename__ = 'maintenance_bills'
    __table_args__ = (
        db.Index('idx-flat_month', 'flat_id', 'month'),
    )
    bill_id = db.Column(db.Integer, primary_key=True)
    flat_id = db.Column(db.Integer, db.ForeignKey('flats.flat_id'), nullable=False,index=True)

    month = db.Column(db.String(7), nullable=False,index=True)
    base_amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(10), default='Pending',index=True)
    method = db.Column(db.String(50))

class Expense(db.Model):
    __tablename__ = 'expenses'
    expense_id = db.Column(db.Integer, primary_key=True)
    flat_id = db.Column(db.Integer, db.ForeignKey('flats.flat_id'),index=True)

    category = db.Column(db.String(50), nullable=False,index=True)
    amount = db.Column(db.Float, nullable=False)
    date = db.Column(db.Date, nullable=False,index=True)
    receipt_url = db.Column(db.String(255))

class FinancialReport(db.Model):
    __tablename__ = 'financial_reports' 
    report_id = db.Column(db.Integer, primary_key=True)
    month = db.Column(db.String(7))
    opening_balance = db.Column(db.Float, default=0.0)
    total_income = db.Column(db.Float, default=0.0)
    total_expenses = db.Column(db.Float, default=0.0)
    closing_balance = db.Column(db.Float, default=0.0)

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True,nullable=False,index=True)
    password_hash = db.Column(db.String(255),nullable=False)
    role = db.Column(db.String(20), default='user',index=True)
    flat_id = db.Column(db.Integer, db.ForeignKey('flats.flat_id'), index=True)
    def set_password(self, pw):
        self.password_hash = generate_password_hash(pw)
    def check_password(self, pw):
        return check_password_hash(self.password_hash, pw)

class AdvancePayment(db.Model):
    __tablename__ = 'advance_payments'

    id = db.Column(db.Integer, primary_key=True)
    flat_id = db.Column(db.Integer, db.ForeignKey('flats.flat_id'), nullable=False,index=True)
    start_month = db.Column(db.String(7), nullable=False,index=True)
    months_paid_for = db.Column(db.Integer, nullable=False)
    total_amount = db.Column(db.Float, nullable=False)
    payment_date = db.Column(db.Date, default=datetime.utcnow,index=True)
    method = db.Column(db.String(50))
    receipt_number = db.Column(db.String(100))