from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required

from blueprints.configurare import configurare_bp
from decorators import admin_required
from models import db, get_setting, set_setting

SETTING_KEYS = [
    'firma_denumire', 'firma_adresa', 'firma_localitate',
    'firma_judet', 'firma_cui', 'firma_telefon',
    'aviz_prefix', 'aviz_tva',
    'footer_titlu', 'footer_text',
]


@configurare_bp.route('/', methods=['GET', 'POST'])
@login_required
@admin_required
def index():
    if request.method == 'POST':
        for key in SETTING_KEYS:
            value = request.form.get(key, '').strip()
            set_setting(key, value)
        db.session.commit()
        flash('Configurarea a fost salvată.', 'success')
        return redirect(url_for('configurare.index'))

    settings = {key: get_setting(key, '') for key in SETTING_KEYS}
    return render_template('configurare/index.html', settings=settings)
