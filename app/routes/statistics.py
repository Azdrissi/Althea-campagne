from flask import Blueprint, render_template
from app.models import Student
from app import db
from sqlalchemy import func, case

bp = Blueprint('statistics', __name__, url_prefix='/statistics')

@bp.route('/')
def index():
    """Statistiques complètes avec analyse prescriptions détaillée"""

    # 1. STATISTIQUES GLOBALES
    total_students = Student.query.count()

    consultations_completees = Student.query.filter(
        (Student.acuite_od.isnot(None)) | (Student.acuite_og.isnot(None))
    ).count()

    lunettes_prescrites = Student.query.filter(
        (Student.sph_od.isnot(None)) | (Student.sph_og.isnot(None))
    ).count()

    referes = Student.query.filter(
        (Student.prise_en_charge.like('%refere_oph%')) |
        (Student.prise_en_charge.like('%refere_orthoptiste%')) |
        (Student.prise_en_charge.like('%chirurgie%'))
    ).count()

    ras = Student.query.filter(
        Student.prise_en_charge.like('%ras%')
    ).count()

    # 2. RÉPARTITION PAR VILLE (toutes colonnes)
    stats_ville = db.session.query(
        Student.ville,
        func.count(Student.id).label('total'),
        func.sum(case((Student.acuite_od.isnot(None), 1), else_=0)).label('consultes'),
        func.sum(case((Student.sph_od.isnot(None), 1), else_=0)).label('lunettes'),
        func.sum(case((Student.prise_en_charge.like('%medicament%'), 1), else_=0)).label('medicament'),
        func.sum(case((Student.prise_en_charge.like('%refere_oph%'), 1), else_=0)).label('refere_oph'),
        func.sum(case((Student.prise_en_charge.like('%refere_orthoptiste%'), 1), else_=0)).label('refere_ortho'),
        func.sum(case((Student.prise_en_charge.like('%chirurgie%'), 1), else_=0)).label('chirurgie'),
        func.sum(case((Student.prise_en_charge.like('%ras%'), 1), else_=0)).label('ras')
    ).group_by(Student.ville).all()

    # 3. RÉPARTITION PAR ÉCOLE (toutes colonnes)
    stats_ecole = db.session.query(
        Student.ecole,
        Student.ville,
        func.count(Student.id).label('total'),
        func.sum(case((Student.acuite_od.isnot(None), 1), else_=0)).label('consultes'),
        func.sum(case((Student.sph_od.isnot(None), 1), else_=0)).label('lunettes'),
        func.sum(case((Student.prise_en_charge.like('%medicament%'), 1), else_=0)).label('medicament'),
        func.sum(case((Student.prise_en_charge.like('%refere_oph%'), 1), else_=0)).label('refere_oph'),
        func.sum(case((Student.prise_en_charge.like('%refere_orthoptiste%'), 1), else_=0)).label('refere_ortho'),
        func.sum(case((Student.prise_en_charge.like('%chirurgie%'), 1), else_=0)).label('chirurgie'),
        func.sum(case((Student.prise_en_charge.like('%ras%'), 1), else_=0)).label('ras')
    ).group_by(Student.ecole, Student.ville).all()

    # 4. ANALYSE PRESCRIPTIONS DÉTAILLÉE (MÉTIER)
    # Récupérer tous les élèves avec prescription
    students_avec_prescription = Student.query.filter(
        (Student.sph_od.isnot(None)) | (Student.sph_og.isnot(None))
    ).all()

    # Initialiser compteurs
    prescriptions = {
        'myopie_faible': 0,      # Sph > -3.00
        'myopie_forte': 0,        # Sph ≤ -3.00
        'hypermetropie_faible': 0, # Sph < +3.00
        'hypermetropie_forte': 0,  # Sph ≥ +3.00
        'astigmatisme_faible': 0,  # |Cyl| < 1.00
        'astigmatisme_moyen': 0,   # |Cyl| 1.00 à 2.00
        'astigmatisme_fort': 0,    # |Cyl| > 2.00
        'myopie_astigmate': 0,
        'hypermetropie_astigmate': 0
    }

    for s in students_avec_prescription:
        # Prendre le pire œil (OD ou OG)
        sph = None
        cyl = None

        if s.sph_od is not None and s.sph_og is not None:
            # Prendre la plus forte correction
            sph = s.sph_od if abs(s.sph_od) > abs(s.sph_og) else s.sph_og
            cyl = s.cyl_od if s.sph_od == sph else s.cyl_og
        elif s.sph_od is not None:
            sph = s.sph_od
            cyl = s.cyl_od
        elif s.sph_og is not None:
            sph = s.sph_og
            cyl = s.cyl_og

        if sph is not None:
            has_astigmatisme = cyl is not None and abs(cyl) >= 0.50

            # Classification
            if sph < 0:  # MYOPIE
                if has_astigmatisme:
                    prescriptions['myopie_astigmate'] += 1
                elif sph > -3.00:
                    prescriptions['myopie_faible'] += 1
                else:
                    prescriptions['myopie_forte'] += 1
            elif sph > 0:  # HYPERMÉTROPIE
                if has_astigmatisme:
                    prescriptions['hypermetropie_astigmate'] += 1
                elif sph < 3.00:
                    prescriptions['hypermetropie_faible'] += 1
                else:
                    prescriptions['hypermetropie_forte'] += 1

            # Classification astigmatisme seul
            if cyl is not None and sph == 0:
                cyl_abs = abs(cyl)
                if cyl_abs < 1.00:
                    prescriptions['astigmatisme_faible'] += 1
                elif cyl_abs <= 2.00:
                    prescriptions['astigmatisme_moyen'] += 1
                else:
                    prescriptions['astigmatisme_fort'] += 1

    # 5. TYPES DE PRISE EN CHARGE
    stats_prise_en_charge = {
        'Lunettes': Student.query.filter(Student.prise_en_charge.like('%lunettes%')).count(),
        'Médicament': Student.query.filter(Student.prise_en_charge.like('%medicament%')).count(),
        'Référé Ophtalmo': Student.query.filter(Student.prise_en_charge.like('%refere_oph%')).count(),
        'Référé Orthoptiste': Student.query.filter(Student.prise_en_charge.like('%refere_orthoptiste%')).count(),
        'Chirurgie': Student.query.filter(Student.prise_en_charge.like('%chirurgie%')).count(),
        'RAS': Student.query.filter(Student.prise_en_charge.like('%ras%')).count(),
    }

    return render_template(
        'statistics.html',
        total_students=total_students,
        consultations_completees=consultations_completees,
        lunettes_prescrites=lunettes_prescrites,
        referes=referes,
        ras=ras,
        stats_ville=stats_ville,
        stats_ecole=stats_ecole,
        prescriptions=prescriptions,
        stats_prise_en_charge=stats_prise_en_charge
    )
