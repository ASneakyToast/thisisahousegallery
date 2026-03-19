import pytest
from django.contrib.auth.models import User
from django.test import Client
from django.urls import reverse

from housegallery.artists.models import Artist
from housegallery.artworks.forms import BulkArtworkDefaultsForm
from housegallery.artworks.forms import BulkArtworkFormSet
from housegallery.artworks.forms import BulkArtworkRowForm
from housegallery.artworks.models import Artwork
from housegallery.artworks.models import ArtworkArtist
from housegallery.artworks.models import ArtworkImage

BULK_ADD_URL_NAME = "wagtailsnippets_artworks_artwork:bulk_add"


@pytest.fixture
def staff_user(db):
    return User.objects.create_superuser(username="staff", password="testpass")


@pytest.fixture
def regular_user(db):
    return User.objects.create_user(
        username="regular", password="testpass", is_staff=False,
    )


@pytest.fixture
def staff_client(staff_user):
    client = Client()
    client.login(username="staff", password="testpass")
    return client


@pytest.fixture
def artist(db):
    a = Artist(name="Test Artist")
    a.save()
    rev = a.save_revision()
    rev.publish()
    return a


@pytest.fixture
def artist2(db):
    a = Artist(name="Second Artist")
    a.save()
    rev = a.save_revision()
    rev.publish()
    return a


@pytest.fixture
def bulk_add_url():
    return reverse(BULK_ADD_URL_NAME)


def _management_form_data(total=5, initial=5):
    """Return Django formset management form data."""
    return {
        "form-TOTAL_FORMS": str(total),
        "form-INITIAL_FORMS": str(initial),
        "form-MIN_NUM_FORMS": "0",
        "form-MAX_NUM_FORMS": "50",
    }


def _row_data(index, **kwargs):
    """Build POST data for a single formset row."""
    prefix = f"form-{index}"
    data = {}
    for field in [
        "title", "image", "description", "width_inches", "height_inches",
        "depth_inches", "size", "price", "materials",
    ]:
        data[f"{prefix}-{field}"] = kwargs.get(field, "")
    return data


# =============================================================================
# Phase 1: Form Unit Tests
# =============================================================================


@pytest.mark.django_db
class TestBulkArtworkDefaultsForm:
    def test_valid_when_empty(self):
        form = BulkArtworkDefaultsForm(data={})
        assert form.is_valid()

    def test_validates_artist_queryset(self, artist):
        form = BulkArtworkDefaultsForm(data={"artists": [artist.pk]})
        assert form.is_valid()

    def test_rejects_nonexistent_artist(self):
        form = BulkArtworkDefaultsForm(data={"artists": [99999]})
        assert not form.is_valid()
        assert "artists" in form.errors


@pytest.mark.django_db
class TestBulkArtworkRowForm:
    def test_valid_with_title_only(self):
        form = BulkArtworkRowForm(data={"title": "My Artwork"})
        assert form.is_valid()

    def test_valid_when_completely_empty(self):
        form = BulkArtworkRowForm(data={})
        assert form.is_valid()

    def test_validates_image_fk(self):
        form = BulkArtworkRowForm(data={"title": "Test", "image": 99999})
        assert not form.is_valid()
        assert "image" in form.errors

    def test_validates_image_fk_exists(self, make_image):
        image = make_image(title="Valid Image")
        form = BulkArtworkRowForm(data={"title": "Test", "image": image.pk})
        assert form.is_valid()

    def test_rejects_negative_dimensions(self):
        form = BulkArtworkRowForm(data={"title": "Test", "width_inches": "-5"})
        assert not form.is_valid()
        assert "width_inches" in form.errors

    def test_is_empty_helper(self):
        form = BulkArtworkRowForm(data={})
        form.is_valid()
        assert form.is_empty()

    def test_is_not_empty_with_title(self):
        form = BulkArtworkRowForm(data={"title": "Something"})
        form.is_valid()
        assert not form.is_empty()


@pytest.mark.django_db
class TestBulkArtworkFormSet:
    def test_rejects_all_empty_rows(self):
        data = _management_form_data(total=2, initial=0)
        data.update(_row_data(0))
        data.update(_row_data(1))
        formset = BulkArtworkFormSet(data)
        assert not formset.is_valid()

    def test_accepts_one_filled_row(self):
        data = _management_form_data(total=2, initial=0)
        data.update(_row_data(0, title="Artwork 1"))
        data.update(_row_data(1))
        formset = BulkArtworkFormSet(data)
        assert formset.is_valid()

    def test_ignores_empty_rows(self):
        data = _management_form_data(total=3, initial=0)
        data.update(_row_data(0, title="Artwork 1"))
        data.update(_row_data(1))
        data.update(_row_data(2, title="Artwork 3"))
        formset = BulkArtworkFormSet(data)
        assert formset.is_valid()


# =============================================================================
# Phase 2: View Access Tests
# =============================================================================


@pytest.mark.django_db
class TestBulkAddViewAccess:
    def test_unauthenticated_denied(self, bulk_add_url):
        client = Client()
        response = client.get(bulk_add_url)
        # Should redirect to login or return 302/403
        assert response.status_code in (302, 403)

    def test_non_staff_denied(self, regular_user, bulk_add_url):
        client = Client()
        client.login(username="regular", password="testpass")
        response = client.get(bulk_add_url)
        assert response.status_code in (302, 403)

    def test_staff_get_renders_form(self, staff_client, bulk_add_url):
        response = staff_client.get(bulk_add_url)
        assert response.status_code == 200
        content = response.content.decode()
        assert "Bulk Add Artworks" in content
        assert "form-TOTAL_FORMS" in content


# =============================================================================
# Phase 3: Integration Tests (Creation Flow)
# =============================================================================


@pytest.mark.django_db
class TestBulkAddCreation:
    def _post_bulk(self, client, url, rows, defaults=None, action="draft"):
        """Helper to POST bulk add form data."""
        data = _management_form_data(total=len(rows), initial=0)
        if defaults:
            data.update(defaults)
        for i, row in enumerate(rows):
            data.update(_row_data(i, **row))
        data["action"] = action
        return client.post(url, data)

    def test_create_single_draft(self, staff_client, bulk_add_url):
        response = self._post_bulk(
            staff_client, bulk_add_url, [{"title": "Draft Artwork"}], action="draft",
        )
        assert response.status_code == 302
        artwork = Artwork.objects.get()
        assert artwork.live is False
        assert "<p>Draft Artwork</p>" in artwork.title

    def test_create_multiple_drafts(self, staff_client, bulk_add_url):
        rows = [
            {"title": "Artwork 1"},
            {"title": "Artwork 2"},
            {"title": "Artwork 3"},
        ]
        response = self._post_bulk(staff_client, bulk_add_url, rows, action="draft")
        assert response.status_code == 302
        assert Artwork.objects.count() == 3

    def test_create_published(self, staff_client, bulk_add_url):
        response = self._post_bulk(
            staff_client, bulk_add_url, [{"title": "Published Art"}], action="publish",
        )
        assert response.status_code == 302
        artwork = Artwork.objects.get()
        assert artwork.live is True
        assert artwork.first_published_at is not None

    def test_artist_assigned_from_defaults(self, staff_client, bulk_add_url, artist):
        defaults = {"artists": [str(artist.pk)]}
        response = self._post_bulk(
            staff_client, bulk_add_url, [{"title": "With Artist"}], defaults=defaults,
        )
        assert response.status_code == 302
        artwork = Artwork.objects.get()
        assert ArtworkArtist.objects.filter(artwork=artwork, artist=artist).exists()

    def test_multiple_artists_assigned(
        self, staff_client, bulk_add_url, artist, artist2,
    ):
        defaults = {"artists": [str(artist.pk), str(artist2.pk)]}
        response = self._post_bulk(
            staff_client, bulk_add_url, [{"title": "Multi Artist"}], defaults=defaults,
        )
        assert response.status_code == 302
        artwork = Artwork.objects.get()
        assert artwork.artwork_artists.count() == 2

    def test_materials_assigned_from_defaults(self, staff_client, bulk_add_url):
        defaults = {"materials": "oil, canvas"}
        response = self._post_bulk(
            staff_client, bulk_add_url, [{"title": "With Materials"}], defaults=defaults,
        )
        assert response.status_code == 302
        artwork = Artwork.objects.get()
        tag_names = sorted([t.name for t in artwork.materials.all()])
        assert tag_names == ["canvas", "oil"]

    def test_image_assigned(self, staff_client, bulk_add_url, make_image):
        image = make_image(title="Artwork Image")
        response = self._post_bulk(
            staff_client,
            bulk_add_url,
            [{"title": "With Image", "image": str(image.pk)}],
        )
        assert response.status_code == 302
        artwork = Artwork.objects.get()
        assert ArtworkImage.objects.filter(artwork=artwork, image=image).exists()

    def test_dimensions_saved(self, staff_client, bulk_add_url):
        response = self._post_bulk(
            staff_client,
            bulk_add_url,
            [
                {
                    "title": "Sized",
                    "width_inches": "24.5",
                    "height_inches": "36",
                    "depth_inches": "1.25",
                },
            ],
        )
        assert response.status_code == 302
        artwork = Artwork.objects.get()
        assert float(artwork.width_inches) == 24.5
        assert float(artwork.height_inches) == 36.0
        assert float(artwork.depth_inches) == 1.25

    def test_title_wrapped_in_p_tags(self, staff_client, bulk_add_url):
        response = self._post_bulk(
            staff_client, bulk_add_url, [{"title": "My Title"}],
        )
        assert response.status_code == 302
        artwork = Artwork.objects.get()
        assert artwork.title == "<p>My Title</p>"

    def test_row_override_beats_default(self, staff_client, bulk_add_url):
        defaults = {"price": "$100", "materials": "oil"}
        rows = [
            {"title": "Default Price"},
            {"title": "Custom Price", "price": "$500", "materials": "acrylic"},
        ]
        response = self._post_bulk(
            staff_client, bulk_add_url, rows, defaults=defaults,
        )
        assert response.status_code == 302
        default_art = Artwork.objects.get(title="<p>Default Price</p>")
        custom_art = Artwork.objects.get(title="<p>Custom Price</p>")
        assert default_art.price == "$100"
        assert custom_art.price == "$500"
        assert "oil" in [t.name for t in default_art.materials.all()]
        assert "acrylic" in [t.name for t in custom_art.materials.all()]
        assert "oil" not in [t.name for t in custom_art.materials.all()]

    def test_success_message(self, staff_client, bulk_add_url):
        response = self._post_bulk(
            staff_client,
            bulk_add_url,
            [{"title": "Art 1"}, {"title": "Art 2"}],
            action="draft",
        )
        assert response.status_code == 302
        # Follow the redirect and check messages
        response = staff_client.get(response.url)
        content = response.content.decode()
        assert "Created 2 artworks" in content

    def test_redirects_to_list(self, staff_client, bulk_add_url):
        response = self._post_bulk(
            staff_client, bulk_add_url, [{"title": "Art"}], action="draft",
        )
        assert response.status_code == 302
        assert reverse("wagtailsnippets_artworks_artwork:list") in response.url


# =============================================================================
# Phase 4: Edge Cases
# =============================================================================


@pytest.mark.django_db
class TestBulkAddEdgeCases:
    def _post_bulk(self, client, url, rows, defaults=None, action="draft"):
        data = _management_form_data(total=len(rows), initial=0)
        if defaults:
            data.update(defaults)
        for i, row in enumerate(rows):
            data.update(_row_data(i, **row))
        data["action"] = action
        return client.post(url, data)

    def test_all_empty_shows_error(self, staff_client, bulk_add_url):
        response = self._post_bulk(staff_client, bulk_add_url, [{}])
        assert response.status_code == 200  # re-renders form
        assert Artwork.objects.count() == 0

    def test_atomic_rollback(self, staff_client, bulk_add_url, make_image):
        """If validation fails in the view, no artworks should be created."""
        image = make_image(title="Valid Image")
        # Submit with one valid row and one with a bad image FK
        data = _management_form_data(total=2, initial=0)
        data.update(_row_data(0, title="Good", image=str(image.pk)))
        data.update(_row_data(1, title="Bad", image="99999"))
        data["action"] = "draft"
        response = staff_client.post(bulk_add_url, data)
        assert response.status_code == 200  # re-renders with errors
        assert Artwork.objects.count() == 0

    def test_revision_captures_relations(
        self, staff_client, bulk_add_url, artist, make_image,
    ):
        image = make_image(title="Rev Image")
        defaults = {"artists": [str(artist.pk)], "materials": "bronze"}
        response = self._post_bulk(
            staff_client,
            bulk_add_url,
            [{"title": "Revisioned", "image": str(image.pk)}],
            defaults=defaults,
            action="publish",
        )
        assert response.status_code == 302
        artwork = Artwork.objects.get()
        revision = artwork.revisions.order_by("-created_at").first()
        assert revision is not None
        rev_data = revision.content
        if isinstance(rev_data, str):
            import json
            rev_data = json.loads(rev_data)
        # Revision should contain artist and image relations
        assert "artwork_artists" in rev_data
        assert "artwork_images" in rev_data
        assert len(rev_data["artwork_artists"]) == 1
        assert len(rev_data["artwork_images"]) == 1

    def test_existing_artworks_unchanged(self, staff_client, bulk_add_url):
        # Create a pre-existing artwork
        existing = Artwork(title="<p>Existing</p>", price="$999")
        existing.save()
        existing.save_revision()

        self._post_bulk(staff_client, bulk_add_url, [{"title": "New Art"}])

        existing.refresh_from_db()
        assert existing.title == "<p>Existing</p>"
        assert existing.price == "$999"
        assert Artwork.objects.count() == 2

    def test_title_html_escaped(self, staff_client, bulk_add_url):
        response = self._post_bulk(
            staff_client, bulk_add_url, [{"title": "<script>alert('xss')</script>"}],
        )
        assert response.status_code == 302
        artwork = Artwork.objects.get()
        assert "<script>" not in artwork.title
        assert "&lt;script&gt;" in artwork.title

    def test_empty_rows_skipped(self, staff_client, bulk_add_url):
        """Empty rows in the middle should be silently skipped."""
        rows = [
            {"title": "First"},
            {},  # empty
            {"title": "Third"},
            {},  # empty
        ]
        response = self._post_bulk(staff_client, bulk_add_url, rows)
        assert response.status_code == 302
        assert Artwork.objects.count() == 2

    def test_date_from_defaults(self, staff_client, bulk_add_url):
        defaults = {"date": "2024-06-15"}
        response = self._post_bulk(
            staff_client, bulk_add_url, [{"title": "Dated"}], defaults=defaults,
        )
        assert response.status_code == 302
        artwork = Artwork.objects.get()
        assert artwork.date is not None
        assert artwork.date.year == 2024
        assert artwork.date.month == 6
        assert artwork.date.day == 15
