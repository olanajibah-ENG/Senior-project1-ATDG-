from rest_framework.permissions import BasePermission
from django.conf import settings

class IsServiceToService(BasePermission):
    """
    Custom permission to allow access only if a specific secret API key is provided in the header.
    """
    def has_permission(self, request, view):
        api_key = request.headers.get('X-API-KEY')
        expected_key = getattr(settings, 'SERVICE_API_KEY', None)

        return bool(api_key and api_key == expected_key)