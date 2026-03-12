from rest_framework import permissions
from housegallery.api.models import ReadOnlyToken


class ReadOnlyTokenPermission(permissions.BasePermission):
    """Allow read-only access for requests authenticated with a ReadOnlyToken."""

    def has_permission(self, request, view):
        if request.method not in permissions.SAFE_METHODS:
            return False
        return isinstance(request.auth, ReadOnlyToken)
