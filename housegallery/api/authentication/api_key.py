from rest_framework import authentication, exceptions
from django.utils import timezone
from housegallery.api.models import APIKey


class APIKeyAuthentication(authentication.BaseAuthentication):
    """Custom API key authentication for artist-scoped access"""
    
    keyword = 'API-Key'
    
    def authenticate(self, request):
        # Get API key from header
        api_key = self.get_api_key_from_request(request)
        if not api_key:
            return None
            
        try:
            key_obj = APIKey.objects.select_related('artist').get(
                key=api_key, 
                is_active=True
            )
        except APIKey.DoesNotExist:
            raise exceptions.AuthenticationFailed('Invalid API key')
        
        # Check IP whitelist if configured
        if key_obj.allowed_ips:
            client_ip = self.get_client_ip(request)
            if client_ip not in key_obj.allowed_ips:
                raise exceptions.AuthenticationFailed('IP address not allowed')
        
        # Update usage statistics
        key_obj.update_usage()
        
        # Return tuple of (user, auth)
        # We use the artist as the "user" for permission checking
        return (key_obj.artist, key_obj)
    
    def get_api_key_from_request(self, request):
        """Extract API key from request headers"""
        # Try header first
        api_key = request.META.get('HTTP_API_KEY')
        if api_key:
            return api_key
            
        # Also check for the custom header format
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        if auth_header.startswith(self.keyword + ' '):
            return auth_header[len(self.keyword) + 1:]
            
        return None
    
    def get_client_ip(self, request):
        """Get the client IP address from the request"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            # Take the first IP in the chain
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    def authenticate_header(self, request):
        """Return the authentication header to use for 401 responses"""
        return self.keyword