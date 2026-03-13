from django.contrib import admin

from apps.customers.models import Company, Domain


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ("name", "schema_name", "company_type", "created_on")
    search_fields = ("name", "schema_name")


@admin.register(Domain)
class DomainAdmin(admin.ModelAdmin):
    list_display = ("domain", "tenant", "is_primary")
    search_fields = ("domain",)
