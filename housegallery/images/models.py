import io
import logging

from django.core.files.uploadedfile import InMemoryUploadedFile
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from PIL import ExifTags
from PIL import Image as PILImage
from wagtail.images.models import AbstractImage
from wagtail.images.models import AbstractRendition
from wagtail.images.models import Image

from taggit.managers import TaggableManager

logger = logging.getLogger(__name__)

# Image size constants
MAX_HIGH_QUALITY_DIMENSION = 2560
MAX_WEB_DIMENSION = 1440


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
    preserve_original = models.BooleanField(
        default=False,
        help_text=(
            "If unchecked, files will be optimized to high-quality web format "
            "(recommended for most uploads). Uses more storage when checked."
        ),
    )
    tags = TaggableManager(blank=True)

    admin_form_fields = ("title", "file", "collection", "alt", "credit", "tags", "description", "preserve_original")


    # When you save the image, check if alt text has been set.
    # If not, set it as the title.
    def save(self, *args, **kwargs):
        if not self.alt:
            self.alt = self.title

        # Track if this is a new file upload that needs processing
        is_new_upload = bool(
            self.file and
            (not self.pk or not hasattr(self, "_file_processed")),
        )

        # Handle new uploads based on preserve_original setting
        if is_new_upload:
            self._validate_uploaded_image()

            # If preserve_original is False (default), process the image
            if not self.preserve_original:
                self._process_uploaded_image()

            # Mark as processed to avoid re-processing on subsequent saves
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
        """
        Get the best rendition for display based on original image characteristics.
        This applies smart processing similar to the original logic but as a rendition.
        """
        try:
            # Open original to analyze characteristics
            with PILImage.open(self.file) as img:
                width, height = img.size

                # For very large images, use max constraint with high quality
                if (width > MAX_HIGH_QUALITY_DIMENSION or
                    height > MAX_HIGH_QUALITY_DIMENSION):
                    filter_spec = (
                        f"max-{MAX_HIGH_QUALITY_DIMENSION}x{MAX_HIGH_QUALITY_DIMENSION}"
                        "|format-webp|webpquality-85"
                    )
                # For medium images, optimize for web
                elif width > MAX_WEB_DIMENSION or height > MAX_WEB_DIMENSION:
                    filter_spec = (
                        f"width-{MAX_WEB_DIMENSION}|format-webp|webpquality-88"
                    )
                # For smaller images, preserve more quality
                else:
                    filter_spec = "original|format-webp|webpquality-92"

                return self.get_rendition(filter_spec)

        except Exception:
            # Fallback to web optimized if analysis fails
            logger.exception("Failed to analyze image for display optimization")
            return self.get_web_optimized()

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

    def _process_uploaded_image(self):
        """
        Process uploaded images (when preserve_original=False):
        - Resize to max 2560px width/height
        - Compress to high quality
        - Handle EXIF rotation
        - Convert to optimal format
        """
        try:
            # Open the image for processing
            self.file.seek(0)
            image = PILImage.open(self.file)

            # Handle EXIF rotation
            image = self._fix_image_rotation(image)

            # Convert to RGB if necessary (for JPEG output)
            if image.mode in ("RGBA", "LA", "P"):
                background = PILImage.new("RGB", image.size, (255, 255, 255))
                if image.mode == "P":
                    image = image.convert("RGBA")
                mask = image.split()[-1] if image.mode == "RGBA" else None
                background.paste(image, mask=mask)
                image = background
            elif image.mode not in ("RGB", "L"):
                image = image.convert("RGB")

            # Resize image if needed (max 2560px for high quality)
            image = self._resize_image(image, max_dimension=MAX_HIGH_QUALITY_DIMENSION)

            # Compress image with high quality (targeting reasonable file size)
            compressed_file = self._compress_image(
                image, target_size_mb=2.0, min_quality=80,
            )

            # Replace the original file
            self.file = compressed_file

            # Update cached file_size field to match the processed file
            self.file_size = compressed_file.size

            logger.info(
                "Processed image: %s (optimized for web)",
                self.file.name,
            )

        except Exception:
            # Handle unexpected errors - continue with original file
            logger.exception(
                "Unexpected error processing image %s", self.file.name,
            )
            # Continue with original file for unexpected errors only

    def _fix_image_rotation(self, image):
        """
        Fix image rotation based on EXIF data.
        """
        try:
            # Get EXIF data using the modern method
            exif = image.getexif()
            if exif is not None:
                # Get orientation tag directly
                orientation_value = exif.get(ExifTags.Base.Orientation.value)
                # EXIF orientation constants
                rotate_180 = 3
                rotate_270 = 6
                rotate_90 = 8
                if orientation_value == rotate_180:
                    image = image.rotate(180, expand=True)
                elif orientation_value == rotate_270:
                    image = image.rotate(270, expand=True)
                elif orientation_value == rotate_90:
                    image = image.rotate(90, expand=True)
        except (AttributeError, KeyError, TypeError):
            # If EXIF processing fails, continue with original image
            pass

        return image

    def _resize_image(self, image, max_dimension=2560):
        """
        Resize image to fit within max_dimension while maintaining aspect ratio.
        """
        width, height = image.size

        if width <= max_dimension and height <= max_dimension:
            return image

        # Calculate new dimensions
        if width > height:
            new_width = max_dimension
            new_height = int((height * max_dimension) / width)
        else:
            new_height = max_dimension
            new_width = int((width * max_dimension) / height)

        # Use high-quality resampling
        return image.resize((new_width, new_height), PILImage.Resampling.LANCZOS)

    def _compress_image(
        self, image, target_size_mb=1.0, min_quality=30, max_quality=95,
    ):
        """
        Compress image to target file size using binary search on quality.
        """
        target_size_bytes = target_size_mb * 1024 * 1024

        # Start with high quality
        quality = max_quality

        for _attempt in range(10):  # Max 10 attempts
            output = io.BytesIO()

            # Save with current quality
            save_kwargs = {
                "format": "JPEG",
                "quality": quality,
                "optimize": True,
                "progressive": True,
            }

            image.save(output, **save_kwargs)
            output_size = output.tell()

            # If size is acceptable, use this quality
            if output_size <= target_size_bytes or quality <= min_quality:
                break

            # Reduce quality for next attempt
            if output_size > target_size_bytes * 1.5:
                # Much too large, reduce quality more aggressively
                quality = max(min_quality, quality - 15)
            else:
                # Close to target, reduce quality more gradually
                quality = max(min_quality, quality - 5)

        # Create Django file object
        file_size = output.tell()
        output.seek(0)

        # Generate new filename
        from pathlib import Path
        original_path = Path(self.file.name)
        new_name = f"{original_path.stem}_processed.jpg"

        return InMemoryUploadedFile(
            output,
            "ImageField",
            new_name,
            "image/jpeg",
            file_size,
            None,
        )


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
