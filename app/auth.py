from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from app.models import User
from app import db

auth_bp = Blueprint('auth', __name__, url_prefix='')


@auth_bp.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            session['user_id'] = user.id
            return redirect(url_for('auth.success_page'))  
        else:
            flash('Invalid username or password')

    return render_template('index.html') 

@auth_bp.route('/success') 
def success_page():
    return render_template('dashboard.html')


@auth_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth.login'))
