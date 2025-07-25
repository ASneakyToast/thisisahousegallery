# Generated by Django 5.0.10 on 2025-07-17 16:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('exhibitions', '0009_alter_exhibitionpage_body_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='exhibitionimage',
            name='image_type',
            field=models.CharField(choices=[('exhibition', 'Exhibition'), ('opening', 'Opening'), ('showcards', 'Showcards'), ('in_progress', 'In Progress')], default='exhibition', help_text='Type of image - exhibition, opening event, showcards, or in-progress shots', max_length=20),
        ),
    ]
