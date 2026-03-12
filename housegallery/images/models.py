import io
import logging

from django.core.files.uploadedfile import InMemoryUploadedFile
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from PIL import Image as PILImage
from PIL import ImageOps
from wagtail.images.models import AbstractImage
from wagtail.images.models import AbstractRendition

from taggit.managers import TaggableManager

logger = logging.getLogger(__name__)


# We define our own custom image class to replace wagtailimages.Image,
# providing various additional data fields
class CustomImage(AbstractImage):
    alt = models.CharField(
        max_length=510, help_text="Max length: 510 characters", blank=True,
    )
    credit = models.CharField(max_length=255, blank=True)
    description = models.TextField(
        blank=True,
        help_text="Optional description or additional information about the image"
    )
    tags = TaggableManager(blank=True)

    admin_form_fields = ("title", "file", "collection", "alt", "credit", "tags", "description")


    # When you save the image, check if alt text has been set.
    # If not, set it as the title.
    def save(self, *args, **kwargs):
        if not self.alt:
            self.alt = self.title

        is_new_upload = bool(
            self.file and
            (not self.pk or not hasattr(self, "_file_processed")),
        )

        if is_new_upload:
            self._validate_uploaded_image()
            self._apply_exif_transpose()
            self._file_processed = True

        super().save(*args, **kwargs)

    # Smart rendition helper methods
    def get_web_optimized(self, max_width=1440):
        """
        Get a web-optimized rendition of the image.
        Applies EXIF rotation, smart compression, and format optimization.
        """
        filter_spec = f"width-{max_width}|format-webp|webpquality-85"
        return self.get_rendition(filter_spec)

    def get_thumbnail(self, size=300):
        """
        Get a thumbnail rendition of the image.
        """
        filter_spec = f"fill-{size}x{size}|format-webp|webpquality-90"
        return self.get_rendition(filter_spec)

    def get_high_quality(self, max_dimension=2560):
        """
        Get a high-quality rendition for gallery viewing.
        """
        filter_spec = f"max-{max_dimension}x{max_dimension}|format-webp|webpquality-95"
        return self.get_rendition(filter_spec)

    def get_display_optimized(self):
        """Get the best rendition for display based on image dimensions."""
        # Default to max-2560 for large originals, which is the common case now
        filter_spec = "max-2560x2560|format-webp|webpquality-85"
        return self.get_rendition(filter_spec)

    def get_original(self):
        """
        Get the original uploaded file (untouched).
        Useful for downloads or when you need the exact original.
        """
        return self.file

    def _validate_uploaded_image(self):
        """
        Validate uploaded images without modifying the original:
        - Check file size (max 20MB input)
        - Verify it's a valid image format
        - Log info about the uploaded image
        """
        # Validate file size (20MB limit)
        max_upload_size = 20 * 1024 * 1024  # 20MB
        if self.file.size > max_upload_size:
            max_size_mb = max_upload_size / (1024 * 1024)
            msg = f"Image file too large. Maximum size is {max_size_mb:.0f}MB"
            raise ValueError(msg)

        try:
            # Validate that the file is a valid image
            self.file.seek(0)  # Reset file pointer
            image = PILImage.open(self.file)
            image.verify()  # Verify it's a valid image

            # Reset file pointer after verification
            self.file.seek(0)

            # Log successful validation (re-open to get dimensions)
            with PILImage.open(self.file) as img:
                logger.info(
                    "Valid image uploaded: %s (%dx%d, %.2fMB)",
                    self.file.name,
                    img.width,
                    img.height,
                    self.file.size / (1024 * 1024),
                )

        except OSError as e:
            # Handle image format/corruption errors
            logger.exception(
                "Invalid or corrupted image file %s", self.file.name,
            )
            msg = f"Invalid image file: {e!s}"
            raise ValueError(msg) from e
        except ValueError:
            # Re-raise validation errors (file size, etc.)
            logger.exception("Image validation failed for %s", self.file.name)
            raise
        except Exception:
            # Handle unexpected errors
            logger.exception(
                "Unexpected error validating image %s", self.file.name,
            )
            # Continue with original file for unexpected errors only

    def _apply_exif_transpose(self):
        """Apply EXIF rotation to ensure width/height match visual orientation."""
        try:
            self.file.seek(0)
            image = PILImage.open(self.file)

            # Check if EXIF transpose is needed
            exif = image.getexif()
            orientation = exif.get(0x0112)  # EXIF orientation tag
            if orientation is None or orientation == 1:
                # No rotation needed
                return

            # Apply EXIF transpose
            transposed = ImageOps.exif_transpose(image)

            # Save back in original format
            output = io.BytesIO()
            img_format = image.format or "JPEG"

            save_kwargs = {"format": img_format}
            if img_format.upper() == "JPEG":
                save_kwargs["quality"] = "keep"
            elif img_format.upper() == "WEBP":
                save_kwargs["quality"] = 95

            transposed.save(output, **save_kwargs)

            # Replace the file
            file_size = output.tell()
            output.seek(0)

            from pathlib import Path

            original_name = Path(self.file.name).name

            self.file = InMemoryUploadedFile(
                output,
                "ImageField",
                original_name,
                f"image/{img_format.lower()}",
                file_size,
                None,
            )
            self.file_size = file_size

        except Exception:
            logger.exception("Failed to apply EXIF transpose to %s", self.file.name)
            # Continue with original file


class Rendition(AbstractRendition):
    image = models.ForeignKey(
        "CustomImage",
        related_name="renditions",
        on_delete=models.CASCADE,
    )

    @property
    def alt(self):
        return self.image.alt

    class Meta:
        unique_together = (
            ("image", "filter_spec", "focal_point_key"),
        )


@receiver(post_save, sender=CustomImage)
def generate_standard_renditions(sender, instance, created, **kwargs):
    """
    Generate standard renditions when an image is uploaded.
    This pre-generates the common sizes used in templates to avoid
    template-time image processing.
    """
    if created:
        try:
            # Legacy template tag renditions ({% image ... width-400 %} etc.)
            instance.get_rendition('width-400')
            instance.get_rendition('width-400|format-webp')
            instance.get_rendition('width-1200')
            instance.get_rendition('width-1200|format-webp')

            # Medium size for srcset
            instance.get_rendition('width-800|format-webp')

            # New helper method renditions
            # get_web_optimized() - used for smaller/medium display
            instance.get_rendition('width-1440|format-webp|webpquality-85')
            # get_display_optimized() - analyzes image and picks best spec
            instance.get_display_optimized()
            # get_thumbnail() - admin and card thumbnails
            instance.get_rendition('fill-300x300|format-webp|webpquality-90')

            logger.info(
                "Generated standard renditions for image: %s",
                instance.title
            )
        except Exception as e:
            logger.error(
                "Failed to generate renditions for image %s: %s",
                instance.title,
                str(e)
            )
