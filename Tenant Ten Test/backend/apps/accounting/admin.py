from django.contrib import admin

from apps.accounting.models import AccountingEntry


@admin.register(AccountingEntry)
class AccountingEntryAdmin(admin.ModelAdmin):
    list_display = ("description", "amount", "currency", "entry_date")
    search_fields = ("description",)
    list_filter = ("currency",)
