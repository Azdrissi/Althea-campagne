# app/routes/printing.py
from flask import Blueprint, send_file, session, flash, redirect, url_for
from app.models import Student
from app import db
from pdf_generator import generate_patient_form_pdf
from datetime import date

bp = Blueprint('printing', __name__)

@bp.route('/print_form/<int:student_id>')
def print_form(student_id):
    """Imprime la fiche pour un élève"""
    student = Student.query.get_or_404(student_id)

    # Préparer les données avec SEULEMENT les champs qui existent
    student_data = {
        'id': student.id,
        'exam_date': date.today().strftime('%d/%m/%Y'),  # Date du jour
        'school_name': getattr(student, 'ecole', ''),
        'class_level': getattr(student, 'classe', ''),
        'city': getattr(student, 'ville', ''),
        'last_name': getattr(student, 'nom', ''),
        'first_name': getattr(student, 'prenom', ''),
        'age': getattr(student, 'age', ''),
        'referred_oph': getattr(student, 'referred_oph', False),
        'referred_opt': getattr(student, 'referred_opt', False),
        'referred_mt': getattr(student, 'referred_mt', False),
        'od_acuite_brute': getattr(student, 'od_acuite_brute', ''),
        'od_acuite_brute_sphere': getattr(student, 'od_acuite_brute_sphere', ''),
        'od_acuite_brute_cylinder': getattr(student, 'od_acuite_brute_cylinder', ''),
        'og_acuite_brute': getattr(student, 'og_acuite_brute', ''),
        'og_acuite_brute_sphere': getattr(student, 'og_acuite_brute_sphere', ''),
        'og_acuite_brute_cylinder': getattr(student, 'og_acuite_brute_cylinder', ''),
        'od_autoref': getattr(student, 'od_autoref', ''),
        'od_autoref_sphere': getattr(student, 'od_autoref_sphere', ''),
        'od_autoref_cylinder': getattr(student, 'od_autoref_cylinder', ''),
        'og_autoref': getattr(student, 'og_autoref', ''),
        'og_autoref_sphere': getattr(student, 'og_autoref_sphere', ''),
        'og_autoref_cylinder': getattr(student, 'og_autoref_cylinder', ''),
        'od_porte': getattr(student, 'od_porte', ''),
        'od_porte_sphere': getattr(student, 'od_porte_sphere', ''),
        'od_porte_cylinder': getattr(student, 'od_porte_cylinder', ''),
        'og_porte': getattr(student, 'og_porte', ''),
        'og_porte_sphere': getattr(student, 'og_porte_sphere', ''),
        'og_porte_cylinder': getattr(student, 'og_porte_cylinder', ''),
        'od_sphere': getattr(student, 'od_sphere', ''),
        'od_cylinder': getattr(student, 'od_cylinder', ''),
        'od_axis': getattr(student, 'od_axis', ''),
        'og_sphere': getattr(student, 'og_sphere', ''),
        'og_cylinder': getattr(student, 'og_cylinder', ''),
        'og_axis': getattr(student, 'og_axis', ''),
        'ep': getattr(student, 'ep', ''),
        'monture': getattr(student, 'monture', ''),
        'modele': getattr(student, 'modele', ''),
        'coloris': getattr(student, 'coloris', ''),
        'observations': getattr(student, 'observations', '')
    }

    # Générer le PDF
    pdf_buffer = generate_patient_form_pdf([student_data], mode='single')

    return send_file(
        pdf_buffer,
        mimetype='application/pdf',
        as_attachment=False,
        download_name=f'fiche_{student.nom}_{student.prenom}.pdf'
    )


@bp.route('/print_forms_batch')
def print_forms_batch():
    """Imprime les fiches de tous les élèves de l'école active en mode 2 par page"""
    session_active = session.get('session_active')
    if not session_active:
        flash('Aucune école active', 'error')
        return redirect(url_for('index'))

    ecole_name = session_active.get('ecole')
    ville_name = session_active.get('ville')

    students = Student.query.filter_by(ecole=ecole_name, ville=ville_name).order_by(Student.nom, Student.prenom).all()

    if not students:
        flash('Aucun élève trouvé pour cette école', 'warning')
        return redirect(url_for('index'))

    students_data = []
    today = date.today().strftime('%d/%m/%Y')

    for student in students:
        students_data.append({
            'id': student.id,
            'exam_date': today,
            'school_name': getattr(student, 'ecole', ''),
            'class_level': getattr(student, 'classe', ''),
            'city': getattr(student, 'ville', ''),
            'last_name': getattr(student, 'nom', ''),
            'first_name': getattr(student, 'prenom', ''),
            'age': getattr(student, 'age', ''),
            'referred_oph': getattr(student, 'referred_oph', False),
            'referred_opt': getattr(student, 'referred_opt', False),
            'referred_mt': getattr(student, 'referred_mt', False),
            'od_acuite_brute': getattr(student, 'od_acuite_brute', ''),
            'od_acuite_brute_sphere': getattr(student, 'od_acuite_brute_sphere', ''),
            'od_acuite_brute_cylinder': getattr(student, 'od_acuite_brute_cylinder', ''),
            'og_acuite_brute': getattr(student, 'og_acuite_brute', ''),
            'og_acuite_brute_sphere': getattr(student, 'og_acuite_brute_sphere', ''),
            'og_acuite_brute_cylinder': getattr(student, 'og_acuite_brute_cylinder', ''),
            'od_autoref': getattr(student, 'od_autoref', ''),
            'od_autoref_sphere': getattr(student, 'od_autoref_sphere', ''),
            'od_autoref_cylinder': getattr(student, 'od_autoref_cylinder', ''),
            'og_autoref': getattr(student, 'og_autoref', ''),
            'og_autoref_sphere': getattr(student, 'og_autoref_sphere', ''),
            'og_autoref_cylinder': getattr(student, 'og_autoref_cylinder', ''),
            'od_porte': getattr(student, 'od_porte', ''),
            'od_porte_sphere': getattr(student, 'od_porte_sphere', ''),
            'od_porte_cylinder': getattr(student, 'od_porte_cylinder', ''),
            'og_porte': getattr(student, 'og_porte', ''),
            'og_porte_sphere': getattr(student, 'og_porte_sphere', ''),
            'og_porte_cylinder': getattr(student, 'og_porte_cylinder', ''),
            'od_sphere': getattr(student, 'od_sphere', ''),
            'od_cylinder': getattr(student, 'od_cylinder', ''),
            'od_axis': getattr(student, 'od_axis', ''),
            'og_sphere': getattr(student, 'og_sphere', ''),
            'og_cylinder': getattr(student, 'og_cylinder', ''),
            'og_axis': getattr(student, 'og_axis', ''),
            'ep': getattr(student, 'ep', ''),
            'monture': getattr(student, 'monture', ''),
            'modele': getattr(student, 'modele', ''),
            'coloris': getattr(student, 'coloris', ''),
            'observations': getattr(student, 'observations', '')
        })

    # Générer le PDF en mode double
    pdf_buffer = generate_patient_form_pdf(students_data, mode='double')

    return send_file(
        pdf_buffer,
        mimetype='application/pdf',
        as_attachment=False,
        download_name=f'fiches_{ecole_name.replace(" ", "_")}.pdf'
    )
