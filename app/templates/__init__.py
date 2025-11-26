import os
from flask import Flask, send_from_directory, render_template, session
from flask_sqlalchemy import SQLAlchemy

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

    # Créer les tables si nécessaire
    with app.app_context():
        db.create_all()

    return app
