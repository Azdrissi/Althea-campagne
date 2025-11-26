from flask import Blueprint, send_file, request
from app.services.pdf_service import PDFService

bp = Blueprint('pdf', __name__, url_prefix='/pdf')

@bp.route('/fiche/<int:student_id>')
def generate_fiche(student_id):
    blank = request.args.get('blank', 'false').lower() == 'true'

    service = PDFService()
    filepath = service.generate_consultation_pdf(student_id, blank=blank)

    return send_file(filepath, as_attachment=True)
