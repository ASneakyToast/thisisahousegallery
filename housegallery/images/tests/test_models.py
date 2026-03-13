import io

import pytest
from PIL import Image as PILImage
from unittest.mock import patch, MagicMock

from django.core.files.uploadedfile import SimpleUploadedFile, InMemoryUploadedFile
from django.db.models.signals import post_save

from housegallery.images.models import CustomImage, generate_standard_renditions


def _create_1x1_png():
    """Create a minimal 1x1 PNG image in memory."""
    buf = io.BytesIO()
    img = PILImage.new("RGB", (1, 1), color="red")
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf.getvalue()


def _create_jpeg_with_orientation(orientation_value):
    """Create a JPEG with a specific EXIF orientation tag."""
    img = PILImage.new("RGB", (100, 50), color="red")  # 100w x 50h
    buf = io.BytesIO()

    # Create EXIF data with orientation
    exif = img.getexif()
    exif[0x0112] = orientation_value  # Orientation tag

    img.save(buf, format="JPEG", exif=exif.tobytes())
    buf.seek(0)
    return buf


@pytest.fixture
def enable_rendition_signal():
    """Re-enable the rendition signal for tests that need it."""
    post_save.connect(generate_standard_renditions, sender=CustomImage)
    yield
    post_save.disconnect(generate_standard_renditions, sender=CustomImage)


@pytest.mark.django_db
class TestCustomImageSave:
    def test_sets_alt_to_title_when_empty(self, make_image):
        image = make_image(title="My Image", alt="")
        assert image.alt == "My Image"

    def test_preserves_existing_alt(self, make_image):
        image = make_image(title="My Image", alt="Custom alt")
        assert image.alt == "Custom alt"

    def test_calls_exif_transpose_on_new_upload(self):
        with patch.object(
            CustomImage, "_apply_exif_transpose"
        ) as mock_transpose, patch.object(
            CustomImage, "_validate_uploaded_image"
        ):
            png_data = _create_1x1_png()
            uploaded_file = SimpleUploadedFile(
                name="test.png", content=png_data, content_type="image/png",
            )
            image = CustomImage(title="New Upload", file=uploaded_file)
            image.save()
            mock_transpose.assert_called_once()

    def test_skips_processing_on_existing_save(self, make_image):
        image = make_image(title="Existing Image")
        with patch.object(
            CustomImage, "_apply_exif_transpose"
        ) as mock_transpose, patch.object(
            CustomImage, "_validate_uploaded_image"
        ):
            image.save()
            mock_transpose.assert_not_called()


@pytest.mark.django_db
class TestExifTranspose:
    def test_noop_when_orientation_is_1(self):
        buf = _create_jpeg_with_orientation(1)
        uploaded_file = SimpleUploadedFile(
            "test.jpg", buf.read(), content_type="image/jpeg",
        )
        image = CustomImage(title="Test", file=uploaded_file)
        original_file = image.file
        image._apply_exif_transpose()
        # File should remain unchanged — no rotation needed
        assert image.file is original_file

    def test_noop_when_no_exif(self):
        png_data = _create_1x1_png()
        uploaded_file = SimpleUploadedFile(
            "test.png", png_data, content_type="image/png",
        )
        image = CustomImage(title="Test", file=uploaded_file)
        original_file = image.file
        image._apply_exif_transpose()
        # File should remain unchanged — no EXIF orientation tag
        assert image.file is original_file

    def test_applies_rotation_when_orientation_set(self):
        buf = _create_jpeg_with_orientation(6)  # 90 deg CW
        uploaded_file = SimpleUploadedFile(
            "rotated.jpg", buf.read(), content_type="image/jpeg",
        )
        image = CustomImage(title="Rotated", file=uploaded_file)
        image._apply_exif_transpose()
        # File should have been replaced (EXIF orientation removed)
        image.file.seek(0)
        result = PILImage.open(image.file)
        orientation = result.getexif().get(0x0112)
        assert orientation is None or orientation == 1

    def test_preserves_jpeg_format(self):
        buf = _create_jpeg_with_orientation(6)
        uploaded_file = SimpleUploadedFile(
            "test.jpg", buf.read(), content_type="image/jpeg",
        )
        image = CustomImage(title="Test", file=uploaded_file)
        image._apply_exif_transpose()
        # Verify the result is still a JPEG by reading it with PIL
        image.file.seek(0)
        result_img = PILImage.open(image.file)
        assert result_img.format == "JPEG"

    def test_handles_exception_gracefully(self):
        buf = _create_jpeg_with_orientation(6)
        uploaded_file = SimpleUploadedFile(
            "test.jpg", buf.read(), content_type="image/jpeg",
        )
        image = CustomImage(title="Test", file=uploaded_file)
        original_file = image.file
        with patch("housegallery.images.models.ImageOps.exif_transpose", side_effect=Exception("boom")):
            image._apply_exif_transpose()
        # Should not raise, file should remain unchanged
        assert image.file is original_file


@pytest.mark.django_db
class TestGenerateStandardRenditions:
    def test_generates_renditions_on_create(self, make_image, enable_rendition_signal):
        with patch.object(
            CustomImage, "get_rendition", return_value=MagicMock()
        ) as mock_rendition, patch.object(
            CustomImage, "get_display_optimized", return_value=MagicMock()
        ) as mock_display:
            make_image(title="Signal Test")
            mock_rendition.assert_called()
            mock_display.assert_called()

    def test_skips_on_update(self, make_image, enable_rendition_signal):
        with patch.object(
            CustomImage, "get_rendition", return_value=MagicMock()
        ) as mock_rendition, patch.object(
            CustomImage, "get_display_optimized", return_value=MagicMock()
        ):
            image = make_image(title="Update Test")
            mock_rendition.reset_mock()
            image.title = "Updated Title"
            image.save()
            mock_rendition.assert_not_called()

    def test_handles_failure_gracefully(self, make_image, enable_rendition_signal):
        with patch.object(
            CustomImage, "get_rendition", side_effect=Exception("rendition error")
        ), patch.object(
            CustomImage, "get_display_optimized", side_effect=Exception("display error")
        ):
            # Should not raise despite get_rendition failing
            image = make_image(title="Failure Test")
            assert image.pk is not None

    def test_generates_all_expected_specs(self, make_image, enable_rendition_signal):
        expected_specs = {
            "width-400",
            "width-400|format-webp",
            "width-1200",
            "width-1200|format-webp",
            "width-800|format-webp",
            "width-1440|format-webp|webpquality-85",
            "fill-300x300|format-webp|webpquality-90",
        }
        with patch.object(
            CustomImage, "get_rendition", return_value=MagicMock()
        ) as mock_rendition, patch.object(
            CustomImage, "get_display_optimized", return_value=MagicMock()
        ):
            make_image(title="Spec Test")
            called_specs = {
                call.args[0] for call in mock_rendition.call_args_list
            }
            assert expected_specs.issubset(called_specs)
