import os
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from app.models import Student

class PDFService:

    def generate_consultation_pdf(self, student_id, blank=False):
        student = Student.query.get_or_404(student_id)

        if blank:
            filename = f"fiche_vierge_{student.nom}_{student.prenom}_{student.id}.pdf"
        else:
            filename = f"fiche_complete_{student.nom}_{student.prenom}_{student.id}.pdf"

        # CORRECTION: Utiliser le bon chemin (racine du projet, pas dans app/)
        # Obtenir le chemin absolu de la racine du projet
        base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
        pdf_dir = os.path.join(base_path, 'data', 'pdf')

        # Créer le dossier s'il n'existe pas
        os.makedirs(pdf_dir, exist_ok=True)

        filepath = os.path.join(pdf_dir, filename)

        doc = SimpleDocTemplate(filepath, pagesize=A4, rightMargin=2*cm, leftMargin=2*cm,
                                topMargin=2*cm, bottomMargin=2*cm)

        elements = []
        styles = getSampleStyleSheet()

        title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'],
                                      fontSize=18, textColor=colors.HexColor('#4472C4'),
                                      spaceAfter=20, alignment=TA_CENTER)

        title = Paragraph("FICHE DE CONSULTATION OPHTALMOLOGIQUE - FONDATION ALTHEA", title_style)
        elements.append(title)
        elements.append(Spacer(1, 0.5*cm))

        header_data = [
            ['Ville', student.ville or '', 'École', student.ecole or ''],
            ['Classe', student.classe or '', 'Date', datetime.now().strftime('%d/%m/%Y')],
            ['Nom', student.nom or '', 'Prénom', student.prenom or ''],
            ['Âge', str(student.age) if student.age else '', 'N° Fiche', f"#{student.id}"]
        ]

        header_table = Table(header_data, colWidths=[3*cm, 6*cm, 3*cm, 6*cm])
        header_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ('BACKGROUND', (2, 0), (2, -1), colors.lightgrey),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))

        elements.append(header_table)
        elements.append(Spacer(1, 1*cm))

        medical_title = Paragraph("<b>DONNÉES MÉDICALES</b>", styles['Heading2'])
        elements.append(medical_title)
        elements.append(Spacer(1, 0.3*cm))

        if not blank:
            medical_data = [
                ['', 'Œil Gauche (OG)', 'Œil Droit (OD)'],
                ['Acuité', f"{student.acuite_og or ''}/10", f"{student.acuite_od or ''}/10"],
                ['Sphère', str(student.sph_og or ''), str(student.sph_od or '')],
                ['Cylindre', str(student.cyl_og or ''), str(student.cyl_od or '')],
                ['Axe', f"{student.axe_og or ''}°", f"{student.axe_od or ''}°"],
            ]
            other_data = [
                ['Écart pupillaire', str(student.ecart_pupillaire or '')],
                ['Prise en charge', student.prise_en_charge or '']
            ]
            obs_text = student.observations or ''
        else:
            medical_data = [
                ['', 'Œil Gauche (OG)', 'Œil Droit (OD)'],
                ['Acuité', '', ''], ['Sphère', '', ''],
                ['Cylindre', '', ''], ['Axe', '', '']
            ]
            other_data = [['Écart pupillaire', ''], ['Prise en charge', '']]
            obs_text = ''

        medical_table = Table(medical_data, colWidths=[5*cm, 5.5*cm, 5.5*cm])
        medical_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4472C4')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ]))

        elements.append(medical_table)
        elements.append(Spacer(1, 0.5*cm))

        other_table = Table(other_data, colWidths=[5*cm, 11*cm])
        other_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))

        elements.append(other_table)
        elements.append(Spacer(1, 0.5*cm))

        obs_data = [['Observations'], [obs_text if obs_text else ' ' * 100]]
        obs_table = Table(obs_data, colWidths=[16*cm], rowHeights=[0.8*cm, 3*cm])
        obs_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, 0), colors.lightgrey),
            ('FONTNAME', (0, 0), (0, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
        ]))

        elements.append(obs_table)
        elements.append(Spacer(1, 1*cm))

        signature_data = [['Examinateur:', '', 'Signature:', '']]
        signature_table = Table(signature_data, colWidths=[3*cm, 5*cm, 3*cm, 5*cm])
        signature_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
        ]))

        elements.append(signature_table)

        doc.build(elements)
        return filepath
