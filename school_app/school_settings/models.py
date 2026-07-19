from django.db import models


class SchoolInfo(models.Model):
    # ── Informations de base ────────────────────────────────────────────────
    nom = models.CharField(max_length=200, default="Institut Bungulu")
    province = models.CharField(max_length=100, default="Nord-Kivu")
    ville = models.CharField(max_length=100, default="Beni")
    commune = models.CharField(max_length=100, default="Bungulu")
    code = models.CharField(max_length=50, default="62024 / 101 / 03 / 1")
    logo = models.ImageField(upload_to='school/', null=True, blank=True)

    # ── PWA Système (back-office : préfets, enseignants) ───────────────────
    pwa_nom = models.CharField(
        "Nom complet (PWA système)", max_length=200,
        default="Système de Gestion Scolaire"
    )
    pwa_nom_court = models.CharField(
        "Nom court (PWA système)", max_length=30, default="SGS"
    )
    pwa_description = models.CharField(
        "Description (PWA système)", max_length=300,
        default="Plateforme de gestion scolaire."
    )

    # ── PWA Portail Parent ──────────────────────────────────────────────────
    portail_pwa_nom = models.CharField(
        "Nom complet (PWA portail parent)", max_length=200,
        default="Portail Parent"
    )
    portail_pwa_nom_court = models.CharField(
        "Nom court (PWA portail parent)", max_length=30, default="Parent"
    )
    portail_pwa_description = models.CharField(
        "Description (PWA portail parent)", max_length=300,
        default="Consultation des résultats scolaires, bulletins et informations des élèves."
    )

    # ── Identité visuelle ───────────────────────────────────────────────────
    theme_color = models.CharField(
        "Couleur principale (theme_color)", max_length=7, default="#1E293B"
    )
    background_color = models.CharField(
        "Couleur d'arrière-plan (background_color)", max_length=7, default="#0f172a"
    )

    class Meta:
        verbose_name = "Informations de l'école"

    def __str__(self):
        return self.nom

    @classmethod
    def get_info(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj
