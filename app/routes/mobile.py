from flask import Blueprint, render_template, request, jsonify, redirect, url_for
from app.models import Student, SessionEcole
from app import db
from werkzeug.utils import secure_filename
import os
from datetime import datetime
import base64

bp = Blueprint('mobile', __name__, url_prefix='/mobile')

@bp.route('/')
def index():
    """Page d'accueil mobile - redirige vers la liste des élèves"""
    return redirect(url_for('mobile.list_students'))

@bp.route('/students')
def list_students():
    """Liste des élèves filtrée par école active"""
    session_active = SessionEcole.get_active()

    # Filtre par statut (optionnel)
    status_filter = request.args.get('status', '')

    if session_active:
        students_query = Student.query.filter_by(
            ville=session_active.ville,
            ecole=session_active.ecole
        )
    else:
        students_query = Student.query

    # Appliquer le filtre de statut si présent
    if status_filter:
        students_query = students_query.filter_by(status=status_filter)

    students = students_query.order_by(Student.classe, Student.nom, Student.prenom).all()

    return render_template('mobile/student_list.html', 
                         students=students, 
                         session_active=session_active,
                         status_filter=status_filter)

@bp.route('/student/<int:id>')
def edit_student(id):
    """Formulaire de consultation mobile"""
    student = Student.query.get_or_404(id)
    return render_template('mobile/student_form.html', student=student)

@bp.route('/student/<int:id>/save', methods=['POST'])
def save_student(id):
    """Sauvegarde des données médicales (version HTML classique)"""
    try:
        student = Student.query.get_or_404(id)

        # Acuité visuelle
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

        # Écart pupillaire
        student.ecart_pupillaire = request.form.get('ecart_pupillaire', type=float)

        # Observations
        student.observations = request.form.get('observations')

        # Type de prise en charge
        student.type_prise_en_charge = request.form.get('type_prise_en_charge')

        # Statut (optionnel)
        status = request.form.get('status')
        if status is not None and status != '':
            student.status = int(status)

        db.session.commit()

        # Après sauvegarde : retour à la liste des élèves mobile
        return redirect(url_for('mobile.list_students'))

    except Exception as e:
        db.session.rollback()
        # En cas d'erreur, on revient aussi sur la fiche avec un message dans la console
        # (on pourrait utiliser flash si besoin)
        return redirect(url_for('mobile.edit_student', id=id))
@bp.route('/student/<int:id>/upload_photo', methods=['POST'])
def upload_photo(id):
    """Upload photo depuis le smartphone"""
    try:
        student = Student.query.get_or_404(id)
        photo_type = request.form.get('photo_type')  # portrait, monture, clinique
        photo_data = request.form.get('photo_data')  # Base64

        if not photo_type or photo_type not in ['portrait', 'monture', 'clinique']:
            return jsonify({'success': False, 'error': 'Type de photo invalide'}), 400

        if not photo_data:
            return jsonify({'success': False, 'error': 'Aucune photo fournie'}), 400

        # Décoder le base64
        photo_data = photo_data.split(',')[1] if ',' in photo_data else photo_data
        photo_bytes = base64.b64decode(photo_data)

        # Créer le nom de fichier
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{student.id}_{photo_type}_{timestamp}.jpg"

        # Chemin du dossier
        basedir = os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        photo_dir = os.path.join(basedir, 'data', 'photos', f'{photo_type}s')
        os.makedirs(photo_dir, exist_ok=True)

        # Sauvegarder le fichier
        filepath = os.path.join(photo_dir, filename)
        with open(filepath, 'wb') as f:
            f.write(photo_bytes)

        # Mettre à jour la base de données
        relative_path = f'data/photos/{photo_type}s/{filename}'
        if photo_type == 'portrait':
            student.photo_portrait = relative_path
        elif photo_type == 'monture':
            student.photo_monture = relative_path
        elif photo_type == 'clinique':
            student.photo_clinique = relative_path

        db.session.commit()

        return jsonify({
            'success': True, 
            'message': 'Photo enregistrée !',
            'filename': filename
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 400

@bp.route('/search')
def search():
    """Recherche rapide"""
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
