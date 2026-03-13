from django.contrib import admin

from apps.manufacturing.models import WorkOrder


@admin.register(WorkOrder)
class WorkOrderAdmin(admin.ModelAdmin):
    list_display = ("title", "status", "quantity", "due_date")
    list_filter = ("status",)
    search_fields = ("title",)
