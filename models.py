from datetime import datetime, date, timezone
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    full_name = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='user')  # 'admin' or 'user'
    active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    avize = db.relationship('Aviz', backref='user', lazy=True)

    __table_args__ = (
        db.CheckConstraint("role IN ('admin', 'user')", name='ck_user_role'),
    )

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'


class Setting(db.Model):
    __tablename__ = 'settings'

    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False)
    value = db.Column(db.Text, nullable=True)

    def __repr__(self):
        return f'<Setting {self.key}={self.value}>'


class Aviz(db.Model):
    __tablename__ = 'avize'

    id = db.Column(db.Integer, primary_key=True)
    numar_complet = db.Column(db.String(50), nullable=False, unique=True)
    numar_secvential = db.Column(db.Integer, nullable=False)
    an_aviz = db.Column(db.Integer, nullable=False)
    data_aviz = db.Column(db.Date, nullable=False, default=date.today)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    # Beneficiar
    beneficiar_nume = db.Column(db.String(200))
    beneficiar_cif = db.Column(db.String(50))
    beneficiar_telefon = db.Column(db.String(50))
    beneficiar_email = db.Column(db.String(200))

    # Autovehicul
    auto_nr = db.Column(db.String(20), nullable=False)
    auto_marca = db.Column(db.String(100), nullable=False)
    auto_model = db.Column(db.String(100), nullable=False)
    auto_serie_sasiu = db.Column(db.String(100))
    auto_serie_motor = db.Column(db.String(100))
    auto_an_fabricatie = db.Column(db.Integer)
    auto_motorizare = db.Column(db.String(100))
    auto_km = db.Column(db.Integer)

    # Defecte
    defect_reclamat = db.Column(db.Text)
    defecte_constatate = db.Column(db.Text)

    # Financiar
    tva_snapshot = db.Column(db.Float, nullable=False, default=19.0)

    # Meta
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    deleted_at = db.Column(db.DateTime, nullable=True)

    # Unique constraint to prevent duplicate sequential numbers per year
    __table_args__ = (
        db.UniqueConstraint('numar_secvential', 'an_aviz', name='uq_aviz_nr_an'),
    )

    materiale = db.relationship('AvizMaterial', backref='aviz', lazy=True,
                                order_by='AvizMaterial.position',
                                cascade='all, delete-orphan')
    servicii = db.relationship('AvizServiciu', backref='aviz', lazy=True,
                               order_by='AvizServiciu.position',
                               cascade='all, delete-orphan')

    @property
    def total_materiale(self):
        return sum(m.valoare or 0 for m in self.materiale)

    @property
    def total_servicii(self):
        return sum(s.valoare or 0 for s in self.servicii)

    @property
    def total_general(self):
        return self.total_materiale + self.total_servicii

    @property
    def tva_valoare(self):
        return self.total_general * (self.tva_snapshot / 100)

    @property
    def total_de_plata(self):
        return self.total_general + self.tva_valoare

    def __repr__(self):
        return f'<Aviz {self.numar_complet}>'


class AvizMaterial(db.Model):
    __tablename__ = 'aviz_materiale'

    id = db.Column(db.Integer, primary_key=True)
    aviz_id = db.Column(db.Integer, db.ForeignKey('avize.id'), nullable=False)
    position = db.Column(db.Integer, nullable=False, default=1)
    denumire = db.Column(db.String(300))
    um = db.Column(db.String(20))
    cantitate = db.Column(db.Float, default=0.0)
    pret_unitar = db.Column(db.Float, default=0.0)
    valoare = db.Column(db.Float, default=0.0)

    def __repr__(self):
        return f'<AvizMaterial {self.denumire}>'


class AvizServiciu(db.Model):
    __tablename__ = 'aviz_servicii'

    id = db.Column(db.Integer, primary_key=True)
    aviz_id = db.Column(db.Integer, db.ForeignKey('avize.id'), nullable=False)
    position = db.Column(db.Integer, nullable=False, default=1)
    denumire = db.Column(db.String(300))
    um = db.Column(db.String(20))
    cantitate = db.Column(db.Float, default=0.0)
    pret_unitar = db.Column(db.Float, default=0.0)
    valoare = db.Column(db.Float, default=0.0)

    def __repr__(self):
        return f'<AvizServiciu {self.denumire}>'


# ── Helpers ──────────────────────────────────────────────────────────────────

def get_setting(key, default=None):
    """Return the value for a settings key, or default if not found."""
    s = Setting.query.filter_by(key=key).first()
    return s.value if s else default


def set_setting(key, value):
    """Insert or update a settings key. Caller is responsible for db.session.commit()."""
    s = Setting.query.filter_by(key=key).first()
    if s:
        s.value = value
    else:
        s = Setting(key=key, value=value)
        db.session.add(s)
