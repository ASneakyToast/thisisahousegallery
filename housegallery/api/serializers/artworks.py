from django.utils.html import strip_tags
from rest_framework import serializers
from housegallery.artworks.models import Artwork, ArtworkImage
from housegallery.artists.models import Artist
from housegallery.api.serializers.images import ImageSerializer


class ArtworkImageSerializer(serializers.ModelSerializer):
    """Serializer for artwork images"""
    image = ImageSerializer(read_only=True)
    
    class Meta:
        model = ArtworkImage
        fields = ['id', 'image', 'caption', 'sort_order']


class ArtworkListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for artwork listings"""
    
    title_plain = serializers.SerializerMethodField()
    artists = serializers.SerializerMethodField()
    primary_image = serializers.SerializerMethodField()
    materials_list = serializers.SerializerMethodField()
    
    class Meta:
        model = Artwork
        fields = [
            'id',
            'title',
            'title_plain',
            'artists',
            'description',
            'materials_list',
            'size',
            'date',
            'primary_image',
        ]
    
    def get_title_plain(self, obj):
        """Return plain text version of title"""
        return strip_tags(obj.title) if obj.title else None
    
    def get_artists(self, obj):
        """Return list of artist names"""
        return [{'id': artist.id, 'name': artist.name} 
                for artist in obj.artists.all()]
    
    def get_primary_image(self, obj):
        """Return the first image as primary"""
        first_image = obj.artwork_images.first()
        if first_image and first_image.image:
            return ImageSerializer(first_image.image).data
        return None
    
    def get_materials_list(self, obj):
        """Return materials as a list"""
        return [tag.name for tag in obj.materials.all()]


class ArtworkSerializer(ArtworkListSerializer):
    """Full serializer for artwork detail with all images"""
    
    images = serializers.SerializerMethodField()
    artifacts = serializers.SerializerMethodField()
    metadata = serializers.SerializerMethodField()
    
    class Meta:
        model = Artwork
        fields = ArtworkListSerializer.Meta.fields + [
            'images',
            'artifacts',
            'metadata',
        ]
    
    def get_images(self, obj):
        """Return all artwork images"""
        artwork_images = obj.artwork_images.select_related('image').order_by('sort_order')
        return ArtworkImageSerializer(artwork_images, many=True).data
    
    def get_artifacts(self, obj):
        """Process artifacts StreamField"""
        artifacts = []
        if obj.artifacts:
            for block in obj.artifacts:
                block_data = {
                    'type': block.block_type,
                    'id': block.id,
                }
                
                if block.block_type == 'image':
                    # Handle image blocks
                    image_id = block.value.get('image')
                    if image_id:
                        try:
                            from housegallery.images.models import CustomImage
                            image = CustomImage.objects.get(id=image_id)
                            block_data['image'] = ImageSerializer(image).data
                            block_data['caption'] = block.value.get('caption', '')
                        except CustomImage.DoesNotExist:
                            pass
                            
                elif block.block_type == 'text':
                    # Handle text blocks
                    block_data['text'] = str(block.value.get('text', ''))
                    
                elif block.block_type == 'document':
                    # Handle document blocks
                    block_data['document'] = {
                        'title': block.value.get('title', ''),
                        'description': str(block.value.get('description', '')),
                        # Note: Document URL would need additional handling
                    }
                
                artifacts.append(block_data)
        
        return artifacts
    
    def get_metadata(self, obj):
        """Return additional metadata"""
        return {
            'created': obj.date.isoformat() if obj.date else None,
            'has_multiple_artists': obj.artists.count() > 1,
            'image_count': obj.artwork_images.count(),
        }