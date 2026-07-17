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
    """Saisie des notes — enseignant (ses classes), préfet interdit ici."""
    user = request.user

    # Préfet n'a pas à saisir les notes directement
    if user.is_prefet():
        messages.info(request, "La saisie des notes est réservée aux enseignants. Utilisez 'Consulter les notes' pour vérifier.")
        return redirect('consulter_notes')

    periodes = [
        ('1P',       '1ère Période'),
        ('2P',       '2ème Période'),
        ('EXAM1',    'Examen S1'),
        ('3P',       '3ème Période'),
        ('4P',       '4ème Période'),
        ('EXAM2',    'Examen S2'),
        ('REPECHAGE','Repêchage'),
    ]

    # L'enseignant ne voit que ses affectations
    try:
        teacher = user.teacher_profile
        matieres_classes = MatiereClasse.objects.filter(
            enseignant=teacher
        ).select_related('matiere', 'classe', 'classe__section')
    except Exception:
        matieres_classes = MatiereClasse.objects.none()

    mc_id   = request.GET.get('mc', '')
    periode = request.GET.get('periode', '1P')
    matiere_classe = None
    eleves = []
    form   = None

    if mc_id:
        matiere_classe = get_object_or_404(MatiereClasse, pk=mc_id)

        # Sécurité : l'enseignant ne peut saisir que ses propres affectations
        try:
            if matiere_classe.enseignant != user.teacher_profile:
                messages.error(request, "Vous ne pouvez modifier que les notes de vos propres matières.")
                return redirect('saisie_notes')
        except Exception:
            messages.error(request, "Profil enseignant introuvable.")
            return redirect('dashboard')

        eleves = Student.objects.filter(classe=matiere_classe.classe).order_by('nom', 'postnom')

        if request.method == 'POST':
            form = NoteForm(request.POST, eleves=eleves, matiere_classe=matiere_classe, periode=periode)
            if form.is_valid():
                form.save()
                messages.success(request, f"Notes enregistrées — {matiere_classe.matiere} / {periode}.")
                return redirect(f'/notes/?mc={mc_id}&periode={periode}')
        else:
            form = NoteForm(eleves=eleves, matiere_classe=matiere_classe, periode=periode)

    return render(request, 'grades/saisie_notes.html', {
        'matieres_classes': matieres_classes,
        'mc_id':            mc_id,
        'periodes':         periodes,
        'periode':          periode,
        'matiere_classe':   matiere_classe,
        'eleves':           eleves,
        'form':             form,
    })


@login_required
def consulter_notes(request):
    """Consultation des notes — préfet voit tout, enseignant voit ses classes."""
    user = request.user
    periodes = [
        ('1P', '1ère P'), ('2P', '2ème P'), ('EXAM1', 'Exam S1'),
        ('3P', '3ème P'), ('4P', '4ème P'), ('EXAM2', 'Exam S2'),
        ('REPECHAGE', 'Repêchage'),
    ]

    if user.is_prefet():
        classes = Classe.objects.select_related('section', 'annee_scolaire')
    else:
        try:
            teacher = user.teacher_profile
            mc_qs   = MatiereClasse.objects.filter(enseignant=teacher).values_list('classe_id', flat=True)
            classes = Classe.objects.filter(pk__in=mc_qs).select_related('section')
        except Exception:
            classes = Classe.objects.none()

    classe_id      = request.GET.get('classe', '')
    mc_id          = request.GET.get('mc', '')
    matieres_classes = []
    eleves_notes   = []
    selected_mc    = None
    periode_filter = request.GET.get('periode', '')

    if classe_id:
        if user.is_prefet():
            matieres_classes = MatiereClasse.objects.filter(
                classe_id=classe_id
            ).select_related('matiere', 'enseignant', 'enseignant__user').order_by('matiere__maxima', 'matiere__nom')
        else:
            try:
                matieres_classes = MatiereClasse.objects.filter(
                    classe_id=classe_id, enseignant=user.teacher_profile
                ).select_related('matiere', 'enseignant', 'enseignant__user')
            except Exception:
                matieres_classes = []

    if mc_id:
        selected_mc = get_object_or_404(MatiereClasse, pk=mc_id)
        eleves = Student.objects.filter(classe=selected_mc.classe).order_by('nom', 'postnom')
        for eleve in eleves:
            row = {'eleve': eleve, 'notes': {}}
            for code, label in periodes:
                try:
                    n = Note.objects.get(eleve=eleve, matiere_classe=selected_mc, periode=code)
                    row['notes'][code] = n.valeur
                except Note.DoesNotExist:
                    row['notes'][code] = None
            eleves_notes.append(row)

    return render(request, 'grades/consulter_notes.html', {
        'classes':          classes,
        'classe_id':        classe_id,
        'mc_id':            mc_id,
        'matieres_classes': matieres_classes,
        'selected_mc':      selected_mc,
        'eleves_notes':     eleves_notes,
        'periodes':         periodes,
    })
