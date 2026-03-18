from datetime import datetime
from flask import render_template, request
from flask_login import login_required, current_user
from sqlalchemy import func

from blueprints.dashboard import dashboard_bp
from models import db, Aviz, AvizMaterial, AvizServiciu, User


def _get_stats(luna, an):
    """Return stats dict for the given month/year, scoped to current user or all (admin)."""
    query = Aviz.query.filter(
        Aviz.deleted_at.is_(None),
        func.extract('month', Aviz.data_aviz) == luna,
        func.extract('year', Aviz.data_aviz) == an,
    )
    if current_user.role != 'admin':
        query = query.filter(Aviz.user_id == current_user.id)

    avize = query.all()
    aviz_ids = [a.id for a in avize]

    total_materiale = db.session.query(func.sum(AvizMaterial.valoare))\
        .filter(AvizMaterial.aviz_id.in_(aviz_ids)).scalar() or 0

    total_servicii = db.session.query(func.sum(AvizServiciu.valoare))\
        .filter(AvizServiciu.aviz_id.in_(aviz_ids)).scalar() or 0

    return {
        'nr_avize': len(avize),
        'total_materiale': total_materiale,
        'total_servicii': total_servicii,
        'total_general': total_materiale + total_servicii,
    }


def _get_admin_per_user(luna, an):
    """Return list of per-user stats for admin view."""
    result = []
    users = User.query.filter_by(active=True).all()
    for user in users:
        avize = Aviz.query.filter(
            Aviz.deleted_at.is_(None),
            Aviz.user_id == user.id,
            func.extract('month', Aviz.data_aviz) == luna,
            func.extract('year', Aviz.data_aviz) == an,
        ).all()
        aviz_ids = [a.id for a in avize]
        total_m = db.session.query(func.sum(AvizMaterial.valoare))\
            .filter(AvizMaterial.aviz_id.in_(aviz_ids)).scalar() or 0
        total_s = db.session.query(func.sum(AvizServiciu.valoare))\
            .filter(AvizServiciu.aviz_id.in_(aviz_ids)).scalar() or 0
        result.append({
            'user': user,
            'nr_avize': len(avize),
            'total_materiale': total_m,
            'total_servicii': total_s,
        })
    return result


@dashboard_bp.route('/')
@dashboard_bp.route('/dashboard')
@login_required
def index():
    now = datetime.now()
    luna = int(request.args.get('luna', now.month))
    an = int(request.args.get('an', now.year))

    stats = _get_stats(luna, an)

    # Recent avize
    q = Aviz.query.filter(Aviz.deleted_at.is_(None))
    if current_user.role != 'admin':
        q = q.filter(Aviz.user_id == current_user.id)
    avize_recente = q.order_by(Aviz.created_at.desc()).limit(10).all()

    per_user = _get_admin_per_user(luna, an) if current_user.role == 'admin' else []

    luni = ['Ianuarie', 'Februarie', 'Martie', 'Aprilie', 'Mai', 'Iunie',
            'Iulie', 'August', 'Septembrie', 'Octombrie', 'Noiembrie', 'Decembrie']
    ani = list(range(2023, now.year + 2))

    return render_template('dashboard/index.html',
                           stats=stats, avize_recente=avize_recente,
                           per_user=per_user, luna=luna, an=an,
                           luni=luni, ani=ani)


@dashboard_bp.route('/dashboard/stats')
@login_required
def stats():
    now = datetime.now()
    luna = int(request.args.get('luna', now.month))
    an = int(request.args.get('an', now.year))
    stats = _get_stats(luna, an)
    return render_template('dashboard/_stats.html', stats=stats, luna=luna, an=an)
