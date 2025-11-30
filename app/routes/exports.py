from flask import Blueprint, render_template, send_file, flash, redirect, url_for, current_app, request, session
from app.models import Student
from app import db
import pandas as pd
from datetime import datetime
import os

bp = Blueprint('exports', __name__, url_prefix='/exports')

@bp.route('/')
def index():
    """Page d'export avec plusieurs options"""
    # Statistiques pour la page
    total_students = Student.query.count()

    # Sites distincts
    if 'session_active' in session:
        session_active = session['session_active']
        sites_query = db.session.query(Student.site).filter_by(
            ville=session_active['ville'],
            ecole=session_active['ecole']
        ).distinct().all()
    else:
        sites_query = db.session.query(Student.site).distinct().all()

    sites = [s[0] for s in sites_query if s[0]]
    total_sites = len(sites)

    # Nombre d'élèves consultés (avec acuité mesurée)
    total_consulted = Student.query.filter(
        (Student.acuite_od.isnot(None)) | (Student.acuite_og.isnot(None))
    ).count()

    # Nombre avec prescription de lunettes
    total_with_glasses = Student.query.filter(
        (Student.sph_od.isnot(None)) | (Student.sph_og.isnot(None))
    ).count()

    return render_template('exports.html',
                         total_students=total_students,
                         total_sites=total_sites,
                         total_consulted=total_consulted,
                         total_with_glasses=total_with_glasses,
                         sites=sites)


@bp.route('/excel')
def export_excel():
    """Export complet - Tous les élèves avec toutes les données"""
    try:
        students = Student.query.all()

        if not students:
            flash("Aucun élève à exporter", "warning")
            return redirect(url_for('exports.index'))

        data = []
        for s in students:
            data.append({
                'ID': s.id,
                'Ville': s.ville or '',
                'École': s.ecole or '',
                'Site': s.site or '',
                'Classe': s.classe or '',
                'Nom': s.nom,
                'Prénom': s.prenom,
                'Âge': s.age or '',
                'Acuité OD': s.acuite_od or '',
                'Acuité OG': s.acuite_og or '',
                'Sphère OD': s.sph_od or '',
                'Cylindre OD': s.cyl_od or '',
                'Axe OD': s.axe_od or '',
                'Sphère OG': s.sph_og or '',
                'Cylindre OG': s.cyl_og or '',
                'Axe OG': s.axe_og or '',
                'EP OD': s.ep_pupillometre_od or '',
                'EP OG': s.ep_pupillometre_og or '',
                'Prise en charge': s.prise_en_charge or '',
                'Observations': s.observations or '',
                'Statut': s.status or '',
            })

        df = pd.DataFrame(data)
        return _send_excel(df, 'export_complet')

    except Exception as e:
        flash(f"Erreur lors de l'export: {str(e)}", "danger")
        return redirect(url_for('exports.index'))


@bp.route('/by_site')
def export_by_site():
    """Export par site spécifique"""
    try:
        site = request.args.get('site')
        if not site:
            flash("Veuillez sélectionner un site", "warning")
            return redirect(url_for('exports.index'))

        students = Student.query.filter_by(site=site).all()

        if not students:
            flash(f"Aucun élève trouvé pour le site {site}", "warning")
            return redirect(url_for('exports.index'))

        data = []
        for s in students:
            data.append({
                'ID': s.id,
                'Classe': s.classe or '',
                'Nom': s.nom,
                'Prénom': s.prenom,
                'Âge': s.age or '',
                'Acuité OD': s.acuite_od or '',
                'Acuité OG': s.acuite_og or '',
                'Sphère OD': s.sph_od or '',
                'Cylindre OD': s.cyl_od or '',
                'Axe OD': s.axe_od or '',
                'Sphère OG': s.sph_og or '',
                'Cylindre OG': s.cyl_og or '',
                'Axe OG': s.axe_og or '',
                'Prise en charge': s.prise_en_charge or '',
            })

        df = pd.DataFrame(data)
        return _send_excel(df, f'export_site_{site}')

    except Exception as e:
        flash(f"Erreur lors de l'export: {str(e)}", "danger")
        return redirect(url_for('exports.index'))


@bp.route('/with_glasses')
def export_with_glasses():
    """Export des élèves avec prescription de lunettes"""
    try:
        students = Student.query.filter(
            (Student.sph_od.isnot(None)) | (Student.sph_og.isnot(None))
        ).all()

        if not students:
            flash("Aucun élève avec prescription trouvé", "warning")
            return redirect(url_for('exports.index'))

        data = []
        for s in students:
            data.append({
                'Nom': s.nom,
                'Prénom': s.prenom,
                'École': s.ecole or '',
                'Site': s.site or '',
                'Classe': s.classe or '',
                'Âge': s.age or '',
                'Sphère OD': s.sph_od or '',
                'Cylindre OD': s.cyl_od or '',
                'Axe OD': s.axe_od or '',
                'Sphère OG': s.sph_og or '',
                'Cylindre OG': s.cyl_og or '',
                'Axe OG': s.axe_og or '',
                'EP OD': s.ep_pupillometre_od or '',
                'EP OG': s.ep_pupillometre_og or '',
            })

        df = pd.DataFrame(data)
        return _send_excel(df, 'eleves_avec_lunettes')

    except Exception as e:
        flash(f"Erreur lors de l'export: {str(e)}", "danger")
        return redirect(url_for('exports.index'))


@bp.route('/referred')
def export_referred():
    """Export des élèves référés (ophtalmo, orthoptiste, chirurgie)"""
    try:
        students = Student.query.filter(
            (Student.prise_en_charge.like('%refere%')) |
            (Student.prise_en_charge.like('%chirurgie%'))
        ).all()

        if not students:
            flash("Aucun élève référé trouvé", "warning")
            return redirect(url_for('exports.index'))

        data = []
        for s in students:
            data.append({
                'Nom': s.nom,
                'Prénom': s.prenom,
                'École': s.ecole or '',
                'Site': s.site or '',
                'Classe': s.classe or '',
                'Âge': s.age or '',
                'Prise en charge': s.prise_en_charge or '',
                'Observations': s.observations or '',
            })

        df = pd.DataFrame(data)
        return _send_excel(df, 'eleves_referes')

    except Exception as e:
        flash(f"Erreur lors de l'export: {str(e)}", "danger")
        return redirect(url_for('exports.index'))


@bp.route('/statistics')
def export_statistics():
    """Export rapport statistique par site"""
    try:
        # Récupérer tous les sites
        sites = db.session.query(Student.site).distinct().all()
        sites = [s[0] for s in sites if s[0]]

        stats_data = []

        for site in sites:
            total = Student.query.filter_by(site=site).count()
            consulted = Student.query.filter_by(site=site).filter(
                (Student.acuite_od.isnot(None)) | (Student.acuite_og.isnot(None))
            ).count()
            with_glasses = Student.query.filter_by(site=site).filter(
                (Student.sph_od.isnot(None)) | (Student.sph_og.isnot(None))
            ).count()
            referred = Student.query.filter_by(site=site).filter(
                (Student.prise_en_charge.like('%refere%')) |
                (Student.prise_en_charge.like('%chirurgie%'))
            ).count()

            stats_data.append({
                'Site': site,
                'Total élèves': total,
                'Consultés': consulted,
                '% Consultés': round(consulted / total * 100, 1) if total > 0 else 0,
                'Avec lunettes': with_glasses,
                '% Lunettes': round(with_glasses / total * 100, 1) if total > 0 else 0,
                'Référés': referred,
                '% Référés': round(referred / total * 100, 1) if total > 0 else 0,
            })

        df = pd.DataFrame(stats_data)
        return _send_excel(df, 'statistiques_par_site')

    except Exception as e:
        flash(f"Erreur lors de l'export: {str(e)}", "danger")
        return redirect(url_for('exports.index'))


@bp.route('/simple_list')
def export_simple_list():
    """Export liste simple pour présence"""
    try:
        students = Student.query.order_by(Student.classe, Student.nom).all()

        if not students:
            flash("Aucun élève à exporter", "warning")
            return redirect(url_for('exports.index'))

        data = []
        for s in students:
            data.append({
                'Classe': s.classe or '',
                'Nom': s.nom,
                'Prénom': s.prenom,
                'École': s.ecole or '',
                'Site': s.site or '',
            })

        df = pd.DataFrame(data)
        return _send_excel(df, 'liste_simple')

    except Exception as e:
        flash(f"Erreur lors de l'export: {str(e)}", "danger")
        return redirect(url_for('exports.index'))


def _send_excel(df, base_name):
    """Fonction helper pour générer et envoyer un fichier Excel"""
    export_dir = os.path.join(current_app.root_path, 'data', 'exports')
    os.makedirs(export_dir, exist_ok=True)

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'{base_name}_{timestamp}.xlsx'
    filepath = os.path.join(export_dir, filename)

    df.to_excel(filepath, index=False, engine='openpyxl')

    return send_file(filepath, as_attachment=True)
