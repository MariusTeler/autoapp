from functools import wraps
from flask import abort
from flask_login import current_user


def admin_required(f):
    """Restrict route to admin users only. Must be used after @login_required."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            abort(403)
        return f(*args, **kwargs)
    return decorated
