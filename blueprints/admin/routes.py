from flask import abort, render_template, redirect, url_for, flash, request
from flask_login import login_required

from blueprints.admin import admin_bp
from decorators import admin_required
from models import db, User


@admin_bp.route('/useri')
@login_required
@admin_required
def useri():
    users = User.query.order_by(User.created_at.asc()).all()
    return render_template('admin/useri.html', users=users)


@admin_bp.route('/useri/nou', methods=['POST'])
@login_required
@admin_required
def useri_nou():
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '')
    full_name = request.form.get('full_name', '').strip()
    role = request.form.get('role', 'user')

    if not username or not password or not full_name:
        flash('Toate câmpurile sunt obligatorii.', 'danger')
        return redirect(url_for('admin.useri'))

    if User.query.filter_by(username=username).first():
        flash(f'Utilizatorul "{username}" există deja.', 'danger')
        return redirect(url_for('admin.useri'))

    user = User(username=username, full_name=full_name, role=role, active=True)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    flash(f'Utilizatorul "{username}" a fost creat.', 'success')
    return redirect(url_for('admin.useri'))


@admin_bp.route('/useri/<int:user_id>/editeaza', methods=['POST'])
@login_required
@admin_required
def useri_editeaza(user_id):
    user = db.get_or_404(User, user_id)
    user.full_name = request.form.get('full_name', user.full_name).strip()
    user.role = request.form.get('role', user.role)

    new_password = request.form.get('password', '').strip()
    if new_password:
        user.set_password(new_password)

    db.session.commit()
    flash(f'Utilizatorul "{user.username}" a fost actualizat.', 'success')
    return redirect(url_for('admin.useri'))


@admin_bp.route('/useri/<int:user_id>/toggle', methods=['POST'])
@login_required
@admin_required
def useri_toggle(user_id):
    user = db.get_or_404(User, user_id)
    user.active = not user.active
    db.session.commit()
    status = 'activat' if user.active else 'dezactivat'
    flash(f'Utilizatorul "{user.username}" a fost {status}.', 'success')
    return redirect(url_for('admin.useri'))
