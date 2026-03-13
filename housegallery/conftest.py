import io
from unittest.mock import MagicMock

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db.models.signals import post_save
from PIL import Image as PILImage
from wagtail.models import Page as WagtailPage

from housegallery.exhibitions.models import ExhibitionsIndexPage
from housegallery.home.models import HomePage
from housegallery.images.models import CustomImage, generate_standard_renditions


@pytest.fixture(autouse=True)
def disable_rendition_signal():
    """Disconnect the rendition generation signal for all tests."""
    post_save.disconnect(generate_standard_renditions, sender=CustomImage)
    yield
    post_save.connect(generate_standard_renditions, sender=CustomImage)


@pytest.fixture
def root_page(db):
    """Get or create the Wagtail root page."""
    root = WagtailPage.objects.first()
    if root is None:
        root = WagtailPage.add_root(title="Root", slug="root")
    return root


@pytest.fixture
def home_page(root_page):
    """Create a HomePage under the root page."""
    # Remove the default Wagtail welcome page if it exists
    WagtailPage.objects.filter(slug="home", depth=2).exclude(
        content_type__model="homepage",
    ).delete()
    root_page.refresh_from_db()
    return root_page.add_child(
        instance=HomePage(title="Home", slug="home")
    )


@pytest.fixture
def exhibitions_index(home_page):
    """Create an ExhibitionsIndexPage under the home page."""
    return home_page.add_child(
        instance=ExhibitionsIndexPage(
            title="Exhibitions", slug="exhibitions"
        )
    )


@pytest.fixture
def make_image(db):
    """Factory fixture that creates a CustomImage with a minimal 1x1 PNG."""

    def _make_image(title="Test Image", alt="", credit=""):
        buf = io.BytesIO()
        img = PILImage.new("RGB", (1, 1), color="red")
        img.save(buf, format="PNG")
        buf.seek(0)

        uploaded_file = SimpleUploadedFile(
            name="test.png",
            content=buf.getvalue(),
            content_type="image/png",
        )

        image = CustomImage(title=title, file=uploaded_file)
        if alt:
            image.alt = alt
        if credit:
            image.credit = credit
        image.save()
        return image

    return _make_image


@pytest.fixture
def make_image_with_renditions():
    """Factory fixture that attaches mock renditions to an image's prefetch cache."""

    def _make_image_with_renditions(image, rendition_specs):
        """Attach mock renditions to an image.

        Args:
            image: A CustomImage instance.
            rendition_specs: List of dicts, each with keys:
                url, width, height, filter_spec.
        """
        mock_renditions = []
        for spec in rendition_specs:
            mock_rendition = MagicMock()
            mock_rendition.url = spec["url"]
            mock_rendition.width = spec["width"]
            mock_rendition.height = spec["height"]
            mock_rendition.filter_spec = spec["filter_spec"]
            mock_renditions.append(mock_rendition)

        if not hasattr(image, "_prefetched_objects_cache"):
            image._prefetched_objects_cache = {}  # noqa: SLF001
        image._prefetched_objects_cache["renditions"] = mock_renditions  # noqa: SLF001
        return mock_renditions

    return _make_image_with_renditions
