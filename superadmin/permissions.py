from rest_framework import permissions

class IsSuperAdmin(permissions.BasePermission):
    """
    Custom permission to only allow super admin users to access the view.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_superuser

class IsDepartmentAdmin(permissions.BasePermission):
    """
    Custom permission to only allow department admins to access the view.
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        try:
            return request.user.admin_profile.is_active
        except:
            return False

    def has_object_permission(self, request, view, obj):
        try:
            admin_profile = request.user.admin_profile
            if not admin_profile.is_active:
                return False
            # Check if the object belongs to one of the admin's departments
            if hasattr(obj, 'department'):
                return obj.department in admin_profile.departments.all()
            return False
        except:
            return False 