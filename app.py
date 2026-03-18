from flask import Flask
from flask_login import LoginManager
from flask_wtf import CSRFProtect
from flask_migrate import Migrate

from config import Config
from models import db, User


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Extensions — instantiated inside factory for test isolation
    login_manager = LoginManager()
    csrf = CSRFProtect()
    migrate = Migrate()

    db.init_app(app)
    csrf.init_app(app)
    migrate.init_app(app, db)

    # Configure login_manager BEFORE init_app (correct order per Flask-Login docs)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Te rugăm să te autentifici pentru a accesa această pagină.'
    login_manager.login_message_category = 'warning'
    login_manager.init_app(app)

    # User loader
    @login_manager.user_loader
    def load_user(user_id):
        user = db.session.get(User, int(user_id))
        return user if (user and user.active) else None

    # Jinja2 filter: Romanian number format "1.234,56"
    def format_ron(value):
        try:
            return f"{float(value):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        except (ValueError, TypeError):
            return "0,00"

    app.jinja_env.filters['format_ron'] = format_ron
    app.jinja_env.globals['enumerate'] = enumerate  # used in Jinja2 templates

    # Register blueprints
    from blueprints.auth import auth_bp
    from blueprints.admin import admin_bp
    from blueprints.dashboard import dashboard_bp
    from blueprints.avize import avize_bp
    from blueprints.configurare import configurare_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(avize_bp)
    app.register_blueprint(configurare_bp)

    # Seed default admin user on first run
    from sqlalchemy.exc import OperationalError, ProgrammingError
    with app.app_context():
        try:
            if db.session.scalar(db.select(db.func.count(User.id))) == 0:
                admin = User(
                    username='admin',
                    full_name='Administrator',
                    role='admin',
                    active=True
                )
                admin.set_password('admin123')
                db.session.add(admin)
                db.session.commit()
        except (OperationalError, ProgrammingError):
            db.session.rollback()
            pass  # Tables not yet created — run flask db upgrade first

    return app
