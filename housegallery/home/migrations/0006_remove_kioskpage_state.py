"""Remove KioskPage from home app state only (no DB changes).

Part of moving KioskPage from home app to kiosk app.
"""

import django.db.models.deletion
import wagtail.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0005_alter_homepage_body'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.DeleteModel(
                    name='KioskPage',
                ),
            ],
            database_operations=[],
        ),
    ]
