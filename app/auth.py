from flask import Blueprint, render_template, request, redirect, url_for, session
from app.models import User,Flat
from app import db

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/')
def home():
    return redirect(url_for('auth.login'))
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username']).first()
        if user and user.check_password(request.form['password']):
            session.clear()
            session['user_id'] = user.id
            session['username'] = user.username
            session['role'] = user.role
            if user.flat_id:
                flat = Flat.query.get(user.flat_id)
                session['flat_id'] = flat.flat_id
                session['flat_number'] = flat.flat_number
            else:
                session['flat_id'] = None
                session['flat_number'] = None
            return redirect(
                url_for('main.dashboard') if user.role == 'admin'
                else url_for('main.user_dashboard')
            )
    return render_template('index.html')
@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        confirm = request.form['confirm_password']
        flat_number = request.form['flat_number']

        if password != confirm:
            return render_template('register.html')

        if User.query.filter_by(username=username).first():
            return render_template('register.html')

        flat = Flat.query.filter_by(flat_number=flat_number, is_active=True).first()
        if not flat:
            return render_template('register.html')

        user = User(
            username=username,
            role='user',
            flat_id=flat.flat_id
        )
        user.set_password(password)

        db.session.add(user)
        db.session.commit()

        return redirect(url_for('auth.login'))

    return render_template('register.html')

@auth_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth.login'))
