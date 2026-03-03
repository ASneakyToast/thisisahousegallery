from unittest.mock import patch

import pytest
from django.test import Client
from django.urls import reverse

from housegallery.newsletter.models import Subscriber


@pytest.mark.django_db
class TestSubscribeView:
    def setup_method(self):
        self.client = Client()
        self.url = reverse("newsletter:subscribe")

    def test_requires_post(self):
        resp = self.client.get(self.url)
        assert resp.status_code == 405

    def test_missing_email(self):
        resp = self.client.post(self.url, {})
        assert resp.status_code == 400
        assert resp.json()["success"] is False

    def test_invalid_email(self):
        resp = self.client.post(self.url, {"email": "notanemail"})
        assert resp.status_code == 400

    @patch("housegallery.newsletter.views._send_confirmation_email")
    def test_valid_email_creates_subscriber(self, mock_send):
        resp = self.client.post(self.url, {"email": "new@example.com"})
        assert resp.status_code == 200
        assert resp.json()["success"] is True
        assert Subscriber.objects.filter(email="new@example.com").exists()
        mock_send.assert_called_once()

    @patch("housegallery.newsletter.views._send_confirmation_email")
    def test_duplicate_active_subscriber(self, mock_send):
        Subscriber.objects.create(
            email="existing@example.com", confirmed=True
        )
        resp = self.client.post(self.url, {"email": "existing@example.com"})
        assert resp.status_code == 200
        assert "already subscribed" in resp.json()["message"].lower()
        mock_send.assert_not_called()

    @patch("housegallery.newsletter.views._send_confirmation_email")
    def test_email_normalized_to_lowercase(self, mock_send):
        resp = self.client.post(self.url, {"email": "Test@Example.COM"})
        assert resp.status_code == 200
        assert Subscriber.objects.filter(email="test@example.com").exists()


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
        import uuid

        url = reverse("newsletter:confirm", args=[uuid.uuid4()])
        resp = self.client.get(url)
        assert resp.status_code == 404


@pytest.mark.django_db
class TestUnsubscribeView:
    def setup_method(self):
        self.client = Client()

    def test_valid_token_unsubscribes(self):
        sub = Subscriber.objects.create(email="test@example.com", confirmed=True)
        url = reverse("newsletter:unsubscribe", args=[sub.unsubscribe_token])
        resp = self.client.get(url)
        assert resp.status_code == 200
        sub.refresh_from_db()
        assert sub.unsubscribed_at is not None

    def test_invalid_token_404(self):
        import uuid

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
    def test_anonymous_user_forbidden(self):
        from housegallery.newsletter.models import Newsletter

        Newsletter.objects.create(title="Test", slug="test")
        client = Client()
        resp = client.get(reverse("newsletter:preview", args=["test"]))
        assert resp.status_code == 403
