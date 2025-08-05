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
        """Return optimized renditions for the image"""
        renditions = {}
        
        try:
            # Thumbnail rendition
            thumbnail = obj.get_thumbnail(size=400)
            renditions['thumbnail'] = {
                'url': thumbnail.url,
                'width': thumbnail.width,
                'height': thumbnail.height,
            }
            
            # Web optimized rendition
            web_optimized = obj.get_web_optimized(max_width=1200)
            renditions['web_optimized'] = {
                'url': web_optimized.url,
                'width': web_optimized.width,
                'height': web_optimized.height,
            }
            
            # High quality rendition
            high_quality = obj.get_high_quality(max_dimension=2400)
            renditions['high_quality'] = {
                'url': high_quality.url,
                'width': high_quality.width,
                'height': high_quality.height,
            }
            
        except Exception as e:
            # Log error but don't fail the serialization
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to generate renditions for image {obj.id}: {str(e)}")
        
        return renditions
    
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