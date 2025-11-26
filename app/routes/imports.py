from flask import Blueprint, render_template, request, flash, redirect, url_for
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

        # Colonnes requises
        required_cols = ['Nom', 'Prénom', 'Ville', 'École']
        missing_cols = [col for col in required_cols if col not in df.columns]

        if missing_cols:
            flash(f'Colonnes manquantes: {", ".join(missing_cols)}', 'danger')
            return redirect(url_for('imports.index'))

        # Importer les élèves
        imported = 0
        errors = 0

        for _, row in df.iterrows():
            try:
                student = Student(
                    nom=row.get('Nom'),
                    prenom=row.get('Prénom'),
                    ville=row.get('Ville'),
                    ecole=row.get('École'),
                    classe=row.get('Classe'),
                    age=row.get('Âge'),
                    status='prelisted'
                )
                db.session.add(student)
                imported += 1
            except Exception as e:
                errors += 1

        db.session.commit()

        flash(f'{imported} élève(s) importé(s) avec succès. {errors} erreur(s).', 'success')
        return redirect(url_for('imports.index'))

    except Exception as e:
        db.session.rollback()
        flash(f'Erreur lors de l\'import: {str(e)}', 'danger')
        return redirect(url_for('imports.index'))
