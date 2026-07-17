"""
Génération PDF du bulletin individuel au format IGE/P.S/005.
Utilise ReportLab Platypus pour reproduire le tableau officiel RDC.
"""
from io import BytesIO
from decimal import Decimal

from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import cm, mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph,
    Spacer, HRFlowable
)
from reportlab.platypus.flowables import KeepTogether

from .models import ModeleBulletin
from students.models import Student
from grades.models import Note
from subjects.models import MatiereClasse
from school_settings.models import SchoolInfo


# ─── Palette ──────────────────────────────────────────────────────────────────
DARK      = colors.HexColor('#1a1a2e')
BLUE      = colors.HexColor('#1565C0')
GREY_HDR  = colors.HexColor('#CFD8DC')
GREY_MAX  = colors.HexColor('#ECEFF1')
WHITE     = colors.white
BLACK     = colors.black
RED_FAIL  = colors.HexColor('#FFCDD2')
GRN_PASS  = colors.HexColor('#C8E6C9')


def _note_str(val):
    if val is None:
        return ''
    v = float(val)
    return str(int(v)) if v == int(v) else f"{v:.1f}"


def _calc_eleve(modele, eleve):
    """Calcule toutes les données de notes pour un élève, renvoie (matieres_data, total_obtenu, total_max)."""
    periodes = ['1P', '2P', 'EXAM1', '3P', '4P', 'EXAM2', 'REPECHAGE']
    matieres_data = []
    total_obtenu = Decimal('0')
    total_max_tg = Decimal('0')

    for bm in modele.matieres.select_related('matiere').order_by('matiere__maxima', 'ordre'):
        mat = bm.matiere
        notes_dict = {}
        try:
            mc = MatiereClasse.objects.get(matiere=mat, classe=modele.classe)
            for p in periodes:
                try:
                    n = Note.objects.get(eleve=eleve, matiere_classe=mc, periode=p)
                    notes_dict[p] = n.valeur
                except Note.DoesNotExist:
                    notes_dict[p] = None
        except Exception:
            for p in periodes:
                notes_dict[p] = None

        mx   = mat.maxima
        n1p  = notes_dict.get('1P')    or Decimal('0')
        n2p  = notes_dict.get('2P')    or Decimal('0')
        ne1  = notes_dict.get('EXAM1') or Decimal('0')
        n3p  = notes_dict.get('3P')    or Decimal('0')
        n4p  = notes_dict.get('4P')    or Decimal('0')
        ne2  = notes_dict.get('EXAM2') or Decimal('0')

        has_s1 = any(notes_dict.get(p) is not None for p in ('1P', '2P', 'EXAM1'))
        has_s2 = any(notes_dict.get(p) is not None for p in ('3P', '4P', 'EXAM2'))

        tot_s1 = (n1p + n2p + ne1) if has_s1 else None
        tot_s2 = (n3p + n4p + ne2) if has_s2 else None
        tg     = (tot_s1 or Decimal('0')) + (tot_s2 or Decimal('0'))
        max_tg = Decimal(mx) * 8

        total_obtenu += tg
        total_max_tg += max_tg

        matieres_data.append({
            'matiere':  mat,
            'n1p':      notes_dict.get('1P'),
            'n2p':      notes_dict.get('2P'),
            'nexam1':   notes_dict.get('EXAM1'),
            'tot_s1':   tot_s1,
            'n3p':      notes_dict.get('3P'),
            'n4p':      notes_dict.get('4P'),
            'nexam2':   notes_dict.get('EXAM2'),
            'tot_s2':   tot_s2,
            'tg':       tg,
            'repechage': notes_dict.get('REPECHAGE'),
        })

    pct = round(float(total_obtenu) / float(total_max_tg) * 100, 2) if total_max_tg else 0
    return matieres_data, total_obtenu, total_max_tg, pct


def _get_classement(modele, eleve_score):
    from django.db.models import Sum
    scores = []
    for e in Student.objects.filter(classe=modele.classe):
        total = Note.objects.filter(
            eleve=e, matiere_classe__classe=modele.classe
        ).exclude(periode='REPECHAGE').aggregate(total=Sum('valeur'))['total'] or Decimal('0')
        scores.append(total)
    scores.sort(reverse=True)
    try:
        return scores.index(eleve_score) + 1
    except ValueError:
        return '-'


def _mention(pct):
    if pct >= 80:   return 'Grande distinction'
    if pct >= 70:   return 'Distinction'
    if pct >= 60:   return 'Satisfaction'
    if pct >= 50:   return 'Réussite'
    return 'Échec'


# ─── Styles ────────────────────────────────────────────────────────────────────
def _styles():
    base = getSampleStyleSheet()
    tiny  = ParagraphStyle('tiny',  parent=base['Normal'], fontSize=6.5, leading=8)
    small = ParagraphStyle('small', parent=base['Normal'], fontSize=7.5, leading=9)
    bold  = ParagraphStyle('bold',  parent=base['Normal'], fontSize=7.5, leading=9, fontName='Helvetica-Bold')
    ctr   = ParagraphStyle('ctr',   parent=base['Normal'], fontSize=7,   leading=8.5, alignment=TA_CENTER)
    ctr_b = ParagraphStyle('ctr_b', parent=base['Normal'], fontSize=7,   leading=8.5, alignment=TA_CENTER, fontName='Helvetica-Bold')
    hdr   = ParagraphStyle('hdr',   parent=base['Normal'], fontSize=8.5, leading=10, fontName='Helvetica-Bold', alignment=TA_CENTER)
    title = ParagraphStyle('title', parent=base['Normal'], fontSize=9,   leading=11, fontName='Helvetica-Bold', alignment=TA_CENTER)
    return tiny, small, bold, ctr, ctr_b, hdr, title


# ─── Vue principale ────────────────────────────────────────────────────────────
@login_required
def bulletin_eleve_pdf(request, pk, eleve_pk):
    modele = get_object_or_404(ModeleBulletin, pk=pk)
    if request.user.is_enseignant():
        from django.http import HttpResponseForbidden
        return HttpResponseForbidden("Accès réservé au Préfet.")

    eleve = get_object_or_404(Student, pk=eleve_pk)
    school = SchoolInfo.get_info()

    matieres_data, total_obtenu, total_max, pct = _calc_eleve(modele, eleve)
    classement = _get_classement(modele, total_obtenu)
    nb_eleves  = eleve.classe.eleves.count() if eleve.classe else 0
    mention    = _mention(pct)

    # ── Document ──
    buf = BytesIO()
    page_w, page_h = A4
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=1.2*cm, rightMargin=1.2*cm,
        topMargin=1.0*cm,  bottomMargin=1.0*cm,
        title=f"Bulletin {eleve.nom_complet}",
    )
    tiny, small, bold, ctr, ctr_b, hdr, title_style = _styles()
    story = []

    # ── En-tête nationale ──
    story.append(Paragraph(
        "REPUBLIQUE DEMOCRATIQUE DU CONGO<br/>"
        "<font size='6'>MINISTERE DE L'ENSEIGNEMENT PRIMAIRE, SECONDAIRE ET PROFESSIONNEL</font>",
        hdr
    ))
    story.append(Spacer(1, 3*mm))

    # ── Infos école / élève côte à côte ──
    p_school = school.province if school else ''
    v_school  = school.ville    if school else ''
    c_school  = school.commune  if school else ''
    n_school  = school.nom      if school else ''
    co_school = school.code     if school else ''

    info_data = [[
        Paragraph(
            f"<b>PROVINCE :</b> {p_school}<br/>"
            f"<b>VILLE :</b> {v_school} &nbsp; <b>COMMUNE :</b> {c_school}<br/>"
            f"<b>ÉCOLE :</b> {n_school}<br/>"
            f"<b>CODE :</b> {co_school}",
            small
        ),
        Paragraph(
            f"<b>ÉLÈVE :</b> {eleve.nom_complet} &nbsp;&nbsp; <b>SEXE :</b> {eleve.get_sexe_display()}<br/>"
            f"<b>NÉ(E) À :</b> {eleve.lieu_naissance or ''} &nbsp; <b>LE</b> {eleve.date_naissance.strftime('%d/%m/%Y') if eleve.date_naissance else ''}<br/>"
            f"<b>CLASSE :</b> {modele.classe}<br/>"
            f"<b>N° PERM. :</b> {eleve.matricule}",
            small
        ),
    ]]
    avail_w = page_w - 2.4*cm
    info_tbl = Table(info_data, colWidths=[avail_w/2, avail_w/2])
    info_tbl.setStyle(TableStyle([
        ('BOX',       (0, 0), (-1, -1), 0.5, BLACK),
        ('LINEBEFORE',(1, 0), (1, 0), 0.5, BLACK),
        ('VALIGN',    (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING',(0, 0), (-1, -1), 3),
        ('BOTTOMPADDING',(0,0),(-1,-1),3),
        ('LEFTPADDING', (0,0),(-1,-1),5),
    ]))
    story.append(info_tbl)
    story.append(Spacer(1, 1*mm))

    # ── Titre du bulletin ──
    story.append(Table([[Paragraph(
        f"BULLETIN — {modele.classe} — ANNÉE SCOLAIRE {modele.annee_scolaire}",
        title_style
    )]], colWidths=[avail_w], style=TableStyle([
        ('BOX', (0,0), (-1,-1), 0.5, BLACK),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
    ])))
    story.append(Spacer(1, 1.5*mm))

    # ── Tableau des notes ──
    # Colonnes : Branche | 1P | 2P | EXAM1 | TOT.S1 | 3P | 4P | EXAM2 | TOT.S2 | TG | % REPÊCH | SIGN
    COL_W = [avail_w * f for f in [.23, .07, .07, .07, .07, .07, .07, .07, .07, .07, .07, .06]]

    def _h(txt): return Paragraph(txt, ctr_b)
    def _c(txt): return Paragraph(txt, ctr)
    def _b(txt): return Paragraph(txt, bold)

    # Ligne de titres de colonnes (3 niveaux fusionnés via span)
    header_rows = [
        [_h('BRANCHES'), _h('PREMIER SEMESTRE'), '', '', '', _h('SECOND SEMESTRE'), '', '', '', _h('T.G.'), _h('REP.'), _h('SIGN.')],
        ['',              _h('TR. JOURNAL.'), '', _h('EXAM'), _h('TOT.'), _h('TR. JOURNAL.'), '', _h('EXAM'), _h('TOT.'), '', '', ''],
        ['',              _h('1ère P'), _h('2ème P'), '', '', _h('3ème P'), _h('4ème P'), '', '', '', '', ''],
    ]

    tbl_data = list(header_rows)

    # Grouper par maxima
    groups = {}
    for row in matieres_data:
        mx = row['matiere'].maxima
        groups.setdefault(mx, []).append(row)

    span_cmds = []          # styles à ajouter dynamiquement
    row_styles = []         # fonds colorés par ligne
    current_row = 3         # après les 3 lignes d'en-tête

    for mx in sorted(groups.keys()):
        # Ligne MAXIMA
        mx2 = mx * 2
        mx4 = mx * 4
        mx8 = mx * 8
        tbl_data.append([
            _b('MAXIMA'), _c(str(mx)), _c(str(mx)), _c(str(mx2)), _c(str(mx4)),
            _c(str(mx)), _c(str(mx)), _c(str(mx2)), _c(str(mx4)),
            _c(str(mx8)), '', '',
        ])
        row_styles.append(('BACKGROUND', (0, current_row), (-1, current_row), GREY_MAX))
        row_styles.append(('FONTNAME',   (0, current_row), (-1, current_row), 'Helvetica-Bold'))
        current_row += 1

        for row in groups[mx]:
            tg_str = _note_str(row['tg']) if row['tg'] else ''
            pct_row = round(float(row['tg']) / float(mx * 8) * 100, 0) if row['tg'] and mx * 8 > 0 else ''
            pct_str = f"{int(pct_row)}%" if pct_row != '' else ''
            tbl_data.append([
                Paragraph(row['matiere'].nom, small),
                _c(_note_str(row['n1p'])),
                _c(_note_str(row['n2p'])),
                _c(_note_str(row['nexam1'])),
                _c(_note_str(row['tot_s1'])),
                _c(_note_str(row['n3p'])),
                _c(_note_str(row['n4p'])),
                _c(_note_str(row['nexam2'])),
                _c(_note_str(row['tot_s2'])),
                Paragraph(f"<b>{tg_str}</b>", ctr_b),
                _c(_note_str(row['repechage'])),
                '',
            ])
            current_row += 1

    # Ligne MAXIMA GÉNÉRAUX
    tbl_data.append([_b('MAXIMA GÉNÉRAUX'), '', '', '', '', '', '', '', '', _c(str(int(total_max))), '', ''])
    row_styles.append(('BACKGROUND', (0, current_row), (-1, current_row), GREY_MAX))
    span_cmds.append(('SPAN', (0, current_row), (8, current_row)))
    span_cmds.append(('SPAN', (10, current_row), (11, current_row)))
    current_row += 1

    # TOTAUX
    tbl_data.append([
        _b('TOTAUX'), '', '', '', _c(str(_note_str(None))),
        '', '', '', '',
        Paragraph(f"<b>{_note_str(total_obtenu)} / {_note_str(total_max)}</b>", ctr_b),
        '', '',
    ])
    row_styles.append(('FONTNAME', (0, current_row), (-1, current_row), 'Helvetica-Bold'))
    current_row += 1

    # POURCENTAGE
    tbl_data.append([
        _b('POURCENTAGE'), '', '', '', '',
        '', '', '', '',
        Paragraph(f"<b>{pct}%</b>", ctr_b),
        '', '',
    ])
    current_row += 1

    # MENTION
    tbl_data.append([
        _b('MENTION'), '', '', '', '',
        '', '', '', '',
        Paragraph(f"<b>{mention}</b>", ctr_b),
        '', '',
    ])
    current_row += 1

    # CLASSEMENT
    tbl_data.append([
        _b('PLACE / NBRE ÉLÈVES'), '', '', '', '',
        '', '', '', '',
        Paragraph(f"<b>{classement} / {nb_eleves}</b>", ctr_b),
        '', '',
    ])
    current_row += 1

    # APPLICATION / CONDUITE
    for label in ['APPLICATION', 'CONDUITE']:
        tbl_data.append([_b(label)] + [''] * 11)
        current_row += 1

    # SIGN. DU RESPONSABLE
    tbl_data.append([_b("SIGN. DU RESPONSABLE")] + [''] * 11)
    current_row += 1

    # ── Construction du tableau ──
    note_tbl = Table(tbl_data, colWidths=COL_W, repeatRows=3)

    total_rows = current_row
    base_style = [
        # En-têtes
        ('BACKGROUND',   (0, 0), (-1, 2), GREY_HDR),
        ('FONTNAME',     (0, 0), (-1, 2), 'Helvetica-Bold'),
        ('FONTSIZE',     (0, 0), (-1, -1), 6.5),
        ('LEADING',      (0, 0), (-1, -1), 8),
        ('ALIGN',        (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN',       (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN',        (0, 3), (0, -1), 'LEFT'),
        # Fusions en-têtes
        ('SPAN',  (0, 0), (0, 2)),   # BRANCHES
        ('SPAN',  (1, 0), (4, 0)),   # PREMIER SEMESTRE
        ('SPAN',  (5, 0), (8, 0)),   # SECOND SEMESTRE
        ('SPAN',  (9, 0), (9, 2)),   # TG
        ('SPAN',  (10, 0),(10, 2)),  # REP
        ('SPAN',  (11, 0),(11, 2)),  # SIGN
        ('SPAN',  (1, 1), (2, 1)),   # TR. JOURNAL S1
        ('SPAN',  (3, 1), (3, 2)),   # EXAM S1
        ('SPAN',  (4, 1), (4, 2)),   # TOT S1
        ('SPAN',  (5, 1), (6, 1)),   # TR. JOURNAL S2
        ('SPAN',  (7, 1), (7, 2)),   # EXAM S2
        ('SPAN',  (8, 1), (8, 2)),   # TOT S2
        # Grille
        ('GRID',         (0, 0), (-1, -1), 0.3, colors.grey),
        ('BOX',          (0, 0), (-1, -1), 0.8, BLACK),
        ('LINEABOVE',    (0, 3), (-1, 3), 0.8, BLACK),
        # Padding
        ('TOPPADDING',   (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING',(0, 0), (-1, -1), 2),
        ('LEFTPADDING',  (0, 0), (0, -1), 3),
    ]

    # Fusion des lignes "bilan" (Totaux, %, Mention, Place, Application, Conduite, Sign)
    bilan_start = total_rows - 7
    for r in range(bilan_start, total_rows):
        base_style.append(('SPAN', (0, r), (8, r)))
        base_style.append(('SPAN', (10, r), (11, r)))

    note_tbl.setStyle(TableStyle(base_style + row_styles + span_cmds))
    story.append(note_tbl)
    story.append(Spacer(1, 3*mm))

    # ── Pied de page légal ──
    footer_lines = [
        "- L'élève ne pourra passer dans la classe supérieure s'il n'a subi avec succès un examen de repêchage en...................",
        "- L'élève passe dans la classe supérieure  (1)",
        "- L'élève double sa classe  (1)",
        "- L'élève a échoué et est à réorienter vers..................  (1)",
    ]
    for line in footer_lines:
        story.append(Paragraph(line, tiny))
    story.append(Spacer(1, 4*mm))

    sigs = Table([[
        Paragraph("Signature de l'élève", small),
        Paragraph("Sceau de l'école", small),
        Paragraph("Le Chef d'Établissement<br/>Nom et Signature", small),
    ]], colWidths=[avail_w/3]*3)
    sigs.setStyle(TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN',(0,0), (-1,-1), 'TOP'),
    ]))
    story.append(sigs)
    story.append(Spacer(1, 3*mm))
    story.append(Paragraph("IGE/P.S/005", ParagraphStyle('ref', fontSize=6, alignment=TA_RIGHT)))

    doc.build(story)
    buf.seek(0)
    filename = f"bulletin_{eleve.matricule}_{modele.annee_scolaire}.pdf"
    resp = HttpResponse(buf, content_type='application/pdf')
    resp['Content-Disposition'] = f'inline; filename="{filename}"'
    return resp
