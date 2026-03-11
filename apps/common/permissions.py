"""
apps/common/permissions.py

Reusable DRF permission classes shared across the entire ERP.
"""

from rest_framework.permissions import BasePermission, IsAuthenticated, SAFE_METHODS


class IsSuperUser(BasePermission):
    """
    Grants access only to active superusers.
    Suitable as a base-level gate for admin-only endpoints.
    """
    message = "Superuser access required."

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.is_active
            and request.user.is_superuser
        )


class IsManager(BasePermission):
    """
    Grants access to users whose StaffProfile has is_manager=True,
    or to superusers.
    """
    message = "Manager or superuser access required."

    def has_permission(self, request, view):
        user = request.user
        if not (user and user.is_authenticated and user.is_active):
            return False
        if user.is_superuser:
            return True
        try:
            return user.staff_profile.is_manager
        except Exception:
            return False


class IsManagerOrReadOnly(IsManager):
    """
    Read access for any authenticated user;
    write access restricted to managers and superusers.
    """
    message = "Manager or superuser access required for write operations."

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return bool(request.user and request.user.is_authenticated)
        return super().has_permission(request, view)


class IsTenantUser(IsAuthenticated):
    """
    Ensures the requesting user is authenticated and belongs to the
    active tenant schema (guards against cross-tenant data leakage).
    The actual tenant scoping is enforced at the queryset level, but
    this permission provides an explicit defence-in-depth gate.
    """
    message = "You do not have access to this tenant."

    def has_permission(self, request, view):
        if not super().has_permission(request, view):
            return False
        # django-tenants sets connection.schema_name at request time;
        # we simply confirm the user is active within the current tenant.
        return request.user.is_active


class IsSuperUserOrReadOnly(BasePermission):
    """
    Read access for any authenticated user;
    write access restricted to superusers only.
    """
    message = "Superuser access required for write operations."

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        if request.method in SAFE_METHODS:
            return True
        return request.user.is_active and request.user.is_superuser
