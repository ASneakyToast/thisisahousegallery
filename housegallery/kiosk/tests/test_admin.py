import pytest
from django.contrib.auth.models import User
from django.test import Client
from django.urls import reverse
from wagtail.models import Page as WagtailPage

from housegallery.home.models import HomePage
from housegallery.kiosk.models import KioskPage


@pytest.fixture
def staff_user(db):
    return User.objects.create_superuser(
        username="staff", password="testpass"
    )


@pytest.fixture
def staff_client(staff_user):
    client = Client()
    client.login(username="staff", password="testpass")
    return client


@pytest.fixture
def home_page(db):
    root = WagtailPage.add_root(title="Root", slug="root-test")
    return root.add_child(
        instance=HomePage(title="Home", slug="home-test")
    )


@pytest.fixture
def kiosk_page(home_page):
    page = home_page.add_child(
        instance=KioskPage(
            title="Lobby Kiosk",
            slug="lobby-kiosk",
        )
    )
    revision = page.save_revision()
    revision.publish()
    page.refresh_from_db()
    return page


@pytest.mark.django_db
class TestKioskListing:
    def test_listing_accessible(self, staff_client):
        response = staff_client.get(reverse("kiosk_pages:index"))
        assert response.status_code == 200

    def test_listing_shows_kiosks(self, staff_client, kiosk_page):
        response = staff_client.get(reverse("kiosk_pages:index"))
        assert response.status_code == 200
        content = response.content.decode()
        assert "Lobby Kiosk" in content
