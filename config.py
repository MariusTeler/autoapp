import os


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    WTF_CSRF_ENABLED = True

    _db_url = os.environ.get('DATABASE_URL', '')
    SQLALCHEMY_DATABASE_URI = (
        _db_url.replace('postgres://', 'postgresql://', 1)
        if _db_url.startswith('postgres://')
        else (_db_url or 'sqlite:///autoapp.db')
    )
