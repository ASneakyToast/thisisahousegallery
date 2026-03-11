import pytest
from django.test import Client
from wagtail.models import Page as WagtailPage

from housegallery.home.models import HomePage
from housegallery.kiosk.models import KioskPage


@pytest.fixture
def client():
    return Client()


@pytest.fixture
def home_page(db):
    root = WagtailPage.add_root(title="Root", slug="root-test")
    return root.add_child(
        instance=HomePage(title="Home", slug="home-test")
    )


@pytest.fixture
def particles_kiosk(home_page):
    page = home_page.add_child(
        instance=KioskPage(
            title="Lobby Kiosk",
            slug="lobby-kiosk",
            display_template="particles",
        )
    )
    revision = page.save_revision()
    revision.publish()
    page.refresh_from_db()
    return page


@pytest.fixture
def simple_kiosk(home_page):
    page = home_page.add_child(
        instance=KioskPage(
            title="Bar Display",
            slug="bar-display",
            display_template="simple",
            background_style="solid_color",
        )
    )
    revision = page.save_revision()
    revision.publish()
    page.refresh_from_db()
    return page


@pytest.fixture
def second_kiosk(home_page):
    page = home_page.add_child(
        instance=KioskPage(
            title="Upstairs Kiosk",
            slug="upstairs-kiosk",
        )
    )
    revision = page.save_revision()
    revision.publish()
    page.refresh_from_db()
    return page


@pytest.mark.django_db
class TestKioskDisplayBySlug:
    def test_returns_200_for_live_particles_kiosk(self, client, particles_kiosk):
        response = client.get("/display/lobby-kiosk/")
        assert response.status_code == 200

    def test_returns_200_for_live_simple_kiosk(self, client, simple_kiosk):
        response = client.get("/display/bar-display/")
        assert response.status_code == 200
        content = response.content.decode()
        assert "Bar Display" in content

    def test_returns_fallback_for_nonexistent_slug(self, client, particles_kiosk):
        response = client.get("/display/nonexistent/")
        assert response.status_code == 200
        content = response.content.decode()
        assert "No kiosk display found" in content

    def test_serves_correct_kiosk(self, client, particles_kiosk, second_kiosk):
        response = client.get("/display/upstairs-kiosk/")
        assert response.status_code == 200
        content = response.content.decode()
        assert "Upstairs Kiosk" in content


@pytest.mark.django_db
class TestKioskListOrDefault:
    def test_single_kiosk_served_directly(self, client, particles_kiosk):
        response = client.get("/display/")
        assert response.status_code == 200
        content = response.content.decode()
        assert "Lobby Kiosk" in content

    def test_no_kiosks_shows_fallback(self, client, home_page):
        response = client.get("/display/")
        assert response.status_code == 200
        content = response.content.decode()
        assert "not configured" in content

    def test_multiple_kiosks_shows_listing(self, client, particles_kiosk, second_kiosk):
        response = client.get("/display/")
        assert response.status_code == 200
        content = response.content.decode()
        assert "Multiple kiosk displays" in content
        assert "Lobby Kiosk" in content
        assert "Upstairs Kiosk" in content

    def test_mixed_templates_shows_listing(self, client, particles_kiosk, simple_kiosk):
        response = client.get("/display/")
        assert response.status_code == 200
        content = response.content.decode()
        assert "Multiple kiosk displays" in content
        assert "Lobby Kiosk" in content
        assert "Bar Display" in content
