from django.contrib import admin

from apps.crm.models import Lead


@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "stage", "created_at")
    search_fields = ("name", "email")
    list_filter = ("stage",)
