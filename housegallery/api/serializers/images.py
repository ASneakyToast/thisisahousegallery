from rest_framework import serializers
from housegallery.images.models import CustomImage


class ImageRenditionSerializer(serializers.Serializer):
    """Serializer for image renditions"""
    url = serializers.CharField()
    width = serializers.IntegerField()
    height = serializers.IntegerField()
    file_size = serializers.IntegerField(required=False)
    format = serializers.CharField(required=False)


class ImageSerializer(serializers.ModelSerializer):
    """Serializer for CustomImage model with rendition support"""
    
    renditions = serializers.SerializerMethodField()
    metadata = serializers.SerializerMethodField()
    original_url = serializers.SerializerMethodField()
    
    class Meta:
        model = CustomImage
        fields = [
            'id',
            'title',
            'alt',
            'credit',
            'description',
            'width',
            'height',
            'file_size',
            'original_url',
            'renditions',
            'metadata',
            'created_at',
            'focal_point_x',
            'focal_point_y',
            'focal_point_width',
            'focal_point_height',
        ]
    
    def get_renditions(self, obj):
        """Return optimized renditions for the image using shared utility."""
        from housegallery.core.image_utils import get_image_urls

        try:
            urls = get_image_urls(obj)
            return {
                'thumbnail': {'url': urls['thumb_url']},
                'medium': {'url': urls['medium_url']},
                'full': {'url': urls['full_url']},
                'srcset': urls['srcset'],
                'sizes': urls['sizes'],
            }
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to generate renditions for image {obj.id}: {str(e)}")
            return {}
    
    def get_metadata(self, obj):
        """Return additional metadata about the image"""
        return {
            'mime_type': self._get_mime_type(obj),
            'has_focal_point': bool(obj.focal_point_x and obj.focal_point_y),
        }
    
    def get_original_url(self, obj):
        """Return the URL of the original image file"""
        return obj.file.url if obj.file else None
    
    def _get_mime_type(self, obj):
        """Determine MIME type from file extension"""
        if obj.file and obj.file.name:
            ext = obj.file.name.lower().split('.')[-1]
            mime_map = {
                'jpg': 'image/jpeg',
                'jpeg': 'image/jpeg',
                'png': 'image/png',
                'gif': 'image/gif',
                'webp': 'image/webp',
                'svg': 'image/svg+xml',
            }
            return mime_map.get(ext, 'image/jpeg')
        return 'image/jpeg'