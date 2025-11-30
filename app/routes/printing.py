from flask import Blueprint, render_template
from app.models import Student

bp = Blueprint('printing', __name__, url_prefix='/printing')

@bp.route('/print_form/<int:student_id>')
def print_form(student_id):
    """Imprimer la fiche complète en PDF"""
    student = Student.query.get_or_404(student_id)
    # Rediriger vers la fonction generate_pdf de students
    from flask import redirect, url_for
    return redirect(url_for('students.generate_pdf', id=student_id))
