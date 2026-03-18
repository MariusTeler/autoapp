from flask import Blueprint

avize_bp = Blueprint('avize', __name__, url_prefix='/avize')

from blueprints.avize import routes  # noqa: F401, E402
