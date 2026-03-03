import pytest
from django.utils import timezone

from housegallery.newsletter.models import Newsletter, Subscriber


@pytest.mark.django_db
class TestSubscriber:
    def test_create_subscriber(self):
        sub = Subscriber.objects.create(email="test@example.com")
        assert sub.email == "test@example.com"
        assert sub.confirmed is False
        assert sub.confirmation_token is not None
        assert sub.unsubscribe_token is not None
        assert sub.is_active is False

    def test_confirm(self):
        sub = Subscriber.objects.create(email="test@example.com")
        sub.confirm()
        sub.refresh_from_db()
        assert sub.confirmed is True
        assert sub.confirmed_at is not None
        assert sub.is_active is True

    def test_unsubscribe(self):
        sub = Subscriber.objects.create(email="test@example.com", confirmed=True)
        sub.unsubscribe()
        sub.refresh_from_db()
        assert sub.unsubscribed_at is not None
        assert sub.is_active is False

    def test_str_pending(self):
        sub = Subscriber(email="test@example.com")
        assert "pending" in str(sub)

    def test_str_confirmed(self):
        sub = Subscriber(email="test@example.com", confirmed=True)
        assert "confirmed" in str(sub)

    def test_str_unsubscribed(self):
        sub = Subscriber(email="test@example.com", unsubscribed_at=timezone.now())
        assert "unsubscribed" in str(sub)

    def test_unique_email(self):
        Subscriber.objects.create(email="test@example.com")
        with pytest.raises(Exception):
            Subscriber.objects.create(email="test@example.com")


@pytest.mark.django_db
class TestNewsletter:
    def test_create_newsletter(self):
        nl = Newsletter.objects.create(title="Test", slug="test")
        assert nl.status == Newsletter.Status.DRAFT
        assert nl.sent_count == 0

    def test_effective_subject_uses_title(self):
        nl = Newsletter(title="My Title", slug="my-title")
        assert nl.effective_subject == "My Title"

    def test_effective_subject_uses_subject(self):
        nl = Newsletter(title="My Title", slug="my-title", subject="Custom Subject")
        assert nl.effective_subject == "Custom Subject"

    def test_template_path(self):
        nl = Newsletter(slug="spring-2026")
        assert nl.template_path == "newsletter/editions/spring-2026.html"

    def test_str(self):
        nl = Newsletter(title="Spring", slug="spring", status=Newsletter.Status.DRAFT)
        assert "Spring" in str(nl)
        assert "Draft" in str(nl)
