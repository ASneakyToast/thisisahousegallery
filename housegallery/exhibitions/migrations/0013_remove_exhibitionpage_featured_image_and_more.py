# Generated by Django 5.0.10 on 2025-07-18 23:57

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('exhibitions', '0012_auto_20250717_2051'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='exhibitionpage',
            name='featured_image',
        ),
        migrations.AddField(
            model_name='eventpage',
            name='related_exhibition',
            field=models.ForeignKey(blank=True, help_text='Link this event to a specific exhibition', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='related_events', to='exhibitions.exhibitionpage'),
        ),
        migrations.AddField(
            model_name='exhibitionpage',
            name='auto_created_opening_event',
            field=models.ForeignKey(blank=True, help_text='The opening event that was automatically created for this exhibition', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='auto_created_from_exhibition', to='exhibitions.eventpage'),
        ),
        migrations.AddField(
            model_name='exhibitionpage',
            name='create_opening_event',
            field=models.BooleanField(default=False, help_text='Check to automatically create an opening reception event for this exhibition'),
        ),
    ]
