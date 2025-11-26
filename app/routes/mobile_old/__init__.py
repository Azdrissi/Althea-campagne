from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.models import Student
from app import db
from datetime import datetime
from werkzeug.utils import secure_filename
import os

bp = Blueprint('mobile', __name__, url_prefix='/mobile')

UPLOAD_FOLDER = 'data/photos'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@bp.route('/students')
def list_students():
    """Liste des élèves pour mobile"""
    students = Student.query.order_by(Student.classe, Student.nom).all()
    return render_template('mobile/student_list.html', students=students)

@bp.route('/student/<int:id>', methods=['GET'])
def view_student(id):
    """Afficher fiche élève (GET)"""
    student = Student.query.get_or_404(id)
    return render_template('mobile/student_form.html', student=student)

@bp.route('/student/<int:id>', methods=['POST'])
def update_student(id):
    """Sauvegarder fiche élève avec photo (POST)"""
    try:
        student = Student.query.get_or_404(id)

        # Mettre à jour les données
        student.age = request.form.get('age', type=int)
        student.classe = request.form.get('classe')

        student.acuite_od = request.form.get('acuite_od', type=int)
        student.acuite_og = request.form.get('acuite_og', type=int)

        student.sph_od = request.form.get('sph_od', type=float)
        student.cyl_od = request.form.get('cyl_od', type=float)
        student.axe_od = request.form.get('axe_od', type=int)

        student.sph_og = request.form.get('sph_og', type=float)
        student.cyl_og = request.form.get('cyl_og', type=float)
        student.axe_og = request.form.get('axe_og', type=int)

        student.ep_pupillometre_od = request.form.get('ep_pupillometre_od', type=float)
        student.ep_pupillometre_og = request.form.get('ep_pupillometre_og', type=float)

        # Prise en charge
        prise_en_charge = request.form.getlist('prise_en_charge')
        student.prise_en_charge = ','.join(prise_en_charge) if prise_en_charge else None

        student.observations = request.form.get('observations')

        # Workflow action
        workflow_action = request.form.get('workflow_action')
        if workflow_action == 'opticien':
            student.status = 'screened'
        elif workflow_action == 'ophtalmo':
            student.status = 'consulted'
        elif workflow_action == 'cloture':
            student.status = 'completed'

        # ⭐ GESTION PHOTO
        if 'photo' in request.files:
            file = request.files['photo']
            if file and file.filename and allowed_file(file.filename):
                # Créer dossier si nécessaire
                os.makedirs(UPLOAD_FOLDER, exist_ok=True)

                # Nom du fichier sécurisé
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = secure_filename(f"{student.id}_{timestamp}_{file.filename}")
                filepath = os.path.join(UPLOAD_FOLDER, filename)

                # Sauvegarder
                file.save(filepath)
                student.photo_monture = filepath

        student.updated_at = datetime.utcnow()
        db.session.commit()

        flash('✅ Élève enregistré avec succès !', 'success')
        return redirect(url_for('mobile.list_students'))

    except Exception as e:
        db.session.rollback()
        flash(f'❌ Erreur: {str(e)}', 'danger')
        return redirect(url_for('mobile.view_student', id=id))
