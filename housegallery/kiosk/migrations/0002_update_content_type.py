"""Update content_type app_label from 'home' to 'kiosk' for KioskPage.

This ensures Wagtail can find the KioskPage model under the new app label.
"""

from django.db import migrations


def update_content_type(apps, schema_editor):
    ContentType = apps.get_model('contenttypes', 'ContentType')
    ContentType.objects.filter(
        app_label='home',
        model='kioskpage',
    ).update(app_label='kiosk')


def revert_content_type(apps, schema_editor):
    ContentType = apps.get_model('contenttypes', 'ContentType')
    ContentType.objects.filter(
        app_label='kiosk',
        model='kioskpage',
    ).update(app_label='home')


class Migration(migrations.Migration):

    dependencies = [
        ('kiosk', '0001_initial'),
        ('contenttypes', '0002_remove_content_type_name'),
    ]

    operations = [
        migrations.RunPython(update_content_type, revert_content_type),
    ]
