from io import BytesIO
from decimal import Decimal

import qrcode

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum
from django.http import HttpResponse
from django.utils import timezone

from accounts.views import prefet_required
from bulletin.models import ModeleBulletin
from classes.models import Classe, AnneeScolaire
from grades.models import Note
from school_settings.models import SchoolInfo
from students.models import Student
from subjects.models import MatiereClasse

from .forms import ActivationForm, CodeAccesForm, PortailConfigForm
from .models import PortailAcces, PortailConfig, PublicationResultats

PERIODES_NORMALES = ['1P', '2P', 'EXAM1', '3P', '4P', 'EXAM2']
PERIODES_LABELS = dict(PublicationResultats.PERIODE_CHOICES)

SESSION_KEY = 'portail_auth'


def _get_acces(eleve):
    acces, _ = PortailAcces.objects.get_or_create(eleve=eleve)
    return acces


def _build_qr_url(request, token):
    config = PortailConfig.get_config()
    base = config.url_portail.rstrip('/') if config.url_portail else request.build_absolute_uri('/').rstrip('/')
    return f"{base}/portail/scan/{token}/"


def _calc_resultats_par_periode(modele, eleve, periodes_a_afficher):
    """Retourne un dict {periode: {label, notes, total_obtenu, total_max, pourcentage, rang}}.

    Optimisations ORM :
    - 1 seule requête pour tous les MatiereClasse de la classe
    - 1 seule requête pour toutes les notes de l'élève (toutes périodes d'un coup)
    - 1 seule requête par période pour les rangs (agrégat par élève)
    """
    resultats = {}
    bms = list(modele.matieres.select_related('matiere').order_by('matiere__maxima', 'ordre'))

    # ── Charger tous les MatiereClasse de la classe en une seule requête ──
    matieres_ids = [bm.matiere_id for bm in bms]
    mc_map = {
        mc.matiere_id: mc
        for mc in MatiereClasse.objects.filter(
            matiere_id__in=matieres_ids, classe=modele.classe
        ).select_related('matiere')
    }
    mc_ids = list(mc_map[mid].pk for mid in mc_map)

    # ── Charger toutes les notes de l'élève en une seule requête ──
    notes_eleve = {}
    for note in Note.objects.filter(
        eleve=eleve,
        matiere_classe__in=list(mc_map.values()),
        periode__in=periodes_a_afficher,
    ).select_related('matiere_classe'):
        notes_eleve[(note.matiere_classe_id, note.periode)] = note.valeur

    for periode in periodes_a_afficher:
        data = {
            'label': PERIODES_LABELS.get(periode, periode),
            'notes': [],
            'total_obtenu': Decimal('0'),
            'total_max': Decimal('0'),
            'pourcentage': 0,
            'rang': '-',
        }
        for bm in bms:
            mc = mc_map.get(bm.matiere_id)
            if mc is None:
                continue                         # matière non affectée à cette classe
            valeur = notes_eleve.get((mc.pk, periode))
            mx = Decimal(str(bm.matiere.maxima))
            data['total_max'] += mx
            if valeur is not None:
                data['total_obtenu'] += valeur
            data['notes'].append({'matiere': bm.matiere, 'note': valeur, 'maxima': bm.matiere.maxima})
        if data['total_max'] > 0:
            data['pourcentage'] = round(float(data['total_obtenu']) / float(data['total_max']) * 100, 2)
        resultats[periode] = data

    # ── Calcul des rangs — 1 requête par période ──
    for periode, data in resultats.items():
        try:
            scores = list(
                Note.objects.filter(matiere_classe__in=mc_ids, periode=periode)
                .values('eleve')
                .annotate(total=Sum('valeur'))
                .order_by('-total')
                .values_list('total', flat=True)
            )
            rang = next(
                (i + 1 for i, s in enumerate(scores)
                 if s is not None and abs(float(s) - float(data['total_obtenu'])) < 0.001),
                '-'
            )
            data['rang'] = rang
        except Exception:
            data['rang'] = '-'

    return resultats


# ─── Portail public ───────────────────────────────────────────────────────────

def portail_accueil(request):
    config = PortailConfig.get_config()
    school = SchoolInfo.get_info()
    return render(request, 'portail/accueil.html', {'config': config, 'school': school})


def portail_scan(request, token):
    acces = get_object_or_404(PortailAcces, token=token)
    config = PortailConfig.get_config()
    school = SchoolInfo.get_info()
    ctx = {'config': config, 'school': school, 'acces': acces}

    if acces.is_bloque():
        return render(request, 'portail/bloque.html', ctx)

    if not acces.active:
        # ── Première utilisation : créer un code d'accès ──
        form = ActivationForm(request.POST or None)
        if request.method == 'POST' and form.is_valid():
            acces.definir_code(form.cleaned_data['code'])
            request.session[SESSION_KEY] = str(acces.token)
            messages.success(request, "Code d'accès créé ! Votre bulletin est maintenant accessible.")
            return redirect('portail_resultats', token=token)
        ctx['form'] = form
        return render(request, 'portail/activation.html', ctx)
    else:
        # ── Connexion : vérifier le code ──
        form = CodeAccesForm(request.POST or None)
        if request.method == 'POST' and form.is_valid():
            if acces.verifier_code(form.cleaned_data['code']):
                acces.tentatives_echec = 0
                acces.bloque_jusqu = None
                acces.save(update_fields=['tentatives_echec', 'bloque_jusqu'])
                request.session[SESSION_KEY] = str(acces.token)
                return redirect('portail_resultats', token=token)
            else:
                acces.incrementer_tentatives()
                if acces.is_bloque():
                    messages.error(request, "Trop de tentatives incorrectes. Accès bloqué 15 minutes.")
                    return redirect('portail_scan', token=token)
                restantes = max(0, 5 - acces.tentatives_echec)
                messages.error(request, f"Code incorrect. {restantes} tentative(s) restante(s).")
        ctx['form'] = form
        return render(request, 'portail/connexion.html', ctx)


def portail_resultats(request, token):
    acces = get_object_or_404(PortailAcces, token=token)
    if request.session.get(SESSION_KEY) != str(acces.token):
        return redirect('portail_scan', token=token)

    config = PortailConfig.get_config()
    school = SchoolInfo.get_info()
    eleve = acces.eleve

    if not eleve.classe:
        return render(request, 'portail/pas_publie.html', {
            'config': config, 'school': school, 'eleve': eleve,
            'message': "Cet élève n'est pas encore affecté à une classe."
        })

    annee = eleve.classe.annee_scolaire
    periodes_publiees = set(
        PublicationResultats.objects.filter(
            classe=eleve.classe, annee_scolaire=annee, publie=True
        ).values_list('periode', flat=True)
    )

    if not periodes_publiees:
        return render(request, 'portail/pas_publie.html', {
            'config': config, 'school': school, 'eleve': eleve,
            'message': "Aucun résultat n'a encore été publié pour votre classe."
        })

    try:
        modele = ModeleBulletin.objects.get(classe=eleve.classe, annee_scolaire=annee)
    except ModeleBulletin.DoesNotExist:
        return render(request, 'portail/pas_publie.html', {
            'config': config, 'school': school, 'eleve': eleve,
            'message': "Le modèle de bulletin de cette classe n'est pas encore configuré."
        })

    periodes_a_afficher = [p for p in PERIODES_NORMALES if p in periodes_publiees]
    resultats = _calc_resultats_par_periode(modele, eleve, periodes_a_afficher)

    # Résultat annuel
    resultat_annuel = None
    if 'ANNUEL' in periodes_publiees and resultats:
        total_annuel = sum(d['total_obtenu'] for d in resultats.values())
        max_annuel = sum(d['total_max'] for d in resultats.values())
        pct_annuel = round(float(total_annuel) / float(max_annuel) * 100, 2) if max_annuel else 0

        mc_ids = list(MatiereClasse.objects.filter(classe=eleve.classe).values_list('pk', flat=True))
        scores_annuel = []
        for e in Student.objects.filter(classe=eleve.classe):
            t = sum(
                (Note.objects.filter(eleve=e, matiere_classe__in=mc_ids, periode=p)
                 .aggregate(t=Sum('valeur'))['t'] or Decimal('0'))
                for p in periodes_a_afficher
            )
            scores_annuel.append(t)
        scores_annuel.sort(reverse=True)
        try:
            rang_annuel = scores_annuel.index(total_annuel) + 1
        except ValueError:
            rang_annuel = '-'

        resultat_annuel = {
            'total': total_annuel, 'max': max_annuel,
            'pourcentage': pct_annuel, 'rang': rang_annuel,
        }

    return render(request, 'portail/resultats.html', {
        'config': config, 'school': school, 'eleve': eleve,
        'acces': acces,
        'modele': modele,                        # ← pour URL téléchargement bulletin
        'resultats': resultats,
        'resultat_annuel': resultat_annuel,
        'nb_eleves': eleve.classe.eleves.count(),
        'annee': annee,
    })


def portail_bulletin_pdf(request, token):
    """Portail parents : téléchargement du bulletin PDF via token (session requise)."""
    acces = get_object_or_404(PortailAcces, token=token)
    if request.session.get(SESSION_KEY) != str(acces.token):
        return redirect('portail_scan', token=token)

    eleve = acces.eleve
    if not eleve.classe:
        from django.http import HttpResponseBadRequest
        return HttpResponseBadRequest("Élève sans classe.")

    annee = eleve.classe.annee_scolaire
    try:
        modele = ModeleBulletin.objects.get(classe=eleve.classe, annee_scolaire=annee)
    except ModeleBulletin.DoesNotExist:
        from django.http import HttpResponseBadRequest
        return HttpResponseBadRequest("Bulletin non configuré pour cette classe.")

    # Vérifier que le résultat annuel est publié
    annuel_publie = PublicationResultats.objects.filter(
        classe=eleve.classe, annee_scolaire=annee, periode='ANNUEL', publie=True
    ).exists()
    if not annuel_publie:
        from django.http import HttpResponseBadRequest
        return HttpResponseBadRequest("Le bulletin annuel n'est pas encore publié.")

    from bulletin.pdf_views import build_bulletin_pdf_response
    return build_bulletin_pdf_response(modele, eleve)


def portail_deconnexion(request, token):
    request.session.pop(SESSION_KEY, None)
    return redirect('portail_scan', token=token)


# ─── QR Code image ────────────────────────────────────────────────────────────

def qr_code_image(request, pk):
    """Renvoie l'image PNG du QR Code d'un élève (accessible Préfet + carte)."""
    eleve = get_object_or_404(Student, pk=pk)
    acces = _get_acces(eleve)
    url = _build_qr_url(request, acces.token)

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10, border=3,
    )
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")

    buf = BytesIO()
    img.save(buf, format='PNG')
    return HttpResponse(buf.getvalue(), content_type='image/png')


# ─── Back-office Préfet ───────────────────────────────────────────────────────

@login_required
@prefet_required
def publication_list(request):
    annee = AnneeScolaire.objects.filter(active=True).first()
    classes = (
        Classe.objects.filter(annee_scolaire=annee).select_related('section')
        if annee else []
    )
    PERIODES = PublicationResultats.PERIODE_CHOICES

    grille = []
    for classe in classes:
        pubs = {
            p.periode: p
            for p in PublicationResultats.objects.filter(classe=classe, annee_scolaire=annee)
        }
        ligne = []
        for code, label in PERIODES:
            pub = pubs.get(code)
            ligne.append({
                'code': code, 'label': label,
                'pub': pub,
                'publie': pub.publie if pub else False,
            })
        grille.append({'classe': classe, 'periodes': ligne})

    return render(request, 'portail/publication_list.html', {
        'grille': grille,
        'periodes': PERIODES,
        'annee': annee,
    })


@login_required
@prefet_required
def publication_toggle(request, classe_id, periode):
    annee = get_object_or_404(AnneeScolaire, active=True)
    classe = get_object_or_404(Classe, pk=classe_id)
    pub, _ = PublicationResultats.objects.get_or_create(
        classe=classe, annee_scolaire=annee, periode=periode,
        defaults={'publie': False}
    )
    if pub.publie:
        pub.depublier()
        messages.success(request, f"Dépublié : {classe} — {pub.get_periode_display()}")
    else:
        pub.publier(request.user)
        messages.success(request, f"Publié : {classe} — {pub.get_periode_display()}")
    return redirect('publication_list')


@login_required
@prefet_required
def portail_config_view(request):
    config = PortailConfig.get_config()
    form = PortailConfigForm(request.POST or None, request.FILES or None, instance=config)
    if form.is_valid():
        form.save()
        messages.success(request, "Configuration du portail enregistrée.")
        return redirect('portail_config')
    return render(request, 'portail/config.html', {'form': form, 'config': config})


@login_required
@prefet_required
def reset_acces_eleve(request, pk):
    eleve = get_object_or_404(Student, pk=pk)
    acces, created = PortailAcces.objects.get_or_create(eleve=eleve)
    if not created and acces.active:
        acces.reset_acces()
        messages.success(request, f"Accès portail réinitialisé pour {eleve.nom_complet}. Le parent devra créer un nouveau code.")
    else:
        messages.info(request, f"L'accès de {eleve.nom_complet} n'était pas encore activé.")
    return redirect('student_detail', pk=pk)


@login_required
@prefet_required
def acces_list(request):
    """Liste tous les élèves avec leur statut d'accès portail."""
    annee = AnneeScolaire.objects.filter(active=True).first()
    classe_id = request.GET.get('classe', '')
    eleves = Student.objects.select_related('classe', 'classe__section', 'portail_acces')
    if classe_id:
        eleves = eleves.filter(classe_id=classe_id)
    elif annee:
        eleves = eleves.filter(classe__annee_scolaire=annee)
    classes = Classe.objects.filter(annee_scolaire=annee).select_related('section') if annee else []
    return render(request, 'portail/acces_list.html', {
        'eleves': eleves, 'classes': classes, 'classe_id': classe_id, 'annee': annee,
    })
