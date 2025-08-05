from rest_framework import permissions


class ArtistScopedPermission(permissions.BasePermission):
    """Ensure users can only access their own artist data"""
    
    def has_permission(self, request, view):
        """Check if the request has valid artist authentication"""
        return hasattr(request, 'auth') and hasattr(request.auth, 'artist')
    
    def has_object_permission(self, request, view, obj):
        """Check if the object belongs to the authenticated artist"""
        # For Artist objects
        if hasattr(obj, 'id') and obj.__class__.__name__ == 'Artist':
            return obj.id == request.auth.artist.id
            
        # For objects with an artist field
        if hasattr(obj, 'artist'):
            return obj.artist == request.auth.artist
            
        # For objects with artists many-to-many field
        if hasattr(obj, 'artists'):
            return request.auth.artist in obj.artists.all()
        
        # Default deny
        return False