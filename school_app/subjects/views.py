from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Matiere, MatiereClasse
from .forms import MatiereForm, MatiereClasseForm
from accounts.views import prefet_required


@login_required
@prefet_required
def matiere_list(request):
    matieres = Matiere.objects.all()
    return render(request, 'subjects/matiere_list.html', {'matieres': matieres})


@login_required
@prefet_required
def matiere_create(request):
    form = MatiereForm(request.POST or None)
    if form.is_valid():
        form.save()
        messages.success(request, "Matière créée.")
        return redirect('matiere_list')
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


# ─── Affectations ─────────────────────────────────────────────────────────────

@login_required
@prefet_required
def affectation_list(request):
    affectations = MatiereClasse.objects.select_related('matiere', 'classe', 'classe__section', 'enseignant', 'enseignant__user')
    from classes.models import Classe, AnneeScolaire
    annee = AnneeScolaire.objects.filter(active=True).first()
    classe_id = request.GET.get('classe', '')
    if classe_id:
        affectations = affectations.filter(classe_id=classe_id)
    classes = Classe.objects.filter(annee_scolaire=annee).select_related('section') if annee else []
    return render(request, 'subjects/affectation_list.html', {
        'affectations': affectations, 'classes': classes, 'classe_id': classe_id
    })


@login_required
@prefet_required
def affectation_create(request):
    form = MatiereClasseForm(request.POST or None)
    if form.is_valid():
        form.save()
        messages.success(request, "Affectation créée.")
        return redirect('affectation_list')
    return render(request, 'subjects/affectation_form.html', {'form': form, 'titre': 'Affecter une matière'})


@login_required
@prefet_required
def affectation_update(request, pk):
    aff = get_object_or_404(MatiereClasse, pk=pk)
    form = MatiereClasseForm(request.POST or None, instance=aff)
    if form.is_valid():
        form.save()
        messages.success(request, "Affectation modifiée.")
        return redirect('affectation_list')
    return render(request, 'subjects/affectation_form.html', {'form': form, 'titre': "Modifier l'affectation", 'obj': aff})


@login_required
@prefet_required
def affectation_delete(request, pk):
    aff = get_object_or_404(MatiereClasse, pk=pk)
    if request.method == 'POST':
        aff.delete()
        messages.success(request, "Affectation supprimée.")
        return redirect('affectation_list')
    return render(request, 'subjects/affectation_confirm_delete.html', {'obj': aff})
