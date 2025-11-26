from flask import Blueprint, render_template, request, jsonify, redirect, url_for
from app.models import SessionEcole, Student
from app import db

bp = Blueprint('session', __name__, url_prefix='/session')

@bp.route('/ecole')
def manage_ecole():
    """Page de gestion de l'école active"""
    session_active = SessionEcole.get_active()

    # Récupérer toutes les écoles disponibles
    ecoles = db.session.query(Student.ville, Student.ecole).distinct().all()

    # Historique des sessions
    historique = SessionEcole.query.order_by(SessionEcole.date_debut.desc()).limit(10).all()

    return render_template('session_ecole.html', 
                         session_active=session_active,
                         ecoles=ecoles,
                         historique=historique)

@bp.route('/ecole/set', methods=['POST'])
def set_ecole():
    """Définir une nouvelle école active"""
    ville = request.form.get('ville')
    ecole = request.form.get('ecole')

    if not ville or not ecole:
        return jsonify({'success': False, 'error': 'Ville et école requis'}), 400

    try:
        session = SessionEcole.set_active(ville, ecole)
        return jsonify({
            'success': True,
            'session': session.to_dict()
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/ecole/cloturer', methods=['POST'])
def cloturer_ecole():
    """Clôturer l'école active"""
    try:
        SessionEcole.cloturer()
        return jsonify({'success': True, 'message': 'École clôturée avec succès'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/ecole/active', methods=['GET'])
def get_ecole_active():
    """Récupérer l'école active (API pour le formulaire)"""
    session = SessionEcole.get_active()
    if session:
        return jsonify({
            'success': True,
            'ville': session.ville,
            'ecole': session.ecole
        })
    else:
        return jsonify({
            'success': False,
            'ville': None,
            'ecole': None
        })

@bp.route('/ecole/create', methods=['POST'])
def create_new_ecole():
    """Créer une nouvelle école (ville + nom)"""
    ville = request.form.get('ville')
    ecole = request.form.get('ecole')

    if not ville or not ecole:
        return jsonify({'success': False, 'error': 'Ville et école requis'}), 400

    try:
        # Définir comme école active
        session = SessionEcole.set_active(ville, ecole)
        return jsonify({
            'success': True,
            'message': f'École "{ecole}" à {ville} activée',
            'session': session.to_dict()
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
