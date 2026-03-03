import os

import pytest
from django.conf import settings
from django.core.management import call_command
from django.core.management.base import CommandError

from housegallery.newsletter.models import Newsletter


def _edition_path(slug):
    return os.path.join(
        settings.BASE_DIR,
        "housegallery", "newsletter", "templates", "newsletter", "editions",
        f"{slug}.html",
    )


@pytest.mark.django_db
class TestCreateNewsletterCommand:
    def test_creates_newsletter_and_template(self):
        slug = "test-edition"
        try:
            call_command("create_newsletter", slug, "Test Edition")
            nl = Newsletter.objects.get(slug=slug)
            assert nl.title == "Test Edition"
            assert nl.status == Newsletter.Status.DRAFT
            assert os.path.exists(_edition_path(slug))
        finally:
            path = _edition_path(slug)
            if os.path.exists(path):
                os.remove(path)

    def test_duplicate_slug_raises(self):
        Newsletter.objects.create(title="Existing", slug="existing")
        with pytest.raises(CommandError, match="already exists"):
            call_command("create_newsletter", "existing", "Another")

    def test_custom_subject(self):
        slug = "custom-subj"
        try:
            call_command(
                "create_newsletter", slug, "My Newsletter",
                subject="Custom Subject Line",
            )
            nl = Newsletter.objects.get(slug=slug)
            assert nl.subject == "Custom Subject Line"
        finally:
            path = _edition_path(slug)
            if os.path.exists(path):
                os.remove(path)
