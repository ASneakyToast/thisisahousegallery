from unittest.mock import MagicMock, patch

import pytest

from housegallery.artists.models import Artist
from housegallery.artworks.models import Artwork, ArtworkArtist, ArtworkImage
from housegallery.images.models import CustomImage
from housegallery.kiosk.models import KioskPage


CAROUSEL_ITEM_KEYS = {
    "thumb_url",
    "full_url",
    "srcset",
    "sizes",
    "caption",
    "image_type",
    "artwork_title",
    "artwork_artist",
    "artwork_date",
    "artwork_materials",
    "artwork_size",
    "exhibition_title",
    "exhibition_date",
    "image_credit",
}

DUMMY_CACHE = {"default": {"BACKEND": "django.core.cache.backends.dummy.DummyCache"}}

MOCK_URLS_TUPLE = ("/media/thumb.jpg", "/media/full.jpg", "/media/thumb.jpg 400w, /media/full.jpg 1440w", "(max-width: 600px) 400px, 1440px")


@pytest.fixture
def kiosk_page(home_page):
    return home_page.add_child(
        instance=KioskPage(
            title="Carousel Kiosk",
            slug="carousel-kiosk",
            display_template="split",
        )
    )


@pytest.mark.django_db
class TestArtworkToCarouselItems:

    def test_empty_when_no_artwork(self, kiosk_page):
        result = kiosk_page._artwork_to_carousel_items({"artwork": None})
        assert result == []

    def test_one_item_per_artwork_image(self, kiosk_page, make_image):
        artwork = Artwork(title="Two Images")
        artwork.save()
        img1 = make_image(title="Image 1")
        img2 = make_image(title="Image 2")
        ArtworkImage.objects.create(artwork=artwork, image=img1)
        ArtworkImage.objects.create(artwork=artwork, image=img2)

        with patch.object(kiosk_page, "_get_image_urls", return_value=MOCK_URLS_TUPLE):
            result = kiosk_page._artwork_to_carousel_items({"artwork": artwork})

        assert len(result) == 2

    def test_dict_has_all_required_keys(self, kiosk_page, make_image):
        artwork = Artwork(title="Key Check")
        artwork.save()
        img = make_image(title="Key Image")
        ArtworkImage.objects.create(artwork=artwork, image=img)

        with patch.object(kiosk_page, "_get_image_urls", return_value=MOCK_URLS_TUPLE):
            result = kiosk_page._artwork_to_carousel_items({"artwork": artwork})

        assert len(result) == 1
        assert set(result[0].keys()) == CAROUSEL_ITEM_KEYS

    def test_metadata_populated(self, kiosk_page, make_image):
        artwork = Artwork(title="Painting A")
        artwork.save()
        img = make_image(title="Painting Image")
        ArtworkImage.objects.create(artwork=artwork, image=img)

        with patch.object(kiosk_page, "_get_image_urls", return_value=MOCK_URLS_TUPLE):
            result = kiosk_page._artwork_to_carousel_items({"artwork": artwork})

        assert result[0]["artwork_title"] == "Painting A"
        assert result[0]["image_type"] == "artwork"

    def test_caption_fallback(self, kiosk_page, make_image):
        artwork = Artwork(title="Fallback Title")
        artwork.save()
        img = make_image(title="Some Image")
        ArtworkImage.objects.create(artwork=artwork, image=img, caption="")

        with patch.object(kiosk_page, "_get_image_urls", return_value=MOCK_URLS_TUPLE):
            result = kiosk_page._artwork_to_carousel_items({"artwork": artwork})

        assert result[0]["caption"] == "Fallback Title"

    def test_caption_uses_explicit_value(self, kiosk_page, make_image):
        artwork = Artwork(title="Artwork Title")
        artwork.save()
        img = make_image(title="Some Image")
        ArtworkImage.objects.create(artwork=artwork, image=img, caption="Explicit Caption")

        with patch.object(kiosk_page, "_get_image_urls", return_value=MOCK_URLS_TUPLE):
            result = kiosk_page._artwork_to_carousel_items({"artwork": artwork})

        assert result[0]["caption"] == "Explicit Caption"

    def test_artist_names_populated(self, kiosk_page, make_image):
        artwork = Artwork(title="Collaborative")
        artwork.save()
        artist = Artist.objects.create(name="Jane Doe")
        ArtworkArtist.objects.create(artwork=artwork, artist=artist)
        img = make_image(title="Collab Image")
        ArtworkImage.objects.create(artwork=artwork, image=img)

        with patch.object(kiosk_page, "_get_image_urls", return_value=MOCK_URLS_TUPLE):
            result = kiosk_page._artwork_to_carousel_items({"artwork": artwork})

        assert result[0]["artwork_artist"] == "Jane Doe"

    def test_image_credit_from_image_model(self, kiosk_page, make_image):
        artwork = Artwork(title="Credit Test")
        artwork.save()
        img = make_image(title="Credited Image", credit="Photo by Alice")
        ArtworkImage.objects.create(artwork=artwork, image=img)

        with patch.object(kiosk_page, "_get_image_urls", return_value=MOCK_URLS_TUPLE):
            result = kiosk_page._artwork_to_carousel_items({"artwork": artwork})

        assert result[0]["image_credit"] == "Photo by Alice"


@pytest.mark.django_db
class TestExhibitionToCarouselItems:

    def test_empty_when_no_exhibition(self, kiosk_page):
        result = kiosk_page._exhibition_to_carousel_items({"exhibition": None})
        assert result == []

    def test_returns_items_from_gallery_images(self, kiosk_page):
        mock_exhibition = MagicMock()
        mock_exhibition.specific = mock_exhibition
        mock_exhibition.title = "Test Show"
        mock_exhibition.get_formatted_date_month_year.return_value = "03.2024"
        mock_exhibition.get_all_gallery_images.return_value = [
            {
                "thumb_url": "/t1.jpg", "full_url": "/f1.jpg",
                "srcset": "", "sizes": "",
                "caption": "Photo 1", "type": "exhibition",
                "credit": "Bob",
            },
            {
                "thumb_url": "/t2.jpg", "full_url": "/f2.jpg",
                "srcset": "", "sizes": "",
                "caption": "Photo 2", "type": "opening",
                "credit": "",
            },
        ]

        result = kiosk_page._exhibition_to_carousel_items(
            {"exhibition": mock_exhibition},
        )

        assert len(result) == 2
        assert result[0]["exhibition_title"] == "Test Show"
        assert result[0]["exhibition_date"] == "03.2024"
        assert result[0]["thumb_url"] == "/t1.jpg"

    def test_max_images_limit(self, kiosk_page):
        mock_exhibition = MagicMock()
        mock_exhibition.specific = mock_exhibition
        mock_exhibition.title = "Big Show"
        mock_exhibition.get_formatted_date_month_year.return_value = ""
        mock_exhibition.get_all_gallery_images.return_value = [
            {"thumb_url": f"/t{i}.jpg", "full_url": f"/f{i}.jpg",
             "srcset": "", "sizes": "",
             "caption": f"P{i}", "type": "exhibition", "credit": ""}
            for i in range(10)
        ]

        result = kiosk_page._exhibition_to_carousel_items(
            {"exhibition": mock_exhibition, "max_images": 2},
        )

        assert len(result) == 2

    def test_filters_by_image_categories(self, kiosk_page):
        mock_exhibition = MagicMock()
        mock_exhibition.specific = mock_exhibition
        mock_exhibition.title = "Filtered Show"
        mock_exhibition.get_formatted_date_month_year.return_value = ""
        mock_exhibition.get_all_gallery_images.return_value = [
            {"thumb_url": "/t1.jpg", "full_url": "/f1.jpg",
             "srcset": "", "sizes": "",
             "caption": "Install", "type": "exhibition", "credit": "",
             "related_artwork": None},
            {"thumb_url": "/t2.jpg", "full_url": "/f2.jpg",
             "srcset": "", "sizes": "",
             "caption": "Opening", "type": "opening", "credit": "",
             "related_artwork": None},
        ]

        result = kiosk_page._exhibition_to_carousel_items(
            {"exhibition": mock_exhibition, "image_categories": ["exhibition"]},
        )

        assert len(result) == 1
        assert result[0]["caption"] == "Install"


@pytest.mark.django_db
class TestArtistToCarouselItems:

    def test_empty_when_no_artist(self, kiosk_page):
        result = kiosk_page._artist_to_carousel_items({"artist": None})
        assert result == []

    def test_includes_all_artworks(self, kiosk_page, make_image):
        artist = Artist.objects.create(name="Multi-work Artist")
        artwork1 = Artwork(title="Work 1")
        artwork1.save()
        artwork2 = Artwork(title="Work 2")
        artwork2.save()

        ArtworkArtist.objects.create(artwork=artwork1, artist=artist)
        ArtworkArtist.objects.create(artwork=artwork2, artist=artist)

        img1 = make_image(title="W1 Image")
        img2 = make_image(title="W2 Image")
        ArtworkImage.objects.create(artwork=artwork1, image=img1)
        ArtworkImage.objects.create(artwork=artwork2, image=img2)

        with patch.object(kiosk_page, "_get_image_urls", return_value=MOCK_URLS_TUPLE):
            result = kiosk_page._artist_to_carousel_items({"artist": artist})

        assert len(result) == 2
        titles = {item["artwork_title"] for item in result}
        assert titles == {"Work 1", "Work 2"}


@pytest.mark.django_db
class TestImageToCarouselItem:

    def test_none_when_no_image(self, kiosk_page):
        result = kiosk_page._image_to_carousel_item({"image": None})
        assert result is None

    def test_dict_has_all_keys(self, kiosk_page, make_image):
        img = make_image(title="Single Image")

        with patch.object(kiosk_page, "_get_image_urls", return_value=MOCK_URLS_TUPLE):
            result = kiosk_page._image_to_carousel_item({"image": img})

        assert result is not None
        assert set(result.keys()) == CAROUSEL_ITEM_KEYS

    def test_caption_from_value(self, kiosk_page, make_image):
        img = make_image(title="Ignored Title")

        with patch.object(kiosk_page, "_get_image_urls", return_value=MOCK_URLS_TUPLE):
            result = kiosk_page._image_to_carousel_item(
                {"image": img, "caption": "My Caption"},
            )

        assert result["caption"] == "My Caption"

    def test_caption_from_title(self, kiosk_page, make_image):
        img = make_image(title="Image Title")

        with patch.object(kiosk_page, "_get_image_urls", return_value=MOCK_URLS_TUPLE):
            result = kiosk_page._image_to_carousel_item({"image": img})

        assert result["caption"] == "Image Title"

    def test_image_credit_from_model(self, kiosk_page, make_image):
        img = make_image(title="Credited", credit="Photographer X")

        with patch.object(kiosk_page, "_get_image_urls", return_value=MOCK_URLS_TUPLE):
            result = kiosk_page._image_to_carousel_item({"image": img})

        assert result["image_credit"] == "Photographer X"


@pytest.mark.django_db
class TestKioskGetImageUrls:

    def test_returns_four_element_tuple(self, kiosk_page, make_image):
        img = make_image(title="Tuple Test")

        with patch("housegallery.core.image_utils.get_image_urls") as mock_urls:
            mock_urls.return_value = {
                "thumb_url": "/thumb.jpg", "medium_url": "/med.jpg",
                "full_url": "/full.jpg", "original_url": "/orig.jpg",
                "srcset": "srcset_val", "sizes": "sizes_val",
                "width": 100, "height": 100,
                "alt": "", "credit": "", "title": "",
            }
            result = kiosk_page._get_image_urls(img)

        assert isinstance(result, tuple)
        assert len(result) == 4

    def test_delegates_to_core_utility(self, kiosk_page, make_image):
        img = make_image(title="Delegate Test")

        with patch("housegallery.core.image_utils.get_image_urls") as mock_urls:
            mock_urls.return_value = {
                "thumb_url": "/thumb.jpg", "medium_url": "/med.jpg",
                "full_url": "/full.jpg", "original_url": "/orig.jpg",
                "srcset": "", "sizes": "",
                "width": 100, "height": 100,
                "alt": "", "credit": "", "title": "",
            }
            kiosk_page._get_image_urls(img)
            mock_urls.assert_called_once_with(img)

    def test_falls_back_to_original_url(self, kiosk_page, make_image):
        img = make_image(title="Fallback Test")

        with patch("housegallery.core.image_utils.get_image_urls") as mock_urls:
            mock_urls.return_value = {
                "thumb_url": "", "medium_url": "",
                "full_url": "", "original_url": "/orig.jpg",
                "srcset": "", "sizes": "",
                "width": 100, "height": 100,
                "alt": "", "credit": "", "title": "",
            }
            thumb, full, srcset, sizes = kiosk_page._get_image_urls(img)

        assert thumb == "/orig.jpg"
        assert full == "/orig.jpg"


@pytest.mark.django_db
class TestImagesetToCarouselItems:

    def test_tagged_set_empty_when_no_tag(self, kiosk_page):
        block = MagicMock()
        block.block_type = "tagged_set"
        block.value = {"tag": ""}

        result = kiosk_page._imageset_to_carousel_items(block)
        assert result == []

    def test_tagged_set_returns_matching_images(self, kiosk_page, make_image):
        img1 = make_image(title="Tagged 1")
        img1.tags.add("kiosk-display")
        img2 = make_image(title="Tagged 2")
        img2.tags.add("kiosk-display")
        make_image(title="Other Tag")

        block = MagicMock()
        block.block_type = "tagged_set"
        block.value = {"tag": "kiosk-display"}

        with patch.object(kiosk_page, "_get_image_urls", return_value=MOCK_URLS_TUPLE):
            result = kiosk_page._imageset_to_carousel_items(block)

        assert len(result) == 2

    def test_all_images_respects_limit(self, kiosk_page, make_image):
        for i in range(5):
            make_image(title=f"Lim {i}")

        block = MagicMock()
        block.block_type = "all_images"
        block.value = {"limit": 2}

        with patch.object(kiosk_page, "_get_image_urls", return_value=MOCK_URLS_TUPLE):
            result = kiosk_page._imageset_to_carousel_items(block)

        assert len(result) == 2

    def test_imageset_item_has_all_keys(self, kiosk_page, make_image):
        img = make_image(title="Key Check Image")
        img.tags.add("test-tag")

        block = MagicMock()
        block.block_type = "tagged_set"
        block.value = {"tag": "test-tag"}

        with patch.object(kiosk_page, "_get_image_urls", return_value=MOCK_URLS_TUPLE):
            result = kiosk_page._imageset_to_carousel_items(block)

        assert len(result) == 1
        assert set(result[0].keys()) == CAROUSEL_ITEM_KEYS


@pytest.mark.django_db
class TestGetCarouselItems:

    @pytest.fixture(autouse=True)
    def _use_dummy_cache(self, settings):
        settings.CACHES = DUMMY_CACHE

    def test_empty_when_no_stream(self, kiosk_page):
        result = kiosk_page.get_carousel_items()
        assert result == []



@pytest.mark.django_db
class TestGetCarouselItemsCache:
    """Caching tests need a real cache backend (not DummyCache)."""

    @pytest.fixture(autouse=True)
    def _use_locmem_cache(self):
        from django.test.utils import override_settings
        with override_settings(CACHES={
            "default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"},
        }):
            yield

    def test_caches_with_pk_and_timestamp(self, home_page):
        from django.core.cache import cache

        kiosk = home_page.add_child(
            instance=KioskPage(
                title="Cache Kiosk", slug="cache-kiosk",
                display_template="split",
            )
        )
        revision = kiosk.save_revision()
        revision.publish()
        kiosk.refresh_from_db()

        # First call populates cache
        result1 = kiosk.get_carousel_items()
        assert result1 == []

        # Verify cache key format
        timestamp = int(kiosk.last_published_at.timestamp())
        cache_key = f"kiosk_carousel_{kiosk.pk}_{timestamp}"
        cached = cache.get(cache_key)
        assert cached is not None
