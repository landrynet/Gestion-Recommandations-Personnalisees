from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0003_photo_profil_bio'),
    ]

    operations = [
        migrations.AlterField(
            model_name='customuser',
            name='role',
            field=models.CharField(
                choices=[('prefet', 'Préfet des études'), ('enseignant', 'Enseignant')],
                db_index=True,
                default='enseignant',
                max_length=20,
            ),
        ),
    ]
