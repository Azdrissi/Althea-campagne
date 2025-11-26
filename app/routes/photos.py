from flask import Blueprint, request, jsonify, current_app
from app.services.photo_service import PhotoService

bp = Blueprint('photos', __name__, url_prefix='/photos')

@bp.route('/capture', methods=['POST'])
def capture_photo():
    try:
        data = request.get_json()
        student_id = data.get('student_id')
        photo_type = data.get('type')  # portrait, monture, clinique
        photo_data = data.get('photo')  # base64

        service = PhotoService()
        filepath = service.save_photo(student_id, photo_type, photo_data)

        return jsonify({'success': True, 'filepath': filepath})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@bp.route('/delete', methods=['POST'])
def delete_photo():
    try:
        data = request.get_json()
        filepath = data.get('filepath')

        service = PhotoService()
        service.delete_photo(filepath)

        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400
