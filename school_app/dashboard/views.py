from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from students.models import Student
from teachers.models import Teacher
from classes.models import Classe, AnneeScolaire
from subjects.models import Matiere
from bulletin.models import ModeleBulletin


@login_required
def dashboard(request):
    annee_active = AnneeScolaire.objects.filter(active=True).first()
    context = {
        'nb_eleves': Student.objects.count(),
        'nb_enseignants': Teacher.objects.count(),
        'nb_classes': Classe.objects.filter(annee_scolaire=annee_active).count() if annee_active else 0,
        'nb_matieres': Matiere.objects.count(),
        'nb_bulletins': ModeleBulletin.objects.count(),
        'annee_active': annee_active,
        'dernieres_classes': Classe.objects.filter(annee_scolaire=annee_active).select_related('section')[:5] if annee_active else [],
        'derniers_eleves': Student.objects.select_related('classe', 'classe__section').order_by('-date_inscription')[:5],
    }
    return render(request, 'dashboard/index.html', context)
