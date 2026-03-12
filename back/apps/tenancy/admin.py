from django.contrib import admin

from apps.tenancy.models import Tenant, TenantDomain


@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "schema_name", "is_active", "created_at")
    search_fields = ("name", "slug", "schema_name")


@admin.register(TenantDomain)
class TenantDomainAdmin(admin.ModelAdmin):
    list_display = ("domain", "tenant", "is_primary", "is_active")
    search_fields = ("domain",)
    list_filter = ("is_primary", "is_active")
