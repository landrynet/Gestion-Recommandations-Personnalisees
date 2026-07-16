from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from students.models import Student
from teachers.models import Teacher
from bulletin.models import ModeleBulletin
from grades.models import Note
from classes.models import Classe, AnneeScolaire
from accounts.views import prefet_required
from decimal import Decimal


@login_required
@prefet_required
def rapport_eleves(request):
    annee = AnneeScolaire.objects.filter(active=True).first()
    classe_id = request.GET.get('classe', '')
    students = Student.objects.select_related('classe', 'classe__section')
    if classe_id:
        students = students.filter(classe_id=classe_id)
    classes = Classe.objects.filter(annee_scolaire=annee).select_related('section') if annee else []
    return render(request, 'reports/rapport_eleves.html', {
        'students': students, 'classes': classes, 'classe_id': classe_id, 'annee': annee
    })


@login_required
@prefet_required
def rapport_enseignants(request):
    teachers = Teacher.objects.select_related('user').prefetch_related(
        'matieres_enseignees', 'matieres_enseignees__matiere', 'matieres_enseignees__classe'
    )
    return render(request, 'reports/rapport_enseignants.html', {'teachers': teachers})


@login_required
@prefet_required
def rapport_resultats(request):
    modele_id = request.GET.get('modele', '')
    bulletins = ModeleBulletin.objects.select_related('classe', 'classe__section', 'annee_scolaire')
    resultats = []

    if modele_id:
        modele = get_object_or_404(ModeleBulletin, pk=modele_id)
        eleves = Student.objects.filter(classe=modele.classe).order_by('nom')
        for eleve in eleves:
            total = Note.objects.filter(
                eleve=eleve,
                matiere_classe__classe=modele.classe
            ).exclude(periode='REPECHAGE').aggregate(
                total=__import__('django.db.models', fromlist=['Sum']).Sum('valeur')
            )['total'] or 0

            max_total = sum(
                bm.matiere.maxima * 8
                for bm in modele.matieres.select_related('matiere')
            )
            pct = round(float(total) / float(max_total) * 100, 2) if max_total else 0
            resultats.append({
                'eleve': eleve, 'total': total, 'max': max_total, 'pourcentage': pct,
                'mention': _mention(pct)
            })
        resultats.sort(key=lambda x: x['total'], reverse=True)
        for i, r in enumerate(resultats):
            r['rang'] = i + 1

    return render(request, 'reports/rapport_resultats.html', {
        'bulletins': bulletins, 'modele_id': modele_id, 'resultats': resultats
    })


def _mention(pct):
    if pct >= 80:
        return "Grande distinction"
    elif pct >= 70:
        return "Distinction"
    elif pct >= 60:
        return "Satisfaction"
    elif pct >= 50:
        return "Réussite"
    else:
        return "Échec"
