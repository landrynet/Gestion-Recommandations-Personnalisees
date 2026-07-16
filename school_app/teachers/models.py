from django.db import models
from accounts.models import CustomUser


class Teacher(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='teacher_profile')
    telephone = models.CharField(max_length=20, blank=True)

    class Meta:
        ordering = ['user__last_name', 'user__first_name']
        verbose_name = "Enseignant"
        verbose_name_plural = "Enseignants"

    def __str__(self):
        return self.nom_complet

    @property
    def nom_complet(self):
        return self.user.get_full_name() or self.user.username

    @property
    def email(self):
        return self.user.email

    @property
    def classes_enseignees(self):
        from subjects.models import MatiereClasse
        return MatiereClasse.objects.filter(enseignant=self).select_related('classe', 'matiere')
