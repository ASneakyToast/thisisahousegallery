import os
import uuid
from unittest.mock import patch

import pytest
from django.conf import settings
from django.contrib.auth.models import User
from django.test import Client
from django.urls import reverse

from housegallery.newsletter.models import Newsletter, Subscriber


@pytest.mark.django_db
class TestSubscribeView:
    def setup_method(self):
        self.client = Client(enforce_csrf_checks=True)
        self.url = reverse("newsletter:subscribe")

    def test_requires_post(self):
        resp = self.client.get(self.url)
        assert resp.status_code == 405

    def test_rejects_without_csrf_token(self):
        resp = self.client.post(self.url, {"email": "test@example.com"})
        assert resp.status_code == 403

    def _post_with_csrf(self, data):
        """POST with a valid CSRF token (via the non-enforcing client)."""
        client = Client()
        return client.post(self.url, data)

    def test_missing_email(self):
        resp = self._post_with_csrf({})
        assert resp.status_code == 400
        assert resp.json()["success"] is False

    def test_invalid_email(self):
        resp = self._post_with_csrf({"email": "notanemail"})
        assert resp.status_code == 400

    @patch("housegallery.newsletter.views._send_confirmation_email")
    def test_valid_email_creates_subscriber(self, mock_send):
        resp = self._post_with_csrf({"email": "new@example.com"})
        assert resp.status_code == 200
        assert resp.json()["success"] is True
        assert Subscriber.objects.filter(email="new@example.com").exists()
        mock_send.assert_called_once()

    @patch("housegallery.newsletter.views._send_confirmation_email")
    def test_duplicate_active_subscriber(self, mock_send):
        Subscriber.objects.create(
            email="existing@example.com", confirmed=True
        )
        resp = self._post_with_csrf({"email": "existing@example.com"})
        assert resp.status_code == 200
        assert "already subscribed" in resp.json()["message"].lower()
        mock_send.assert_not_called()

    @patch("housegallery.newsletter.views._send_confirmation_email")
    def test_email_normalized_to_lowercase(self, mock_send):
        resp = self._post_with_csrf({"email": "Test@Example.COM"})
        assert resp.status_code == 200
        assert Subscriber.objects.filter(email="test@example.com").exists()

    def test_rate_limiting(self):
        client = Client()
        for _ in range(5):
            client.post(self.url, {"email": "rate@example.com"})
        resp = client.post(self.url, {"email": "rate@example.com"})
        assert resp.status_code == 429


@pytest.mark.django_db
class TestConfirmView:
    def setup_method(self):
        self.client = Client()

    def test_valid_token_confirms(self):
        sub = Subscriber.objects.create(email="test@example.com")
        url = reverse("newsletter:confirm", args=[sub.confirmation_token])
        resp = self.client.get(url)
        assert resp.status_code == 200
        sub.refresh_from_db()
        assert sub.confirmed is True

    def test_invalid_token_404(self):
        url = reverse("newsletter:confirm", args=[uuid.uuid4()])
        resp = self.client.get(url)
        assert resp.status_code == 404


@pytest.mark.django_db
class TestUnsubscribeView:
    def setup_method(self):
        self.client = Client()

    def test_get_shows_confirmation_page(self):
        sub = Subscriber.objects.create(email="test@example.com", confirmed=True)
        url = reverse("newsletter:unsubscribe", args=[sub.unsubscribe_token])
        resp = self.client.get(url)
        assert resp.status_code == 200
        assert b"Are you sure" in resp.content
        sub.refresh_from_db()
        assert sub.unsubscribed_at is None  # Not unsubscribed yet

    def test_post_performs_unsubscribe(self):
        sub = Subscriber.objects.create(email="test@example.com", confirmed=True)
        url = reverse("newsletter:unsubscribe", args=[sub.unsubscribe_token])
        resp = self.client.post(url)
        assert resp.status_code == 200
        assert b"has been removed" in resp.content
        sub.refresh_from_db()
        assert sub.unsubscribed_at is not None

    def test_already_unsubscribed_get(self):
        from django.utils import timezone
        sub = Subscriber.objects.create(
            email="test@example.com", confirmed=True,
            unsubscribed_at=timezone.now(),
        )
        url = reverse("newsletter:unsubscribe", args=[sub.unsubscribe_token])
        resp = self.client.get(url)
        assert resp.status_code == 200
        assert b"Already Unsubscribed" in resp.content

    def test_invalid_token_404(self):
        url = reverse("newsletter:unsubscribe", args=[uuid.uuid4()])
        resp = self.client.get(url)
        assert resp.status_code == 404


@pytest.mark.django_db
class TestSignupPage:
    def test_signup_page_renders(self):
        client = Client()
        resp = client.get(reverse("newsletter:signup"))
        assert resp.status_code == 200


@pytest.mark.django_db
class TestPreviewView:
    def test_anonymous_user_redirects_to_login(self):
        Newsletter.objects.create(title="Test", slug="test")
        client = Client()
        resp = client.get(reverse("newsletter:preview", args=["test"]))
        assert resp.status_code == 302
        assert "/login/" in resp.url or "/admin/login/" in resp.url

    def test_staff_user_can_access(self):
        Newsletter.objects.create(title="Test", slug="test")
        # Create a temporary template for the preview
        editions_dir = os.path.join(
            settings.BASE_DIR,
            "housegallery", "newsletter", "templates", "newsletter", "editions",
        )
        path = os.path.join(editions_dir, "test.html")
        os.makedirs(editions_dir, exist_ok=True)
        try:
            with open(path, "w") as f:
                f.write(
                    '{% extends "newsletter/emails/base_email.html" %}'
                    "{% block content %}<p>Preview</p>{% endblock %}"
                )
            from django.template import engines

            for loader in engines["django"].engine.template_loaders:
                if hasattr(loader, "reset"):
                    loader.reset()
            user = User.objects.create_user("staff", password="pass", is_staff=True)
            client = Client()
            client.force_login(user)
            resp = client.get(reverse("newsletter:preview", args=["test"]))
            assert resp.status_code == 200
        finally:
            if os.path.exists(path):
                os.remove(path)
