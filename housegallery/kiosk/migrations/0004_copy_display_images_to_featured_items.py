"""Data migration: copy display_images → featured_items for existing KioskPages.

The block types single_image, tagged_set, and all_images are identical
between KioskImageSourceBlock and KioskFeaturedItemsBlock, so the raw
StreamField JSON can be copied directly.
"""
from django.db import migrations


def copy_display_images_to_featured_items(apps, schema_editor):
    """Copy display_images StreamField data into featured_items using raw SQL
    to avoid StreamField deserialization issues in migrations."""
    db_alias = schema_editor.connection.alias
    from django.db import connections
    connection = connections[db_alias]

    with connection.cursor() as cursor:
        cursor.execute("""
            UPDATE kiosk_kioskpage
            SET featured_items = display_images
            WHERE (featured_items IS NULL OR featured_items::text = '[]')
              AND display_images IS NOT NULL
              AND display_images::text != '[]'
        """)


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('kiosk', '0003_add_featured_items'),
    ]

    operations = [
        migrations.RunPython(copy_display_images_to_featured_items, noop),
    ]
