from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("api", "0002_allow_blank_key"),
    ]

    operations = [
        migrations.CreateModel(
            name="ReadOnlyToken",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "key",
                    models.CharField(
                        blank=True,
                        db_index=True,
                        help_text="The token. Generated automatically if not provided.",
                        max_length=64,
                        unique=True,
                    ),
                ),
                (
                    "name",
                    models.CharField(
                        help_text="e.g. 'Kiosk display', 'Portfolio site'",
                        max_length=100,
                    ),
                ),
                (
                    "is_active",
                    models.BooleanField(
                        default=True,
                        help_text="Whether this token is currently active",
                    ),
                ),
                (
                    "allowed_ips",
                    models.JSONField(
                        blank=True,
                        default=list,
                        help_text="List of allowed IP addresses. Empty list allows all IPs.",
                    ),
                ),
                ("created", models.DateTimeField(auto_now_add=True)),
                ("last_used", models.DateTimeField(blank=True, null=True)),
                ("usage_count", models.PositiveIntegerField(default=0)),
            ],
            options={
                "verbose_name": "Read-Only Token",
                "verbose_name_plural": "Read-Only Tokens",
                "ordering": ["-created"],
            },
        ),
    ]
