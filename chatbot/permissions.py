from rest_framework.permissions import BasePermission

class PublicEndpoint(BasePermission):
    """
    Allow unrestricted access to the chatbot API.
    """
    def has_permission(self, request, view):
        return True  # Always allow access