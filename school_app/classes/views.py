from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from django.db import transaction
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


@login_required
@prefet_required
def annee_activer(request, pk):
    """Rendre une année active (désactive toutes les autres)."""
    annee = get_object_or_404(AnneeScolaire, pk=pk)
    if request.method == 'POST':
        annee.active = True
        annee.save()  # Le modèle désactive les autres automatiquement
        messages.success(request, f"Année {annee} activée avec succès.")
    return redirect('annee_list')


@login_required
@prefet_required
def reconduire_annee(request, pk):
    """
    Reconduction d'une année scolaire vers une nouvelle :
    - Recopie les classes (même nom/section, nouvelle année)
    - Recopie les affectations matières/enseignants par classe
    - Déplace les élèves vers leurs nouvelles classes
    - Notes et bulletins : fresh start (ne sont pas copiés)
    """
    source_annee = get_object_or_404(AnneeScolaire, pk=pk)
    toutes_annees = AnneeScolaire.objects.exclude(pk=pk).order_by('-annee')

    # Préparer l'aperçu des données de la source
    classes_source = Classe.objects.filter(
        annee_scolaire=source_annee
    ).select_related('section').prefetch_related('matieres__matiere', 'matieres__enseignant', 'eleves')

    apercu = []
    for c in classes_source:
        apercu.append({
            'classe': c,
            'nb_matieres': c.matieres.count(),
            'nb_eleves': c.eleves.count(),
        })

    if request.method == 'POST':
        nouvelle_annee_str = request.POST.get('nouvelle_annee', '').strip()
        target_pk = request.POST.get('annee_existante', '')
        copier_matieres = request.POST.get('copier_matieres') == '1'
        copier_eleves = request.POST.get('copier_eleves') == '1'
        activer = request.POST.get('activer_nouvelle') == '1'

        # ── Obtenir ou créer la nouvelle année ──
        if target_pk:
            target_annee = get_object_or_404(AnneeScolaire, pk=target_pk)
        elif nouvelle_annee_str:
            if AnneeScolaire.objects.filter(annee=nouvelle_annee_str).exists():
                messages.error(request, f"L'année «{nouvelle_annee_str}» existe déjà. Sélectionnez-la dans la liste.")
                return redirect(request.path)
            target_annee = AnneeScolaire.objects.create(annee=nouvelle_annee_str, active=False)
        else:
            messages.error(request, "Indiquez une nouvelle année scolaire.")
            return redirect(request.path)

        stats = {'classes': 0, 'matieres': 0, 'eleves': 0, 'ignorees': 0}

        try:
            with transaction.atomic():
                # ── Reconduire chaque classe ──
                for c in classes_source:
                    # Créer la classe dans la nouvelle année (skip si existe déjà)
                    new_classe, created = Classe.objects.get_or_create(
                        nom=c.nom,
                        section=c.section,
                        annee_scolaire=target_annee,
                    )
                    if created:
                        stats['classes'] += 1
                    else:
                        stats['ignorees'] += 1

                    if copier_matieres:
                        # Copier les affectations matières/enseignants
                        from subjects.models import MatiereClasse
                        for mc in c.matieres.select_related('matiere', 'enseignant'):
                            _, mc_created = MatiereClasse.objects.get_or_create(
                                matiere=mc.matiere,
                                classe=new_classe,
                                defaults={'enseignant': mc.enseignant}
                            )
                            if mc_created:
                                stats['matieres'] += 1

                    if copier_eleves:
                        # Déplacer les élèves vers la nouvelle classe
                        for eleve in c.eleves.all():
                            eleve.classe = new_classe
                            eleve.save(update_fields=['classe'])
                            stats['eleves'] += 1

                # ── Activer la nouvelle année si demandé ──
                if activer:
                    target_annee.active = True
                    target_annee.save()

        except Exception as e:
            messages.error(request, f"Erreur lors de la reconduction : {e}")
            return redirect(request.path)

        msg_parts = [f"{stats['classes']} classe(s) créée(s)"]
        if copier_matieres:
            msg_parts.append(f"{stats['matieres']} affectation(s) matières copiée(s)")
        if copier_eleves:
            msg_parts.append(f"{stats['eleves']} élève(s) déplacé(s)")
        if stats['ignorees']:
            msg_parts.append(f"{stats['ignorees']} classe(s) déjà existante(s) ignorée(s)")

        messages.success(
            request,
            f"✅ Reconduction vers {target_annee} terminée : {', '.join(msg_parts)}. "
            f"Les notes et bulletins repartent de zéro pour la nouvelle année."
        )
        return redirect('annee_list')

    # Suggestion automatique de la prochaine année
    suggestion = _suggerer_prochaine_annee(source_annee.annee)

    return render(request, 'classes/reconduire_annee.html', {
        'source_annee': source_annee,
        'toutes_annees': toutes_annees,
        'apercu': apercu,
        'suggestion': suggestion,
    })


def _suggerer_prochaine_annee(annee_str):
    """À partir de '2024-2025' suggère '2025-2026'."""
    try:
        debut, fin = annee_str.split('-')
        return f"{int(debut)+1}-{int(fin)+1}"
    except Exception:
        return ""


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
    annee    = AnneeScolaire.objects.filter(active=True).first()
    annee_id = request.GET.get('annee', annee.pk if annee else None)
    classes  = Classe.objects.select_related('section', 'annee_scolaire')
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
