from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import AnneeScolaire, Section, Classe
from .forms import AnneeScolaireForm, SectionForm, ClasseForm
from accounts.views import prefet_required


# ─── Année Scolaire ───────────────────────────────────────────────────────────

@login_required
@prefet_required
def annee_list(request):
    annees = AnneeScolaire.objects.all()
    return render(request, 'classes/annee_list.html', {'annees': annees})


@login_required
@prefet_required
def annee_create(request):
    form = AnneeScolaireForm(request.POST or None)
    if form.is_valid():
        form.save()
        messages.success(request, "Année scolaire créée.")
        return redirect('annee_list')
    return render(request, 'classes/annee_form.html', {'form': form, 'titre': "Ajouter une année scolaire"})


@login_required
@prefet_required
def annee_update(request, pk):
    annee = get_object_or_404(AnneeScolaire, pk=pk)
    form = AnneeScolaireForm(request.POST or None, instance=annee)
    if form.is_valid():
        form.save()
        messages.success(request, "Année scolaire modifiée.")
        return redirect('annee_list')
    return render(request, 'classes/annee_form.html', {'form': form, 'titre': "Modifier l'année scolaire", 'obj': annee})


@login_required
@prefet_required
def annee_delete(request, pk):
    annee = get_object_or_404(AnneeScolaire, pk=pk)
    if request.method == 'POST':
        annee.delete()
        messages.success(request, "Année scolaire supprimée.")
        return redirect('annee_list')
    return render(request, 'classes/confirm_delete.html', {'obj': annee, 'type': 'année scolaire'})


# ─── Section ──────────────────────────────────────────────────────────────────

@login_required
@prefet_required
def section_list(request):
    sections = Section.objects.all()
    return render(request, 'classes/section_list.html', {'sections': sections})


@login_required
@prefet_required
def section_create(request):
    form = SectionForm(request.POST or None)
    if form.is_valid():
        form.save()
        messages.success(request, "Section créée.")
        return redirect('section_list')
    return render(request, 'classes/section_form.html', {'form': form, 'titre': 'Ajouter une section'})


@login_required
@prefet_required
def section_update(request, pk):
    section = get_object_or_404(Section, pk=pk)
    form = SectionForm(request.POST or None, instance=section)
    if form.is_valid():
        form.save()
        messages.success(request, "Section modifiée.")
        return redirect('section_list')
    return render(request, 'classes/section_form.html', {'form': form, 'titre': 'Modifier la section', 'obj': section})


@login_required
@prefet_required
def section_delete(request, pk):
    section = get_object_or_404(Section, pk=pk)
    if request.method == 'POST':
        section.delete()
        messages.success(request, "Section supprimée.")
        return redirect('section_list')
    return render(request, 'classes/confirm_delete.html', {'obj': section, 'type': 'section'})


# ─── Classe ───────────────────────────────────────────────────────────────────

@login_required
def classe_list(request):
    annee = AnneeScolaire.objects.filter(active=True).first()
    annee_id = request.GET.get('annee', annee.pk if annee else None)
    classes = Classe.objects.select_related('section', 'annee_scolaire')
    if annee_id:
        classes = classes.filter(annee_scolaire_id=annee_id)
    annees = AnneeScolaire.objects.all()
    return render(request, 'classes/classe_list.html', {
        'classes': classes, 'annees': annees, 'annee_id': str(annee_id) if annee_id else ''
    })


@login_required
@prefet_required
def classe_create(request):
    form = ClasseForm(request.POST or None)
    if form.is_valid():
        form.save()
        messages.success(request, "Classe créée.")
        return redirect('classe_list')
    return render(request, 'classes/classe_form.html', {'form': form, 'titre': 'Créer une classe'})


@login_required
@prefet_required
def classe_update(request, pk):
    classe = get_object_or_404(Classe, pk=pk)
    form = ClasseForm(request.POST or None, instance=classe)
    if form.is_valid():
        form.save()
        messages.success(request, "Classe modifiée.")
        return redirect('classe_list')
    return render(request, 'classes/classe_form.html', {'form': form, 'titre': 'Modifier la classe', 'obj': classe})


@login_required
@prefet_required
def classe_delete(request, pk):
    classe = get_object_or_404(Classe, pk=pk)
    if request.method == 'POST':
        classe.delete()
        messages.success(request, "Classe supprimée.")
        return redirect('classe_list')
    return render(request, 'classes/confirm_delete.html', {'obj': classe, 'type': 'classe'})
