from django.db import models


class AnneeScolaire(models.Model):
    annee = models.CharField(max_length=9, unique=True)  # ex: 2024-2025
    active = models.BooleanField(default=False)

    class Meta:
        ordering = ['-annee']
        verbose_name = "Année scolaire"
        verbose_name_plural = "Années scolaires"

    def __str__(self):
        return self.annee

    def save(self, *args, **kwargs):
        if self.active:
            AnneeScolaire.objects.exclude(pk=self.pk).update(active=False)
        super().save(*args, **kwargs)


class Section(models.Model):
    nom = models.CharField(max_length=100, unique=True)

    class Meta:
        ordering = ['nom']
        verbose_name = "Section"

    def __str__(self):
        return self.nom


class Classe(models.Model):
    nom = models.CharField(max_length=50)
    section = models.ForeignKey(Section, on_delete=models.CASCADE, related_name='classes')
    annee_scolaire = models.ForeignKey(AnneeScolaire, on_delete=models.CASCADE, related_name='classes')

    class Meta:
        ordering = ['nom', 'section__nom']
        unique_together = ['nom', 'section', 'annee_scolaire']
        verbose_name = "Classe"

    def __str__(self):
        return f"{self.nom} {self.section}"

    @property
    def nom_complet(self):
        return f"{self.nom} {self.section} - {self.annee_scolaire}"
