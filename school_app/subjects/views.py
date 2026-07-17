from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from .models import Matiere, MatiereClasse
from .forms import MatiereForm, MatiereClasseForm
from accounts.views import prefet_required
from classes.models import Classe, AnneeScolaire


@login_required
@prefet_required
def matiere_list(request):
    """Liste globale des matières + affectations par classe pour l'année active."""
    annee = AnneeScolaire.objects.filter(active=True).first()
    matieres = Matiere.objects.prefetch_related('affectations__classe__section')

    matieres_20 = matieres.filter(maxima=20)
    matieres_30 = matieres.filter(maxima=30)
    matieres_60 = matieres.filter(maxima=60)

    classes = (
        Classe.objects.filter(annee_scolaire=annee)
            .select_related('section')
            .prefetch_related('matieres__matiere')
        if annee else []
    )

    return render(request, 'subjects/matiere_list.html', {
        'matieres_20': matieres_20,
        'matieres_30': matieres_30,
        'matieres_60': matieres_60,
        'classes': classes,
        'annee': annee,
        'total': matieres.count(),
    })


@login_required
@prefet_required
def matiere_create(request):
    form = MatiereForm(request.POST or None)
    if form.is_valid():
        matiere = form.save()
        messages.success(request, f"Matière « {matiere.nom} » créée. Pensez à l'affecter aux classes concernées.")
        return redirect('affectation_list')
    return render(request, 'subjects/matiere_form.html', {'form': form, 'titre': 'Ajouter une matière'})


@login_required
@prefet_required
def matiere_update(request, pk):
    matiere = get_object_or_404(Matiere, pk=pk)
    form = MatiereForm(request.POST or None, instance=matiere)
    if form.is_valid():
        form.save()
        messages.success(request, "Matière modifiée.")
        return redirect('matiere_list')
    return render(request, 'subjects/matiere_form.html', {'form': form, 'titre': 'Modifier la matière', 'obj': matiere})


@login_required
@prefet_required
def matiere_delete(request, pk):
    matiere = get_object_or_404(Matiere, pk=pk)
    if request.method == 'POST':
        matiere.delete()
        messages.success(request, "Matière supprimée.")
        return redirect('matiere_list')
    return render(request, 'subjects/matiere_confirm_delete.html', {'obj': matiere})


# ─── Affectations (vue centrée sur la classe) ──────────────────────────────────

@login_required
@prefet_required
def affectation_list(request):
    """Vue centrée sur la classe : choisir une classe, voir/gérer ses matières."""
    annee = AnneeScolaire.objects.filter(active=True).first()
    classes = (
        Classe.objects.filter(annee_scolaire=annee).select_related('section')
        if annee else Classe.objects.select_related('section')
    )
    classe_id = request.GET.get('classe', '')
    selected_classe = None
    affectations = MatiereClasse.objects.none()
    matieres_non_20 = matieres_non_30 = matieres_non_60 = Matiere.objects.none()

    if classe_id:
        selected_classe = get_object_or_404(Classe, pk=classe_id)
        affectations = MatiereClasse.objects.filter(
            classe=selected_classe
        ).select_related('matiere', 'enseignant', 'enseignant__user').order_by('matiere__maxima', 'matiere__nom')

        affectees_ids = affectations.values_list('matiere_id', flat=True)
        matieres_non_20 = Matiere.objects.filter(maxima=20).exclude(pk__in=affectees_ids)
        matieres_non_30 = Matiere.objects.filter(maxima=30).exclude(pk__in=affectees_ids)
        matieres_non_60 = Matiere.objects.filter(maxima=60).exclude(pk__in=affectees_ids)

    return render(request, 'subjects/affectation_list.html', {
        'classes':          classes,
        'classe_id':        classe_id,
        'selected_classe':  selected_classe,
        'affectations':     affectations,
        'matieres_non_20':  matieres_non_20,
        'matieres_non_30':  matieres_non_30,
        'matieres_non_60':  matieres_non_60,
        'annee':            annee,
    })


@login_required
@prefet_required
def affectation_create(request):
    """Affecter une matière à une classe (+ enseignant optionnel)."""
    classe_id = request.GET.get('classe') or request.POST.get('classe_prefill')
    form = MatiereClasseForm(request.POST or None)

    if classe_id and request.method == 'GET':
        try:
            classe = Classe.objects.get(pk=classe_id)
            form.initial = {'classe': classe}
        except Classe.DoesNotExist:
            pass

    if form.is_valid():
        aff = form.save()
        messages.success(request, f"Matière « {aff.matiere} » affectée à {aff.classe}.")
        return redirect(reverse('affectation_list') + f'?classe={aff.classe.pk}')

    return render(request, 'subjects/affectation_form.html', {
        'form': form,
        'titre': 'Affecter une matière à une classe',
        'classe_prefill': classe_id,
    })


@login_required
@prefet_required
def affectation_rapide(request):
    """Affectation rapide depuis le panneau classe : cocher les matières voulues."""
    if request.method != 'POST':
        return redirect('affectation_list')

    classe_id = request.POST.get('classe_id')
    selected_classe = get_object_or_404(Classe, pk=classe_id)
    matieres_ids = request.POST.getlist('matieres')

    added = 0
    for mid in matieres_ids:
        m = get_object_or_404(Matiere, pk=mid)
        _, created = MatiereClasse.objects.get_or_create(matiere=m, classe=selected_classe)
        if created:
            added += 1

    if added:
        messages.success(request, f"{added} matière(s) ajoutée(s) à {selected_classe}.")
    else:
        messages.info(request, "Aucune nouvelle matière ajoutée (déjà toutes affectées).")
    return redirect(reverse('affectation_list') + f'?classe={classe_id}')


@login_required
@prefet_required
def affectation_update(request, pk):
    aff = get_object_or_404(MatiereClasse, pk=pk)
    form = MatiereClasseForm(request.POST or None, instance=aff)
    if form.is_valid():
        form.save()
        messages.success(request, "Affectation modifiée.")
        return redirect(reverse('affectation_list') + f'?classe={aff.classe.pk}')
    return render(request, 'subjects/affectation_form.html', {
        'form': form,
        'titre': "Modifier l'affectation",
        'obj': aff,
    })


@login_required
@prefet_required
def affectation_delete(request, pk):
    aff = get_object_or_404(MatiereClasse, pk=pk)
    classe_pk = aff.classe.pk
    if request.method == 'POST':
        aff.delete()
        messages.success(request, "Matière retirée de la classe.")
        return redirect(reverse('affectation_list') + f'?classe={classe_pk}')
    return render(request, 'subjects/affectation_confirm_delete.html', {'obj': aff})
