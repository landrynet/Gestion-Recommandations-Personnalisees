from django.db import models
from django.utils import timezone


class AnneeScolaire(models.Model):
    annee = models.CharField(max_length=9, unique=True)  # ex: 2024-2025
    active = models.BooleanField(default=False)
    cloturee = models.BooleanField(default=False, verbose_name="Clôturée")
    date_debut = models.DateField(null=True, blank=True, verbose_name="Date de début")
    date_fin = models.DateField(null=True, blank=True, verbose_name="Date de fin")
    date_cloture = models.DateTimeField(null=True, blank=True, verbose_name="Date de clôture")

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

    @property
    def est_modifiable(self):
        """Une année est modifiable si elle n'est pas clôturée."""
        return not self.cloturee

    def cloturer(self, user=None):
        """Clôture définitive de l'année scolaire."""
        self.cloturee = True
        self.active = False
        self.date_cloture = timezone.now()
        self.save()
        JournalOperation.objects.create(
            type_operation='CLOTURE_ANNEE',
            annee_scolaire=self,
            utilisateur=user,
            details={'annee': self.annee},
        )


class Niveau(models.Model):
    """Niveau scolaire (ex: 7ème, 8ème, 1ère Secondaire, etc.)"""
    nom = models.CharField(max_length=50, unique=True, verbose_name="Nom")
    ordre = models.PositiveIntegerField(
        default=0,
        verbose_name="Ordre de promotion",
        help_text="Utilisé pour la promotion automatique. Ordre croissant = niveaux successifs."
    )
    cycle = models.CharField(
        max_length=50, blank=True,
        verbose_name="Cycle",
        help_text="Optionnel: Primaire, Secondaire, etc."
    )

    class Meta:
        ordering = ['ordre', 'nom']
        verbose_name = "Niveau"
        verbose_name_plural = "Niveaux"

    def __str__(self):
        return self.nom

    def get_niveau_suivant(self):
        """Retourne le niveau immédiatement supérieur selon l'ordre."""
        return Niveau.objects.filter(ordre__gt=self.ordre).order_by('ordre').first()


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
    niveau = models.ForeignKey(
        Niveau,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='classes',
        verbose_name="Niveau"
    )

    class Meta:
        ordering = ['niveau__ordre', 'nom', 'section__nom']
        unique_together = ['nom', 'section', 'annee_scolaire']
        verbose_name = "Classe"

    def __str__(self):
        if self.niveau:
            return f"{self.niveau} {self.section} {self.nom}"
        return f"{self.nom} {self.section}"

    @property
    def nom_complet(self):
        if self.niveau:
            return f"{self.niveau} {self.section} {self.nom} - {self.annee_scolaire}"
        return f"{self.nom} {self.section} - {self.annee_scolaire}"

    @property
    def est_modifiable(self):
        return self.annee_scolaire.est_modifiable


class DecisionPromotion(models.Model):
    """Décision de promotion d'un élève à la fin d'une année scolaire."""
    DECISION_CHOICES = [
        ('ADMIS', 'Admis — Promotion'),
        ('REDOUBLE', 'Redouble'),
        ('TRANSFERE', 'Transféré'),
        ('DIPLOME', 'Diplômé / Fin de cycle'),
    ]

    eleve = models.ForeignKey(
        'students.Student', on_delete=models.CASCADE, related_name='decisions_promotion'
    )
    annee_scolaire = models.ForeignKey(
        AnneeScolaire, on_delete=models.CASCADE, related_name='decisions_promotion'
    )
    classe_source = models.ForeignKey(
        Classe, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='decisions_depart',
        verbose_name="Classe d'origine"
    )
    decision = models.CharField(max_length=20, choices=DECISION_CHOICES, default='ADMIS')
    classe_destination = models.ForeignKey(
        Classe, null=True, blank=True, on_delete=models.SET_NULL,
        related_name='decisions_arrivee',
        verbose_name="Classe de destination"
    )
    observations = models.TextField(blank=True, verbose_name="Observations")
    validee = models.BooleanField(default=False, verbose_name="Validée")
    date_decision = models.DateTimeField(auto_now_add=True)
    decidee_par = models.ForeignKey(
        'accounts.CustomUser', on_delete=models.SET_NULL, null=True, blank=True
    )

    class Meta:
        unique_together = ['eleve', 'annee_scolaire']
        ordering = ['eleve__nom', 'eleve__postnom']
        verbose_name = "Décision de promotion"
        verbose_name_plural = "Décisions de promotion"

    def __str__(self):
        return f"{self.eleve} — {self.get_decision_display()} ({self.annee_scolaire})"


class JournalOperation(models.Model):
    """Journal d'audit des opérations importantes sur les années scolaires."""
    TYPE_CHOICES = [
        ('CREATION_ANNEE', "Création d'une année"),
        ('ACTIVATION_ANNEE', "Activation d'une année"),
        ('CLOTURE_ANNEE', "Clôture d'une année"),
        ('MIGRATION', "Migration des données"),
        ('PROMOTION', "Promotion des élèves"),
        ('ARCHIVAGE', "Archivage"),
    ]

    type_operation = models.CharField(max_length=30, choices=TYPE_CHOICES)
    annee_scolaire = models.ForeignKey(
        AnneeScolaire, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='journal_operations'
    )
    utilisateur = models.ForeignKey(
        'accounts.CustomUser', on_delete=models.SET_NULL, null=True, blank=True
    )
    details = models.JSONField(default=dict, blank=True)
    date_operation = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date_operation']
        verbose_name = "Journal d'opération"
        verbose_name_plural = "Journal des opérations"

    def __str__(self):
        return f"{self.get_type_operation_display()} — {self.date_operation:%d/%m/%Y %H:%M}"
