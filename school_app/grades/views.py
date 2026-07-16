from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Note
from .forms import NoteForm
from subjects.models import MatiereClasse
from students.models import Student
from classes.models import Classe


@login_required
def saisie_notes(request):
    user = request.user
    periodes = [
        ('1P', '1ère Période'), ('2P', '2ème Période'), ('EXAM1', 'Examen S1'),
        ('3P', '3ème Période'), ('4P', '4ème Période'), ('EXAM2', 'Examen S2'),
        ('REPECHAGE', 'Repêchage'),
    ]

    if user.is_prefet():
        # Le préfet peut choisir n'importe quelle affectation
        matieres_classes = MatiereClasse.objects.select_related(
            'matiere', 'classe', 'classe__section', 'enseignant', 'enseignant__user'
        )
    else:
        # L'enseignant ne voit que ses affectations
        try:
            teacher = user.teacher_profile
            matieres_classes = MatiereClasse.objects.filter(
                enseignant=teacher
            ).select_related('matiere', 'classe', 'classe__section')
        except Exception:
            matieres_classes = MatiereClasse.objects.none()

    mc_id = request.GET.get('mc', '')
    periode = request.GET.get('periode', '1P')
    matiere_classe = None
    eleves = []
    form = None

    if mc_id:
        matiere_classe = get_object_or_404(MatiereClasse, pk=mc_id)
        eleves = Student.objects.filter(classe=matiere_classe.classe).order_by('nom', 'postnom')

        if request.method == 'POST':
            form = NoteForm(request.POST, eleves=eleves, matiere_classe=matiere_classe, periode=periode)
            if form.is_valid():
                form.save()
                messages.success(request, f"Notes enregistrées pour la {periode}.")
                return redirect(f'/notes/?mc={mc_id}&periode={periode}')
        else:
            form = NoteForm(eleves=eleves, matiere_classe=matiere_classe, periode=periode)

    return render(request, 'grades/saisie_notes.html', {
        'matieres_classes': matieres_classes,
        'mc_id': mc_id,
        'periodes': periodes,
        'periode': periode,
        'matiere_classe': matiere_classe,
        'eleves': eleves,
        'form': form,
    })


@login_required
def consulter_notes(request):
    """Vue de consultation des notes par classe et matière."""
    user = request.user
    if user.is_prefet():
        classes = Classe.objects.select_related('section', 'annee_scolaire')
    else:
        try:
            teacher = user.teacher_profile
            mc_qs = MatiereClasse.objects.filter(enseignant=teacher).values_list('classe_id', flat=True)
            classes = Classe.objects.filter(pk__in=mc_qs).select_related('section')
        except Exception:
            classes = Classe.objects.none()

    classe_id = request.GET.get('classe', '')
    matieres_classes = []
    if classe_id:
        matieres_classes = MatiereClasse.objects.filter(
            classe_id=classe_id
        ).select_related('matiere', 'enseignant', 'enseignant__user')

    return render(request, 'grades/consulter_notes.html', {
        'classes': classes, 'classe_id': classe_id, 'matieres_classes': matieres_classes
    })
