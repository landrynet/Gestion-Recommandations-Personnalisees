from django.db import models


class Matiere(models.Model):
    MAXIMA_CHOICES = [
        (20, 'MAXIMA 20'),
        (30, 'MAXIMA 30'),
        (60, 'MAXIMA 60'),
    ]
    nom = models.CharField(max_length=100, unique=True)
    maxima = models.IntegerField(choices=MAXIMA_CHOICES, default=20)

    class Meta:
        ordering = ['maxima', 'nom']
        verbose_name = "Matière"
        verbose_name_plural = "Matières"

    def __str__(self):
        return self.nom

    @property
    def maxima_label(self):
        return f"MAXIMA {self.maxima}"


class MatiereClasse(models.Model):
    matiere = models.ForeignKey(Matiere, on_delete=models.CASCADE, related_name='affectations')
    classe = models.ForeignKey('classes.Classe', on_delete=models.CASCADE, related_name='matieres')
    enseignant = models.ForeignKey(
        'teachers.Teacher',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='matieres_enseignees'
    )

    class Meta:
        unique_together = ['matiere', 'classe']
        ordering = ['matiere__maxima', 'matiere__nom']
        verbose_name = "Affectation matière-classe"

    def __str__(self):
        return f"{self.matiere} → {self.classe}"
