# Generated by Django 5.0.10 on 2025-07-19 00:01

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('exhibitions', '0014_add_performance_indexes'),
    ]

    operations = [
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS idx_installation_photo_page_id ON exhibitions_installationphoto (page_id);",
            reverse_sql="DROP INDEX IF EXISTS idx_installation_photo_page_id;"
        ),
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS idx_installation_photo_image_id ON exhibitions_installationphoto (image_id);",
            reverse_sql="DROP INDEX IF EXISTS idx_installation_photo_image_id;"
        ),
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS idx_installation_photo_artwork_id ON exhibitions_installationphoto (related_artwork_id);",
            reverse_sql="DROP INDEX IF EXISTS idx_installation_photo_artwork_id;"
        ),
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS idx_opening_photo_page_id ON exhibitions_openingreceptionphoto (page_id);",
            reverse_sql="DROP INDEX IF EXISTS idx_opening_photo_page_id;"
        ),
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS idx_opening_photo_image_id ON exhibitions_openingreceptionphoto (image_id);",
            reverse_sql="DROP INDEX IF EXISTS idx_opening_photo_image_id;"
        ),
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS idx_showcard_photo_page_id ON exhibitions_showcardphoto (page_id);",
            reverse_sql="DROP INDEX IF EXISTS idx_showcard_photo_page_id;"
        ),
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS idx_showcard_photo_image_id ON exhibitions_showcardphoto (image_id);",
            reverse_sql="DROP INDEX IF EXISTS idx_showcard_photo_image_id;"
        ),
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS idx_inprogress_photo_page_id ON exhibitions_inprogressphoto (page_id);",
            reverse_sql="DROP INDEX IF EXISTS idx_inprogress_photo_page_id;"
        ),
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS idx_inprogress_photo_image_id ON exhibitions_inprogressphoto (image_id);",
            reverse_sql="DROP INDEX IF EXISTS idx_inprogress_photo_image_id;"
        ),
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS idx_typed_images_sort_order ON exhibitions_installationphoto (page_id, sort_order);",
            reverse_sql="DROP INDEX IF EXISTS idx_typed_images_sort_order;"
        ),
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS idx_opening_images_sort_order ON exhibitions_openingreceptionphoto (page_id, sort_order);",
            reverse_sql="DROP INDEX IF EXISTS idx_opening_images_sort_order;"
        ),
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS idx_showcard_images_sort_order ON exhibitions_showcardphoto (page_id, sort_order);",
            reverse_sql="DROP INDEX IF EXISTS idx_showcard_images_sort_order;"
        ),
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS idx_inprogress_images_sort_order ON exhibitions_inprogressphoto (page_id, sort_order);",
            reverse_sql="DROP INDEX IF EXISTS idx_inprogress_images_sort_order;"
        ),
    ]
