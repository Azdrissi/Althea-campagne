from flask import Blueprint, render_template
from app.models import Student
from app import db
from sqlalchemy import func, case, and_

bp = Blueprint('statistics', __name__, url_prefix='/statistics')

@bp.route('/')
def index():
    """Statistiques de campagne alignées sur les prises en charge."""

    # 1. STATISTIQUES GLOBALES BASÉES SUR LA PRISE EN CHARGE
    total_students = Student.query.count()

    # Élèves ayant au moins une prise en charge (lunettes, médicament, référé, chirurgie, RAS…)
    eleves_avec_pec_query = Student.query.filter(
        and_(
            Student.prise_en_charge.isnot(None),
            Student.prise_en_charge != ''
        )
    )
    consultations_completees = eleves_avec_pec_query.count()

    # Comptages globaux basés sur le bloc "Détail Prises en Charge" (calculé plus bas)
    lunettes_prescrites = None
    referes = None
    ras = None

    # Taux de complétude = élèves avec prise en charge / total élèves
    taux_completude = 0
    if total_students > 0:
        taux_completude = round((consultations_completees / total_students) * 100)

    # 2. ANALYSE PRESCRIPTIONS DÉTAILLÉE (MYOPIE / HYPERMÉTROPIE)
    students_avec_prescription = Student.query.filter(
        (Student.sph_od.isnot(None)) | (Student.sph_og.isnot(None))
    ).all()

    prescriptions = {
        'myopie_faible': 0,          # Sph entre 0 et -3.00
        'myopie_forte': 0,           # Sph <= -3.00
        'hypermetropie_faible': 0,   # Sph entre 0 et +3.00
        'hypermetropie_forte': 0,    # Sph >= +3.00
        'myopie_astigmate': 0,
        'hypermetropie_astigmate': 0
    }

    for s in students_avec_prescription:
        sph = None
        cyl = None

        if s.sph_od is not None and s.sph_og is not None:
            # On prend la sphère la plus forte en valeur absolue
            if abs(s.sph_od) >= abs(s.sph_og):
                sph = s.sph_od
                cyl = s.cyl_od
            else:
                sph = s.sph_og
                cyl = s.cyl_og
        elif s.sph_od is not None:
            sph = s.sph_od
            cyl = s.cyl_od
        elif s.sph_og is not None:
            sph = s.sph_og
            cyl = s.cyl_og

        if sph is not None:
            # Myopie
            if sph < 0:
                if sph <= -3.00:
                    prescriptions['myopie_forte'] += 1
                else:
                    prescriptions['myopie_faible'] += 1

                if cyl is not None and abs(cyl) >= 0.75:
                    prescriptions['myopie_astigmate'] += 1

            # Hypermétropie
            elif sph > 0:
                if sph >= 3.00:
                    prescriptions['hypermetropie_forte'] += 1
                else:
                    prescriptions['hypermetropie_faible'] += 1

                if cyl is not None and abs(cyl) >= 0.75:
                    prescriptions['hypermetropie_astigmate'] += 1

    # 3. DÉTAIL PRISES EN CHARGE (BLOC QUE VOUS TROUVEZ LE PLUS JUSTE)
    stats_prise_en_charge = {
        'Lunettes': eleves_avec_pec_query.filter(Student.prise_en_charge.like('%lunettes%')).count(),
        'Médicament': eleves_avec_pec_query.filter(Student.prise_en_charge.like('%medicament%')).count(),
        'Référé Ophtalmo': eleves_avec_pec_query.filter(Student.prise_en_charge.like('%refere_oph%')).count(),
        'Référé Orthoptiste': eleves_avec_pec_query.filter(Student.prise_en_charge.like('%refere_orthoptiste%')).count(),
        'Chirurgie': eleves_avec_pec_query.filter(Student.prise_en_charge.like('%chirurgie%')).count(),
        'RAS': eleves_avec_pec_query.filter(Student.prise_en_charge.like('%ras%')).count(),
    }

    # Maintenant, on aligne les compteurs globaux sur ce bloc détaillé
    lunettes_prescrites = stats_prise_en_charge['Lunettes']
    referes = (
        stats_prise_en_charge['Référé Ophtalmo']
        + stats_prise_en_charge['Référé Orthoptiste']
        + stats_prise_en_charge['Chirurgie']
    )
    ras = stats_prise_en_charge['RAS']

    # 4. RÉPARTITION PAR ÉCOLE / SITE (UNIQUEMENT SI PLUS D'UNE ÉCOLE)
    stats_ecole = db.session.query(
        Student.ecole,
        Student.site,
        func.count(Student.id).label('total'),
        func.sum(
            case(
                (and_(Student.prise_en_charge.isnot(None), Student.prise_en_charge != ''), 1),
                else_=0
            )
        ).label('consultes'),
        func.sum(case((Student.prise_en_charge.like('%lunettes%'), 1), else_=0)).label('lunettes'),
        func.sum(case((Student.prise_en_charge.like('%medicament%'), 1), else_=0)).label('medicament'),
        func.sum(case((Student.prise_en_charge.like('%refere_oph%'), 1), else_=0)).label('refere_oph'),
        func.sum(case((Student.prise_en_charge.like('%refere_orthoptiste%'), 1), else_=0)).label('refere_ortho'),
        func.sum(case((Student.prise_en_charge.like('%chirurgie%'), 1), else_=0)).label('chirurgie'),
        func.sum(case((Student.prise_en_charge.like('%ras%'), 1), else_=0)).label('ras_nb')
    ).group_by(Student.ecole, Student.site).all()

    multi_ecoles = len(stats_ecole) > 1

    return render_template(
        'statistics.html',
        total_students=total_students,
        consultations_completees=consultations_completees,
        lunettes_prescrites=lunettes_prescrites,
        referes=referes,
        ras=ras,
        taux_completude=taux_completude,
        prescriptions=prescriptions,
        stats_prise_en_charge=stats_prise_en_charge,
        stats_ecole=stats_ecole,
        multi_ecoles=multi_ecoles
    )
