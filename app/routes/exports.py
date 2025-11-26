from flask import Blueprint, render_template, send_file, flash, redirect, url_for, current_app
from app.models import Student
from app import db
import pandas as pd
from datetime import datetime
import os

bp = Blueprint('exports', __name__, url_prefix='/exports')

@bp.route('/')
def index():
    """Page simple d'export : un seul bouton Export Excel"""
    total_students = Student.query.count()
    return render_template('exports.html', total_students=total_students)

@bp.route('/excel')
def export_excel():
    """Exporte tous les élèves en un fichier Excel"""
    try:
        students = Student.query.all()
        if not students:
            flash("Aucun élève à exporter", "warning")
            return redirect(url_for('exports.index'))

        # Préparer les données pour l'export
        data = []
        for s in students:
            data.append({
                'ID': s.id,
                'Ville': getattr(s, 'ville', ''),
                'École': getattr(s, 'ecole', ''),
                'Classe': getattr(s, 'classe', ''),
                'Nom': s.nom,
                'Prénom': s.prenom,
                'Âge': getattr(s, 'age', ''),
                'Acuité OG': getattr(s, 'acuite_og', ''),
                'Acuité OD': getattr(s, 'acuite_od', ''),
                'Sphère OG': getattr(s, 'sph_og', ''),
                'Cylindre OG': getattr(s, 'cyl_og', ''),
                'Axe OG': getattr(s, 'axe_og', ''),
                'Sphère OD': getattr(s, 'sph_od', ''),
                'Cylindre OD': getattr(s, 'cyl_od', ''),
                'Axe OD': getattr(s, 'axe_od', ''),
                'Écart pupillaire': getattr(s, 'ecart_pupillaire', ''),
                'Type prise en charge': getattr(s, 'type_prise_en_charge', ''),
                'Observations': getattr(s, 'observations', ''),
                'Statut': getattr(s, 'status', ''),
            })

        df = pd.DataFrame(data)

        # Dossier d'export sous le répertoire de l'application
        export_dir = os.path.join(current_app.root_path, 'data', 'exports')
        os.makedirs(export_dir, exist_ok=True)

        # Nom du fichier
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'export_eleves_{timestamp}.xlsx'
        filepath = os.path.join(export_dir, filename)

        # Sauvegarder le fichier Excel
        df.to_excel(filepath, index=False, engine='openpyxl')

        # Envoyer le fichier au navigateur
        return send_file(filepath, as_attachment=True)

    except Exception as e:
        flash(f"Erreur lors de l'export: {str(e)}", "danger")
        return redirect(url_for('exports.index'))
