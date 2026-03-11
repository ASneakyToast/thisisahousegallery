import pytest
from wagtail.models import Page as WagtailPage

from housegallery.home.models import HomePage
from housegallery.kiosk.models import KioskPage


@pytest.fixture
def home_page(db):
    root = WagtailPage.add_root(title="Root", slug="root-test")
    return root.add_child(
        instance=HomePage(title="Home", slug="home-test")
    )


@pytest.fixture
def particles_kiosk(home_page):
    return home_page.add_child(
        instance=KioskPage(
            title="Lobby Kiosk",
            slug="lobby-kiosk",
            display_template="particles",
        )
    )


@pytest.fixture
def simple_kiosk(home_page):
    return home_page.add_child(
        instance=KioskPage(
            title="Bar Display",
            slug="bar-display",
            display_template="simple",
            background_style="solid_color",
            background_color="#222222",
        )
    )


@pytest.mark.django_db
class TestKioskPageDefaults:
    def test_default_display_template(self, particles_kiosk):
        assert particles_kiosk.display_template == "particles"

    def test_default_background_style(self, particles_kiosk):
        assert particles_kiosk.background_style == "particles"

    def test_default_background_color(self, particles_kiosk):
        assert particles_kiosk.background_color == "#111111"

    def test_default_particle_settings(self, particles_kiosk):
        assert particles_kiosk.max_particles == 8
        assert particles_kiosk.spawn_interval_min == 1500
        assert particles_kiosk.spawn_interval_max == 4000


@pytest.mark.django_db
class TestKioskPageTemplateSelection:
    def test_particles_template(self, particles_kiosk):
        template = particles_kiosk.get_template()
        assert template == "pages/kiosk/kiosk_particles.html"

    def test_simple_template(self, simple_kiosk):
        template = simple_kiosk.get_template()
        assert template == "pages/kiosk/kiosk_simple.html"

    def test_unknown_template_falls_back_to_particles(self, home_page):
        kiosk = home_page.add_child(
            instance=KioskPage(
                title="Fallback",
                slug="fallback",
                display_template="nonexistent",
            )
        )
        assert kiosk.get_template() == "pages/kiosk/kiosk_particles.html"


@pytest.mark.django_db
class TestSimpleKioskConfig:
    def test_simple_kiosk_creation(self, simple_kiosk):
        assert simple_kiosk.display_template == "simple"
        assert simple_kiosk.background_style == "solid_color"
        assert simple_kiosk.background_color == "#222222"


@pytest.mark.django_db
class TestMultipleKiosks:
    def test_both_template_types_coexist(self, particles_kiosk, simple_kiosk):
        assert KioskPage.objects.count() == 2

    def test_multiple_kiosks_same_template(self, home_page):
        home_page.add_child(
            instance=KioskPage(title="Lobby", slug="lobby")
        )
        home_page.add_child(
            instance=KioskPage(title="Upstairs", slug="upstairs")
        )
        assert KioskPage.objects.count() == 2


@pytest.mark.django_db
class TestParentPageType:
    def test_parent_page_types(self):
        assert 'home.HomePage' in KioskPage.parent_page_types

    def test_no_subpage_types(self):
        assert KioskPage.subpage_types == []
