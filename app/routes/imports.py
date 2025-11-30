from flask import Blueprint, render_template, request, flash, redirect, url_for, session
from app.models import Student
from app import db
import pandas as pd
from werkzeug.utils import secure_filename
import os

bp = Blueprint('imports', __name__, url_prefix='/imports')

ALLOWED_EXTENSIONS = {'xlsx', 'xls', 'csv'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@bp.route('/')
def index():
    return render_template('imports.html')

@bp.route('/import_excel', methods=['POST'])
def import_excel():
    """Importer élèves depuis Excel/CSV"""
    try:
        # ✅ Vérifier qu'une session école est active
        if 'session_active' not in session:
            flash('Veuillez d\'abord démarrer une école', 'danger')
            return redirect(url_for('index'))

        session_active = session['session_active']
        ville = session_active['ville']
        ecole = session_active['ecole']

        if 'file' not in request.files:
            flash('Aucun fichier sélectionné', 'danger')
            return redirect(url_for('imports.index'))

        file = request.files['file']

        if file.filename == '':
            flash('Aucun fichier sélectionné', 'danger')
            return redirect(url_for('imports.index'))

        if not allowed_file(file.filename):
            flash('Format non autorisé. Utilisez .xlsx, .xls ou .csv', 'danger')
            return redirect(url_for('imports.index'))

        # Lire le fichier
        if file.filename.endswith('.csv'):
            df = pd.read_csv(file)
        else:
            df = pd.read_excel(file)

        # ✅ Colonnes requises (SANS Ville et École car on les prend de la session)
        required_cols = ['Nom', 'Prénom']
        missing_cols = [col for col in required_cols if col not in df.columns]

        if missing_cols:
            flash(f'Colonnes manquantes: {", ".join(missing_cols)}', 'danger')
            return redirect(url_for('imports.index'))

        # Importer les élèves
        imported = 0
        errors = 0

        for _, row in df.iterrows():
            try:
                # ✅ Ville et École viennent de la session active
                # ✅ Site vient de "Nom École" dans le fichier Excel
                site_value = row.get('Nom École', 'École Principale')

                # ✅ Support "Niveau" et "Classe"
                classe_value = row.get('Classe', row.get('Niveau', ''))

                student = Student(
                    nom=row.get('Nom'),
                    prenom=row.get('Prénom'),
                    ville=ville,  # ✅ Depuis la session
                    ecole=ecole,  # ✅ Depuis la session
                    site=site_value,  # ✅ Depuis "Nom École" dans Excel
                    classe=classe_value,  # ✅ Support Niveau ou Classe
                    age=row.get('Âge'),
                    status='prelisted'
                )

                db.session.add(student)
                imported += 1
            except Exception as e:
                errors += 1
                print(f"Erreur import ligne {_}: {e}")

        db.session.commit()

        if imported > 0:
            flash(f'✅ {imported} élève(s) importé(s) avec succès ! {errors} erreur(s).', 'success')
        else:
            flash(f'⚠️ Aucun élève importé. {errors} erreur(s).', 'warning')

        return redirect(url_for('students.list_students'))

    except Exception as e:
        db.session.rollback()
        flash(f'Erreur lors de l\'import: {str(e)}', 'danger')
        return redirect(url_for('imports.index'))
