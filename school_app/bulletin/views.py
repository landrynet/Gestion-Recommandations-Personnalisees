from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from .models import ModeleBulletin, ModeleBulletinMatiere
from accounts.views import prefet_required
from grades.models import Note
from students.models import Student
from subjects.models import Matiere
from classes.models import Classe, AnneeScolaire
from decimal import Decimal


@login_required
def bulletin_list(request):
    bulletins = ModeleBulletin.objects.select_related('classe', 'classe__section', 'annee_scolaire')
    return render(request, 'bulletin/bulletin_list.html', {'bulletins': bulletins})


@login_required
@prefet_required
def bulletin_create(request):
    annee = AnneeScolaire.objects.filter(active=True).first()
    classes = Classe.objects.filter(annee_scolaire=annee).select_related('section') if annee else []
    matieres_20 = Matiere.objects.filter(maxima=20)
    matieres_30 = Matiere.objects.filter(maxima=30)
    matieres_60 = Matiere.objects.filter(maxima=60)
    all_matieres = list(matieres_20) + list(matieres_30) + list(matieres_60)

    if request.method == 'POST':
        classe_id = request.POST.get('classe')
        annee_id = request.POST.get('annee_scolaire')
        if not classe_id or not annee_id:
            messages.error(request, "Veuillez sélectionner une classe et une année scolaire.")
        else:
            classe = get_object_or_404(Classe, pk=classe_id)
            annee_obj = get_object_or_404(AnneeScolaire, pk=annee_id)
            modele, created = ModeleBulletin.objects.get_or_create(
                classe=classe, annee_scolaire=annee_obj
            )
            modele.matieres.all().delete()
            ordre = 0
            for m in all_matieres:
                if request.POST.get(f'mat_{m.pk}'):
                    ModeleBulletinMatiere.objects.create(modele=modele, matiere=m, ordre=ordre)
                    ordre += 1
            messages.success(request, f"Modèle de bulletin {'créé' if created else 'mis à jour'} pour {classe}.")
            return redirect('bulletin_list')

    return render(request, 'bulletin/bulletin_form.html', {
        'classes': classes,
        'annees': AnneeScolaire.objects.all(),
        'annee': annee,
        'titre': 'Créer un modèle de bulletin',
        'matieres_20': matieres_20,
        'matieres_30': matieres_30,
        'matieres_60': matieres_60,
        'selected_ids': set(),
    })


@login_required
@prefet_required
def bulletin_update(request, pk):
    modele = get_object_or_404(ModeleBulletin, pk=pk)
    annee = AnneeScolaire.objects.filter(active=True).first()
    classes = Classe.objects.filter(annee_scolaire=annee).select_related('section') if annee else []
    matieres_20 = Matiere.objects.filter(maxima=20)
    matieres_30 = Matiere.objects.filter(maxima=30)
    matieres_60 = Matiere.objects.filter(maxima=60)
    all_matieres = list(matieres_20) + list(matieres_30) + list(matieres_60)

    if request.method == 'POST':
        modele.matieres.all().delete()
        ordre = 0
        for m in all_matieres:
            if request.POST.get(f'mat_{m.pk}'):
                ModeleBulletinMatiere.objects.create(modele=modele, matiere=m, ordre=ordre)
                ordre += 1
        messages.success(request, "Modèle mis à jour.")
        return redirect('bulletin_list')

    selected_ids = set(modele.matieres.values_list('matiere_id', flat=True))
    return render(request, 'bulletin/bulletin_form.html', {
        'classes': classes,
        'annees': AnneeScolaire.objects.all(),
        'annee': annee,
        'titre': 'Modifier le modèle de bulletin',
        'obj': modele,
        'matieres_20': matieres_20,
        'matieres_30': matieres_30,
        'matieres_60': matieres_60,
        'selected_ids': selected_ids,
    })


@login_required
@prefet_required
def bulletin_delete(request, pk):
    modele = get_object_or_404(ModeleBulletin, pk=pk)
    if request.method == 'POST':
        modele.delete()
        messages.success(request, "Modèle supprimé.")
        return redirect('bulletin_list')
    return render(request, 'bulletin/bulletin_confirm_delete.html', {'obj': modele})


@login_required
@prefet_required
def bulletin_publish(request, pk):
    modele = get_object_or_404(ModeleBulletin, pk=pk)
    if request.method == 'POST':
        modele.publie = True
        modele.date_publication = timezone.now()
        modele.save()
        messages.success(request, f"Résultats publiés pour {modele.classe}.")
    return redirect('bulletin_list')


@login_required
def bulletin_eleve(request, pk, eleve_pk):
    modele = get_object_or_404(ModeleBulletin, pk=pk)
    eleve = get_object_or_404(Student, pk=eleve_pk)
    periodes = ['1P', '2P', 'EXAM1', '3P', '4P', 'EXAM2', 'REPECHAGE']
    matieres_data = []
    total_obtenu = Decimal('0')
    total_max_tg = Decimal('0')

    for bm in modele.matieres.select_related('matiere').order_by('matiere__maxima', 'ordre'):
        mat = bm.matiere
        notes_dict = {}
        try:
            mc = mat.affectations.get(classe=modele.classe)
            for p in periodes:
                try:
                    n = Note.objects.get(eleve=eleve, matiere_classe=mc, periode=p)
                    notes_dict[p] = n.valeur
                except Note.DoesNotExist:
                    notes_dict[p] = None
        except Exception:
            for p in periodes:
                notes_dict[p] = None

        mx = mat.maxima
        n1p = notes_dict.get('1P') or Decimal('0')
        n2p = notes_dict.get('2P') or Decimal('0')
        nexam1 = notes_dict.get('EXAM1') or Decimal('0')
        n3p = notes_dict.get('3P') or Decimal('0')
        n4p = notes_dict.get('4P') or Decimal('0')
        nexam2 = notes_dict.get('EXAM2') or Decimal('0')

        tot_s1 = n1p + n2p + nexam1
        tot_s2 = n3p + n4p + nexam2
        tg = tot_s1 + tot_s2
        max_tg = Decimal(mx) * 8

        total_obtenu += tg
        total_max_tg += max_tg

        matieres_data.append({
            'matiere': mat,
            'maxima': mx,
            'n1p': notes_dict.get('1P'), 'n2p': notes_dict.get('2P'),
            'nexam1': notes_dict.get('EXAM1'), 'tot_s1': tot_s1,
            'n3p': notes_dict.get('3P'), 'n4p': notes_dict.get('4P'),
            'nexam2': notes_dict.get('EXAM2'), 'tot_s2': tot_s2,
            'tg': tg,
            'repechage': notes_dict.get('REPECHAGE'),
        })

    pourcentage = round(float(total_obtenu) / float(total_max_tg) * 100, 2) if total_max_tg > 0 else 0
    classement = _get_classement(modele, eleve, total_obtenu)
    nb_eleves = eleve.classe.eleves.count() if eleve.classe else 0

    return render(request, 'bulletin/bulletin_eleve.html', {
        'modele': modele, 'eleve': eleve,
        'matieres_data': matieres_data,
        'total_obtenu': total_obtenu,
        'total_max': total_max_tg,
        'pourcentage': pourcentage,
        'classement': classement,
        'nb_eleves': nb_eleves,
    })


def _get_classement(modele, eleve, my_score):
    scores = []
    eleves = Student.objects.filter(classe=modele.classe)
    for e in eleves:
        total = Note.objects.filter(
            eleve=e, matiere_classe__classe=modele.classe
        ).exclude(periode='REPECHAGE').aggregate(
            total=__import__('django.db.models', fromlist=['Sum']).Sum('valeur')
        )['total'] or Decimal('0')
        scores.append(total)
    scores.sort(reverse=True)
    try:
        return scores.index(my_score) + 1
    except ValueError:
        return '-'


@login_required
def bulletin_classe(request, pk):
    modele = get_object_or_404(ModeleBulletin, pk=pk)
    eleves = Student.objects.filter(classe=modele.classe).order_by('nom', 'postnom')
    return render(request, 'bulletin/bulletin_classe.html', {
        'modele': modele, 'eleves': eleves
    })
