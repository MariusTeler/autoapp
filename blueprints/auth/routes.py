from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user

from blueprints.auth import auth_bp
from models import User


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        user = User.query.filter_by(username=username).first()

        if not user or not user.check_password(password):
            flash('Utilizator sau parolă incorectă.', 'danger')
            return render_template('auth/login.html')

        if not user.active:
            flash('Contul tău este dezactivat. Contactează administratorul.', 'danger')
            return render_template('auth/login.html')

        login_user(user)

        # Warn if still using default admin password
        if user.username == 'admin' and user.check_password('admin123'):
            flash('Atenție: folosești parola implicită! Schimb-o din panoul Admin Useri.', 'warning')

        next_page = request.args.get('next')
        return redirect(next_page or url_for('dashboard.index'))

    return render_template('auth/login.html')


@auth_bp.route('/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
    flash('Te-ai deconectat cu succes.', 'info')
    return redirect(url_for('auth.login'))
