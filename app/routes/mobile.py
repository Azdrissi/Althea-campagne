from flask import Blueprint, render_template, request, jsonify, redirect, url_for
from app.models import Student, SessionEcole
from app import db
from datetime import datetime
import os
import base64

bp = Blueprint('mobile', __name__, url_prefix='/mobile')


@bp.route('/')
def index():
    """Page d'accueil mobile - redirige vers la liste des élèves."""
    return redirect(url_for('mobile.list_students'))


@bp.route('/students')
def list_students():
    """Liste des élèves côté mobile, filtrée par session école active, triée par dernière mise à jour."""
    session_active = SessionEcole.get_active()

    status_filter = request.args.get('status', '').strip()

    if session_active:
        students_query = Student.query.filter_by(
            ville=session_active.ville,
            ecole=session_active.ecole
        )
    else:
        students_query = Student.query

    if status_filter:
        students_query = students_query.filter_by(status=status_filter)

    students = students_query.order_by(
        Student.updated_at.desc().nullslast(),
        Student.id.desc()
    ).all()

    return render_template(
        'mobile/student_list.html',
        students=students,
        session_active=session_active,
        status_filter=status_filter
    )


@bp.route('/student/<int:id>')
def edit_student(id):
    """Formulaire de consultation mobile pour un élève donné."""
    student = Student.query.get_or_404(id)
    return render_template('mobile/student_form.html', student=student)


@bp.route('/student/<int:id>/save', methods=['POST'])
def save_student(id):
    """Sauvegarde des données médicales (version mobile)."""
    try:
        student = Student.query.get_or_404(id)

        # Informations de base éventuellement modifiables
        age = request.form.get('age', type=int)
        if age is not None:
            student.age = age
        classe = request.form.get('classe')
        if classe:
            student.classe = classe

        # Acuité visuelle (sélection 10 -> 1)
        student.acuite_od = request.form.get('acuite_od', type=float)
        student.acuite_og = request.form.get('acuite_og', type=float)

        # Prescription OD
        student.sph_od = request.form.get('sph_od', type=float)
        student.cyl_od = request.form.get('cyl_od', type=float)
        student.axe_od = request.form.get('axe_od', type=int)

        # Prescription OG
        student.sph_og = request.form.get('sph_og', type=float)
        student.cyl_og = request.form.get('cyl_og', type=float)
        student.axe_og = request.form.get('axe_og', type=int)

        # EP (20–35 mm selon les templates)
        student.ep_pupillometre_od = request.form.get('ep_pupillometre_od', type=float)
        student.ep_pupillometre_og = request.form.get('ep_pupillometre_og', type=float)

        # Observations
        student.observations = request.form.get('observations')

        # Prises en charge (cases à cocher)
        prises_list = request.form.getlist('prise_en_charge')
        if prises_list:
            student.prise_en_charge = ",".join([p for p in prises_list if p])
        else:
            student.prise_en_charge = None

        # LOGIQUE STATUT / CONSULTATION
        has_consult_data = any([
            student.acuite_od is not None,
            student.acuite_og is not None,
            student.sph_od is not None,
            student.sph_og is not None,
        ])
        has_pec = bool(student.prise_en_charge)

        if has_consult_data or has_pec:
            # Passage automatique de pré-listé à pris en charge
            if student.status == 'prelisted':
                student.status = 'completed'
            # Date de consultation
            if hasattr(student, 'date_consultation'):
                student.date_consultation = datetime.utcnow()

        # Mise à jour timestamp
        if hasattr(student, 'updated_at'):
            student.updated_at = datetime.utcnow()

        db.session.commit()
        return redirect(url_for('mobile.list_students'))

    except Exception:
        db.session.rollback()
        return redirect(url_for('mobile.edit_student', id=id))


@bp.route('/student/<int:id>/upload_photo', methods=['POST'])
def upload_photo(id):
    """Upload d'une photo depuis le mobile (base64), pour portrait / monture / clinique."""
    try:
        student = Student.query.get_or_404(id)
        photo_type = request.form.get('photo_type')  # portrait, monture, clinique
        photo_data = request.form.get('photo_data')  # base64

        if not photo_type or photo_type not in ['portrait', 'monture', 'clinique']:
            return jsonify({'success': False, 'error': 'Type de photo invalide'}), 400

        if not photo_data:
            return jsonify({'success': False, 'error': 'Aucune photo fournie'}), 400

        # Décoder le base64
        if ',' in photo_data:
            photo_data = photo_data.split(',', 1)[1]
        photo_bytes = base64.b64decode(photo_data)

        # Construire le chemin de sauvegarde
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
        photos_dir = os.path.join(base_dir, 'data', 'photos', f'{photo_type}s')
        os.makedirs(photos_dir, exist_ok=True)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{student.id}_{photo_type}_{timestamp}.jpg"
        filepath = os.path.join(photos_dir, filename)

        with open(filepath, 'wb') as f:
            f.write(photo_bytes)

        # Enregistrer le chemin relatif dans la base
        rel_path = f"data/photos/{photo_type}s/{filename}"
        if photo_type == 'portrait' and hasattr(student, 'photo_portrait'):
            student.photo_portrait = rel_path
        elif photo_type == 'monture' and hasattr(student, 'photo_monture'):
            student.photo_monture = rel_path
        elif photo_type == 'clinique' and hasattr(student, 'photo_clinique'):
            student.photo_clinique = rel_path

        if hasattr(student, 'updated_at'):
            student.updated_at = datetime.utcnow()

        db.session.commit()

        return jsonify({'success': True, 'filename': filename})

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 400


@bp.route('/search')
def search():
    """Recherche rapide pour l'interface mobile (auto-complétion)."""
    query = request.args.get('q', '').strip()

    if not query or len(query) < 2:
        return jsonify([])

    session_active = SessionEcole.get_active()
    students_query = Student.query

    if session_active:
        students_query = students_query.filter_by(
            ville=session_active.ville,
            ecole=session_active.ecole
        )

    search_term = f"%{query}%"
    students = students_query.filter(
        db.or_(
            Student.nom.ilike(search_term),
            Student.prenom.ilike(search_term)
        )
    ).limit(20).all()

    return jsonify([{
        'id': s.id,
        'nom': s.nom,
        'prenom': s.prenom,
        'classe': s.classe,
        'status': s.status,
        'status_label': s.get_status_label()
    } for s in students])
