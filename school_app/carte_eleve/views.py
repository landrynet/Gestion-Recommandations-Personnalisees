import base64
from io import BytesIO

import qrcode

from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required

from accounts.views import prefet_required
from classes.models import Classe, AnneeScolaire
from portail.models import PortailAcces, PortailConfig
from school_settings.models import SchoolInfo
from students.models import Student


def _get_acces(eleve):
    acces, _ = PortailAcces.objects.get_or_create(eleve=eleve)
    return acces


def _qr_base64(request, eleve):
    acces = _get_acces(eleve)
    config = PortailConfig.get_config()
    base_url = config.url_portail.rstrip('/') if config.url_portail else request.build_absolute_uri('/').rstrip('/')
    url = f"{base_url}/portail/scan/{acces.token}/"

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=6, border=2,
    )
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = BytesIO()
    img.save(buf, format='PNG')
    return base64.b64encode(buf.getvalue()).decode()


@login_required
@prefet_required
def carte_list(request):
    annee = AnneeScolaire.objects.filter(active=True).first()
    classe_id = request.GET.get('classe', '')
    classes = Classe.objects.filter(annee_scolaire=annee).select_related('section') if annee else []
    eleves = Student.objects.select_related('classe', 'classe__section')
    if classe_id:
        eleves = eleves.filter(classe_id=classe_id)
    elif annee:
        eleves = eleves.filter(classe__annee_scolaire=annee)
    return render(request, 'carte_eleve/liste.html', {
        'eleves': eleves, 'classes': classes,
        'classe_id': classe_id, 'annee': annee,
    })


@login_required
@prefet_required
def carte_preview(request, pk):
    eleve = get_object_or_404(Student, pk=pk)
    school = SchoolInfo.get_info()
    config = PortailConfig.get_config()
    qr_b64 = _qr_base64(request, eleve)
    return render(request, 'carte_eleve/carte_single.html', {
        'eleves_data': [{'eleve': eleve, 'qr_b64': qr_b64}],
        'school': school, 'config': config,
        'annee': eleve.classe.annee_scolaire if eleve.classe else None,
        'mode': 'preview',
        'titre': f"Carte de {eleve.nom_complet}",
    })


@login_required
@prefet_required
def cartes_classe(request, classe_id):
    classe = get_object_or_404(Classe, pk=classe_id)
    school = SchoolInfo.get_info()
    config = PortailConfig.get_config()

    # Paginer par lots de 20 pour éviter de tout charger en mémoire
    LOT = 20
    try:
        page = max(1, int(request.GET.get('page', 1)))
    except (ValueError, TypeError):
        page = 1
    offset = (page - 1) * LOT

    eleves_qs = Student.objects.filter(classe=classe).order_by('nom', 'postnom')
    total = eleves_qs.count()
    eleves_lot = eleves_qs[offset:offset + LOT]

    eleves_data = [{'eleve': e, 'qr_b64': _qr_base64(request, e)} for e in eleves_lot]

    nb_pages = (total + LOT - 1) // LOT
    return render(request, 'carte_eleve/carte_single.html', {
        'eleves_data': eleves_data, 'school': school, 'config': config,
        'annee': classe.annee_scolaire, 'mode': 'print',
        'titre': f"Cartes — {classe}",
        'page': page, 'nb_pages': nb_pages, 'total': total,
        'page_suivante': page + 1 if page < nb_pages else None,
        'page_precedente': page - 1 if page > 1 else None,
        'classe_id': classe_id,
    })
