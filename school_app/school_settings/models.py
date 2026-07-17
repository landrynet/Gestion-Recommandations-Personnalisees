from django.db import models


class SchoolInfo(models.Model):
    nom = models.CharField(max_length=200, default="Institut Bungulu")
    province = models.CharField(max_length=100, default="Nord-Kivu")
    ville = models.CharField(max_length=100, default="Beni")
    commune = models.CharField(max_length=100, default="Bungulu")
    code = models.CharField(max_length=50, default="62024 / 101 / 03 / 1")
    logo = models.ImageField(upload_to='school/', null=True, blank=True)

    class Meta:
        verbose_name = "Informations de l'école"

    def __str__(self):
        return self.nom

    @classmethod
    def get_info(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj
