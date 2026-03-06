import os
from unittest.mock import patch

import pytest
from django.conf import settings
from django.core import mail
from django.core.management import call_command
from django.core.management.base import CommandError

from housegallery.newsletter.models import Newsletter, Subscriber


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


@pytest.mark.django_db
class TestSendNewsletterCommand:
    """Tests for the send_newsletter management command."""

    @pytest.fixture(autouse=True)
    def setup_newsletter(self):
        """Create a newsletter with a temporary template on disk."""
        self.newsletter = Newsletter.objects.create(
            title="Test Edition", slug="test-edition"
        )
        path = _edition_path("test-edition")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            f.write(
                '{% extends "newsletter/emails/base_email.html" %}'
                "{% block content %}<p>Test</p>{% endblock %}"
            )
        # Clear Django's template cache so dynamically created templates
        # are discovered (CachedLoader negatively caches missing templates).
        from django.template import engines

        for loader in engines["django"].engine.template_loaders:
            if hasattr(loader, "reset"):
                loader.reset()
        yield
        if os.path.exists(path):
            os.remove(path)

    def _create_subscriber(self, email="sub@example.com", confirmed=True, **kwargs):
        return Subscriber.objects.create(email=email, confirmed=confirmed, **kwargs)

    def test_nonexistent_slug_raises(self):
        with pytest.raises(CommandError, match="No newsletter found"):
            call_command("send_newsletter", "nonexistent")

    def test_already_sent_without_force_raises(self):
        self.newsletter.status = Newsletter.Status.SENT
        self.newsletter.save()
        with pytest.raises(CommandError, match="already sent"):
            call_command("send_newsletter", "test-edition")

    def test_already_sent_with_force_succeeds(self):
        self.newsletter.status = Newsletter.Status.SENT
        self.newsletter.save()
        self._create_subscriber()
        call_command("send_newsletter", "test-edition", force=True)
        assert len(mail.outbox) == 1

    def test_no_recipients_warning(self):
        call_command("send_newsletter", "test-edition")
        assert len(mail.outbox) == 0

    def test_successful_send(self):
        self._create_subscriber("one@example.com")
        self._create_subscriber("two@example.com")
        call_command("send_newsletter", "test-edition")

        assert len(mail.outbox) == 2
        self.newsletter.refresh_from_db()
        assert self.newsletter.status == Newsletter.Status.SENT
        assert self.newsletter.sent_count == 2
        assert self.newsletter.sent_at is not None

    def test_dry_run_sends_nothing(self):
        self._create_subscriber()
        call_command("send_newsletter", "test-edition", dry_run=True)
        assert len(mail.outbox) == 0
        self.newsletter.refresh_from_db()
        assert self.newsletter.status == Newsletter.Status.DRAFT

    def test_test_mode_single_recipient(self):
        self._create_subscriber()
        call_command("send_newsletter", "test-edition", test="test@example.com")

        assert len(mail.outbox) == 1
        assert mail.outbox[0].to == ["test@example.com"]
        # Should NOT update newsletter status for test sends
        self.newsletter.refresh_from_db()
        assert self.newsletter.status == Newsletter.Status.DRAFT

    def test_excludes_unsubscribed(self):
        from django.utils import timezone
        self._create_subscriber("active@example.com")
        self._create_subscriber("unsub@example.com", unsubscribed_at=timezone.now())
        call_command("send_newsletter", "test-edition")

        assert len(mail.outbox) == 1
        assert mail.outbox[0].to == ["active@example.com"]

    def test_excludes_bounced_by_default(self):
        self._create_subscriber("good@example.com")
        self._create_subscriber("bounced@example.com", bounce_count=3)
        call_command("send_newsletter", "test-edition")

        assert len(mail.outbox) == 1
        assert mail.outbox[0].to == ["good@example.com"]

    def test_bounce_recorded_on_send_failure(self):
        sub = self._create_subscriber()
        with patch.object(
            mail.EmailMessage, "send", side_effect=Exception("SMTP error")
        ):
            call_command("send_newsletter", "test-edition")

        sub.refresh_from_db()
        assert sub.bounce_count == 1

    def test_list_unsubscribe_header(self):
        self._create_subscriber()
        call_command("send_newsletter", "test-edition")

        msg = mail.outbox[0]
        assert "List-Unsubscribe" in msg.extra_headers
        assert "/newsletter/unsubscribe/" in msg.extra_headers["List-Unsubscribe"]

    def test_newsletter_status_updated_after_send(self):
        self._create_subscriber()
        call_command("send_newsletter", "test-edition")

        self.newsletter.refresh_from_db()
        assert self.newsletter.status == Newsletter.Status.SENT
        assert self.newsletter.sent_count == 1
