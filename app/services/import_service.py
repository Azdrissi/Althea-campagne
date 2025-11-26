import csv
import io
from app.models import Student
from app import db

class ImportService:

    def preview_csv(self, file):
        """Prévisualise les données du CSV"""
        file_content = file.read().decode('utf-8-sig')
        csv_reader = csv.DictReader(io.StringIO(file_content))

        rows = []
        for row in csv_reader:
            rows.append({
                'ville': row.get('ville', ''),
                'ecole': row.get('ecole', ''),
                'classe': row.get('classe', ''),
                'nom': row.get('nom', ''),
                'prenom': row.get('prenom', ''),
                'age': row.get('age', '')
            })

        return {
            'total': len(rows),
            'rows': rows[:50]  # Prévisualisation des 50 premiers
        }

    def import_students(self, rows):
        """Importe les élèves en base de données"""
        imported = 0
        duplicates = 0
        errors = []

        for row in rows:
            try:
                # Vérifier les doublons
                existing = Student.query.filter_by(
                    nom=row['nom'],
                    prenom=row['prenom'],
                    ecole=row['ecole']
                ).first()

                if existing:
                    duplicates += 1
                    continue

                # Créer l'élève
                student = Student(
                    ville=row['ville'],
                    ecole=row['ecole'],
                    classe=row['classe'],
                    nom=row['nom'],
                    prenom=row['prenom'],
                    age=int(row['age']) if row['age'] else None,
                    status='prelisted'
                )

                db.session.add(student)
                imported += 1

            except Exception as e:
                errors.append(f"Ligne {row}: {str(e)}")

        db.session.commit()

        return {
            'imported': imported,
            'duplicates': duplicates,
            'errors': errors
        }
