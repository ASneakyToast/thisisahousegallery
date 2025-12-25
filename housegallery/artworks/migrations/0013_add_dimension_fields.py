from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('artworks', '0012_add_price_field'),
    ]

    operations = [
        migrations.AddField(
            model_name='artwork',
            name='width_inches',
            field=models.DecimalField(
                blank=True,
                null=True,
                max_digits=7,
                decimal_places=3,
                help_text='Width in inches'
            ),
        ),
        migrations.AddField(
            model_name='artwork',
            name='height_inches',
            field=models.DecimalField(
                blank=True,
                null=True,
                max_digits=7,
                decimal_places=3,
                help_text='Height in inches'
            ),
        ),
        migrations.AddField(
            model_name='artwork',
            name='depth_inches',
            field=models.DecimalField(
                blank=True,
                null=True,
                max_digits=7,
                decimal_places=3,
                help_text='Depth in inches (optional for 2D works)'
            ),
        ),
        migrations.AlterField(
            model_name='artwork',
            name='size',
            field=models.CharField(
                blank=True,
                max_length=255,
                help_text='DEPRECATED: Use dimension fields instead'
            ),
        ),
    ]
