import secrets
import string

from django.contrib.auth.models import AbstractUser
from django.db import models


def generate_temp_password(length=12):
    """Génère un mot de passe temporaire fort (majuscule, minuscule, chiffre, spécial)."""
    specials = '!@#$%&*'
    alphabet  = string.ascii_letters + string.digits + specials
    while True:
        pwd = [
            secrets.choice(string.ascii_uppercase),
            secrets.choice(string.ascii_lowercase),
            secrets.choice(string.digits),
            secrets.choice(specials),
        ]
        pwd += [secrets.choice(alphabet) for _ in range(length - 4)]
        secrets.SystemRandom().shuffle(pwd)
        result = ''.join(pwd)
        # Vérification force minimale
        import re
        if (len(result) >= length
                and re.search(r'[A-Z]', result)
                and re.search(r'[a-z]', result)
                and re.search(r'\d', result)
                and re.search(r'[!@#$%&*]', result)):
            return result


class CustomUser(AbstractUser):
    ROLE_CHOICES = [
        ('prefet',      'Préfet des études'),
        ('enseignant',  'Enseignant'),
    ]
    role                 = models.CharField(max_length=20, choices=ROLE_CHOICES, default='enseignant')
    telephone            = models.CharField('Téléphone', max_length=20, blank=True)
    must_change_password = models.BooleanField(
        'Doit changer le mot de passe', default=False,
        help_text='Oblige la personne à changer son mot de passe à la prochaine connexion.',
    )
    photo_profil = models.ImageField(
        'Photo de profil', upload_to='profils/', blank=True, null=True,
        help_text='Photo de profil affichée dans la barre de navigation et sur la page de profil.'
    )
    bio = models.TextField('Biographie / Note', blank=True, default='')

    def is_prefet(self):
        return self.role == 'prefet'

    def is_enseignant(self):
        return self.role == 'enseignant'

    def get_initiales(self):
        """Retourne les initiales du nom complet pour l'avatar par défaut."""
        parts = self.get_full_name().split()
        if len(parts) >= 2:
            return (parts[0][0] + parts[-1][0]).upper()
        if parts:
            return parts[0][:2].upper()
        return self.username[:2].upper()

    def __str__(self):
        return f"{self.get_full_name() or self.email or self.username} ({self.get_role_display()})"
