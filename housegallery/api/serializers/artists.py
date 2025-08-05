from rest_framework import serializers
from housegallery.artists.models import Artist, SocialMediaLinkBlock
from housegallery.api.serializers.images import ImageSerializer


class SocialMediaLinkSerializer(serializers.Serializer):
    """Serializer for social media links in StreamField"""
    platform = serializers.CharField()
    platform_name = serializers.CharField(required=False, allow_blank=True)
    url = serializers.URLField()
    handle = serializers.CharField(required=False, allow_blank=True)


class ArtistSerializer(serializers.ModelSerializer):
    """Serializer for Artist model with full profile data"""
    
    profile_image = ImageSerializer(read_only=True)
    social_media_links = serializers.SerializerMethodField()
    metadata = serializers.SerializerMethodField()
    
    class Meta:
        model = Artist
        fields = [
            'id',
            'name',
            'bio',
            'website',
            'birth_year',
            'profile_image',
            'social_media_links',
            'metadata',
        ]
    
    def get_social_media_links(self, obj):
        """Extract social media links from StreamField"""
        links = []
        if obj.social_media_links:
            for block in obj.social_media_links:
                if block.block_type == 'social_link':
                    links.append({
                        'platform': block.value.get('platform'),
                        'platform_name': block.value.get('platform_name', ''),
                        'url': block.value.get('url'),
                        'handle': block.value.get('handle', ''),
                    })
        return links
    
    def get_metadata(self, obj):
        """Add metadata about the artist"""
        return {
            'artwork_count': obj.artwork_list.count() if hasattr(obj, 'artwork_list') else 0,
        }