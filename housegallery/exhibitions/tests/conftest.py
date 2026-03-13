import datetime

import pytest

from housegallery.artworks.models import Artwork, ArtworkImage
from housegallery.exhibitions.models import (
    ExhibitionArtwork,
    ExhibitionPage,
    ExhibitionPhoto,
    InProgressPhoto,
    InstallationPhoto,
    OpeningReceptionPhoto,
    ShowcardPhoto,
)


@pytest.fixture
def exhibition_page(exhibitions_index):
    """Published ExhibitionPage with dates."""
    page = exhibitions_index.add_child(
        instance=ExhibitionPage(
            title="Test Exhibition",
            slug="test-exhibition",
            start_date=datetime.date(2024, 3, 1),
            end_date=datetime.date(2024, 4, 30),
        )
    )
    # Must publish to set last_published_at (used in cache keys)
    revision = page.save_revision()
    revision.publish()
    page.refresh_from_db()
    return page


@pytest.fixture
def make_installation_photo(make_image):
    """Factory for InstallationPhoto objects."""
    def _factory(page, **kwargs):
        image = make_image(title=kwargs.pop("title", "Installation Photo"))
        return InstallationPhoto.objects.create(page=page, image=image, **kwargs)
    return _factory


@pytest.fixture
def make_opening_photo(make_image):
    """Factory for OpeningReceptionPhoto objects."""
    def _factory(page, **kwargs):
        image = make_image(title=kwargs.pop("title", "Opening Photo"))
        return OpeningReceptionPhoto.objects.create(page=page, image=image, **kwargs)
    return _factory


@pytest.fixture
def make_showcard_photo(make_image):
    """Factory for ShowcardPhoto objects."""
    def _factory(page, **kwargs):
        image = make_image(title=kwargs.pop("title", "Showcard Photo"))
        return ShowcardPhoto.objects.create(page=page, image=image, **kwargs)
    return _factory


@pytest.fixture
def make_in_progress_photo(make_image):
    """Factory for InProgressPhoto objects."""
    def _factory(page, **kwargs):
        image = make_image(title=kwargs.pop("title", "In Progress Photo"))
        return InProgressPhoto.objects.create(page=page, image=image, **kwargs)
    return _factory


@pytest.fixture
def make_exhibition_photo(make_image):
    """Factory for ExhibitionPhoto (new unified model) objects with optional tags."""
    def _factory(page, tags=None, **kwargs):
        image = make_image(title=kwargs.pop("title", "Exhibition Photo"))
        if tags:
            for tag in tags:
                image.tags.add(tag)
        return ExhibitionPhoto.objects.create(page=page, image=image, **kwargs)
    return _factory


@pytest.fixture
def make_exhibition_artwork(make_image):
    """Factory that creates an Artwork with an image and links it to an ExhibitionPage."""
    def _factory(page, artwork_title="Test Artwork", **kwargs):
        artwork = Artwork(title=artwork_title)
        artwork.save()
        image = make_image(title=f"{artwork_title} Image")
        ArtworkImage.objects.create(artwork=artwork, image=image)
        ExhibitionArtwork.objects.create(page=page, artwork=artwork)
        return artwork
    return _factory
