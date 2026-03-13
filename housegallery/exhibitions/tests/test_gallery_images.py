from unittest.mock import patch

import pytest


DUMMY_CACHE = {"default": {"BACKEND": "django.core.cache.backends.dummy.DummyCache"}}

MOCK_IMAGE_URLS = {
    "thumb_url": "/media/test_thumb.jpg",
    "medium_url": "/media/test_medium.jpg",
    "full_url": "/media/test_full.jpg",
    "original_url": "/media/test_original.jpg",
    "srcset": "/media/test_thumb.jpg 400w, /media/test_medium.jpg 800w",
    "sizes": "(max-width: 600px) 400px, (max-width: 1200px) 800px, 1440px",
    "width": 1440,
    "height": 960,
    "alt": "Test Image",
    "credit": "Test Credit",
    "title": "Test Image",
}


def _mock_get_image_urls(image_obj, specs=None):
    """Return predictable image URL dict, using actual image metadata."""
    return {
        **MOCK_IMAGE_URLS,
        "title": image_obj.title or "Test Image",
        "alt": getattr(image_obj, "alt", "") or image_obj.title or "",
        "credit": getattr(image_obj, "credit", "") or "",
    }


@pytest.mark.django_db
class TestGetAllGalleryImages:
    """Tests for ExhibitionPage.get_all_gallery_images()."""

    @pytest.fixture(autouse=True)
    def _patch_image_urls(self, settings):
        settings.CACHES = DUMMY_CACHE
        with patch(
            "housegallery.core.image_utils.get_image_urls",
            side_effect=_mock_get_image_urls,
        ):
            yield

    def test_empty_list_when_no_images(self, exhibition_page):
        result = exhibition_page.get_all_gallery_images()
        assert result == []

    def test_includes_installation_photos(self, exhibition_page, make_installation_photo):
        make_installation_photo(exhibition_page, title="Install 1")
        make_installation_photo(exhibition_page, title="Install 2")
        result = exhibition_page.get_all_gallery_images()
        assert len(result) == 2
        assert all(img["type"] == "exhibition" for img in result)

    def test_includes_opening_photos(self, exhibition_page, make_opening_photo):
        make_opening_photo(exhibition_page, title="Opening 1")
        result = exhibition_page.get_all_gallery_images()
        assert len(result) == 1
        assert result[0]["type"] == "opening"

    def test_includes_showcard_photos(self, exhibition_page, make_showcard_photo):
        make_showcard_photo(exhibition_page, title="Showcard 1")
        result = exhibition_page.get_all_gallery_images()
        assert len(result) == 1
        assert result[0]["type"] == "showcards"

    def test_includes_in_progress_photos(self, exhibition_page, make_in_progress_photo):
        make_in_progress_photo(exhibition_page, title="InProg 1")
        result = exhibition_page.get_all_gallery_images()
        assert len(result) == 1
        assert result[0]["type"] == "in_progress"

    def test_includes_unified_exhibition_photos_default_type(
        self, exhibition_page, make_exhibition_photo,
    ):
        make_exhibition_photo(exhibition_page, title="Unified Photo")
        result = exhibition_page.get_all_gallery_images()
        assert len(result) == 1
        assert result[0]["type"] == "exhibition"  # Default when no tags

    def test_tag_based_categorization_installation(
        self, exhibition_page, make_exhibition_photo,
    ):
        make_exhibition_photo(exhibition_page, tags=["installation"])
        result = exhibition_page.get_all_gallery_images()
        unified = [r for r in result if r["type"] == "exhibition"]
        assert len(unified) == 1

    def test_tag_based_categorization_opening(
        self, exhibition_page, make_exhibition_photo,
    ):
        make_exhibition_photo(exhibition_page, tags=["opening-reception"])
        result = exhibition_page.get_all_gallery_images()
        assert any(r["type"] == "opening" for r in result)

    def test_tag_based_categorization_showcard(
        self, exhibition_page, make_exhibition_photo,
    ):
        make_exhibition_photo(exhibition_page, tags=["showcard"])
        result = exhibition_page.get_all_gallery_images()
        assert any(r["type"] == "showcards" for r in result)

    def test_tag_based_categorization_in_progress(
        self, exhibition_page, make_exhibition_photo,
    ):
        make_exhibition_photo(exhibition_page, tags=["in-progress"])
        result = exhibition_page.get_all_gallery_images()
        assert any(r["type"] == "in_progress" for r in result)

    def test_caption_override_on_unified_photos(
        self, exhibition_page, make_exhibition_photo,
    ):
        make_exhibition_photo(
            exhibition_page, title="Original", caption="Custom Caption",
        )
        result = exhibition_page.get_all_gallery_images()
        assert result[0]["caption"] == "Custom Caption"

    def test_output_dict_structure(self, exhibition_page, make_installation_photo):
        make_installation_photo(exhibition_page)
        result = exhibition_page.get_all_gallery_images()
        assert len(result) == 1
        expected_keys = {
            "image_title", "caption", "credit", "type",
            "thumb_url", "full_url", "thumb_webp_url", "full_webp_url",
            "srcset", "sizes",
        }
        assert expected_keys.issubset(set(result[0].keys()))

    def test_multiple_types_combined(
        self, exhibition_page,
        make_installation_photo, make_opening_photo,
        make_showcard_photo, make_in_progress_photo,
    ):
        make_installation_photo(exhibition_page)
        make_opening_photo(exhibition_page)
        make_showcard_photo(exhibition_page)
        make_in_progress_photo(exhibition_page)
        result = exhibition_page.get_all_gallery_images()
        assert len(result) == 4
        types = [img["type"] for img in result]
        assert "exhibition" in types
        assert "opening" in types
        assert "showcards" in types
        assert "in_progress" in types


@pytest.mark.django_db
class TestGetImagesByType:
    """Tests for ExhibitionPage.get_images_by_type()."""

    @pytest.fixture(autouse=True)
    def _patch_image_urls(self, settings):
        settings.CACHES = DUMMY_CACHE
        with patch(
            "housegallery.core.image_utils.get_image_urls",
            side_effect=_mock_get_image_urls,
        ):
            yield

    def test_filters_by_exhibition(
        self, exhibition_page, make_installation_photo, make_opening_photo,
    ):
        make_installation_photo(exhibition_page)
        make_opening_photo(exhibition_page)
        result = exhibition_page.get_images_by_type("exhibition")
        assert all(img["type"] == "exhibition" for img in result)
        assert len(result) == 1

    def test_filters_by_opening(
        self, exhibition_page, make_installation_photo, make_opening_photo,
    ):
        make_installation_photo(exhibition_page)
        make_opening_photo(exhibition_page)
        result = exhibition_page.get_images_by_type("opening")
        assert all(img["type"] == "opening" for img in result)
        assert len(result) == 1

    def test_returns_all_when_none(
        self, exhibition_page, make_installation_photo, make_opening_photo,
    ):
        make_installation_photo(exhibition_page)
        make_opening_photo(exhibition_page)
        result = exhibition_page.get_images_by_type(None)
        assert len(result) == 2


@pytest.mark.django_db
class TestGetFilteredGalleryImages:
    """Tests for ExhibitionPage.get_filtered_gallery_images()."""

    @pytest.fixture(autouse=True)
    def _patch_image_urls(self, settings):
        settings.CACHES = DUMMY_CACHE
        with patch(
            "housegallery.core.image_utils.get_image_urls",
            side_effect=_mock_get_image_urls,
        ):
            yield

    def test_first_showcard_first(
        self, exhibition_page, make_showcard_photo, make_installation_photo,
    ):
        make_installation_photo(exhibition_page)
        make_showcard_photo(exhibition_page)
        result = exhibition_page.get_filtered_gallery_images()
        assert result[0]["type"] == "showcards"

    def test_remaining_showcards_last(
        self, exhibition_page, make_showcard_photo, make_installation_photo,
    ):
        make_showcard_photo(exhibition_page, title="Showcard 1")
        make_showcard_photo(exhibition_page, title="Showcard 2")
        make_installation_photo(exhibition_page)
        result = exhibition_page.get_filtered_gallery_images()
        assert result[0]["type"] == "showcards"
        assert result[-1]["type"] == "showcards"

    def test_excludes_opening_and_in_progress(
        self, exhibition_page,
        make_opening_photo, make_in_progress_photo, make_installation_photo,
    ):
        make_opening_photo(exhibition_page)
        make_in_progress_photo(exhibition_page)
        make_installation_photo(exhibition_page)
        result = exhibition_page.get_filtered_gallery_images()
        types = {img["type"] for img in result}
        assert "opening" not in types
        assert "in_progress" not in types

    def test_max_images_limit(self, exhibition_page, make_installation_photo):
        for i in range(5):
            make_installation_photo(exhibition_page, title=f"Install {i}")
        result = exhibition_page.get_filtered_gallery_images(max_images=3)
        assert len(result) == 3

    def test_empty_when_no_images(self, exhibition_page):
        result = exhibition_page.get_filtered_gallery_images()
        assert result == []

    def test_artworks_included_in_middle(
        self, exhibition_page, make_installation_photo, make_exhibition_artwork,
    ):
        make_installation_photo(exhibition_page)
        make_exhibition_artwork(exhibition_page, artwork_title="Gallery Piece")
        result = exhibition_page.get_filtered_gallery_images()
        types = [img["type"] for img in result]
        assert "artwork" in types
        assert "exhibition" in types


@pytest.mark.django_db
class TestGetUnifiedGalleryImages:
    """Tests for ExhibitionPage.get_unified_gallery_images()."""

    @pytest.fixture(autouse=True)
    def _patch_image_urls(self, settings):
        settings.CACHES = DUMMY_CACHE
        with patch(
            "housegallery.core.image_utils.get_image_urls",
            side_effect=_mock_get_image_urls,
        ):
            yield

    def test_installation_photos_first(
        self, exhibition_page, make_installation_photo, make_opening_photo,
    ):
        make_opening_photo(exhibition_page)
        make_installation_photo(exhibition_page)
        result = exhibition_page.get_unified_gallery_images()
        assert len(result) == 2
        assert result[0]["type"] == "exhibition"
        assert result[1]["type"] == "opening"

    def test_artworks_after_installation(
        self, exhibition_page, make_installation_photo, make_exhibition_artwork,
    ):
        make_installation_photo(exhibition_page)
        make_exhibition_artwork(exhibition_page, artwork_title="Piece A")
        result = exhibition_page.get_unified_gallery_images()
        types = [img["type"] for img in result]
        assert types.index("exhibition") < types.index("artwork")

    def test_opening_after_artworks(
        self, exhibition_page,
        make_installation_photo, make_exhibition_artwork, make_opening_photo,
    ):
        make_installation_photo(exhibition_page)
        make_exhibition_artwork(exhibition_page, artwork_title="Art 1")
        make_opening_photo(exhibition_page)
        result = exhibition_page.get_unified_gallery_images()
        types = [img["type"] for img in result]
        assert types.index("artwork") < types.index("opening")

    def test_in_progress_after_opening(
        self, exhibition_page, make_opening_photo, make_in_progress_photo,
    ):
        make_opening_photo(exhibition_page)
        make_in_progress_photo(exhibition_page)
        result = exhibition_page.get_unified_gallery_images()
        types = [img["type"] for img in result]
        assert types.index("opening") < types.index("in_progress")

    def test_artwork_metadata_structure(self, exhibition_page, make_exhibition_artwork):
        make_exhibition_artwork(exhibition_page, artwork_title="Sculpture X")
        result = exhibition_page.get_unified_gallery_images()
        artwork_images = [img for img in result if img["type"] == "artwork"]
        assert len(artwork_images) >= 1
        related = artwork_images[0]["related_artwork"]
        assert "title" in related
        assert "artist_names" in related
        assert "date" in related
        assert "size_display" in related

    def test_includes_srcset_sizes(self, exhibition_page, make_installation_photo):
        make_installation_photo(exhibition_page)
        result = exhibition_page.get_unified_gallery_images()
        assert "srcset" in result[0]
        assert "sizes" in result[0]

    def test_includes_exhibition_context(self, exhibition_page, make_installation_photo):
        make_installation_photo(exhibition_page)
        result = exhibition_page.get_unified_gallery_images()
        assert result[0]["exhibition_title"] == "Test Exhibition"
        assert "exhibition_date" in result[0]

    def test_empty_when_no_images(self, exhibition_page):
        result = exhibition_page.get_unified_gallery_images()
        assert result == []


@pytest.mark.django_db
class TestGetRandomizedGalleryImages:
    """Tests for ExhibitionPage.get_randomized_gallery_images()."""

    @pytest.fixture(autouse=True)
    def _patch_image_urls(self, settings):
        settings.CACHES = DUMMY_CACHE
        with patch(
            "housegallery.core.image_utils.get_image_urls",
            side_effect=_mock_get_image_urls,
        ):
            yield

    def test_same_seed_same_order(
        self, exhibition_page,
        make_installation_photo, make_opening_photo,
    ):
        for i in range(4):
            make_installation_photo(exhibition_page, title=f"Install {i}")
        make_opening_photo(exhibition_page)

        result_a = exhibition_page.get_randomized_gallery_images(seed="fixed-seed")
        result_b = exhibition_page.get_randomized_gallery_images(seed="fixed-seed")
        assert result_a == result_b

    def test_different_seed_different_order(
        self, exhibition_page,
        make_installation_photo, make_opening_photo, make_showcard_photo,
    ):
        for i in range(6):
            make_installation_photo(exhibition_page, title=f"Install {i}")
        for i in range(3):
            make_opening_photo(exhibition_page, title=f"Opening {i}")
        make_showcard_photo(exhibition_page)

        result_a = exhibition_page.get_randomized_gallery_images(seed="seed-alpha")
        result_b = exhibition_page.get_randomized_gallery_images(seed="seed-beta")

        titles_a = [img["image_title"] for img in result_a]
        titles_b = [img["image_title"] for img in result_b]
        assert titles_a != titles_b

    def test_returns_all_images(
        self, exhibition_page, make_installation_photo, make_opening_photo,
    ):
        make_installation_photo(exhibition_page)
        make_opening_photo(exhibition_page)
        result = exhibition_page.get_randomized_gallery_images(seed="any")
        assert len(result) == 2
