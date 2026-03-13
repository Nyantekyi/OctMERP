from rest_framework.permissions import BasePermission


class HasTenantModulePermission(BasePermission):
    message = "This module is not enabled for this company."

    def has_permission(self, request, view):
        tenant = getattr(request, "tenant", None)
        required_module = getattr(view, "required_module", None)
        if tenant is None or not required_module:
            return True
        return required_module in getattr(tenant, "enabled_modules", [])
