from unittest.mock import MagicMock, patch

import pytest

from housegallery.core.image_utils import (
    _find_rendition_in_prefetch,
    get_image_urls,
    get_image_urls_batch,
)
from housegallery.images.models import CustomImage


def _mock_rendition(url="/media/test.jpg", width=400, height=300, filter_spec="width-400"):
    """Helper to create a mock rendition with standard attributes."""
    rendition = MagicMock()
    rendition.url = url
    rendition.width = width
    rendition.height = height
    rendition.filter_spec = filter_spec
    return rendition


@pytest.mark.django_db
class TestFindRenditionInPrefetch:
    def test_exact_match_found(self, make_image, make_image_with_renditions):
        image = make_image()
        specs = [
            {"url": "/media/thumb.jpg", "width": 400, "height": 300, "filter_spec": "width-400"},
            {"url": "/media/full.jpg", "width": 1440, "height": 1080, "filter_spec": "width-1440|format-webp|webpquality-85"},
        ]
        mock_renditions = make_image_with_renditions(image, specs)

        result = _find_rendition_in_prefetch(image, "width-400")

        assert result is not None
        assert result.url == "/media/thumb.jpg"
        assert result.filter_spec == "width-400"

    def test_no_match_returns_none(self, make_image, make_image_with_renditions):
        image = make_image()
        specs = [
            {"url": "/media/thumb.jpg", "width": 400, "height": 300, "filter_spec": "width-400"},
        ]
        make_image_with_renditions(image, specs)

        result = _find_rendition_in_prefetch(image, "width-9999")

        assert result is None

    def test_no_prefetch_cache_returns_none(self, make_image):
        image = make_image()
        # No renditions exist and no prefetch cache set

        result = _find_rendition_in_prefetch(image, "width-400")

        assert result is None

    def test_exception_returns_none(self):
        image_obj = MagicMock()
        image_obj.renditions.all.side_effect = RuntimeError("DB error")

        result = _find_rendition_in_prefetch(image_obj, "width-400")

        assert result is None


@pytest.mark.django_db
class TestGetImageUrls:
    def test_returns_all_expected_keys(self, make_image):
        image = make_image(title="Keys Test", alt="Alt text", credit="Photo credit")
        mock_rendition = _mock_rendition()
        with patch.object(image, "get_rendition", return_value=mock_rendition):
            result = get_image_urls(image)

        expected_keys = {
            "thumb_url", "medium_url", "full_url", "original_url",
            "srcset", "sizes", "width", "height", "alt", "credit", "title",
        }
        assert expected_keys.issubset(result.keys())

    def test_default_specs_produce_three_sizes(self, make_image):
        image = make_image()
        mock_rendition = _mock_rendition()
        with patch.object(image, "get_rendition", return_value=mock_rendition):
            result = get_image_urls(image)

        assert result["thumb_url"] != ""
        assert result["medium_url"] != ""
        assert result["full_url"] != ""

    def test_custom_specs_override(self, make_image):
        image = make_image()
        custom_specs = {
            "small": "width-200",
            "large": "width-2000|format-webp",
        }
        mock_rendition = _mock_rendition()
        with patch.object(image, "get_rendition", return_value=mock_rendition):
            result = get_image_urls(image, specs=custom_specs)

        assert "small_url" in result
        assert "large_url" in result
        # Default keys should not be present
        assert "thumb_url" not in result
        assert "medium_url" not in result
        assert "full_url" not in result

    def test_srcset_built_from_multiple_renditions(self, make_image):
        image = make_image()

        def mock_get_rendition(filter_spec):
            if filter_spec == "width-400":
                return _mock_rendition(url="/media/thumb.jpg", width=400, filter_spec="width-400")
            elif filter_spec == "width-800|format-webp":
                return _mock_rendition(url="/media/medium.webp", width=800, filter_spec="width-800|format-webp")
            elif filter_spec == "width-1440|format-webp|webpquality-85":
                return _mock_rendition(url="/media/full.webp", width=1440, filter_spec="width-1440|format-webp|webpquality-85")
            return _mock_rendition()

        with patch.object(image, "get_rendition", side_effect=mock_get_rendition):
            result = get_image_urls(image)

        assert "/media/thumb.jpg 400w" in result["srcset"]
        assert "/media/medium.webp 800w" in result["srcset"]
        assert "/media/full.webp 1440w" in result["srcset"]

    def test_srcset_empty_for_single_rendition(self, make_image):
        image = make_image()
        single_spec = {"only": "width-600"}
        mock_rendition = _mock_rendition(url="/media/only.jpg", width=600, filter_spec="width-600")
        with patch.object(image, "get_rendition", return_value=mock_rendition):
            result = get_image_urls(image, specs=single_spec)

        assert result["srcset"] == ""

    def test_sizes_present_with_srcset(self, make_image):
        image = make_image()

        def mock_get_rendition(filter_spec):
            if filter_spec == "width-400":
                return _mock_rendition(url="/media/thumb.jpg", width=400, filter_spec="width-400")
            elif filter_spec == "width-800|format-webp":
                return _mock_rendition(url="/media/medium.webp", width=800, filter_spec="width-800|format-webp")
            elif filter_spec == "width-1440|format-webp|webpquality-85":
                return _mock_rendition(url="/media/full.webp", width=1440, filter_spec="width-1440|format-webp|webpquality-85")
            return _mock_rendition()

        with patch.object(image, "get_rendition", side_effect=mock_get_rendition):
            result = get_image_urls(image)

        assert result["sizes"] == "(max-width: 600px) 400px, (max-width: 1200px) 800px, 1440px"

    def test_sizes_absent_without_srcset(self, make_image):
        image = make_image()
        single_spec = {"only": "width-600"}
        mock_rendition = _mock_rendition()
        with patch.object(image, "get_rendition", return_value=mock_rendition):
            result = get_image_urls(image, specs=single_spec)

        assert result["sizes"] == ""

    def test_alt_credit_title_metadata(self, make_image):
        image = make_image(title="Gallery Shot", alt="A painting", credit="J. Doe")
        mock_rendition = _mock_rendition()
        with patch.object(image, "get_rendition", return_value=mock_rendition):
            result = get_image_urls(image)

        assert result["alt"] == "A painting"
        assert result["credit"] == "J. Doe"
        assert result["title"] == "Gallery Shot"

    def test_uses_prefetched_rendition_when_available(self, make_image, make_image_with_renditions):
        image = make_image()
        specs = [
            {"url": "/media/thumb.jpg", "width": 400, "height": 300, "filter_spec": "width-400"},
            {"url": "/media/medium.webp", "width": 800, "height": 600, "filter_spec": "width-800|format-webp"},
            {"url": "/media/full.webp", "width": 1440, "height": 1080, "filter_spec": "width-1440|format-webp|webpquality-85"},
        ]
        make_image_with_renditions(image, specs)

        with patch.object(image, "get_rendition") as mock_get:
            result = get_image_urls(image)

        # get_rendition should NOT have been called since all renditions were prefetched
        mock_get.assert_not_called()
        assert result["thumb_url"] == "/media/thumb.jpg"
        assert result["medium_url"] == "/media/medium.webp"
        assert result["full_url"] == "/media/full.webp"

    def test_falls_back_to_get_rendition(self, make_image):
        image = make_image()
        # No prefetch cache set
        mock_rendition = _mock_rendition(url="/media/fallback.jpg")
        with patch.object(image, "get_rendition", return_value=mock_rendition) as mock_get:
            result = get_image_urls(image)

        assert mock_get.call_count > 0
        assert result["thumb_url"] == "/media/fallback.jpg"

    def test_handles_exception_gracefully(self, make_image):
        image = make_image()
        with patch.object(image, "get_rendition", side_effect=Exception("Rendition failed")):
            result = get_image_urls(image)

        assert result["thumb_url"] == ""
        assert result["medium_url"] == ""
        assert result["full_url"] == ""


@pytest.mark.django_db
class TestGetImageUrlsBatch:
    def test_empty_input_returns_empty_list(self):
        result = get_image_urls_batch([])

        assert result == []

    def test_preserves_input_order(self, make_image):
        image_a = make_image(title="Alpha")
        image_b = make_image(title="Bravo")
        image_c = make_image(title="Charlie")

        with patch.object(CustomImage, "get_rendition", return_value=_mock_rendition()):
            result = get_image_urls_batch([image_a, image_b, image_c])

        assert len(result) == 3
        assert result[0]["title"] == "Alpha"
        assert result[1]["title"] == "Bravo"
        assert result[2]["title"] == "Charlie"

    def test_each_dict_matches_get_image_urls_structure(self, make_image):
        image = make_image()

        expected_keys = {
            "thumb_url", "medium_url", "full_url", "original_url",
            "srcset", "sizes", "width", "height", "alt", "credit", "title",
        }

        with patch.object(CustomImage, "get_rendition", return_value=_mock_rendition()):
            result = get_image_urls_batch([image])

        assert len(result) == 1
        assert expected_keys.issubset(result[0].keys())

    def test_custom_specs_passed_through(self, make_image):
        image = make_image()
        custom_specs = {
            "tiny": "width-100",
            "huge": "width-3000|format-webp",
        }

        with patch.object(CustomImage, "get_rendition", return_value=_mock_rendition()):
            result = get_image_urls_batch([image], specs=custom_specs)

        assert len(result) == 1
        assert "tiny_url" in result[0]
        assert "huge_url" in result[0]
        assert "thumb_url" not in result[0]
