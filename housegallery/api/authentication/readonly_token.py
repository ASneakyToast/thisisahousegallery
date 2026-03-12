from rest_framework import authentication, exceptions
from housegallery.api.models import ReadOnlyToken


class ReadOnlyTokenAuthentication(authentication.BaseAuthentication):
    """Bearer token authentication for read-only API access."""

    keyword = 'Bearer'

    def authenticate(self, request):
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        if not auth_header.startswith(self.keyword + ' '):
            return None

        token = auth_header[len(self.keyword) + 1:]
        if not token:
            return None

        try:
            token_obj = ReadOnlyToken.objects.get(key=token, is_active=True)
        except ReadOnlyToken.DoesNotExist:
            raise exceptions.AuthenticationFailed('Invalid token')

        # Check IP whitelist if configured
        if token_obj.allowed_ips:
            client_ip = self.get_client_ip(request)
            if client_ip not in token_obj.allowed_ips:
                raise exceptions.AuthenticationFailed('IP address not allowed')

        token_obj.update_usage()

        # Return (None, token_obj) — no user/artist attached
        return (None, token_obj)

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR')

    def authenticate_header(self, request):
        return self.keyword
