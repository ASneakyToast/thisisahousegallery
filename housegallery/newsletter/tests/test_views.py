import uuid
from unittest.mock import patch

import pytest
from django.test import Client
from django.urls import reverse

from housegallery.newsletter.models import Subscriber


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
class TestUnsubscribeRequestPage:
    def test_page_renders(self):
        client = Client()
        resp = client.get(reverse("newsletter:unsubscribe_request_page"))
        assert resp.status_code == 200


@pytest.mark.django_db
class TestUnsubscribeRequestView:
    def setup_method(self):
        from django.core.cache import cache

        cache.clear()
        self.client = Client(enforce_csrf_checks=True)
        self.url = reverse("newsletter:unsubscribe_request")

    def test_requires_post(self):
        resp = self.client.get(self.url)
        assert resp.status_code == 405

    def test_rejects_without_csrf_token(self):
        resp = self.client.post(self.url, {"email": "test@example.com"})
        assert resp.status_code == 403

    def _post_with_csrf(self, data):
        client = Client()
        return client.post(self.url, data)

    def test_missing_email(self):
        resp = self._post_with_csrf({})
        assert resp.status_code == 400
        assert resp.json()["success"] is False

    def test_invalid_email(self):
        resp = self._post_with_csrf({"email": "notanemail"})
        assert resp.status_code == 400

    @patch("housegallery.newsletter.views._send_unsubscribe_email")
    def test_active_subscriber_sends_email(self, mock_send):
        Subscriber.objects.create(email="active@example.com", confirmed=True)
        resp = self._post_with_csrf({"email": "active@example.com"})
        assert resp.status_code == 200
        assert resp.json()["success"] is True
        mock_send.assert_called_once()

    @patch("housegallery.newsletter.views._send_unsubscribe_email")
    def test_nonexistent_email_returns_generic_success(self, mock_send):
        resp = self._post_with_csrf({"email": "nobody@example.com"})
        assert resp.status_code == 200
        assert resp.json()["success"] is True
        mock_send.assert_not_called()

    @patch("housegallery.newsletter.views._send_unsubscribe_email")
    def test_inactive_subscriber_no_email(self, mock_send):
        """Unconfirmed subscriber should not receive unsubscribe email."""
        Subscriber.objects.create(email="pending@example.com", confirmed=False)
        resp = self._post_with_csrf({"email": "pending@example.com"})
        assert resp.status_code == 200
        assert resp.json()["success"] is True
        mock_send.assert_not_called()

    @patch("housegallery.newsletter.views._send_unsubscribe_email")
    def test_already_unsubscribed_no_email(self, mock_send):
        from django.utils import timezone

        Subscriber.objects.create(
            email="gone@example.com",
            confirmed=True,
            unsubscribed_at=timezone.now(),
        )
        resp = self._post_with_csrf({"email": "gone@example.com"})
        assert resp.status_code == 200
        assert resp.json()["success"] is True
        mock_send.assert_not_called()

    def test_rate_limiting(self):
        client = Client()
        for _ in range(5):
            client.post(self.url, {"email": "rate@example.com"})
        resp = client.post(self.url, {"email": "rate@example.com"})
        assert resp.status_code == 429


