from unittest.mock import patch

import pytest

from housegallery.api.serializers.images import ImageSerializer


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


@pytest.mark.django_db
class TestImageSerializer:

    def test_get_renditions_returns_expected_structure(self, make_image):
        image = make_image(title="Test Image")
        with patch(
            "housegallery.core.image_utils.get_image_urls",
            return_value=MOCK_IMAGE_URLS,
        ):
            serializer = ImageSerializer(instance=image)
            renditions = serializer.data["renditions"]

        assert "thumbnail" in renditions
        assert renditions["thumbnail"]["url"] == "/media/test_thumb.jpg"
        assert "medium" in renditions
        assert renditions["medium"]["url"] == "/media/test_medium.jpg"
        assert "full" in renditions
        assert renditions["full"]["url"] == "/media/test_full.jpg"
        assert "srcset" in renditions
        assert "sizes" in renditions

    def test_get_renditions_returns_empty_dict_on_exception(self, make_image):
        image = make_image(title="Error Image")
        with patch(
            "housegallery.core.image_utils.get_image_urls",
            side_effect=Exception("rendition error"),
        ):
            serializer = ImageSerializer(instance=image)
            renditions = serializer.data["renditions"]

        assert renditions == {}

    def test_get_metadata_returns_mime_type(self, make_image):
        image = make_image(title="PNG Image")
        serializer = ImageSerializer(instance=image)
        metadata = serializer.data["metadata"]

        assert "mime_type" in metadata
        assert metadata["mime_type"] == "image/png"

    def test_get_metadata_has_focal_point_true(self, make_image):
        image = make_image(title="Focal Image")
        image.focal_point_x = 100
        image.focal_point_y = 200
        image.focal_point_width = 50
        image.focal_point_height = 50
        image.save(update_fields=[
            "focal_point_x", "focal_point_y",
            "focal_point_width", "focal_point_height",
        ])

        serializer = ImageSerializer(instance=image)
        metadata = serializer.data["metadata"]

        assert metadata["has_focal_point"] is True

    def test_get_metadata_has_focal_point_false(self, make_image):
        image = make_image(title="No Focal Image")
        serializer = ImageSerializer(instance=image)
        metadata = serializer.data["metadata"]

        assert metadata["has_focal_point"] is False

    def test_get_original_url_returns_file_url(self, make_image):
        image = make_image(title="URL Image")
        serializer = ImageSerializer(instance=image)
        original_url = serializer.data["original_url"]

        assert original_url is not None
        assert isinstance(original_url, str)
        assert len(original_url) > 0

    def test_serializer_fields_complete(self, make_image):
        image = make_image(title="Fields Image")
        with patch(
            "housegallery.core.image_utils.get_image_urls",
            return_value=MOCK_IMAGE_URLS,
        ):
            serializer = ImageSerializer(instance=image)
            data = serializer.data

        expected_fields = [
            "id", "title", "alt", "credit", "description",
            "width", "height", "file_size",
            "original_url", "renditions", "metadata",
            "created_at",
            "focal_point_x", "focal_point_y",
            "focal_point_width", "focal_point_height",
        ]
        for field in expected_fields:
            assert field in data, f"Missing field: {field}"

    def test_mime_type_jpg(self, make_image):
        image = make_image(title="JPEG Image")
        image.file.name = "images/test_photo.jpg"

        serializer = ImageSerializer(instance=image)
        metadata = serializer.data["metadata"]

        assert metadata["mime_type"] == "image/jpeg"

    def test_mime_type_webp(self, make_image):
        image = make_image(title="WebP Image")
        image.file.name = "images/test_photo.webp"

        serializer = ImageSerializer(instance=image)
        metadata = serializer.data["metadata"]

        assert metadata["mime_type"] == "image/webp"
