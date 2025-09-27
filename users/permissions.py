from rest_framework.permissions import BasePermission

class IsStaffUser(BasePermission):
    """
    Mengizinkan hanya staff user (is_staff=True).
    """
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_staff)
