from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from app.models import User
from app import db

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/', methods=['GET'])
def index():
    return redirect(url_for('auth.login'))

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        u = User.query.filter_by(username=request.form['username']).first()
        if u and u.check_password(request.form['password']):
            session['user_id'] = u.id
            return redirect(url_for('main.dashboard'))
        error = 'Invalid username or password'
    return render_template('login.html', error=error)

@auth_bp.route('/logout')
def logout():
    session.pop('user_id', None)
    return render_template('logout.html')
