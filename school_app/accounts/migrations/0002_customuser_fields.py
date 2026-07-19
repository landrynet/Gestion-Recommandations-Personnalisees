from django.db import migrations, models


class Migration(migrations.Migration):
    """Ajoute must_change_password et telephone à CustomUser.

    NOTE : l'unicité de l'e-mail est gérée dans le formulaire (clean_email),
    pas par une contrainte base de données, afin de rester compatible avec
    les comptes existants qui ont un e-mail vide.
    """

    dependencies = [
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='customuser',
            name='must_change_password',
            field=models.BooleanField(
                default=False,
                verbose_name='Doit changer le mot de passe',
                help_text='Oblige la personne à changer son mot de passe à la prochaine connexion.',
            ),
        ),
        migrations.AddField(
            model_name='customuser',
            name='telephone',
            field=models.CharField(
                max_length=20, blank=True,
                verbose_name='Téléphone',
            ),
        ),
    ]
