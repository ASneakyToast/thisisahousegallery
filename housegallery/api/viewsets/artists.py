from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from housegallery.artists.models import Artist
from housegallery.api.serializers import ArtistSerializer
from housegallery.api.authentication.api_key import APIKeyAuthentication
from housegallery.api.permissions.artist_scoped import ArtistScopedPermission


class ArtistViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for Artist data.
    
    Provides read-only access to artist information.
    API key authentication ensures users only see their own artist data.
    """
    
    serializer_class = ArtistSerializer
    authentication_classes = [APIKeyAuthentication]
    permission_classes = [ArtistScopedPermission]
    
    def get_queryset(self):
        """Return only the authenticated artist"""
        if hasattr(self.request, 'auth') and hasattr(self.request.auth, 'artist'):
            # Return a queryset containing only the authenticated artist
            return Artist.objects.filter(id=self.request.auth.artist.id)
        return Artist.objects.none()
    
    @action(detail=False, methods=['get'], url_path='profile')
    def profile(self, request):
        """
        Get the authenticated artist's profile.
        
        This is a convenience endpoint that returns the artist data
        without needing to know the artist ID.
        """
        if hasattr(request, 'auth') and hasattr(request.auth, 'artist'):
            serializer = self.get_serializer(request.auth.artist)
            return Response(serializer.data)
        return Response({"detail": "Not authenticated"}, status=401)