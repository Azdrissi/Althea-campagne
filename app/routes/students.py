from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash, session
from app.models import Student
from app import db
from datetime import datetime
from sqlalchemy import or_

bp = Blueprint('students', __name__, url_prefix='/students')

@bp.route('/')
def list_students():
    search_term = request.args.get('search', '').strip()

    if 'session_active' in session:
        session_active = session['session_active']
        ville = session_active['ville']
        ecole = session_active['ecole']
        query = Student.query.filter_by(ville=ville, ecole=ecole)
    else:
        query = Student.query

    if search_term:
        search_pattern = f'%{search_term}%'
        query = query.filter(
            or_(
                Student.nom.ilike(search_pattern),
                Student.prenom.ilike(search_pattern),
                Student.observations.ilike(search_pattern)
            )
        )

    students = query.order_by(Student.classe, Student.nom).all()
    return render_template('student_list.html', students=students, search_term=search_term)

@bp.route('/new')
def new_student():
    if 'session_active' not in session:
        flash("Veuillez d'abord démarrer une école", 'warning')
        return redirect(url_for('index'))

    session_active = session['session_active']
    student = type('obj', (object,), {
        'id': None,
        'ville': session_active['ville'],
        'ecole': session_active['ecole'],
        'nom': '',  # ← CHANGÉ: '' au lieu de None
        'prenom': '',  # ← CHANGÉ: '' au lieu de None
        'age': None,
        'classe': None,
        'status': 'prelisted',
        'acuite_od': None,
        'acuite_og': None,
        'sph_od': None,
        'cyl_od': None,
        'axe_od': None,
        'sph_og': None,
        'cyl_og': None,
        'axe_og': None,
        'ep_pupillometre_od': None,
        'ep_pupillometre_og': None,
        'prise_en_charge': None,
        'observations': None,
        'photo_monture': None
    })()

    return render_template('student_form.html', student=student, is_new=True)

@bp.route('/new', methods=['POST'])
def create_student():
    try:
        if 'session_active' not in session:
            flash("Veuillez d'abord démarrer une école", 'danger')
            return redirect(url_for('index'))

        session_active = session['session_active']
        student = Student(
            ville=session_active['ville'],
            ecole=session_active['ecole'],
            classe=request.form.get('classe'),
            nom=request.form.get('nom'),
            prenom=request.form.get('prenom'),
            age=request.form.get('age', type=int),
            status='prelisted'
        )

        db.session.add(student)
        db.session.commit()

        flash('Élève créé avec succès !', 'success')
        return redirect(url_for('students.edit_student', id=student.id))
    except Exception as e:
        db.session.rollback()
        flash(f'Erreur: {str(e)}', 'danger')
        return redirect(url_for('students.new_student'))

@bp.route('/edit/<int:id>')
def edit_student(id):
    student = Student.query.get_or_404(id)
    return render_template('student_form.html', student=student, is_new=False)

@bp.route('/edit/<int:id>', methods=['POST'])
def update_student(id):
    try:
        student = Student.query.get_or_404(id)

        student.nom = request.form.get('nom', student.nom)
        student.prenom = request.form.get('prenom', student.prenom)
        student.age = request.form.get('age', type=int)
        student.classe = request.form.get('classe', student.classe)

        student.acuite_od = request.form.get('acuite_od', type=int)
        student.acuite_og = request.form.get('acuite_og', type=int)

        student.sph_od = request.form.get('sph_od', type=float)
        student.cyl_od = request.form.get('cyl_od', type=float)
        student.axe_od = request.form.get('axe_od', type=int)

        student.sph_og = request.form.get('sph_og', type=float)
        student.cyl_og = request.form.get('cyl_og', type=float)
        student.axe_og = request.form.get('axe_og', type=int)

        student.ep_pupillometre_od = request.form.get('ep_pupillometre_od', type=float)
        student.ep_pupillometre_og = request.form.get('ep_pupillometre_og', type=float)

        prise_en_charge = request.form.getlist('prise_en_charge')
        student.prise_en_charge = ','.join(prise_en_charge) if prise_en_charge else None

        student.observations = request.form.get('observations')
        student.updated_at = datetime.utcnow()

        db.session.commit()

        flash('Élève mis à jour avec succès !', 'success')
        return redirect(url_for('students.list_students'))

    except Exception as e:
        db.session.rollback()
        flash(f'Erreur: {str(e)}', 'danger')
        return redirect(url_for('students.edit_student', id=id))

@bp.route('/delete/<int:id>', methods=['POST'])
def delete_student(id):
    try:
        student = Student.query.get_or_404(id)
        db.session.delete(student)
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 400



@bp.route('/<int:student_id>/print/full')
def print_student_full(student_id):
    """Impression HTML complète de la fiche (avec logo, cadres, etc.)."""
    student = Student.query.get_or_404(student_id)
    return render_template('print_student_full.html', student=student)


@bp.route('/<int:student_id>/print/preprinted')
def print_student_preprinted(student_id):
    """Impression sur fiche pré-imprimée Fondation Althea (données seules)."""
    student = Student.query.get_or_404(student_id)
    return render_template('print_student_preprinted.html', student=student)

@bp.route('/pdf/<int:id>')
def generate_pdf(id):
    from flask import make_response
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.units import cm
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER
    from io import BytesIO

    student = Student.query.get_or_404(id)

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        textColor=colors.HexColor('#2c3e50'),
        alignment=TA_CENTER,
        spaceAfter=30
    )

    title = Paragraph(f"FICHE DE CONSULTATION<br/>{student.nom} {student.prenom}", title_style)
    elements.append(title)
    elements.append(Spacer(1, 0.5*cm))

    info_data = [
        ['INFORMATIONS GÉNÉRALES', ''],
        ['Nom', student.nom or '-'],
        ['Prénom', student.prenom or '-'],
        ['Âge', str(student.age) if student.age else '-'],
        ['Classe', student.classe or '-'],
        ['École', student.ecole or '-'],
        ['Ville', student.ville or '-']
    ]

    info_table = Table(info_data, colWidths=[6*cm, 10*cm])
    info_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498db')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 1*cm))

    acuite_data = [
        ['ACUITÉ VISUELLE', '', ''],
        ['', 'OD', 'OG'],
        ['Acuité', 
         f"{student.acuite_od}/10" if student.acuite_od else '-',
         f"{student.acuite_og}/10" if student.acuite_og else '-']
    ]

    acuite_table = Table(acuite_data, colWidths=[6*cm, 5*cm, 5*cm])
    acuite_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e74c3c')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('SPAN', (0, 0), (-1, 0)),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    elements.append(acuite_table)
    elements.append(Spacer(1, 1*cm))

    prescription_data = [
        ['PRESCRIPTION', '', '', '', '', ''],
        ['', 'Sphère', 'Cylindre', 'Axe', 'EP', ''],
        ['OD', 
         f"{student.sph_od:+.2f}" if student.sph_od else '-',
         f"{student.cyl_od:+.2f}" if student.cyl_od else '-',
         f"{student.axe_od}°" if student.axe_od else '-',
         f"{student.ep_pupillometre_od} mm" if student.ep_pupillometre_od else '-',
         ''],
        ['OG',
         f"{student.sph_og:+.2f}" if student.sph_og else '-',
         f"{student.cyl_og:+.2f}" if student.cyl_og else '-',
         f"{student.axe_og}°" if student.axe_og else '-',
         f"{student.ep_pupillometre_og} mm" if student.ep_pupillometre_og else '-',
         '']
    ]

    prescription_table = Table(prescription_data, colWidths=[2*cm, 3*cm, 3*cm, 2.5*cm, 3*cm, 2.5*cm])
    prescription_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#27ae60')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('SPAN', (0, 0), (-1, 0)),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    elements.append(prescription_table)
    elements.append(Spacer(1, 1*cm))

    prise_data = [
        ['PRISE EN CHARGE', ''],
        ['Type', student.prise_en_charge or 'Aucune']
    ]

    prise_table = Table(prise_data, colWidths=[6*cm, 10*cm])
    prise_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f39c12')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    elements.append(prise_table)
    elements.append(Spacer(1, 1*cm))

    if student.observations:
        obs_data = [
            ['OBSERVATIONS', ''],
            ['', student.observations]
        ]
        obs_table = Table(obs_data, colWidths=[6*cm, 10*cm])
        obs_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#95a5a6')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('SPAN', (0, 0), (-1, 0)),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'TOP')
        ]))
        elements.append(obs_table)

    doc.build(elements)
    buffer.seek(0)

    response = make_response(buffer.getvalue())
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'inline; filename=fiche_{student.nom}_{student.prenom}.pdf'

    return response
