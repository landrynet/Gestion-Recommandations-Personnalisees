from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('school_settings', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='schoolinfo',
            name='pwa_nom',
            field=models.CharField(
                default='Système de Gestion Scolaire',
                max_length=200,
                verbose_name='Nom complet (PWA système)',
            ),
        ),
        migrations.AddField(
            model_name='schoolinfo',
            name='pwa_nom_court',
            field=models.CharField(
                default='SGS',
                max_length=30,
                verbose_name='Nom court (PWA système)',
            ),
        ),
        migrations.AddField(
            model_name='schoolinfo',
            name='pwa_description',
            field=models.CharField(
                default='Plateforme de gestion scolaire.',
                max_length=300,
                verbose_name='Description (PWA système)',
            ),
        ),
        migrations.AddField(
            model_name='schoolinfo',
            name='portail_pwa_nom',
            field=models.CharField(
                default='Portail Parent',
                max_length=200,
                verbose_name='Nom complet (PWA portail parent)',
            ),
        ),
        migrations.AddField(
            model_name='schoolinfo',
            name='portail_pwa_nom_court',
            field=models.CharField(
                default='Parent',
                max_length=30,
                verbose_name='Nom court (PWA portail parent)',
            ),
        ),
        migrations.AddField(
            model_name='schoolinfo',
            name='portail_pwa_description',
            field=models.CharField(
                default='Consultation des résultats scolaires, bulletins et informations des élèves.',
                max_length=300,
                verbose_name='Description (PWA portail parent)',
            ),
        ),
        migrations.AddField(
            model_name='schoolinfo',
            name='theme_color',
            field=models.CharField(
                default='#1E293B',
                max_length=7,
                verbose_name="Couleur principale (theme_color)",
            ),
        ),
        migrations.AddField(
            model_name='schoolinfo',
            name='background_color',
            field=models.CharField(
                default='#0f172a',
                max_length=7,
                verbose_name="Couleur d'arrière-plan (background_color)",
            ),
        ),
    ]
