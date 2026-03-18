from flask import Blueprint

configurare_bp = Blueprint('configurare', __name__, url_prefix='/configurare')

from blueprints.configurare import routes  # noqa: F401, E402
