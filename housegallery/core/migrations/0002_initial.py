# Generated by Django 5.0.10 on 2025-06-26 05:57

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('core', '0001_initial'),
        ('images', '0001_initial'),
        ('wagtailcore', '0094_alter_page_locale'),
    ]

    operations = [
        migrations.AddField(
            model_name='blankpage',
            name='listing_image',
            field=models.ForeignKey(blank=True, help_text='Choose the image you wish to be displayed when this page appears in listings', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to='images.customimage'),
        ),
        migrations.AddField(
            model_name='navigationsettings',
            name='main_menu',
            field=models.ForeignKey(blank=True, help_text='Select the menu to be displayed in the site header', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to='core.navigationmenu'),
        ),
        migrations.AddField(
            model_name='navigationsettings',
            name='site',
            field=models.OneToOneField(editable=False, on_delete=django.db.models.deletion.CASCADE, to='wagtailcore.site'),
        ),
    ]
