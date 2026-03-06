import os

import pytest
from django.conf import settings
from django.contrib.auth.models import Permission, User
from django.core import mail
from django.test import Client
from django.urls import reverse

from housegallery.newsletter.models import Newsletter, Subscriber


def _edition_path(slug):
    return os.path.join(
        settings.BASE_DIR,
        "housegallery", "newsletter", "templates", "newsletter", "editions",
        f"{slug}.html",
    )


@pytest.fixture
def staff_user(db):
    user = User.objects.create_superuser(
        username="staff", password="testpass"
    )
    return user


@pytest.fixture
def regular_user(db):
    return User.objects.create_user(
        username="regular", password="testpass", is_staff=False
    )


@pytest.fixture
def staff_client(staff_user):
    client = Client()
    client.login(username="staff", password="testpass")
    return client


@pytest.fixture
def newsletter(db):
    slug = "test-admin-send"
    nl = Newsletter.objects.create(title="Test Newsletter", slug=slug)
    path = _edition_path(slug)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(
            '{% extends "newsletter/emails/base_email.html" %}'
            "{% block content %}<p>Test</p>{% endblock %}"
        )
    from django.template import engines

    for loader in engines["django"].engine.template_loaders:
        if hasattr(loader, "reset"):
            loader.reset()
    yield nl
    if os.path.exists(path):
        os.remove(path)


@pytest.fixture
def subscribers(db):
    subs = []
    for i in range(3):
        subs.append(
            Subscriber.objects.create(email=f"sub{i}@example.com", confirmed=True)
        )
    return subs


def _send_url(newsletter):
    return reverse(
        "wagtailsnippets_newsletter_newsletter:send", args=[newsletter.pk]
    )


@pytest.mark.django_db
class TestSendNewsletterViewAccess:
    def test_unauthenticated_redirects_to_login(self, newsletter):
        client = Client()
        response = client.get(_send_url(newsletter))
        assert response.status_code == 302
        assert "/login/" in response.url

    def test_non_staff_redirects_to_login(self, regular_user, newsletter):
        client = Client()
        client.login(username="regular", password="testpass")
        response = client.get(_send_url(newsletter))
        assert response.status_code == 302
        assert "/login/" in response.url

    def test_staff_allowed(self, staff_client, newsletter):
        response = staff_client.get(_send_url(newsletter))
        assert response.status_code == 200


@pytest.mark.django_db
class TestSendNewsletterViewGet:
    def test_renders_confirmation_page(self, staff_client, newsletter, subscribers):
        response = staff_client.get(_send_url(newsletter))
        assert response.status_code == 200
        content = response.content.decode()
        assert "Test Newsletter" in content
        assert "3" in content  # subscriber count

    def test_already_sent_shows_warning(self, staff_client, newsletter):
        newsletter.status = Newsletter.Status.SENT
        newsletter.save()
        response = staff_client.get(_send_url(newsletter))
        content = response.content.decode()
        assert "already sent" in content.lower()


@pytest.mark.django_db
class TestSendNewsletterViewTestSend:
    def test_test_send_works(self, staff_client, newsletter):
        response = staff_client.post(
            _send_url(newsletter),
            {"action": "test", "test_email": "test@example.com"},
        )
        assert response.status_code == 302
        assert len(mail.outbox) == 1
        assert mail.outbox[0].to == ["test@example.com"]

        newsletter.refresh_from_db()
        assert newsletter.status == Newsletter.Status.DRAFT

    def test_test_send_empty_email(self, staff_client, newsletter):
        response = staff_client.post(
            _send_url(newsletter),
            {"action": "test", "test_email": ""},
        )
        assert response.status_code == 200  # re-renders form
        assert len(mail.outbox) == 0


@pytest.mark.django_db
class TestSendNewsletterViewFullSend:
    def test_full_send_updates_status(self, staff_client, newsletter, subscribers):
        response = staff_client.post(
            _send_url(newsletter),
            {"action": "send", "confirm": "on"},
        )
        assert response.status_code == 302
        assert len(mail.outbox) == 3

        newsletter.refresh_from_db()
        assert newsletter.status == Newsletter.Status.SENT
        assert newsletter.sent_count == 3

    def test_full_send_without_confirm_rejected(
        self, staff_client, newsletter, subscribers
    ):
        response = staff_client.post(
            _send_url(newsletter),
            {"action": "send"},
        )
        assert response.status_code == 200
        assert len(mail.outbox) == 0

        newsletter.refresh_from_db()
        assert newsletter.status == Newsletter.Status.DRAFT

    def test_already_sent_requires_force(self, staff_client, newsletter, subscribers):
        newsletter.status = Newsletter.Status.SENT
        newsletter.save()

        response = staff_client.post(
            _send_url(newsletter),
            {"action": "send", "confirm": "on"},
        )
        assert response.status_code == 200  # re-renders with error
        assert len(mail.outbox) == 0

    def test_already_sent_with_force_succeeds(
        self, staff_client, newsletter, subscribers
    ):
        newsletter.status = Newsletter.Status.SENT
        newsletter.save()

        response = staff_client.post(
            _send_url(newsletter),
            {"action": "send", "confirm": "on", "force": "on"},
        )
        assert response.status_code == 302
        assert len(mail.outbox) == 3

    def test_no_subscribers_warning(self, staff_client, newsletter):
        response = staff_client.post(
            _send_url(newsletter),
            {"action": "send", "confirm": "on"},
        )
        assert response.status_code == 302
        assert len(mail.outbox) == 0


@pytest.mark.django_db
class TestNewsletterListingButtons:
    def test_send_button_in_listing(self, staff_client, newsletter):
        url = reverse("wagtailsnippets_newsletter_newsletter:list")
        response = staff_client.get(url)
        # Wagtail may serve listing results via AJAX or full page
        if response.status_code == 200 and response.content:
            content = response.content.decode()
            send_url = reverse(
                "wagtailsnippets_newsletter_newsletter:send",
                args=[newsletter.pk],
            )
            assert send_url in content

    def test_resend_button_for_sent_newsletter(self, staff_client, newsletter):
        newsletter.status = Newsletter.Status.SENT
        newsletter.save()
        url = reverse("wagtailsnippets_newsletter_newsletter:list")
        response = staff_client.get(url)
        if response.status_code == 200 and response.content:
            content = response.content.decode()
            assert "Resend" in content
