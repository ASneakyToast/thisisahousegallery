from unittest.mock import patch

import pytest
from django.core import mail
from django.test import Client, RequestFactory
from wagtail.models import Site

from housegallery.newsletter.models import NewsletterEmailSettings, Subscriber
from housegallery.newsletter.views import (
    _CONFIRMATION_DEFAULTS,
    _UNSUBSCRIBE_DEFAULTS,
    _SafeDict,
    _get_email_settings,
    _send_confirmation_email,
    _send_unsubscribe_email,
)


class TestSafeDict:
    def test_known_keys_replaced(self):
        d = _SafeDict(email="test@example.com")
        assert "Hello {email}".format_map(d) == "Hello test@example.com"

    def test_unknown_keys_preserved(self):
        d = _SafeDict(email="test@example.com")
        assert "{unknown} {email}".format_map(d) == "{unknown} test@example.com"

    def test_empty_dict_preserves_all(self):
        d = _SafeDict()
        assert "{foo} {bar}".format_map(d) == "{foo} {bar}"


@pytest.mark.django_db
class TestGetEmailSettings:
    def test_returns_settings_with_empty_defaults(self):
        result = _get_email_settings()
        assert result is not None
        assert result.confirmation_subject == ""

    def test_returns_settings_with_custom_values(self):
        site = Site.objects.get(is_default_site=True)
        NewsletterEmailSettings.objects.create(
            site=site, confirmation_subject="Custom"
        )
        result = _get_email_settings()
        assert result is not None
        assert result.confirmation_subject == "Custom"


@pytest.mark.django_db
class TestConfirmationEmailWithSettings:
    def setup_method(self):
        self.factory = RequestFactory()
        self.request = self.factory.get("/")
        self.request.META["SERVER_NAME"] = "testserver"
        self.request.META["SERVER_PORT"] = "80"
        self.subscriber = Subscriber.objects.create(email="test@example.com")

    def test_uses_defaults_when_no_settings(self):
        _send_confirmation_email(self.request, self.subscriber)
        assert len(mail.outbox) == 1
        msg = mail.outbox[0]
        assert msg.subject == _CONFIRMATION_DEFAULTS["subject"]
        assert _CONFIRMATION_DEFAULTS["heading"] in msg.alternatives[0][0]

    def test_uses_custom_subject(self):
        site = Site.objects.get(is_default_site=True)
        NewsletterEmailSettings.objects.create(
            site=site,
            confirmation_subject="Custom Subject",
        )
        _send_confirmation_email(self.request, self.subscriber)
        assert mail.outbox[0].subject == "Custom Subject"

    def test_uses_custom_body_with_email_placeholder(self):
        site = Site.objects.get(is_default_site=True)
        NewsletterEmailSettings.objects.create(
            site=site,
            confirmation_body="Welcome {email} to our list!",
        )
        _send_confirmation_email(self.request, self.subscriber)
        html = mail.outbox[0].alternatives[0][0]
        assert "Welcome test@example.com to our list!" in html

    def test_falls_back_on_empty_fields(self):
        site = Site.objects.get(is_default_site=True)
        NewsletterEmailSettings.objects.create(
            site=site,
            confirmation_subject="",  # empty → use default
            confirmation_heading="Custom Heading",
        )
        _send_confirmation_email(self.request, self.subscriber)
        msg = mail.outbox[0]
        assert msg.subject == _CONFIRMATION_DEFAULTS["subject"]
        assert "Custom Heading" in msg.alternatives[0][0]


@pytest.mark.django_db
class TestUnsubscribeEmailWithSettings:
    def setup_method(self):
        self.factory = RequestFactory()
        self.request = self.factory.get("/")
        self.request.META["SERVER_NAME"] = "testserver"
        self.request.META["SERVER_PORT"] = "80"
        self.subscriber = Subscriber.objects.create(
            email="test@example.com", confirmed=True
        )

    def test_uses_defaults_when_no_settings(self):
        _send_unsubscribe_email(self.request, self.subscriber)
        assert len(mail.outbox) == 1
        msg = mail.outbox[0]
        assert msg.subject == _UNSUBSCRIBE_DEFAULTS["subject"]

    def test_uses_custom_subject(self):
        site = Site.objects.get(is_default_site=True)
        NewsletterEmailSettings.objects.create(
            site=site,
            unsubscribe_subject="Custom Unsub Subject",
        )
        _send_unsubscribe_email(self.request, self.subscriber)
        assert mail.outbox[0].subject == "Custom Unsub Subject"

    def test_uses_custom_body_with_email_placeholder(self):
        site = Site.objects.get(is_default_site=True)
        NewsletterEmailSettings.objects.create(
            site=site,
            unsubscribe_body="Removing {email} from list.",
        )
        _send_unsubscribe_email(self.request, self.subscriber)
        html = mail.outbox[0].alternatives[0][0]
        assert "Removing test@example.com from list." in html
