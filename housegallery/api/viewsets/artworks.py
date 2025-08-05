from django.db.models import Prefetch, Q
from rest_framework import viewsets, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from housegallery.artworks.models import Artwork, ArtworkImage
from housegallery.api.serializers import ArtworkSerializer, ArtworkListSerializer
from housegallery.api.authentication.api_key import APIKeyAuthentication
from housegallery.api.permissions.artist_scoped import ArtistScopedPermission


class ArtworkViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for Artwork data.
    
    Provides read-only access to artworks for the authenticated artist.
    Supports filtering, searching, and ordering.
    """
    
    authentication_classes = [APIKeyAuthentication]
    permission_classes = [ArtistScopedPermission]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'description']
    ordering_fields = ['date', 'id']
    ordering = ['-date', '-id']
    
    def get_serializer_class(self):
        """Use lightweight serializer for list view"""
        if self.action == 'list':
            return ArtworkListSerializer
        return ArtworkSerializer
    
    def get_queryset(self):
        """Return artworks for the authenticated artist only"""
        if not hasattr(self.request, 'auth') or not hasattr(self.request.auth, 'artist'):
            return Artwork.objects.none()
        
        artist = self.request.auth.artist
        
        # Base queryset with optimized queries
        queryset = Artwork.objects.filter(
            artists=artist
        ).select_related(
            # No direct FK relationships to select
        ).prefetch_related(
            'artists',
            'materials',
            Prefetch(
                'artwork_images',
                queryset=ArtworkImage.objects.select_related('image').order_by('sort_order')
            )
        ).distinct()
        
        # Apply filters from query params
        queryset = self._apply_filters(queryset)
        
        return queryset
    
    def _apply_filters(self, queryset):
        """Apply additional filters from query parameters"""
        params = self.request.query_params
        
        # Filter by materials/tags
        materials = params.get('materials')
        if materials:
            material_list = [m.strip() for m in materials.split(',')]
            queryset = queryset.filter(materials__name__in=material_list).distinct()
        
        # Filter by year
        year = params.get('year')
        if year:
            try:
                year = int(year)
                queryset = queryset.filter(date__year=year)
            except ValueError:
                pass
        
        # Filter by date range
        date_from = params.get('date_from')
        date_to = params.get('date_to')
        if date_from:
            queryset = queryset.filter(date__gte=date_from)
        if date_to:
            queryset = queryset.filter(date__lte=date_to)
        
        # Filter by size presence
        has_size = params.get('has_size')
        if has_size is not None:
            if has_size.lower() == 'true':
                queryset = queryset.exclude(size='')
            elif has_size.lower() == 'false':
                queryset = queryset.filter(size='')
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def featured(self, request):
        """
        Return featured artworks.
        
        This could be customized to return artworks marked as featured,
        or use some other logic to determine featured pieces.
        """
        # For now, return the 6 most recent artworks
        featured = self.get_queryset().order_by('-date', '-id')[:6]
        serializer = ArtworkListSerializer(featured, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def materials(self, request):
        """
        Return all unique materials/tags used by this artist's artworks.
        """
        artist = request.auth.artist
        materials = set()
        
        # Get all materials from the artist's artworks
        artworks = Artwork.objects.filter(artists=artist).prefetch_related('materials')
        for artwork in artworks:
            for material in artwork.materials.all():
                materials.add(material.name)
        
        return Response({
            'materials': sorted(list(materials))
        })