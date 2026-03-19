from datetime import datetime, date, timezone
from flask import render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from sqlalchemy.exc import IntegrityError

from blueprints.avize import avize_bp
from models import db, Aviz, AvizMaterial, AvizServiciu, User, get_setting


def _check_ownership(aviz):
    """Abort 403 if current user doesn't own the aviz and is not admin."""
    if current_user.role != 'admin' and aviz.user_id != current_user.id:
        abort(403)


def _next_numar(an):
    """Calculate next sequential number for the given year (including soft-deleted rows)."""
    max_nr = db.session.query(db.func.max(Aviz.numar_secvential))\
        .filter(Aviz.an_aviz == an).scalar()
    return (max_nr or 0) + 1


def _save_aviz_items(aviz, form):
    """Parse materiale and servicii from form, replace existing rows."""
    # Clear existing items
    AvizMaterial.query.filter_by(aviz_id=aviz.id).delete()
    AvizServiciu.query.filter_by(aviz_id=aviz.id).delete()

    # Parse materiale
    idx = 0
    while f'materiale[{idx}][denumire]' in form:
        denumire = form.get(f'materiale[{idx}][denumire]', '').strip()
        if denumire:
            m = AvizMaterial(
                aviz_id=aviz.id,
                position=idx + 1,
                denumire=denumire,
                um=form.get(f'materiale[{idx}][um]', ''),
                cantitate=float(form.get(f'materiale[{idx}][cantitate]', 0) or 0),
                pret_unitar=float(form.get(f'materiale[{idx}][pret_unitar]', 0) or 0),
                valoare=float(form.get(f'materiale[{idx}][valoare]', 0) or 0),
            )
            db.session.add(m)
        idx += 1

    # Parse servicii
    idx = 0
    while f'servicii[{idx}][denumire]' in form:
        denumire = form.get(f'servicii[{idx}][denumire]', '').strip()
        if denumire:
            s = AvizServiciu(
                aviz_id=aviz.id,
                position=idx + 1,
                denumire=denumire,
                um=form.get(f'servicii[{idx}][um]', ''),
                cantitate=float(form.get(f'servicii[{idx}][cantitate]', 0) or 0),
                pret_unitar=float(form.get(f'servicii[{idx}][pret_unitar]', 0) or 0),
                valoare=float(form.get(f'servicii[{idx}][valoare]', 0) or 0),
            )
            db.session.add(s)
        idx += 1


@avize_bp.route('/')
@login_required
def lista():
    query = Aviz.query.filter(Aviz.deleted_at.is_(None))
    if current_user.role != 'admin':
        query = query.filter(Aviz.user_id == current_user.id)

    # Filters
    nr = request.args.get('nr', '').strip()
    data_de_la = request.args.get('data_de_la', '').strip()
    data_pana_la = request.args.get('data_pana_la', '').strip()
    beneficiar = request.args.get('beneficiar', '').strip()
    auto_nr = request.args.get('auto_nr', '').strip()
    user_id = request.args.get('user_id', '').strip()

    if nr:
        query = query.filter(Aviz.numar_complet.ilike(f'%{nr}%'))
    if data_de_la:
        try:
            query = query.filter(Aviz.data_aviz >= datetime.strptime(data_de_la, '%Y-%m-%d').date())
        except ValueError:
            pass
    if data_pana_la:
        try:
            query = query.filter(Aviz.data_aviz <= datetime.strptime(data_pana_la, '%Y-%m-%d').date())
        except ValueError:
            pass
    if beneficiar:
        query = query.filter(Aviz.beneficiar_nume.ilike(f'%{beneficiar}%'))
    if auto_nr:
        query = query.filter(Aviz.auto_nr.ilike(f'%{auto_nr}%'))
    if user_id and current_user.role == 'admin':
        query = query.filter(Aviz.user_id == int(user_id))

    users = User.query.filter_by(active=True).order_by(User.full_name).all() if current_user.role == 'admin' else []
    avize = query.order_by(Aviz.data_aviz.desc(), Aviz.numar_secvential.desc()).all()
    return render_template('avize/lista.html', avize=avize,
                           nr=nr, data_de_la=data_de_la, data_pana_la=data_pana_la,
                           beneficiar=beneficiar, auto_nr=auto_nr, user_id=user_id, users=users)


@avize_bp.route('/nou', methods=['GET', 'POST'])
@login_required
def nou():
    if request.method == 'POST':
        auto_nr = request.form.get('auto_nr', '').strip()
        auto_marca = request.form.get('auto_marca', '').strip()
        auto_model = request.form.get('auto_model', '').strip()

        if not auto_nr or not auto_marca or not auto_model:
            flash('Nr. Auto, Marcă și Model sunt obligatorii.', 'danger')
            return redirect(url_for('avize.nou'))

        an = date.today().year
        prefix = get_setting('aviz_prefix', 'SRV')
        tva = float(get_setting('aviz_tva', '19') or 19)

        def _create_aviz(nr_seq):
            numar_complet = f"{prefix}-{an}-{nr_seq:03d}"
            aviz = Aviz(
                numar_complet=numar_complet,
                numar_secvential=nr_seq,
                an_aviz=an,
                data_aviz=date.today(),
                user_id=current_user.id,
                tva_snapshot=tva,
                beneficiar_nume=request.form.get('beneficiar_nume', '').strip() or None,
                beneficiar_cif=request.form.get('beneficiar_cif', '').strip() or None,
                beneficiar_telefon=request.form.get('beneficiar_telefon', '').strip() or None,
                beneficiar_email=request.form.get('beneficiar_email', '').strip() or None,
                auto_nr=auto_nr,
                auto_marca=auto_marca,
                auto_model=auto_model,
                auto_serie_sasiu=request.form.get('auto_serie_sasiu', '').strip() or None,
                auto_serie_motor=request.form.get('auto_serie_motor', '').strip() or None,
                auto_an_fabricatie=int(request.form.get('auto_an_fabricatie') or 0) or None,
                auto_motorizare=request.form.get('auto_motorizare', '').strip() or None,
                auto_km=int(request.form.get('auto_km') or 0) or None,
                defect_reclamat=request.form.get('defect_reclamat', '').strip() or None,
                defecte_constatate=request.form.get('defecte_constatate', '').strip() or None,
            )
            return aviz

        # Try with retry for race condition
        for attempt in range(2):
            try:
                nr_seq = _next_numar(an)
                aviz = _create_aviz(nr_seq)
                db.session.add(aviz)
                db.session.flush()  # Get aviz.id before adding items
                _save_aviz_items(aviz, request.form)
                db.session.commit()
                flash(f'Avizul {aviz.numar_complet} a fost creat.', 'success')
                return redirect(url_for('avize.detaliu', aviz_id=aviz.id))
            except IntegrityError:
                db.session.rollback()
                if attempt == 1:
                    flash('Eroare la generarea numărului de aviz. Încearcă din nou.', 'danger')
                    return redirect(url_for('avize.nou'))

    tva = get_setting('aviz_tva', '19')
    settings = {
        'firma_denumire': get_setting('firma_denumire', ''),
        'firma_adresa': get_setting('firma_adresa', ''),
        'firma_localitate': get_setting('firma_localitate', ''),
        'firma_judet': get_setting('firma_judet', ''),
        'firma_cui': get_setting('firma_cui', ''),
        'firma_telefon': get_setting('firma_telefon', ''),
        'aviz_tva': tva,
    }
    return render_template('avize/formular.html', aviz=None, settings=settings,
                           today=date.today().strftime('%d.%m.%Y'))


@avize_bp.route('/<int:aviz_id>')
@login_required
def detaliu(aviz_id):
    aviz = Aviz.query.filter_by(id=aviz_id, deleted_at=None).first_or_404()
    _check_ownership(aviz)
    settings = {k: get_setting(k, '') for k in [
        'firma_denumire', 'firma_adresa', 'firma_localitate',
        'firma_judet', 'firma_cui', 'firma_telefon',
        'footer_titlu', 'footer_text'
    ]}
    return render_template('avize/detaliu.html', aviz=aviz, settings=settings)


@avize_bp.route('/<int:aviz_id>/editeaza', methods=['GET', 'POST'])
@login_required
def editeaza(aviz_id):
    aviz = Aviz.query.filter_by(id=aviz_id, deleted_at=None).first_or_404()
    _check_ownership(aviz)

    if request.method == 'POST':
        auto_nr = request.form.get('auto_nr', '').strip()
        auto_marca = request.form.get('auto_marca', '').strip()
        auto_model = request.form.get('auto_model', '').strip()

        if not auto_nr or not auto_marca or not auto_model:
            flash('Nr. Auto, Marcă și Model sunt obligatorii.', 'danger')
            return redirect(url_for('avize.editeaza', aviz_id=aviz_id))

        aviz.beneficiar_nume = request.form.get('beneficiar_nume', '').strip() or None
        aviz.beneficiar_cif = request.form.get('beneficiar_cif', '').strip() or None
        aviz.beneficiar_telefon = request.form.get('beneficiar_telefon', '').strip() or None
        aviz.beneficiar_email = request.form.get('beneficiar_email', '').strip() or None
        aviz.auto_nr = auto_nr
        aviz.auto_marca = auto_marca
        aviz.auto_model = auto_model
        aviz.auto_serie_sasiu = request.form.get('auto_serie_sasiu', '').strip() or None
        aviz.auto_serie_motor = request.form.get('auto_serie_motor', '').strip() or None
        aviz.auto_an_fabricatie = int(request.form.get('auto_an_fabricatie') or 0) or None
        aviz.auto_motorizare = request.form.get('auto_motorizare', '').strip() or None
        aviz.auto_km = int(request.form.get('auto_km') or 0) or None
        aviz.defect_reclamat = request.form.get('defect_reclamat', '').strip() or None
        aviz.defecte_constatate = request.form.get('defecte_constatate', '').strip() or None

        _save_aviz_items(aviz, request.form)
        db.session.commit()
        flash('Avizul a fost actualizat.', 'success')
        return redirect(url_for('avize.detaliu', aviz_id=aviz.id))

    settings = {
        'firma_denumire': get_setting('firma_denumire', ''),
        'firma_adresa': get_setting('firma_adresa', ''),
        'firma_localitate': get_setting('firma_localitate', ''),
        'firma_judet': get_setting('firma_judet', ''),
        'firma_cui': get_setting('firma_cui', ''),
        'firma_telefon': get_setting('firma_telefon', ''),
        'aviz_tva': aviz.tva_snapshot,
    }
    return render_template('avize/formular.html', aviz=aviz, settings=settings,
                           today=aviz.data_aviz.strftime('%d.%m.%Y'))


@avize_bp.route('/<int:aviz_id>/sterge', methods=['POST'])
@login_required
def sterge(aviz_id):
    aviz = Aviz.query.filter_by(id=aviz_id, deleted_at=None).first_or_404()
    _check_ownership(aviz)
    aviz.deleted_at = datetime.now(timezone.utc)
    db.session.commit()
    flash(f'Avizul {aviz.numar_complet} a fost șters.', 'success')
    return redirect(url_for('avize.lista'))


@avize_bp.route('/<int:aviz_id>/print')
@login_required
def print_aviz(aviz_id):
    aviz = Aviz.query.filter_by(id=aviz_id, deleted_at=None).first_or_404()
    _check_ownership(aviz)
    settings = {k: get_setting(k, '') for k in [
        'firma_denumire', 'firma_adresa', 'firma_localitate',
        'firma_judet', 'firma_cui', 'firma_telefon',
        'footer_titlu', 'footer_text'
    ]}
    return render_template('avize/print.html', aviz=aviz, settings=settings)
