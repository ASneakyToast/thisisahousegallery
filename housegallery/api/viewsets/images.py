from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from housegallery.images.models import CustomImage
from housegallery.artworks.models import Artwork
from housegallery.api.serializers import ImageSerializer
from housegallery.api.authentication.api_key import APIKeyAuthentication
from housegallery.api.permissions.artist_scoped import ArtistScopedPermission


class ImageViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for Image data.
    
    Provides read-only access to images belonging to the authenticated artist's artworks.
    Includes endpoints for rendition generation.
    """
    
    serializer_class = ImageSerializer
    authentication_classes = [APIKeyAuthentication]
    permission_classes = [ArtistScopedPermission]
    
    def get_queryset(self):
        """Return images that belong to the authenticated artist's artworks"""
        if not hasattr(self.request, 'auth') or not hasattr(self.request.auth, 'artist'):
            return CustomImage.objects.none()
        
        artist = self.request.auth.artist
        
        # Get all images from artworks that belong to this artist
        artwork_ids = Artwork.objects.filter(artists=artist).values_list('id', flat=True)
        image_ids = set()
        
        # Get images from artwork_images
        from housegallery.artworks.models import ArtworkImage
        artwork_images = ArtworkImage.objects.filter(
            artwork_id__in=artwork_ids
        ).values_list('image_id', flat=True)
        image_ids.update(artwork_images)
        
        # Also get the artist's profile image
        if artist.profile_image_id:
            image_ids.add(artist.profile_image_id)
        
        return CustomImage.objects.filter(id__in=image_ids)
    
    @action(detail=True, methods=['get'])
    def renditions(self, request, pk=None):
        """
        Get all available renditions for a specific image.
        
        Returns detailed information about each rendition including
        dimensions, file size, and format.
        """
        image = self.get_object()
        
        renditions = {
            'image_id': image.id,
            'original': {
                'url': image.file.url,
                'width': image.width,
                'height': image.height,
                'file_size': image.file_size,
                'format': image.file.name.split('.')[-1].upper() if image.file.name else 'UNKNOWN'
            },
            'renditions': {}
        }
        
        # Standard renditions
        rendition_specs = [
            ('thumbnail_400', 'width-400|format-webp|webpquality-90'),
            ('web_optimized_1200', 'width-1200|format-webp|webpquality-85'),
            ('high_quality_2400', 'max-2400x2400|format-webp|webpquality-95'),
        ]
        
        for name, spec in rendition_specs:
            try:
                rendition = image.get_rendition(spec)
                renditions['renditions'][name] = {
                    'url': rendition.url,
                    'width': rendition.width,
                    'height': rendition.height,
                    'file_size': rendition.file.size if hasattr(rendition.file, 'size') else None,
                    'format': 'WebP'
                }
            except Exception as e:
                # Log error but continue with other renditions
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Failed to generate rendition {name} for image {image.id}: {str(e)}")
        
        return Response(renditions)
    
    @action(detail=True, methods=['post'])
    def custom_rendition(self, request, pk=None):
        """
        Generate a custom rendition on-demand.
        
        Request body should contain:
        - width: desired width (optional)
        - height: desired height (optional)
        - format: output format (jpeg, png, webp)
        - quality: compression quality (1-100)
        """
        image = self.get_object()
        
        # Parse parameters
        width = request.data.get('width')
        height = request.data.get('height')
        output_format = request.data.get('format', 'webp').lower()
        quality = request.data.get('quality', 85)
        
        # Validate parameters
        if not width and not height:
            return Response(
                {'error': 'Either width or height must be specified'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if output_format not in ['jpeg', 'png', 'webp']:
            return Response(
                {'error': 'Format must be jpeg, png, or webp'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            quality = int(quality)
            if quality < 1 or quality > 100:
                raise ValueError
        except (ValueError, TypeError):
            return Response(
                {'error': 'Quality must be an integer between 1 and 100'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Build filter spec
        filter_parts = []
        
        if width and height:
            filter_parts.append(f'fill-{width}x{height}')
        elif width:
            filter_parts.append(f'width-{width}')
        else:
            filter_parts.append(f'height-{height}')
        
        if output_format != 'png':  # PNG doesn't support quality
            if output_format == 'webp':
                filter_parts.append(f'format-webp|webpquality-{quality}')
            else:
                filter_parts.append(f'format-jpeg|jpegquality-{quality}')
        else:
            filter_parts.append('format-png')
        
        filter_spec = '|'.join(filter_parts)
        
        try:
            rendition = image.get_rendition(filter_spec)
            return Response({
                'url': rendition.url,
                'width': rendition.width,
                'height': rendition.height,
                'format': output_format.upper(),
                'filter_spec': filter_spec
            })
        except Exception as e:
            return Response(
                {'error': f'Failed to generate rendition: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )