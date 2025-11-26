import os
import base64
from datetime import datetime
from app.models import Student
from app import db
from PIL import Image
import io

class PhotoService:

    def save_photo(self, student_id, photo_type, photo_data):
        """Sauvegarde une photo capturée"""
        # Décoder le base64
        if ',' in photo_data:
            photo_data = photo_data.split(',')[1]

        image_data = base64.b64decode(photo_data)
        image = Image.open(io.BytesIO(image_data))

        # Optimiser et redimensionner
        max_size = (800, 800)
        image.thumbnail(max_size, Image.Resampling.LANCZOS)

        # Générer le nom de fichier
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{student_id}_{photo_type}_{timestamp}.jpg"

        # Déterminer le dossier
        folder_map = {
            'portrait': 'portraits',
            'monture': 'montures',
            'clinique': 'cliniques'
        }
        folder = folder_map.get(photo_type, 'portraits')

        # S'assurer que le dossier existe
        folder_path = os.path.join('data', 'photos', folder)
        os.makedirs(folder_path, exist_ok=True)

        # Chemin complet
        filepath = os.path.join(folder_path, filename)

        # Sauvegarder
        image.save(filepath, 'JPEG', quality=85, optimize=True)

        # Mettre à jour le modèle
        student = Student.query.get(student_id)
        if student:
            if photo_type == 'portrait':
                student.photo_portrait = filepath
            elif photo_type == 'monture':
                student.photo_monture = filepath
            elif photo_type == 'clinique':
                student.photo_clinique = filepath
            db.session.commit()

        return filepath

    def delete_photo(self, filepath):
        """Supprime une photo"""
        if os.path.exists(filepath):
            os.remove(filepath)
