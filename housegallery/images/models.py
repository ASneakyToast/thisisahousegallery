import io
import os
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.db import models
from PIL import Image as PILImage, ExifTags
from PIL.ImageFile import ImageFile

from wagtail.images.models import AbstractImage, AbstractRendition, Image


# We define our own custom image class to replace wagtailimages.Image,
# providing various additional data fields
class CustomImage(AbstractImage):
    alt = models.CharField(max_length=510, help_text="Max length: 510 characters", blank=True)
    credit = models.CharField(max_length=255, blank=True)

    admin_form_fields = Image.admin_form_fields + (
        'alt',
        'credit',
    )

    # When you save the image, check if alt text has been set. If not, set it as the title.
    def save(self, *args, **kwargs):
        if not self.alt:
            self.alt = self.title

        # Process image if this is a new upload
        if self.file and not self.pk:
            self._process_uploaded_image()

        super().save(*args, **kwargs)

    def _process_uploaded_image(self):
        """
        Process uploaded images to:
        - Resize to max 2560px width/height
        - Compress to under 1MB while maintaining quality
        - Handle EXIF rotation
        - Validate file size (max 10MB input)
        """
        # Validate file size (10MB limit)
        max_upload_size = 10 * 1024 * 1024  # 10MB
        if self.file.size > max_upload_size:
            raise ValueError(f"Image file too large. Maximum size is {max_upload_size / (1024*1024):.0f}MB")

        try:
            # Open the image
            image = PILImage.open(self.file)
            
            # Handle EXIF rotation
            image = self._fix_image_rotation(image)
            
            # Convert to RGB if necessary (for JPEG output)
            if image.mode in ('RGBA', 'LA', 'P'):
                background = PILImage.new('RGB', image.size, (255, 255, 255))
                if image.mode == 'P':
                    image = image.convert('RGBA')
                background.paste(image, mask=image.split()[-1] if image.mode == 'RGBA' else None)
                image = background
            elif image.mode not in ('RGB', 'L'):
                image = image.convert('RGB')

            # Resize image if needed (max 2560px)
            image = self._resize_image(image, max_dimension=2560)
            
            # Compress image to target size (1MB)
            compressed_file = self._compress_image(image, target_size_mb=1.0)
            
            # Replace the original file
            self.file = compressed_file
            
            # Update cached file_size field to match the processed file
            self.file_size = compressed_file.size
            
        except Exception as e:
            # Log the error but don't prevent saving
            print(f"Image processing failed for {self.file.name}: {str(e)}")
            # Continue with original file if processing fails

    def _fix_image_rotation(self, image):
        """
        Fix image rotation based on EXIF data.
        """
        try:
            for orientation in ExifTags.TAGS.keys():
                if ExifTags.TAGS[orientation] == 'Orientation':
                    break
            
            exif = image._getexif()
            if exif is not None:
                orientation_value = exif.get(orientation)
                if orientation_value == 3:
                    image = image.rotate(180, expand=True)
                elif orientation_value == 6:
                    image = image.rotate(270, expand=True)
                elif orientation_value == 8:
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

    def _compress_image(self, image, target_size_mb=1.0, min_quality=30, max_quality=95):
        """
        Compress image to target file size using binary search on quality.
        """
        target_size_bytes = target_size_mb * 1024 * 1024
        
        # Start with high quality
        quality = max_quality
        
        for attempt in range(10):  # Max 10 attempts
            output = io.BytesIO()
            
            # Save with current quality
            save_kwargs = {
                'format': 'JPEG',
                'quality': quality,
                'optimize': True,
                'progressive': True
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
        original_name = self.file.name
        name_parts = os.path.splitext(original_name)
        new_name = f"{name_parts[0]}_processed.jpg"
        
        return InMemoryUploadedFile(
            output,
            'ImageField',
            new_name,
            'image/jpeg',
            file_size,
            None
        )


class Rendition(AbstractRendition):
    image = models.ForeignKey(
        'CustomImage',
        related_name='renditions',
        on_delete=models.CASCADE
    )

    @property
    def alt(self):
        return self.image.alt

    class Meta:
        unique_together = (
            ('image', 'filter_spec', 'focal_point_key'),
        )
