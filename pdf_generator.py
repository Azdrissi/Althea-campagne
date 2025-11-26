# pdf_generator.py
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from io import BytesIO
from datetime import date

def generate_patient_form_pdf(children_data, mode='single'):
    """
    Génère un PDF pour impression sur fiches pré-imprimées Althea

    Args:
        children_data: liste de dictionnaires contenant les données élèves
        mode: 'single' pour 1 fiche (1/2 A4) ou 'double' pour 2 fiches (A4 complète)

    Returns:
        BytesIO object contenant le PDF
    """
    buffer = BytesIO()

    # Dimensions A4: 210mm x 297mm
    if mode == 'single':
        # Format 1/2 A4 paysage: 210mm x 148.5mm
        page_width = 210 * mm
        page_height = 148.5 * mm
    else:
        # Format A4 portrait pour 2 fiches
        page_width = 210 * mm
        page_height = 297 * mm

    c = canvas.Canvas(buffer, pagesize=(page_width, page_height))

    # Traiter les enfants
    for idx, child in enumerate(children_data):
        if mode == 'double' and idx > 0 and idx % 2 == 0:
            c.showPage()

        # Calculer l'offset vertical pour mode double
        if mode == 'double':
            y_offset = page_height - (148.5 * mm) if idx % 2 == 0 else 0
        else:
            y_offset = 0
            if idx > 0:
                c.showPage()

        # Dessiner les données pour cette fiche
        draw_patient_data(c, child, y_offset)

    c.save()
    buffer.seek(0)
    return buffer


def draw_patient_data(c, child, y_offset=0):
    """
    Dessine les données d'un élève sur la fiche

    Args:
        c: canvas ReportLab
        child: dictionnaire avec les données de l'élève
        y_offset: décalage vertical (pour mode double)
    """
    # Configuration des polices
    c.setFont("Helvetica", 9)

    # Marges et positions (en mm depuis le bord gauche/bas)
    # Ces valeurs sont à ajuster selon votre fiche exacte
    base_y = y_offset

    # N° (en haut à droite)
    c.drawRightString(200*mm, base_y + 140*mm, str(child.get('id', '')))

    # Date (en haut à droite)
    date_str = child.get('exam_date', '')
    c.drawString(168*mm, base_y + 133*mm, date_str)

    # Ligne École / Classe / Ville
    c.drawString(15*mm, base_y + 125*mm, child.get('school_name', ''))
    c.drawString(90*mm, base_y + 125*mm, child.get('class_level', ''))
    c.drawString(165*mm, base_y + 125*mm, child.get('city', ''))

    # Ligne Nom / Prénom / Age
    c.setFont("Helvetica-Bold", 11)
    c.drawString(15*mm, base_y + 115*mm, child.get('last_name', '').upper())
    c.drawString(85*mm, base_y + 115*mm, child.get('first_name', ''))
    c.setFont("Helvetica", 9)
    c.drawString(180*mm, base_y + 115*mm, str(child.get('age', '')))

    # Cases OPH, OPT, MT
    if child.get('referred_oph'):
        c.drawString(25*mm, base_y + 105*mm, "X")
    if child.get('referred_opt'):
        c.drawString(74*mm, base_y + 105*mm, "X")
    if child.get('referred_mt'):
        c.drawString(123*mm, base_y + 105*mm, "X")

    # Acuité brute
    y_pos = base_y + 95*mm
    c.drawString(45*mm, y_pos, format_vision(child.get('od_acuite_brute')))
    c.drawString(70*mm, y_pos, format_parentheses(
        child.get('od_acuite_brute_sphere'), 
        child.get('od_acuite_brute_cylinder')
    ))
    c.drawString(125*mm, y_pos, format_vision(child.get('og_acuite_brute')))
    c.drawString(150*mm, y_pos, format_parentheses(
        child.get('og_acuite_brute_sphere'),
        child.get('og_acuite_brute_cylinder')
    ))

    # Autoréf
    y_pos = base_y + 87*mm
    c.drawString(45*mm, y_pos, format_vision(child.get('od_autoref')))
    c.drawString(70*mm, y_pos, format_parentheses(
        child.get('od_autoref_sphere'),
        child.get('od_autoref_cylinder')
    ))
    c.drawString(125*mm, y_pos, format_vision(child.get('og_autoref')))
    c.drawString(150*mm, y_pos, format_parentheses(
        child.get('og_autoref_sphere'),
        child.get('og_autoref_cylinder')
    ))

    # Porte (lunettes actuelles)
    y_pos = base_y + 79*mm
    c.drawString(45*mm, y_pos, format_vision(child.get('od_porte')))
    c.drawString(70*mm, y_pos, format_parentheses(
        child.get('od_porte_sphere'),
        child.get('od_porte_cylinder')
    ))
    c.drawString(125*mm, y_pos, format_vision(child.get('og_porte')))
    c.drawString(150*mm, y_pos, format_parentheses(
        child.get('og_porte_sphere'),
        child.get('og_porte_cylinder')
    ))

    # Nouvelle Prescription
    y_pos = base_y + 66*mm
    c.drawString(65*mm, y_pos, format_prescription(
        child.get('od_sphere'),
        child.get('od_cylinder'),
        child.get('od_axis')
    ))
    c.drawString(145*mm, y_pos, format_prescription(
        child.get('og_sphere'),
        child.get('og_cylinder'),
        child.get('og_axis')
    ))

    # Monture / Modèle / Coloris / EP
    y_pos = base_y + 54*mm
    c.drawString(25*mm, y_pos, child.get('monture', '') or '')
    c.drawString(60*mm, y_pos, child.get('modele', '') or '')
    c.drawString(90*mm, y_pos, child.get('coloris', '') or '')
    c.drawString(165*mm, y_pos, str(child.get('ep', '') or ''))

    # Observations
    y_pos = base_y + 42*mm
    observations = child.get('observations', '')
    if observations:
        # Limiter à 3-4 lignes
        c.setFont("Helvetica", 8)
        lines = wrap_text(observations, 70)
        for i, line in enumerate(lines[:4]):
            c.drawString(15*mm, y_pos - (i*3.5*mm), line)
        c.setFont("Helvetica", 9)


def format_vision(value):
    """Formate une valeur d'acuité visuelle"""
    if not value:
        return ""
    return str(value)


def format_parentheses(sphere, cylinder):
    """Formate (sphère/cylindre)"""
    if not sphere and not cylinder:
        return ""

    parts = []
    if sphere:
        parts.append(format_diopter(sphere))
    if cylinder:
        parts.append(format_diopter(cylinder))

    if not parts:
        return ""

    return f"({'/'.join(parts)})"


def format_prescription(sphere, cylinder, axis):
    """Formate une prescription complète OD ou OG"""
    if not sphere and not cylinder:
        return ""

    result = ""
    if sphere:
        result += format_diopter(sphere)
    if cylinder:
        result += f" ({format_diopter(cylinder)}"
        if axis:
            result += f" à {axis}°"
        result += ")"

    return result


def format_diopter(value):
    """Formate une valeur de dioptrie avec signe"""
    if not value:
        return ""

    try:
        num = float(value)
        if num > 0:
            return f"+{num:.2f}"
        return f"{num:.2f}"
    except (ValueError, TypeError):
        return str(value)


def wrap_text(text, max_length):
    """Découpe un texte en lignes de longueur maximale"""
    words = text.split()
    lines = []
    current_line = []
    current_length = 0

    for word in words:
        if current_length + len(word) + 1 <= max_length:
            current_line.append(word)
            current_length += len(word) + 1
        else:
            if current_line:
                lines.append(' '.join(current_line))
            current_line = [word]
            current_length = len(word)

    if current_line:
        lines.append(' '.join(current_line))

    return lines


def calculate_age(date_of_birth):
    """Calcule l'âge à partir de la date de naissance"""
    if not date_of_birth:
        return ''
    today = date.today()
    return today.year - date_of_birth.year - ((today.month, today.day) < (date_of_birth.month, date_of_birth.day))
