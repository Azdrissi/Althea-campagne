from app import db
from datetime import datetime

class Student(db.Model):
    __tablename__ = 'students'

    # ID et informations de base
    id = db.Column(db.Integer, primary_key=True)
    ville = db.Column(db.String(100), nullable=False)
    ecole = db.Column(db.String(200), nullable=False)
    classe = db.Column(db.String(50), nullable=False)
    nom = db.Column(db.String(100), nullable=False)
    prenom = db.Column(db.String(100), nullable=False)
    age = db.Column(db.Integer)

    # Acuité visuelle
    acuite_og = db.Column(db.Float)
    acuite_od = db.Column(db.Float)

    # Prescription Œil Gauche
    sph_og = db.Column(db.Float)
    cyl_og = db.Column(db.Float)
    axe_og = db.Column(db.Integer)

    # Prescription Œil Droit
    sph_od = db.Column(db.Float)
    cyl_od = db.Column(db.Float)
    axe_od = db.Column(db.Integer)

    # Écart pupillaire (3 mesures)
    ecart_pupillaire = db.Column(db.Float)
    ep_pupillometre_od = db.Column(db.Float)
    ep_pupillometre_og = db.Column(db.Float)

    # Autres données
    autorefractometre = db.Column(db.Text)
    observations = db.Column(db.Text)

    # Prise en charge
    prise_en_charge = db.Column(db.Text)

    # Photos
    photo_portrait = db.Column(db.String(255))
    photo_monture = db.Column(db.String(255))
    photo_clinique = db.Column(db.String(255))

    # Statut avec workflow détaillé
    status = db.Column(db.String(50), default='prelisted')
    # Valeurs possibles:
    # - prelisted: Pré-listé
    # - chez_opticien: Chez l'opticien
    # - chez_ophtalmo: Chez l'ophtalmologue
    # - choix_monture: Choix de monture (magasin)
    # - completed: Terminé (clôturé)

    ecole_cloturee = db.Column(db.Boolean, default=False)
    date_consultation = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def get_prises_en_charge_list(self):
        """Retourne la liste des prises en charge"""
        if self.prise_en_charge:
            return [p.strip() for p in self.prise_en_charge.split(',') if p.strip()]
        return []

    def set_prises_en_charge_list(self, prises_list):
        """Définit les prises en charge à partir d'une liste"""
        if prises_list:
            self.prise_en_charge = ','.join([p for p in prises_list if p])
        else:
            self.prise_en_charge = None

    def get_status_label(self):
        """Retourne le libellé du statut"""
        labels = {
            'prelisted': 'Pré-listé',
            'chez_opticien': 'Chez Opticien',
            'chez_ophtalmo': 'Chez Ophtalmo',
            'choix_monture': 'Choix Monture',
            'completed': 'Terminé'
        }
        return labels.get(self.status, 'Inconnu')

    def get_status_color(self):
        """Retourne la couleur du badge de statut"""
        colors = {
            'prelisted': 'warning',
            'chez_opticien': 'info',
            'chez_ophtalmo': 'primary',
            'choix_monture': 'secondary',
            'completed': 'success'
        }
        return colors.get(self.status, 'secondary')

    def to_dict(self):
        return {
            'id': self.id,
            'ville': self.ville,
            'ecole': self.ecole,
            'classe': self.classe,
            'nom': self.nom,
            'prenom': self.prenom,
            'age': self.age,
            'acuite_og': self.acuite_og,
            'acuite_od': self.acuite_od,
            'sph_og': self.sph_og,
            'cyl_og': self.cyl_og,
            'axe_og': self.axe_og,
            'sph_od': self.sph_od,
            'cyl_od': self.cyl_od,
            'axe_od': self.axe_od,
            'ecart_pupillaire': self.ecart_pupillaire,
            'ep_pupillometre_od': self.ep_pupillometre_od,
            'ep_pupillometre_og': self.ep_pupillometre_og,
            'autorefractometre': self.autorefractometre,
            'observations': self.observations,
            'prise_en_charge': self.prise_en_charge,
            'prises_en_charge_list': self.get_prises_en_charge_list(),
            'photo_portrait': self.photo_portrait,
            'photo_monture': self.photo_monture,
            'photo_clinique': self.photo_clinique,
            'status': self.status,
            'status_label': self.get_status_label(),
            'status_color': self.get_status_color(),
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

    def __repr__(self):
        return f'<Student {self.nom} {self.prenom}>'


class SessionEcole(db.Model):
    """Table pour gérer l'école active en cours de campagne"""
    __tablename__ = 'session_ecole'

    id = db.Column(db.Integer, primary_key=True)
    ville = db.Column(db.String(100), nullable=False)
    ecole = db.Column(db.String(200), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    date_debut = db.Column(db.DateTime, default=datetime.utcnow)
    date_cloture = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    @staticmethod
    def get_active():
        """Récupère la session école active"""
        return SessionEcole.query.filter_by(is_active=True).first()

    @staticmethod
    def set_active(ville, ecole):
        """Définit une nouvelle école active"""
        SessionEcole.query.filter_by(is_active=True).update({'is_active': False})
        session = SessionEcole.query.filter_by(ville=ville, ecole=ecole).first()
        if session:
            session.is_active = True
            session.date_debut = datetime.utcnow()
            session.date_cloture = None
        else:
            session = SessionEcole(ville=ville, ecole=ecole, is_active=True)
            db.session.add(session)
        db.session.commit()
        return session

    @staticmethod
    def cloturer():
        """Clôture la session active"""
        session = SessionEcole.get_active()
        if session:
            session.is_active = False
            session.date_cloture = datetime.utcnow()
            db.session.commit()

    def to_dict(self):
        return {
            'id': self.id,
            'ville': self.ville,
            'ecole': self.ecole,
            'is_active': self.is_active,
            'date_debut': self.date_debut.isoformat() if self.date_debut else None,
            'date_cloture': self.date_cloture.isoformat() if self.date_cloture else None
        }

    def __repr__(self):
        return f'<SessionEcole {self.ville} - {self.ecole}>'
