import os
from flask import Flask, send_from_directory, render_template, session, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

def create_app():
    app = Flask(__name__)

    # Configuration
    basedir = os.path.abspath(os.path.dirname(__file__))
    app.config['SECRET_KEY'] = 'votre-cle-secrete-ici'
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(basedir, "..", "data", "campaign.db")}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Initialiser la base de données
    db.init_app(app)

    # Context processor pour rendre session_active disponible partout
    @app.context_processor
    def inject_session():
        return {
            'session_active': session.get('session_active', None)
        }

    # Route pour servir les photos depuis data/photos
    @app.route('/data/<path:filename>')
    def serve_data_file(filename):
        data_dir = os.path.join(basedir, '..', 'data')
        return send_from_directory(data_dir, filename)

    # Route principale
    @app.route('/')
    def index():
        return render_template('index.html')

    # Routes de gestion de session école
    @app.route('/session/start', methods=['POST'])
    def start_session():
        ville = request.form.get('ville')
        ecole = request.form.get('ecole')

        if ville and ecole:
            session['session_active'] = {
                'ville': ville,
                'ecole': ecole,
                'date_debut': datetime.now().strftime('%d/%m/%Y %H:%M')
            }
            flash(f'École "{ecole}" démarrée avec succès !', 'success')
        else:
            flash('Veuillez remplir Ville et École', 'danger')
        return redirect(url_for('index'))

    @app.route('/session/close', methods=['POST'])
    def close_session():
        if 'session_active' in session:
            ecole = session['session_active']['ecole']
            session.pop('session_active', None)
            flash(f'École "{ecole}" clôturée avec succès !', 'success')
        return redirect(url_for('index'))

    # Importer et enregistrer les blueprints
    from app.routes import students
    app.register_blueprint(students.bp)

    from app.routes import exports
    app.register_blueprint(exports.bp)

    from app.routes import imports
    app.register_blueprint(imports.bp)

    from app.routes import statistics
    app.register_blueprint(statistics.bp)

    from app.routes import mobile
    app.register_blueprint(mobile.bp)

    # ✅ AJOUT : Blueprint pour l'impression PDF
    from app.routes import printing
    app.register_blueprint(printing.bp, url_prefix='/printing')

    # Créer les tables si nécessaire
    with app.app_context():
        db.create_all()

    return app
