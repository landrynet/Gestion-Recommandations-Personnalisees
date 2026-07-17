from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    ROLE_CHOICES = [
        ('prefet', 'Préfet des études'),
        ('enseignant', 'Enseignant'),
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='enseignant')

    def is_prefet(self):
        return self.role == 'prefet'

    def is_enseignant(self):
        return self.role == 'enseignant'

    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.get_role_display()})"
