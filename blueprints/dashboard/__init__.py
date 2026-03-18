from flask import Blueprint

# No url_prefix — dashboard routes register at application root (/, /dashboard, /dashboard/stats)
dashboard_bp = Blueprint('dashboard', __name__)

from blueprints.dashboard import routes  # noqa: F401, E402
