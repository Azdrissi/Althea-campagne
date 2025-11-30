from flask import current_app, Blueprint, render_template, request, jsonify, redirect, url_for, flash, session
from werkzeug.utils import secure_filename
from app.models import Student
from app import db
from datetime import datetime
from sqlalchemy import or_

bp = Blueprint('students', __name__, url_prefix='/students')

# ---------------------------------------------------------
# LISTE DES ELEVES (tri : derniers modifiés en premier)
# ---------------------------------------------------------
@bp.route('/')
def list_students():
    search_term = request.args.get('search', '').strip()
    site_filter = request.args.get('site', '').strip()

    if 'session_active' in session:
        sa = session['session_active']
        query = Student.query.filter_by(ville=sa['ville'], ecole=sa['ecole'])
    else:
        query = Student.query

    if site_filter:
        query = query.filter_by(site=site_filter)

    if search_term:
        search_pattern = f'%{search_term}%'
        query = query.filter(
            or_(
                Student.nom.ilike(search_pattern),
                Student.prenom.ilike(search_pattern),
                Student.observations.ilike(search_pattern)
            )
        )

    students = query.order_by(
        Student.updated_at.desc().nullslast(),
        Student.id.desc()
    ).all()

    sites = []
    if 'session_active' in session:
        sa = session['session_active']
        rows = db.session.query(Student.site).filter_by(
            ville=sa['ville'], ecole=sa['ecole']
        ).distinct().all()
        sites = [s[0] for s in rows if s[0]]

    return render_template(
        'student_list.html',
        students=students,
        search_term=search_term,
        site_filter=site_filter,
        sites=sites
    )

# ---------------------------------------------------------
# NOUVEL ELEVE
# ---------------------------------------------------------
@bp.route('/new')
def new_student():
    if 'session_active' not in session:
        flash("Veuillez d'abord démarrer une école.", "danger")
        return redirect(url_for('index'))

    sa = session['session_active']

    rows = db.session.query(Student.site).filter_by(
        ville=sa['ville'], ecole=sa['ecole']
    ).distinct().all()
    available_sites = [s[0] for s in rows if s[0]]

    student = type('obj', (object,), {
        'id': None,
        'ville': sa['ville'],
        'ecole': sa['ecole'],
        'site': '',
        'nom': '',
        'prenom': '',
        'classe': '',
        'age': None,
        'acuite_od': None,
        'acuite_og': None,
        'sph_od': None,
        'sph_og': None,
        'cyl_od': None,
        'cyl_og': None,
        'axe_od': None,
        'axe_og': None,
        'ep_pupillometre_od': None,
        'ep_pupillometre_og': None,
        'prise_en_charge': None,
        'observations': '',
        'status': 'prelisted',
        'photo_monture': None,
        'updated_at': None
    })()

    return render_template('student_form.html', student=student, is_new=True, available_sites=available_sites)

# ---------------------------------------------------------
# CREATION
# ---------------------------------------------------------
@bp.route('/new', methods=['POST'])
def create_student():
    try:
        if 'session_active' not in session:
            flash("Veuillez d'abord démarrer une école", 'danger')
            return redirect(url_for('index'))

        sa = session['session_active']
        site = request.form.get('site')

        if not site:
            flash("Veuillez sélectionner un site/annexe", 'danger')
            return redirect(url_for('students.new_student'))

        student = Student(
            ville=sa['ville'],
            ecole=sa['ecole'],
            site=site,
            nom=request.form.get('nom'),
            prenom=request.form.get('prenom'),
            classe=request.form.get('classe'),
            age=request.form.get('age', type=int),
            status='prelisted',
            updated_at=datetime.utcnow()
        )

        db.session.add(student)
        db.session.commit()

        flash("Élève créé avec succès", "success")
        return redirect(url_for('students.edit_student', id=student.id))

    except Exception as e:
        db.session.rollback()
        flash(f"Erreur: {e}", "danger")
        return redirect(url_for('students.new_student'))

# ---------------------------------------------------------
# EDITER
# ---------------------------------------------------------
@bp.route('/edit/<int:id>')
def edit_student(id):
    student = Student.query.get_or_404(id)

    available_sites = []
    if 'session_active' in session:
        sa = session['session_active']
        rows = db.session.query(Student.site).filter_by(
            ville=sa['ville'], ecole=sa['ecole']
        ).distinct().all()
        available_sites = [s[0] for s in rows if s[0]]

    return render_template('student_form.html', student=student, is_new=False, available_sites=available_sites)

# ---------------------------------------------------------
# UPDATE
# ---------------------------------------------------------
@bp.route('/update/<int:id>', methods=['POST'])
def update_student(id):
    try:
        student = Student.query.get_or_404(id)

        student.nom = request.form.get('nom', student.nom)
        student.prenom = request.form.get('prenom', student.prenom)
        student.age = request.form.get('age', type=int)
        student.classe = request.form.get('classe', student.classe)

        new_site = request.form.get('site')
        if new_site:
            student.site = new_site

        student.acuite_od = request.form.get('acuite_od')
        student.acuite_og = request.form.get('acuite_og')

        student.sph_od = request.form.get('sph_od', type=float)
        student.sph_og = request.form.get('sph_og', type=float)
        student.cyl_od = request.form.get('cyl_od', type=float)
        student.cyl_og = request.form.get('cyl_og', type=float)
        student.axe_od = request.form.get('axe_od', type=float)
        student.axe_og = request.form.get('axe_og', type=float)

        student.ep_pupillometre_od = request.form.get('ep_pupillometre_od', type=float)
        student.ep_pupillometre_og = request.form.get('ep_pupillometre_og', type=float)

        pec = request.form.getlist('prise_en_charge')
        student.prise_en_charge = ','.join(pec) if pec else None

        student.observations = request.form.get('observations')

        # Passage automatique en "Pris en charge"
        has_consult = any([
            student.acuite_od,
            student.acuite_og,
            student.sph_od is not None,
            student.sph_og is not None,
            student.prise_en_charge
        ])

        if has_consult:
            if student.status == 'prelisted':
                student.status = 'completed'
            student.date_consultation = datetime.utcnow()

        student.updated_at = datetime.utcnow()

        db.session.commit()
        flash("Élève mis à jour", "success")
        return redirect(url_for('students.list_students'))

    except Exception as e:
        db.session.rollback()
        flash(f"Erreur: {e}", "danger")
        return redirect(url_for('students.edit_student', id=id))

# ---------------------------------------------------------
# DELETE
# ---------------------------------------------------------
@bp.route('/delete/<int:id>', methods=['POST'])
def delete_student(id):
    try:
        student = Student.query.get_or_404(id)
        db.session.delete(student)
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 400

# ---------------------------------------------------------
# IMPRESSIONS (pré-imprimé — individuel)
# ---------------------------------------------------------
@bp.route('/print_preprinted/<int:student_id>')
def print_student_preprinted(student_id):
    student = Student.query.get_or_404(student_id)
    return render_template('print_preprinted.html', student=student)

# ---------------------------------------------------------
# IMPRESSION FICHE COMPLETE — INDIVIDUELLE
# ---------------------------------------------------------
@bp.route('/print_full/<int:student_id>')
def print_student_full(student_id):
    student = Student.query.get_or_404(student_id)
    return render_template('print_full.html', student=student)

# ---------------------------------------------------------
# IMPRESSION TOUTES FICHES — PRE-IMPRIME
# ---------------------------------------------------------
@bp.route('/print_all_preprinted')
def print_all_preprinted():
    site = request.args.get('site', '').strip()

    if 'session_active' in session:
        sa = session['session_active']
        query = Student.query.filter_by(ville=sa['ville'], ecole=sa['ecole'])
    else:
        query = Student.query

    if site:
        query = query.filter_by(site=site)

    students = query.order_by(Student.site, Student.classe, Student.nom).all()

    if not students:
        flash("Aucun élève pour ce filtre", "warning")
        return redirect(url_for('students.list_students'))

    return render_template('print_preprinted_all.html', students=students)

# ---------------------------------------------------------
# IMPRESSION TOUTES FICHES — COMPLET
# ---------------------------------------------------------
@bp.route('/print_all_full')
def print_all_full():
    site = request.args.get('site', '').strip()

    if 'session_active' in session:
        sa = session['session_active']
        query = Student.query.filter_by(ville=sa['ville'], ecole=sa['ecole'])
    else:
        query = Student.query

    if site:
        query = query.filter_by(site=site)

    students = query.order_by(Student.site, Student.classe, Student.nom).all()

    if not students:
        flash("Aucun élève pour ce filtre", "warning")
        return redirect(url_for('students.list_students'))

    return render_template('print_full_all.html', students=students)
